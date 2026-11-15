# c1b2b 执行消费者真实现场验收

日期：2026-11-16。状态：真实现场定向验收与资源收尾完成，[同片独立最终复核](2026-11-16-training-cycle-execution-product-review.md)已核原件，需求／维护性两轴approve／0。仅由临时测试 Workflow 驱动已实现的六个活动；不实现或认证 c1c 正式总 Workflow。

固定产品提交 `bcc304894622040a7d844f8c6f9ddfded65aa895`，非 editable wheel SHA256 `55029a3b4b574b7934e40bc115b32ff4b99600a9e47894dbaf1c6c59937e5bba`。源码、安装和 283 参考文件身份由[安装验收](2026-11-16-training-cycle-execution-installed-checks.md)分别记录，本页只记真实现场新增证据。

本现场使用新独立配置、运行目录和控制目录；已有 native 安装、依赖及空 fixture Git 提交只读复用。用户已接受当前 Docker 容器及当前 Unix 用户作为执行边界，原 `execution enable --trusted-current-container` 仅写本次新配置。通过原 `services.control` 启动本地 Temporal、MLflow、training-budget-worker 与 training-cycle-worker，两个 worker 各有独立 PID/event loop。预算服务队列 `ergora-training-budget-v1` 有 8 槽；cycle 的五个普通活动共用 `ergora-training-cycle-v1` 的 1 槽，stop 使用 `ergora-training-cycle-stop-v1` 独立 1 槽。临时默认 SDK sandbox Worker 只承接 Workflow tasks。未使用通用 executor 服务。

预先固定 CPU 合同为 `[1,2,3,4] · [5,6,7,8] = 70`，输入和算法绑定在注册 runner argv 中。runner timeout 10 秒，experiment queue+run 120 秒；cycle wall/cleanup/control 为 300/60/30 秒。首次只读观察 10 秒，后续普通活动截止为 `min(保守扣除调度与等待耗时后的 work, 原 control, 10秒)`，普通活动最多 32 次轮询、间隔 1 秒、SDK maximum_attempts=1，stop 使用最近事实中保守扣除耗时后的 total。任何失败不延长预算或重授同一 cycle。

由原项目注册、baseline、runner、experiment preview/confirm 和 cycle 授权 API 创建候选；由原 prepare-controller/submit-controller producer 生成 intent/attempt/receipt。临时 Workflow 从 v2 facts 等待同固定 run、同 binding/job 的 runtime/native 双 QUEUED 后，调度一次 request；之后只读观察。执行必须经过原 request、预算根 admit、唯一 launch、native attempt/ack、Sandbox、runner 与原 reaper。没有模型、数据集、GPU 或训练任务。runner 故意不写 `evidence.json`：原质量门槛拒绝是预期，native SUCCEEDED 不代表测量被接受。

追加定向场景包括真实 SDK attempt2 只读重试和一次真实存储 flock 阻塞期间的独立 stop 槽检查。重试注入明确为原活动返回后的测试错误，不称网络丢包；该测试仅将 request 的 SDK maximum_attempts 设为 2，初始间隔 0.1 秒，两次共用同一至多 10 秒 SDK schedule-to-close，不扩大原预算。每个场景新授权。旧 N32 容量矩阵不重跑，旧现场不计本片证明。

## 实际结果

