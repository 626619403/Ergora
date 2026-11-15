# r5 私有现场 harness 独立静态审查

2026-11-16。Reviewer：fresh-context 独立 agent `cycle_r5_harness_review`。初审需求符合性与可维护性均为 request changes／开放 2 项；文末同片修正复核后两轴均 **approve，开放 0**。范围仅为新身份准备、正例／故障 driver、wrapper、观测及 root 中断工具的静态准入；不认证任何未来现场、产品完成、真实训练质量或进程收尾。旧现场的结果及旧审查的原范围／身份保持，不能转记到新包。

## 输入、身份与检查

读取项目 `AGENTS.md`、`docs/PLAN.md`、首轮计划 W2/W3/W4/W5/W7/W8、eviction 修补交付、旧 [harness 审查及 r6](2026-11-16-training-cycle-live-harness-review.md)、maintainable-project-delivery／independent-review brief 与 ergora-codebase-quality 的验证和仓库约定。主树为 `refactor/architecture-foundations`、HEAD `df43660`；工作树原有文档变化未覆盖。只写本报告，未改 harness、产品、服务、PLAN，未提交／推送。

独立读取新旧原字节并核 `prep-identity.json` 的 11 条记录，均与文件匹配：9 份原 fault/helper 脚本逐字相同；`root_case.py` 只将 expected worker SHA 从旧版改为新版本；observer 只改三处 r5 输入／输出／停止 marker 名。另核 `prepare_negative.py` 差异，只有 tag 校验及其对所有 case IDs／run／setup 名的应用；`drive_positive_r5.py` 只有 cpu5／positive-r5／review-r5／输出目录替换。新 setup 另行逐行读取，未将它误称为旧 setup 的逐字复制。

14 份下表 Python 文件均经独立 `ast.parse` 和内存 `compile`，没有导入或执行任何 harness；未运行服务、网络、API、runner、Workflow、Replayer、产品测试或 preparation。只读核实际安装 worker、原 S/H flock seam、原 services 及 pidfd owner。下列 SHA256 是本轮读取的准确 raw 身份。

|文件（均相对 ignored `cw1/`）|SHA256|
|---|---|
|`fault-harness-r5/prepare_negative.py`|`4188942642c860b11257b1032dedc5918da70101b83e8effb40e9a164662dea9`|
|`fault-harness-r5/drive_fault.py`|`ca6fa0ab31e1422439abeb48ea33a2e61880625e4e8e133c89fa319f10172e7f`|
|`fault-harness-r5/drive_extra.py`|`0a092740d67b3638321992379bd6836427714786e95ca65f71a301c91cd2ba36`|
|`fault-harness-r5/service_wrapper.py`|`8658d70ba791b35829e8860676bc95c513435c24b3a32bd41f1ed2e7f919a559`|
|`fault-harness-r5/service_wrapper_extra.py`|`870b88aeaa353173919dff56d8ac4792b37aadeac5e31fed1300d472328e77f3`|
|`fault-harness-r5/fault_operation.py`|`30e547b0c2448744fc6c3e7d0865c37ea6cf42da55d029d1df88b3ad8643a2cf`|
|`fault-harness-r5/root_case.py`|`8d32a350d2b7862569a2fbbaee71b9319349aa7a7f50ffecb577ac16e10f4708`|
|`fault-harness-r5/root_interrupt.py`|`5598d0535455cbf3d551bef859f1c53c8af9ec959a10322e94b09b4c039d4c36`|
|`fault-harness-r5/observe_wrappers.py`|`f1908b9f5ee93547f5c26c27172391242178c083b5c7a648bc69cb1f7c5eff8f`|
|`fault-harness-r5/probe_signals.py`|`20f75733d8002b01753d5e24a81411667bb55dd1430fba8f59a0cf9d2ecd6bb7`|
|`fault-harness-r5/service_control.py`|`61105e7a207952c72a7e655f0ab93e240e7e0257a5424610fb820c19313c10a7`|
|`observe_live_r5.py`|`7e4753a92d9d006e27864d484b3177aa596324578408e23d7f3eb46139cdb095`|
|`live_setup_r5.py`|`51930552b83ac1b9444299d7a04ae6c94947593fbd6bd9f947942ec022169d18`|
|`drive_positive_r5.py`|`b73b71c134a9c1ca36be87f9fabbadc2ffb44f104ddd6b2d7e65211342ba13e7`|

