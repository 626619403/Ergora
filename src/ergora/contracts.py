"""Shared JSON structures; domain checks and content identities stay with their owners."""

import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator, validators


def _is_finite_number(checker, value) -> bool:
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


StrictValidator = validators.extend(Draft202012Validator, type_checker=Draft202012Validator.TYPE_CHECKER.redefine_many({
    # Numeric bounds ask the number checker first. Both types must agree on
    # finite integers so an overflowing int cannot bypass minimum / maximum.
    "integer": lambda checker, value: type(value) is int and _is_finite_number(checker, value),
    "number": _is_finite_number,
}))
_SCHEMAS = Path(__file__).parent / "data/schemas"
EVALUATION_MANIFEST = json.loads((_SCHEMAS / "evaluation-manifest-v1.json").read_text(encoding="utf-8"))
EVALUATION_RESULT = json.loads((_SCHEMAS / "evaluation-result-v1.json").read_text(encoding="utf-8"))
STATE_BACKUP = json.loads((_SCHEMAS / "state-backup-v1.json").read_text(encoding="utf-8"))
AGENT_DEFINITION = json.loads((_SCHEMAS / "agent-definition-v1.json").read_text(encoding="utf-8"))

WORKFLOW_DEFINITION = json.loads((_SCHEMAS / "workflow-definition-v1.json").read_text(encoding="utf-8"))
WORKFLOW_DEFINITIONS = {1: WORKFLOW_DEFINITION,
                        2: json.loads((_SCHEMAS / "workflow-definition-v2.json").read_text(encoding="utf-8"))}
COMPOSITION_GRANT = {"$defs": WORKFLOW_DEFINITION["$defs"], "$ref": "#/$defs/grant"}
COMPOSITION_INPUT = json.loads((_SCHEMAS / "composition-input-v1.json").read_text(encoding="utf-8"))
COMPOSITION_MANIFEST = json.loads((_SCHEMAS / "composition-manifest-v1.json").read_text(encoding="utf-8"))
ISSUE_OBSERVATION = json.loads((_SCHEMAS / "issue-observation-v1.json").read_text(encoding="utf-8"))
CANDIDATE_REVIEW_CONTEXT = json.loads((_SCHEMAS / "candidate-review-context-v1.json").read_text(encoding="utf-8"))
REVIEW_REQUEST = {"$defs": CANDIDATE_REVIEW_CONTEXT["$defs"], "$ref": "#/$defs/review_request"}


def validate(value, schema: dict, context: str) -> None:
    error = next(StrictValidator(schema).iter_errors(value), None)
    if error is not None:
        pointer = "/" + "/".join(str(part).replace("~", "~0").replace("/", "~1") for part in error.absolute_path)
        raise ValueError(f"{context} at {pointer}: {error.message}") from error
