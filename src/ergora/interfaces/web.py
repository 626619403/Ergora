"""Local control plane. All state transitions use the same application functions as the CLI."""

import hashlib
import sys
import tempfile
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Body, FastAPI, Path as PathParameter, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from ergora import __version__
import ergora.training.application as training
import ergora.definitions.agents as agent_definitions
import ergora.agents.runs as agent_runs
import ergora.campaigns.application as campaigns
from ergora.campaigns.records import tasks_by_id, training_gpu_release_task, training_readback_task, training_screen_task
import ergora.definitions.bundles as definition_bundles
import ergora.development.drafts as drafts
import ergora.improvement.document_corrections as document_corrections
import ergora.improvement.evaluation as evaluation
import ergora.development.handoff as handoff
import ergora.issues.application as issues
import ergora.issues.writebacks as issue_writebacks
import ergora.improvement.kernel as kernel
import ergora.improvement.memory as memory
import ergora.improvement.optimization as optimization
import ergora.configuration.projects as projects
import ergora.configuration.registrations as registrations
import ergora.improvement.research as research
import ergora.improvement.retrospectives as retrospectives
import ergora.operations.services as services
import ergora.development.application as tasks
import ergora.definitions.skills as skill_assets
import ergora.improvement.skill_adoption as skills
import ergora.operations.tools as tools
import ergora.definitions.workflows as workflow_definitions
from ergora.configuration import catalog as components
from ergora.development import envelopes as task_envelopes
from ergora.storage.state import State
import ergora.native.compiler as native_compiler
import ergora.native.resources as native_resources
from ergora._paths import DATA_ROOT


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectPayload(Payload):
    id: str
    repo: str


class HandoffEvidencePayload(Payload):
    packet: str
    packet_sha256: str
    selection: list[dict] = Field(default_factory=list)


class RetrospectivePreparePayload(HandoffEvidencePayload):
    objective: str
    manifest: str
    instance: str
    destination: str
    max_prompt_bytes: int = Field(strict=True)

    def arguments(self) -> dict:
        values = self.model_dump()
        for name in ('packet', 'manifest', 'destination'):
            values[name] = Path(values[name])
        return values


class SkillRetrospectivePreparePayload(RetrospectivePreparePayload):
    name: str
    digest: str
    head_revision: int = Field(strict=True)


class MemoryRetrospectivePreparePayload(RetrospectivePreparePayload):
    memory_id: str | None
    revision: int = Field(strict=True)


class WorkflowRetrospectivePreparePayload(RetrospectivePreparePayload):
    target_manifest: str
    target_digest: str
    next_version: str

    def arguments(self) -> dict:
        values = super().arguments()
        values['target_manifest'] = Path(values['target_manifest'])
        return values


class RetrospectiveInputPayload(Payload):
    directory: str


class RetrospectiveResultPayload(RetrospectiveInputPayload):
    input_digest: str
    result: str
    result_sha256: str

    def arguments(self) -> dict:
        values = self.model_dump()
        values['source'] = Path(values.pop('directory'))
        values['result'] = Path(values['result'])
        return values


class RetrospectiveExportPayload(RetrospectiveResultPayload):
    candidate_digest: str
    destination: str

    def arguments(self) -> dict:
        values = super().arguments()
        values['destination'] = Path(values['destination'])
        return values


class CompositionInputPayload(Payload):
    directory: str
    input_digest: str
    backend: str | None = None
    model: str | None = None
    reason: str | None = None
    codex_config: str | None = None

    def arguments(self) -> dict:
        values = self.model_dump()
        values['source'] = Path(values.pop('directory'))
        if values['codex_config'] is not None:
            values['codex_config'] = Path(values['codex_config'])
        return values


class CompositionRunPayload(CompositionInputPayload):
    timeout: int = Field(strict=True, ge=1, le=3600)


class BindingPayload(Payload):
    binding: dict
    revision: int


class RevisionPayload(Payload):
    revision: int


class CorrectionSuggestionsPayload(Payload):
    enabled: bool = Field(strict=True)
    revision: int = Field(strict=True, ge=1)


class DocumentCorrectionApplyPayload(Payload):
    revision: int = Field(strict=True, ge=1)
    candidate_digest: str = Field(strict=True, pattern=r"^[a-f0-9]{64}$")
    base_sha256: str = Field(strict=True, pattern=r"^[a-f0-9]{64}$")
    scope_sha256: str = Field(strict=True, pattern=r"^[a-f0-9]{64}$")
    confirm: bool = Field(strict=True)


class DocumentCorrectionWithdrawPayload(Payload):
    reason: str = Field(strict=True, min_length=1, max_length=65536, pattern=r"\S")


class DefinitionImportPayload(Payload):
    directory: str


class DefinitionRevisionPayload(Payload):
    base_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    definition: dict
    resource_changes: dict | None = None
    accepted_candidate: dict | None = None


class WorkflowRevisionCheckPayload(DefinitionRevisionPayload):
    impact: dict | None = None


class DefinitionFilePayload(Payload):
    base_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    path: str
    offset: int = Field(default=0, strict=True, ge=0)
    limit: int = Field(default=65_536, strict=True, ge=1, le=65_536)


class DefinitionDocumentPayload(Payload):
    text: str
    format: Literal["json", "yaml"] = "json"


class DoctorPayload(Payload):
    timeout: int = Field(default=5, strict=True, ge=1, le=30)


class ServicesPayload(Payload):
    action: Literal["start", "stop", "shutdown"]
    names: list[str] = Field(default_factory=list)
    revision: int = Field(strict=True, ge=1)
    confirm: bool = Field(default=False, strict=True)
    timeout: int = Field(default=30, strict=True, ge=1, le=60)


class RegistrationPayload(Payload):
    definition: dict
    revision: int = Field(strict=True, ge=0)


class RegistrationRevisionPayload(Payload):
    revision: int = Field(strict=True, ge=0)


class RegistrationImportPayload(RegistrationPayload):
    preview_sha256: str = Field(pattern="^[0-9a-f]{64}$")


class TaskDefinitionPayload(Payload):
    definition: dict
    revision: int = Field(strict=True, ge=1)


class IssueCapturePayload(Payload):
    revision: int = Field(strict=True, ge=1)


class IssueLinkPayload(IssueCapturePayload):
    snapshot_sha256: str
    task_id: str
    creation_sha256: str
    reason: str


class IssueWritebackPreparePayload(IssueCapturePayload):
    task_id: str
    run_id: str
    candidate_sha: str


class IssueLabelPreparePayload(IssueWritebackPreparePayload):
    label_name: str = Field(min_length=1)


class IssueCandidateObservePayload(IssueWritebackPreparePayload):
    base_branch: str


class IssueReviewLinkPayload(IssueCandidateObservePayload):
    review_number: str
    reason: str


class IssueWritebackSendPayload(IssueCapturePayload):
    confirm: bool = Field(strict=True)


class IssueWritebackObservePayload(Payload):
    comment_id: str | None = None
    page: int = Field(default=1, strict=True, ge=1, le=10_000)
    cursor: str | None = None


class TaskCreationPayload(TaskDefinitionPayload):
    preview_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    prepare_sha256: str | None = Field(default=None, pattern="^[0-9a-f]{64}$")


class TaskResumePayload(Payload):
    revision: int = Field(strict=True, ge=1)
    intent_sha256: str = Field(pattern="^[0-9a-f]{64}$")


class TaskStartPayload(Payload):
    revision: int = Field(strict=True, ge=1)
    creation_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    timeout: int = Field(default=20, strict=True, ge=1, le=60)


class TaskResumeStartPayload(TaskResumePayload):
    timeout: int = Field(default=20, strict=True, ge=1, le=60)


class TrainingBaselinePreviewPayload(Payload):
    baseline: dict


class TrainingBaselineInitPayload(TrainingBaselinePreviewPayload):
    revision: int = Field(strict=True, ge=1)
    baseline_sha256: str = Field(pattern="^[0-9a-f]{64}$")


class TrainingRunnerPreviewPayload(Payload):
    runner: dict


