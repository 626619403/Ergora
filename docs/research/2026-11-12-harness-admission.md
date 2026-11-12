# F8 Harness 准入：OpenHands SDK 固定版本与 DeepSeek 最小接口

日期：2026-11-12；Ergora 产品基线 `784da65da89bdd2fed4742e57e3f904c0f295216`。对应 [F8 分片](../plans/2026-11-12-harness-admission.md)与[总计划 F8／DS5](../plans/2026-11-01-all-in-one.md)。这是 fresh-context 一手资料及源码研究：本研究没有安装依赖、import SDK、请求模型、运行 Harness、执行取消实验或外部业务写入。其他执行者的安装／运行记录须在本片交付记录单独登记，不借本文宣称通过。

## 1. 选择及准入结论

**OpenHands SDK 1.62.0 保留评估，暂缓正式准入；下一步只选择 DeepSeek Python SDK 0.2.2rc2 的 `sdk-minimal` 接口做 H1a 有界探针。两者目前都没有新增 Ergora 兼容结论。**

OpenHands 有真实 Python API、原生结构化 Finish、事件、持久会话及 stdio MCP，但固定版本的 `LocalConversation` 无条件发现用户／项目插件；空 `tools`、空 `plugins`、关闭自动 Skill 均不能关闭这条路径。插件能增加 MCP、hooks、Skill 和 Agent，默认工具还有独立于 regex 的自动附加路径。因此不能把它注册成现有同模板的 `task-mcp`／`text-only` 受限叶，也不能把“原生能调用”当作所有正式角色可替换的证据。[插件装载](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py#L1204) · [默认工具附加](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/agent/base.py#L591)

DeepSeek 的 `sdk-minimal` 是完整、显式的 profile 树，有公开 patch 入口及必须显式指定的 home；可以定向关闭原生工具生产者，再插入原 task MCP。它更适合先证明工具集合和生命周期。不过默认 profile 仍有 shell、图像读取和目录修改，默认策略为 `danger-full-access`；“minimal”本身不满足受限合同。其结果文本可由现有严格 JSON／schema 消费者验证，缺少原生 prompt-cancel 不必然阻止外层取消，但必须实际验证原进程所有者能结束该 runtime 和全部后代。[最小树及边界](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/bundle/sdk-minimal/README.md#L12) · [Python SDK 入口](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/README.md#L29) · [wire 限制](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/sdk/server/README.md#L211)

|判定项|OpenHands 1.62.0|DeepSeek 0.2.2rc2 下一步范围|
|---|---|---|
|存在可原生调用接口|源码确认；未运行|源码及已发布包确认；本研究未运行|
|同模板正式 `task-mcp` 替换|**本版暂不支持**：ambient 与工具自动附加缺口|**尚未准入**：仅评估显式 profile／固定双工具 server|
|结构化终值|官方 Finish `response_schema`；需包裹 Ergora `summary` 字段|`final_response` 是文本；严格解析后交原 schema 验证|
|会话续接|有原生 ID／落盘／恢复；ambient 会重新发现|有明确 `resume_session`；外部进程不恢复|
|取消覆盖与平台|SDK close／interrupt 不等于宿主后代停止|单 invocation 独占 runtime 有静态继承依据；待 Linux／Windows 各自探针|

选择范围只到 SDK driver、配置投影、原始事件与结果验证；不迁入 OpenHands Agent Server／automation、DeepSeek Super-agent、另一个派工器、页面或数据库。

## 2. 固定身份、安装边界和证据来源

### OpenHands：优先核定的固定发布版

|对象|核定身份及依据|
|---|---|
|官方 Python 包|`openhands-sdk==1.62.0`，`Requires-Python: >=3.12`；PyPI 精确版本 JSON 中未 yanked。基础 Ergora 继续 Python >=3.11，SDK 只能放独立可选环境。[精确包元数据](https://pypi.org/pypi/openhands-sdk/1.62.0/json)|
|发布与源码|`v1.62.0`，2026-11-11 12:46:25 UTC 发布；tag API 解到 `504a88cab0fb48ee5226238ad7b8f1d865fa84a8`。[发布](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.62.0) · [tag 对应提交 API](https://api.github.com/repos/OpenHands/software-agent-sdk/commits/v1.62.0)|
|许可|该提交根 `LICENSE` 为 MIT；包 JSON／wheel METADATA 未提供 SPDX 字段，许可结论来自官方源码许可文件。[LICENSE](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/LICENSE)|
|分发|`openhands_sdk-1.62.0-py3-none-any.whl`，993,840 B，SHA256 `1ff083f5bff6090c6e3f0536ed2d3eaff2145536ce54cbcf50f3566167587065`；`any` 是 wheel 分发标签，不是所有平台／工具通过证明。[PyPI 文件](https://pypi.org/project/openhands-sdk/1.62.0/#files)|
|最小依赖边界|SDK 自带 Agent／Conversation／Finish／MCP；terminal、file editor 等另属 `openhands-tools`。本次候选无需安装 tools／workspace／agent-server 包。SDK 本身仍依赖 FastMCP、LiteLLM、Laminar 等，顶层 pin 不冻结整个依赖图；实测须保存完整 resolver 版本与发行文件身份。[包定义](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/pyproject.toml#L1) · [官方 quick start 的分包 import](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/README.md#L64)|

待执行的最小安装配方是 `uv venv --python 3.12 <独立持久环境>`，再对其中的明确 Python 执行 `uv pip install --python <该Python> 'openhands-sdk==1.62.0'`。这是评估环境配方，不能添加到 Ergora 基础依赖，也不是兼容验收。无需为研究安装官方完整开发 workspace。

### DeepSeek：发布包和当前源码分别固定

当前官方源码快照是 `e8f7b93a344964de3dca1ace9e72b6e4d6de87cb`，提交于 2026-11-11，根版本 `0.2.2-rc.2`，MIT，Node 源码环境要求 >=24.9.0。它仍明确标为 developer preview，存在破坏兼容变化。[固定提交](https://api.github.com/repos/deepseek-ai/deepseek-harness/commits/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb) · [根包](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/package.json#L1) · [预览声明](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/README.md#L11)

PyPI 已发布 `deepseek-harness-sdk==0.2.2rc2`，Python >=3.10，精确依赖 `deepseek-harness-runtime-bin==0.2.2rc2` 和 `pydantic>=2.12,<3`。SDK wheel SHA256 为 `ad14f1b1fccb29f7d97e5a7e0ee9dbb96d8af11292308bba66bf19a623d31899`；本研究下载并静态比较其六个 `.py`，与上述提交的 `python/sdk/src/deepseek_harness/` 逐字一致。**未下载／重建 runtime 二进制，不能把这六文件比对扩大成整个 runtime 的源码构建证明。** [SDK 包元数据](https://pypi.org/pypi/deepseek-harness-sdk/0.2.2rc2/json) · [runtime 包元数据](https://pypi.org/pypi/deepseek-harness-runtime-bin/0.2.2rc2/json) · [源码 SDK 定义](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/pyproject.toml#L5)

runtime 实际发布 manylinux_2_28 x86_64／aarch64、macOS 14 arm64／x86_64、win_amd64 wheel；没有 Windows arm64 wheel。该 wheel 包含正常 `dsh` CLI、Node 依赖闭包和原生 helper，启动 SDK 不要求系统 Node，Office／authoring 下载是另一项显式操作。[实际文件清单](https://pypi.org/project/deepseek-harness-runtime-bin/0.2.2rc2/#files) · [runtime 官方说明](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk-runtime/README.md#L5)

本次同时观察到 npm `@deepseek-ai/dsh` 的 `latest` 仍指 `0.2.2-rc.1`，但固定 `0.2.2-rc.2` 已存在。`/releases/latest` 返回 404；不能据此断言没有 npm／PyPI 发布。本次不混用 npm latest 和 Python rc2。[npm latest](https://registry.npmjs.org/@deepseek-ai/dsh/latest) · [npm 固定版本](https://registry.npmjs.org/@deepseek-ai/dsh/0.2.2-rc.2) · [GitHub latest 查询](https://api.github.com/repos/deepseek-ai/deepseek-harness/releases/latest)

## 3. OpenHands 的真实接口及不能跨越的边界

### 构造、模型配置和结构化终值

选定接口是本地 Python `Agent`＋`Conversation`，不使用远程 Agent Server、ACP 或 CLI wrapper。官方最小运行链是 `LLM(...) → Agent(...) → Conversation(agent, workspace) → send_message(prompt) → run()`；workspace 字符串会生成 `LocalWorkspace`。模型、`base_url`、`api_key` 均为真实构造字段，官方 MCP 示例使用 `SecretStr` 和环境引用。[官方运行示例](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/README.md#L64) · [环境模型配置示例](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/examples/01_standalone_sdk/07_mcp_integration.py#L25) · [本地 workspace 构造](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py#L408)

Ergora 只应保存 `api_key_env: LINGZHI_API_KEY` 一类引用，由可选子进程读取 `os.environ[引用名]` 再传给 LLM；不把值写入 binding、request、argv、模板或公开记录。模型名称／provider 协议、base URL 和容量必须由实际配置与调用证明，不能从“可填 OpenAI 风格 URL”推出用户网关兼容。也不要把 inference key 放入 `Conversation.secrets` 供工具注入：后者的职责是工具环境和模型可见的 secret 描述。[secret registry 行为](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py#L3020)

1.62.0 已有**原生结构化最终结果**，无需让模型写文件或截取 Markdown：注册 `FinishTool`，在显式 `Tool(name="FinishTool", params={"response_schema": schema})` 上绑定 Pydantic model 或 JSON Schema，关闭自动注入的同名默认 Finish。官方可运行示例是 `56_structured_output.py`；实现会把 schema 合入工具参数，并在收到／解析时验证。[完整官方示例](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/examples/01_standalone_sdk/56_structured_output.py) · [schema 验证与解析](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/tool/tool.py#L491)

一个实际冲突必须保留：`kind`、`security_risk`、`structured_output`、`summary` 为 response schema 根保留字段，而现有 Ergora 结果根字段有 `summary`。最小映射可用 `{"stage_result": <原schema>}` 外壳，再解包交 `agents.validate_result`；不能原样塞入现有 schema。`parse_last_response(events)` 只找最近相关 ActionEvent，未保证属于当前轮或已成功完成；恢复旧会话时须限定本次事件区间、检查 `execution_status == finished` 和有效 Finish，再解析，不能拿历史 Finish 当新回执。MCP／插件可能使 conversation 内 Agent 被复制，读取工具映射应以 `conversation.agent` 为准。[保留字段](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/tool/tool.py#L64) · [parse_last_response](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/tool/tool.py#L596) · [Agent 配置复制](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py#L1330)

`run()` 返回 `None`，达到迭代上限／stuck 时可能只设置 `error`／`stuck` 而不抛异常；等待确认也能返回。不能用“函数返回／进程 exit 0”推导完成。原生有 `max_iteration_per_run`、`max_budget_per_run`，但费用来源有缺口，外层 wall timeout 仍归原进程所有者。[run 语义与限制](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py#L2136) · [状态枚举](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/conversation/state.py#L49)

### 工具、ambient 和 stdio MCP

|公开控制|实际效果／残留|
|---|---|
|`tools=[]`、`include_default_tools=[]`|显式工具和普通默认工具可关闭；默认通常只有 Finish，Think 需显式加入。但存在后述自动附加路径。[AgentBase 字段](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/agent/base.py#L126)|
|`filter_tools_regex`|筛选已解析显式工具／MCP 工具；默认 built-in 不受筛选。解析／连接已发生，过滤模型可见名字不等于禁止启动 server、hook 或本地配置读取。[初始化顺序](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/agent/base.py#L560)|
|`AgentContext` 的自动加载开关|user/public/project skills 和 memory 默认 false，可以显式固定；不控制 ambient plugin。[字段定义](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/context/agent_context.py#L99)|
|`plugins=[]`／`hook_config=None`|未附加显式插件／hook，但 `LocalConversation` 仍无条件 `load_available_plugins(include_user=True, include_project=True)`，并合并插件 skills、MCP、hooks、agents。已核构造没有公开关闭参数；不能用不存在的参数或私有 monkeypatch 伪装支持。[构造](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py#L233) · [ambient 路径](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py#L1204)|
|独立 `OH_PERSISTENCE_DIR`|可隔离 OpenHands 自身 home，必须在 import 前设定；不覆盖 `Path.home()/.agents/plugins`，也不关闭工作目录和 Git 根目录下的 `.agents/plugins`／`.openhands/plugins`。不能据此称 ambient 已关。[路径规则](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/utils/path.py#L34) · [插件搜索目录](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/plugin/discovery.py#L29)|
|自动 built-in|可调用 AgentSkills 会自动加入 `InvokeSkillTool`；非视觉模型发现已存 vision profile 时自动加入 `VisionInspectTool`，即使 `include_default_tools=[]`。后者用于已有图像的辅助推理，不应误报为任意文件读取；但它仍使“只给两个工具”声明不成立。[附加条件](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/agent/base.py#L593) · [vision profile 发现](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/tool/builtins/vision_inspect.py#L95)|
|系统身份／观测|默认提示还会读 OpenHands persistence 下 `SOUL.md`；可显式系统 prompt 或 `soul_content`，但不能关闭插件路径。Laminar 能受环境启用，评估应固定可传入的 inference／观测配置，而非继承任意环境再声称没有其他网络。[SOUL](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/agent/base.py#L66) · [Laminar 环境](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/observability/laminar.py#L169)|

stdio MCP 的真实插入口是 `Agent(mcp_config={name: MCPServer(command=..., args=..., env=..., cwd=...)})`，字段还有 `timeout`、`enabled`；`MCPServer` 禁止未知字段，没有 `enabled_tools`／`allowed_tools`。可按实际工具名用 Agent regex 过滤，不能直接照搬 Codex 配置。单 server 和多 server 有命名差异，且支持 `tools/list_changed` 动态注册；有效工具集必须实测并保存。[官方完整 MCP 示例](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/examples/01_standalone_sdk/07_mcp_integration.py) · [MCPServer schema](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/mcp/config.py#L504) · [发现及动态更新](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/mcp/utils.py#L396)

### 事件、usage、会话和停止

`callbacks` 收到原生 Pydantic Event，含 id、timestamp、source、parent_id；本地事件默认先持久化再通知调用者。可按 `model_dump(mode="json")` 保存原始事件，并与 invocation 绑定，不另建任务账本。`conversation.conversation_stats.get_combined_metrics()` 提供累计指标，token usages 含 response_id、model、prompt／completion、cache read／write、reasoning。provider 缺 usage 时不应补零，恢复后累计值不能全部算作本次增量。[事件身份](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/event/base.py#L21) · [持久化顺序](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py#L462) · [TokenUsage](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/llm/utils/metrics.py#L34)

**费用不是统一可信账单。** `_compute_cost` 优先读 provider/proxy header，其次 reported usage，再回退 LiteLLM 价格表／显式单价；日志还把 unavailable cost 写成 `float(cost or 0.0)`，错误日志也写零。因此只保存来源明确的自报 usage／费用和覆盖区间，未知仍未知；不能把 accumulated_cost 或日志零直接投成已知花费，也不把估算回填正式计费。[费用来源及日志](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/llm/utils/telemetry.py#L369)

原生 conversation ID 为 UUID；显式给 `persistence_dir` 和同一 ID 可以 create-or-resume，`base_state.json` 保存 Agent／状态，事件由独立存储保存。官方示例展示再次构造后继续输入。恢复允许调用者改变 LLM、context、prompt，并对 tools 做兼容检查；ambient 插件还会从当前磁盘重新发现。所以 SDK resume 不是 Ergora 的冻结授权恢复，H3 必须额外检查原 binding／资料／授权修订、workspace 和原 invocation 身份。[完整 persistence 示例](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/examples/01_standalone_sdk/10_persistence.py) · [create-or-resume 合同](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/conversation/state.py#L499) · [恢复采用 Agent](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/conversation/state.py#L601)

`pause()` 在 step 边界生效；同步 `run()` 中 `interrupt()` 回退为 pause。异步 `arun()` 可取消 asyncio task 并标记 token，但 tool worker thread 可能仍在执行，要求具体 executor 配合 `interrupt()`。`close()` 清理工具 executor；这是 SDK 的清理责任，不是外层已确认所有后代退出。[pause／interrupt／close](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py#L2961) · [仍在运行的 tool thread](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/agent/parallel_executor.py#L222)

特别是 OpenHands MCPClient 明确记载 FastMCP stdio 使用 `start_new_session=True`；SDK close 先做有界 async close，再尝试从 FastMCP transport 内部提取 PID 并 POSIX 进程组 TERM／KILL，失败仅日志记录。普通外层 `killpg(driver_pid)` 不能自动覆盖另一个 session 的 MCP server；Linux supervised subreaper 或 Windows Job 能否兜底须实际证明。[MCP 进程组与清理](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/openhands-sdk/openhands/sdk/mcp/client.py#L210)

官方有 Windows tools CI，但其范围为 Python 3.13 的选定 `tests/tools`，还明确排除若干 terminal cleanup／shutdown／browser 测试；这不是全 SDK、MCP、Ergora Job 取消通过。MCP fallback 使用 `os.getpgid/killpg` 的源码也不能直接搬成 Windows 保证。Linux 源码路径及任何 wheel 可安装性同样不是本机取消实测。[Windows CI 实际范围](https://github.com/OpenHands/software-agent-sdk/blob/504a88cab0fb48ee5226238ad7b8f1d865fa84a8/.github/workflows/tests.yml#L255)

## 4. DeepSeek 当前 headless／SDK 形态与 H1a 草图

### 只选 Python SDK＋sdk-minimal，不同时实现 headless

当前 headless 的真实命令是 `dsh --profile headless ...`，另有 `dsh headless` 别名。它继承较大的 base tree，`--json` 提供 session／status／text／thinking／tool_call／tool_result／final NDJSON，成功须同时检查退出零和 `final.reason.kind == completed`。final answer 无截断，但其他投影有限长；`--session-id` 是精确恢复，校验 cwd／session 归属。它没有任意 stage result schema 参数，JSON event envelope 不等于结构化任务答案。[官方完整 headless 用法](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/bundle/headless/README.md#L12) · [headless 输出与完成条件](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/bundle/headless/README.md#L120)

Python SDK 直接拥有 runtime subprocess，不必自己重写 JSON-RPC。`DeepSeekHarness` lazy start，单个实例跨 run 复用 runtime；`Session.run` 先订阅再提交，按其原生 inbox／idle 区间返回 `RunResult(session_id, final_response, finish_reason, events, notifications)`。notifications 可含后代活动，events 是根 session；不要让子 Agent 的文本替换根结果。`request_timeout_seconds` 限协议响应等待，**不限制后续完整运行时间**。[高层入口／结果语义](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/src/deepseek_harness/api.py#L102) · [结果与通知](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/README.md#L140)

以下是待 H1a 实例化的适配草图，**没有在本研究运行**。完整官方可运行基础示例是 [minimal.py](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/examples/minimal.py)，MCP 的完整公开配置示例在 [mcp-client README](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/mcp/mcp-client/README.md#L31)，自定义 provider 示例在 [pi-ai README](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/llm/llm-pi-ai/README.md#L37)。不能在未实例化路径／端口和核对发行闭包前复制成兼容配置。

```python
import json
from dataclasses import asdict
from deepseek_harness import DeepSeekHarness

# 路径、ID、prompt、schema 来自原 Invocation；密钥由外部环境提供。
def record(notification):
    native_events.write(json.dumps(asdict(notification), ensure_ascii=False) + "\n")
    native_events.flush()

with DeepSeekHarness(
    profile="sdk-minimal", dsh_home=str(native_home),
    cwd=str(request.cwd), runtime_cwd=str(request.cwd),
    patches=(str(frozen_patch),), provider="ergora-loopback", model="probe-model",
    initialize_timeout_seconds=15, request_timeout_seconds=15,
    shutdown_timeout_seconds=5,
) as harness:
    result = harness.run(request.prompt, session_id=native_id, on_notification=record)
    # 先保存原 RunResult、native_id 和原生回执，再作原合同验证。
    if result.finish_reason != "completed":
        raise ValueError("Harness input did not complete")
    stage_result = json.loads(result.final_response)
# 原 agents.invoke 的消费者继续 validate_result(stage_result, request.schema)。
```

空文本、plain malformed JSON、代码围栏、解释前缀、多个 JSON 对象、错误 schema 均应明确失败；不用 regex 修复，不把 `finish_reason=completed` 当可信评分。外层超时／未知回执仍由原 owner 处理。

H1a 的 patch 形状如下；真实文件必须由原 Invocation 的固定 Python、原 task MCP argv／cwd 和本地 loopback 端口生成，不能允许模型自由添加条目。`LINGZHI_API_KEY` 这里只是外部环境引用；loopback 使用其独立测试凭据，不发送真实凭据给实验服务。

```yaml
- id: persistent-bash
  disabled: true
- id: persistent-pwsh
  disabled: true
- id: tool-fs
  disabled: true
- id: tool-working-directory
  disabled: true
- id: mcp-resources
  disabled: true
- id: llm-deepseek
  disabled: true
- insert:
    - id: llm-ergora
      name: '@deepseek-ai/dsh-llm-pi-ai'
      config:
        providers:
          ergora-loopback:
            apiKeyEnv: LINGZHI_API_KEY
            api: openai-completions
            baseURL: 'http://127.0.0.1:<本次端口>/v1'
            models:
              - id: probe-model
                contextWindow: 65536
                maxTokens: 2048
            retryPolicy:
              mode: normal
              maxRetries: 0
    - id: mcp-ergora-task
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: ergora_task
        transport: stdio
        command: '<原 task MCP 的绝对 Python 路径>'
        args: ['<原 task MCP argv，按独立数组项生成>']
        cwd: '<原 task MCP cwd>'
        startupTimeoutMs: 15000
        toolCallTimeoutMs: 15000
        closeTimeoutMs: 5000
        failOnStartupError: true
        reconnect:
          enabled: false
```

这使用公开 profile patch，不改私有 SDK 字段、不改 HOME、不装第二套业务平台。最小树的 `tool-fs`、persistent shell、working-directory 是实际 model-facing 生产者；只把 sandbox mode 改成只读不等于移除它们。`mcp-resources` 必须显式关闭，避免自动加入另外三个共享资源工具。MCP client 的必要注入是 tools，资源服务 peer 为 optional；H1a 仍需确认打包 runtime 中这些插件可解析，缺失就明确不支持，不在启动时自动下载插件。[完整最小 profile](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/bundle/sdk-minimal/cordis.patch.yml) · [MCP schema／inject](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/mcp/mcp-client/src/index.ts#L43) · [optional peers](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/mcp/mcp-client/package.json#L81) · [共享资源工具](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/mcp/mcp-resources/README.md#L12)

MCP client 没有每 server 的工具 allowlist 配置；此方案只依赖原 server 本身精确暴露 `list/read`，模型看到 `mcp__ergora_task__list/read`，wire 仍发原工具名。不能插入任意 server 后靠“只提示用两个工具”限制。`failOnStartupError: true` 使该插件激活失败，但 app-boot 允许非 required 插件失败后继续，故这一个 flag 不保证 required task MCP 存在。接受结果前必须由原 task MCP 审计链证明完整资料读取，缺连接／缺读取明确拒绝；H1a 捕获模型实际请求中的工具 schema 并测断连反例。[MCP 选项与命名](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/mcp/mcp-client/README.md#L52) · [启动失败策略](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/boot/app-boot/README.md#L98)

`apiKeyEnv` 应始终显式设置；pi-ai 省略它会回退 provider-native ambient credential discovery。provider key 本身就是请求选择的路由名；不能把 `deepseek-official` 简单指向用户 ChatGPT 网关就宣称协议适配。源包支持手工声明 `openai-completions`／`openai-responses` 等路由，但实际网关、模型、推理参数和 usage 均待真实调用。[路由与 credential 规则](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/llm/llm-pi-ai/README.md#L29)

### home、原生会话、事件和生命周期

Python SDK 必须显式传 `dsh_home` 或 child env 中非空 `DSH_HOME`，不会自动发现 `~/.dsh`。profile／home／ordered patches 仍是受信任装配输入，须固定并保存其身份；独立 home 不是文件隔离。`sdk-minimal` 不装 workspace instructions、skills、managed credentials、telemetry 和 subagent 工具；内部仍有 session／jobs／subprocess 服务，不能把“无这些 model 工具”误说成没有运行期服务。[home／patch 合同](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/README.md#L29) · [最小树](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/bundle/sdk-minimal/cordis.patch.yml)

`resume_session(id)` 明确请求恢复，缺失／不可读／不兼容／占用的 session 会失败而非新建；`start_session(id)` 只是 lazy handle，不能冒充恢复。保持相同 home 和 workspace，原生持久化保存 JSONL 和 session-owned 资源；恢复会修复中断末轮，不恢复 shell／browser／其他外部进程。也不能由原生修复推导外部副作用从未发生。[原生恢复语义](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/README.md#L53) · [resume 实现](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/src/deepseek_harness/api.py#L174)

保存 native notification 的 method／payload、root events、session_id、finish_reason 和本次事件区间即可。usage 可来自 `assistant/message.data.usage` 或持久 assistant stream 中最后 usage sample；原生 token-meter 区分 provider usage 和四字符一 token 等启发式 context 估算。失败重试、compaction 等辅助调用须单独注明覆盖范围；没有 usage 不写零，不把 context occupancy 估计投成计费。[usage 的实际提取](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/llm/token-meter/src/usage-projection.ts#L81) · [usage／估算边界](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/llm/token-meter/README.md#L49)

取消必须区分三层：

1. SDK wire 没有每 prompt cancel／每 session close；`request_timeout_seconds` 超时不停止运行。一次正式 Invocation 必须独占一个 SDK 实例／runtime，不能让取消 A 同时停止 B。[wire 限制](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/sdk/server/README.md#L211)
2. `HarnessClient.close()` 先给 runtime `shutdown` 刷盘机会，再关闭 stdin、等待、terminate／kill **直接 runtime 进程**；它不自行保证宿主整个后代树。runtime shutdown 文档要求 dispose root、排空 owned Agents／persistence；强杀仍可能留下未刷盘终值。[Python close](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/src/deepseek_harness/client.py#L103) · [runtime shutdown](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/sdk/server/README.md#L87) · [checkpoint 限制](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/bundle/sdk-minimal/README.md#L39)
3. **外层原进程 owner 保持最终停止责任。** Python client `Popen` 没设 `start_new_session`／`creationflags`。DSH MCP transport 交由锁定的官方 `@modelcontextprotocol/client==2.2.0`，没有传 detached；本研究核该 npm 原包 `dist/stdio.mjs:74–87` 的 `spawn` 实际只有 env／stdio／shell:false／windowsHide／cwd，未设 detached，Node 默认继承组。该依赖 close 仅结束直接 MCP child；协议协商还会先启动临时 probe sibling，故一次 MCP 连接不一定只有一个启动 PID。以上为“单 runtime＋原 stdio server 继承原 group／Job”的静态依据，**不能代替实际停止探针**，更不能扩大到已禁用的 PTY 或任意新插件。[Python spawn](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/python/sdk/src/deepseek_harness/client.py#L75) · [DSH transport](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/mcp/mcp-client/src/transport.ts#L31) · [锁定依赖](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/mcp/mcp-client/package.json#L57) · [官方 MCP 2.2.0 原包](https://registry.npmjs.org/@modelcontextprotocol/client/-/client-2.2.0.tgz)

MCP generation 自身会区分 transport closeConfirmed 和 cleanupError，并给 pending work 等待预算；上层 deadline 超时不等于操作停止。外层必须保存真实进程退出／后代采样，不把关闭请求、socket 断开或模型最终文本称为停止确认。[MCP generation](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/mcp/mcp-client/src/generation.ts#L61)

## 5. 与 Ergora 原 owner 的最小映射

现有 [AgentBackend／Invocation](../../src/ergora/agent_backends.py)、[agents.invoke／结果校验](../../src/ergora/agents.py)、[processes.run](../../src/ergora/processes.py) 和 [mini 独立环境 driver](../../src/ergora/data/drivers/mini.py) 已提供扩展边界。H1a 先验证，不注册生产实现；通过后最小自研范围如下。

|已有 owner|必要局部映射；不转移的权威|
|---|---|
|组件描述／binding／局部 backend 映射|一个可选 Python driver 的精确版本、环境解释器、模型路由与环境引用字段；availability 分可执行文件、依赖版本、协议能力与真实模型可用性，doctor 不调用模型。能力模式按实开放。|
|`Invocation`|沿用 role／prompt／cwd／protocol／timeout／schema／mode／task_mcp；driver request 仅引用原 prompt/schema 和固定 patch，不接收任意 Cordis 树、任意插件安装或自由 argv。|
|`AgentBackend.command/read_result`|写一次 driver request，返回独立 Python＋driver argv；读取本次原生结果／严格 JSON，最终仍由 `agents.validate_result` 验原 schema。原始事件和 native session 描述只是该 invocation 的产物，不是第二账本。|
|`processes.run`／stage driver|继续持有 wall timeout、cancel、stdout/stderr、Linux supervised subreaper 或 Windows Job；SDK close 提供刷盘机会，原 owner 对停止与子孙残留作最终判断。可选 driver 不另设进程组或独立调度器。|
|正式 task MCP／资料消费者|继续由原 stdio server 暴露固定 `list/read`、固定资源和全文／分页审计；模型看到工具、发起读取、完整继承、未越权各须独立证据。无法满足则 `check_mode`／composition policy 明确拒绝。|
|原任务／候选／批准／恢复|native session_id 不替代 task/run/candidate ID；任何 finished／completed／自报 usage 不产生可信评分或批准。未知回执保持未知，先读回对账，不自动提交新 prompt。|

Windows 的原普通调用有 Job owner；参考正式 supervised 执行当前要求 Linux／WSL2。DSH 发布 win_amd64、选择 PowerShell 或存在 SDK API 都不能改变这项平台合同。Linux、Windows native、WSL2 是分别记录的范围，不能拿一个平台结果覆盖另一个。[原平台分支](../../src/ergora/processes.py) · [SDK 最小树平台选择](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/bundle/sdk-minimal/cordis.patch.yml#L87)

## 6. H1a 前置探针与后续验收出口

先在独立可选环境、本地项目和 loopback inference 服务完成以下有界验证。loopback 证明调用／工具／状态映射，不证明真实模型质量、网关兼容或正式模板通过。每份证据绑定 SDK／runtime／patch／解释器和当前 Ergora 候选身份。

1. **发行及公开接口。** 验精确版本、非 editable 文件身份、runtime 平台、完整 import；公开 `sdk-minimal`＋patch 能启动、pi-ai／MCP 插件确在发行闭包内，错误字段／缺失模块清楚失败。记录安装图，禁止自动安装外部插件或顺带下载 authoring runtime。
2. **实际工具集合和 ambient。** loopback 捕获真实模型请求，精确等于原 task `list/read`；shell、read_image、working_directory、共享资源工具均不出现也不可调用。放入只用于测试的 workspace ambient 标记，核完整 profile／home／patch 身份。广告列表之外，再请求未授权工具验证执行拒绝；不把空工具表单当权限证明。
3. **原资源链。** 让 loopback 真实发 MCP list/read，读完整祖先 Skill／context／分页内容，以原审计记录核查而非模型自报；未知资源、超限、server 启动失败、transport 断连均不得产出被接受的正式结果。MCP protocol probe／serving 两次启动及重连设置按实际记录。
4. **结果与失败。** 成功／provider 错误／`finish_reason` 非 completed／完整运行预算／malformed JSON／错误 schema／exit 0 无最终结果；只接受本次完整区间。缺失 usage 保持 unknown；保存有来源原样 usage、重试／辅助调用覆盖，不把估值作为账单。
5. **原 owner 停止。** 在初始化、慢 LLM、慢 MCP、MCP wrapper＋孙进程各窗口取消／超时；核 driver、runtime、probe sibling、server 和后代的退出及端口／管道释放。至少在 Linux 原 group 与正式 supervised subreaper 两条相关路径实测；针对脱离组孙进程核兜底。Windows 只有实际 Job 探针通过才记录该调用范围支持。正常 close、TERM、强杀、未知回执分别记账，不能只测正常退出。
6. **持久化读回。** 关闭后原 ID 读回，显式 resume、不发新输入即可验证原历史；缺 session／占用／workspace 或授权修订不匹配须拒绝或按原恢复流程处置。模拟接收 prompt 后断连，保持原 ID 与未知状态，不自动重跑。原生 session 能恢复不等于原 task／候选可以继续。

只有 H1a 证明所选公开配置可控，才进入一个最小产品 adapter。H2 仍需受影响 suite、基础 Python >=3.11／新非 editable 包与 283 冻结身份、实际有预算的模型调用、**同一模板只替换支持的叶后端**、完整资料及精确候选门禁；H3 才承接单一消费者的会话读回／续接和授权修订。OpenHands 本版的 ambient 缺口保持暂缓；DSH 任一模式／平台未过门槛就保留有证据的 unsupported，不为 all-in-one 放宽权限。

## 7. 获取、静态核对及未证明项

本研究只向官方 GitHub、PyPI／files.pythonhosted.org、npm registry 做了 **18 次 HTTP GET**，2026-11-12 05:13:51–05:23:29 UTC，17 次 200、DeepSeek `/releases/latest` 一次 404，未重试。内置 web_run 工具当时不可调用，改用标准库只读 HTTP；未使用二手文章。旧 [DeepSeek 调研](2026-11-02-deepseek-agents.md)只用于导航，当前接口结论均重新读上述固定源码。

原响应、原压缩包、SDK wheel、metadata 和提取副本保存在 `.ergora/checks/f8-harness-admission/research/`；`manifest.json` 每条含获取 UTC、URL、HTTP 状态／错误、字节数、SHA256，404 body 原样保留。`deepseek-sdk-source-comparison.json` 保存六 Python 文件的字节身份比较。缓存为私有验证材料，不纳入公开报告附件或包；没有使用临时目录。

|关键原件|字节数／SHA256|
|---|---|
|OpenHands 固定源码 archive|5,730,059 B；`1c91cd7f97074706d0bfb2fde0608c104b69de6bdbe58d44f6c7275d0b9ea1d7`|
|OpenHands wheel METADATA|1,351 B；`1f5ba86dff043f3ead223ec1305796d7e2ac9a4bc55e25eac067eb0b8e6e5265`，与 PyPI core-metadata hash 一致|
|DeepSeek 固定源码 archive|43,003,294 B；`96bbd0ac8201c9a74a1641efe53fcb20c69d11e9ef8525ef01e1fede662d0c20`|
|DeepSeek SDK wheel|24,513 B；`ad14f1b1fccb29f7d97e5a7e0ee9dbb96d8af11292308bba66bf19a623d31899`，与 PyPI hash 一致|
|官方 MCP Node client 2.2.0 原包|1,635,826 B；`0373c9045f222055e853451685a9ed1a1dacb36b9df84e4e67e5a93fed1b1448`，另核 npm 公布的 shasum 一致|

尚未证明：任何 SDK 在本研究环境的实际 import／启动、用户网关／模型调用、正式 task MCP 准入、取消及全部后代停止、Windows／WSL2 调用、强杀后最终事件持久性、跨版本迁移、runtime 二进制与源码完整重建身份，以及同模板正式六阶段／可信候选结果。以上均是后续原 owner 的验收工作；研究只给选择依据和反例，不给未运行兼容结论。
