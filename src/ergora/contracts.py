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
    "integer": lambda checker, value: type(value) is int,
    "number": _is_finite_number,
}))
_SCHEMAS = Path(__file__).parent / "data/schemas"
EVALUATION_MANIFEST = json.loads((_SCHEMAS / "evaluation-manifest-v1.json").read_text(encoding="utf-8"))
EVALUATION_RESULT = json.loads((_SCHEMAS / "evaluation-result-v1.json").read_text(encoding="utf-8"))


def validate(value, schema: dict, context: str) -> None:
    error = next(StrictValidator(schema).iter_errors(value), None)
    if error is not None:
        pointer = "/" + "/".join(str(part).replace("~", "~0").replace("/", "~1") for part in error.absolute_path)
        raise ValueError(f"{context} at {pointer}: {error.message}") from error
