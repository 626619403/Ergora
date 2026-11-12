# F7c-C3b：显式关联已有 PR／MR

接续[C3a候选观察](2026-11-11-candidate-observation.md)与[第一方研究](../research/2026-11-11-existing-review-association.md)。研究基线为`93b538fd474120fa05574dcdcf376b7666502c8d`；实现基线为C3a普通提交／推送的`ad331c854a6fbdbf6bacc3aac4350bb8d393713f`。C3a自己的CI43042210053双OS七必要步骤与原评审精确终核现已通过，前片精确交付终结。本片已有未提交实现；下表和交付记录分别表达实际实现、验证与审查状态。

## 用户行为与范围

操作者提供原v7来源任务、原run、完整已导出candidate、明确base分支、一个原来源仓库内的PR number／MR iid和关联理由。工具核当前候选与指定资源，保存不可变的本地上下文关联，并允许CLI／HTTP离线读回。仅向provider发GET，不创建、编辑、关闭、合并PR／MR，不修改refs、评论或标签。

关联的语义固定为`operator_asserted_review_context`、`context_only=true`、`execution_authorized=false`、`proves_original_attempt=false`。原candidate、approval、claim、评论／标签attempt/result及unknown保持，不因关联而确认任何远端原attempt。源issue、评审资源的作者和本地操作者分别表达；不要求资源作者等于当前reader，不新增认证身份系统。

首片只接受同来源repo／project、原export head分支与精确candidate。首次关联时当前本地ref和远端head均须相等，base ref须可见且名字与review相符；原task base与当前base的差异另存事实，不重新定基或批准。draft/state按实际值保存，关联不额外要求open/draft。fork、跨repo、按标题搜索、任意URL与自动猜测不在本片。

GET是分时观察，不是共同snapshot/CAS/ABA检测；GET也可能让provider内部计算派生merge对象，不能承诺服务端零内部写入。v7原来源未冻结历史repo native ID，本片不能回填或宣称历史仓库未被替换；保存当前repo/review native身份，另核当前源issue native ID以发现常见namespace重用。404是未找到或不可见，首次关联拒绝，已存历史仍可读。

## 所有权与实现约束

|原Module|窄增量与理由|
|---|---|
|`tasks`／`reference_task_export`|复用已发布来源、原export/run/candidate和C3a对象/ref观察，不复制原生任务解析、Git进程或正式执行逻辑；inspect保持禁lazy fetch及replacement|
|`IssueBackend`本族|新增指定review单资源读取Interface；GH／GL各自核URL、number/iid/native ID、同repo和head/base字段。复用完整有界HTTP与白名单，无上层provider分派或新SDK|
|`issues`|拥有本地上下文关联、canonical记录／scope和普通load校验；CLI、HTTP与backup分别消费保存／离线读／校验。留在现有观测与context所有者，不建立通用publication层|
|`State`|仅新增本域关联表及必要schema迁移，沿原预迁移备份、短事务和所有旧表writer fence。不是第二run账本或新数据库|
|`backups`|继续委托`issues.validate_storage`，不用新增领域分派；旧v1–v3备份与新表存在性分别处理。离线校验不访问Git、tracker或Temporal|
|CLI／HTTP／描述|共用同一用例，HTTP保留同源和`X-Ergora-Request`保护；描述只登记实际operation。F7d页面另片，不复制表单或事件入口|

每个新guard须对应外部输入、持久身份或事务竞态。每个新helper先找实际生产消费者与现有所有者；私有协议算法按本族归属，不为满足复用数量制造wrapper。新增公共格式仅表达实际关联合同，不预建远端create/send的prepare/attempt/result。

## 数据与读取合同

