# 固定 SDK 的同会话续接机制探针

日期：2026-11-14。产品基线 `fde425164e45a15e255eb62e0e6f6fd959e00f6c`；承接 [H3b 计划](../plans/2026-11-14-harness-session-continuation.md)。**DeepSeek SDK／runtime `0.2.2rc2` 在同一新建私有 home／session ID／cwd 下，替换本次 task-MCP scope 后，成功执行一次 `resume_session → Session.run`。** 这是两调用成功路径的本地合成机制证据；Ergora 续接产品、真实模型、故障恢复和正式六阶段尚未由本探针验收。

准备阶段使用 S1 原 noneditable 安装包，561 产品文件与原 wheel 逐字一致，wheel SHA256 为 `7cbf6594483b7197640b0be74a869ac05c811e014623cd7e5cb968dba9f6d8ab`，没有安装或修改产品。纯合成父 workflow 提供 Skill 和 95,066B 跨页附件，叶继承全部资料；两个 prepared input 的 composition／grant／资源相同，仅 task 与派生输入摘要改变。各自 scope 绑定独立新 run ID，四个文件共 95,485B；新旧 scope 的文件内容／来源完全一致。新 patch 仅改变 MCP scope 路径、scope SHA 和 audit 路径。

固定 `sdk-minimal` patch 禁用原生 shell、文件、目录修改、共享资源及默认模型路由，仅注入 task-MCP 的 `list/read` 和 `127.0.0.1` 合成推理路由。沿 H1 已成功的 completions SSE 响应格式，由夹具按固定计划触发工具并返回 JSON。两个 SDK 进程均由 S1 安装版原 `processes.run` 限 90 秒，没有重试或夹具失败。

|调用|原 owner 实测耗时|本地 HTTP|实际工具动作|原生结果／通知|
|---|---:|---:|---|---|
|初次调用|23.267 秒|8|分页 list 两次、read 五次|48 个 root event／50 条通知，completed|
|同 ID 续接|7.742 秒|8|新 scope 下分页 list 两次、read 五次|本轮 44 个 root event／46 条通知，completed|

两轮全部 HTTP 的工具 schema 只有 `mcp__ergora_task__list/read`；各自新 native audit 通过 `verify_native`、`verify_reads` 和四文件完整连续范围审计。祖先附件的来源确为父 workflow，95,066B 均在各自调用中读完。续接首条原 HTTP 实际包含完整前轮 user prompt、前轮 assistant 最终 JSON 和本次新 prompt；前轮两个记忆标记没有被复制进本次 prompt。合成响应证明传输与消费链，不能证明真实模型理解或自主选择工具。

两次 receipt 消息 ID 不同，seq 分别为 0／49，`agent/inbox/spliced` 的完整 inserted content 等于各自实际 native prompt；后续 `user/message` 保持同 ID／正文。两次均观察到同 root 的 `session.status=idle` 通知及 `turn/end.reason.kind=completed`，没有从旧末轮答案提取新结果。

|原日志观察点|字节／事件数|完整 SHA256|
|---|---|---|
|初次调用正常 close 后 B0|133,924B／48|`c42737c88fb2cb0832ea3232160c0ad39c1600782e31920ffc47fa7bbc9fb778`|
|resume 返回、持原 lease 的 B1|133,992B／49|`b12821195ce485103fa8ed1dbb384842f997fc3c74d985df84ae1cabe7dca90f`|
|续接正常 close 后 B2|266,902B／93|`f0baaaea60260a04836751e12d6976b79a488aa3a28d43fa72763fb7c1362afe`|

B0 是 B1／B2 的完整原字节前缀，B1 是 B2 的完整前缀；header 的原 ID／cwd 保持，只有一个 canonical v4 session 文件，没有复制 home。B1 即时观察已包含新增 68B、seq 48 的 `session/end-seed`，约 0.26 秒有界稳定观察没有再变；非阻塞 flock 实测原 runtime 仍持有 writer lease。没有调用内部 flush 或重试恢复。

**SDK idle／RunResult 不是最终归档刷盘屏障。** 初次调用在 `Session.run` 已完成、idle 已通知时，文件仍以 `step/start` 结束；正常 close 后才多落盘 1,933B。续接同样在 close 后多落盘 2,026B。两次末三条均为已经出现在本轮 SDK events 中的 `assistant/message`、`step/end`、`turn/end`。本片因此在 close 后取 B0／B2；不能在 `Session.run` 返回时就声明末轮完整归档已经持久化。

原 owner 的十个采样 PID／starttime 身份终态无存活，两个 owner 均退出 0，loopback 已关闭且端口拒绝连接。只证明这些受控身份的收尾，不扩大为全宿主隔离。全部十六份原 HTTP request body／SSE response、两份 input／scope／patch／audit、通知／JSONL 与各 byte cut 私有保留；138 份原件清单 SHA256 为 `3affc94434f9adab403c75eb5df6a4816ce604b8b1a8f668c3dcee45c432282c`，离线审计 SHA256 为 `817fa957a48a31a7876e077ce6b75feae91fee3e0200b5af8b681a36af2d53ff`。

本探针使用假凭据、纯合成资料和本地响应，没有真实模型、业务／资产或外部网络调用。已完成的 architecture 保持原 SHA；产品实现、intent 去重、并发、发送后断连、unknown／预算／取消、真实模型和独立实现评审继续按 H3b 原 owner 推进。
