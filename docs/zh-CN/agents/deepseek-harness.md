# DeepSeek Harness 只读叶后端

简体中文 · [English](../../agents/deepseek-harness.md) · [文档目录](../../README.zh-CN.md)

可选适配固定为 SDK／runtime-bin `0.2.2rc2`，使用独立环境；基础 Ergora 不依赖它。目前支持 Linux/WSL2 的 `composition check-input/run-input`，模式为 `text-only` 或 `task-mcp`，角色为 reviewer、experiment-planner、performance-analyst、kernel-tuner。后两类产物仍是文本提案，不是实际测量或 kernel 执行。此后端支持独立受限调用与已存历史观察；持久native开发会话、`agent run` 的原生调用、workspace写入和正式任务恢复尚不支持；OpenHands SDK 暂未注册。

安装器已提供 uv 后，可在持久目录单独安装：

```bash
ERGORA_DSH_ENV="$HOME/.local/share/ergora-tools/deepseek-harness/0.2.2rc2/.venv"
uv venv --python 3.12 "$ERGORA_DSH_ENV"
uv pip install --python "$ERGORA_DSH_ENV/bin/python" \
  'deepseek-harness-sdk==0.2.2rc2' 'deepseek-harness-runtime-bin==0.2.2rc2'
```

在所选[Agent定义的新版本](../../definitions/agents.md#derive-a-new-version-from-a-pinned-original-bundle)中设置完整 `backend`；解释器替换为上一步实际绝对路径，模型与URL替换为自己服务的值：

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

`api` 显式选择 `openai-responses` 或 `openai-completions`；省略时保持 Chat Completions。选择服务实际提供的入口，平台不会因失败自动切换协议；task-MCP 还须兼容所选协议的工具调用及 SSE。环境变量由启动 Ergora 的 shell 提供，不把密钥填入JSON。`context_window`和`max_tokens`按实际模型配置，默认值不证明服务支持相同容量。包版本诊断不调用模型，也不证明认证、网关或模型质量通过。

发布新的 Agent 版本并沿父引用准备新输入，保留完整祖先资料及权限上限，然后调用：

```bash
ergora composition check-input my-project ./prepared-review --mode task-mcp
ergora composition run-input my-project ./prepared-review --mode task-mcp --timeout 300
ergora agent runs my-project
ergora agent output my-project RUN_ID
```

这里采用叶定义的完整后端配置。单独 `--backend deepseek-harness` 不会填充必需的解释器、服务和认证变量名。只含内联资料时可显式选择text-only；有Skill附件时用task-mcp，按[全文读取说明](../../definitions/workflows/leaf-calls.md#verify-complete-attachment-reads)检查原回执。

默认调用使用新原生home／session、固定最小profile与生成的patch；无原生shell、文件、工作目录及额外MCP工具。task-mcp只提供原scope的list/read。适配保存原生身份、完整prompt、事件和终值到本次`.protocol`目录，整体时限／停止仍由原进程owner负责。这不提供OS隔离。

必须同时核对完成状态、严格JSON／原结果schema和原MCP连接回执；任一原生工具错误使本次调用失败，不隐式重试或续接会话。上游可能在插件失败或断连后仍返回completed，因此最终文本本身不能代表成功。失败或结果不明先按原run ID查看证据，不创建另一次调用冒充恢复。正式六阶段、持久会话和其他平台须分别满足对应后端合同与验收。

## 查看已保存的原生历史

Linux／WSL2 可在原调用记录页点击“读取原生历史”，然后逐页查看保存的输入、工具结果和模型回复。读取只访问原 run 的归档，不启动 SDK、不调用模型，也不恢复会话；其他后端会显示不支持。原 stdout／stderr 查看方式保持。

```bash
ergora agent output my-project RUN_ID --native-history
# 下一页：使用上一页返回的 next_offset 和 revision
ergora agent output my-project RUN_ID --native-history \
  --history-offset NEXT_OFFSET --history-revision REVISION
```

每页默认最多 65,536B，可用 `--history-limit` 在 4–65,536B 内调整；游标以字节为单位，返回内容保持 UTF-8 边界。网页只展示当前一页，完整导出可由调用者逐页保存 `native_history.content`，直到 `next_offset` 为 null。观察 revision 绑定当前文件身份和时间／大小，不是完整内容 SHA，也不证明写入者已停止。读取期间文件变化会拒绝旧页，应“从头读取”或不带旧 revision 从零开始。只支持原调用保存的、未压缩的 v4 单会话归档；归档丢失、ID／目录不符或未来存储代次不能当作空历史。归档末尾不等于成功完成，原调用状态和结果回执仍独立核查。

## 项目原生开发会话

普通 `agent run` 可用明确的出生 intent 和项目修订保存项目会话。在项目总览的“项目会话 / 运行 Agent”选择原历史会话后，只输入新任务说明即可继续；CLI 使用 `agent continue`。角色、模板产物、已选 Skill、记忆和 native 配置在新建时冻结，后续沿原 workspace 权限运行。它与正式任务执行和批准分别处理。Codex会话命令固定`--no-daemon`；清理证据只覆盖本轮实际拥有的进程子树。已确认final回收且原生引用可用的停止轮次可接受新的明确prompt；unknown结果不能重放。

当前 CLI／HTTP 参数、丢回复后的精确 intent 观察和逐轮停止见[项目会话操作](../../operations/services.md#project-native-sessions)。持久接口选择 Linux／WSL2 的 Codex，不因此启用其他后端的持久能力。既有单次 composition 结果和原生归档仍通过原 run／output 记录观察。
