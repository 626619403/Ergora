"""Local control plane. All state transitions use the same application functions as the CLI."""

import hashlib
import sys
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import Body, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import __version__, agent_definitions, agent_runs, components, drafts, evaluation, handoff, kernel, memory, optimization, projects, reference, registrations, research, services, tasks, skill_assets, skills, tools, workflow_definitions
from .state import State


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectPayload(Payload):
    id: str
    repo: str


class BindingPayload(Payload):
    binding: dict
    revision: int


class RevisionPayload(Payload):
    revision: int


class DefinitionRevisionPayload(Payload):
    base_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    definition: dict


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


class TaskCreationPayload(TaskDefinitionPayload):
    preview_sha256: str = Field(pattern="^[0-9a-f]{64}$")


class TaskResumePayload(Payload):
    revision: int = Field(strict=True, ge=1)
    intent_sha256: str = Field(pattern="^[0-9a-f]{64}$")


class TaskStartPayload(Payload):
    revision: int = Field(strict=True, ge=1)
    creation_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    timeout: int = Field(default=20, strict=True, ge=1, le=60)


class TaskResumeStartPayload(TaskResumePayload):
    timeout: int = Field(default=20, strict=True, ge=1, le=60)


class TaskRunDecisionPayload(Payload):
    revision: int = Field(strict=True, ge=1)
    run_id: str = Field(min_length=1, max_length=128)
    confirm: bool = Field(strict=True)
    timeout: int = Field(default=20, strict=True, ge=1, le=60)


class TaskApprovePayload(TaskRunDecisionPayload):
    plan_sha256: str = Field(pattern="^[0-9a-f]{64}$")


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
    timeout: int = 300
    skills: list[str] = Field(default_factory=list)
    recall: str | None = None
    template: str | None = None


class KernelPayload(Payload):
    action: str = "plan"
    timeout: int = 30
    reconcile_reason: str | None = None


class DraftPayload(RevisionPayload):
    id: str
    kind: str
    input: dict


class CompositionPreviewPayload(Payload):
    id: str
    version: str
    grant: dict


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

    @application.exception_handler(ValueError)
    @application.exception_handler(OSError)
    async def application_error(request, error):
        return JSONResponse({"error": str(error)}, status_code=400)

    console = Path(__file__).parent / "data/console"
    application.mount("/assets", StaticFiles(directory=console), name="assets")

    @application.get("/")
    def index():
        return FileResponse(console / "index.html")

    @application.get("/api/bootstrap")
    def bootstrap():
        return {"version": __version__, "projects": projects.list_projects(state), "tools": tools.catalog(),
                "layers": components.LAYERS,
                "templates": list(reference.TEMPLATES), "agent_contracts": {kind: reference.agent_contract(kind) for kind in reference.TEMPLATES},
                "platform": sys.platform, "state_directory": str(state.root),
                "reference_supported": sys.platform == "linux",
                "boundary": "local trusted-user control plane"}

    @application.get("/api/installation-profiles")
    def installation_profiles():
        return tools.installation_profiles()

    @application.get("/api/agent-definitions")
    def agent_library(role: str | None = None, specialty: str | None = None):
        return agent_definitions.definitions(state, role=role, specialty=specialty)

    @application.get("/api/agent-definitions/{identity}/{version}")
    def agent_definition(identity: str, version: str):
        return agent_definitions.get(state, identity, version, material=True)

    @application.post("/api/agent-definitions/{identity}/{version}/revisions/check")
    def check_agent_revision(identity: str, version: str, body: DefinitionRevisionPayload):
        return agent_definitions.revise(state, identity, version, body.base_digest, body.definition)

    @application.post("/api/agent-definitions/{identity}/{version}/revisions")
    def publish_agent_revision(identity: str, version: str, body: DefinitionRevisionPayload):
        return agent_definitions.revise(state, identity, version, body.base_digest, body.definition, publish=True)

    @application.get("/api/workflow-definitions")
    def workflow_library():
        return workflow_definitions.definitions(state)

    @application.get("/api/workflow-definitions/{identity}/{version}")
    def workflow_definition(identity: str, version: str):
        return workflow_definitions.get(state, identity, version, material=True)

    @application.post("/api/workflow-definitions/{identity}/{version}/revisions/check")
    def check_workflow_revision(identity: str, version: str, body: DefinitionRevisionPayload):
        return workflow_definitions.revise(state, identity, version, body.base_digest, body.definition)

    @application.post("/api/workflow-definitions/{identity}/{version}/revisions")
    def publish_workflow_revision(identity: str, version: str, body: DefinitionRevisionPayload):
        return workflow_definitions.revise(state, identity, version, body.base_digest, body.definition, publish=True)

    @application.get("/api/composition/presets")
    def composition_presets():
        return workflow_definitions.presets()

    @application.post("/api/composition/presets/{identity}/install")
    def install_composition_preset(identity: str):
        return workflow_definitions.install_preset(state, identity)

    @application.post("/api/composition/preview")
    def preview_composition(body: CompositionPreviewPayload):
        return workflow_definitions.preview(state.root, body.id, body.version, body.grant)

    @application.post("/api/projects")
    def add_project(body: ProjectPayload):
        return projects.create(state, body.id, Path(body.repo))

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

    @application.post("/api/projects/{project_id}/doctor")
    def probe_tools(project_id: str, body: DoctorPayload):
        return tools.doctor(state, project_id, probe=True, timeout=body.timeout)

    @application.get("/api/projects/{project_id}/tasks")
    def formal_tasks(project_id: str, limit: int = 50, after: str | None = None):
        return tasks.listing(state, project_id, limit=limit, after=after)

    @application.post("/api/projects/{project_id}/tasks/preview")
    def preview_formal_task(project_id: str, body: TaskDefinitionPayload):
        return tasks.preview(state, project_id, body.definition, body.revision)

    @application.post("/api/projects/{project_id}/tasks")
    def create_formal_task(project_id: str, body: TaskCreationPayload):
        return tasks.create(state, project_id, body.definition, body.revision, body.preview_sha256)

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
        return tasks.show(state, project_id, task_id)

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
        return agent_runs.run_agent(state, project_id, body.role, body.prompt, body.timeout, body.skills, body.recall, body.template)

    @application.post("/api/projects/{project_id}/kernel-runs")
    def kernel_create(project_id: str, body: KernelPayload):
        return kernel.create(state, project_id, body.action, body.timeout)

    @application.post("/api/projects/{project_id}/kernel-runs/{run_id}")
    def kernel_operate(project_id: str, run_id: str, body: KernelPayload):
        return kernel.operate(state, project_id, run_id, body.action, body.timeout, body.reconcile_reason)

    @application.get("/api/projects/{project_id}/agent-runs/{run_id}/output")
    def agent_output(project_id: str, run_id: str):
        return agent_runs.output(state, project_id, run_id)

    @application.post("/api/projects/{project_id}/memories")
    def save_memory(project_id: str, body: MemoryPayload):
        return memory.save(state, project_id, body.text, body.source, body.id, body.revision)

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
        return reference.template_details(kind)

    @application.post("/api/projects/{project_id}/drafts/validate")
    def validate_draft(project_id: str, body: DraftPayload):
        state.project(project_id)
        return reference.validate_input(body.kind, body.input)

    @application.post("/api/projects/{project_id}/drafts")
    def save_draft(project_id: str, body: DraftPayload):
        return drafts.save(state, project_id, body.id, body.kind, body.input, body.revision)

    return application
