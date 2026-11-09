# AC4.3b：只读审查DAG运行

日期：2026-11-09。固定基线`e9b682c4be4f19aa11aca4717a7f6d86050278ed`；该合同文档已精确交付，同片独立对象/文档适用门禁与07:09:15.760037 UTC HTTPS远端终核通过。行为依据[已审端口合同](../plans/2026-11-09-review-dag-contract.md)。本片修后R2包、四条实际服务旅程及新旧history通过；自身首审补证后357.75秒复审approve，新独立最终Spec/Standards通过、RD-1关闭；本地门禁完成，普通交付及精确CI/远端待核。

## 本片合同与所有者

在原review阶段内，支持显式dag-v1协议的有界只读串并行与嵌套具名端口；不改原六阶段/批准/verify，不接写执行者。旧用户任务/正式信封/历史不隐式升级。新运行只在创建、版本Input、原Workflow/Executor、取消恢复/证据已一起接通后准入；保留全部必需/建议意见及原收据状态。完整祖先材料与前驱原产物不截断，超限提前拒绝。

现有编译器继续拥有唯一冻结图，原Input拥有路由，原Workflow拥有调度/取消，原Executor/FileAdapter拥有实际输入/原件核验，原evidence/handoff拥有读取。拟新增标准库端口算法仅由这些真实调用者共享，负责实例/依赖/投影的有界计算，不建第二调度/账本或通用插件层。

## 实施节点

|节点|实现与验收|状态|
|---|---|---|
|B1端口图|从既有静态图派生稳定叶子先后/具名端口共享表/完整传递汇合；混合嵌套、重复引用、共享join不指数展开、控制前驱意见覆盖|源码与R2安装包通过；独立最终Spec/Standards通过|
|B2版本准入|显式协议固定到原创建意图/正式v4与独立Input/queue/request-root，旧入口明确拒绝；无字段旧字节不变|R2安装包与额外3项原创建/裸run-memo恢复通过；旧history重放通过|
|B3实际执行|原Workflow按就绪依赖/祖先限额提交，原Executor核原请求/收据/claim/候选/SHA，完整前驱进入实际prompt/能力报告；无逐叶history查询|R2十一组259项通过，实际四旅程通过；RD-1源码复核通过，独立28条原链及126产物终核通过|
|B4恢复与容量|会话/并发/取消竞态/unknown对账、worker继续与原调用不重复；共享表及完整审计正文预算拒绝|R2容量/取消/恢复与真实worker停启、原ID对账通过；128个原PID/starttime采样零存活|
|B5最终交付|非editable身份/283冻结、实际CLI/Temporal/Supervisor/evidence/handoff、新旧history与清理、自身模板/全新独立两轴、普通推送自己的CI/远端|372/283身份、四旅程和九旧重放通过；自身补证复审approve、独立34文件终核通过；普通交付/精确CI及远端待核|

先在B1固定纯数据算法与高价值检查，再接真实消费者；不发布仅可声明但不能执行的公共v4。每节点完成后更新本记录及PLAN，最终测试/模型/独立/精确交付分开记录；R4及设计文档检查不当作本片证据。

## 源码阶段观察

新`review_dags`以原冻结实例和标准库TopologicalSorter求完成依赖，按稳定地址投影具名输入及共享join表；只算数据，不持久化图或调度状态。实际消费者为原信封形状准入、v4 Workflow与原Executor。所有祖先共享限额沿原review路径，叶子仍用原stage/job/monitor；初版将原v3意见读取下沉到FileAdapter方法，随后按RD-1修订到无SDK的共用reader，未建立另一可信意见解析器。

源码首轮B1检查因basetemp父目录未建立而未进入功能；建立后6通过/3测试夹具问题（资源来源实例本就不同、空join已被原schema拒绝、来源反例先触发终结覆盖），修正夹具后B1加原建议运行共**36 passed /73.72秒**。原始`b1.log`、`b1-r2.log`与修后`b2.log`留在`.ergora/checks/ac4-dag-runtime/`，它们不代替正在新增的正式端口旅程和最终包验证。