新 setup identity 所指 manifest 原字节 SHA256 为 `34e3c4f06912eca774dcd422f8e48df1df2e325f4c219d6f2d35eff7faff379c`；其实际安装 worker 原字节为 `7996f73d51cdfe4a749d4b1ab80b86a757091546723960bd92087d3a046c53e9`。已只读复核这两个 SHA，不据 setup 内的 `services_started=false` 推断之后服务当前状态。新 wheel／53 项安装测试／原完整 history replay 的结果来自修补交付，本 reviewer 没有重跑。

## Findings

### R5-H1 / P1：新正例 driver 仍会遮蔽首因并中断独立证据采集

位置：`cw1/drive_positive_r5.py:75–107`。

当正式 Workflow 的 result、query 或结果断言先失败时，except 中直接 await describe／cancel；这些诊断 RPC 再失败会取代原错。无论主流程是否失败，finally 又串行 fetch history、写 status、Replayer、decode/audit：例如原 result 超时后 Temporal 暂时不可用，或 replay 先失败，后续 audit 完全不会保存；history/status/replay 的新异常会成为最终异常。`failure.txt` 的存在不能保证原 traceback 的最终保留，也不能弥补独立原件缺失。这是实际 r5 重新纳入范围的文件；旧 fault driver 的 H2 修复没有覆盖它。

最小修正：在现有正例文件内采用已审 fault driver 的 primary exception／traceback 与逐阶段 collect 结构，不必抽公共新模块。清理 describe、cancel、result 各自采集；raw history 先保存，最终 status、activity audit、native/evidence-after、replay 独立运行；有主错最终重抛主错，次级错单列并使该次验收失败／待证。无主错但 collection 失败也不得宣布通过。保持原授权、预算、固定 run 和业务断言。静态复核应覆盖“主 result 失败后 describe／replay 再失败”路径；不得执行现场来替代这条控制流修正。

### R5-H2 / P2：W7 hold-ready marker 仍存在空／半 JSON 发布窗口

位置：初审 `cw1/fault-harness-r5/service_wrapper.py:67–68` 与 `drive_fault.py:102–103`。

wrapper 直接对 `hold-ready.json` 调用 `write_text`，创建／截断文件发生在完整写入之前；driver 仅等待 exists 就立刻 read/decode。跨进程可在文件已出现、内容未写完时调度 driver，导致 JSONDecodeError，提前进入 cancel／收尾，真实 history flood 根本未发生。这与旧 extra H6 的可达竞态相同；extra marker 已原子发布，但 W7 marker 尚未修正。文件逐字复制本身不能排除此缺口。

最小修正：在原 wrapper 内将完整 marker 写到同目录独占临时文件，close 后 replace 发布，照用已审 extra wrapper 的局部做法。保留新 case 的原件不覆盖约束和原 scheduled-time deadline，不增加 hold 或产品窗口。也可在原窗口内专门重读暂态半 JSON，但原子发布更小、更容易核对。修后仅需静态核准确新 SHA／发布顺序／deadline 不变，再由 root 单独执行实际 W7。

## 已确认的边界与现场仍须提供的证据

