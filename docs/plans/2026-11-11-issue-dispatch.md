# F7b.1：来源冻结与正式入口的窄准入

基线`3c4ef3928fe756bf596fd1da1cc80c7eb1e6578d`，分支`refactor/architecture-foundations`。承接[F7b.0快照与显式上下文关联](2026-11-11-issue-mapping.md)和[F7总分片](2026-11-11-project-trackers.md)。B0自己的精确CI42982197290七必要步骤及原评审终核已通过。B1b来源合同／离线发布和材料路径已精确交付4638c3b；自己的CI42995785084与同片独立终核通过，6558671原失败保持。[B1c窄准入](2026-11-11-source-task-admission.md)实现和实际运行验收另行进行。

## 结果与边界

操作者可以选择一份已保存的精确工单快照，为本项目明确预览／创建一个新任务；新合同保留完整来源身份及正文，并向实际工作／审查实例提供该冻结上下文。正式start复用原项目policy、可信检查、工单占用、提交意图、attempt-before-send、原workflow/run与memo核验，不要求未选择的A2A、MLflow或其他无关服务。离线预览和读取不要求tracker当前在线；正式执行仍要求所选Agent与执行服务实际可用。

工单文本仍无授权能力，来源更新也不改写旧任务／批准。B0的operator_asserted_context关系保持原义，不自动升级为正式来源准入，也不声称运行Agent已读。旧任务输入v1–v6、creation v1／v2、283冻结发行、原入口doctor及租约行为保持可读／可恢复。暂不接收webhook／轮询，不回写远端，不新建调度器／占用库；F7c／F7d分别负责这些真实消费者。

## 已核真实调用与限制

|所有者|当前事实／新片约束|
|---|---|
|[tasks](../../src/ergora/tasks.py)|`_definition`校验定义v1／v2，preview／create调用原task_creation；create已有项目写保留。来源选择应在这里组合，不让CLI／HTTP复制厂商逻辑。|
|[reference_task_creation](../../src/ergora/reference_task_creation.py)|原creation明确只支持v1／v2，恰好七份native文件、每份1MiB／总intent16MiB；编译／校验绑定原compiled与spec。增加来源必须显式版本化，不能在旧记录偷偷增加文件、降低核验或覆写旧intent。|
|[task_envelopes](../../src/ergora/task_envelopes.py)、[reference_inputs](../../src/ergora/reference_inputs.py)|既有composition envelope v2–v6；WorkflowInput ABC与本族注册表拥有工作流类型／queue／request根／activity／adapter及原始输入传输。优先在该Interface扩展真实版本，transport与上层不再另建版本分派表。native桥的纯读取路径当前只依赖标准库，不随意增加隐式SDK／验证依赖。|
|[reference_workflows](../../src/ergora/reference_workflows.py)|v6复用原六阶段与named-source产物协议，不递归复制先前prompt／产物。新来源必须实际交付且保持该材料增长约束，不能只在数据库留下“已关联”。|
|[reference_task_submission](../../src/ergora/reference_task_submission.py)|专用进程沿原task_action并包装spec／transport，拥有lookup-before-start、attempt-before-send、原输入SHA／memo、冲突和unknown恢复。新入口仍用该所有者，不另写start／重试状态机。|
|[冻结native cli](../../src/ergora/data/reference/platform/local/agent_platform/cli.py)|start原顺序为doctor、task type／可信checks、connect、claim和start。原doctor包含A2A／MLflow等整套依赖；仅新显式入口需要窄准入，旧入口语义保持，不全局把report改成ready。|
|[原ingress](../../src/ergora/data/reference/platform/upstream/platform/dev_platform/ingress.py)|只接受kind／project／issue_id，namespace casefold，相同namespace跨host保守共享claim。新来源必须保存完整API身份，但不能新建host-specific占用库以绕开旧入口；在兼容演进前继续保留此保守碰撞。|
|[issues](../../src/ergora/issues.py)|B0快照有完整观察／当次绑定与内容SHA，正文可离线读取。新任务选择snapshot SHA，不从当前head或链接推断冻结来源。|

## B1a：先选合同与Interface

至少比较以下两种具体方案，选型写入本文件及交付记录后才改实现：

