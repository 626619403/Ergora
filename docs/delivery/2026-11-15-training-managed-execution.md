# B3.3c 真实执行与停止：逐步交付

日期：2026-11-15。固定[设计r2](../plans/2026-11-15-training-managed-execution.md)已获新fresh-context计划两轴approve／开放0／0，R1仅设计关闭；c1本地r2两安装身份、24控制回归、16架构、真实Temporal控制旅程及自身原模板已通过，新fresh-context产品最终本地两轴approve／开放0／0，准备普通固定发布；c2未实施。实际实施基线为B3.3b普通发布的`6c7e9d924f822e60a54ce8c0686a56758ae0359a`，它自己的CI及独立终核现已闭合。kernel专家保留在v3优化路径。下列分段保留当时状态。

本次只读复核原BudgetedStart／phase supervisor、processes回收、原submission／run历史、取消、native request／executor和解释器／依赖路径。计划将完整工作拆为c1非阻塞phase生命周期与c2显式单job受管执行，各自验收与独立审查。新增launch预留在执行S出生前消耗一次许可，避免hook前强杀后因缺attempt而重跑；原start slot、clock和实验账本保持原owner。

下一步固定c0原要求、候选文档与实际源码身份，交新的fresh-context计划评审者。当前不把草案中的命令、schema2能力、launch／attempt／ack／stopped或并行执行记为产品接口。B3.3b产品及原283没有因这两份草案而改变。

## c0 r1生命周期问题与r2修正

固定23份design-scope-r1的SHA256为`dadb2647c00f81651c5d97cd2c973cbe8af25d5c05e8b76f590e929e6938bc8b`。新fresh-context评审者独立复现r1的顺序冲突：先由原processes.run回收业务、发stopped，再在同S新起publisher，父据已stopped于total杀S后publisher仍活着；探针已精确SIGKILL／waitpid收尾。作者接受，r2明确S在stopped后仅直接做记录读取／写入／同步及结果观察，不再生成任何子进程；发布卡住时父只终止无子进程的S，持久证明unknown。

r2同时明确复用原reference.worker_command的包自身bootstrap，避免另一套环境加载；评审者Python -S探针只确认现有validator／clock及native依赖解析的导入边界，不认证未来gate或真实native依赖。原r1完整候选／probe-results.json保持，当前未修改产品、运行训练或授执行权；待同reviewer正式报告及固定r2复核。

## c0通过、c1开始本地实施

新的[独立计划报告](2026-11-15-training-managed-execution-plan-review.md)已对固定r2两轴approve／开放0／0，R1仅在设计层关闭。c1沿原`_BudgetPhase`拆start／非阻塞poll／request_stop／finish，原run调用同一生命周期；父侧用出生前已核budget.folder与固定相对路径纯拼接，真实safe_file／mkdir／stderr.open留对应S。原owner仍只运行原四种控制phase，不新增执行能力或runner。

原phase-isolation fixture去掉ThreadPoolExecutor，改同一父进程真实交错监管两S；peer进入受控fsync阻塞，monitor仍须回收真实setsid后代，父不启subreaper。收尾先向全部peer请求停止并继续轮询全部，已终止后才finish。父侧业务路径查验用可达失败接缝保护，不以只看函数文字认证非阻塞。原大帧、持有reader、异常S、取消、fence与final阻塞及原合同回归仍待实际运行；当前没有验收通过主张。

## c1源码首项与r1／r2安装身份

原phase-isolation源码精准回归1 passed／68 deselected／31.05秒，外层32.055秒；同一父进程实际轮询两S、peer确实触达受控fsync、monitor回收真实setsid后代、peer此时仍存活，父subreaper为0，最后两S／helper及后代均被原断言检查停止。源码r1冻结三文件清单SHA256为`1435f5b301d09febc5717c5d55cae0ef1cb953a9fd458af28901a7c860055604`。

r1两安装650逐字／283及依赖检查通过，wheel为`414a8ccf150f263159a99da02967bf3f73684e872b25bf1fa3ee65dc4359ecb0`；未用它跑最终完整矩阵。自查后r2只补尚未发送payload的selector初始化失败收尾，以及将已有有界startup stderr纳入unknown原因；原peer测试字节不改。r2三文件scope为`b7869bd8ac5baa22968bc00d830571fdcbef5af849676c3f986e46bbb29efdf0`，新安装进行中。第一次r2构建脚本误指不存在的前置venv，尚未启动构建即FileNotFoundError；原空输出及失败单列，修为已完成的c1 r1 SDK解释器后再构建，不改产品迎合脚本。

实际安装输入只冻结174份tracked tests/examples，未复制node_modules／构建产物。接着验原24项控制接缝、完整架构边界、真实Temporal控制CLI旅程和原自身结构模板，再交新的fresh-context产品审查；此前源码1项及r1身份不转授最终r2全部行为。无c2执行权限／runner／训练／GPU／收益主张。

## c1 r2安装与实际控制旅程

r2非editable core／SDK各650份源码／wheel／site-packages逐字、283参考和依赖检查通过；唯一产品变化为原reference_training_budget，未增加模块。wheel SHA256为`e66e1e5a73fc5bea6a2c4fc08a5cf349d26a88c7c7d0221531e6af9ed7a7cbb0`，core无Temporal，SDK为1.34.0。安装完整架构边界16 passed／0.44秒，外层1.217秒。174份实际测试输入保持，最终原24项控制回归及自身原模板仍在运行。

