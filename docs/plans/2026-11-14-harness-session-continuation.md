# F8-H3b：显式续接原生只读会话

日期：2026-11-14。承接已精确交付的 [H3a](2026-11-14-harness-session-readback.md)和[原接缝调查](../architecture/2026-11-14-harness-session-seam.md)。基线产品 `fde425164e45a15e255eb62e0e6f6fd959e00f6c`；S1 自己的 CI 与 W1 试用另片收口。下面是本片验收合同；实际状态见末节与所属交付。

## 首片范围

选择一个已有带祖先 Skill 的 standalone 只读 task-MCP 叶，先运行新的、具备续接冻结信息且显式 opt-in 的 source，再显式追加一次新任务。新源入口拟为原 `composition run-input --allow-one-continuation`，默认为 false；`stage_driver` 的正式只读调用也使用 `run_input`，不能以 `formal_execution_authorized=False` 判定 standalone。supervised 调用不接受该 opt-in，正式阶段维持原默认。

新的 prepared input 必须复用原 composition／root／leaf／grant／全部资源；任务正文与 prompt 必然改变，不能误要求新旧完整 input digest 相等。新入口消费完整 prepared input，复用原 inspect／材料预算，不能直接把 raw slash 命令交给原生路由。

保留原 native home／cwd／session，仅新增关联 source run 的调用、输入、结果与审计；不复制 home 分叉、不覆盖源回执，不在新输入中采用活动记忆或 Skill。旧 H2 源缺失调用时冻结资料的字段，不能回填后宣称原已保存。正式 workspace／task 恢复、任意多轮交互、迁移／fork、跨版本 SDK 与累计 usage 成本不在首片范围。

## 可验收节点

1. **设计与原生事实**：核固定 `0.2.2rc2` 的显式 `resume_session → Session.run`、prompt receipt、原生命令路由、结果／增量事件、MCP 和 lease。比较继续传完整 prepared input 与仅传原 run／新 task 两种 Interface，选择复用现有 inspect／freeze／进程 owner 的较小合同；不新建 session registry 或预算表。
2. **调用时冻结与准入**：新 source 保存真实 schema／原调用额度、项目修订与 repo／cwd 身份、后端绑定／policy、精确输入、SDK/profile/patch 及原生身份；续接核相同原结构及原资源。当前项目或资料／权限／绑定已变时拒绝续接，仍允许原档只读查看。不支持的源、模式、后端、旧格式和缺原件明确失败。
3. **唯一输入意图**：原 `agent_runs` 在 SDK 输入前保存 source、intent、新输入 digest／timeout 与占用。原 `file_lock` 持有整个会话操作；首片一个 source 只允许一次新 prompt，同 intent 重复只读返回原记录，冲突 intent 拒绝，子续接不能再当 source。进程中断、回执丢失或 unknown 不释放占用、不自动重发；SDK 原生 lease 不是应用幂等保障。
4. **同一调用链与证据**：沿 `agents.invoke → AgentBackend.command → processes.run`，由具体 Adapter 处理原生协议，上层不判断后端名字。复用新的 task-MCP freeze／probe／verify_native，把新 scope 和 audit 绑定新 run；明确旧上下文仍含源资料。原档完整前缀、恢复写入区间、本 prompt receipt 到 idle 的增量及新结果分别记录，不能取旧末轮文本当新结果。
5. **有界授权与收尾**：续接为新显式 wall budget，源已花成本保持；调用 owner 先扣准备／preflight 实际耗时，余量交原进程 owner，清理尾部单列。一次 Ergora 调用／新 prompt 可有多次模型 HTTP 和工具循环，不能写成一次推理请求或完整累计计费。验证取消／超时／接收后断连及原 owner 身份清理；缺终态保持 unknown。
6. **行为验收**：复用原 suite 的真实风险用例：结构／资源／schema 漂移、项目／cwd／原档身份、双调用竞争、重复／冲突 intent、断连窗口、原结果保持、新 MCP 归属及预算。固定 loopback 故障夹具与新的真实 source／续接分别记录；实际继承资源完整读取并能在续接回答原会话内容，不把成功文本当 GPU 或候选采用。
7. **交付出口**：noneditable 包／两 RECORD／283、必要受影响检查；更新原 CLI／手册入口和本片交付。实际 Ergora 自身审查模板加新的 fresh-context 两轴，修实证 finding 后复核；普通发布当前分支、精确远端及自己的 CI。不合入 main。

## 当前状态

节点 1 的[两种 Interface 调查](../architecture/2026-11-14-harness-continuation-options.md)和[两调用机制探针](../delivery/2026-11-14-harness-continuation-probe.md)已完成，选择方案 A：原 Invocation 携带已准入的来源描述，原 command／结果／进程消费保持。全新私有 home 的本地 loopback 已核新 MCP scope、原上下文带回和实际 B0／B1／B2 刷盘；SDK idle 不是持久化屏障，正常 close 后才读取最终归档。

节点 2–7 已完成，产品 `47443840b68693f63ee011dc6fbe29421a42223f` 已普通推送并核完整远端Ref；自己的 CI `43495562208` 为 Success，8 job／30 必要步骤由原独立两轴终核。r1安装回归130通过／12跳过及实际SDK成功保留为原候选证据；新的独立评审复现home副本／时窗与失败增量两P2，r3已修并按原场景复核，开放0。r3包561／两RECORD／283、源35项和安装133项通过／12跳过；实际SDK四场景与真实模型两调用均通过，自身原结构模板73.433秒approve。最终新独立两轴补核通过、本地出口开放0／0；精确发布与自己的CI已收口，开放0／0。原迁移失败和夹具失败详见交付，不能替代最终候选的实际验收。

预期复用／修改范围为原 `agent_runs`、`Invocation`／`agents.invoke`、DeepSeek Adapter 与独立 driver、原 CLI／output consumer、既有 composition／DeepSeek 测试及手册。若新调用从原 home 续接，output 必须按 DB 中核准的同项目 source lineage 读取原 root protocol／cwd，同时仍返回本调用 stdout／结果及本次 interval；不能让 backend 信任任意 `identity.home` 或用 symlink 迁就原 reader。
