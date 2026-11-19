# Use the DeepSeek Harness backend

English · [Documentation](../README.md) · [简体中文](../zh-CN/agents/deepseek-harness.md)

## DeepSeek Harness read-only leaf backend

The optional adapter pins SDK/runtime-bin `0.2.2rc2` in a separate environment; basic Ergora does not depend on it. Supported Linux/WSL2 entry points are `composition check-input/run-input` in `text-only` or `task-mcp` mode for reviewer, experiment-planner, performance-analyst and kernel-tuner roles. The last two produce textual proposals, not measurements or kernel execution. This backend supports independent restricted calls and saved-history observation. Persistent native development sessions, native `agent run`, workspace writes and formal-task recovery remain unsupported. OpenHands SDK is not registered.

After the installer provides uv, install separately in persistent storage:

```bash
ERGORA_DSH_ENV="$HOME/.local/share/ergora-tools/deepseek-harness/0.2.2rc2/.venv"
uv venv --python 3.12 "$ERGORA_DSH_ENV"
uv pip install --python "$ERGORA_DSH_ENV/bin/python" \
  'deepseek-harness-sdk==0.2.2rc2' 'deepseek-harness-runtime-bin==0.2.2rc2'
```

Set the complete `backend` in a [new version of the selected Agent definition](../definitions/agents.md#derive-a-new-version-from-a-pinned-original-bundle). Replace the interpreter with the actual absolute path above and the model/URL with values for your service:

```json
{
  "tool": "deepseek-harness",
  "python": "/YOUR_HOME/.local/share/ergora-tools/deepseek-harness/0.2.2rc2/.venv/bin/python",
  "model": "YOUR_MODEL_ID",
  "base_url": "https://YOUR_PROVIDER/v1",
  "api_key_env": "LINGZHI_API_KEY",
  "api": "openai-responses",
  "context_window": 131072,
  "max_tokens": 4096
}
```

`api` explicitly selects `openai-responses` or `openai-completions`; omission retains Chat Completions. Choose an interface the service actually provides. The platform does not switch protocols automatically after failure. Task MCP additionally requires compatible tool calls and SSE on that protocol. The shell starting Ergora supplies environment variables; do not put keys in JSON. Configure `context_window` and `max_tokens` for the actual model; defaults do not prove service capacity. Package-version diagnostics call no model and establish neither authentication, gateway nor model quality.

Publish the new Agent version and prepare new input through parent references, retaining complete ancestor materials and permission ceilings, then invoke:

```bash
ergora composition check-input my-project ./prepared-review --mode task-mcp
ergora composition run-input my-project ./prepared-review --mode task-mcp --timeout 300
ergora agent runs my-project
ergora agent output my-project RUN_ID
```

This uses the leaf definition's complete backend configuration. `--backend deepseek-harness` alone does not supply the required interpreter, service or credential-variable name. Explicit text-only mode suits inline-only materials. Use task-mcp for Skill attachments and inspect original receipts through [complete-read verification](../definitions/workflows/leaf-calls.md#verify-complete-attachment-reads).

Default calls use a fresh native home/session, fixed minimal profile and generated patch, without native shell, file, working-directory or extra MCP tools. Task MCP exposes only the original scope's list/read. The adapter saves native identities, complete prompt, events and terminal value in this call's `.protocol` directory. The original process owner retains overall timeout/stop responsibilities. This provides no OS isolation.

Check completion status, strict JSON/original result schema and the original MCP connection receipt together. Any native tool error fails the call, without implicit retry or session continuation. Upstream may return completed after plugin failure/disconnection, so final text alone is not success. On failure or an unknown result, inspect evidence by original run ID before proceeding. Do not create another call as purported recovery. Formal six-stage execution, persistent sessions and other platforms require their own supported backend contract and acceptance.

### Read saved native history

On Linux/WSL2, select “Read native history” on the original invocation record and page through saved inputs, tool results and model replies. Reading accesses only that run's archive, without starting the SDK, invoking models or restoring a session. Other backends report unsupported. Original stdout/stderr viewing remains available.

```bash
ergora agent output my-project RUN_ID --native-history
# Next page: use next_offset and revision from the previous response.
ergora agent output my-project RUN_ID --native-history \
  --history-offset NEXT_OFFSET --history-revision REVISION
```

Each page defaults to at most 65,536B; choose 4–65,536B with `--history-limit`. Cursors use bytes and preserve UTF-8 boundaries. The page displays only the current window. For a complete export, save successive `native_history.content` values until `next_offset` is null. Observed revision binds current file identity and time/size, not a complete content SHA or proof the writer stopped. A changed file refuses an old page. “Read from start” or restart at zero without the old revision. Only the original saved uncompressed v4 single-session archive is supported. Missing archives, mismatched IDs/directories or future storage generations are not empty history. Archive EOF does not mean successful completion; original call status and result receipts remain separate checks.

### Project native development sessions

The ordinary `agent run` path can save a project session with an explicit birth intent and project revision. Select its original history and continue with a new prompt through `agent continue` or the project overview's “项目会话 / 运行 Agent” dialog. Role, template artifacts, selected Skills, memory and native configuration freeze at session creation; later turns use the same native workspace permissions. This is separate from formal-task execution and approval. The Codex session command uses `--no-daemon`; only the turn's owned process subtree is covered by its cleanup evidence. A stopped turn with a confirmed final cleanup and usable native reference can receive a new explicit prompt; an unknown outcome cannot be replayed.

See [project-session operations](../operations/services.md#project-native-sessions) for the current CLI/HTTP inputs, exact-intent observation after a lost reply and per-turn stop. The persistent interface selects Codex on Linux/WSL2; it does not enable other backends' persistent capabilities. Existing single-use composition results and native archives remain observable through their original run/output records.

Continue: [Configure and authenticate Agents](configuration.md) · [Invoke and inspect one frozen workflow leaf](../definitions/workflows/leaf-calls.md).
