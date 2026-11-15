# c1b2a：真实服务安装验收

日期：2026-11-16。修后提交 `eedba08c8c112683a7946726aab3f4fd590f26d6` 已完成本页所列新包、真实服务链路、存储隔离和生命周期验收，全部自建运行资源已收尾。原 `fef7d98` 包的安装／非法请求路由结果保留在[服务交付](2026-11-16-training-cycle-service.md)，不转用于修后产品。

新 wheel SHA256：`747e221b584fa71518e2b64ce69fcace2eb4ef1340450cfd50e6f47e8729e017`。core／SDK 各 663 个产品文件 source＝wheel＝site，执行位相等；283 参考文件 verify PASS，依赖检查通过；core 无 SDK，SDK 1.34.0。178 个测试／示例在 build 前冻结，命令与完整输出保存在 ignored `package-r2/`。相对 `478c98891522930817fa7005a8ac96e408f37230` 仅五个原产品 owner 变化，无新增／删除产品文件。

验收使用独立 CPU 项目、真实 Temporal 与管理 Supervisor；应用 SDK Python 启动 budget／cycle 两个独立进程，原 native 依赖及参考安装保持。最小测试 Workflow 使用 `TrainingCycleWorkflow` 名称、默认 SDK sandbox、原六字段 input 和原 producer 写出的 intent／attempt／memo／receipt，只驱动四活动；它不是正式总 Workflow。准备的 CPU baseline／runner／候选仅用于服务合同，不证明执行器运行、训练质量或优化收益。

|验收项|方法与当前状态|
|---|---|
|修后安装身份|通过；旧 Temporal／Supervisor 显式停止／关闭，新包原命令重建，Temporal／budget／cycle 三个不同 PID，保留 stopwaitsecs＝70|
|真实四活动与 SDK 来源|正常轮通过；原 `_CycleOperation` prepare／submit、原 attempt／memo／receipt、默认 sandbox Workflow；首次 inspect 真实认证为 queried，controller 最终 COMPLETED|
|首活动缺 receipt|通过；测试仅在 producer H 的原 receipt 写入前等待，真实 activity H 观察 receipt 不存在、查询原 SDK run 并调用原 owner 写回；producer 随后观察同一 receipt。两处原记录前的 absent 标记、真实 history 与原件均保留|
|单次 start 与对账|正常轮通过；新场景由原 API 新建两实验／新授权；ordinal 1 非重试拒绝；ordinal 0 的 prepare／confirm／dispatch 三份真实引用；重复 start 与 reconcile 均只 reconcile，原 attempt 字节不变|
|实际 SDK attempt 2|通过；测试 wrapper 在原 start 完整执行返回后主动抛 retryable ApplicationError，由真实 SDK 重试。attempt 2 的 H request 与结果仅含认证／reconcile；原 intent／attempt bytes 和 inode 不变，无第二份 prepare／根。此项不是网络丢 completion 故障认证；仅该测试 Workflow 使用 maximum_attempts＝2，正式副作用策略仍属 c1c|
|交接根跨服务关闭|通过；正常产品 command 下，start 已确认交接后显式停止 cycle 服务，再启动并继续对账／stop；原预算根在停止和重启后保持同一完整 PID 身份，最后由显式 stop 收尾|
|正常 stop 完整性|通过；全部 6＝2＋2N 分支均有原 S/H stopped、returncode 0 和 stdout 引用，实际 bytes／SHA256 逐项吻合；原预算根退出并留下 fenced final。执行器停止事实保留 null，不从服务状态推断|
|独立 stop 槽|通过；normal inspect 的 H 在指定 cycle.json 读取接缝等待真实 flock，stop 六分支全部返回时该 H 仍存活。随后释放外部测试锁，normal 才继续；没有把业务存储移入父 loop|
|SIGTERM／SIGINT／重复取消|分别通过；持阻塞 H 时触发 TERM、INT 或四次真实服务 task.cancel，保留原 S/H／唯一 reaper，核 H 与旧服务 PID 退出、两个真实 Worker run／shutdown 终态；另显式停止 Supervisor 可能重启的新实例|
|stop Worker fatal|通过；USR1 向真实 SDK activity poller 异常队列注入测试 RuntimeError。真实 on_fatal_error 后 normal shutdown 已开始而 stop 阻塞 H 仍存活，随后两 Worker 与原 H 实际收尾；原 fatal 日志保留|
|强杀边界|直接 SIGKILL 受控场景通过：旧服务 PID 已退出时 H 仍活，明确记录 business_stop＝unknown；之后等待原 H 收尾并调用原显式 local stop。此项未实测 Supervisor 等待 70 秒后的 SIGKILL，不把后续清理证据归功于强杀|
|最终收尾|通过；核 144 个记录的进程身份，无业务残留；73 份独立 stdout 引用逐份 bytes／SHA256 相符；3 个实际预算根均退出并有原 final。11 个测试 controller 最终 5 COMPLETED／6 TERMINATED；3 个候选 Workflow 中 1 原已 COMPLETED，2 在本次最终测试清理显式 TERMINATED。所有服务停止、管理 daemon not_running、socket 不存在，7233／8233 无监听|