- 新版本WorkflowInput／任务定义，直接复用最新v6执行与原恢复所有者，把完整来源及实际交付方式纳入新输入身份。优点是原输入、SDK执行与材料同一精确合同；代价是必须注册新版本worker／queue／request根，并保持旧replay兼容。首片是否只支持work-units-v2组合，需要由真实调用路径及默认模板旅程决定，不能隐式替旧任务升级。
- 新版本creation保存完整来源，显式委托原inner执行输入。优点是可减少执行图变化；必须证明来源确实进入原输入／阶段材料、原memo和证据校验，且窄准入有明确版本入口。若只能在旧constraints塞文本、或凭可伪造的marker跳过doctor，该方案不成立。

当前倾向让显式新输入版本拥有来源与准入，最终决定须以调用／恢复／材料预算验证为据。不预先承诺新版本号，不为未来所有wrapper建立插件框架。选择不同工具仍通过各自已有Adapter；版本差异在其本族Interface内，不把GitHub／GitLab分支扩散到任务、transport或模板。

### B1a选型与第一实现片

独立fresh-context设计者核实际调用后推荐第一方案，已采纳：task-definition v3增加`source: {snapshot_sha256}`，保留原数字`issue_id`和业务input；creation v3仍恰好七份native文件、正文只保存到task.spec的新v7 envelope的`issue_source`中。v7继承v6的work-units-v2、named-source材料与同一六阶段，新增合法Input／Adapter／Workflow及自身queue／request根，全部旧版本保留。来源合同与默认API解析归纯标准库`issue_sources`，由快照读取、tracker及envelope共同消费；不在native纯读取路径引入jsonschema或SDK，不再复制快照runtime校验和默认URL表。

来源与本项目已冻结执行配置比较provider／完整API base／namespace及local issue_id；完整snapshot SHA保留native ID与正文。登记只提供provider／namespace，其无host格式不充当API来源证据。允许同来源的历史快照用于新修订；原观察配置修订和本次执行配置修订分别保存，无关Agent编辑不强迫重新抓工单。

B1b实现完整输入和材料路径，保留原广doctor；验收结论限离线preview／create／恢复及材料合同，不提前声称窄依赖准入或实际Agent消费。B1c再在已核精确creation的专用提交进程内按新Input提供实际依赖预检，继续调用原task_action与同一claim／attempt／memo；不为分片加入临时offline registry、占位workflow_type或将来要删除的start开关。[独立设计报告](2026-11-11-issue-dispatch-design-review.md)作为选型证据保留，实际实现仍须新的完整评审。

B1a验收需要回答：新定义／creation／input具体字段和版本，来源如何绑定legacy tracker与登记项目，哪些检查只对新入口适用，所有原始身份和阶段材料如何穿过现有读取／提交／证据／handoff所有者。给出完整调用图与增改文件清单，核旧v1–v6和其他入口保持，不仅是schema通过；用新的fresh-context独立设计评审核可达绕过／恢复窗口。

## 来源与材料规则

1. 固定完整快照及其canonical SHA：provider、完整API base、namespace、number／iid、native ID、完整正文、原响应SHA／ETag／updated_at、原项目／配置修订与绑定引用。HTTP原body未保存，不能声称可重建原响应。源码来源／读取时间和当前执行配置修订分别表示。
2. 操作者明确当前项目revision、所选快照与任务目标，再走原preview SHA确认。至少校验来源provider／API／namespace与本项目预期来源、local issue_id与原native tracker；跨host或源切换不得靠旧hostless登记自动通过。是否允许旧配置修订的同来源快照，应按来源身份而非无关Agent设置变化决定，并有反例。
3. 所选快照在离线编译时已完整可用，不以当前token有值或tracker可达代替它的身份；后续远端写入是另一权限和恢复合同。标签、正文、链接、ETag和updated_at均不能提升权限、修改可信检查或替代owner批准。
4. 将完整来源纳入新不可变创建／执行身份，并实际交付给需要的工作／审查实例。沿原输入／context／固定资料所有者读取，保留所有祖先Skill／上下文与父级权限；不为工单内容扩张MCP／shell／文件能力。核真实原输入、Agent范围与读取原件，不从标题或link推断已消费。
5. 不改变原1MiB文件／intent、prompt、固定材料预算来让样例通过。捕获成功不代表一定可执行：与manifest／任务材料合计超限时，在发布／start之前明确拒绝，无截断、隐式摘要或重复递归携带。来源大正文、UTF8边界及恰好预算附近须有实际反例。

