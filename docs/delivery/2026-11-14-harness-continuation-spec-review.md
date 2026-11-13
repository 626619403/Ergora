# F8-H3b 独立需求与行为审查

日期：2026-11-14。审查者 `/root/h3b_spec_review`，新独立上下文；先读原[需求](../plans/2026-11-14-harness-session-continuation.md)与[方案](../architecture/2026-11-14-harness-continuation-options.md)，再读实际产品及调用者，随后核作者记录。固定基线 `67966095814eec01f2e1e5d65d87e289320ad79f`；初始工作树 diff SHA256 `3be4c27f8ac83d65e0315ca8feeee40a4bdca3b9085885f92264bf6d67dd5edd`，私有原件 `review-r1.diff`。

范围：五个产品文件 `agent_backends.py`、`agent_runs.py`、`agents.py`、`cli.py`、`data/drivers/deepseek.py`，`test_deepseek_backend.py`；相邻 `processes`、`state`、`task_mcp`、prepared-input 编译／校验及 `stage_driver`。核所有 tracked／untracked，读 README、后端手册、当前架构、本片计划／交付／未跟踪机制探针。W1 附录限已发布片状态记账。

**需求与行为判词：所审源代码范围通过，两个 P2 已修复并独立复核，开放发现 0；最终交付验收仍待补证据。** 默认关闭、standalone 限定、完整 prepared 结构与祖先资源、权限上限、独立 scope／结果、intent 占用与 unknown 不重发均有实际消费者；沿原 Invocation／进程 owner，未发现第二调度器或正式恢复接管。维护性由另一独立方向评价，本报告不替代其判词。

1. **P2，同路径副本可在 SDK 启动窗口接管输入，已关闭。** 初始 `deepseek.py:303`／`agent_backends.py:425` 只冻结／核 cwd，没有 home 的物理身份；rename 原 home 后同路径 copytree，新 prompt 成功落到副本，原档未增长，违背方案“原 home … 普通目录物理身份”“不让副本成为权威”。首修补 `home_identity` 后，调用前替换已拒绝；但 SDK `__enter__` 时替换仍先发送、退出才失败。最终修复在 `deepseek.py:360` 的 send-intent／`session.run` 前即时复核原目录，并保持整个操作的目录检查。原窗口独立复测仅有 source 一次输入，child failed／unknown；副本只增加恢复种子，未收到新 prompt，换权显式保留 observation_error。

2. **P2，失败调用没有持久保存实际恢复／收尾区间，已关闭。** 初始 `deepseek.py:336` 的 resume 已写入后，cwd RPC／恢复校验失败可先于 `native-restore`；最终 B2 又只在正常 completed 后生成，上层 `agent_runs.py:317` 仅成功时消费。注入“resume 追加 end-seed 后 cwd RPC 断连”，原档新增 40B，但 child 无 restore／最终 interval；发送断连也无关闭后 B2。违背方案“保存 restore interval”“恢复／shutdown 新增字节分别记账”。最终 `deepseek.py:353` 先保存 B1，`agent_runs.py:330` 在原 owner 收尾后统一消费 Adapter 的物理观察。两种原故障独立复测均持久保存 B1／B2、原前缀、restore／activity SHA；native.completed 为 false，child 保持 unknown，同 intent 不重发。

私有初次复现位于 `.ergora/checks/harness-session-continuation/spec-review-r1/`：`reproduction.json`、`home-fix-recheck.json`、`home-race-recheck.json`、`failure-reproduction.json`。最终 `recheck-current.py` exit 0；`home-race-recheck2.json`／`failure-recheck2.json` 保留修复复核。另验 resume 写入后回执丢失，B1 保持 null，B2／post-source SHA 仍持久保存且无新 prompt。六文件复核 diff SHA256 `90c14415978fafe742cf4f42e94655683137f19d267babe1dd1cf49314134b7e`，逐文件身份见私有 `source-recheck2-identity.json`。复用既有 SDK double，MCP preflight 用本地替身；未安装、未启动 SDK／模型或网络，重复 intent 仍不重发。固定 SDK 的公开 resume／cwd RPC／receipt 消费源码另经只读核对。

已读 r1 安装原输出：130 passed／12 skipped、118.37 秒；实际 SDK 合成成功记录为 12 HTTP、新 scope、两轮完整附件读取及原前缀／结果保持。561／两 RECORD／283 是作者提供的 r1 包记录；这些旧候选证据不覆盖审查后的产品修改。剩余：最终候选包／相关回归、真实 SDK 故障与停止、真实模型、Ergora 自身模板及精确发布／CI；未完成项不判通过。