所有故障入口都位于 ignored `training-cycle-service-acceptance/harness-r2/`，不会写入产品、参考安装或共享环境。服务进程中的标记日志是显式测试 instrumentation；业务存储仍由原 H 处理。原件与命令记录保存在同一 ignored 验收目录，不把机器私有路径写入公开文档。

首次存储阻塞探针因测试取样起点早于首次 inspect 完成，误取已结束 H 的标记而失败；失败日志／history 保留于 `business-blocked-r2` 与 `run-blocked-r2`。该 controller 已终止，无候选 start。修正测试取样边界后使用新实验／新 cycle 授权在 `business-blocked-r2b` 通过，没有改产品或重授旧时钟。

现场业务选择为 N＝2；真实 SDK 下 32 候选 fanout 未在本页运行，66 refs／容量边界按独立源码和冻结安装测试记账。信号／重复取消／fatal 场景持有真实 cold H，未另做未交接预算根故障实验，相关原生命周期安装接缝不混入现场计数。两候选 Workflow 的最终管理 terminate 只清理测试流程，不当作本地执行器停止证明；本页没有启动执行器、训练或 GPU 工作。

最终证据集中于 ignored `training-cycle-service-acceptance/live-r2/final-audit.json`、`final-listeners-and-original-identities.json` 与各 `business-*`／`run-*` 目录。原 r1 Temporal 已在切换时停止，新 Temporal 也已最终停止；数据库和所有失败／成功原件保留。未改产品／native／共享环境，未提交或推送。


## r3：launch guard 容量分类修正后的定向实测

本节仅记录提交 `97a0bbfae9687c15927f1437a374cd070baf0a94`、wheel SHA256 `081aab4594f8afa18505c3ec8a8b78ff98690510303a7041e3074af5fcab38cf` 的新实测。主控新建 package-r3 的 core／SDK 各 663 文件／执行位同一、283 参考与依赖通过；本次只读核 source pin／安装清单，未重复构建。原 r2 生命周期结果保留其原身份，不转记为 r3 运行。

从 daemon not_running／无旧服务开始，由新 SDK Python 经原 services 创建 Supervisor 配置；实际 budget／cycle 为不同 PID，配置和 `/proc` 命令都指向新安装，cycle stopwaitsecs＝70。原件使用全新 `harness-r3/`、`live-r3/`、`business-*-r3/`，r2 原件保持。

|定向场景|结果与证据|
|---|---|
|两候选正常链路|已通过；新 API 实验／新授权下，原 producer 与默认 sandbox fixture 完成 inspect、ordinal 0 start／交接、重复 start 只 reconcile、显式 reconcile、stop 六分支。原 intent／attempt bytes 和 inode 不变，完整引用核 SHA256／bytes；实际 stop SDK Payloads 含 metadata 为 2,930 bytes|
|32 候选 stop|通过真实 SDK 完整 fanout：writer 1＋drain 1＋notify 32＋observe 32，ordinal 0–31 各恰好一次；66／66 为真实 ref，全部 S/H stopped、returncode 0，raw bytes／SHA256 逐项相符。实际 Temporal history 的 Payloads 含 metadata 为 **19,354 bytes**，未触发容量拒绝|
|最终收尾|通过；2 个 controller 与 1 个候选 Workflow 均原已 COMPLETED，无管理 terminate；唯一实际预算根退出并有原 final。核 140 个记录身份，无业务残留；84 个活动 stdout refs＋4 个 producer refs 全部吻合。服务／Temporal 停止，daemon not_running，socket 不存在，7233／8233 无监听|

