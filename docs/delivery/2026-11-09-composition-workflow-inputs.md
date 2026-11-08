# AC3c.3 / CR1：版本化Temporal输入与六阶段继承

日期：2026-11-09。状态：WI1–3已实现并验证；R4源码/安装包各91项、双版本SDK及四类坏输入永久拒绝通过，自身模板真实审查approve，新独立最终复核与精确交付待完成。基线e9c3484fbfa0cfb8cf0737c4d930b5ec176992d3。前片AC3c.2已获双OS CI42529979473及22:35:26 UTC独立远端终结，本片不能把前片包365身份视为新片验证。

本片只实现新版Workflow入口和原始输入/投影适配；正式v2 start/status拒绝保持，worker/批准/真实executor留CR2/3。新增reference_workflows在原reference边界拥有WorkflowInput ABC及局部两版本映射；LegacyInput和CompositionInput通过同一entrypoint/start interface交付原始payload。VerifiedSpecClient从原始单payload核完整JSON身份，核准后才向原DevelopmentTransport返回legacy投影；新start也由同一输入合同选择入口，不能先解包丢弃组合身份。

CompositionDevelopmentWorkflow继承原DevelopmentWorkflow的六阶段、工作单元、批准、signals/fence与结果；只增加明确类型、完整v2输入核验、stage context/admission和状态/结果摘要。每次加入完整信封后再核原1,000,000字节上限，不静默截断。不是新调度器，未重新实现原六阶段。新增ABC有两种实际输入变化，并由原runtime client及新workflow实际消费；两个实现的注册留所属模块，不按厂商分派。

- [x] WI1：原始输入/投影共有合同、显式新Workflow，旧入口兼容及原始JSON身份/容量检查。
- [x] WI2：SDK注册/信号继承、原有runtime/单payload/提交定向回归、非editable包及365→366资源与283冻结身份。
- [x] WI3：本地真实Temporal与明确合成控制活动，核原始payload/每阶段context/计划等待及继承信号、旧新两类型；不能当完整真实Agent/可信候选验收。
- [ ] WI4：新fresh-context独立结构/需求审查、Ergora自身模板真实审查，精确普通提交/必要CI及远端终结；前片CI先完成，再推下一候选。

实际完整v2正式批准/执行仍在[父计划](2026-11-09-composition-runtime.md)CR2/3，原verify写legacy spec路径的问题必须解决后才开放。没有修改冻结参考或增加新的服务/依赖。

WI1源码定向：版本输入9例及原payload/runtime/架构四套共50 passed（31.90秒、零skip）。已验证原始单payload与匹配legacy但不同admission拒绝、继承query/signal、每六阶段context携完整信封和实际上下文容量拒绝；这里只是离线调用与SDK元数据，不冒称worker已跑。原提交/批准/旧组合拒绝的受影响源码回归在途，下一非editable包及本地Temporal。

WI2初版包50 passed（29.91秒）、366源/wheel/安装一致、283冻结不变，wheel7f84…；WI3初版真实Temporal1.9.1/Server1.32.0与SDK worker13.38秒完成旧新各六阶段、计划等待/信号、原始payload/全部stage context、两种相同legacy不同输入拒绝及完整历史重放，服务已停止。这是明确合成外部回执，不是真实Agent/owner/candidate验收。随后检查旧worker/executor边界：为阻止旧worker把组合请求误派入原单Agent队列，新增版本专用ergora_composition_submit活动名，CR2将由新worker实现独立请求命名空间并接相应读取/执行所有者；公开v2仍拒绝。首版结果不作为此协议细化后的验证，R2待验。

补充：原提交/批准/旧组合拒绝三套源码回归106 passed（409.25秒，零skip）。R2新wheel `4bb71770bf06d80ed279555462cc3e8a9fc62c1da14d710ed65d696e7dbdd8b8`的366源/包/非editable安装与283冻结身份一致。第一次R2回归命令误拼不存在的suite，exit4/零收集已保留为collection-error，纠正为原`test_original_payloads.py`后重跑中，不记前次通过。R2 SDK旅程使用新的专用submit活动，并核两种类型各自完整历史；旧R1实验v2 history不作为新协议重放证据。