- **身份与权限：** 新 tag 同时作用于 project／baseline／experiment／runner／cycle 和目录；旧全局原件存在时拒绝复用。root 须真实传入新 tag，包括 extra 的 `--prepare` 路径；遗漏时拒绝不等于新身份准备成功。正例固定 cpu5／positive-r5／独立 review-r5，并在投递前验证新 manifest 与 candidate 的绑定。共享不可变 runner repo、materials 及原 c/s/h 不等于复用旧授权，也不构成新训练证据。helper 只允许 stop 原 cycle worker；前台 wrapper 及原 services owner 的职责清楚，未发现新增提权或宽范围发信号路径。
- **W2：** pre fault 在原 adapter 调用前失败，post fault 在原 adapter 完整返回后用 SDK failure 代替 completion；它们各自不能冒称物理丢包。post marker 不保证 publication 已发生，root 必须核真实原 intent／attempt／receipt、request／launch／ack／owner 数量、SHA 和 root 身份，再结合真实 history 的最大 attempt1、start/request 至多各一次、后继 observe／reconcile 判定。driver 的 control checks 只是其中一部分。
- **W3：** 固定 receipt.run_id，无重新 authorize／submit；root_interrupt 保存 authorization／cycle／controller 与当时 managed 原件，核原 SHA／BOOT clock，再以 pidfd 通知旧完整身份、等待退出后用同解释器／installation／settings／环境启新 child。新 child 由其直接父 Popen wait，旧 exec session 的实际 wait 仍归 root。driver 的 immutable 过滤不覆盖所有 authorization／controller 原件，须同时使用 root interruption 的完整 catalog 比较；control-check 全 true 不单独证明完整 W3。真实同 run、重启后只读 observe、原计数／activity IDs／A/D 与原链最终不变仍待现场。
- **W4：** marker 来自实际非 cold dual-QUEUED、尚无 managed request 的原 adapter 返回；原 finite hold 不刷新产品 allowance。root timer 通过原 owner 仅停 Temporal，要求原完整身份退出也赶上同 marker deadline，采样原 authorization BOOT work 至非正、留原 total 中的 restore 空间后恢复；异常后独立尝试恢复，主错与次级错误区分。实际 stop/start 回执、原 server 退出时刻、断联区间跨原 work 耗尽、恢复后没有新 request/publication、最终 stop reason 必须一起核，不可只用最终剩余量推断断联命中。新 case 的预算必须在 authorize 前冻结。
- **W5：** 原 S/H seam 使用精确 authorization 路径／activity type／request mode 的真实 flock，未替换原清理算法。两次 API 请求、第二次时原 H 完整身份仍在且 normal 未 exit、stop 独立 queue 及实际 enter 先于 normal adapter exit 均有独立记录；缺 marker／样本不会按通过处理。SDK CANCELED、stop envelope、durable／drain／executor proof 与全部资源 wait 必须分项。TRY_CANCEL 的本地完成不会替代实际 S/H 清理。
- **W7：** driver 使用真实 Describe 的 `history_size_bytes >= 8*1024*1024`，而非导出 JSON 文件大小；每次完整 malformed signal Payloads 小于32KiB，最多384次／16并发。拟将新 settings 的 `flood_seconds` 设7，仅改变原窗口内采集尝试：实际截止仍为 `min(original_hold_deadline-.35, now+7)`，wrapper 的原 hold 仍从 SDK scheduled_time 算、至多8.5秒，并非续期。尚不能静态保证7秒足够；未达真实 server 阈值必须保留失败／待证，不加长预算补通过。还须由真实 history 验 `history_capacity_limit`、cold 后无第二普通命令、原完整结果与 replay；本场景不认证第256／257次 ordinary 的另一矩阵。
- **W8：** probe 使用默认实际 converter 的完整 Payloads，验证 compact JSON 恰到边界但含 metadata 后超限、原身份／reason 拒绝和真实一个合法 stop，并核 query/outcome 中明确 null 的未证明字段。stop-failure extra 明确是原 stop 返回之后的容量类型消费桥接，不是实际 N32 aggregate overflow；原完整 stop 结果和真实 failure history 要分别保留。
- **采集与收尾：** fault／extra driver 已逐项保留主错，raw originals／history／audit 与 replay 分开；W5 自有 flock 先释放。root_case 的完整身份通知使用原 pidfd owner；`requested_not_yet_waited` 只是请求。新 observer 路径隔离不表示已有新采样；sampler 也明确可能漏掉短命后代。原 owner/S/reaper 原件、旧新 wrapper 的实际 session／Popen wait、自建 formal/native Workflow 终态、所有 S/H／root／后代及服务／sampler 最终清理仍须 root 实际审计。未认证未来新 history 的完整 replay。