|检查|真实观察|结论边界|
|---|---|---|
|前置与拓扑|原 API 注册及发布一致；Temporal 与 MLflow 健康检查通过；预算／cycle 服务为独立 PID，通用 executor 保持 STOPPED|服务 RUNNING 与业务准备就绪分开验证；只启动列明服务|
|首个执行候选|原 producer 产生固定 controller run；v2 冷观察、start、同 run 双 QUEUED、request 一次、有限观察、stop 顺序实际完成；11 个活动 completion，27 个完整 refs|唯一 request 调度后没有第二次 request；原 request/launch/attempt/ack/stopped 同链|
|CPU 与原 gate|两个执行候选均写出 actual=expected=70，native SUCCEEDED；均无 evidence.json，原 gate passed=false、archive_report=null|首场最终 v2 runtime 为 COMPLETED/GATE_FAILED，durable_stop/executor_stop/reap 均 true；没有接受测量、训练质量或性能结论|
|实际 SDK retry|原 request 活动第一次返回 requested 后注入测试 retryable error；真实 SDK attempt2 返回 existing_only；两次 request 摘要相同，attempt2 的原操作只有 inspect-controller-activity 与 observe-candidate|history 仅一个 request schedule；不重新发布 request、补 root 或 launch。不是网络丢回复试验|
|独立 stop 槽|真实普通 H 在读取 cycle 原件时等待 flock；持锁期间 stop 队列完成 cold 检查并进入 stop-writer，1.797 秒后父 stop 已可见；随后释放锁，drain／notify／execution observation 与正常观察各自完成|持锁期间证明 stop 已实际运行并发布；完整 stop completion 和 durable stopped 在之后独立核实，不以发布等同全部清理|
|交错事实|重试场最后一次普通观察同时给出 native SUCCEEDED、durable stopped=true、runtime 仍 RUNNING/QUEUED；最终固定子 run 自然 COMPLETED|保留非原子观察，不由 native 或 reap 推导 runtime phase|
|六活动与重放|inspect/start/reconcile/stop v1 和两个 v2 均取得真实成功结果；三个临时默认 sandbox Workflow 的真实 history replay 通过|这是 E7 临时消费者证据，不替代 c1c 正式 Workflow、E8 或任意多轮实现|
|完整性与容量|全场 56 个不同完整 stdout refs 字节数／SHA 核实；投影 source_operation_id 与同封套 ref 匹配；三场实际 SDK completion 最大分别为 3,597／3,582／2,691 字节，均含 payload metadata|没有截断原件或用 ref 隐去父侧错误；不重复认证旧 N32 边界|

## 保留的失败与修正

首次新运行目录的最终 socket 路径为 106 字节，但 Supervisor 先绑定追加 `.PID` 的临时路径，超过 AF_UNIX 上限，原 services.control 拒绝启动。没有 cycle 授权或 runner 执行。已保留原失败目录与原因，改用新短私有真实路径重新注册，无 symlink 绕行、产品或依赖修改，也未复用授权。

MLflow 初次进程 RUNNING 时 HTTP health 尚未就绪，首次探测 ConnectionRefused；待原服务完成启动后，明确健康检查通过才授权候选。没有把 Supervisor 进程状态当任务 readiness。

重试场临时 fixture 误给旧 inspect.v1 传 ordinal，原活动返回 non-retryable `cycle_activity_request_rejected`。失败留在原 history。只修临时 fixture 的 wire 形状，新增一个独立授权的 observe→inspect→stop 最小补验成功；该场没有 start/request，没有预算根或 runner。其余执行场不重跑，也未更改任何产品逻辑。首次审计脚本把链中 canonical SHA 与文件 raw SHA 混比而失败；审计改为分别核 canonical 同链与 raw 原件摘要，原产品记录未改。

## 收尾与可复核材料

两个原预算根均有 final 原件且原身份已退出；两条原执行链有完整 stopped 同链。三个 controller 与两个候选的五个固定 Workflow 最终均自然 COMPLETED，未调用 terminate。两轮原 services.control shutdown 均 confirmed，最终 daemon not_running；7233、8233、5000 均无监听。外部采样结合原 owner、S/H、executor／supervisor／reaper 和活动原件，共核 171 个完整 PID/start_ticks/boot_id 身份：live=0、unknown=0。采样可能漏过极短子进程，其回收证据仍以原 S/reaper completion 与持久 stopped 为准，不声称主机全局进程审计。

旧 stack 的 platform 配置仍为 execution_enabled=false；新注册发布仍一致，三个消费者产品文件在收尾时与固定 r5 摘要相同。所有命令、冻结 runner argv、实际配置／注册、原授权与历史、注入代码／事件、原件摘要、replay、进程与服务收尾记录保存在忽略的私有验收材料中，由独立 reviewer 直接读取。本页不公布机器路径。没有提交／推送、安装系统包、修改 native/shared venv、模型调用、GPU、真实训练、collect/accept/release、自动后继或正式总 Workflow。
