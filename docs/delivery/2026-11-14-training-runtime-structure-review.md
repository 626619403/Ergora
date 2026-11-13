# F9b1 原生训练实时查询：结构、性能与冗余独立审查

日期：2026-11-14。审查者：fresh-context agent `/root/f9b1_structure_review`。先读原始要求、[活动计划](../plans/2026-11-14-training-runtime.md)、冻结差异与实际调用者，再读作者交付记录。采用仓库 `AGENTS.md`、maintainable-project-delivery／independent-review brief、codebase-design 与 code-review Standards 方向；AIHERO 索引用于定位相关 Skill。

基线和当前 HEAD 均为 `8182499fa46c61adecea2f6defd2c777a433eed5`，候选是未提交工作树。精确范围为私有 `.ergora/checks/training-runtime/review-r1-files.json` 的16个文件及 `review-r1.diff`；三个新增实现／fixture／test均全文读取。首次审查与最终补核之间产品、测试、CI及使用说明哈希保持原冻结身份，变化仅为 `docs/PLAN.md`、本片 plan／delivery 的状态记录及新增验收摘要／审查记录。邻接读取包括原 training reader、task runtime、registration、console生命周期、原 `perf_temporal` 模型／连接／client／workflow及实际 Temporal SDK 1.34.0。

## 需求范围结论

**本方向源码及最终本地证据补核通过，无 finding；普通发布与自己的 CI仍开放。** CLI、HTTP 共用 `training.status`，先复用原离线 reader 核登记、模板、manifest／spec与 Git 归属，再显式查询。新调用链只有 describe、首历史事件、query、result；完整原 Experiment JSON 以既有 `canonical_sha` 比较，describe 后固定实际 run，结果读取使用 `follow_runs=False`。原领域负结果保留；其他 Temporal 结束显示 `NEEDS_RECONCILIATION`，未把外部停止、门禁通过或批准当作查询结论。未发现第二账本、调度器、批准协议或模板权限旁路。

## 可维护性结论

**通过本次检查范围；阻塞0，其他可行动 finding 0。**

|检查点|判断依据|
|---|---|
|Module 与 Interface 的实际消费者|`training.status` 由 CLI／HTTP 两处消费；`reference.training_runtime_status` 的单一应用调用者是 training owner。新的 `reference_training_runtime` 是项目专属子进程的 Implementation，隔离 import-time CONFIG／STATE 与可选 SDK，具有具体生命周期职责；不需要为当前唯一原训练 owner增加插件 Interface。|
|原 owner 与成熟库复用|直接复用原 Binding／Experiment／Status／Outcome、workflow ID、connection及 SDK。原 `perf_temporal.client` 是完整操作 CLI，status 不核完整启动输入／固定 run；`DevelopmentTransport` 验证开发任务 spec，不能接训练 Experiment。当前选择未把开发任务合同复制给训练。|
|校验归属与配置范围|timeout／run ID 检查属于公开输入，原 Experiment validator拥有实验参数范围；安装身份门禁新增 perf_temporal家族。完整输入、run与返回 binding检查保护运行事实归属。没有把实验时限钉成测试夹具的默认值，也未新增无实际消费者的兼容分支。|
|进程、性能与冗余|进程创建、环境和错误处理沿已有 task runtime模式；RPC、协程与外层进程均有界，原查询路径不启动后代作业。只读请求复核身份、启动独立进程有固定开销，但没有自动轮询或全历史扫描；未发现足以构成 finding 的重复计算。相似的 task／training启动样板均留在 reference owner，当前没有需要通用执行框架解决的具体维护问题。|
|页面与回归保护|`training.js:37`、`:46` 同时核 DOM连接、项目、home、详情序号及本次查询序号，旧成功／错误均不能覆盖后选实验。新增15项合同场景集中保护原输入认领、负结果、NOT_FOUND区别和无写读取；只登记既有 Linux CI组，未新增测试框架或重复 CI流程。|

## 检查与证据边界

