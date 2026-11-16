# M6 真实 CPU 两轮：最小资产前置清单

2026-11-16。只读资产盘点，基线主树 `debf6f9`，进入时 Git 工作区干净。已读根 AGENTS、PLAN、已审 M6 runtime 计划及旧真实现场交付；本次仅写本页。未启动服务、联网、探针、导入 SDK、安装、测试、回放或训练。以下存在与 SHA 只证明文件现存，不能证明环境可用、正式 V2 已实现或真实两轮通过。M6 设计页开头的待审字样属于原文，当前审查状态依 PLAN；静态批准不转成运行通过。

## 可复用原件与身份

证据前缀 `L=.ergora/checks/cw-live-r1/`，均为仓库相对 ignored 路径，不是公共下载。持久 CPU 源码及 native 安装的私有绝对位置只沿 `L/setup-r5/identity.json` 的 `assets`、`native` 本地解析；本页不发布这些位置或私有源码。已按该引用逐文件确认四源码、七材料、review 和 comparator 存在并计算 SHA，没有递归搜索整个 `.ergora`。

|现存证据／素材|raw SHA256／原身份|
|---|---|
|`L/setup-r5/identity.json`|`74dff0e917ae1e6a4463288d0977cfc9ec10992cbbd31f1b1d03a8cf48c812eb`；仅记录旧安装与资产定位|
|`L/setup-r5/definition.json`|`f346f8c573af9e31f3d37738e80f005963b5f58450b7d1907f284a4b98938e67`；项目 cpu5／revision1，六阶段开发检查明确不在私有 CPU 合同内|
|`L/setup-r5/baseline.json`|`680ab4df62c61e8b04b90390f95a7036e293658fdcb03aa6560c053b8b29fafb`；cpu-baseline-r5，commit `d04229205fc5d9f2e90617d2592812e9229a36e6`|
|`L/setup-r5/runner.json`|`646dcbf667cc705515af8f31669b143fe33b488bb015212556d94951205cdbc8`；cpu-measured-r5／timeout60秒；登记 runner 逻辑摘要 `dcec4f018f26d1e26ca20631dd23d7c4bd3b6c9ad9245149df49e66bfa7831ce`|
|`L/s/training/manifests/positive-r5.json`|`34e3c4f06912eca774dcd422f8e48df1df2e325f4c219d6f2d35eff7faff379c`；旧 experiment positive-r5；不能由 draft 摘要替代|
|`L/setup-r5/manifest-draft.json`|`ce352ae064070e25303740d4691326e847f4ff1d3731a0490d827240774fd7a1`|
|`.ergora/checks/cw1/live_setup_r5.py`|`51930552b83ac1b9444299d7a04ae6c94947593fbd6bd9f947942ec022169d18`|
|`.ergora/checks/cw1/drive_positive_r5.py`|`640935f72f2b5cd34cc092a5f776510a10c093bb1605cae5ca33e7ee5934b4a3`|
|CPU repo 的 prepare.py／runner.py|`b9022a4fc685a1ab8c73534d835e5d23b928a6b98ede197620b5107a0b3bdb37`／`3dc4f844e4b68ec4d4eae230c3f0331d90579aab806e77e5cd57b3b255dfbadc`|
|CPU repo 的 oracle.py／workload.py|`b652530d79c30d6d245500ca59bb47b2d74d23657e4eb4f35354e6cb8533b04d`／`2a99383c82968046f3b46963b8a422218db8b96370697f3450cf9bbdd1640524`|
|native upstream/compare_runs.py|`9d931b68dc8577cad3f66355588e526a55e5ecf3ebf0bc0e0b0f179828f0ad1d`|
|CPU review-r5.json|`82098e26ea6768bf6396940a14918068090ddfea04c3a80a9efd18e7ab2b6f9b`；仅绑定旧最终 manifest／commit，不授予新候选|

材料当前 SHA 与旧 manifest 相符：baseline-config `6c2a143d400907a5ad11796d64953db6cc1598170489e884549aef7a7c245fc6`；candidate-config `859bef2fc02906d0e8bb901662f5e9b05fcd7a6a30b1198d0abfd36fd6eec09f`；dataset `1734ddd5791b858b1051838f1167f0e33548e9b375c49b32b6fb120a6594a985`；environment `11847a01f874a38e435700d18c4372b4065af9d6562f3c6a462a84cd61152ec6`；initial-state `9f5496fc55f776dac23d28afc533eed44a5c6804aa449d602b30223c279b6774`；validation-contract `3de216967b27ef68343ea23f6ae2b5b6bbea1b4e0aaee00478b3fdfc0c37ca4d`；workload-contract `baa140035f87751486095f84c93197cec57c1a600040ee0647a93f49f29fc2f4`。未读取或发布完整 environment 内容。

