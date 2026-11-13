# F8-H3b 独立结构与规范审查

日期：2026-11-14。审查者：fresh-context agent `/root/h3b_structure_review`；未参与实现。按项目 `AGENTS.md`、AIHERO、codebase-design、maintainable-project-delivery／independent-review 与 code-review 的 Standards 方向审查。原要求为 [H3b 计划](../plans/2026-11-14-harness-session-continuation.md)及[两种 Interface 设计](../architecture/2026-11-14-harness-continuation-options.md)。

## 范围与判词

固定基线 `67966095814eec01f2e1e5d65d87e289320ad79f`；其 `src/tests` 与产品基线 `fde425164e45a15e255eb62e0e6f6fd959e00f6c` 无差异。已检查 `git status`、全部 tracked diff 与新机制探针文档，包括 README、后端手册、当前架构、总／片计划、片交付和 W1 发布记账。产品为 `agent_backends.py`、`agent_runs.py`、`agents.py`、`cli.py`、`data/drivers/deepseek.py`，测试追加于既有 `test_deepseek_backend.py`。

初查 r1，随后复查发送前封存 home 身份的三文件改动。此时五产品＋测试的基线 diff SHA256 为 `f6b1869ac54f2f545ac3daa5be75c455ae7ec1a49f1314dc0642248d823d882d`。这是未提交候选，r1 安装包的历史成绩不自动继承后改源码。

- **维护性：产品职责与依赖方向通过本轮静态检查，无产品结构 finding；恢复入口有一项 P3 待同步。** `agent_runs` 仍拥有准入、唯一 intent、DB 和 lineage；Adapter／driver 拥有原生合同；`processes.run`、原文件锁和 task-MCP owner 被复用。未发现新调度、账本或单次使用的公共框架。
- **需求符合性：待 P2 修复及最终候选验收。** 本方向发现一个最终归档采集时的物理身份窗口；不以结构合理代替行为通过。

## 实证 finding

1. **P2，待修：正常 close 后的 home 替换仍被当作原会话成功。** `src/ergora/data/drivers/deepseek.py:369` 的 B2 采集，以及 `src/ergora/agent_backends.py:473` 的结果复核只核字节／区间，没有将最终 home／cwd 对回发送前的目录身份。用既有 SDK double，仅在 child 第三次 `_history`（正常 close 后、B2 前）将原 home rename 留存并 copytree 回同路径：新 inode 的副本仍得到 `status=succeeded`、`continuation.state=completed`。这会将副本归档接受为原 home 的完成证据，违反本片保持原物理 home 的合同。最小修改：在现有 driver／collector 中复用 `call_directory`，使 B1／B2 和最终采集的 cwd／home 对应已冻结 dev/inode；异常保留 unknown，不重发。私有实证：`.ergora/checks/harness-session-continuation/structure-review-r1/home-after-close-reproduction.json`，2 次 SDK-double 调用、0 网络调用。
2. **P3，待同步：恢复入口指向已完成的迁移修复。** `docs/PLAN.md:21` 仍写 76 通过／2 失败且 codec 注入迁移“待修”，而片计划／交付已记录迁移修复、首次 89 通过及后补预算检查。恢复者会重复诊断已解决问题。最小修改：保留历史结果于交付，将总计划的下一步更新为当前候选、实际证据和剩余验收。已通知实现者。

## 结构检查与限度

已沿 CLI → `continue_input` → `_run_prepared` → `agents.invoke` → Adapter command → 原 process owner 检查真实调用者；`stage_driver` 保持默认关闭。三个新后端方法承担能力拒绝、源采集和本次结果采集的不同职责。`call_directory`／`call_files`／`native_history_page` 在 Adapter 与隔离 driver 两个生产位置复用，仅模块级标准库 import。重复读取保护准入、复制和发送之间的资料／磁盘漂移，不因代码形状相似建议删除。私有 inbox／patch／history 算法有本片实际消费者，未扩成通用事件恢复器。

Fowler smell baseline、必要分支和测试逐项按可达场景检查：未发现需抽象类型的字符串分派、配置默认值硬锁、额外 CI 框架或只证明普通可见异常的新增测试。现有测试追加保护意图重放、并发、资料／身份漂移、旧结果误取与预算重置等静默风险。

独立读取 r1 包身份、七 suite 原输出（130 passed／12 skipped，pytest 118.37 秒）、实际 SDK loopback-success-r2 原 summary 和夹具（source＋resume 成功、12 HTTP、85,042B 父附件、新 scope、旧记录／结果及原前缀保持）。另以只读脚本核 561 当前产品：后续 home 修复使两产品区别于 r1，其余相同；未把 r1 成绩记作后改候选验收。

本轮未安装、执行真实 SDK／模型、完整回归、提交或推送；未改产品／计划。新增比例小复现只使用既有 SDK double。实际故障／取消／owner 清理、真实模型、自身模板、新包、最终文档与远端 CI 仍需实现者提供最终候选证据后复核。

## 同片修复复核一