- GH用`GET pulls/{number}`，分别保存number、REST id、opaque node_id；head/base repo须与C3a当前repo native身份一致，head.ref/SHA必须是原export/candidate，base.ref等于明确输入。`base.sha`是这次PR响应事实，不冒充当前branch tip。
- GL用数字project ID路由`merge_requests/{iid}`；iid与global id分开，project/source_project/target_project均核同项目。MR.sha核原candidate；`diff_refs`可null或未就绪，非空字段各按原含义保存。start_sha不是实时target tip，base_sha是merge-base；diff head不同须明确投影，不能覆盖MR.sha。
- 原title及body/description按不可信文本全文保存，支持的null与空串分开。沿原单响应1MiB、20秒socket I/O、无redirect/retry；正常约五次GET，不承诺总墙钟20秒。最终canonical关联文档也设明确字节上限，超限拒绝，不截断后称完整。
- 记录包含project、source snapshot、原creation/compiled/run/candidate/export身份、当前repo／review native身份、完整原生内容与状态、分时head/base事实／比较、读取时间与HTTP字节摘要、reason及linked_at。白名单保存，不持久化raw repo JSON或临时clone token。
- scope由原project/task/creation/run/candidate/export语义槽派生；review目标、base、reason、时间是operand／证据，不是换值另建槽的逃生口。同候选首片固定一个review。同目标重复操作返回原历史记录，明确不是fresh读；不同目标冲突，不能覆盖或自动supersede。历史变化的另一次观察后续按真实需求立片。
- 外部读取不持SQLite写锁。最终短事务重核revision／绑定和原scope，并发由唯一约束决定赢家；本地commit前失败无记录，commit后回复丢失可离线按原身份读回，不伪造远端unknown。
- 同一load算法供保存、离线show和backup使用，核完整schema／预算、canonical SHA、scope、SQL列、同repo/candidate、source snapshot与project归属。离线验证只证明保存证据的一致性，不证明外部原任务或当前远端仍未变化。

## 可验收节点

|节点|出口|状态|
|---|---|---|
|R0 研究／立片|第一方GET字段、原所有者、最小持久合同与故障旅程；固定前片提交基线|研究完成，新增GET0／12缓存原件已核；实现基线ad331c8已固定；C3a精确终核通过|
|R1 原生读取|GH指定PR／GL指定MR，两族统一Interface、完整身份和正文；fork/nullrepo/错误head等失败不产生记录|已通过源码与r2受影响安装，完整独立Spec／Standards开放0／0|
|R2 本地关联|原task/candidate绑定、同scope唯一不可变保存、重复／并发／修订变化、离线读；不改原writeback／claim|已通过源码与r2受影响安装，完整独立Spec／Standards开放0／0|
|R3 迁移与备份|新表、旧打开连接writer fence、失败回滚、旧备份／新记录同一load校验；损坏有意义地拒绝|已通过源码与r2受影响安装，完整独立Spec／Standards开放0／0|
|R4 CLI／HTTP旅程|两provider真实本地v7→Git export→新CLI保存／fresh CLI与HTTP离线读；只控制SDK端口，不称六阶段模型运行|两provider原v7／Git→fresh CLI保存／离线读通过；HTTP同用例通过，仅SDK端口受控|
|R5 安装与审查|新非editable包／RECORD／283，必要受影响检查；实际内置审查模板、fresh-context完整独立Spec/Standards、文档静态|r1包447／两RECORD／283及八安装suite189通过／1跳过；实际自身首轮超时；九完整核心聚焦546.83秒approve／五scope全文审计通过，后两处修正不借模型判词；独立SP1／ST1补证／最小修正后r2包447／283及68安装项通过，完整28独立两轴开放0／0，SP1／ST1／ST2关闭；最后静态28文件／367链接issue0，本地出口通过；R6待核|
|R6 精确交付|普通提交／推送、精确Git／remote和本提交自己的必要双OS CI；更新本片记录及PLAN|572c44e普通提交、28Git／ready与作者SSH同完整Ref通过；原push60秒超时无终态，远端已到commit；自己的CI43068731988第四API样本双OS七必要步骤success/completed及原评审离线终核通过，精确交付终结|

验证沿既有loopback provider、本地Git和备份旅程，保护可静默出错的合同，不逐个镜像普通参数异常。重点是number/iid/global id混淆、namespace/native ID变化、可空异步diff、base前进的不同语义、正文预算、无写锁网络、同scope并发与备份篡改。必要checks通过后，除新改动／失败／未决风险外不重复完整套件或模型。

每节点完成后更新本计划、所属`docs/delivery/`记录与[PLAN](../PLAN.md)，按AGENTS重新核对。严格分开实现、运行验证、模型审查、独立审查和精确交付状态。后续仍为F7d用户旅程／有界事件，再推进F8–F10、G1；自动分支发布／草稿创建的严格合同继续另片，不借本地context关联宣称接入。