## 分片与验收

|节点|范围与验收|状态|
|---|---|---|
|B1a 合同／准入设计|比较上面两方案，选共享Interface和来源材料路径；保留原claim兼容、全部旧版本读取／恢复，新的独立设计评审|已选definition3／creation3／input7，独立设计审查完成；预算／交接细节见下文|
|B1b 来源任务离线发布|显式snapshot→preview→create／resume；完整来源冻结／新task ID、重复／丢响应／绑定编辑与发布冲突；原文件及批准保持，未start；新安装包和实际CLI／HTTP旅程|最终r3包444／两RECORD／283、受影响28及实际CLI／HTTP15检查通过；自身首审／聚焦复核均approve／全部scope完整读取；完整32文件独立两轴开放0／0、两P2／一P3关闭，本地出口通过，精确交付继续，start仍原广doctor|
|B1c 窄入口与原运行恢复|仅新显式入口按实际所选能力检查运行依赖，沿原policy／checks／connect／claim；实际原ID start／未知恢复及旧入口竞争，六阶段与精确owner／candidate保持|待B1b；无权限的范围按原规则记录，不要求宿主权限|
|B1d 完整交付|Ergora真实审查模板、完整祖先读取、新fresh-context完整两轴；受影响检查、安装／文档／普通推送、精确Git／远端及自己的必要CI|逐完整实现片执行，不借设计报告提前关闭|

必须覆盖的真实错误：错host／namespace／local ID／native ID，编辑snapshot／输入SHA，来源切换与无关绑定修订，删除token后的离线预览，工单更新保留旧创建／批准；不需要的A2A／MLflow缺失可用且实际必需Agent／runtime缺失明确拒绝；与原入口同一claim的竞争、lookup与start冲突、attempt后丢响应、原memo不匹配；完整资料交付／预算拒绝和旧v1–v6读回／恢复。复用原测试夹具与调度／进程monitor，不新增同构CI或为了证明普通异常而堆测试。

B0的精确提交／CI状态以其[计划](2026-11-11-issue-mapping.md)和[交付记录](../delivery/2026-11-11-issue-mapping.md)为准。每节点完成后更新本计划、所属交付记录及[PLAN](../PLAN.md)，新实现片另固定自己的基线／证据／审查范围。项目整体、F7c／d与F8–F10／G1仍未完成。

## B1b CI后的依赖修正

6558671已普通推送，自己的42991272992 Windows architecture回归失败；原CI保留，不关闭精确交付。新增issue_snapshots仅集中原SQL读取／row重建／digest校验，实际供issues与tasks消费，issues继续拥有observe／capture／link，不再task／issues互相导入。首inventory context逐字段迁至纯task_envelopes、creation与v7 workflow直接复用；Input与workflow不反向导入。handoff直接unwrap完整原输入及来源合同，仅v7取issue_source并绑定冻结selection，旧v1–v6不因任意附加字段改变语义。基础依赖表增加纯issue_sources和标准库约束，继续禁止运行层依赖／导入环。原12项source架构修后通过，安装r4及同片独立复核待结果；不借原r3／模型结论证明修后源码。

依赖修正最终r4：445包／两RECORD／283冻结、安装125／209.38秒、真实离线旅程15／11.08秒通过；自身12附件177571B／161.00秒approve、五scope连续读取和所属采样清理已核。完整20文件同片独立终核两轴开放0／0、ST3关闭，本地修正出口通过；新修正提交／远端／自己的CI仍须另核，原6558671双OS失败保持，不自动关闭B1c。

修正4638c3b已精确20Git／ready、445包／283冻结、普通推送及独立SSH Ref同完整SHA通过；自己的CI42995785084第三官方run原HTML Success、Linux三／Windows四必要步骤与原评审七组原件终核通过，B1b精确交付终结。原655／429912失败、REST403、lazy matrix／navigation404和非终态样本保持；不将HTML终核称成功REST或完整日志，B1c仍单独验收。