本附录更新当前结论：**上述 P2 已关闭；产品结构／必要控制流无新增 finding。P3 恢复入口仍待实现者同步，最终候选验收待补。** 复核的五产品＋测试基线 diff SHA256 为 `90c14415978fafe742cf4f42e94655683137f19d267babe1dd1cf49314134b7e`。

`native_directories` 在原独立 driver 内持有 cwd／home 整条目录链，Adapter 和 driver 是两个真实生产消费者；新增 expected 身份参数直接服务源 seal、发送前和终态观察，没有扩大为公共 session 管理。发送前即时重核与跨 close／B2 的守卫分别覆盖不同漂移窗口，保留有理由。原 `agent_runs` 仍在原 process owner 收尾后使用同一 `continuation_result`，失败时仅记录 bounded observation／observation_error；`completed:false` 和 unknown 不因观察到归档增量提升为成功，也不释放名额。

独立、无网络复跑原 close→B2 替换：结果已为 `failed/unknown`，保存目录身份错误；相同 intent 返回同记录，SDK-double 调用总数保持 2。私有原件为 `structure-review-r1/home-after-close-rereview.json`。另核两个小场景，原件为同目录的 `restore-and-presend-rereview.json`：

- resume 后 cwd RPC 断连：保存 B0=9,349B、B1=B2=9,389B，原前缀保持、`completed:false`，本次新 prompt 未发送（只有源的 1 次 SDK-double run）；重读无重发。
- cwd RPC 返回前替换 home：发送前守卫拒绝，保留 `failed/unknown` 和 observation_error，SDK-double run 总数仍为 1；重读无重发。

这些复核只关闭已演示的身份与失败观察窗口，未运行实际 SDK／模型或安装新包；r1／r2 历史成绩仍限各自候选。等待最终 r3 包、相关 suite、实际 SDK 故障／停止、真实模型、自身模板及更新后的文档证据。

## r3 实际证据补核

当前五产品＋测试 diff 仍为 `90c14415978fafe742cf4f42e94655683137f19d267babe1dd1cf49314134b7e`，无新增代码。**本方向 P2、P3 均已关闭；维护性与已检查产品行为通过，开放 finding 为 0。** `docs/PLAN.md` 恢复入口已指向 r3 当前证据及剩余工作，历史迁移失败留在交付中。README、后端手册、当前架构和交付对一次续接、unknown、原 owner、失败观察与未支持范围的说明与实现相符；片计划的阶段状态仍需随最终收口同步。

只读补核以下原件，没有再次安装、运行 suite、SDK 或模型：

- r3 noneditable wheel SHA256 `587c345fae69a70fdf0d436433bebe7a3df81ce801eca6003c2909c2a5c392a4`。重算 wheel／安装 RECORD 的 568／573 个有摘要项、283 参考文件；561 当前产品文件、wheel 和安装逐字相同。七 suite 原 stdout 为 **133 passed／12 skipped，125.12 秒**；原进程记录为 127.014 秒、exit 0，跳过不算执行。
- 读取 `audit-r3.py` 并在内存移除唯一写文件语句后执行其只读主体；所得五场景记录与原 `audit-r3.json` 逐字一致，SHA256 `a3c75f0d4770f7cfd8c3d5c9330edd3ce7689aa57ecd067e9edaef21210f3b54`。核完整 prepared prompt／祖先 inline、两轮独立 scope／读取审计、结果摘要、DB 原记录、同 home／ID／cwd 及 B0/B1/B2 全字节摘要；未改该审计脚本或原记录。
- 固定 SDK 四场景原件 `loopback-{success,disconnect,timeout,cancel}-r4`：成功 12 HTTP、28.841 秒；其余各 7 HTTP，分别 failed／timed_out／cancelled 且 unknown。原前缀和已知 B1/B2 保留；失败观察 `completed:false`，原记录／结果保持，重复无新请求。timeout 的 34.863 秒是含 source 的夹具总时间，新续接授权为 12 秒。四例各 11 个已采样 PID/starttime 和真实模型例 10 个身份现再次只读核查，均无存活；监听关闭证据限夹具终态，不扩大为全宿主隔离。
- `real-model-r1` 确为原 `refactoring-quality` 结构叶与显式 Responses 绑定：source 63.193 秒、child 36.864 秒成功；三份父 Skill 附件 4,084B 两轮完整读取、新 scope、原前缀与旧结果保持。独立核两个前轮随机标记均不在新 **native prompt**、均出现在实际 child response；不以合成回复替代该证据，不宣称累计计费或异后端错误独立性。

本方向最终实际行为与结构检查已无阻断项。实际 Ergora 自身审查模板、最终公开文件静态检查、普通发布／精确远端及本候选自己的 CI 仍由原交付 owner 收口；本补核不提前宣称整片已发布或 CI 已通过。

## 自身模板与公开摘要补核

已只读核 `self-review-r1-codex.json`、原 run／input／stdin、九文件 packet 索引和原回复：原 `ergora-structure-review/root/review` 使用明确的 Codex 回退，73.433 秒、approve，无可执行 finding；结果 SHA256 为 `acdb060f5c6570769fcff414e06f7a5115380373c145d4a60618dcfccdcdc9fb`。九份完整文件 220,205B 逐项按长度与 SHA 从实际 task 中重取，实际 prompt＝stdin、祖先 inline 均在其中，五产品及测试与当前候选逐字相同。审查时的三份文档快照与之后的状态补记分别处理，不把模板回复冒称独立运行验收。

