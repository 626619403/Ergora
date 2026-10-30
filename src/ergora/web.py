"""Local control plane. All state transitions use the same application functions as the CLI."""

import difflib
import json
from pathlib import Path
from typing import Literal

from fastapi import Body, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import __version__, drafts, evaluation, kernel, memory, optimization, projects, reference, research, skills, tools
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
                "templates": list(reference.TEMPLATES), "agent_contracts": {kind: reference.agent_contract(kind) for kind in reference.TEMPLATES},
                "boundary": "local trusted-user control plane"}

    @application.post("/api/projects")
    def add_project(body: ProjectPayload):
        return projects.create(state, body.id, Path(body.repo))

    @application.get("/api/projects/{project_id}/dashboard")
    def dashboard(project_id: str):
        return {"project": state.project(project_id), "tools": tools.doctor(state, project_id),
                "agent_runs": tools.runs(state, project_id), "memories": memory.records(state, project_id),
                "skills": skills.versions(state, project_id), "evaluations": evaluation.listing(state, project_id),
                "optimizations": optimization.listing(state, project_id), "research": research.listing(state, project_id),
                "drafts": drafts.listing(state, project_id), "kernel_runs": kernel.listing(state, project_id)}

    @application.put("/api/projects/{project_id}/bindings/{layer}")
    def bind(project_id: str, layer: str, body: BindingPayload):
        return projects.bind(state, project_id, layer, body.binding, body.revision)

    @application.post("/api/projects/{project_id}/agent-runs")
    def agent_run(project_id: str, body: AgentPayload):
        return tools.run_agent(state, project_id, body.role, body.prompt, body.timeout, body.skills, body.recall, body.template)

    @application.post("/api/projects/{project_id}/kernel-runs")
    def kernel_create(project_id: str, body: KernelPayload):
        return kernel.create(state, project_id, body.action, body.timeout)

    @application.post("/api/projects/{project_id}/kernel-runs/{run_id}")
    def kernel_operate(project_id: str, run_id: str, body: KernelPayload):
        return kernel.operate(state, project_id, run_id, body.action, body.timeout, body.reconcile_reason)

    @application.get("/api/projects/{project_id}/agent-runs/{run_id}/output")
    def agent_output(project_id: str, run_id: str):
        return tools.output(state, project_id, run_id)

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
        return skills.import_bundle(state, project_id, Path(body.directory), body.hypothesis)

    @application.get("/api/projects/{project_id}/skills/diff")
    def skill_diff(project_id: str, baseline: str, candidate: str):
        before, after = skills.get(state, project_id, baseline), skills.get(state, project_id, candidate)
        before_text = (Path(before["path"]) / "SKILL.md").read_text()
        after_text = (Path(after["path"]) / "SKILL.md").read_text()
        changed = [name for name in sorted(set(before["files"]) | set(after["files"])) if before["files"].get(name) != after["files"].get(name)]
        return {"diff": "".join(difflib.unified_diff(before_text.splitlines(True), after_text.splitlines(True), fromfile=baseline[:12], tofile=candidate[:12])),
                "changed_files": changed, "baseline": before, "candidate": after}

    @application.post("/api/projects/{project_id}/skills/adopt")
    def adopt_skill(project_id: str, body: AdoptPayload):
        return skills.adopt(state, project_id, body.baseline_run, body.candidate_run, body.revision, body.reason)

    @application.post("/api/projects/{project_id}/skills/rollback")
    def rollback_skill(project_id: str, body: RollbackPayload):
        return skills.rollback(state, project_id, body.name, body.digest, body.revision, body.reason)

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
        if kind not in reference.TEMPLATES:
            raise ValueError("Unknown template")
        if kind == "training-optimization":
            directory = reference.ROOT / "platform/templates" / kind
            return {"kind": kind, "agents": reference.agent_contract(kind),
                    "files": {**{path.name: path.read_text() for path in sorted(directory.iterdir()) if path.is_file()},
                              "agent-contract.json": json.dumps(reference.agent_contract(kind), ensure_ascii=False, indent=2)}}
        return {"kind": kind, "agents": reference.agent_contract(kind),
                "input": json.loads((reference.ROOT / "platform/templates" / kind / "input.json").read_text())}

    @application.post("/api/projects/{project_id}/drafts/validate")
    def validate_draft(project_id: str, body: DraftPayload):
        state.project(project_id)
        return reference.validate_input(body.kind, body.input)

    @application.post("/api/projects/{project_id}/drafts")
    def save_draft(project_id: str, body: DraftPayload):
        return drafts.save(state, project_id, body.id, body.kind, body.input, body.revision)

    return application
