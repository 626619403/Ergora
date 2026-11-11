"""Shared project-scoped snapshot reads for issue and task use cases."""

import json
import re

from .issue_sources import validate_snapshot


def validate_digest(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch('[a-f0-9]{64}', value):
        raise ValueError('Issue record identity must be a SHA256 digest')


def snapshot_from_row(row) -> dict:
    payload = json.loads(row['document'])
    result = {'schema_version': 1, 'sha256': row['sha'], 'first_observed_at': row['first_observed_at'], 'payload': payload}
    validate_snapshot(result)
    if payload['observation']['project']['id'] != row['project']:
        raise ValueError('Saved issue snapshot differs from its project')
    return result


def snapshot(state, project_id: str, digest: str) -> dict:
    state.project(project_id)
    validate_digest(digest)
    with state.connect() as db:
        row = db.execute('SELECT * FROM issue_snapshots WHERE project=? AND sha=?', (project_id, digest)).fetchone()
    if row is None:
        raise ValueError('Unknown issue snapshot in this project')
    return snapshot_from_row(row)