class TrainingRunnerRegistrationPayload(TrainingRunnerPreviewPayload):
    revision: int = Field(strict=True, ge=1)
    runner_sha256: str = Field(pattern="^[0-9a-f]{64}$")


class TrainingExperimentPreviewPayload(Payload):
    experiment: dict
    runner_template_id: str
    max_run_seconds: int | None = Field(default=None, strict=True, ge=60, le=86400)


class TrainingPreparationPayload(TrainingExperimentPreviewPayload):
    revision: int = Field(strict=True, ge=1)
    preview_sha256: str = Field(pattern="^[0-9a-f]{64}$")


class TrainingPreparationResumePayload(Payload):
    revision: int = Field(strict=True, ge=1)
    intent_sha256: str = Field(pattern="^[0-9a-f]{64}$")


class TrainingStartPayload(Payload):
    revision: int = Field(strict=True, ge=1)
    manifest_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    timeout: int = Field(default=20, strict=True, ge=1, le=60)


class TrainingResumeStartPayload(Payload):
    revision: int = Field(strict=True, ge=1)
    intent_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    timeout: int = Field(default=20, strict=True, ge=1, le=60)


class TrainingApprovalPayload(Payload):
    revision: int = Field(strict=True, ge=1)
    run_id: str = Field(min_length=1, max_length=128)
    evidence_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    confirm: bool = Field(strict=True)
    timeout: int = Field(default=20, strict=True, ge=1, le=60)


class TrainingResumeApprovalPayload(TrainingResumeStartPayload):
    confirm: bool = Field(strict=True)


class TrainingCancelPayload(Payload):
    revision: int = Field(strict=True, ge=1)
    request_id: str = Field(min_length=1, max_length=120)
    run_id: str = Field(min_length=1, max_length=128)
    reason: str = Field(min_length=1, max_length=1000)
    timeout: int = Field(default=20, strict=True, ge=1, le=60)


class TrainingResumeCancelPayload(TrainingResumeStartPayload):
    request_id: str = Field(min_length=1, max_length=120)


class TaskRunDecisionPayload(Payload):
    revision: int = Field(strict=True, ge=1)
    run_id: str = Field(min_length=1, max_length=128)
    confirm: bool = Field(strict=True)
    timeout: int = Field(default=20, strict=True, ge=1, le=60)


class TaskApprovePayload(TaskRunDecisionPayload):
    plan_sha256: str = Field(pattern="^[0-9a-f]{64}$")


class TaskWorkPriorityPayload(TaskRunDecisionPayload):
    plan_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    work_unit_id: str = Field(pattern="^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")


WorkPriorityDecisionId = Annotated[str, PathParameter(pattern="^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")]


class TaskResumeDecisionPayload(TaskResumeStartPayload):
    confirm: bool = Field(strict=True)


class TaskCancelPayload(Payload):
    revision: int = Field(strict=True, ge=1)
    run_id: str = Field(min_length=1, max_length=128)
    reason: str = Field(min_length=1, max_length=1000)
    confirm: bool = Field(strict=True)
    timeout: int = Field(default=20, strict=True, ge=1, le=60)