两轮均未启动执行器或训练；32 候选只验证 stop，没有候选 start 或预算根。两轮新授权预算均为 wall 900／cleanup 180／control 60 秒，未重授旧时钟。32 候选的完整计划为 231,293 bytes；原产品 `_cycle_snapshot` 自身产生的完整 snapshot 为 5,775 bytes，没有测试裁剪。准备原 API 资产／计划／授权用时 95.70 秒，真实 producer／fixture drive 为 10.02 秒。此场景证明 32 候选完整 fanout，不作为容量超限拒绝的实证；launch guard 容量反例仍按主控独立新安装接缝记账。

本轮原件包含完整原 producer request／receipt、Workflow history、实际 SDK Payloads protobuf、逐 ordinal 分支 stdout 与 SHA 引用、实际服务命令、关闭和端口观察。外部测试 `/proc` 观察器以 50ms 间隔记录 138 个服务／子孙原身份且终态零存活；没有在产品 loop 加业务 I/O 或改动服务入口。短暂未采样子进程仍以原 S／唯一 reaper 的 stopped 与真实 wait 返回为证。最终清理记录位于 ignored `live-r3/final-audit.json`、`producer-ref-audit.json`、`final-listeners-and-identities.json`。r3 本轮没有失败重跑或新增产品修改，原 r2 失败原件保持。


## r3b：真实 N32 混合 unknown 与最终 SDK 容量边界

沿用 r3 wheel `081aab4594f8afa18505c3ec8a8b78ff98690510303a7041e3074af5fcab38cf`。当前源码 `af176cf6e79adb9c6ef6f32946672bc77cdb89de` 相对包来源 `97a0bbf` 仅测试一行变化，产品相同。两场景分别通过原 API 新建 32 候选、cycle 与 wall 900／cleanup 180／control 60 秒授权；不复用已停止授权，不启动候选／执行器。

唯一故障注入沿既有 `failed_owner` constructor 接缝：仅 `notify-owner` ordinal 0 抛普通 ValueError；真实 SDK、原服务、S/H、唯一 reaper 和其他 65 分支保持。它是测试 constructor 故障，不是实际 OS syscall 失败。短／长错误保存在独立私有设置；业务 stop reason 保持完整短输入，避免先触发 request 或 cold 操作容量。

|场景|实际结果|
|---|---|
|短 constructor reason，N32|初跑一次通过；实际 SDK stop input 含 metadata 489 bytes，完整结果 19,510 bytes。65 个 peer refs＋1 完整 inline unknown；92-byte 原原因逐字保留，unknown 的 stopped=false／returncode=null，且没有 operation 目录／伪造 ref。其他 65 分支全 stopped／rc0，原 stop_durable=true，授权／plan／ready hashes 不变|
|约 20KB constructor reason，N32|初跑一次通过；实际 SDK history 的 stop input 为 493 bytes，随后真实 ActivityTaskFailed 为非重试 `cycle_activity_capacity_exceeded`。产品原日志完整未发送封套由同 SDK 编码为 **39,518 bytes**；20,066-byte 原原因逐字保留。全部 65 已创建 peer stopped／rc0／refs 核实，另 1 inline unknown 无 H／无目录／无 ref；原 stop_durable=true，授权／输入 hashes 不变|
|最终收尾|两场景 controller 均原已 COMPLETED，无管理 terminate；无候选 submission／预算根。274 个记录身份零存活，134 个独立活动 stdout refs 校验通过。两次服务／Temporal／daemon 关闭确认，最终 socket 不存在、7233／8233 无监听|

新原件位于 ignored `harness-r3b/`、`live-r3b/`、`business-*-r3b/`。长场景 preflight 精确编码实际业务 input，并用旧完整 N32 封套加当前错误做明确标注的投影；最终证据来自真实 SDK history 和产品原日志的完整 `full unsent value`。长场景投影为 39,487 bytes，实际未发送封套为 39,518 bytes，二者明确分列；没有用投影代替实际拒绝，未丢弃原因或字段适配容量。

两场景均仅初跑一次通过，没有修改产品、扩大容量或重授授权。原始 history 逐项核对了实际输入 payload；短场景完成结果与客户端原结果相等，长场景原 activity failure 的 type、non_retryable=true、retry_state=2 均保存。完整未发送封套仅作为外部验收原件从原日志恢复，不是新增产品账本。定向证据见私有 `business-mixed-r3b/complete-result-audit.json`、`business-aggregate-r3b/complete-result-audit.json`、后者 `worker-stderr-delta.txt` 与 `original-unsent-envelope-from-worker-log.json`；总收尾为 `live-r3b/final-audit.json`。
