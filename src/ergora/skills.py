"""Compare evaluated Skill candidates and explicitly adopt them.

Asset operations remain available here for existing Python callers; new callers
use skill_assets so evaluation never depends on the adoption use case.
"""

from . import evaluation, skill_assets
from .skill_assets import (
    digest_tree as digest_tree,
    export as export,
    get as get,
    import_bundle as import_bundle,
    metadata as metadata,
    rollback as rollback,
    versions as versions,
)
from .state import State


def adopt(state: State, project_id: str, baseline_run: str, candidate_run: str, expected_revision: int, reason: str) -> dict:
    comparison = evaluation.compare(state, project_id, baseline_run, candidate_run)
    if not comparison["eligible"]:
        raise ValueError("Candidate is not eligible: " + "; ".join(comparison["reasons"]))
    candidate = skill_assets.get(state, project_id, comparison["candidate"])
    return skill_assets.move_head(state, project_id, candidate["name"], comparison["candidate"], expected_revision,
                                  "adopt", reason, expected_digest=comparison["baseline"], evidence=[baseline_run, candidate_run])
