# Q4.2b1 前置阻断：计划与交付记录

日期：2026-11-15。以[具体计划](../plans/2026-11-15-training-start-fence.md)为准。修订合同已通过独立计划评审，当前处于实现和验证，未发布。

已核原取消入口要求start回执／run ID；最后preflight后仍可能有晚到start RPC；原本地adapter在同一registry锁下拥有完整binding的fence／lookup和拒绝future create。本片先接入这项原阻断能力，明确与Temporal取消／实际executor停止分开。原导入链需要Temporal SDK，但本地fence不连接服务；将来实际依赖以安装旅程确认。

|步骤|状态|
|---|---|
|实施前合同|r2新fresh-context需求／维护两轴approve、开放设计项0／0；R1／R2设计关闭，初版结论和全文保留，见[原报告](2026-11-15-training-start-fence-plan-review.md)|
|源码／安装／运行|初版CLI／应用／原submission进程已接入；实施基线固定a2已普通发布1b58e929aaf495c16f448454c78de23718786ae9。源码定向运行中，安装／实现审查待；a2自己的CI／原终核待，终核前不推后继产品|
|后继义务|注册漂移后恢复、原授权归属、不可续期预算、完整executor、Temporal双向容量及CPU循环仍开放；本片不关闭它们|

本片文档与a2产品交付分开管理，不混入a2已冻结的模型输入或源码验收。验收原件写入ignored持久目录`.ergora/checks/training-start-fence/`。当前未调用模型、真实训练、资源平台或业务项目；Kernel专家及283参考保持。

## 初版接入与验收范围

复用原`training._setup`的项目revision预留和原`reference.training_submission`进程，新增薄`fence-start`CLI。原`_Submission`从冻结intent或原records核完整Experiment，明确确认manifest；mutation前核原registry lock／job request／fence路径，再调用固定本地factory的原`fence_and_lookup`。没有新表、文件writer、锁协议或scheduler；不等待跨RPC的原submission lock，不调用`core.environment()`。

返回本地fence原路径／完整字节SHA、锁内job和观察到的submission状态；runtime未查询、执行／停止均未确认。已有匹配fence允许终态后读回，首次观察到submitted／rejected时拒绝新增；错误／外层进程超时明确保留“可能已阻断”。用户手册增加命令、实际release效果和恢复方式。

新增验证留在已有submission／release suite和原SDK服务fixture：无intent／prepared／unknown、错确认／依赖／身份／symlink、status读后完成、跨进程最后preflight后的在途RPC与丢fence回复、真实native create／lookup及ticket两种顺序、未选中成功实验保持。`source-fence-r1`源码运行中；它是原native owner＋SDK服务替身的合同验收，不是真实Temporal、训练或资源停止证明。正式安装、原回归、自身模板和新独立实现审查尚待。

## 源码与隔离安装进度

原`source-fence-r1`为14通过／4失败，pytest78.11秒。三个symlink由原`safe_file`报`Path escapes trusted root`拒绝，新测试误匹配其他错误文案；完整Experiment冲突由原adapter在新建空`registry.lock`后拒绝，新测试误要求连这个正常锁文件也不能新增。仅修测试预期，不修改产品以迁就测试；原失败XML／日志保留。

修后`source-fence-r2`为18通过／45未选，pytest74.48秒，外层75.36秒。包含真实原registry的两种create顺序、跨进程hold在最后preflight之后的SDK start、fence回复丢失后迟到receipt与幂等读回，以及原native release票据两顺序；服务交互为SDK替身，不是真实Temporal运行。

新r1非editable wheel分别安装到core／SDK环境，`package-r1-core`／`package-r1-sdk`核645源／wheel／真实site-packages逐字一致，283参考PASS；core无SDK、SDK1.34.0，两环境依赖检查通过。相对1b58e92仅修改CLI、training、reference及原submission四产品文件，无新增产品模块、参考或持久格式。安装七原training suite与无服务实际CLI旅程运行中；新独立reviewer已核源码，最终两轴及自身模板仍待。

## 自身审查发现与r2修正

自身原`ergora-structure-review`实际run`0e8cb84ea9f4456bb3d79d6c6156d670`，22完整文件437,442B、完整diff及三祖先资源进入实际stdin，51.963秒，`request-changes`。R1：冻结intent分支不经原records，原native lookup虽核完整Experiment，却直接把未验证的request.job_id放进Job，导致匹配spec但job_id为null／其他实验ID时可写fence并成功回传损坏身份。新独立reviewer已按原源码确认该P2；原r1静态approve不覆盖这一后发现问题。

