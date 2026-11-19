# Editor comparison prototype

This developer example compares three interfaces using the same inputs and backend interfaces:

|Entry point|Relationship graph|Property form|
|---|---|---|
|`native.html`|Cytoscape 3.33.1 already bundled with Ergora|Native HTML|
|`flow.html`|React Flow 12.12.1 / React 19.2.0|Native HTML|
|`schema.html`|The same Cytoscape|JSON Forms 3.8.0 / React 19.2.0|

The default Ergora installation depends on neither this example nor Node.js. There are no Agent invocation or formal task submission buttons; it only validates and saves independent experimental drafts through existing APIs. Fields, dependencies, and JSON edit the same input; graph positions are not written into that input. The server continues to own semantic digests, domain validation, and revisions.

## Build and start

Python 3.11+, Git, Node.js, and npm are required. The Bash commands below start at the repository root; runtime environment, state, and project use separate directories. The default port is 8981, adjustable with `--port`.

```bash
python3 -m venv "$HOME/.local/share/ergora-editor-comparison/venv"
"$HOME/.local/share/ergora-editor-comparison/venv/bin/python" -m pip install '.[web]'
mkdir -p "$HOME/projects/ergora-editor-comparison"
git -C "$HOME/projects/ergora-editor-comparison" init
"$HOME/.local/share/ergora-editor-comparison/venv/bin/ergora" \
  --home "$HOME/.local/state/ergora-editor-comparison" \
  project add editor-comparison --repo "$HOME/projects/ergora-editor-comparison"
cd examples/editor-comparison
npm ci --ignore-scripts --no-audit --no-fund
npm run build
"$HOME/.local/share/ergora-editor-comparison/venv/bin/python" prototype/serve.py \
  --home "$HOME/.local/state/ergora-editor-comparison"
```

Open `http://127.0.0.1:8981/comparison/native.html?project=editor-comparison` in a browser and use the top links to switch approaches. The service listens only locally; press Ctrl+C in the terminal to stop. On subsequent runs, reuse your experimental state and project rather than recreating the virtual environment or registering the same project name.

`npm run build` reads existing template schemas, API client, and Cytoscape assets from this source tree. `prototype/dist/` contains three separate complete bundles, per-file raw/gzip sizes, and third-party licenses; `node_modules/` and build output are excluded from Git. Do not treat this developer server as the default product entry point.

## The same editing journey

1. Select `repository-governance` or `large-change`, select a unit, edit its ID, path, or description, then click “更新节点”. Renaming updates dependency references as well.
2. Use the dependency source / target form to add or remove dependencies. Cytoscape also supports Shift-clicking the source then the target; React Flow supports dragging between ports. The form provides a keyboard alternative.
3. Drag nodes or zoom the graph, then click “校验当前输入” to confirm that input and digest are preserved. After editing JSON, explicitly load it with “校验并载入 JSON”.
4. Add a cycle or enter an out-of-bounds path and observe server rejection with input retained. After correcting it, click “保存试验草稿”; saving uses the existing revision checks.

Each approach / template is saved as an `editor-<方案>-<模板>` draft. Opening a page starts from the template; existing drafts are used only to read the revision for saving, and the prototype does not automatically restore their input. It also lacks undo / redo, complete unsaved-change protection, and cross-tab revision conflict handling. These belong to the subsequent formal editor plan.

JSON Forms generates controls using the official `NoValidation` mode. Its default Ajv browser compilation is actually rejected by the existing CSP; this example preserves security headers and delegates explicit validation to the same backend, without client-side Schema error messages. Rules / composition schemas, dynamic schemas, and other renderers were not accepted in this example; do not generalize this mode into a promise of complete JSON Forms compatibility. See [third-party notes (Chinese)](THIRD_PARTY.md).

This round's browser validation ran on Linux, Node 24, and a fixed Chromium version; its results do not cover capacity, other browsers, or running the prototype on Windows. See the [workflow guide](../../docs/definitions/workflows/compose.md) for current product pages and handoff boundaries.