基础服务 `observe_live_r5.py:16–20,46–51` 保留旧 simple sampler：`same()` 对 OSError／ValueError 一律返回 False，最终只输出 survivors，没有 unknown 分类。因此它只能报告“在成功匹配的观测中未发现存活原身份”，不能凭该输出或末尾的 zero-live-survivors 文案声称所有身份均确定退出／unknown0。PID 字典与0.1秒采样也不是完整后代 census。root 已明确另以原 S/H／reaper 及完整身份追加核对；增强 fault observer 则对 absent、PID复用、仍存在但身份不可判定分别分类并令 unknown 失败。此项按上述限制使用，不要求为本轮新增第三个 sampler；若最终交付只引用 simple sampler 来证明 unknown0，应保留验收未完成。

初审两项需修正并按准确字节复核后再决定 r5 harness 的静态准入。其余条件是未来现场必须提交的原证据，不能由本报告预先标成完成。

## 同片最小修正复核 r2

独立读取修后完整文件和 `prep-correction-identity.json`，该差异原件 raw SHA256 为 `5a63d885e4bdc8a7578c9d6819faec8d14808ae3b3f344c4607f5d7e11b92fec`。两份新 Python 经 AST／内存 compile，未导入／执行；上表其余身份与初审范围保持。本节准确新身份覆盖表内这两份初审文件，不覆盖历史结果。

|文件|修后 raw SHA256|
|---|---|
|`fault-harness-r5/service_wrapper.py`|`0a12e3f97761836ae90c7a5581047047b25ae56ef8725d378e6f506dbd7c203c`|
|`drive_positive_r5.py`|`640935f72f2b5cd34cc092a5f776510a10c093bb1605cae5ca33e7ee5934b4a3`|

R5-H1 关闭：正例 `:46–149` 将网络连接／运行纳入主错捕获；主异常与 traceback 在任何诊断之前保存。cleanup describe／cancel／result、native／evidence、query、history、status、audit、replay 各自通过 collect 记录错误；raw history 在 audit／replay 前保存，audit 或 replay 失败不会跳过另一项。最终优先重抛主异常；仅 collection 失败也明确失败，不冒称通过。原产品预算、授权、固定 run、结果／ordinal 断言保持。启动前 manifest／review 校验失败尚无已提交 Workflow，直接失败不构成这里的首因遮蔽路径。

R5-H2 关闭：wrapper `:64–71` 保留原 scheduled_time deadline 与至多8.5秒窗口，仅把 ready 发布改成同目录 `.tmp` 独占创建、完整写入并 close 后 replace。driver 见 ready 存在时不再能读到尚未写完的目标 JSON。该 marker 无 crash-durability 合同，也不承担业务 stop proof。

r2 需求符合性／可维护性两轴均 **approve，开放 0**，仅表示上述准确身份的私有 harness 可继续由 root 进行实际验收。root 另报 r5 W2 pre-start 通过、pre-request 在途及独立 CPU review 已产出；本 reviewer 未执行／检查那些运行原件，不将它们列为本轮实际通过项。W3／W4／W5／W7／W8、完整实际 history replay、全部进程 wait 和最终服务收尾仍各自按原证据判定。

root 随后报告已在新 case 授权前固定 W4 wall90／cleanup60／control30，W7 仅设 flood_seconds=7；本轮静态分析确认这些选择与上述窗口算法相容，但未读取运行后授权原件来认证现场预算身份。simple sampler 的 unknown 局限已明确由 root 追加原件和完整身份核对，不包含于本静态 approve 的资源停止证明中。

## W7 单 signal 负载窄复核 r3

按 root 请求，只读核尚未执行的新 W7 producer 调整及 `w7-producer-sizing-r5.json`。独立从旧准确 driver 原字节比较，确认新 `fault-harness-r5/drive_fault.py` **只有 `:105` 的 `os.urandom(22500)` 改为 `os.urandom(24000)`**；新 raw SHA256 为 `f8346fdd4070f184c027904fa89c0cac82e53625bb7c4653e51c63c456103819`，旧值仍为 `ca6fa0ab31e1422439abeb48ea33a2e61880625e4e8e133c89fa319f10172e7f`。新文件 AST／内存 compile 通过，未导入／执行脚本或调用 converter／服务。