旧完整现场在 `L/first-positive-r5/`：created `9f89d9ee4bb1bbb269603612edc7caa537b7a49d371f5046ba0ce0abc40a5438`，authorized `856962b238403f551883a175ca7c5af5715bb156457a98b2527fd48c2df1d5d8`，history `dc7d9587823941f0f7a99d0a6f2c6a366d58ddbd7d50f695f48cc7c87fbd47c8`，evidence-after `8a1e635036a6232f95b865a88a2f1d53a24e0df296a1aaa1abe38fec41a7898a`。旧 accepted archive 目录为 `L/s/training/projects/cpu5/perf/experiments/positive-r5/accepted-evidence/9da94e910e9cd8fba6dce021a8cfbca0253f4d16febd3038c2bab34d981a4af8/`。目录存在不是本次完整归档复验；旧首轮无 ordinal1、measurement_accepted 仍 null，不能复制为新两轮结果。

## 复用合同与调用轮廓

旧 CPU runner 可作为两个新候选各自执行时的同一数值/测量工具：8组固定输入，每组32整数，AB/BA交替，每臂新进程；baseline 重复平方和，candidate 闭式等价；独立 oracle 逐次奇数相加生成平方并核512个输出。归一化32整数，至少8对，10000次 paired bootstrap、95%区间，下界节省须超过10ms。包含进程启动和输出 I/O，共享 CPU 不保证独占。质量为 NOT_EVALUATED，不是训练质量放宽授权。runner 只排除输出根的 execution.log，仍包含嵌套同名和其余 runner-owned 产物；不能扩大排除。

prepare 工具的静态入口为 `materials --output`，以及 `manifest --materials --source --comparator --output --commit --experiment-id --baseline-id --author --owner`。runner 为安装 Python `-B` 调用，参数沿登记材料：`--manifest {manifest} --output {output} --baseline-repo {baseline_repo} --candidate-repo {candidate_repo} --materials … --comparator … --review …`。oracle 接 `--input --outputs`。runner 核源码、clean Git checkout、材料摘要以及独立 review 对 manifest/commit 的绑定；不能把旧 review 换名复用。

旧 setup 顺序是 registration → baseline preview/initialize → runner preview/register → experiment preview/prepare（旧 max_run_seconds180）→ inspect。它硬编码 cpu5/positive-r5 并拒绝占用，不能原样重跑来覆盖旧资源。旧 driver 硬编码一个候选、cycle first、旧 create/authorize/prepare-controller/submit-controller，再取固定 receipt handle观察；wall600/cleanup120/control30 是旧出生参数，不能证明足够两轮。其私有 `_CycleOperation` 调用与旧首轮断言只能作路径参照，不能替代 M6 正式 V2 creator、v3活动和真实 history 验证，也不能发明第二验收器。

## 后续最小可执行清单

1. 等 M5 与 M6 精确联合候选实现/冻结，固定新非editable core/SDK/wheel、完整产品/输入与真实 SDK 版本。重新核实际 creator、版本路由及现有唯一 reader/comparator 接口；旧包定位文件的存在不等于可用安装。
2. 明确两个预先选定候选的独立 experiment ID、最终 manifest、commit/config 与共同 baseline 合同。现有确认的正例只有 positive-r5；不同旧现场重复执行不自动构成两个可消费候选。可复用同一源合同/runner/oracle，但须为两项分别 prepare、独立 review最终 manifest；不得临时搜索新候选、改 baseline 或从旧 archive 复制新证据。
3. 按原入口建立新登记/runner材料和新 experiment；若复用既有登记，先核准确 revision与绑定。新出生 schema3/program-v2 cycle选定 N=2，冻结 measurement_sources、共同合同、原 intent/permission、连续 BOOT根与一次预算。旧 owner/sourcepin/ID/clock 不升级、不补写、不重新授权续命；旧已停止现场只作历史证据。
4. 在运行前由现场 owner 确认可用 Temporal endpoint/namespace和管理/收尾权限、准确安装、四 versioned poller/两业务许可、budget/native/executor、真实项目 revision、磁盘和可捕获进程、同 BOOT执行条件。旧交付记录服务全停；本次未确认当前服务状态、端口或 SDK 可连接性。先确定原预算足以两轮完整 I/O及cleanup reserve，不能测试中续预算。
5. 从正式父Workflow真实调度得到 activity.info、固定 run/namespace及scheduled history，依 M6 原验收器顺序执行两个真实候选，重新产出成对原数据/oracle/comparator/gate/archive。保留全prefix、同次 acceptance、原五records和第二 intent 的原前驱绑定；默认sandbox与完整实际编码/容量/恢复/取消/stop/重启/丢回复等按 M6既定矩阵验收，不能以本次清单或旧首轮通过抵扣。
6. 分列父子终态、人工release窗口与执行器停止，保留原件/实际wait/完整进程身份/服务及端口收尾，再做独立终核。无自动release、baseline晋升或把 null停止字段补true。

真实模型训练/GPU及质量 B3仍独立待实际工作负载、设备、完整输入/预算和teacher/student/judge或可信质量oracle；这些CPU素材不关闭该条件。本次结论仅为后续最小准备路径，未改变任何产品开放状态。
