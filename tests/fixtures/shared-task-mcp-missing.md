---
{
  "id": "task-mcp-missing-sdk",
  "revision": 1,
  "title": "任务 MCP 缺少可选依赖",
  "aliases": ["任务 MCP 启动失败", "Task MCP SDK missing"],
  "error_signatures": ["Task MCP requires the optional dependency"],
  "applicability": {"technology": "ergora-task-mcp", "environment": "linux", "versions": ["0.2.0"]},
  "status": "verified",
  "sources": [
    {"uri": "https://github.com/626619403/Ergora/blob/3bd4779a0a6fa303e528d285e82b41668812b8db/src/ergora/agents/mcp.py#L23-L27", "revision": "3bd4779a0a6fa303e528d285e82b41668812b8db"},
    {"uri": "https://github.com/626619403/Ergora/blob/3bd4779a0a6fa303e528d285e82b41668812b8db/docs/definitions/workflows/leaf-calls.md#L84-L90", "revision": "3bd4779a0a6fa303e528d285e82b41668812b8db"},
    {"uri": "https://github.com/626619403/Ergora/blob/3bd4779a0a6fa303e528d285e82b41668812b8db/pyproject.toml#L18-L22", "revision": "3bd4779a0a6fa303e528d285e82b41668812b8db"}
  ],
  "expires_at": null
}
---
# 症状 / Symptom

在 Linux 上检查 Task MCP 可用性时出现 `Task MCP requires the optional dependency`。

## 原因 / Cause

运行 Ergora 的 Python 找不到顶层 `mcp` 模块。发行包将 MCP SDK 声明为 `task-mcp` 可选依赖。

## 处理 / Resolution

Use the environment that actually starts Ergora. Inspect whether that interpreter can find the
SDK with `python -c 'import importlib.util; print(importlib.util.find_spec("mcp"))'`. When the
optional SDK is required for this task, install the `task-mcp` extra in that environment and
repeat the original admission check.

## 核验 / Verification

The pinned source raises this exact error after the Linux platform check and only when lookup
of the `mcp` module returns no spec. A passing availability check establishes module discovery.
Use the original Task MCP connection receipt when verifying actual service operation.
