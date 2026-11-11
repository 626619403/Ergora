# F7c-C3a：候选与远端分支的只读核对

基线 `93b538fd474120fa05574dcdcf376b7666502c8d`，分支 `refactor/architecture-foundations`。第一方依据见[候选发布研究](../research/2026-11-11-candidate-publication.md)。接续[C2a标签](2026-11-11-issue-label-writeback.md)与[逐项目工单计划](2026-11-11-project-trackers.md)。立片时C2a自己的CI43023048173仍在运行，现已由原评审终核双OS七必要步骤，93b538f精确交付终结；其通过不替代本片。

## 行为与范围

给定原已发布v7来源任务、原run、完整候选SHA及显式远端base分支，读取原export收据、当前本地导出ref和候选／base commit，再用当前绑定的GitHub／GitLab读取仓库及两条精确分支。head分支固定为原export分支。分别比较远端head与候选、远端base与原冻结base、本地ref与候选。返回每个事实的来源、读取时间、完整SHA与覆盖限制；不输出可推送／已批准／已发布的综合授权判断。

这是当前观察，不是服务端事务或CAS，不能发现两次读取之间的ABA，也不能证明原export之后没有改动。404仅表示未找到或不可见，不证明远端分支不存在；认证、限流、redirect、部分／超限返回及错误目标须可见失败。不得根据404自动创建。未见或不可见的ref令相应比较为null，不能按相等处理。

本片只读，无新表／正式账本／State版本，无fetch／push／ref写入、PR／MR创建、标签／评论写入、close／merge或自动重试。原candidate、approval、claim和attempt-before-send保持。普通push的fast-forward语义不能保证竞速出现的人工ref不被改写；带force名字的选项不作为本片替代。后续发布须另立可验证合同，显式既有PR／MR关联也单独验收。

GitLab标签的固定版本研究已补足schema，但路由目标和scoped rename无原子条件；当前严格追加能力继续unsupported，不将其研究完成记成标签实现完成。

## Module所有权与实际消费者

- 原`tasks`拥有来源creation／snapshot／export绑定。将C1私有候选校验移至此owner，供`issue_writebacks`与`issues`两个真实生产文件共用，C1 intent／digest／记录字节不变，避免复制绑定规则。
- 原`reference_task_export`拥有本地Git读，增加只读inspect操作，复用已有原任务／export记录和Git进程清理；inspect保守要求已验证的Git>=2.43，强制禁lazy fetch及对象replacement，旧显式export fetch保持；`tasks`通过原reference Interface调用，不由HTTP或工单层直接操作Git。
- 原`IssueBackend`本族增加一个repository/ref读取Interface；GH／GL各自拥有路径、原生字段、精确目标映射和404语义。上层只调用同一Interface，无provider分派；共用原有界HTTP，无SDK依赖。
- 新观察用例留在原`issues`观察owner，CLI与受保护HTTP共同调用；不新建通用远程操作层。配置只登记真实新增operation，无新增用户必配服务。

## 可验收节点

|节点|出口|状态|
|---|---|---|
|O0 第一方研究与设计|Git普通push／远端ref及平台身份的真实合同；明确只读最小片、竞态与未验范围|完成；12次无凭据GET及设计已记录|
|O1 原所有者与协议|共用source-candidate验证；原export只读Git；GH／GL同一Interface，精确ref与opaque分支名|已实现；SP1／SP2已独立关闭；自身首审SP3真实red后最小修正，r3新包及受影响18项、完整独立通过，SP1–SP3关闭|
|O2 CLI／HTTP与故障旅程|一致／漂移／不可见、错误native目标／ref、认证／限流、旧C1记录和备份保持；读取不写数据库／Git／tracker|r1安装196通过／1跳过保留；r2受影响49通过／1文案断言失败，修正后该回归1通过；无产品二次改动|
|O3 安装与结构审查|新非editable包／两RECORD／283冻结，必要受影响回归；实际自身模板、新fresh-context完整独立两轴|r2包446／两RECORD／283通过，相对r1仅原Git owner变化；自身首审306.03秒request-changes／完整读取通过；SP3修正后r3包446／283及受影响18项通过，聚焦自身164.79秒approve／五scope完整读取通过，完整29文件独立两轴0／0通过，本地出口完成|
|O4 精确交付|普通提交／推送、精确Git／remote及本片自己的双OS必要CI；更新手册／架构／本片记录|ad331c8普通提交／推送、29Git／ready及作者SSH同完整SHA通过，自己的CI43042210053双OS七必要步骤及原评审精确终核通过，C3a精确交付终结；REST403／matrix404／原非终态保留|

当前[交付记录](../delivery/2026-11-11-candidate-observation.md)记录每步实际证据。只用loopback和本地Git做平台写零次验收，不向真实账号创建分支或PR／MR。凭据继续外部变量，持久原件置home下忽略检查目录。