## r3 最终本地证据补核

本附录更新上述阶段性判词：**r3 的需求与行为本地出口通过；两个 P2 均已关闭，开放 finding 为 0。** 五产品＋测试仍为复核过的 diff SHA256 `90c14415978fafe742cf4f42e94655683137f19d267babe1dd1cf49314134b7e`，无新代码。维护性仍归另一独立方向；普通发布、精确远端及本候选自己的 CI 未取得证据，不提前判通过。

本轮独立编写只读审计，从 r3 noneditable 安装环境读取原件，没有再安装、运行 suite、启动 SDK／模型或网络调用。私有 `final-r3-artifact-audit.json` SHA256 `f25143396435bf0c335246eee40fb5ffadba3e20fa953a10280576c9172373a5` 保存逐项结果：

- r3 wheel SHA256 `587c345fae69a70fdf0d436433bebe7a3df81ce801eca6003c2909c2a5c392a4` 重算一致；561 产品在当前源码、构建快照、wheel、安装逐字相同。wheel／安装 RECORD 分别核 568／573 个有摘要项，283 参考文件既匹配 manifest，也逐字匹配固定基线。七 suite 原 stdout 为 **133 passed／12 skipped，125.12 秒**，原进程 exit 0／127.014 秒，跳过不算执行。
- 四份实际固定 SDK 原件 `loopback-{success,disconnect,timeout,cancel}-r4`：成功为 succeeded／completed、12 HTTP；其余各 7 HTTP，分别 failed／timed_out／cancelled 且 unknown，无成功结果。独立核原 home／cwd 物理身份、同一 header／session、唯一新 prompt、源完整字节前缀及 B0／B1／B2 的真实区间 SHA；失败 `native.completed:false`。逐调用 prepared prompt、全部祖先 inline、schema／binding、scope／audit／附件读取与 DB 两条原记录一致，源结果不变；原重放断言及原档没有第二次新输入。timeout 新授权确为 12 秒，34.863 秒是含 source 的夹具总时间。四例各 11 个采样 PID／starttime 当前均无活动；监听关闭限原夹具终态证据。
- 真实模型 `real-model-r1` 沿原 `refactoring-quality` 的结构审查叶，显式 Responses 绑定；source／child 为 63.193／36.864 秒，独立结果与新 scope 保持。三份父 Skill 附件共 4,084B 两轮各完整读取；两个随机前轮标记均不在新 native prompt、均出现在真实 child 回复。原前缀、旧结果、DB lineage 与唯一新输入保持；10 个采样进程当前无活动。这不证明提供方 HTTP 次数、账单、模型错误独立性或正式候选批准。
- 自身原 `ergora-structure-review/root/review` 的 Codex 回退为实际成功、73.433 秒、approve。九文件 220,205B 按原索引从实际 task 逐项重取核 SHA／长度，实际 prompt＝stdin，三项祖先 inline 均存在；六份产品／测试与最终候选逐字相同，三份文档是当时快照，随后状态补记另行核对。原 result SHA256 `acdb060f5c6570769fcff414e06f7a5115380373c145d4a60618dcfccdcdc9fb` 重算一致，不把模板回复替代独立行为验收。

重新核全部 tracked／untracked 范围：十份 Markdown 与新增[公开摘要](evidence/2026-11-14-harness-session-continuation.json)均在本片范围内，W1 附录仍仅发布记账。README、手册、当前架构、总／片计划、交付和两审查报告的当前状态与证据一致；新增失败 B2／`restored_bytes:null`／`observation_error` 说明符合实现。公开摘要五案例及自身模板字段匹配原件，SHA256 `845e36e0835d9e10d40b1e53729d56145294ba2d37f7d01738b4b3120a8d001f`；未包含机器绝对路径、服务地址或凭据。私有 `final-self-docs-audit.json` 保留 packet、原 DB／回复、当前文件及本地链接检查，`git diff --check` 通过。正式恢复、workspace、任意多轮、跨版本／后端迁移、累计费用和 GPU 仍未由本片承诺；本地方向无发布前阻断项。

## 原片发布身份补核（CI 待终核）

已独立补核原片提交 `47443840b68693f63ee011dc6fbe29421a42223f`，父提交为固定基线 `67966095814eec01f2e1e5d65d87e289320ad79f`。**原片普通发布与精确远端身份通过；本地需求与行为判词仍通过、开放发现 0；本候选自己的 CI 待终核。** 本轮为离线原件与 Git 对象核验，没有安装、重跑 suite、启动 SDK／模型或网络调用。