class TaskExportPayload(Payload):
    revision: int = Field(strict=True, ge=1)
    run_id: str = Field(min_length=1, max_length=128)
    candidate_sha: str = Field(pattern="^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
    branch: str = Field(min_length=1, max_length=1024)
    confirm: bool = Field(strict=True)
    timeout: int = Field(default=20, strict=True, ge=1, le=60)


class TaskHandoffPayload(Payload):
    run_id: str = Field(min_length=1, max_length=128)
    timeout: int = Field(default=20, strict=True, ge=1, le=60)


class MemoryPayload(RevisionPayload):
    revision: int = 0
    text: str
    source: dict[str, str]
    id: str | None = None
    expires_at: str | None = None


class RestorePayload(RevisionPayload):
    from_revision: int


class ImportPayload(Payload):
    directory: str
    hypothesis: str = "Imported candidate"


class AdoptPayload(RevisionPayload):
    baseline_run: str
    candidate_run: str
    reason: str


class RollbackPayload(RevisionPayload):
    name: str
    digest: str
    reason: str


class EvaluationPayload(Payload):
    digest: str
    suite: str


class OptimizePayload(Payload):
    baseline: str
    suite: str
    objective: str
    max_evaluations: int = 20
    max_proposals: int = 5
    timeout: int = 300


class ResearchPayload(Payload):
    urls: list[str]
    id: str | None = None
    max_bytes: int = 1_000_000
    timeout: int = 30
    allow_private: bool = False


class ReviewPayload(RevisionPayload):
    status: Literal["reviewed", "dismissed"]
    reason: str


class AgentPayload(Payload):
    role: str
    prompt: str
    timeout: int = Field(default=300, strict=True, ge=1, le=3600)
    skills: list[str] = Field(default_factory=list)
    recall: str | None = None
    template: str | None = None
    session_intent: str | None = None
    expected_revision: int | None = Field(default=None, strict=True, ge=1)
    codex_config: str | None = None


class AgentContinuePayload(Payload):
    parent_run_id: str
    prompt: str
    expected_revision: int = Field(strict=True, ge=1)
    intent_id: str
    timeout: int = Field(default=300, strict=True, ge=1, le=3600)


class AgentStopPayload(Payload):
    run_id: str
    intent_id: str


class KernelPayload(Payload):
    action: str = "plan"
    timeout: int = 30
    reconcile_reason: str | None = None


class DraftPayload(RevisionPayload):
    id: str
    kind: str
    input: dict


class CompositionSelectionPayload(Payload):
    id: str
    version: str
    grant: dict


class CompositionPreviewPayload(CompositionSelectionPayload):
    admission: dict | None = None


class CompositionFreezePayload(CompositionSelectionPayload):
    preview_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def _timeline_native_receipt(receipt: dict | None) -> dict | None:
    if receipt is None:
        return None
    run = receipt["run"] or {}
    return {**{key: receipt[key] for key in ("session_id", "parent_run_id", "intent_id", "run_id", "dispatch")},
            "start_status": receipt["native_start"]["status"],
            **{key: run[key] for key in ("status", "result_sha256", "execution_stopped", "returncode",
                                       "campaign_recipient_blocker") if key in run}}


def _timeline_history_timing(history: dict) -> dict:
    timing = history.get("timing")
    if not isinstance(timing, dict) or timing.get("clock") != "temporal_history":
        return {}
    intervals = timing.get("intervals_ns")
    if not isinstance(intervals, dict):
        return {}
    selected = {}
    for name in ("ready_to_scheduled", "scheduled_to_worker_started", "worker_started_to_delivery_terminal"):
        value = intervals.get(name)
        if type(value) is int and value >= 0:
            selected[name] = value
    return {"timing": {"clock": timing["clock"], "intervals_ns": selected}} if selected else {}


def _training_timeline_recipient(recipient: dict) -> dict:
    history = recipient["history"]
    intent = recipient["intent"]
    projected_history = None
    if history is not None:
        projected_history = {key: history[key] for key in ("status", "scheduled_event_id", "started_event_id",
                                                          "completed_event_id") if key in history}
        projected_history.update(_timeline_history_timing(history))
    return {"status": recipient["status"], "reason": recipient.get("reason"),
            "wake_id": intent["wake_id"] if intent is not None else None,
            "history": projected_history,
            "native_receipt": _timeline_native_receipt(recipient["native_receipt"])}


_ASSIGNMENT_HISTORY_REASONS = frozenset({
    "original_native_intent_occupied", "assignment_already_resumed", "stale_parent", "session_slot_timeout",
    "stopped", "expired", "native_turn_expired", "recipient_authority_revoked", "training_pending_unavailable",
})
_ASSIGNMENT_NATIVE_BLOCKERS = frozenset({"stopped", "expired", "authority_unavailable"})


def _assignment_timeline(assignment: dict) -> dict:
    claim = assignment["claim"]
    history = assignment["history"]
    release = assignment["release"]
    refusal = assignment.get("refusal")
    native = _timeline_native_receipt(assignment["native_receipt"])
    if native is not None:
        blocker = native.get("campaign_recipient_blocker")
        if not isinstance(blocker, str) or blocker not in _ASSIGNMENT_NATIVE_BLOCKERS:
            native.pop("campaign_recipient_blocker", None)
    projected_history = None
    if history is not None:
        projected_history = {key: history[key] for key in ("status", "waiting_accepted_event_id",
                             "waiting_completed_event_id", "training_wait_started_event_id",
                             "scheduled_event_id", "started_event_id") if key in history}
        if "error" in history:
            projected_history["verification_failed"] = True
        # The History owner supplies an outcome only for a verified completed Activity.
        outcome = history.get("outcome")
        if isinstance(outcome, dict) and outcome.get("status") in ("observed", "blocked", "unknown"):
            if "completed_event_id" in history:
                projected_history["completed_event_id"] = history["completed_event_id"]
            reason = outcome.get("reason")
            if outcome["status"] == "blocked" and isinstance(reason, str) and reason in _ASSIGNMENT_HISTORY_REASONS:
                projected_history["reason"] = reason
        elif history["status"] == "unknown":
            terminal_status = history.get("terminal_status")
            terminal_event_id = history.get("completed_event_id")
            if (terminal_status in ("failed", "timed_out", "cancelled")
                    and type(terminal_event_id) is int and terminal_event_id > 0):
                projected_history.update(terminal_status=terminal_status, terminal_event_id=terminal_event_id)
        projected_history.update(_timeline_history_timing(history))
    return {"waiting_task_id": assignment["waiting_task_id"], "task_id": assignment["task_id"],
            "assignee": {key: assignment["assignee"][key] for key in ("role", "generation")},
            "slot_status": assignment["slot_status"],
            "claim": ({"native_run_id": claim["native_run_id"], "wake_id": claim["intent"]["wake_id"],
                       "waiting_receipt_sha256": claim["intent"]["source"]["waiting_receipt_sha256"]}
                      if claim is not None else None),
            "history": projected_history,
            "native_receipt": native,
            "release": ({key: release[key] for key in ("status", "session_id", "run_id", "request_sha256",
                                                        "attempt_sha256") if key in release}
                        if release is not None else None),
            **({"refusal": {key: refusal[key] for key in ("attempt_sha256", "reason")}} if refusal is not None else {}),
            **({"release_observation_failed": True} if "release_error" in assignment else {}),
            **({"release_unobserved": True} if assignment.get("release_unobserved") is True else {})}


def create_app(home: Path | None = None) -> FastAPI:
    state = State(home)
    application = FastAPI(title="Ergora", version=__version__, docs_url=None, redoc_url=None, openapi_url="/api/openapi.json")
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

    @application.middleware("http")
    async def local_boundary(request: Request, call_next):
        if request.url.path.startswith("/api/"):
            origin = request.headers.get("origin")
            expected = f"{request.url.scheme}://{request.headers.get('host', '')}"
            if request.headers.get("sec-fetch-site") == "cross-site" or (origin is not None and origin != expected):
                return JSONResponse({"error": "Use the local console origin"}, status_code=403)
            if request.method in ("POST", "PUT", "DELETE", "PATCH"):
                if request.headers.get("x-ergora-request") != "1":
                    return JSONResponse({"error": "Missing local request header"}, status_code=403)
                if len(await request.body()) > 4_000_000:
                    return JSONResponse({"error": "Request exceeds 4 MB"}, status_code=413)
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cache-Control"] = "no-store"
        return response

    @application.exception_handler(agent_runs.SessionRejected)
    async def session_admission_rejected(request, error):
        return JSONResponse(status_code=400, content={"error": str(error), "admission_rejected": True,
                            "native_effect_started": False, "intent_id": error.intent_id})

    @application.exception_handler(ValueError)
    @application.exception_handler(OSError)
    async def application_error(request, error):
        return JSONResponse({"error": str(error)}, status_code=400)

    console = DATA_ROOT / "console"
    application.mount("/assets", StaticFiles(directory=console), name="assets")

    @application.get("/")
    def index():
        return FileResponse(console / "index.html")

    @application.get("/api/bootstrap")
    def bootstrap():
        return {"version": __version__, "projects": projects.list_projects(state), "tools": tools.catalog(),
                "layers": components.LAYERS,
                "templates": list(native_resources.TEMPLATES), "agent_contracts": {kind: native_resources.agent_contract(kind) for kind in native_resources.TEMPLATES},
                "platform": sys.platform, "state_directory": str(state.root),
                "reference_supported": sys.platform == "linux",
                "boundary": "local trusted-user control plane"}

    @application.get("/api/installation-profiles")
    def installation_profiles():
        return tools.installation_profiles()

    @application.get("/api/agent-definitions")
    def agent_library(role: str | None = None, specialty: str | None = None):
        return agent_definitions.definitions(state, role=role, specialty=specialty)

    @application.post("/api/definition-documents/convert")
    def convert_definition_document(body: DefinitionDocumentPayload):
        return definition_bundles.convert_document(body.text, body.format)

    @application.get("/api/agent-definitions/{identity}/{version}")
    def agent_definition(identity: str, version: str):
        return agent_definitions.get(state, identity, version, material=True)

    @application.post("/api/agent-definitions/{identity}/{version}/revisions/check")
    def check_agent_revision(identity: str, version: str, body: DefinitionRevisionPayload):
        return agent_definitions.revise(state, identity, version, **body.model_dump())

    @application.post("/api/agent-definitions/{identity}/{version}/revisions")
    def publish_agent_revision(identity: str, version: str, body: DefinitionRevisionPayload):
        return agent_definitions.revise(state, identity, version, **body.model_dump(), publish=True)

    @application.post("/api/agent-definitions/{identity}/{version}/revisions/preview-resources")
    def preview_agent_resources(identity: str, version: str, body: DefinitionRevisionPayload):
        return agent_definitions.revise(state, identity, version, **body.model_dump(), preview_resources=True)

    @application.post("/api/agent-definitions/{identity}/{version}/files/read")
    def read_agent_file(identity: str, version: str, body: DefinitionFilePayload):
        return agent_definitions.read_file(state, identity, version, **body.model_dump())

    @application.get("/api/workflow-definitions")
    def workflow_library():
        return workflow_definitions.definitions(state)

    @application.post("/api/workflow-definitions/import")
    def import_workflow_definition(body: DefinitionImportPayload):
        return workflow_definitions.import_bundle(state, Path(body.directory))

    @application.get("/api/workflow-definitions/{identity}/{version}")
    def workflow_definition(identity: str, version: str):
        return workflow_definitions.get(state, identity, version, material=True)

    @application.post("/api/workflow-definitions/{identity}/{version}/revisions/check")
    def check_workflow_revision(identity: str, version: str, body: WorkflowRevisionCheckPayload):
        return workflow_definitions.revise(state, identity, version, **body.model_dump())

    @application.post("/api/workflow-definitions/{identity}/{version}/revisions")
    def publish_workflow_revision(identity: str, version: str, body: DefinitionRevisionPayload):
        return workflow_definitions.revise(state, identity, version, **body.model_dump(), publish=True)

    @application.post("/api/workflow-definitions/{identity}/{version}/revisions/preview-resources")
    def preview_workflow_resources(identity: str, version: str, body: WorkflowRevisionCheckPayload):
        return workflow_definitions.revise(state, identity, version, **body.model_dump(), preview_resources=True)

    @application.post("/api/workflow-definitions/{identity}/{version}/files/read")
    def read_workflow_file(identity: str, version: str, body: DefinitionFilePayload):
        return workflow_definitions.read_file(state, identity, version, **body.model_dump())

    @application.get("/api/composition/presets")
    def composition_presets():
        return workflow_definitions.presets()

    @application.post("/api/composition/presets/{identity}/install")
    def install_composition_preset(identity: str):
        return workflow_definitions.install_preset(state, identity)

    @application.post("/api/composition/preview")
    def preview_composition(body: CompositionPreviewPayload):
        from ergora.interfaces import composition_preview

        return composition_preview.preview(state.root, body.id, body.version, body.grant, body.admission)

    @application.post("/api/composition/manifests")
    def freeze_composition(body: CompositionFreezePayload):
        return workflow_definitions.freeze_manifest(state.root, body.id, body.version, body.grant, body.preview_sha256)

    @application.get("/api/composition/manifests/{preview_sha256}")
    def frozen_composition(preview_sha256: str, material: bool = False):
        return workflow_definitions.frozen_manifest(state.root, preview_sha256, material=material)

    @application.post("/api/projects")
    def add_project(body: ProjectPayload):
        return projects.create(state, body.id, Path(body.repo))

    @application.post("/api/projects/{project_id}/handoff/evidence")
    def handoff_evidence(project_id: str, body: HandoffEvidencePayload):
        state.project(project_id)
        selected = handoff.evidence(Path(body.packet), body.selection, sha256=body.packet_sha256)
        if selected["index"]["project"] != project_id:
            raise ValueError("Handoff evidence belongs to a different project")
        return selected

    @application.post("/api/projects/{project_id}/retrospectives/skills/prepare")
    def prepare_skill_retrospective(project_id: str, body: SkillRetrospectivePreparePayload):
        return retrospectives.prepare(state, project_id, **body.arguments())

    @application.post("/api/projects/{project_id}/retrospectives/memories/prepare")
    def prepare_memory_retrospective(project_id: str, body: MemoryRetrospectivePreparePayload):
        return retrospectives.prepare_memory(state, project_id, **body.arguments())

    @application.post("/api/projects/{project_id}/retrospectives/workflows/prepare")
    def prepare_workflow_retrospective(project_id: str, body: WorkflowRetrospectivePreparePayload):
        return retrospectives.prepare_workflow(state, project_id, **body.arguments())

    @application.post("/api/projects/{project_id}/retrospectives/inputs/inspect")
    def inspect_retrospective_input(project_id: str, body: RetrospectiveInputPayload):
        state.project(project_id)
        return retrospectives.inspect_input(Path(body.directory), project_id=project_id)

    @application.post("/api/projects/{project_id}/retrospectives/skills/check")
    def check_skill_retrospective(project_id: str, body: RetrospectiveResultPayload):
        state.project(project_id)
        return retrospectives.check(project_id=project_id, **body.arguments())

    @application.post("/api/projects/{project_id}/retrospectives/memories/check")
    def check_memory_retrospective(project_id: str, body: RetrospectiveResultPayload):
        state.project(project_id)
        return retrospectives.check_memory(project_id=project_id, **body.arguments())

    @application.post("/api/projects/{project_id}/retrospectives/workflows/check")
    def check_workflow_retrospective(project_id: str, body: RetrospectiveResultPayload):
        state.project(project_id)
        return retrospectives.check_workflow(project_id=project_id, **body.arguments())

    @application.post("/api/projects/{project_id}/retrospectives/skills/export")
    def export_skill_retrospective(project_id: str, body: RetrospectiveExportPayload):
        state.project(project_id)
        return retrospectives.export(project_id=project_id, **body.arguments())

    @application.post("/api/projects/{project_id}/retrospectives/memories/export")
    def export_memory_retrospective(project_id: str, body: RetrospectiveExportPayload):
        state.project(project_id)
        return retrospectives.export_memory(project_id=project_id, **body.arguments())

    @application.post("/api/projects/{project_id}/retrospectives/workflows/export")
    def export_workflow_retrospective(project_id: str, body: RetrospectiveExportPayload):
        state.project(project_id)
        return retrospectives.export_workflow(project_id=project_id, **body.arguments())

    @application.post("/api/project-registrations")
    def register_project(body: RegistrationPayload):
        return registrations.register(state, body.definition, body.revision)

    @application.post("/api/project-registration-imports/preview")
    def preview_registration_import(body: RegistrationPayload):
        return registrations.preview_import(state, body.definition, body.revision)

    @application.post("/api/project-registration-imports")
    def apply_registration_import(body: RegistrationImportPayload):
        return registrations.apply_import(state, body.definition, body.revision, body.preview_sha256)

    @application.get("/api/projects/{project_id}/registration")
    def project_registration(project_id: str):
        return registrations.status(state, project_id)

    @application.post("/api/projects/{project_id}/registration/resume")
    def resume_registration(project_id: str, body: RegistrationRevisionPayload):
        return registrations.resume(state, project_id, body.revision)

    @application.get("/api/projects/{project_id}/dashboard")
    def dashboard(project_id: str):
        project = state.project(project_id)
        return {"project": project, "configuration": projects.effective_configuration(project),
                "tools": tools.doctor(state, project_id, project=project),
                "agent_runs": agent_runs.runs(state, project_id), "memories": memory.records(state, project_id),
                "skills": skill_assets.versions(state, project_id), "evaluations": evaluation.listing(state, project_id),
                "optimizations": optimization.listing(state, project_id), "research": research.listing(state, project_id),
                "drafts": drafts.listing(state, project_id), "kernel_runs": kernel.listing(state, project_id)}

    @application.get("/api/projects/{project_id}/configuration")
    def project_configuration(project_id: str):
        return projects.effective_configuration(state.project(project_id))

    @application.put("/api/projects/{project_id}/correction-suggestions")
    def set_correction_suggestions(project_id: str, body: CorrectionSuggestionsPayload):
        return projects.set_correction_suggestions(state, project_id, body.enabled, body.revision)

    @application.get("/api/projects/{project_id}/document-corrections/{proposal_id}")
    def inspect_document_correction(project_id: str, proposal_id: str):
        return document_corrections.inspect_proposal(state, project_id, proposal_id)

    @application.get("/api/projects/{project_id}/document-corrections/{proposal_id}/preview")
    def document_correction_preview(project_id: str, proposal_id: str,
                                    candidate_digest: Annotated[str, Query(pattern=r"^[a-f0-9]{64}$")]):
        preview = document_corrections.get_preview(state, project_id, proposal_id)
        if preview['candidate_digest'] != candidate_digest:
            raise ValueError('Document preview differs from the selected candidate digest')
        return preview

    @application.post("/api/projects/{project_id}/document-corrections/{proposal_id}/apply")
    def apply_document_correction(project_id: str, proposal_id: str, body: DocumentCorrectionApplyPayload):
        preview = document_corrections.get_preview(state, project_id, proposal_id)
        return document_corrections.apply(state, project_id, preview, **body.model_dump())

    @application.post("/api/projects/{project_id}/document-corrections/{proposal_id}/withdraw")
    def withdraw_document_correction(project_id: str, proposal_id: str, body: DocumentCorrectionWithdrawPayload):
        preview = document_corrections.get_preview(state, project_id, proposal_id)
        return document_corrections.withdraw(state, project_id, preview, reason=body.reason)

    @application.post("/api/projects/{project_id}/doctor")
    def probe_tools(project_id: str, body: DoctorPayload):
        return tools.doctor(state, project_id, probe=True, timeout=body.timeout)

    @application.get("/api/projects/{project_id}/tasks")
    def formal_tasks(project_id: str, limit: int = 50, after: str | None = None):
        return tasks.listing(state, project_id, limit=limit, after=after)

    @application.get("/api/projects/{project_id}/training")
    def training_experiments(project_id: str, limit: int = 50, after: str | None = None):
        return training.inspect(state, project_id, limit=limit, after=after)

    @application.get("/api/projects/{project_id}/training-cycles/{cycle_id}")
    def training_cycle_status(project_id: str, cycle_id: str, authorization_sha256: str | None = None):
        import ergora.training.cycles as training_cycles

        return training_cycles.status(state, project_id, cycle_id, authorization_sha256=authorization_sha256)

    @application.post("/api/projects/{project_id}/training/baseline-preview")
    def training_baseline_preview(project_id: str, body: TrainingBaselinePreviewPayload):
        return training.preview_baseline(state, project_id, body.baseline)

    @application.post("/api/projects/{project_id}/training/init-baseline")
    def training_baseline_init(project_id: str, body: TrainingBaselineInitPayload):
        return training.initialize_baseline(state, project_id, body.baseline, body.revision, body.baseline_sha256)

    @application.post("/api/projects/{project_id}/training/runner-preview")
    def training_runner_preview(project_id: str, body: TrainingRunnerPreviewPayload):
        return training.preview_runner(state, project_id, body.runner)

    @application.post("/api/projects/{project_id}/training/register-runner")
    def training_runner_registration(project_id: str, body: TrainingRunnerRegistrationPayload):
        return training.register_runner(state, project_id, body.runner, body.revision, body.runner_sha256)

    @application.post("/api/projects/{project_id}/training/experiment-preview")
    def training_experiment_preview(project_id: str, body: TrainingExperimentPreviewPayload):
        return training.preview_experiment(state, project_id, body.experiment, body.runner_template_id,
                                           max_run_seconds=body.max_run_seconds)

    @application.post("/api/projects/{project_id}/training/prepare")
    def training_prepare(project_id: str, body: TrainingPreparationPayload):
        return training.prepare_experiment(state, project_id, body.experiment, body.runner_template_id,
                  body.revision, body.preview_sha256, max_run_seconds=body.max_run_seconds)

    @application.get("/api/projects/{project_id}/training/{experiment_id}/preparation")
    def training_preparation(project_id: str, experiment_id: str):
        return training.preparation(state, project_id, experiment_id)

    @application.post("/api/projects/{project_id}/training/{experiment_id}/resume-prepare")
    def training_preparation_resume(project_id: str, experiment_id: str, body: TrainingPreparationResumePayload):
        return training.resume_prepare(state, project_id, experiment_id, body.revision, body.intent_sha256)

    @application.get("/api/projects/{project_id}/training/{experiment_id}")
    def training_experiment(project_id: str, experiment_id: str):
        return training.inspect(state, project_id, experiment_id)

    @application.get("/api/projects/{project_id}/training/{experiment_id}/status")
    def training_status(project_id: str, experiment_id: str, run_id: str | None = None, timeout: int = 20):
        return training.status(state, project_id, experiment_id, run_id=run_id, timeout=timeout)

    @application.get("/api/projects/{project_id}/training/{experiment_id}/evidence")
    def training_evidence(project_id: str, experiment_id: str, artifact: str | None = None,
                          evidence_sha256: str | None = None, screen_result_sha256: str | None = None,
                          offset: int = 0, limit: int = 12_000, retained_archive: bool = False):
        return training.evidence(state, project_id, experiment_id, artifact=artifact,
                                 evidence_sha256=evidence_sha256, screen_result_sha256=screen_result_sha256,
                                 offset=offset, limit=limit, retained_archive=retained_archive)

    @application.get("/api/projects/{project_id}/training/{experiment_id}/submission")
    def training_submission(project_id: str, experiment_id: str):
        return training.submission(state, project_id, experiment_id)

    @application.post("/api/projects/{project_id}/training/{experiment_id}/start")
    def training_start(project_id: str, experiment_id: str, body: TrainingStartPayload):
        return training.start(state, project_id, experiment_id, body.revision, body.manifest_sha256, timeout=body.timeout)

    @application.post("/api/projects/{project_id}/training/{experiment_id}/resume-start")
    def training_resume_start(project_id: str, experiment_id: str, body: TrainingResumeStartPayload):
        return training.resume_start(state, project_id, experiment_id, body.revision, body.intent_sha256, timeout=body.timeout)

    @application.get("/api/projects/{project_id}/training/{experiment_id}/approval")
    def training_approval(project_id: str, experiment_id: str):
        return training.approval(state, project_id, experiment_id)

    @application.post("/api/projects/{project_id}/training/{experiment_id}/approve")
    def training_approve(project_id: str, experiment_id: str, body: TrainingApprovalPayload):
        return training.approve(state, project_id, experiment_id, body.revision, run_id=body.run_id,
                               evidence_sha256=body.evidence_sha256, confirm=body.confirm, timeout=body.timeout)

    @application.post("/api/projects/{project_id}/training/{experiment_id}/resume-approve")
    def training_resume_approve(project_id: str, experiment_id: str, body: TrainingResumeApprovalPayload):
        return training.resume_approve(state, project_id, experiment_id, body.revision, body.intent_sha256,
                                      confirm=body.confirm, timeout=body.timeout)

    @application.get("/api/projects/{project_id}/training/{experiment_id}/cancellations/{request_id}")
    def training_cancellation(project_id: str, experiment_id: str, request_id: str):
        return training.cancellation(state, project_id, experiment_id, request_id)

    @application.post("/api/projects/{project_id}/training/{experiment_id}/cancel")
    def training_cancel(project_id: str, experiment_id: str, body: TrainingCancelPayload):
        return training.cancel(state, project_id, experiment_id, body.request_id, body.revision,
                               run_id=body.run_id, reason=body.reason, timeout=body.timeout)

    @application.post("/api/projects/{project_id}/training/{experiment_id}/resume-cancel")
    def training_resume_cancel(project_id: str, experiment_id: str, body: TrainingResumeCancelPayload):
        return training.resume_cancel(state, project_id, experiment_id, body.request_id, body.revision,
                                      body.intent_sha256, timeout=body.timeout)

    @application.get("/api/projects/{project_id}/training/{experiment_id}/stop-status")
    def training_stop_status(project_id: str, experiment_id: str, timeout: int = 20):
        return training.stop_status(state, project_id, experiment_id, timeout=timeout)

    @application.get("/api/projects/{project_id}/issues/{issue_id}")
    def project_issue(project_id: str, issue_id: str):
        return issues.show(state, project_id, issue_id)

    @application.post("/api/projects/{project_id}/issues/{issue_id}/snapshots")
    def capture_project_issue(project_id: str, issue_id: str, body: IssueCapturePayload):
        return issues.capture(state, project_id, issue_id, body.revision)

    @application.get("/api/projects/{project_id}/issue-snapshots")
    def saved_project_issues(project_id: str, limit: int = 50, after: str | None = None):
        return issues.snapshots(state, project_id, limit=limit, after=after)

    @application.get("/api/projects/{project_id}/issue-snapshots/{sha256}")
    def saved_project_issue(project_id: str, sha256: str):
        return issues.snapshot(state, project_id, sha256)

    @application.post("/api/projects/{project_id}/issue-links")
    def link_project_issue(project_id: str, body: IssueLinkPayload):
        return issues.link_task(state, project_id, body.snapshot_sha256, body.task_id,
                                body.creation_sha256, body.revision, body.reason)

    @application.get("/api/projects/{project_id}/issue-links")
    def project_issue_links(project_id: str, snapshot_sha256: str | None = None, task_id: str | None = None,
                            limit: int = 50, after: str | None = None):
        return issues.links(state, project_id, snapshot_sha256=snapshot_sha256, task_id=task_id,
                            limit=limit, after=after)

    @application.post("/api/projects/{project_id}/issue-writebacks")
    def prepare_issue_writeback(project_id: str, body: IssueWritebackPreparePayload):
        return issue_writebacks.prepare(state, project_id, body.task_id, body.revision,
                                        run_id=body.run_id, candidate_sha=body.candidate_sha)

    @application.post("/api/projects/{project_id}/issue-label-writebacks")
    def prepare_issue_label_writeback(project_id: str, body: IssueLabelPreparePayload):
        return issue_writebacks.prepare_label(state, project_id, body.task_id, body.revision,
            run_id=body.run_id, candidate_sha=body.candidate_sha, label_name=body.label_name)

    @application.post("/api/projects/{project_id}/candidate-observations")
    def observe_remote_candidate(project_id: str, body: IssueCandidateObservePayload):
        return issues.remote_candidate(state, project_id, body.task_id, body.revision,
            run_id=body.run_id, candidate_sha=body.candidate_sha, base_branch=body.base_branch)

    @application.post("/api/projects/{project_id}/candidate-review-links")
    def link_candidate_review(project_id: str, body: IssueReviewLinkPayload):
        return issues.link_review(state, project_id, body.task_id, body.revision,
            run_id=body.run_id, candidate_sha=body.candidate_sha, base_branch=body.base_branch,
            review_number=body.review_number, reason=body.reason)

    @application.get("/api/projects/{project_id}/candidate-review-links/{digest}")
    def saved_candidate_review(project_id: str, digest: str):
        return issues.review_link(state, project_id, digest)

    @application.get("/api/projects/{project_id}/issue-writebacks/{digest}")
    def saved_issue_writeback(project_id: str, digest: str):
        return issue_writebacks.status(state, project_id, digest)

    @application.post("/api/projects/{project_id}/issue-writebacks/{digest}/send")
    def send_issue_writeback(project_id: str, digest: str, body: IssueWritebackSendPayload):
        return issue_writebacks.send(state, project_id, digest, body.revision, confirm=body.confirm)

    @application.post("/api/projects/{project_id}/issue-writebacks/{digest}/observe")
    def observe_issue_writeback(project_id: str, digest: str, body: IssueWritebackObservePayload):
        return issue_writebacks.observe(state, project_id, digest,
            comment_id=body.comment_id, page=body.page, cursor=body.cursor)

    @application.post("/api/projects/{project_id}/tasks/prepare")
    def prepare_formal_task(project_id: str, body: TaskDefinitionPayload):
        return tasks.prepare(state, project_id, body.definition, body.revision)

    @application.get("/api/projects/{project_id}/tasks/{task_id}/preparation")
    def formal_task_preparation(project_id: str, task_id: str,
                                prepare_sha256: str | None = None, preview_sha256: str | None = None):
        if prepare_sha256 is not None or preview_sha256 is not None:
            if prepare_sha256 is None or preview_sha256 is None:
                raise ValueError("Select both the original preparation and prepared preview digests")
            return tasks.preparation_readiness(state, project_id, task_id,
                prepare_sha256=prepare_sha256, preview_sha256=preview_sha256)
        return tasks.preparation(state, project_id, task_id)

    @application.post("/api/projects/{project_id}/tasks/preview")
    def preview_formal_task(project_id: str, body: TaskDefinitionPayload):
        snapshot = tasks.preview(state, project_id, body.definition, body.revision)
        if snapshot["status"] == "preview":
            document = snapshot["files"]["task.spec.json"]
            if "context" in document:
                snapshot["selected_context"] = task_envelopes.selected_context(document)
        return snapshot

    @application.post("/api/projects/{project_id}/tasks")
    def create_formal_task(project_id: str, body: TaskCreationPayload):
        return tasks.create(state, project_id, body.definition, body.revision, body.preview_sha256,
                            prepare_sha256=body.prepare_sha256)

    @application.get("/api/projects/{project_id}/tasks/{task_id}/creation")
    def formal_task_creation(project_id: str, task_id: str):
        return tasks.creation(state, project_id, task_id)

    @application.get("/api/projects/{project_id}/tasks/{task_id}/status")
    def formal_task_status(project_id: str, task_id: str, run_id: str | None = None, timeout: int = 20):
        return tasks.status(state, project_id, task_id, run_id=run_id, timeout=timeout)

    @application.get("/api/projects/{project_id}/tasks/{task_id}/plan")
    def formal_task_plan(project_id: str, task_id: str, run_id: str, plan_sha256: str, timeout: int = 20):
        return tasks.plan(state, project_id, task_id, run_id=run_id, plan_sha256=plan_sha256, timeout=timeout)

    @application.get("/api/projects/{project_id}/tasks/{task_id}/events")
    def formal_task_events(project_id: str, task_id: str, run_id: str, limit: int = 20,
                           after: str | None = None, timeout: int = 20):
        return tasks.events(state, project_id, task_id, run_id=run_id, limit=limit, after=after, timeout=timeout)

    @application.get("/api/projects/{project_id}/tasks/{task_id}/jobs/{event_id}")
    def formal_task_job(project_id: str, task_id: str, event_id: int, run_id: str,
                        artifact: str | None = None, receipt_sha256: str | None = None,
                        offset: int = 0, limit: int = 8192, timeout: int = 20):
        return tasks.job(state, project_id, task_id, run_id=run_id, event_id=event_id,
                         artifact=artifact, receipt_sha256=receipt_sha256, offset=offset,
                         limit=limit, timeout=timeout)

    @application.get("/api/projects/{project_id}/tasks/{task_id}/external-status")
    def formal_task_external_status(project_id: str, task_id: str, run_id: str, timeout: int = 20):
        return tasks.external_status(state, project_id, task_id, run_id=run_id, timeout=timeout)

    @application.get("/api/projects/{project_id}/tasks/{task_id}/evidence")
    def formal_task_evidence(project_id: str, task_id: str, run_id: str, timeout: int = 20):
        return tasks.evidence(state, project_id, task_id, run_id=run_id, timeout=timeout)

    @application.get("/api/projects/{project_id}/campaigns/{campaign_id}/tasks/{task_id}/timeline")
    async def campaign_task_timeline(project_id: str, campaign_id: str, task_id: str):
        reader = State(state.root, read_only=True)
        observed = await campaigns.status(reader, project_id, campaign_id, online=True, task_id=task_id)
        fields = ("project", "campaign", "project_revision", "operator_euid", "plan_sha256",
                  "attempt_sha256", "result_saved", "workflow_id", "run_id", "current_run_id",
                  "remote_status", "remote_error", "temporal_status", "workflow_state_status",
                  "task_observation_history_status", "task_observation_history_error", "task_evidence")
        plan = observed["plan"]
        selected = tasks_by_id(observed)[task_id]
        task_states = observed.get("tasks", {})
        task_state = task_states.get(task_id)
        direct_dependencies = []
        for dependency_id in selected["depends_on"]:
            dependency = task_states.get(dependency_id, {})
            source = dependency.get("state_source")
            if source is None:
                source = "workflow" if dependency and observed["workflow_state_status"] == "observed" else "unavailable"
            direct_dependencies.append({"task_id": dependency_id, "state_source": source,
                                        "status": dependency.get("status") if source != "unavailable" else None})
        training_task = {}
        if training_readback_task(selected):
            training_task = {"task_id": task_id, "depends_on": selected["depends_on"],
                             "locator": selected["source"]["locator"]}
            if training_screen_task(selected) or training_gpu_release_task(selected):
                training_task["source_kind"] = selected["source"]["kind"]
            if task_state is not None:
                task_state = {key: task_state[key] for key in ("status", "eligible", "readback_observation", "state_source")
                              if key in task_state}
            if "recipient" in selected and "recipient" in observed:
                training_task["recipient"] = _training_timeline_recipient(observed["recipient"])
        stop = observed["stop"]
        stop_receipt = stop["receipt"] or {}
        rollover = observed.get("rollover")
        assignment = observed.get("assignment")
        assignment_evidence = (_assignment_timeline(assignment) if assignment is not None
                               and assignment["waiting_task_id"] == task_id else None)
        completion = observed.get("readback_completion")
        if completion is not None and completion.get("task_id") == task_id:
            completion = {name: value for name, value in completion.items() if name != "recipient"}
        else:
            completion = None
        terminal_evidence = {}
        if training_task:
            for name in ("readback_terminal", "readback_followup_terminal"):
                terminal = observed.get(name)
                if terminal is not None and terminal.get("task_id") == task_id:
                    terminal_evidence[name] = terminal
        return {**{name: observed[name] for name in fields if name in observed},
                "acceptance": plan["acceptance"], "expires_at": plan["limits"]["expires_at"],
                "workflow_phase": observed.get("workflow_state", {}).get("phase"),
                "task_state": task_state,
                **({"direct_dependencies": direct_dependencies} if direct_dependencies else {}),
                **({"training_task": training_task} if training_task else {}),
                **({"assignment": assignment_evidence} if assignment_evidence is not None else {}),
                **terminal_evidence,
                "stop": {"status": stop["status"], "remote_status": stop["remote_status"],
                         "update_id": stop["update_id"], "local_fence_saved": stop.get("local_fence_saved"),
                         "decision": stop_receipt.get("decision"), "receipt_run_id": stop_receipt.get("run_id")},
                "rollover": {"status": rollover["status"], "update_id": rollover["update_id"]} if rollover else None,
                "task_observation_history": observed.get("task_observation_history", {}).get(task_id, {}),
                "readback_completion": completion}

    @application.post("/api/projects/{project_id}/tasks/{task_id}/handoff")
    def download_formal_task_handoff(project_id: str, task_id: str, body: TaskHandoffPayload):
        with tempfile.TemporaryDirectory(prefix='ergora-handoff-') as directory:
            output = Path(directory) / 'handoff.zip'
            metadata = tasks.handoff(state, project_id, task_id, run_id=body.run_id,
                                     output=output, timeout=body.timeout)
            with output.open('rb') as stream:
                raw = stream.read(handoff.PACKET_LIMIT + 1)
            if len(raw) > handoff.PACKET_LIMIT:
                raise ValueError('Handoff download exceeds 72 MiB')
            digest = hashlib.sha256(raw).hexdigest()
            if digest != metadata['sha256']:
                raise ValueError('Handoff download bytes changed after collection')
        return Response(raw, media_type='application/zip', headers={
            'Content-Disposition': 'attachment; filename="ergora-handoff.zip"',
            'X-Ergora-Handoff-SHA256': digest})

    @application.get("/api/projects/{project_id}/tasks/{task_id}/reconciliation")
    def formal_task_reconciliation(project_id: str, task_id: str):
        return tasks.reconciliation(state, project_id, task_id)

    @application.post("/api/projects/{project_id}/tasks/{task_id}/reconcile")
    def reconcile_formal_task(project_id: str, task_id: str, body: TaskRunDecisionPayload):
        return tasks.reconcile(state, project_id, task_id, body.revision,
                               run_id=body.run_id, confirm=body.confirm, timeout=body.timeout)

    @application.post("/api/projects/{project_id}/tasks/{task_id}/resume-reconcile")
    def resume_formal_task_reconciliation(project_id: str, task_id: str, body: TaskResumeDecisionPayload):
        return tasks.resume_reconcile(state, project_id, task_id, body.revision,
                                      body.intent_sha256, confirm=body.confirm, timeout=body.timeout)

    @application.post("/api/projects/{project_id}/tasks/{task_id}/resume-create")
    def resume_formal_task_creation(project_id: str, task_id: str, body: TaskResumePayload):
        return tasks.resume_create(state, project_id, task_id, body.revision, body.intent_sha256)

    @application.post("/api/projects/{project_id}/tasks/{task_id}/start")
    def start_formal_task(project_id: str, task_id: str, body: TaskStartPayload):
        return tasks.start(state, project_id, task_id, body.revision, body.creation_sha256, timeout=body.timeout)

    @application.get("/api/projects/{project_id}/tasks/{task_id}/submission")
    def formal_task_submission(project_id: str, task_id: str):
        return tasks.submission(state, project_id, task_id)

    @application.post("/api/projects/{project_id}/tasks/{task_id}/resume-start")
    def resume_formal_task_start(project_id: str, task_id: str, body: TaskResumeStartPayload):
        return tasks.resume_start(state, project_id, task_id, body.revision, body.intent_sha256, timeout=body.timeout)

    @application.get("/api/projects/{project_id}/tasks/{task_id}/approvals")
    def formal_task_approval_records(project_id: str, task_id: str,
                                     run_id: Annotated[str, Query(min_length=1, max_length=128)]):
        return tasks.approval_records(state, project_id, task_id, run_id=run_id)

    @application.get("/api/projects/{project_id}/tasks/{task_id}/approvals/{decision_id}")
    def formal_task_approval(project_id: str, task_id: str, decision_id: str):
        return tasks.approval(state, project_id, task_id, decision_id)

    @application.post("/api/projects/{project_id}/tasks/{task_id}/approvals/{decision_id}")
    def approve_formal_task(project_id: str, task_id: str, decision_id: str, body: TaskApprovePayload):
        return tasks.approve(state, project_id, task_id, decision_id, body.revision,
                             run_id=body.run_id, plan_sha256=body.plan_sha256, confirm=body.confirm, timeout=body.timeout)

    @application.post("/api/projects/{project_id}/tasks/{task_id}/approvals/{decision_id}/resume")
    def resume_formal_task_approval(project_id: str, task_id: str, decision_id: str, body: TaskResumeDecisionPayload):
        return tasks.resume_approve(state, project_id, task_id, decision_id, body.revision,
                                    body.intent_sha256, confirm=body.confirm, timeout=body.timeout)

    @application.get("/api/projects/{project_id}/tasks/{task_id}/work-priority/{decision_id}")
    def formal_task_work_priority(project_id: str, task_id: str, decision_id: WorkPriorityDecisionId,
                                  run_id: Annotated[str, Query(min_length=1, max_length=128)],
                                  timeout: Annotated[int, Query(ge=1, le=60)] = 20):
        return tasks.work_priority(state, project_id, task_id, decision_id, run_id=run_id, timeout=timeout)

    @application.post("/api/projects/{project_id}/tasks/{task_id}/work-priority/{decision_id}")
    def prioritize_formal_task_work(project_id: str, task_id: str, decision_id: WorkPriorityDecisionId,
                                    body: TaskWorkPriorityPayload):
        return tasks.prioritize_work_unit(state, project_id, task_id, body.work_unit_id, body.revision,
                                          run_id=body.run_id, plan_sha256=body.plan_sha256, decision_id=decision_id,
                                          confirm=body.confirm, timeout=body.timeout)

    @application.get("/api/projects/{project_id}/tasks/{task_id}/cancellations/{request_id}")
    def formal_task_cancellation(project_id: str, task_id: str, request_id: str):
        return tasks.cancellation(state, project_id, task_id, request_id)

    @application.post("/api/projects/{project_id}/tasks/{task_id}/cancellations/{request_id}")
    def cancel_formal_task(project_id: str, task_id: str, request_id: str, body: TaskCancelPayload):
        return tasks.cancel(state, project_id, task_id, request_id, body.revision,
                            run_id=body.run_id, reason=body.reason, confirm=body.confirm, timeout=body.timeout)

    @application.post("/api/projects/{project_id}/tasks/{task_id}/cancellations/{request_id}/resume")
    def resume_formal_task_cancellation(project_id: str, task_id: str, request_id: str, body: TaskResumeDecisionPayload):
        return tasks.resume_cancel(state, project_id, task_id, request_id, body.revision,
                                   body.intent_sha256, confirm=body.confirm, timeout=body.timeout)

    @application.get("/api/projects/{project_id}/tasks/{task_id}/export")
    def formal_task_export(project_id: str, task_id: str):
        return tasks.export_status(state, project_id, task_id)

    @application.post("/api/projects/{project_id}/tasks/{task_id}/export")
    def export_formal_task(project_id: str, task_id: str, body: TaskExportPayload):
        return tasks.export(state, project_id, task_id, body.revision, run_id=body.run_id,
                            candidate_sha=body.candidate_sha, branch=body.branch,
                            confirm=body.confirm, timeout=body.timeout)

    @application.post("/api/projects/{project_id}/tasks/{task_id}/export/resume")
    def resume_formal_task_export(project_id: str, task_id: str, body: TaskResumeDecisionPayload):
        return tasks.resume_export(state, project_id, task_id, body.revision, body.intent_sha256,
                                   confirm=body.confirm, timeout=body.timeout)

    @application.get("/api/projects/{project_id}/tasks/{task_id}")
    def formal_task(project_id: str, task_id: str):
        snapshot = tasks.show(state, project_id, task_id)
        document = snapshot.get("admission_envelope", {})
        if "context" in document:
            snapshot["selected_context"] = task_envelopes.selected_context(document)
        return snapshot

    @application.get("/api/projects/{project_id}/services")
    def service_status(project_id: str):
        return services.status(state, project_id)

    @application.post("/api/projects/{project_id}/services")
    def control_services(project_id: str, body: ServicesPayload):
        return services.control(state, project_id, body.action, body.names, body.revision,
                                confirm=body.confirm, timeout=body.timeout)

    @application.get("/api/projects/{project_id}/services/{name}/logs")
    def service_logs(project_id: str, name: str, offset: int = 0, limit: int = 8192, stderr: bool = False):
        return services.logs(state, project_id, name, offset=offset, limit=limit, stderr=stderr)

    @application.put("/api/projects/{project_id}/bindings/{layer}")
    def bind(project_id: str, layer: str, body: BindingPayload):
        return projects.bind(state, project_id, layer, body.binding, body.revision)

    @application.post("/api/projects/{project_id}/agent-runs")
    def agent_run(project_id: str, body: AgentPayload):
        return agent_runs.run_agent(state, project_id, body.role, body.prompt, body.timeout, body.skills, body.recall, body.template,
                                    session_intent=body.session_intent, expected_revision=body.expected_revision,
                                    codex_config=Path(body.codex_config) if body.codex_config is not None else None)

    @application.get("/api/projects/{project_id}/agent-runs")
    def list_agent_runs(project_id: str):
        return agent_runs.runs(state, project_id)

    @application.get("/api/projects/{project_id}/agent-sessions")
    def list_agent_sessions(project_id: str, after: Annotated[int, Query(ge=0)] = 0,
                            limit: Annotated[int, Query(ge=1, le=100)] = 20, intent_id: str | None = None):
        return agent_runs.sessions(state, project_id, after=after, limit=limit, intent_id=intent_id)

    @application.get("/api/projects/{project_id}/agent-sessions/{session_id}")
    def inspect_agent_session(project_id: str, session_id: str, after: Annotated[int, Query(ge=0)] = 0,
                              limit: Annotated[int, Query(ge=1, le=100)] = 20):
        return agent_runs.inspect_session(state, project_id, session_id, after=after, limit=limit)

    @application.get("/api/projects/{project_id}/agent-sessions/{session_id}/continuations/{intent_id}")
    def inspect_agent_continuation(project_id: str, session_id: str, intent_id: str, parent_run_id: str):
        return agent_runs.continuation_receipt(state, project_id, session_id, parent_run_id, intent_id)

    @application.post("/api/projects/{project_id}/agent-sessions/{session_id}/continue")
    def continue_agent_session(project_id: str, session_id: str, body: AgentContinuePayload):
        return agent_runs.continue_session(state, project_id, session_id, body.parent_run_id, body.prompt,
                                           expected_revision=body.expected_revision, intent_id=body.intent_id, timeout=body.timeout)

    @application.post("/api/projects/{project_id}/agent-sessions/{session_id}/stop")
    def stop_agent_session(project_id: str, session_id: str, body: AgentStopPayload):
        return agent_runs.stop_session(state, project_id, session_id, body.run_id, intent_id=body.intent_id)

    @application.post("/api/projects/{project_id}/composition-inputs/check")
    def check_composition_input(project_id: str, body: CompositionInputPayload):
        return agent_runs.check_input(state, project_id, mode="text-only", **body.arguments())

    @application.post("/api/projects/{project_id}/composition-inputs/run")
    def run_composition_input(project_id: str, body: CompositionRunPayload):
        return agent_runs.run_input(state, project_id, mode="text-only", **body.arguments())

    @application.post("/api/projects/{project_id}/kernel-runs")
    def kernel_create(project_id: str, body: KernelPayload):
        return kernel.create(state, project_id, body.action, body.timeout)

    @application.post("/api/projects/{project_id}/kernel-runs/{run_id}")
    def kernel_operate(project_id: str, run_id: str, body: KernelPayload):
        return kernel.operate(state, project_id, run_id, body.action, body.timeout, body.reconcile_reason)

    @application.get("/api/projects/{project_id}/agent-runs/{run_id}/output")
    def agent_output(project_id: str, run_id: str, native_history: bool = False,
                     history_offset: int = 0, history_limit: int = 65536, history_revision: str | None = None):
        return agent_runs.output(state, project_id, run_id, native_history=native_history,
                                 offset=history_offset, limit=history_limit, revision=history_revision)

    @application.post("/api/projects/{project_id}/memories")
    def save_memory(project_id: str, body: MemoryPayload):
        return memory.save(state, project_id, body.text, body.source, body.id, body.revision,
                           **body.model_dump(include={"expires_at"}, exclude_unset=True))

    @application.get("/api/projects/{project_id}/memory-catalog")
    def memory_catalog(project_id: str):
        return memory.catalog(state, project_id)

    @application.delete("/api/projects/{project_id}/memories/{memory_id}")
    def delete_memory(project_id: str, memory_id: str, body: RevisionPayload):
        return memory.delete(state, project_id, memory_id, body.revision)

    @application.get("/api/projects/{project_id}/memories/{memory_id}/history")
    def memory_history(project_id: str, memory_id: str):
        return memory.history(state, project_id, memory_id)

    @application.post("/api/projects/{project_id}/memories/{memory_id}/restore")
    def restore_memory(project_id: str, memory_id: str, body: RestorePayload):
        return memory.restore(state, project_id, memory_id, body.from_revision, body.revision)

    @application.post("/api/projects/{project_id}/memory-sync")
    def sync_memory(project_id: str, rebuild: bool = False):
        return memory.sync(state, project_id, rebuild)

    @application.get("/api/projects/{project_id}/memory-search")
    def search_memory(project_id: str, query: str):
        return memory.search(state, project_id, query)

    @application.get("/api/projects/{project_id}/skills/heads")
    def skill_heads(project_id: str):
        return skill_assets.versions(state, project_id, heads_only=True)

    @application.post("/api/projects/{project_id}/skills/import")
    def import_skill(project_id: str, body: ImportPayload):
        return skill_assets.import_bundle(state, project_id, Path(body.directory), body.hypothesis)

    @application.get("/api/projects/{project_id}/skills/diff")
    def skill_diff(project_id: str, baseline: str, candidate: str):
        return skill_assets.diff(state, project_id, baseline, candidate)

    @application.post("/api/projects/{project_id}/skills/adopt")
    def adopt_skill(project_id: str, body: AdoptPayload):
        return skills.adopt(state, project_id, body.baseline_run, body.candidate_run, body.revision, body.reason)

    @application.post("/api/projects/{project_id}/skills/rollback")
    def rollback_skill(project_id: str, body: RollbackPayload):
        return skill_assets.rollback(state, project_id, body.name, body.digest, body.revision, body.reason)

    @application.post("/api/projects/{project_id}/evaluations/suites")
    def register_suite(project_id: str, body: dict = Body(...)):
        return evaluation.register(state, project_id, body)

    @application.post("/api/projects/{project_id}/evaluations/run")
    def run_evaluation(project_id: str, body: EvaluationPayload):
        return evaluation.evaluate(state, project_id, body.digest, body.suite)

    @application.get("/api/projects/{project_id}/evaluations/compare")
    def compare_evaluations(project_id: str, baseline: str, candidate: str):
        return evaluation.compare(state, project_id, baseline, candidate)

    @application.post("/api/projects/{project_id}/optimizations")
    def optimize_skill(project_id: str, body: OptimizePayload):
        return optimization.optimize(state, project_id, body.baseline, body.suite, body.objective,
                                     body.max_evaluations, body.max_proposals, body.timeout)

    @application.post("/api/projects/{project_id}/research-runs")
    def observe_sources(project_id: str, body: ResearchPayload):
        return research.run(state, project_id, body.urls, body.max_bytes, body.timeout, body.allow_private, body.id)

    @application.post("/api/projects/{project_id}/research-runs/{run_id}/cancel")
    def cancel_research(project_id: str, run_id: str):
        return research.cancel(state, project_id, run_id)

    @application.get("/api/projects/{project_id}/research-proposals/{proposal_id}")
    def source_proposal(project_id: str, proposal_id: str):
        return research.proposal(state, project_id, proposal_id)

    @application.post("/api/projects/{project_id}/research-proposals/{proposal_id}/review")
    def review_source(project_id: str, proposal_id: str, body: ReviewPayload):
        return research.review(state, project_id, proposal_id, body.status, body.revision, body.reason)

    @application.get("/api/templates/{kind}")
    def template(kind: str):
        return native_resources.template_details(kind)

    @application.post("/api/projects/{project_id}/drafts/validate")
    def validate_draft(project_id: str, body: DraftPayload):
        state.project(project_id)
        return native_compiler.validate_input(body.kind, body.input)

    @application.post("/api/projects/{project_id}/drafts")
    def save_draft(project_id: str, body: DraftPayload):
        return drafts.save(state, project_id, body.id, body.kind, body.input, body.revision)

    return application