R2最终四套安装包50 passed（30.30秒，零skip）；真实SDK/Temporal旅程13.87秒通过：旧入口仍用dev_submit，新入口只用ergora_composition_submit，原始完整单payload、每阶段admission、计划等待/继承signal、两类相同投影错误输入拒绝、各自完整history重放与terminal查询均核过。服务finally退出且loopback端口关闭。证据在忽略的`.ergora/checks/ac3c3-runtime/r2/`：package-identities.json、wheel-regression.log、sdk-journey.json及两history。性能仅为该本地合成协议旅程用时，不代表模型/生产吞吐。下一新的独立两轴与真实模板审查，不更改受审源码直到调用终结。

R2自身真实structure-review/任务MCP 128.73秒返回request-changes，完整48,482字节附件读取；提出畸形数值实例路径在`task_envelopes.unwrap`触发AttributeError，不能转换为不可重试ContractViolation。新的独立者在原R2安装包复现并登记CR1-SP1。原包上numeric-path/duplicate-path/null-document三项新合同均红，原回执/红例保留。现已在信封所有者核顶层对象、非空字符串与唯一路径，不增加宽泛异常吞没或复制图权限验证；R3源码/新包/SDK及真实自身再审待完成。Standards的P3也采纳：可选Temporal跳过前移到测试模块收集处，避免无SDK先建立九套项目/静态包夹具。该测试效率改动不改变生产合同。

R3源码/安装包五套各90 passed（44.95/47.47秒、零skip），366/283身份及12.02秒真实双版本SDK/重放通过；另8.31秒真实SDK坏输入旅程从三份原history核出不可重试ContractViolation/零活动，独立者已核。R3 wheel为845dde7fbc2d389558c55420f1c2e4c7d02c5e65618f5a725fc6a8891ff05b5a。R3真实自身审查153.57秒再次request-changes，提出小体积深嵌套graph JSON会触发RecursionError逃过永久拒绝；独立者在原R3复现CR1-SP2，新增10,000层/20,001字节graph的旧包红例。现只在信封graph解码处把此RecursionError转换为ValueError，不吞没任意异常；R4发行/SDK/自身与独立复核待验。SP1/ST1的原修复证据与SP2分开保留。

R4最终：五套源码91 passed（46.31秒）及同五套非editable安装包91 passed（48.01秒），均零skip。wheel `bfd98f933ba6622ca6d9d4caf6705174f1ec706a5fcf552a474c6d58daf105bb`的366源/包/安装与283冻结身份一致。实际双版本六阶段/信号/全部context/两种碰撞拒绝/各自重放12.55秒通过；另四类坏输入SDK旅程7.48秒，各以ContractViolation/non_retryable终结、零活动。两专用服务均已停，未接真实Agent/owner/candidate的边界不变。受影响五套包含完整正式组合创建/恢复，不以106项旧源码回归冒充修后重跑。

R4真实自身structure-review＋任务MCP 132.03秒approve，完整读取50,938字节受保护附件，保护源码、完整prompt/输入、DB/result身份已由调用脚本核对。公开保存[最终身份](evidence/2026-11-09-cr1-self-review-identity.json)、[原始结果](evidence/2026-11-09-cr1-self-review-result.json)及[R2–4完整判定历史](evidence/2026-11-09-cr1-self-review-history.json)；R2/R3的request-changes保持。最终fresh-context审查仍须独立核这些原始交付证据与修正，不能以此approve替代。

新的[独立最终本地审查](2026-11-09-composition-workflow-inputs-review.md)通过：Standards/Spec无未解决finding，ST1/SP1/SP2均关闭；实际R4包/原history/全部真实MCP读取、完整输入/prompt/DB/result与公开三份原始证明分别核实。14文件精确交付、必要双OS CI及即时远端仍待完成；WI4先完成本地审查，不预勾整个交付。