- 独立有界探针位于私有 `.ergora/checks/training-runtime/structure-review-r1/`，命令为 `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv-dev/bin/python -P .ergora/checks/training-runtime/structure-review-r1/probe.py`。两套不同 config／state 在独立子进程中保持各自目录；未给 run ID与显式固定 run均正确；原生 DataConverter 能保留 `poll_seconds=300`、`max_run_seconds=86400`、`release_wait_seconds=604800`、`cancel_wait_seconds=3600` 的完整 Experiment。拒绝取消的查询在外层进程时限 **6.016秒** 后报 unknown，并已回收 PID。结果保存在同目录 `result.json`。探针没有网络、服务、安装或训练原件读写。
- 直接执行 `reference.verify()`：固定参考 **283文件 PASS**。未修改产品、原参考或既有证据，未执行 Git写操作；新增内容仅此报告与授权私有探针。
- 作者 source-r3 原日志为 **47通过／1失败**；失败指旧已加载的 reference内部导入清单。source-r4 为更新后原14项架构检查全通过。本审查保留两轮身份与失败，不合并成一次全通过，也未重复跑大套测试。
- 初审时安装、实际 CPU旅程、浏览器及自身模板原件待补；以下记录同一候选的最终补核。本审查没有再次启动服务／浏览器、调用模型、安装、跑大测试或修改产品；不继承 F9a成绩。

## 最终本地证据补核

同片最终原件齐备后，由同一审查者只读复核。本轴最终本地出口通过，阻塞0，其他可行动 finding 0。私有可复算审计为 `.ergora/checks/training-runtime/structure-review-r1/final-evidence-audit.py`／`final-evidence-audit.json`；实际执行命令为 `PYTHONDONTWRITEBYTECODE=1 .venv-dev/bin/python -P .ergora/checks/training-runtime/structure-review-r1/final-evidence-audit.py`，结果 passed。

|证据|独立核验结果与范围|
|---|---|
|最终安装身份与回归|wheel SHA `7ac58997490fac91b3ed15d75f6a5c13b7f36b3b4a517b7dcb069f3295e59adf`；564产品文件在当前源码／构建快照／wheel／noneditable安装间逐字一致。重算 wheel RECORD 572行、安装 RECORD 577行及283参考文件摘要。安装四suite原日志为48通过／54.67秒，受控进程56.438秒；旧 F9a scope注记与独立 correction原件保留，本次按实际 F9b1快照核验。|
|真实原生事实与恢复范围|核初始 `not_found`、原 `QUEUED`、固定 workflow／run的最终查询与 SDK完整 Outcome相等。通过真实 SDK／DataConverter重新解码42事件首输入及末尾 Outcome，完整原 Experiment和 `CANCEL_UNCONFIRMED`均一致；本地 executor的 `CANCELLED`仍独立保留、started文件不存在。21配置／训练原件 SHA保持。|
|辅助失败与同 run接续|全文核初始／三轮恢复脚本及原命令、cleanup记录：首辅助缺 asyncio、下一辅助缺原生搜索路径、再下一轮因把真实 `CANCEL_UNCONFIRMED`预设为 `CANCELLED`而退出。最终恢复沿同一 SQLite／workflow／run读取，命令日志中 start与cancel各一次，没有重新 prepare／start／cancel。原脚本、负结果与中断收尾保持；通过范围是实际控制事实及原 run读回，不改写为一次从头无失败的训练旅程。|
|自身原结构模板|从实际 task逐份提取14完整文件，重算197,068B及各自 SHA；产品／测试／邻接调用者与当前候选一致，plan／delivery是调用时的完整状态快照。prompt与实际 stdin逐字一致，三份祖先／叶资源均在 stdin，叶权限等于父模板及 grant，formal execution未授权。原 reply／result一致且 SHA为 `70d3aeb687eeb092dbfa79e1785d241188575f7103c60714cdc1447db4dfa559`；46.248秒、approve仅作为静态模板审查，不冒称异后端成功或独立运行验收。|
|实际页面与迟到响应|核默认导航30请求／0 status，随后手动原负结果与完整 Outcome。实际 status持有后切项目、重选同详情、两次倒序返回均通过；倒序旧回复的 phase加哨兵用于辨识。45个请求均 GET／200，其中6个status。实际 API字节及 JSON与原 SDK绑定查询一致，served training.js与当前源码／安装相同。三视口1440／960／390无整页横向溢出，原桌面／手机截图已独立视觉读取。|
|进程收尾与公开主张|核四次 monitor cleanup、浏览器 close成功及 closure范围；补核时原 controller身份不存活，7233／42391无监听。monitor的 cancelled／-9只证明私有验证进程已停。公开[验收摘要](evidence/2026-11-14-training-runtime.json)的身份、原负结果、原件数量及范围与原件一致；没有 GPU、模型训练、统计收益、采用或远端停止成功主张。|

本轴最终本地核验不覆盖普通发布、精确远端 Ref及本片自己的 CI；这三项须发布后另补。F9b2写操作、F9c可信采用、真实 B3、完整 C2和未验平台继续按各自合同保持开放。