逐项读取 `static-r5.json`、`commit-r1.json`、`push-r1.json`、`ref-r1.json`、`ci-discovery-r1.json`，独立重取原片 Git blobs：固定基线至该提交恰为 17 文件，其字节数及 SHA 均匹配静态清单与 ready／Git 记录。五产品＋测试保持已审六文件 SHA，原片产品 diff 重算仍为 `90c14415978fafe742cf4f42e94655683137f19d267babe1dd1cf49314134b7e`；原片 `git diff --check` 通过。发布版公开摘要 SHA256 为 `3d4a4b92200d7459d28d6be5c15f73c2161d2f37879d93eb18bb5fa158395a5c`，状态准确保留本地出口通过及发布／CI 待验；static-r4 至 r5 仅交付文档末段静态检查记账变化。

推送原件 exit 0，目标为 `HEAD:refs/heads/refactor/architecture-foundations`，采用普通推送；随后的 `ls-remote` 原 stdout 完整返回同一候选 SHA 与该分支。Actions 官方列表原页的 HTTP 200、长度及 SHA 重算通过，唯一完整提交链接关联运行 `43495562208`；原运行页同样绑定该完整提交，记录状态为 `In progress`。两页 SHA256 分别为 `8510a44e43596d23840f27f6150bc15c8f6ee8639a98fd816ea43c861be2b19e`、`a654fa8abdbfd4cf4eb3486369eb21b6099490d895e693c68f4f250bebcc27ad`。终态及必要 job／步骤尚待后续原件，本附录不作 CI 成功判词。

私有 `spec-review-r1/publication-r1-audit.json` SHA256 `c257f48faae471f3ea2107335765f5b33d6a452b0d85086c3986b6d311199c22` 保存逐文件及原件摘要。审查对象是上述已发布原片；本附录、后续状态记账及下一片工作树文档属于发布后的记录。

## 本候选 CI 与精确终验

**需求与行为方向的 H3b 原片精确交付终验通过，开放发现 0。** 原片仍为 `47443840b68693f63ee011dc6fbe29421a42223f`；r3 本地出口、普通推送／精确远端及[自己的 CI `43495562208`](https://github.com/626619403/Ergora/actions/runs/43495562208)现均已取得并独立核验原件。维护性判词仍由另一独立方向给出，下一片 F9a 工作树不在本次终验范围内。

独立离线解析原页面与 JSON，重算 24 份原 HTTP 200 响应的长度及 SHA：列表 1、运行页 5、job 原 UI JSON 1、job 页面 17。第五运行页 `ci-run-html-r5` 完整提交链接绑定本候选，状态为 `Success`，原页 SHA256 `c66cf585f6dbb87e193bb3b9699c5e793e019b2d3d9fe0059465533ac56100c2`。原 UI JSON 恰为 8 job、`hasMore:false`，逐项 ID／名称／当前 run 链接匹配 metadata；早期 JSON 的运行中状态仅用于身份映射，终态取各 job 的最新原页。

按该提交冻结的 workflow 与六个 Linux 分组核期望集合：plan 1、Linux 6、Windows 1，无漏 job。plan／Linux 最新 r2，Windows `132127694689` 最新 r3。30 个必要步骤包括分组规划 1、七 native job 各四项包构建安装／参考身份／应用回归／观察上传共 28，以及 Windows PowerShell 5.1 安装升级 1；每项均为 `success`，有 `started_at`／`completed_at` 与 `job_completed`，日志路径逐字包含本候选完整 SHA、对应 check ID 及步骤号。最新页面全部 82 个 check-step 均终态；Linux 上六个 Windows 专属条件步骤按原 workflow 跳过，未计入必要成功数。

独立投影与 `ci-parsed-r3.json` 逐字段一致，私有 `spec-review-r1/ci-final-r1-audit.json` SHA256 `5eb16f7526b40b173916461c7c2ccb773ff510b392470f20a10ffd686eaca304` 保存逐响应、job 和步骤证据。运行页 r1–r4 的 `In progress`、Windows r1／r2 未终态及前两次解析未通过的原记录保持；本附录以新增终态证据更新先前待验结论。此次仅核已有原件与冻结 Git 对象，没有新请求、安装、测试或模型／SDK 调用，也未下载日志正文或 artifact。