B3初轮**19 passed /6 failed /104.44秒**，六项原因为测试并行启动两个`reference.executor.main`触发原scanner单例锁。夹具改用scanner本来分派的原`process`处理函数，七组完整/篡改/容量用例**7 passed /85.43秒**；没有修改生产锁或另建执行器。原失败、修后执行器与无关慢分支检查分别在`b3.log`、`b3-executor-r2.log`、`b4-progress.log`。

## RD-1与安装候选

新独立实现评审确认RD-1：R1把所有版本的原FileAdapter构造替换为版本adapter factory，间接导入SDK Workflow，破坏旧v2/v3执行器的可选SDK布局；异常还会跳出原收据处理。两轴属于同一兼容缺陷，不当成两个bug。已将共用可信意见读取放入不依赖Temporal的`reference_review_opinions`，真正调用者为原活动与Executor；Executor沿原`WorkflowInput.request_root`选择请求目录，保持原FileAdapter。源码实际阻断SDK/Workflow重导入后，两旧版本的完整stage/终态收据检查**2 passed /23.99秒**；原R1包反例及修后新R2包/独立复核另记。

R1包源/wheel/非editable安装**371文件/283冻结**核验通过，wheel SHA`eecac8def4cf26c6130d1e0c0b143938c36e19b7d71e9a49c64a238b6bda63ac`。原v1/v2/v3九份history在该包重放通过。R1真实旅程因验收环境遗漏原native依赖a2a-sdk在启动服务时失败，尚未发送任务；保留失败与4个已观察原PID/starttime零存活/端口关闭。R2在新目录按原requirements.lock安装native依赖后再安装新Ergora包，不修改旧环境或冻结依赖；R1结果不能替代RD-1修正候选。

R1非editable十一组**257 passed /671.95秒**；新加的实际SDK阻断回归在同一R1包**2 failed /20.29秒**，明确复现RD-1。R2源/wheel/安装**372文件/283冻结**一致，wheel SHA`1d266efb0329f267383ba3abc295c7bf6421f1c3a8012a2d220dd7dae05a629b`；新非editable全部十一组及四条服务旅程在跑。额外R2公开创建/原意图协议固定、无memo裸run拒绝、有原memo恢复且不再start的**3 passed /24.50秒**；这些用例在十一组收集后新增，结果分别记账，不合称同轮全部通过。R2首条实际服务旅程已完成，包括worker停启、一个原advisory FAILED前驱及两个后继、8原job、新history及离线handoff；余三条与清理待完成。真实自身模板已按用户授权用Codex/task-mcp开始，尚无模型审查结论。

## R2安装包及实际服务验收

[最终R2包身份与分段测试](evidence/2026-11-09-ac4-dag-package-r2.json)：十一组 **259 passed /0 failed /0 skipped /604.60秒**，包含RD-1两条实际旧版本Executor无SDK回归。后来增加的原创建协议与裸run-memo恢复 **3 passed /24.50秒** 单独记账；不把它们合称同轮262项通过。R2完整源/wheel/非editable安装372文件一致，283冻结保持，原R1两红与失败日志仍保留。

独立复核发现原架构门禁尚未登记新基础依赖及原生reader所有者，原测试在R2安装包独立执行 **2 failed /8 passed /0.88秒**。仅同步原检查的明确所有权：`task_envelopes`只可依赖`review_dags`，二者外部导入仍仅标准库；`reference_review_opinions`加入允许访问原生适配器的所有者集合。没有放开任意应用依赖、删除层级/无环检查或修改生产包。修后同一R2安装包 **11 passed /0.20秒**。

[四条全新公开CLI/Supervisor/Temporal/scanner旅程](evidence/2026-11-09-ac4-dag-journey-r2.json) **464.97秒通过**：

- 串行建议前驱request-changes：结构子模板的原收据FAILED，原意见和全部产物完整进入正确性/测试价值两个后继；三个独立会话、八个原job最终REVIEW_READY。前驱活动期间只停worker，executor仍发布原收据；原前六请求保持，worker恢复后仅原三个Agent调用，无重派。
- 必需后继request-changes：三个review均执行，原必需收据FAILED，结果BLOCKED，未伪造通过汇合。
- 前驱进程故障：原收据FAILED，没有可信意见，不启动两个后继，结果BLOCKED。
- 前驱活动时公开cancel：原收据CANCELLED、两个后继均未启动；保留CANCEL_UNCONFIRMED，原ID显式对账确认无未决/意外job后释放claim，不改写原outcome。

