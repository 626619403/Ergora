"""Short trusted control activities. Long agent/CI work is owned by external executors."""
import asyncio
from temporalio import activity
from temporalio.exceptions import ApplicationError
from .adapter import ApprovalRejected, ContractViolation, canonical, MAX_RECEIPT_BYTES, MAX_CONTEXT_BYTES
from .contracts import canonical_sha, validate_spec
from .registry import load_profile


def require(ok, detail):
    if not ok: raise ApplicationError(detail, type="ContractViolation", non_retryable=True)


class Activities:
    def __init__(self, adapter): self.adapter = adapter

    @activity.defn(name="dev_validate")
    async def validate(self, spec: dict) -> dict:
        try:
            validate_spec(spec)
            request = spec["request"]
            installed = load_profile(request["task_type"], request["task_version"])
            require(canonical_sha(installed) == spec["profile_sha256"], "Installed trusted profile changed; create a new admitted task revision")
        except ValueError as error:
            raise ApplicationError(str(error), type="ContractViolation", non_retryable=True) from error
        return {"validated": True}

    @activity.defn(name="dev_submit")
    async def submit(self, context: dict) -> dict:
        try:
            validate_spec(context["spec"])
            require(len(canonical(context)) <= MAX_CONTEXT_BYTES, "Stage context exceeds the control-plane payload limit")
            require(context["request_sha256"] == context["spec"]["request_sha256"], "Context request hash mismatch")
            async with asyncio.timeout(20): return await self.adapter.submit(context)
        except ContractViolation as error:
            raise ApplicationError(str(error), type="ContractViolation", non_retryable=True) from error

    @activity.defn(name="dev_poll")
    async def poll(self, job: dict) -> dict | None:
        try:
            async with asyncio.timeout(20): result = await self.adapter.poll(job)
            if result is None: return None
            require(len(canonical(result)) <= MAX_RECEIPT_BYTES, "Receipt metadata exceeds 32 KiB")
            require(result.get("job_id") == job["job_id"] and result.get("job_sha256") == job["job_sha256"], "Receipt job binding mismatch")
            require(result.get("state") in {"SUCCEEDED", "FAILED", "CANCELLED"}, "Invalid receipt state")
            if result["state"] != "SUCCEEDED": return result
            context = job["context"]; profile = context["spec"]["profile"]
            stage = context["stage"].split(":", 1)[0]
            actor = result["actor"]
            role = profile.get("roles", {}).get(stage, {"inventory": "inspector", "plan": "planner", "work": "implementer", "integrate": "integrator", "verify": "verifier", "review": "reviewer"}[stage])
            require(actor.get("role") == role, "Unexpected executor role")
            expected = context.get("expected_candidate_sha")
            if expected: require(result.get("candidate_sha") == expected, "Receipt candidate differs from the exact candidate being evaluated")
            names = {a["name"] for a in result["artifacts"]}
            required = set(profile.get("artifacts_by_stage", {}).get(stage, []))
            require(required <= names, "Missing required stage artifacts: " + ", ".join(sorted(required - names)))
            checks = {c["id"]: c["status"] for c in result.get("checks", [])}
            require(all(value == "pass" for value in checks.values()), "A stage check failed")
            if stage == "verify":
                require(actor.get("kind") == "ci", "Verification must be attested by the trusted deterministic CI executor")
                require(set(profile["required_checks"]) <= set(checks), "Missing required verification checks")
                require(actor["id"] not in context["author_ids"], "Verifier cannot be an implementation principal")
                require(actor["session_id"] not in context["author_sessions"], "Verifier cannot reuse an implementation session")
            if stage == "review":
                require(checks.get("independent-review") == "pass", "Independent reviewer must explicitly approve")
                require(actor.get("kind") in {"agent", "human"}, "Reviewer must be a reviewer agent or human")
                require(actor["id"] not in context["author_ids"], "Reviewer cannot review their own implementation")
                require(actor["session_id"] not in context["author_sessions"], "Reviewer requires a fresh independent session")
            return result
        except (ContractViolation, KeyError, TypeError, ValueError) as error:
            raise ApplicationError(str(error), type="ContractViolation", non_retryable=True) from error

    @activity.defn(name="dev_authorize_plan")
    async def authorize(self, context: dict) -> dict:
        try:
            async with asyncio.timeout(20): return await self.adapter.authorize(context)
        except ApprovalRejected as error:
            raise ApplicationError(str(error), type="ApprovalRejected", non_retryable=True) from error

    @activity.defn(name="dev_fence")
    async def fence(self, context: dict) -> dict:
        try:
            async with asyncio.timeout(20): return await self.adapter.fence(context)
        except ContractViolation as error:
            raise ApplicationError(str(error), type="ContractViolation", non_retryable=True) from error

    def registered(self):
        return [self.validate, self.submit, self.poll, self.authorize, self.fence]
