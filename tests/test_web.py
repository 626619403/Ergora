import json
import sys
from pathlib import Path
import subprocess

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient

import ergora.improvement.memory as memory
import ergora.configuration.projects as projects
import ergora.definitions.skills as skill_assets
from ergora.storage.state import State
from ergora.interfaces.web import create_app
from test_agents import native_session_case, native_correction_case
from test_document_corrections import project as document_project, proposal as document_proposal, consent as document_consent


@pytest.fixture
def console(tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    state = State(tmp_path / "data")
    projects.create(state, "demo", repo)
    projects.create(state, "other", repo)
    headers = {"Origin": "http://127.0.0.1:8977", "X-Ergora-Request": "1"}
    with TestClient(create_app(state.root), base_url="http://127.0.0.1:8977", headers=headers) as client:
        yield client, state, repo


def test_local_http_boundary_and_packaged_assets(console):
    client, state, repo = console
    index = client.get("/")
    assert index.status_code == 200 and "/assets/app.js" in index.text
    assert "script-src 'self'" in index.headers["content-security-policy"]
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/assets/vendor/cytoscape.min.js").status_code == 200
    payload = {"id": "third", "repo": str(repo)}
    assert client.post("/api/projects", json=payload, headers={"X-Ergora-Request": ""}).status_code == 403
    assert client.post("/api/projects", json=payload, headers={"Origin": "https://attacker.example"}).status_code == 403
    assert client.get("/api/bootstrap", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert client.get("/api/bootstrap", headers={"Host": "attacker.example", "Origin": "http://attacker.example"}).status_code == 400
    assert [item["id"] for item in client.get("/api/bootstrap").json()["projects"]] == ["demo", "other"]


def test_campaign_timeline_reads_and_exposes_only_the_selected_original_task(console, monkeypatch):
    from ergora.campaigns import application

    client, state, _ = console
    calls = []
    selected = {"task_id": "selected", "status": "observed", "eligible": False,
                "attempt_status": "failed", "update_id": "saved",
                "readback_observation": {"status": "available"},
                "waiting_receipt": {"update_id": "original-wait"}, "receipt": None}
    attempt = {"terminal": {"status": "failed", "run_id": "original", "update_id": "saved",
                            "accepted_event_id": 28, "completed_event_id": 29,
                            "receipt": None, "reason": "readback_already_admitted"}}
    completion = {"task_id": "selected", "completed_event_id": 19}

    async def status(store, project, campaign, *, online, task_id):
        calls.append((store.root, project, campaign, online, task_id))
        return {"project": project, "campaign": campaign, "run_id": "original", "current_run_id": "successor",
                "workflow_state_status": "observed",
                "plan": {"acceptance": "Inspect original evidence", "limits": {"expires_at": 100},
                         "tasks": [{"task_id": "selected", "depends_on": [], "source": {}},
                                   {"task_id": "other-private"}]},
                "tasks": {"selected": {**selected, "recipient": {"prompt": "selected-private-prompt"}},
                          "other-private": {"recipient": {"prompt": "other-private-prompt"}}},
                "task_observation_history": {"selected": attempt, "other-private": {}},
                "task_evidence": {"task_id": task_id, "correlation": "unavailable"},
                "stop": {"status": "unknown", "remote_status": "unavailable", "update_id": "original-stop",
                         "receipt": None, "local_fence_saved": True},
                "rollover": {"status": "unresolved", "update_id": "original-rollover"},
                "readback_completion": {**completion, "recipient": {"task_id": "other-private"}}}

    monkeypatch.setattr(application, "status", status)
    path = "/api/projects/demo/campaigns/record/tasks/selected/timeline"
    assert client.get(path, headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert client.post(path).status_code == 405
    response = client.get(path)
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    observed = response.json()
    assert calls == [(state.root, "demo", "record", True, "selected")]
    assert observed["run_id"] == "original" and observed["current_run_id"] == "successor"
    assert observed["task_state"] == selected and observed["task_observation_history"] == attempt
    assert observed["task_evidence"]["correlation"] == "unavailable"
    assert "training_task" not in observed
    assert "assignment" not in observed
    assert "direct_dependencies" not in observed
    assert observed["stop"] == {"status": "unknown", "remote_status": "unavailable", "update_id": "original-stop",
                                "decision": None, "receipt_run_id": None, "local_fence_saved": True}
    assert observed["rollover"] == {"status": "unresolved", "update_id": "original-rollover"}
    assert observed["readback_completion"] == completion
    assert "other-private" not in response.text and "selected-private-prompt" not in response.text


@pytest.mark.parametrize("case", ["observed", "blocked", "local-stop", "scheduled", "unknown", "awaiting", "absent", "other-task"])
def test_campaign_fixed_timeline_scopes_original_recipient(console, monkeypatch, case):
    from ergora.campaigns import application

    client, state, _ = console
    label = "other" if case == "other-task" else "fixed"
    recipient = {"session_id": "original-session", "parent_run_id": "original-parent", "intent_id": "original-intent",
                 "prompt": "private-prompt", "timeout_seconds": 20}
    selected = {"task_id": "fixed", "depends_on": [], "source": {}, "readback": {}, "recipient": recipient}
    other = {"task_id": "other", "depends_on": ["fixed"], "source": {}}
    private_intent = {"task_id": "fixed", "wake_id": "original-owner-wake", "source": "private-wake-source"}
    timing = {"clock": "temporal_history", "intervals_ns": {"ready_to_scheduled": 521}}
    history = {"status": "observed", "scheduled_event_id": 18, "started_event_id": 19,
               "completed_event_id": 20, "timing": timing}
    run = {"status": "succeeded", "execution_stopped": True, "result_sha256": "f" * 64, "returncode": 0}
    links = {"session_id": "original-session", "parent_run_id": "original-parent", "intent_id": "original-intent",
             "run_id": "original-native-run", "dispatch": "accepted"}
    wake = {"status": "observed", "intent": private_intent,
            "native_receipt": {**links, "native_start": {"status": "started", "process": "private-process"},
                               "run": {**run, "submitted": "private-prompt"}},
            "history": {**history, "intent": private_intent, "outcome": {"private-field": "private-outcome"}}}
    expected = {"status": "observed", "reason": None, "wake_id": "original-owner-wake", "history": history,
                "native_receipt": {**links, **run, "start_status": "started"}}
    if case == "blocked":
        wake.update(status="blocked", reason="stopped", history={**history, "status": "blocked"}, native_receipt=None)
        expected.update(status="blocked", reason="stopped", history={**history, "status": "blocked"}, native_receipt=None)
    elif case == "local-stop":
        wake = {"status": "blocked", "reason": "stopped", "intent": None, "history": None, "native_receipt": None}
        expected = {"status": "blocked", "reason": "stopped", "wake_id": None, "history": None, "native_receipt": None}
    elif case == "scheduled":
        scheduled = {"status": "scheduled", "scheduled_event_id": 18}
        wake.update(status="scheduled", history=scheduled, native_receipt=None)
        expected.update(status="scheduled", history=scheduled, native_receipt=None)
    elif case == "unknown":
        wake.update(status="unknown", history=None,
                    native_receipt={**links, "dispatch": "incomplete", "native_start": {"status": "unrecorded"}, "run": None})
        expected.update(status="unknown", history=None, native_receipt={**links, "dispatch": "incomplete", "start_status": "unrecorded"})
    elif case == "awaiting":
        wake = {"status": "awaiting_readback", "intent": None, "history": None, "native_receipt": None}

    async def status(store, project, campaign, *, online, task_id):
        assert (store.root, store._read_only, project, campaign, online, task_id) == (state.root, True, "demo", "record", True, label)
        return {"workflow_state_status": "observed",
                "plan": {"acceptance": "Verify original wake", "limits": {"expires_at": 100}, "tasks": [selected, other]},
                "tasks": {"fixed": {**selected, "status": "observed"}, "other": other},
                "stop": {"status": "not_recorded", "remote_status": "not_requested", "update_id": None, "receipt": None},
                **({"recipient": wake} if case != "absent" else {})}

    monkeypatch.setattr(application, "status", status)
    response = client.get(f"/api/projects/demo/campaigns/record/tasks/{label}/timeline")
    assert response.status_code == 200, response.text
    observed = response.json()
    assert "recipient" not in observed["task_state"] and "private-" not in response.text
    if case in ("awaiting", "absent", "other-task"):
        assert "recipient" not in observed and "original-owner-wake" not in response.text
    else:
        assert observed["recipient"] == expected


@pytest.mark.parametrize("disposition", ["released", "unknown", "release-error", "refused", "completed-unknown", "timed-out",
                                         "invalid-terminal-status", "contradictory",
                                         "reason-path", "reason-object", "native-blocker", "other-task", "training-wait",
                                         "training-release-unobserved"])
def test_campaign_timeline_scopes_independent_assignment_evidence(console, monkeypatch, disposition):
    from errno import EACCES
    from os import strerror

    from ergora.campaigns import application

    client, state, _ = console
    task = {"task_id": "fixed", "depends_on": [], "source": {}}
    assignee = {"role": "performance-analyst", "generation": 8}
    claim = {"native_run_id": "original-a2-run", "wake_id": "original-a2-wake", "waiting_receipt_sha256": "a" * 64}
    history = {"status": "unknown", "waiting_accepted_event_id": 9, "waiting_completed_event_id": 10,
               "scheduled_event_id": 12, "started_event_id": 13}
    original_history = {**history, "completed_event_id": 14}
    native = {"session_id": "a2-session", "parent_run_id": "a2-parent", "intent_id": "a2-intent",
              "run_id": claim["native_run_id"], "dispatch": "accepted"}
    run = {"status": "succeeded", "result_sha256": "b" * 64, "execution_stopped": True, "returncode": 0}
    start_status = "started"
    release = {"session_id": native["session_id"], "run_id": native["run_id"], "request_sha256": "c" * 64}
    private_lock = state.root / "runs/a2-session.session.lock"
    scoped_error = str(PermissionError(EACCES, strerror(EACCES), str(private_lock)))
    projected_extra, raw_extra = {}, {}
    raw_blocker = None
    if disposition == "unknown":
        run = None
        start_status = native["dispatch"] = "unrecorded"
        release = None
    elif disposition == "release-error":
        release = None
        raw_extra["release_error"] = scoped_error
        projected_extra["release_observation_failed"] = True
    elif disposition == "refused":
        run = None
        start_status = native["dispatch"] = "unrecorded"
        history.update(status="blocked", completed_event_id=14, reason="stale_parent")
        original_history.update(status="blocked", outcome={"status": "blocked", "reason": "stale_parent"})
        raw_extra["refusal"] = projected_extra["refusal"] = {"attempt_sha256": "d" * 64, "reason": "stale_parent"}
        release = {"status": "refused", "attempt_sha256": projected_extra["refusal"]["attempt_sha256"]}
    elif disposition == "completed-unknown":
        history["completed_event_id"] = 14
        original_history["outcome"] = {"status": "unknown"}
    elif disposition == "timed-out":
        history.update(terminal_event_id=14, terminal_status="timed_out")
        original_history["terminal_status"] = "timed_out"
    elif disposition == "invalid-terminal-status":
        original_history["terminal_status"] = {"error": scoped_error}
    elif disposition == "contradictory":
        history = {"status": "contradictory", "verification_failed": True}
        original_history = {"status": "contradictory", "error": f"Invalid decoded payload at {private_lock}"}
    elif disposition in ("reason-path", "reason-object"):
        history.update(status="blocked", completed_event_id=14)
        reason = scoped_error if disposition == "reason-path" else {"error": scoped_error}
        original_history.update(status="blocked", outcome={"status": "blocked", "reason": reason})
        raw_blocker = reason
    elif disposition == "native-blocker":
        run = {"status": "cancelled", "execution_stopped": True, "returncode": -9,
               "campaign_recipient_blocker": "stopped"}
    elif disposition in ("training-wait", "training-release-unobserved"):
        task["source"] = {"kind": "training_full_result", "locator": {"experiment_id": "alpha"}}
        history = {"status": "unknown", "training_wait_started_event_id": 1, "scheduled_event_id": 12,
                   "started_event_id": 13}
        original_history = {**history, "completed_event_id": 14}
        if disposition == "training-release-unobserved":
            release = None
            raw_extra["release_unobserved"] = projected_extra["release_unobserved"] = True
    if disposition == "other-task":
        raw_extra["release_unobserved"] = True
    if disposition in ("released", "training-wait", "timed-out", "other-task"):
        intervals = {"ready_to_scheduled": 0, "scheduled_to_worker_started": 39850,
                     "worker_started_to_delivery_terminal": 1779422223}
        history["timing"] = {"clock": "temporal_history", "intervals_ns": intervals}
        original_history["timing"] = {**history["timing"], "events": {"ready": "private-value"},
                                      "intervals_ns": {**intervals, "unsupported": "private-value"}}
    elif disposition == "unknown":
        original_history["timing"] = {"clock": "temporal_history", "intervals_ns": {
            "ready_to_scheduled": -1, "scheduled_to_worker_started": False, "worker_started_to_delivery_terminal": None}}
    elif disposition == "release-error":
        original_history["timing"] = {"clock": "private-value", "intervals_ns": {"ready_to_scheduled": 0}}
    elif disposition == "invalid-terminal-status":
        original_history["timing"] = {"clock": "temporal_history", "intervals_ns": "private-value"}
    raw_run = None if run is None else {**run, "submitted": "private-value"}
    if raw_blocker is not None:
        raw_run["campaign_recipient_blocker"] = raw_blocker
    assignment = {"waiting_task_id": "other-private" if disposition == "other-task" else task["task_id"],
                  "task_id": "independent", "assignee": {**assignee, "context": "private-value"},
                  "slot_status": "claimed" if release is None else "released",
                  "claim": {"native_run_id": claim["native_run_id"],
                            "intent": {"wake_id": claim["wake_id"], "source": {
                                "waiting_receipt_sha256": claim["waiting_receipt_sha256"], "grant": "private-value"}},
                            "slot_release": {"context_digest": "private-value"}},
                  "history": {**original_history, "intent": "private-value"},
                  "native_receipt": {**native, "native_start": {"status": start_status, "process": "private-value"},
                                     "run": raw_run},
                  "release": {**release, "context_digest": "private-value"} if release is not None else None, **raw_extra}

    async def status(store, project, campaign, *, online, task_id):
        assert (store.root, project, campaign, online, task_id) == (state.root, "demo", "record", True, "fixed")
        return {"workflow_state_status": "unavailable", "task_evidence": task,
                "plan": {"acceptance": "Inspect original independent assignment", "limits": {"expires_at": 100},
                         "tasks": [task]},
                "stop": {"status": "not_recorded", "remote_status": "not_requested", "update_id": None, "receipt": None},
                "assignment": assignment}

    monkeypatch.setattr(application, "status", status)
    response = client.get("/api/projects/demo/campaigns/record/tasks/fixed/timeline")
    assert response.status_code == 200
    projected = response.json()
    assert projected["task_state"] is None
    if disposition in ("training-wait", "training-release-unobserved"):
        assert projected["training_task"]["locator"] == task["source"]["locator"]
    else:
        assert projected["task_evidence"] == task
    assert "private-value" not in response.text and "other-private" not in response.text
    assert str(private_lock) not in response.text
    if disposition == "other-task":
        assert "assignment" not in projected
    else:
        assert projected["assignment"] == {
            "waiting_task_id": "fixed", "task_id": "independent", "assignee": assignee,
            "slot_status": assignment["slot_status"], "claim": claim, "history": history,
            "native_receipt": {**native, "start_status": start_status, **(run or {})},
            "release": release, **projected_extra,
        }


@pytest.mark.parametrize("source", ["workflow", "history", "unavailable"])
def test_campaign_timeline_projects_only_direct_dependency_state(console, monkeypatch, source):
    from ergora.campaigns import application

    client, state, _ = console
    selected = {"task_id": "selected", "depends_on": ["full", "parent"], "source": {}}
    parent = {"task_id": "parent", "depends_on": ["grandparent-private"], "source": {"secret": "parent-source-private"}}
    frozen = [selected, {"task_id": "full"}, parent, {"task_id": "grandparent-private"}, {"task_id": "other-private"}]
    selected_state = {**selected, "status": "waiting_dependencies", "eligible": False}
    original_receipt = {"terminal": {"status": "unresolved", "update_id": "selected-original-update"}}
    full = {"status": "observed", "eligible": False, "source": {"locator": "full-source-private"},
            "readback": {"grant": "full-grant-private"}, "recipient": {"prompt": "full-recipient-private"}}
    parent_state = {**parent, "status": "waiting_job", "receipt": {"proof": "parent-receipt-private"}}
    if source == "workflow":
        tasks = {"full": full, "parent": parent_state, "selected": selected_state,
                 "grandparent-private": {"status": "observed"}, "other-private": {"status": "ready"}}
    else:
        tasks = {"full": {**full, "state_source": "history"}} if source == "history" else {}

    async def status(store, project, campaign, *, online, task_id):
        assert (store.root, project, campaign, online, task_id) == (state.root, "demo", "record", True, "selected")
        return {"plan": {"acceptance": "Inspect original dependency", "limits": {"expires_at": 100}, "tasks": frozen},
                "workflow_state_status": "observed" if source == "workflow" else "unavailable",
                "tasks": tasks, "task_evidence": selected,
                "stop": {"status": "not_recorded", "remote_status": "not_requested", "update_id": None, "receipt": None},
                "task_observation_history": {"selected": original_receipt, "parent": {"private": "parent-history-private"}},
                "readback_completion": {"task_id": "full", "native_result_sha256": "full-result-private"}}

    monkeypatch.setattr(application, "status", status)
    response = client.get("/api/projects/demo/campaigns/record/tasks/selected/timeline")
    assert response.status_code == 200, response.text
    projected = response.json()
    assert projected["direct_dependencies"] == [
        {"task_id": "full", "state_source": source, "status": None if source == "unavailable" else "observed"},
        {"task_id": "parent", "state_source": "workflow" if source == "workflow" else "unavailable",
         "status": "waiting_job" if source == "workflow" else None},
    ]
    assert projected["task_state"] == (selected_state if source == "workflow" else None)
    assert projected["task_observation_history"] == original_receipt and projected["readback_completion"] is None
    assert "-private" not in response.text


@pytest.mark.parametrize("foreign_evidence", [None, "readback_terminal", "readback_followup_terminal"])
@pytest.mark.parametrize(("kind", "activity_type"), [
    ("training_full_result", "ergora_campaign_training_full_result_reobserve"),
    ("training_full_result", "ergora_campaign_training_full_result_recover_receipt"),
    ("training_screen_result", "ergora_campaign_training_screen_result_recover_receipt"),
    (None, "ergora_campaign_fixed_check_receipt_recovery"),
])
def test_campaign_timeline_keeps_only_selected_history_terminals(console, monkeypatch, foreign_evidence, kind,
                                                                activity_type):
    from ergora.campaigns import application

    client, state, _ = console
    task = {"task_id": "selected", "depends_on": [], "source": {"kind": kind, "locator": {}} if kind else {}}
    provenance = {"source_sha256": "a" * 64} if kind else {"waiting_receipt_sha256": "a" * 64}
    terminal = {"task_id": "selected", "status": "timed_out", "run_id": "original-run",
                "activity_id": "original-read", **provenance,
                "scheduled_event_id": 11, "started_event_id": 12, "terminal_event_id": 13,
                "cause": {"kind": "timeout", "type": "HEARTBEAT"}}
    followup = {**terminal, "status": "cancelled", "activity_id": "original-followup",
                "activity_type": activity_type, "original_timeout_event_id": 13,
                "scheduled_event_id": 17, "started_event_id": 18, "cancel_requested_event_id": 19,
                "terminal_event_id": 20}
    del followup["cause"]
    evidence = {"readback_terminal": terminal, "readback_followup_terminal": followup}
    observed_evidence = {key: {**value, "recipient": {"prompt": "private-prompt"},
                              **({"cause": {**value["cause"], "message": "private-message"}} if "cause" in value else {})}
                         for key, value in evidence.items()}
    if foreign_evidence:
        observed_evidence[foreign_evidence]["task_id"] = "other-private"

    async def status(store, project, campaign, *, online, task_id):
        assert (store.root, project, campaign, online, task_id) == (state.root, "demo", "record", True, "selected")
        return {"run_id": "original-run", "workflow_state_status": "unavailable",
                "plan": {"acceptance": "Read the original result", "limits": {"expires_at": 100}, "tasks": [task]},
                "stop": {"status": "not_recorded", "remote_status": "not_requested", "update_id": None, "receipt": None},
                **observed_evidence}

    monkeypatch.setattr(application, "status", status)
    response = client.get("/api/projects/demo/campaigns/record/tasks/selected/timeline")
    assert response.status_code == 200, response.text
    observed = response.json()
    assert observed["task_state"] is None and observed["readback_completion"] is None
    assert {name: observed[name] for name in evidence if name in observed} == {
        name: value for name, value in evidence.items() if name != foreign_evidence}
    assert "private-" not in response.text and "other-private" not in response.text


@pytest.mark.parametrize("workflow_observed", [True, False])
@pytest.mark.parametrize("kind", ["training_full_result", "training_screen_result", "training_gpu_release"])
def test_campaign_training_timeline_keeps_the_original_result_and_native_dispositions(console, monkeypatch,
                                                                                     workflow_observed, kind):
    from ergora.campaigns import application

    client, state, _ = console
    locator = {"experiment_id": "alpha", "workflow_id": "training-workflow", "run_id": "training-run",
               "job_id": "original-job", "attempt_sha256": "a" * 64, "native_request_sha256": "b" * 64}
    task = {"task_id": "full", "depends_on": [],
            "source": {"kind": kind, "locator": locator},
            "recipient": {"prompt": "hidden-prompt"}}
    readback = {"status": "available", "activity_id": "original-reader", "native_result_sha256": "c" * 64}
    completion = {"task_id": "full", "native_result_sha256": "c" * 64, "reader_cleanup_sha256": "d" * 64,
                  "local_gpu_lease": {"status": "unknown", "read_only": True}, "completed_event_id": 13}
    scope = {}
    if kind == "training_screen_result":
        scope = {"source_kind": kind}
        completion.update(**scope, native_result_state="SCREEN_REJECTED", decision="rejected",
                          screen_result_sha256="f" * 64, full_execution_authorized=False)
    elif kind == "training_gpu_release":
        scope = {"source_kind": kind}
        locator.update(session_id="a" * 32, lease_id="b" * 64)
        del completion["native_result_sha256"]
        completion.update(**scope, local_gpu_lease={"status": "released", "read_only": True,
                                                    "release_ref": {"sequence": 5}})
    run = {"status": "succeeded", "execution_stopped": True, "result_sha256": "e" * 64, "returncode": 0}
    receipt = {"session_id": "original-session", "parent_run_id": "original-parent", "intent_id": "original-intent",
               "run_id": "native-run", "dispatch": "accepted"}
    activity = {"status": "unknown", "scheduled_event_id": 17, "started_event_id": 18, "completed_event_id": 19}
    intervals = {"ready_to_scheduled": 423563716, "scheduled_to_worker_started": 0}
    if workflow_observed:
        intervals["worker_started_to_delivery_terminal"] = 1779422223
    activity["timing"] = {"clock": "temporal_history", "intervals_ns": intervals}
    raw_timing = {**activity["timing"], "events": {"ready": "private-value"}, "intervals_ns": {
        "worker_started_to_delivery_terminal": "private-value", **intervals, "unsupported": "private-value"}}

    async def status(store, project, campaign, *, online, task_id):
        assert (store.root, project, campaign, online, task_id) == (state.root, "demo", "record", True, "full")
        return {"project": project, "campaign": campaign, "run_id": "campaign-run",
                "workflow_state_status": "observed" if workflow_observed else "unavailable",
                "plan": {"acceptance": "Verify original training", "limits": {"expires_at": 100}, "tasks": [task]},
                "tasks": {"full": {**task, "status": "observed", "eligible": False,
                                   **({"readback_observation": readback} if workflow_observed
                                      else {"state_source": "history"})}},
                "stop": {"status": "not_recorded", "remote_status": "not_requested", "update_id": None, "receipt": None},
                "readback_completion": {**completion, "recipient": {"hidden-prompt": "private-value"}},
                "recipient": {"status": "observed", "intent": {"wake_id": "original-wake", "source": "private-value"},
                              "history": {**activity, "timing": raw_timing, "intent": "private-value"},
                              "native_receipt": {**receipt, "native_start": {"status": "started", "process": "private-value"},
                                                 "run": {**run, "binding": "private-value", "submitted": "hidden-prompt"}}}}

    monkeypatch.setattr(application, "status", status)
    response = client.get("/api/projects/demo/campaigns/record/tasks/full/timeline")
    assert response.status_code == 200, response.text
    observed = response.json()
    assert observed["run_id"] == "campaign-run"
    assert observed["task_state"] == {
        "status": "observed", "eligible": False,
        **({"readback_observation": readback} if workflow_observed else {"state_source": "history"}),
    }
    assert observed["readback_completion"] == completion
    assert "readback_terminal" not in observed and "readback_followup_terminal" not in observed
    assert observed["training_task"] == {
        "task_id": "full", "depends_on": [], "locator": locator, **scope,
        "recipient": {"status": "observed", "reason": None, "wake_id": "original-wake", "history": activity,
                      "native_receipt": {**receipt, "start_status": "started", **run}},
    }
    assert "hidden-prompt" not in response.text and "private-value" not in response.text


def test_formal_work_priority_confirms_exact_command_and_reads_the_original(console, monkeypatch):
    from ergora.development import application as tasks

    client, state, _ = console
    path = "/api/projects/demo/tasks/task-one/work-priority/owner-one"
    query = {"run_id": "original-run", "timeout": 7}
    body = {**query, "revision": 1, "confirm": True, "work_unit_id": "pending-b", "plan_sha256": "a" * 64}
    calls = []
    recorded = {"task_id": "task-one", "decision_id": "owner-one", "run_id": "original-run",
                "work_unit_id": "pending-b", "plan_sha256": "a" * 64, "project_revision": 1}

    def native(project, home, operation, payload, *, timeout):
        calls.append((project["revision"], home, operation, payload, timeout))
        if payload["run_id"] != "original-run":
            raise ValueError("Work priority must pin the original submitted run ID")
        return {**recorded, "status": "unknown" if operation == "prioritize" else "applied", "attempt_saved": True}

    monkeypatch.setattr(tasks, "_project", lambda store, project: store.project(project))
    monkeypatch.setattr(tasks.development_native, "task_work_priority", native)
    assert client.post(path, json=body, headers={"X-Ergora-Request": ""}).status_code == 403
    assert client.post(path, json=body, headers={"Origin": "https://attacker.example"}).status_code == 403
    for invalid in ({"revision": "1"}, {"confirm": 1}, {"timeout": True}, {"timeout": 61}, {"run_id": ""},
                    {"work_unit_id": "bad.unit"}, {"plan_sha256": "bad"}, {"decision_id": "other"}):
        assert client.post(path, json={**body, **invalid}).status_code == 422
    assert client.post(path, json={**body, "confirm": False}).status_code == 400
    assert client.post(path, json={**body, "revision": 2}).status_code == 400
    assert client.get(path).status_code == 422
    assert client.get(path, params={**query, "timeout": 0}).status_code == 422
    assert client.get(path + "!", params=query).status_code == 422
    assert client.post(path + "!", json=body).status_code == 422
    assert calls == []

    submitted = client.post(path, json=body)
    assert submitted.status_code == 200
    assert submitted.json() == {**recorded, "status": "unknown", "attempt_saved": True}
    assert projects.bind(state, "demo", "reviewer", {"tool": "codex", "model": "later-model"}, 1)["revision"] == 2
    assert client.get(path, params={**query, "run_id": "other-run"}).status_code == 400
    observed = client.get(path, params=query, headers={"X-Ergora-Request": ""})
    assert observed.status_code == 200
    assert observed.json() == {**recorded, "status": "applied", "attempt_saved": True}
    identity = {key: recorded[key] for key in ("task_id", "decision_id", "run_id")}
    assert calls == [
        (1, state.root, "prioritize", {**identity, "work_unit_id": "pending-b", "plan_sha256": "a" * 64}, 7),
        (2, state.root, "inspect", {**identity, "run_id": "other-run"}, 7),
        (2, state.root, "inspect", identity, 7),
    ]


def test_workflow_revision_impact_is_available_only_on_read_only_routes(console, tmp_path):
    from ergora.definitions import agents, workflows
    from test_workflow_definitions import EXAMPLES, definition, grant, leaf, ref, write_bundle

    client, state, _ = console
    agent = agents.import_bundle(state, EXAMPLES / "agents/architecture-reviewer")
    document = definition("impact-root", [leaf("review", ref(agent, "agent"))])
    original = workflows.import_bundle(state, write_bundle(tmp_path / "impact-root", document))
    selection = {"schema_version": 1, "roots": [{"ref": ref(original, "workflow"), "grant": grant()}]}
    payload = {"base_digest": original["digest"], "definition": {**document, "version": "1.0.1"}, "impact": selection}
    index = state.root / "workflow-definitions/index.json"
    before = index.read_bytes()
    route = "/api/workflow-definitions/impact-root/1.0.0/revisions"
    observed = client.post(route + "/check", json=payload)
    assert observed.status_code == 200
    assert observed.json() == workflows.revise(state, "impact-root", "1.0.0", **payload)
    assert observed.json()["impact"]["roots"][0]["affected_paths"] == ["root"]
    assert client.post(route, json=payload).status_code == 422
    assert index.read_bytes() == before


def test_installation_profiles_match_cli_without_rewriting_projects(console):
    client, state, _ = console
    before = state.project("demo")
    observed = client.get("/api/installation-profiles")
    assert observed.status_code == 200
    result = subprocess.run([sys.executable, "-m", "ergora", "tools", "profiles"],
                            capture_output=True, text=True, encoding="utf-8", timeout=10)
    assert result.returncode == 0, result.stderr
    assert observed.json() == json.loads(result.stdout)
    assert state.project("demo") == before


def test_binding_revisions_and_cli_web_share_durable_state(console):
    client, state, repo = console
    path = "/api/projects/demo/bindings/implementer"
    binding = {"tool": "command", "argv": [sys.executable, "-c", "import sys;print(sys.stdin.read())"]}
    assert client.put(path, json={"binding": binding, "revision": 1}).status_code == 200
    assert client.put(path, json={"binding": binding, "revision": 1}).status_code == 400
    assert state.project("demo")["revision"] == 2
    result = client.post("/api/projects/demo/agent-runs", json={"role": "implementer", "prompt": "API fixture", "timeout": 5}).json()
    assert result["status"] == "succeeded"
    assert "API fixture" in Path(result["output"], "stdout.txt").read_text()
    preview = client.get(f"/api/projects/demo/agent-runs/{result['id']}/output").json()
    assert "API fixture" in preview["streams"]["stdout"]["text"]
    assert "native_history" not in preview
    unsupported = client.get(f"/api/projects/demo/agent-runs/{result['id']}/output?native_history=true").json()
    assert unsupported["native_history"]["available"] is False
    Path(result["output"], "stdout.txt").write_text("Z" * 70000)
    bounded = client.get(f"/api/projects/demo/agent-runs/{result['id']}/output").json()["streams"]["stdout"]
    assert len(bounded["text"]) == 65536 and bounded["truncated"]
    assert client.get(f"/api/projects/other/agent-runs/{result['id']}/output").status_code == 400
    assert client.get("/api/projects/other/dashboard").json()["agent_runs"] == []


def test_correction_suggestion_preference_http_and_cli_share_project_revision(console, capsys):
    import ergora.interfaces.cli as cli

    client, state, _ = console
    base = "/api/projects/demo"
    before = state.project("demo")
    assert client.get(base + "/configuration").json()["correction_suggestions"] == {"enabled": True, "source": "default"}
    assert state.project("demo") == before
    updated = client.put(base + "/correction-suggestions", json={"enabled": False, "revision": before["revision"]})
    assert updated.status_code == 200
    assert updated.json()["revision"] == before["revision"] + 1
    assert client.get(base + "/configuration").json()["correction_suggestions"] == {"enabled": False, "source": "project"}
    assert cli.main(["--home", str(state.root), "project", "correction-suggestions", "demo", "--enabled", "true",
                     "--revision", str(updated.json()["revision"])]) == 0
    assert json.loads(capsys.readouterr().out) == state.project("demo")
    assert client.get(base + "/configuration").json()["correction_suggestions"] == {"enabled": True, "source": "project"}
    current = state.project("demo")
    assert client.put(base + "/correction-suggestions", json={"enabled": False, "revision": before["revision"]}).status_code == 400
    for payload in ({"enabled": "false", "revision": current["revision"]}, {"enabled": 0, "revision": current["revision"]},
                    {"enabled": False, "revision": True}, {"enabled": False, "revision": str(current["revision"])},
                    {"enabled": False, "revision": current["revision"], "confirm": True}):
        assert client.put(base + "/correction-suggestions", json=payload).status_code == 422
    assert client.put(base + "/correction-suggestions", json={"enabled": False, "revision": current["revision"]},
                      headers={"X-Ergora-Request": ""}).status_code == 403
    assert state.project("demo") == current and state.project("other")["revision"] == before["revision"]


@pytest.mark.parametrize("action", ["apply", "withdraw"])
@pytest.mark.skipif(sys.platform != "linux", reason="Exact document replacement uses the Linux/WSL process and file owner")
def test_document_correction_http_reads_original_preview_and_observes_lost_decision(document_project, tmp_path, action, monkeypatch):
    from ergora.improvement import document_corrections

    state, repo, before = document_project
    value = document_proposal(state, tmp_path / "proposal")
    read_preview = document_corrections.get_preview
    preview_reads = []
    def tracked_preview(*args, **kwargs):
        preview_reads.append(args[2])
        return read_preview(*args, **kwargs)
    monkeypatch.setattr(document_corrections, "get_preview", tracked_preview)
    proposal_id = value["request"]["proposal_id"]
    headers = {"Origin": "http://127.0.0.1:8977", "X-Ergora-Request": "1"}
    with TestClient(create_app(state.root), base_url="http://127.0.0.1:8977", headers=headers) as client:
        url = f"/api/projects/demo/document-corrections/{proposal_id}"
        directory = state.root / "retrospectives" / "documents"
        original = {str(path.relative_to(directory)): path.read_bytes() for path in directory.rglob("*") if path.is_file()}
        for _ in range(2):
            observed = client.get(url)
            assert observed.status_code == 200
            assert observed.json()["preview"] is None and observed.json()["can_apply"] is True
            assert observed.json()["candidate_digest"] == value["candidate_digest"]
        assert preview_reads == []
        assert client.get(url + "/preview", params={"candidate_digest": value["candidate_digest"]}).json() == value
        assert client.get(url + "/preview", params={"candidate_digest": "0" * 64}).status_code == 400
        assert preview_reads == [proposal_id, proposal_id]
        for query in ({}, {"candidate_digest": "invalid"}):
            assert client.get(url + "/preview", params=query).status_code == 422
        assert client.get(url.replace(proposal_id, "0" * 32)).status_code == 400
        assert {str(path.relative_to(directory)): path.read_bytes() for path in directory.rglob("*") if path.is_file()} == original
        assert (repo / "AGENTS.md").read_bytes() == before
        consent = document_consent(value)
        for change in ({"confirm": "true"}, {"confirm": 1}, {"revision": True}, {"revision": "1"},
                       {"base_sha256": "invalid"}, {"preview": value}, {"path": "docs/guide.md"}, {"consent": "user approved"}):
            assert client.post(url + "/apply", json={**consent, **change}).status_code == 422
        for change in ({"confirm": False}, {"revision": consent["revision"] + 1}, {"candidate_digest": "0" * 64},
                       {"base_sha256": "0" * 64}, {"scope_sha256": "0" * 64}):
            assert client.post(url + "/apply", json={**consent, **change}).status_code == 400
        assert client.post(url + "/apply", json=consent, headers={"X-Ergora-Request": ""}).status_code == 403
        assert client.post(url + "/apply", json=consent, headers={"Origin": "https://other.example"}).status_code == 403
        for payload in ({"reason": ""}, {"reason": "   "}, {"reason": True}, {"reason": "task only", "confirm": True}):
            assert client.post(url + "/withdraw", json=payload).status_code == 422
        assert (repo / "AGENTS.md").read_bytes() == before
        assert client.get(url).json()["status"] == "ready"
        # Discard the mutation reply and recover exclusively through the original proposal ID.
        response = client.post(url + "/" + action, json=consent if action == "apply" else {"reason": "Use only for this task."})
        assert response.status_code == 200
        del response
        terminal = "applied" if action == "apply" else "withdrawn"
        before_status_reads = list(preview_reads)
        for _ in range(2):
            observed = client.get(url).json()
            assert observed["status"] == terminal and observed["can_apply"] is False
            assert observed["preview"] is None and observed["candidate_digest"] == value["candidate_digest"]
        assert preview_reads == before_status_reads
        expected = value["change"]["after"]["text"].encode("utf-8") if action == "apply" else before
        assert (repo / "AGENTS.md").read_bytes() == expected
        assert (repo / "docs/guide.md").read_bytes() == b"# Existing guide\nKeep the useful context."
        projects.create(state, "other", repo)
        assert client.get(url.replace("/demo/", "/other/")).status_code == 400
        assert client.get(url.replace("/demo/", "/other/") + "/preview", params={"candidate_digest": value["candidate_digest"]}).status_code == 400
        assert client.post(url.replace("/demo/", "/other/") + "/apply", json=consent).status_code == 400
        assert (repo / "AGENTS.md").read_bytes() == expected


def test_native_correction_http_first_reply_contains_preview_but_polling_is_light(native_correction_case, monkeypatch):
    from ergora.improvement import document_corrections

    state, repo, config, _, _ = native_correction_case
    headers = {"Origin": "http://127.0.0.1:8977", "X-Ergora-Request": "1"}
    with TestClient(create_app(state.root), base_url="http://127.0.0.1:8977", headers=headers) as client:
        base = "/api/projects/demo"
        response = client.post(base + "/agent-runs", json={"role": "implementer", "prompt": "A source-bound controlled correction.",
            "timeout": 10, "session_intent": "http-light-correction", "expected_revision": state.project("demo")["revision"],
            "codex_config": str(config)})
        assert response.status_code == 200
        run = response.json()
        preview = run["correction_suggestion"]["preview"]
        assert preview["change"]["before"]["text"] and preview["change"]["after"]["text"] and preview["change"]["diff"]
        proposal_id, digest = preview["request"]["proposal_id"], preview["candidate_digest"]
        url = base + "/document-corrections/" + proposal_id
        original = Path(run["result"]).read_bytes()
        assert client.get(url + "/preview", params={"candidate_digest": digest}).json() == preview

        def forbidden(*args, **kwargs):
            raise AssertionError("Light polling must not load the full preview or recompute proposal/Git material")

        with monkeypatch.context() as patch:
            for name in ("get_preview", "check_native", "_snapshot"):
                patch.setattr(document_corrections, name, forbidden)
            for _ in range(2):
                status = client.get(url).json()
                assert status["preview"] is None and status["candidate_digest"] == digest and status["can_apply"] is True
                session = client.get(base + "/agent-sessions/" + run["id"]).json()
                suggestion = session["turns"][0]["correction_suggestion"]
                assert suggestion["preview"] is None and suggestion["candidate_digest"] == digest
                recorded = client.get(base + "/agent-runs").json()[0]
                assert recorded["id"] == run["id"]
                if "correction_suggestion" in recorded:
                    assert recorded["correction_suggestion"]["preview"] is None
                    assert recorded["correction_suggestion"]["candidate_digest"] == digest
                output = client.get(base + "/agent-runs/" + run["id"] + "/output").json()
                assert output["result"]["text"].encode("utf-8") == original
                if "correction_suggestion" in output:
                    assert output["correction_suggestion"]["preview"] is None
            final = state.root / "runs" / (run["id"] + ".session-turn") / "final"
            final.rename(final.with_name("saved-final"))
            assert client.get(url).json()["can_apply"] is False
            changed = client.get(base + "/agent-sessions/" + run["id"]).json()
            assert changed["status"] == "unknown" and changed["turns"][0]["correction_suggestion"]["can_apply"] is False
        assert Path(run["result"]).read_bytes() == original
        assert len((repo / "native-calls.jsonl").read_text().splitlines()) == 1


def test_project_sessions_http_and_cli_preserve_exact_operation_inputs(console, tmp_path, monkeypatch, capsys):
    import ergora.agents.runs as agent_runs
    import ergora.interfaces.cli as cli

    client, state, _ = console
    calls = []
    root = {"id": "session-root", "project": "demo", "status": "succeeded", "session": {"id": "session-root"}}
    page = {"sessions": [{"id": root["id"], "birth_intent": "birth-once"}], "next_after": None}
    detail = {"id": root["id"], "turns": [root], "next_after": None}
    receipt = {"run_id": root["id"], "dispatch": "accepted", "run": root}
    stopped = {"run_id": "exact-turn", "stop_requested": True, "notification": "unconfirmed", "run": root}

    def start(control, project, role, prompt, timeout, skill_names, recall, template, **options):
        calls.append((control.root, project, role, prompt, timeout, skill_names, recall, template, options))
        return root

    def listing(control, project, **options):
        calls.append((control.root, project, options))
        return page

    def inspect(control, project, session, **options):
        calls.append((control.root, project, session, options))
        return detail

    def followup(control, project, session, parent, prompt, **options):
        calls.append((control.root, project, session, parent, prompt, options))
        return root

    def inspect_continuation(control, project, session, parent, intent):
        calls.append((control.root, project, session, parent, intent))
        return receipt

    def stop(control, project, session, run, **options):
        calls.append((control.root, project, session, run, options))
        return stopped

    monkeypatch.setattr(agent_runs, "run_agent", start)
    monkeypatch.setattr(agent_runs, "sessions", listing)
    monkeypatch.setattr(agent_runs, "inspect_session", inspect)
    monkeypatch.setattr(agent_runs, "continuation_receipt", inspect_continuation)
    monkeypatch.setattr(agent_runs, "continue_session", followup)
    monkeypatch.setattr(agent_runs, "stop_session", stop)
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Continue developing: café\n", encoding="utf-8")
    config = tmp_path / "native options.toml"
    payload = {"role": "implementer", "prompt": prompt.read_text(), "timeout": 71, "skills": ["original-skill"],
               "recall": "original memory", "template": "large-change", "session_intent": "birth-once",
               "expected_revision": 3, "codex_config": str(config)}
    base = "/api/projects/demo"
    assert client.post(base + "/agent-runs", json=payload).json() == root
    initial = calls.pop()
    assert initial == (state.root, "demo", "implementer", prompt.read_text(), 71, ["original-skill"],
                       "original memory", "large-change", {"session_intent": "birth-once", "expected_revision": 3, "codex_config": config})
    prefix = ["--home", str(state.root), "agent"]
    assert cli.main(prefix + ["run", "demo", "implementer", "--prompt", str(prompt), "--timeout", "71",
        "--skill", "original-skill", "--recall", "original memory", "--template", "large-change",
        "--session-intent", "birth-once", "--revision", "3", "--codex-config", str(config)]) == 0
    assert calls.pop() == initial and json.loads(capsys.readouterr().out) == root
    assert client.get(base + "/agent-sessions?after=2&limit=7&intent_id=birth-once").json() == page
    listing_call = calls.pop()
    assert listing_call == (state.root, "demo", {"after": 2, "limit": 7, "intent_id": "birth-once"})
    assert cli.main(prefix + ["sessions", "demo", "--after", "2", "--limit", "7", "--intent", "birth-once"]) == 0
    assert calls.pop() == listing_call and json.loads(capsys.readouterr().out) == page
    url = base + "/agent-sessions/session-root"
    assert client.get(url + "?after=1&limit=4").json() == detail
    inspect_call = calls.pop()
    assert inspect_call == (state.root, "demo", "session-root", {"after": 1, "limit": 4})
    assert cli.main(prefix + ["session", "demo", "session-root", "--after", "1", "--limit", "4"]) == 0
    assert calls.pop() == inspect_call and json.loads(capsys.readouterr().out) == detail
    continuation = {"parent_run_id": "exact-parent", "prompt": prompt.read_text(), "expected_revision": 3,
                    "intent_id": "continue-once", "timeout": 83}
    assert client.post(url + "/continue", json=continuation).json() == root
    followup_call = calls.pop()
    assert followup_call == (state.root, "demo", "session-root", "exact-parent", prompt.read_text(),
                             {"expected_revision": 3, "intent_id": "continue-once", "timeout": 83})
    assert cli.main(prefix + ["continue", "demo", "session-root", "--parent", "exact-parent", "--prompt", str(prompt),
        "--revision", "3", "--intent", "continue-once", "--timeout", "83"]) == 0
    assert calls.pop() == followup_call and json.loads(capsys.readouterr().out) == root
    assert client.get(url + "/continuations/continue-once", params={"parent_run_id": "exact-parent"}).json() == receipt
    receipt_call = calls.pop()
    assert receipt_call == (state.root, "demo", "session-root", "exact-parent", "continue-once")
    assert cli.main(prefix + ["continuation-receipt", "demo", "session-root", "--parent", "exact-parent",
        "--intent", "continue-once"]) == 0
    assert calls.pop() == receipt_call and json.loads(capsys.readouterr().out) == receipt
    assert client.post(url + "/stop", json={"run_id": "exact-turn", "intent_id": "stop-once"}).json() == stopped
    stop_call = calls.pop()
    assert stop_call == (state.root, "demo", "session-root", "exact-turn", {"intent_id": "stop-once"})
    assert cli.main(prefix + ["stop", "demo", "session-root", "--run", "exact-turn", "--intent", "stop-once"]) == 0
    assert calls.pop() == stop_call and json.loads(capsys.readouterr().out) == stopped

    # Transport validation cannot add execution authority or silently coerce revision/budget values.
    for change in ({"expected_revision": True}, {"timeout": "83"}, {"cwd": "/elsewhere"}, {"native_uuid": "external"}):
        assert client.post(url + "/continue", json={**continuation, **change}).status_code == 422
    assert client.get(base + "/agent-sessions?after=-1").status_code == 422
    assert client.post(url + "/stop", json={"run_id": "exact-turn", "intent_id": "stop-once"},
                       headers={"X-Ergora-Request": ""}).status_code == 403
    assert client.post(url + "/continue", json=continuation, headers={"Origin": "https://other.example"}).status_code == 403
    assert calls == []


@pytest.mark.skipif(sys.platform != "linux", reason="Persistent native turns use the Linux process owner")
def test_project_native_session_http_and_cli_share_original_development_chain(native_session_case, tmp_path):
    state, repo, config, _ = native_session_case
    revision = state.project("demo")["revision"]
    base = "/api/projects/demo/agent-sessions"
    headers = {"Origin": "http://127.0.0.1:8977", "X-Ergora-Request": "1"}
    with TestClient(create_app(state.root), base_url="http://127.0.0.1:8977", headers=headers) as client:
        rejected = client.post("/api/projects/demo/agent-runs", json={"role": "implementer", "prompt": "stale start",
            "timeout": 10, "session_intent": "rejected-birth", "expected_revision": revision - 1, "codex_config": str(config)})
        assert rejected.status_code == 400
        assert rejected.json() == {"error": "Session start requires the current project revision", "admission_rejected": True,
                                   "native_effect_started": False, "intent_id": "rejected-birth"}
        oversized = client.post("/api/projects/demo/agent-runs", json={"role": "implementer", "prompt": "X" * 1_000_001,
            "session_intent": "oversized-birth", "expected_revision": revision, "codex_config": str(config)})
        assert oversized.status_code == 400 and oversized.json()["admission_rejected"] is True
        assert oversized.json()["intent_id"] == "oversized-birth" and not oversized.json()["native_effect_started"]
        assert client.get(base, params={"intent_id": "rejected-birth"}).json()["sessions"] == []
        assert not (repo / "native-calls.jsonl").exists()
        # Discard the submitted call's reply and recover only by its exact original birth intent.
        response = client.post("/api/projects/demo/agent-runs", json={"role": "implementer", "prompt": "HTTP first change",
            "timeout": 10, "session_intent": "http-birth", "expected_revision": revision, "codex_config": str(config)})
        assert response.status_code == 200
        del response
        observed = client.get(base, params={"intent_id": "http-birth"}).json()
        assert len(observed["sessions"]) == 1 and observed["next_after"] is None
        session = observed["sessions"][0]
        assert session["birth_intent"] == "http-birth" and session["sandbox"] == "workspace-write"
        assert session["can_continue"] and (repo / "turn-1.txt").read_text() == "HTTP first change"
        assert client.get(base, params={"intent_id": "unrelated-birth"}).json()["sessions"] == []
        assert client.get(base.replace("/demo/", "/other/")).status_code == 400
        continuation_url = f"{base}/{session['id']}/continuations/http-next"
        parent = {"parent_run_id": session["latest_run"]}
        assert client.get(continuation_url, params=parent).json()["dispatch"] == "unrecorded"
        response = client.post(f"{base}/{session['id']}/continue", json={**parent, "prompt": "HTTP second change",
            "expected_revision": revision, "intent_id": "http-next", "timeout": 10})
        assert response.status_code == 200
        del response
        receipt = client.get(continuation_url, params=parent).json()
        assert receipt["dispatch"] == "accepted" and receipt["intent_id"] == "http-next"
        assert receipt["native_start"]["status"] == "started"
        assert client.get(continuation_url, params={"parent_run_id": "another-parent"}).status_code == 400
        second = receipt["run"]
        assert second["status"] == "succeeded", second
        assert second["session"]["parent_run"] == session["latest_run"]
        assert second["formal_execution_authorized"] is False
        prompt = tmp_path / "third.md"
        prompt.write_text("CLI third change")
        process = subprocess.run([sys.executable, "-m", "ergora", "--home", str(state.root), "agent", "continue", "demo",
            session["id"], "--parent", second["id"], "--prompt", str(prompt), "--revision", str(revision),
            "--intent", "cli-third", "--timeout", "10"], capture_output=True, text=True, timeout=20)
        assert process.returncode == 0, process.stderr
        third = json.loads(process.stdout)
        assert third["status"] == "succeeded", third
        first_page = client.get(f"{base}/{session['id']}?limit=2").json()
        final_page = client.get(f"{base}/{session['id']}?after={first_page['next_after']}&limit=2").json()
        assert [turn["session"]["ordinal"] for turn in first_page["turns"] + final_page["turns"]] == [0, 1, 2]
        assert final_page["next_after"] is None and final_page["latest_run"] == third["id"]
        output = client.get(f"/api/projects/demo/agent-runs/{third['id']}/output").json()
        assert output["result"]["available"] and output["result"]["text"] == "fixture-original turn 3"
        assert output["result"]["sha256"] == third["result_sha256"]
        assert (repo / "turn-2.txt").read_text() == "HTTP second change"
        assert (repo / "turn-3.txt").read_text() == "CLI third change"
        calls = [json.loads(line) for line in (repo / "native-calls.jsonl").read_text().splitlines()]
        assert len(calls) == 3 and len({call["id"] for call in calls}) == 1
        assert len({call["home"] for call in calls}) == 1


@pytest.mark.skipif(sys.platform != "linux", reason="Native archive reads admit Linux/WSL2")
def test_native_history_http_and_cli_read_the_same_saved_run_without_mutating_it(console):
    client, state, _ = console
    run_id = "saved-harness-run"
    protocol = state.root / "runs" / (run_id + ".protocol")
    cwd = state.root / "runs" / (run_id + ".cwd")
    home = protocol / "native-home"
    archive = home / "sessions/project/native-session/session.v4.jsonl"
    archive.parent.mkdir(parents=True)
    identity = {"home": str(home), "session_id": "native-session", "profile": "sdk-minimal"}
    (protocol / "native-identity.json").write_text(json.dumps(identity))
    raw = (json.dumps({"version": 4, "id": "native-session", "cwd": str(cwd)}) + "\n" +
           json.dumps({"text": "保存的回复🙂" * 30}, ensure_ascii=False) + "\n").encode()
    archive.write_bytes(raw)
    document = {"id": run_id, "project": "demo", "status": "succeeded", "binding": {"tool": "deepseek-harness"}}
    encoded = json.dumps(document)
    with state.connect() as db:
        db.execute("INSERT INTO agent_runs VALUES (?, ?, ?)", (run_id, "demo", encoded))
    url = f"/api/projects/demo/agent-runs/{run_id}/output"
    first = client.get(url, params={"native_history": True, "history_limit": 255})
    assert first.status_code == 200
    page = first.json()["native_history"]
    assert page["next_offset"] is not None
    args = [sys.executable, "-m", "ergora", "--home", str(state.root), "agent", "output", "demo", run_id,
            "--native-history", "--history-limit", "255"]
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == first.json()
    assert client.get(url, params={"native_history": True, "history_offset": page["next_offset"]}).status_code == 400
    cursor = {"native_history": True, "history_offset": page["next_offset"], "history_limit": 255,
              "history_revision": page["revision"]}
    following = client.get(url, params=cursor)
    assert following.status_code == 200 and following.json()["native_history"]["offset"] == page["next_offset"]
    assert client.get(url.replace("/demo/", "/other/"), params=cursor).status_code == 400
    assert archive.read_bytes() == raw
    with state.connect() as db:
        assert db.execute("SELECT document FROM agent_runs WHERE id=?", (run_id,)).fetchone()[0] == encoded


def test_memory_provenance_search_conflict_and_restore(console):
    client, state, _ = console
    base = "/api/projects/demo/memories"
    payload = {"text": '<img src=x onerror="alert(1)"> observed text', "source": {"uri": "manual:fixture", "revision": "v1"}}
    created = client.post(base, json=payload).json()
    assert memory.records(State(state.root), "demo")[0]["text"] == payload["text"]
    memory.save(state, "demo", "Corrected observation", payload["source"], created["id"], 1)
    assert client.post(base, json={**payload, "id": created["id"], "revision": 1}).status_code == 400
    restored = client.post(f"{base}/{created['id']}/restore", json={"from_revision": 1, "revision": 2}).json()
    assert restored["revision"] == 3 and restored["text"] == payload["text"]
    searched = client.get("/api/projects/demo/memory-search", params={"query": "observed"}).json()
    assert searched["results"][0]["id"] == created["id"]
    assert client.get("/api/projects/other/dashboard").json()["memories"] == []
    assert client.request("DELETE", f"{base}/{created['id']}", json={"revision": 3}).status_code == 200
    expired = client.post(base, json={**payload, "expires_at": "2001-01-01T08:00:00+08:00"}).json()
    assert client.get("/api/projects/demo/dashboard").json()["memories"] == []
    catalog = client.get("/api/projects/demo/memory-catalog").json()
    assert catalog["records"][0] == {"record": expired, "validity": "expired"} and catalog["observed_at"]
    corrected = client.post(base, json={**payload, "id": expired["id"], "revision": 1}).json()
    assert corrected["expires_at"] == expired["expires_at"]
    renewed = client.post(base, json={**payload, "id": expired["id"], "revision": 2, "expires_at": None}).json()
    assert "expires_at" not in renewed
    assert client.get("/api/projects/demo/memory-search", params={"query": "observed"}).json()["results"] == [renewed]


def test_all_templates_and_formal_dag_constraints(console):
    client, state, _ = console
    for kind in ("repository-governance", "large-change"):
        task_input = client.get(f"/api/templates/{kind}").json()["input"]
        payload = {"id": kind, "kind": kind, "input": task_input, "revision": 0}
        assert client.post("/api/projects/demo/drafts/validate", json=payload).json()["status"] == "PASS"
        saved = client.post("/api/projects/demo/drafts", json=payload).json()
        assert saved["state"] == "draft" and saved["revision"] == 1
        assert client.post("/api/projects/demo/drafts", json=payload).status_code == 400
        units = task_input["work_units"]
        units[0]["depends_on"] = [units[1]["id"]]
        units[1]["depends_on"] = [units[0]["id"]]
        assert client.post("/api/projects/demo/drafts/validate", json=payload).status_code == 400
    task_input = client.get("/api/templates/repository-governance").json()["input"]
    task_input["work_units"][1]["paths"] = task_input["work_units"][0]["paths"]
    assert client.post("/api/projects/demo/drafts", json={"id": "overlap", "kind": "repository-governance", "input": task_input, "revision": 0}).status_code == 400
    training = client.get("/api/templates/training-optimization").json()
    assert {"workload-contract.md", "experiment.json", "baseline.json"} <= set(training["files"])
    assert client.get("/api/projects/other/dashboard").json()["drafts"] == []
    assert len(client.get("/api/projects/demo/dashboard").json()["drafts"]) == 2


def test_template_roles_and_structured_agent_selection(console):
    import ergora.agents.invocation as agents
    client, state, repo = console
    bootstrap = client.get("/api/bootstrap").json()
    assert bootstrap["layers"]["reviewer"]["requires"] == ["independent-candidate-review"]
    command = next(item for item in bootstrap["tools"]["reviewer"] if item["tool"] == "command")
    assert command["configuration"]["properties"]["capabilities"]["default"] == ["independent-candidate-review"]
    assert command["configuration"]["required"] == ["tool", "argv"]
    assert set(bootstrap["agent_contracts"]) == set(bootstrap["templates"])
    for kind, contract in bootstrap["agent_contracts"].items():
        assert client.get(f"/api/templates/{kind}").json()["agents"] == contract
    binding = {"tool": "command", "argv": [sys.executable, str(Path(__file__).parent / "fixtures/stage_agent.py")],
               "protocol": "stage-json-v1", "capabilities": agents.ROLE_CAPABILITIES["experiment-planner"]}
    path = "/api/projects/demo/bindings/experiment-planner"
    assert client.put(path, json={"binding": binding, "revision": 1}).status_code == 200
    response = client.post("/api/projects/demo/agent-runs", json={"role": "experiment-planner", "template": "training-optimization", "prompt": "Propose an experiment"})
    result = response.json()
    assert result["status"] == "succeeded"
    assert set(json.loads(Path(result["result"]).read_text())["artifacts"]) == {"hypothesis", "experiment-proposal"}
    assert client.post("/api/projects/demo/agent-runs", json={"role": "verifier", "prompt": "Bypass trusted checks"}).status_code == 400
    assert client.post("/api/projects/demo/kernel-runs", json={"action": "plan"}).status_code == 400


def test_skill_evidence_and_adoption_use_existing_business_gate(console, tmp_path):
    client, state, repo = console
    directory = tmp_path / "api-skill"
    directory.mkdir()
    baseline_text = "---\nname: api-skill\ndescription: API fixture\n---\nBASELINE\n"
    directory.joinpath("SKILL.md").write_text(baseline_text)
    baseline = client.post("/api/projects/demo/skills/import", json={"directory": str(directory)}).json()
    directory.joinpath("SKILL.md").write_text(baseline_text.replace("BASELINE", "IMPROVED"))
    candidate = client.post("/api/projects/demo/skills/import", json={"directory": str(directory), "hypothesis": "Measured fixture gain"}).json()
    diff = client.get("/api/projects/demo/skills/diff", params={"baseline": baseline["digest"], "candidate": candidate["digest"]}).json()
    assert "+IMPROVED" in diff["diff"] and diff["changed_files"] == ["SKILL.md"]
    evaluator = repo / "evaluate.py"
    evaluator.write_text('import json,sys,pathlib\nr=json.load(sys.stdin)\ns=.9 if "IMPROVED" in pathlib.Path(r["skill_dir"],"SKILL.md").read_text() else .5\nprint(json.dumps({"score":s,"passed":True,"cost":0,"feedback":"fixture"}))\n')
    manifest = {"schema_version": 1, "evaluator_argv": [sys.executable, str(evaluator)], "evaluator_files": [str(evaluator)], "timeout_seconds": 5, "minimum_gain": .1, "max_reported_cost": 1, "cases": [{"id": split, "split": split, "input": {"task": split}} for split in ("train", "validation", "holdout")]}
    suite = client.post("/api/projects/demo/evaluations/suites", json=manifest).json()
    runs = [client.post("/api/projects/demo/evaluations/run", json={"digest": digest, "suite": suite["digest"]}).json() for digest in (baseline["digest"], candidate["digest"])]
    comparison = client.get("/api/projects/demo/evaluations/compare", params={"baseline": runs[0]["id"], "candidate": runs[1]["id"]}).json()
    assert comparison["eligible"]
    payload = {"baseline_run": runs[0]["id"], "candidate_run": runs[1]["id"], "revision": 1, "reason": "Reviewed API fixture evidence"}
    assert client.post("/api/projects/demo/skills/adopt", json=payload).status_code == 200
    assert skill_assets.versions(State(state.root), "demo")["active"][0]["digest"] == candidate["digest"]
    assert client.post("/api/projects/demo/skills/adopt", json=payload).status_code == 400


@pytest.mark.parametrize("clean_exit", [False, True])
def test_reported_cost_failure_http_cli_and_dashboard_retain_subtotal(console, tmp_path, monkeypatch, capsys, clean_exit):
    import ergora.improvement.evaluation as evaluation
    from ergora.interfaces.cli import main

    client, state, repo = console
    source = tmp_path / "accounting-skill"
    source.mkdir()
    (source / "SKILL.md").write_text("---\nname: accounting-skill\ndescription: Cost reporting fixture\n---\nEvidence\n")
    baseline = client.post("/api/projects/demo/skills/import", json={"directory": str(source)}).json()
    evaluator = repo / "accounting.py"
    evaluator.write_text("raise AssertionError('This source fixture must use its in-process port')\n")
    manifest = {"schema_version": 1, "evaluator_argv": [sys.executable, str(evaluator)], "evaluator_files": [str(evaluator)],
                "timeout_seconds": 5, "minimum_gain": .1, "max_reported_cost": 1,
                "cases": [{"id": split, "split": split, "input": {"task": split}} for split in ("train", "validation", "holdout")]}
    suite = client.post("/api/projects/demo/evaluations/suites", json=manifest).json()
    calls = []

    def process(argv, cwd, output, *args, **kwargs):
        calls.append(output)
        output.mkdir(parents=True)
        if output.name == "train":
            payload = {"score": 1, "passed": True, "cost": .25, "feedback": "Port fixture"}
        else:
            assert output.name == "validation", "No holdout call may follow an unevaluable result"
            payload = {"outcome": "unevaluable", "cost": .375, "feedback": "No score"}
        succeeded = output.name == "train" or clean_exit
        (output / "stdout.txt").write_text(json.dumps(payload))
        return {"status": "succeeded" if succeeded else "failed", "returncode": 0 if succeeded else 2,
                "output": str(output)}

    monkeypatch.setattr(evaluation.processes, "run", process)
    result = client.post("/api/projects/demo/evaluations/run", json={"digest": baseline["digest"], "suite": suite["digest"]}).json()
    subtotal = .625 if clean_exit else .25
    assert result["status"] == "failed" and result["reported_cost"] == subtotal
    assert result["reported_cost_complete"] is clean_exit and len(result["cases"]) == 2
    row = result["cases"][-1]
    assert {"score", "passed"}.isdisjoint(row)
    if clean_exit:
        assert row["outcome"] == "unevaluable" and row["cost"] == .375 and row["returncode"] == 0
    else:
        assert {"outcome", "cost"}.isdisjoint(row) and row["returncode"] == 2
    assert main(["--home", str(state.root), "evaluation", "show", "demo", result["id"]]) == 0
    assert json.loads(capsys.readouterr().out) == result
    observed = client.get("/api/projects/demo/dashboard").json()["evaluations"]["runs"]
    assert observed == [result] and len(calls) == 2
    if clean_exit:
        assert main(["--home", str(state.root), "evaluation", "run", "demo", baseline["digest"], "--suite", suite["digest"]]) == 1
        run = json.loads(capsys.readouterr().out)
        assert run["status"] == "failed" and run["reported_cost"] == subtotal and run["reported_cost_complete"] is True
        assert run["cases"][-1]["outcome"] == "unevaluable" and len(calls) == 4


@pytest.mark.skipif(sys.platform != "linux", reason="mini driver explicitly requires Linux/bash")
def test_slow_optional_mini_probe_keeps_dashboard_repairable(console, tmp_path):
    client, state, _ = console
    slow = tmp_path / "slow-python"
    slow.write_text(f"#!{sys.executable}\nimport time;time.sleep(8)\n")
    slow.chmod(0o700)
    path = "/api/projects/demo/bindings/implementer"
    binding = {"tool": "mini-swe-agent", "model": "provider/model", "python": str(slow)}
    assert client.put(path, json={"binding": binding, "revision": 1}).status_code == 200
    response = client.get("/api/projects/demo/dashboard")
    assert response.status_code == 200
    check = next(item for item in response.json()["tools"]["checks"] if item["layer"] == "implementer")
    assert check["installed"] is False
    assert client.put(path, json={"binding": {"tool": "codex"}, "revision": 2}).status_code == 200


def test_training_cycle_status_http_preserves_the_original_owner_projection(console, monkeypatch):
    import ergora.training.cycles as training_cycles

    client, state, _ = console
    original = state.project('demo')
    expected_sha = 'a' * 64
    observed = {'cycle_id': 'fixed-search', 'status': 'ready', 'runtime_status': 'not_queried',
                'search': {'status': 'needs_reconciliation', 'sequence_trials': 2, 'executed_trials': 1,
                           'skipped_trials': 1, 'promising_count': 0, 'full_accepted_count': 0,
                           'verified_gain_count': 0}}
    calls = []

    def status(control, project, cycle, *, authorization_sha256=None):
        calls.append((control.root, project, cycle, authorization_sha256))
        if authorization_sha256 not in (None, expected_sha):
            raise ValueError('Original cycle authorization changed')
        return observed

    monkeypatch.setattr(training_cycles, 'status', status)
    url = '/api/projects/demo/training-cycles/fixed-search'
    assert client.get(url).json() == observed
    assert client.get(url, params={'authorization_sha256': expected_sha}).json() == observed
    assert client.get(url, params={'authorization_sha256': 'b' * 64}).status_code == 400
    assert calls == [(state.root, 'demo', 'fixed-search', digest) for digest in (None, expected_sha, 'b' * 64)]
    assert state.project('demo') == original
