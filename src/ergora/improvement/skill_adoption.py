"""Compare evaluated Skill candidates and explicitly adopt them."""

import ergora.improvement.evaluation as evaluation
import ergora.definitions.skills as skill_assets
from ergora.storage.state import State


def adopt(state: State, project_id: str, baseline_run: str, candidate_run: str, expected_revision: int, reason: str) -> dict:
    comparison = evaluation.compare(state, project_id, baseline_run, candidate_run)
    if not comparison["eligible"]:
        raise ValueError("Candidate is not eligible: " + "; ".join(comparison["reasons"]))
    candidate = skill_assets.get(state, project_id, comparison["candidate"])
    return skill_assets.move_head(state, project_id, candidate["name"], comparison["candidate"], expected_revision,
                                  "adopt", reason, expected_digest=comparison["baseline"], evidence=[baseline_run, candidate_run])