该调整只增加每条 malformed signal 的数据量，base64 数据部分由30000变为32000字节；完整 Payloads 的实际 metadata／编码仍必须在运行时计算并严格拒绝 `>=32768`，不能由这个原始字节数直接宣称完整编码合规。payload 形状仍然 malformed，不产生合法 stop intent。原最多384条／16并发配置、真实 Describe 的8MiB阈值、`min(original_wall_deadline-.35, now+flood_seconds)`、每批剩余时间 timeout 和原结果 release／未达阈值失败逻辑逐字不变；wrapper 原 scheduled-time／至多8.5秒 hold 未被本次修改。root 指定的新 settings 为 flood_seconds=7，不续产品 allowance。

r3 针对这一个 producer 数据量变更，需求符合性／可维护性两轴均 **approve，开放 0**；新 SHA 覆盖初审表内该 driver，r2 其余准确身份保持。旧r4未达阈值的历史结果不改写，增加每条负载也不能静态保证新现场达到阈值。实际完整编码字节数、server history_size_bytes 过8MiB、`history_capacity_limit` stop／无第二普通命令、完整 history replay 与全部资源 wait 仍须新现场原件。本 reviewer 未认证 root 并行报告的 W3 首case启动 argv 差异、其收尾或后继 r5b 运行结果。

## W4 同 handle 只读等待窄复核 r4

只读核新的 `fault-harness-r5/drive_extra.py`，raw SHA256 **`a18e0956da519feff740b3003e851b56e0cff2dead43852775a75d2082303dde`**；相对初审／r3 的旧 driver `0a092740d67b3638321992379bd6836427714786e95ca65f71a301c91cd2ba36`，独立计算的完整 diff 与 `prep-w4-read-continuation-identity.json` 逐字匹配，后者 raw SHA256 为 `63a8f374989a3cf1b49c53237a03a74a69baca6ee64ea0273592749b824b8900`。新文件 AST／内存 compile 通过；未导入／执行 harness、SDK、服务或 Replayer。

变更只新增真实 SDK `temporalio.service.RPCError/RPCStatusCode` 导入及 W4 的 result 等待分支 `:200–218`。只读检查本安装 SDK 源码，确认 `RPCError.status` 返回实际 RPCStatusCode，UNAVAILABLE 为14；此处捕获实际异常类型且只接受 `status == UNAVAILABLE`，非凭异常文案或任意 Exception 继续。其他 RPC status 原样抛出，TimeoutError、取消、Workflow failure 与记录写入失败也不会被此循环吞为成功。

W4 在开始等 result 时只生成一次 `monotonic()+result_wait_seconds` 测试截止（原新设置为180秒）；每次仍调用原 receipt.run_id 绑定的同一 handle.result，只传该固定截止的剩余秒数，没有重建 client／handle、重新授权或派发业务 effect。重试后的短 sleep 同样受剩余时间收窄；超过固定截止时 wait_for 以超时退出，循环不刷新截止。每次真实 UNAVAILABLE 的类型／status／完整 traceback、wall／monotonic 时刻、固定截止与 workflow/run 身份都追加保存，先前错误不会改写为未发生。非W4的 result 路径保持原样。

该180秒是原 harness 的只读结果观察上界，与原 authorization BOOT work／total、活动窗口和业务清理 allowance 分开。新增分支未修改 authorization、clock、预算、settings 或产品；原 root outage helper、无新 request/publication 的 history／原件检查及 collection／cleanup owner 均保持。当前正式类无 continue-as-new 路径，验收仍须核实际 run 身份与原 history，不由同 handle 的描述代替。

r4 针对这个 W4 只读 RPC continuation 变更，需求符合性／可维护性两轴均 **approve，开放 0**。此 SHA 覆盖前表的 drive_extra，其余已审准确身份保持。root 另报告旧 W4 真实断联与业务／history 检查命中、但只读 client 重试耗尽使 driver exit1；本 reviewer 未核那些运行原件，旧 failed 不因本修改追认通过。新 r5b 的真实断联时刻、原预算／clock／SHA、同 run 无新 publication、history replay 及所有完整身份的退出／wait 仍须新现场分别验收。

## W7 cold prefill 显式分支静态复核 r5

