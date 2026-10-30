from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from dev_platform.contracts import path_contains

from .core import CONFIG, STATE, git, project, read, require, settings, slug, write
from .sandbox import Sandbox, model_protocol


class SearchState(TypedDict):
    project: str
    search_id: str
    baseline_sha: str
    goal: str
    limit: int
    negative_results: str
    candidates: list[dict]


def graph(checkpointer):
    def load(state: SearchState):
        p = project(state["project"])
        require(p["base_sha"] == state["baseline_sha"], "Project baseline changed; create a new search ID")
        negative = STATE / "search" / "negative-results.jsonl"
        records = [negative.read_text()[-20000:]] if negative.exists() else []
        for path in sorted((STATE / 'training/negative-results').glob('*.json')):
            value = read(path)
            if value['project'] == state['project']: records.append(json.dumps(value, ensure_ascii=False))
        return {"negative_results": '\n'.join(records)[-40000:]}

    def propose(state: SearchState):
        p = project(state["project"])
        folder = STATE / "search" / state["search_id"]
        checkout = folder / "checkout"
        if not checkout.exists():
            folder.mkdir(parents=True, exist_ok=True)
            git(folder, "clone", "--no-local", p["repo"], str(checkout))
            git(checkout, "checkout", "--detach", state["baseline_sha"])
        output = folder / "output"
        result_schema = {"type": "object", "properties": {"candidates": {"type": "array", "minItems": 1,
             "maxItems": state["limit"], "items": {"type": "object", "properties": {
             "title": {"type": "string"}, "mechanism": {"type": "string"}, "paths": {"type": "array", "items": {"type": "string"}},
             "validation": {"type": "string"}}, "required": ["title", "mechanism", "paths", "validation"], "additionalProperties": False}}},
             "required": ["candidates"], "additionalProperties": False}
        prompt = """Inspect this read-only repository and propose bounded candidates for the supplied goal.
Explain a concrete mechanism and an independent validation for each. Use only approved paths.
Account for negative results. Produce proposals only; the operator selects a task before any implementation or experiment.
""" + json.dumps({"goal": state["goal"], "baseline_sha": state["baseline_sha"], "checkout": str(checkout),
                  "allowed_paths": p["allowed_paths"], "negative_results": state["negative_results"]}, ensure_ascii=False)
        protocol = folder / "protocol"
        command = model_protocol(protocol, prompt, result_schema, "codex", settings())
        name = "af-search-" + hashlib.sha256(state["search_id"].encode()).hexdigest()[:32]
        code = Sandbox().run(name, checkout, output, command, writable=False, timeout=600, model="codex", protocol=protocol)
        require(code == 0, "Candidate generation failed; inspect search output execution.log")
        return {"candidates": read(output / "result.json")["candidates"]}

    def validate(state: SearchState):
        allowed = project(state["project"])["allowed_paths"]
        candidates = state["candidates"]
        require(1 <= len(candidates) <= state["limit"], "Candidate count exceeds search budget")
        for item in candidates:
            require(set(item) == {"title", "mechanism", "paths", "validation"}, "Unexpected candidate fields")
            require(item["paths"] and all(isinstance(x, str) and x and not x.startswith("/") and
                    all(part not in {"", ".", ".."} for part in x.split("/")) and
                    any(path_contains(prefix, x) for prefix in allowed) for x in item["paths"]), "Candidate widens approved project scope")
        write(STATE / "search" / state["search_id"] / "candidates.json", dict(state))
        return {}

    builder = StateGraph(SearchState)
    for name, node in (("load-baseline", load), ("propose", propose), ("validate", validate)):
        builder.add_node(name, node)
    builder.add_edge(START, "load-baseline")
    builder.add_edge("load-baseline", "propose")
    builder.add_edge("propose", "validate")
    builder.add_edge("validate", END)
    return builder.compile(checkpointer=checkpointer)


def run(name: str, search_id: str, goal: str, limit: int = 3, resume: bool = False) -> dict:
    slug(search_id)
    require(1 <= limit <= 5, "Choose between one and five candidates")
    p = project(name)
    initial: SearchState = {"project": name, "search_id": search_id, "baseline_sha": p["base_sha"],
        "goal": goal, "limit": limit, "negative_results": "", "candidates": []}
    snapshot = STATE / "search" / search_id / "input.json"
    write(snapshot, initial)
    with SqliteSaver.from_conn_string(str(STATE / "search/checkpoints.sqlite3")) as saver:
        app = graph(saver)
        config = {"configurable": {"thread_id": p["base_sha"] + ":" + search_id}, "recursion_limit": 8}
        existing = app.get_state(config)
        require(resume or not existing.values, "Search already exists; use --resume with the same input")
        return app.invoke(None if resume else initial, config=config)