四份完整v4 history分别195/201/167/162事件，全部SDK重放通过；四份原证据索引与离线handoff均核验通过。正常shutdown后三服务端口关闭，128个原PID/starttime与递归后代采样零存活；采样不保证捕获每个短命进程。[九份旧v1/v2/v3完整history](evidence/2026-11-09-ac4-dag-legacy-replay-r2.json)也在R2包重放通过，未重建原输入或更新旧历史。

## 自身模板首审与补证复审

Codex `gpt-6.1-sol`/high通过本版structure-review/task-mcp运行 **283.54秒 /succeeded /CLI exit0 /request-changes**；[原结果](evidence/2026-11-09-ac4-dag-self-review-r1-result.json)及[25份完整源码/输入身份](evidence/2026-11-09-ac4-dag-self-review-r1-identity.json)保持。附件403,690字节；结果没有确认新源码缺陷，要求补齐当时尚在运行的R2验收，以及未提供的schema、原submission/memo/evidence/handoff所有者。它确认RD-1修正的依赖方向，另建议复用Workflow已派生DAG、对完整构造与调度测量后再作性能结论；该建议明确非阻塞，当前没有加速声明或新增缓存/第二份状态。

补证复审保留同一生产包，增加上述完整所有者、原架构门禁登记、真实验收脚本/结果、分段测试与清理范围，冻结后用自身模板重新调用。精确提交、自己的CI与HTTPS远端仍是提交后的独立交付门禁，不预先当作已通过；实际模型结果与同片独立完整范围终核另记。Claude上游400已在前片有界调查，按用户授权使用Codex回退，不反复登录，也不声称模型错误独立。

## 自身补证复审通过与本地收口

同一R2生产包上的Codex structure-review/task-mcp复审run `60a9d429f6bb48d1a4c1dbacbab1fc74` **357.75秒 /succeeded /CLI exit0 /approve**。[37份源码与精确输入](evidence/2026-11-09-ac4-dag-self-review-r2-identity.json)及[原模型结果](evidence/2026-11-09-ac4-dag-self-review-r2-result.json)保持，附件587,523字节、SHA `8de8b9851b2f98a58d28167708786f12e7e71a56e63c38a29b2bdc2f1f3dcbb4`。它确认前次所有者及运行验收缺口已补，无新增阻塞源码finding；保留非阻塞的重复派生DAG测量建议，没有以“建议已修”冒称改变本候选。

[实际native流分页核验](evidence/2026-11-09-ac4-dag-self-review-read-audit.json)分别核首审13页/403,690字节及复审19页/587,523字节，连续至`next_offset=null`，重组原附件字节/摘要匹配，37份源码仍一致。两次各有一个错误URI请求，随后正确完整读取，原失败留在原流。模型没有运行本片测试或证明模型质量、独立模型错误、OS隔离或完整活动进程崩溃恢复。独立者另核包二进制与原件链，不以模型对供给摘要的阅读替代该项核验。

最终完整范围、静态链接/CLI parser、同片独立终核与普通提交后自己的CI/明确HTTPS远端分别登记；下一片先明确写执行者的原工作单元/单checkout写所有者及能力合同，再注册真实支持的新版本，避免将当前只读`run-input`冒充写执行入口。


同片[新独立最终审查](2026-11-09-review-dag-runtime-review.md)完成全部34文件、8公开JSON、37模型源码及原请求/回执/claim/产物/实际输入终核，**Spec与Standards通过，RD-1关闭，零剩余本地阻塞**。性能建议保留为后续有实际规模数据时再评估的事项；本片未新增缓存、依赖、CI作业或调度/账本。普通提交与自己的双OS CI/明确HTTPS即时远端SHA是剩余交付门禁，不能引用前片CI替代。