在原身份冲突接缝补一个job-id变体，旧r1安装`installed-job-id-red-r1`实红一失败／2.83秒：未按合同拒绝，原fence已创建。当前仅在原submission的frozen分支，沿已有document读取可有request并核原`local-perf-<experiment>`ID；完整Experiment仍由原registry锁内lookup核对，不依赖当前spec／runner、不改283参考。源码定向绿、重新安装／原回归、自身复审与独立R1处置待；r1通过结果不转授修后r2。

原实际CLI旅程`native-journey-r1`六命令符合预期，但私有驱动末尾误以为原prepare没有创建registry.lock，最终额外文件断言失败；原日志和前后库存保持。`native-journey-r2`用新项目纠正驱动后六CLI通过／15.385秒：core缺SDK和缺confirm拒绝，SDK无服务本地fence／重复读回／本地submission／拒绝后续start-check符合合同；48原文件和DB保持，仅新增所选fence，未解析特意放置的非法credentials。它仍只认证r1产品；最终r2须重新实跑。

## r2当前证据

- R1修后源码`source-job-id-green-r2`一通过／2.76秒；完整Experiment冲突、冻结spec／runner删除和幂等语义继续沿原接缝，最终安装回归在途。
- 新r2 wheel SHA`58760d22a34f3c6dea95c8cce08814f8c79f56a83e68c55fd659859cbc2598c5`。core／SDK两新非editable安装各645源／wheel／实际site-packages逐字一致，283参考PASS，两环境依赖检查通过。r1安装保留，不被覆盖。
- `native-journey-r3`用r2安装从原公开owner重新准备双合成合同，实际六CLI通过／16.689秒；48原文件及DB保持，仅新增所选fence，未选中实验无fence、没有start intent／服务／模型／runner调用。core缺SDK与缺confirm拒绝发生在新增fence前；非法credentials未被解析。
- 自身原结构模板r2实际run`169339e442f64a379f296a910a856b59`，35.450秒、succeeded／approve；22完整文件440,004B、完整diff及三祖先资源进入实际stdin。它复核R1修正与结构，不认证未提供的运行原件或CI。原r1 request-changes／结果保持。
- 原release接缝补充在alpha被fence后实际调用原beta release owner，验证未选中成功实验仍能创建自己的本地票据，同时alpha原票据保持；最终安装七suite将验证该场景。

新独立reviewer已直接核r2产品／两安装及CLI／自身原件身份；完整本地两轴与R1关闭待最终安装七suite，不提前宣称发布或自己的CI通过。

原r1安装七suite已结束：130通过、pytest667.42秒／外层668.596秒，一次既有TestClient弃用提示，无失败／跳过。这只认证先前r1代码及当时测试集，不包含后补R1 job-id回归和beta实际release；修后r2完整安装回归仍运行中。

## 最终安装验收

修后`installed-tests-r2`七原training suite已**131通过**，pytest674.59秒／外层675.816秒，无失败／跳过，一次既有TestClient弃用提示；由r2 SDK安装解释器以`-I -B -m pytest`运行，从真实site-packages导入。包含修后job-ID拒绝、全部原lost-ack／取消／准备／证据／release，以及alpha阻断后beta真实native release票据接缝。没有新增suite或CI job。

r2两安装645逐字／283、六真实CLI／48原文件及DB、源回归红绿和自身复审approve均已记录，十一文档249本地文件链接无缺失、`git diff --check`通过。原r1四个测试预期失败、私有旅程断言失败、结构审查R1与旧安装实红均保留。原独立reviewer接最终本地终核；本片普通发布和自己的CI尚待，未以a2的终态替代。

前片a2的CI43647584681／attempt1现八job／30必要步骤全成功，原独立终核两轴approve／开放0／0，前置发布门禁已闭合。本片通过自身最终本地审查后可普通推送当前开发分支，不合main。后继b2仅计划，已独立审查；原登记恢复、预算／全周期停止及自动循环仍未实现。

## 独立最终本地终核

新fresh-context reviewer已追加[最终报告](2026-11-15-training-start-fence-review.md)：需求／可维护性两轴approve，R1关闭，开放0／0。直接核131项安装XML、185原件及完整SHA、645源／wheel／两安装身份、实际CLI／自身原结果和暂存后完整差异。原22,307B报告SHA`ec25d275795152beefd05f860c7bc87170105e224bafac457e0d46a0b046a2bb`；原失败保持。该结论只覆盖本片本地，普通发布／自己的CI另核；b2实施前计划另归自己的独立审查。
