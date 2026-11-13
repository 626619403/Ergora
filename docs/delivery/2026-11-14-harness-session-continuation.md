# F8-H3b 显式原生续接交付

日期：2026-11-14。按[本片计划](../plans/2026-11-14-harness-session-continuation.md)从 `fde425164e45a15e255eb62e0e6f6fd959e00f6c` 的产品继续；S1／W1 文档收尾不算本片产品。

## 当前事实

正在调查固定 SDK 和现有调用链，尚未实现续接或完成行为验收。现有 `run_input → _run_prepared → agents.invoke → AgentBackend.command → processes.run` 每次新建 cwd／home／session；`agent output --native-history` 仅观察原档。原 `agent_runs` document 可保存关联调用与意图，原 `file_lock` 可持有整个操作，`task_mcp.freeze` 可为同一冻结资料创建新 run scope，无需新增第二数据库或调度器。

固定 SDK 的 `DeepSeekHarness.run(session_id=...)` 不等于显式恢复；续接要 `resume_session` 后对 Session 发送新输入。原 SDK 不能以客户端幂等键保证 prompt 至多一次，因此 intent 必须由应用在发送前保存。原生回执／通知不等于持久 JSONL 已刷盘，丢回执也不能判定未发送。

实际调用者核对发现正式只读 `stage_driver` 也走 `run_input`，其文档的 `formal_execution_authorized=False` 不足以批准 standalone 续接；新源须显式 opt-in，默认关闭，supervised 不接受该选项。完整 prepared prompt 在任务前带原资源或 `Operator supplied task` 前缀，不把用户 task 的 slash 文本直接路由成原生命令。原 output 固定当前 run 的 protocol／cwd，后续需要由 `agent_runs` 解析核准的 source lineage，不能放宽后端任意 home 路径。

实际自身审查、新 fresh-context 实现评审、测试包、模型调用、发布和自己的 CI 均未执行，不以设计或 H3a 的成功关闭。本片优先核 task-MCP 的新审计和继承资源，完整候选采用／正式 task 恢复／GPU 仍归原 owner。

## 设计选择

[两种 Interface 调查](../architecture/2026-11-14-harness-continuation-options.md)已完成，文档 SHA `3c355f7ad98c07299cce098463d84c0c5068917ef183edb4413b1ce250daf1fb`。采用原 Invocation 的可选已准入来源，保持原 command／read_result／processes 消费，不新增 session manager。选择 task-MCP 的新源＋一次续接，实际检查完整继承资料和新 scope；完整新 prepared task 允许改变 input／prompt digest，结构与材料保持。

设计调查仅静态读取，九份产品匹配精确 HEAD、固定 SDK 六源码匹配留存 wheel、十二本地链接有效；没有 import SDK／启动 runtime。下一步新增一个本地合成 HTTP 的两调用机制探针：全新私有源、原 home／ID／cwd 续接、MCP scope 变更、上下文和刷盘边界；不使用真实凭据或业务资源。原始成功／失败、进程身份与观察限度单独保存，不能替代后续产品／真实模型验收。