只读核新 `fault-harness-r5/drive_fault.py`，raw SHA256 **`1c226be76cc4f5109c7ffc82684065f07a89f841c352ed0528d04b9f42b755f0`**；原独占备份 `drive_fault-before-prefill-r5.py.txt` 为 r3 的 `f8346fdd4070f184c027904fa89c0cac82e53625bb7c4653e51c63c456103819`。独立计算完整 unified diff，与 `w7-prefill-r5.diff` 逐字匹配，其 SHA256 为 `6c58b1edeebf425e1589dde24e14cbe636a5dc4ee1e64f9ae30eba70d587a773`；`prep-w7-prefill-identity.json` raw SHA256 为 `26cc6f2d0753ba5878d6b83ba3ccaab2004c38ce87eab715a614100db63d93c8`。独立核 flood 以外原字节、其他顶层 AST、原非prefill分支及其余 owner 保持，新文件 AST／内存 compile 通过。未导入／执行脚本、SDK、converter、服务、runner 或 Replayer。

新行为仅在明确配置 `history_prefill` 时进入 `flood:101–245`，提前在原 cold 执行期间发 malformed signals；没有增第二个调度器或改产品。原 handle 从固定 receipt.run_id 取得，discovery 只读同 handle 的真实 history；要求真实 start input 等于原 intent，唯一 cold `candidate-0-1` 的 type／queue／完整 request／ordinal0／retry1／schedule与start窗口匹配。读取本安装 SDK 源码确认 fetch_history 使用 handle 原 run_id、history.run_id 来自真实首个 start event，activity.Info 的 scheduled_time 使用 protobuf ToDatetime 加 UTC。新分支按相同微秒转换从真实 scheduled event_time 推导 `+min(8.5, actual_schedule_to_close-.75)`，并将 flood 固定截止进一步收窄为该值减.35与当前时刻加配置 flood_seconds 的较小值；没有用发现时刻重造10秒或续期。真实 timeout 非正／大于本类cold10秒上界、绑定不符或晚到只能失败。

首次发送前必须见同 workflow/run/action/activity/attempt 的唯一真实 adapter-enter 且无原return／exit，编码后在第一批前再核一次。完整实际 converter Payloads 仍严格小于32768；配置 signal_limit 被限制为1..384，每批至多16。每批所有 signal 与后续 Describe 在同一固定截止的 asyncio.timeout 中；gather(return_exceptions=True) 等待整批，统计 issued 与实际 ack，任何异常结果都会抛出首个错误，不把异常列表当成功。发生整体 timeout 会保留 timing_miss 和此前 Describe 样本；只有该截止内实际 Describe 的 history_size_bytes 过8MiB才令 reached=true，不用导出JSON大小或后续 collector 补成命中。

真实原子 hold-ready 仍必需：flood 末尾在原 hold deadline 内核其完整 run/action/activity/attempt、原结果精确路径、与独立推导值精确相等的 wall_deadline。没有把推导 deadline 冒称实际 ready。discovery／decode／编码／RPC／最终 marker 任一失败均进入原主错保留路径；finally 分别尝试 release 原结果与写 flood report，次级错误不会替换首因，也不会作为通过。未达阈值或 marker 未验证保持失败／待证；原 wrapper finite hold 仍是兜底，不因此给产品增加 allowance。

r5 针对这个显式 prefill 变体，需求符合性／可维护性两轴均 **approve，开放 0**，未发现需阻断的新静态问题。新 SHA 覆盖 r3 的 drive_fault，其余已审身份保持。root 须使用全新 tag／冻结 settings 和原预算执行，保留原 initial history、完整 batch／Describe、ready及event原件；并单独判定首个实际 server signal 与原 adapter 返回的时序。跨进程“读到enter且尚未读到return”的采样不能单独证明两者不存在竞态，更不能仅据该检查宣称精确首个server-signal先于原返回；若实际顺序未证明，该子项待证。root 另报旧W7再次未达阈值、其 cancel/replay/wait已完成及W2/W5原路径通过，本 reviewer 未核那些现场原件，不改写它们的范围／结果。新的真实8MiB guard、无第二ordinary、完整history replay及全部实际资源wait仍未由本静态意见认证。