已核[公开验收摘要](evidence/2026-11-14-harness-session-continuation.json)：五案例字段与刚复算的私有 audit 完全相同，自身审查字段与原结果相同；未包含机器绝对路径、服务地址或凭据。新增后端手册失败 B2／`restored_bytes:null`／`observation_error` 段与实际实现一致。已重查完整 tracked／untracked 文件范围，没有新增产品或测试改动；自身模板和公开摘要检查无新 finding。

总计划的原 P3 已关闭；片计划和交付正文尚存“实际 SDK／模型在途”“自身模板尚未完成”的旧当前状态文字，已通知原 owner 按已完成证据同步，属于本片记录收口。普通发布、精确远端及自己的 CI 仍待原 owner，未取得证据前不宣称通过。

随后再次读取总计划、片计划当前状态与交付开头／r3 状态段，均已同步 133／12、四 SDK 场景、真实模型及自身 73.433 秒 approve；前述状态提示关闭。当前公开摘要 SHA256 为 `845e36e0835d9e10d40b1e53729d56145294ba2d37f7d01738b4b3120a8d001f`，产品／测试 diff 仍为 `90c14415978fafe742cf4f42e94655683137f19d267babe1dd1cf49314134b7e`。**本方向本地出口通过，产品结构／规范与文档开放 finding 为 0；普通发布、精确远端和自己的 CI 尚未核验。**

## 同片普通发布身份核验

精确提交 `47443840b68693f63ee011dc6fbe29421a42223f` 的唯一父提交为原固定基线 `67966095814eec01f2e1e5d65d87e289320ad79f`。独立从 Git 对象重取全部 17 份变更文件，大小与 SHA256 均逐项符合 `static-r5.json` 的 ready 清单及 `commit-r1.json`；五产品＋测试 diff 仍为 `90c14415978fafe742cf4f42e94655683137f19d267babe1dd1cf49314134b7e`，没有未审产品修改。发布前新增状态记账限总计划／交付／公开摘要，不改变原行为判词。静态原记录为 225 个本地链接、无坏链接／私有机器字符串、diff check exit 0；扫描排除的通用 loopback 安装 URL 在原固定基线已有，不新增私有服务。

只读核原作者 `push-r1.json`：普通 push，无 force，exit 0、5.961 秒；`ref-r1.json` exit 0、1.416 秒，精确返回上述完整 SHA 和 `refs/heads/refactor/architecture-foundations`。未重新发起远端查询、推送或模型调用。**本方向发布身份核验通过，开放 finding 仍为 0。**

另重算官方 Actions 列表原 HTML SHA 并解析 embedded JSON，确认 [Portability run 43495562208](https://github.com/626619403/Ergora/actions/runs/43495562208) 绑定上述完整提交和当前分支；留存观察为 `WORKFLOW_RUN_STATUS_IN_PROGRESS`。这仅证明本候选自己的 CI 已启动，尚无终态及完整 job／必要步骤证据，不能记作 CI 成功。

## H3b 自有 CI 精确终验

本附录覆盖上节 CI 待验状态。独立只读核官方 `ci-run-html-r5`、`ci-jobs-json-r1` 原 HTTP 200／body，以及每个 job 的最新终态页面：plan／六个 Linux job 为 r2，Windows job `132127694689` 为 r3。本轮选取的 10 份原 HTTP 回执，其最终 URL、原字节大小和 SHA256 均匹配；没有新请求、日志／artifact 下载或模型调用。

run 页面明确为 **Success**，完整提交链接仍为 `47443840b68693f63ee011dc6fbe29421a42223f`。原 jobs batch 共 8 项、`hasMore:false`；逐项 ID／name／run href 与元数据一致。用该固定提交的 workflow 与 Linux 分组文件确定检查范围：plan 1 项、Linux 六组各 4 项、Windows 5 项，合计 **8 job／30 必要步骤全部 success**。每个必要步骤均有 `completed_at`、`data-job-completed`，且 log 路径明确包含上述完整 SHA、对应 job ID 和 step number；所有页面的其余步骤也未出现失败结论。Linux 上按条件跳过的 Windows 专属步骤不计入必要项。

独立 HTML 解析所得 job、步骤、结论、起止时间与 `ci-parsed-r3.json` 逐字段相同；该原解析记录 SHA256 为 `8a0eaed739e94fd5b4b2fc6c594608de36713ca0a9961663732fce7eeb39ff15`。原 jobs batch 的早期 in-progress 状态仅用于确定完整清单，最终结论取自上述终态页面。

**本方向 H3b 精确发布／自有 CI 终验通过，结构／规范开放 finding 为 0。** 判词限已审并发布的 `47443840b68693f63ee011dc6fbe29421a42223f`、其 r3 包／实际调用证据与本次 CI；不扩为 Windows 原生续接、正式任务恢复、GPU、其他后端或另片 F9a 工作树验收。