同一r2真实本地Temporal／budget worker的实际CLI控制旅程54.635秒通过：原submitted run、queued native request、共同预算下自动fence／原取消、只读回查和同slot resume，原授权／request／attempt字节保持，第二候选未启动。Supervisor、worker、owner／phase和两端口均已按脚本收尾；没有启动executor或业务训练。它是改变phase监管后的控制集成验收，不能替代c2的runner／全后代持久stop或真实训练／GPU验收。架构文档已同步新低层生命周期和仍串行的原owner边界。

## c1原自身结构模板通过、独立产品评审进行中

同一r2安装使用原`ergora-structure-review@1.0.0`及用户已授权Codex回退，实际54.264秒两轴approve／开放0／0，外层56.786秒。19份全文268198B与三份祖先资源完整进入实际stdin，原结果SHA256为`487188320a1c127267eed032429696a909d65e99e910372cdfefa13ca3a22604`；仅审供应的完整源码文本，不认证私有包／运行或CI。未声称异后端。

新的fresh-context产品reviewer已独立接收固定10份候选及原要求／c0r2合同、现有安装／架构／真实控制原件。候选scope为`5657f03c5a1225149863d55ee75ccd9cf43875a6cce09978e8db1354c049d4c9`；产品／测试继续等于source-scope-r2，完整原24项安装回归尚未结束，最终本地结论不预记通过。前置b自己的CI43674493548及原独立终核继续分别等待。

## c1 r2控制回归完成

原最终安装控制回归已结束：24 passed／80 deselected／495.27秒，外层496.327秒，exit0。输入为冻结174份tracked tests/examples中的原training_submission、reference及services三suite，沿原24项选择，覆盖phase peer隔离、短写／大结果、异常S、父死亡、safe-reap、fence／final发布故障、原start slot及来源边界。完整命令、stdout、stderr及JUnit均保留，不把选择子集称全库回归；同r2完整架构16项另计。

关键私有原件位于`.ergora/checks/training-phase-lifecycle/`，公开文档仅登记相对路径和SHA256，不要求读者有本机缓存：

|原件|SHA256|
|---|---|
|`source-scope-r2/scope.json`（三产品／测试）|`b7869bd8ac5baa22968bc00d830571fdcbef5af849676c3f986e46bbb29efdf0`|
|`installed-tests-r1-scope/scope.json`（174输入）|`df5957fae258427ccddf076a5983e2501dbae695194e4f8071055f713afdb42a`|
|`installed-regression-r2.json`|`60d28e096c4a96859c38158cbf8097c1d843e048f9d9793f6f3a911f80e721f4`|
|`architecture-r2.json`|`b0c701bcf068abf391f2e171f0483d9e154eb959159c9f325ae5b8589d27f9e5`|
|`native-journey-r2.json`|`d9f5f6afd8f0f8ef0f371af35f0b678a516b90f5c85430bce5f86dbf1b1c37ce`|
|`self-review-r2-codex.json`|`fc0fd9c76ef1440e985cba4a82ab6945ae0998203dacff701bf278b5956be2d6`|

原fresh-context产品reviewer已获完整回归原件继续终核，最终两轴结论与精确发布仍待。c1只提供原phase生命周期，原BudgetedStart生产四mode仍串行；没有c2出生能力、execute命令、launch／attempt／ack／durable stopped或自动循环。前置b自己的Windows CI及原独立发布终核未闭合前不推送本片；未改v3 kernel路径。

## c1独立最终本地审查通过

新的fresh-context[产品报告](2026-11-15-training-phase-lifecycle-review.md)对固定r2需求／结构两轴approve，开放0／0。评审者沿真实调用链核父侧无业务metadata I/O、四mode仍串行、stopped后无spawn及原唯一reaper，另独立便宜探针核769次实际短写、大帧、90k stderr排空并仅留64KiB、selector／Popen启动故障收尾。它逐字核两650安装、283参考、174测试输入，直接读取24项完整原件、架构、实际九CLI／同run原件与全部已知PID／socket收尾，以及自身19全文／三祖先资源实际stdin和原result，未发现可证实产品finding。

作者最终三份进度文档也已由同reviewer完整补核，`product-audit/final-docs.json` SHA256为`47699f0abb08a794e2dd9f71f2d295fae07ddc7048bb512c6ec610f33901eb8f`。此后只追加审查／发布状态。前置b自己的CI与原独立终核、本片精确stage／普通发布和自己的CI仍分别待闭合；不以本地通过代替它们。

## 前置b闭合，准备c1精确发布

前置固定6c7自己的CI43674493548／attempt1八job／30必要步骤全部success，原产品reviewer固定发布与CI终核两轴approve／开放0／0，原[终核报告](2026-11-15-training-executor-protocol-review.md)已追加。本片产品／测试继续等于已审r2，只追加这些门禁状态及原报告；现做完整staged范围／AST／Git tree链接和摘要核对。未将后继c2笔记或产品混入，也不提前认证c1自己的发布／CI。
