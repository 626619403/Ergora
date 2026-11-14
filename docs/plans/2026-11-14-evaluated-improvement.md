# F10：有来源的任务上下文与受评价改进

日期：2026-11-14；起点为C3固定候选`f47cd50fcce600fba92f64aff73982012f6e31c9`，自己的CI43539314720八job／30必要步骤成功、原结构轴终核通过。[总合同](2026-11-01-all-in-one.md#8-p1低代码更多真实工具与演进闭环)／[当前计划](../PLAN.md)。先复用现有owner，逐片实现、更新证据与独立审查；不建立第二记忆库、评价器、调度器或自治批准者。

## 已直接核对的现状

- `memory.py`是项目记忆权威，已有来源URI／修订、追加修订、历史、恢复和删除；删除清空全部历史正文与来源，不恢复已删内容。`records`当前按active过滤，尚无失效时间。`search`支持本地SQLite或ReMe，远端正文不作为canonical返回；ReMe是可重建投影。
- `agent_runs.py --recall`已经消费`memory.search`，并将召回文档保存进原运行context。这里不是正式Task的完整上下文选择入口，不能据此关闭F10。
- `skill_assets.py`已有目录原字节身份、导入／版本／活动head／历史、diff、显式回退；`skills.py`与`evaluation.py`已有固定基线／候选评价后明确采用，GEPA与research仅提供候选。不能重新实现一套Skill状态机。
- `workflow_definitions.py`／`definition_bundles.py`已有祖先资源、完整材料／权限／容量核对、资源修订及manifest冻结；`tasks.py`和`task_envelopes.py`负责正式准入／原输入材料。新增任务上下文应进入这些原owner，不能拼接一个绕过祖先资源或容量检查的旁路。
- 盘点起点`state.py`为schema v4，writer fence已覆盖旧连接；F10a已沿原迁移实现v5。新writer不得丢弃有效期，旧客户端重开拒绝新库；已开旧reader或缓存无法撤销，升级先停旧进程，不能仅因JSON列可追加字段而省略兼容性设计。

## 分片与验收

|节点|实施与复用|可验收出口|状态|
|---|---|---|---|
|F10a 记忆有效期|沿原`memory`增加可选带时区的`expires_at`；默认旧记录无限期，不回写旧内容；更正／恢复为新revision，恢复原过期revision不能自动续期。新增显式catalog展示有效／失效／删除与判定时刻，默认检索仅返回当前有效资料。CLI／HTTP／页面共用原owner；ReMe同步清理失效投影，搜索返回前以最新本地状态过滤远端命中。|时区／到期边界、非法日期不落盘、同revision冲突、原过期历史保留、删除仍不可恢复；ReMe延迟／陈旧命中不能注入失效正文。schema迁移／旧writer fence／备份恢复、实际CLI／HTTP／页面和自身模板／新独立两轴。|[具体合同](2026-11-14-memory-validity.md)本地完成：r1包575／两RECORD／283、78通过／7平台跳过、原CLI HTTP页面／三宽／模板／收尾通过；新两轴最终本地与固定发布approve／开放0／0；a2899e8自己的CI43542024437八job／30必要步骤成功、原结构轴CI终核通过|
|F10b 明确选择与冻结|为正式任务选择精确项目记忆revision和已采用Skill digest，先预览完整来源／有效性／字节容量，再在原创建／input envelope中固定材料。新上下文拒绝过期／删除／被替换资料；旧run继续原快照，不热换。沿原祖先权限上限、完整资源合同和预算，必要时新增明确schema版本，保留旧版本读取。|预览后修改／失效／删除／head变化必须拒绝旧预览；提交恢复保持原意图与已冻结材料；库存／计划／work／review接收同一要求的完整材料，无静默截断、选中根之外无权限扩张。真实原输入／stdin核对，CLI与HTTP一致。|[具体合同](2026-11-14-task-context-selection.md)已固定；v7／v11沿原根资源修订，修后r2包577／两RECORD／283，安装229／6、原九job七叶完整材料和实际CLI／HTTP及准入反例通过；自身approve、新独立两轴最终本地approve／开放0／0，已普通发布f1cfcdd／29blob／完整Ref同一，原两轴发布补核approve，自己的CI43545573942八job／30必要步骤及原结构轴终核通过|
|F10c 有证据的复盘候选|从已保存的任务／运行／评价／负结果与原source身份，显式生成记忆／Skill／流程候选；沿原ReMe／GEPA／research与已有导入／diff／评价／采用／回退接口，记录成本、失败和不确定性。|候选不能改活动head、可信评价器、权限或原证据；完整基线／候选／评价身份和明确采用理由可查；重复／中断保留原ID，不自动采用。先只读候选，再单列采用入口。|F10c1已普通发布396e9d1，r2包577／两RECORD／283，安装131／6、实际八CLI／自身模板、新独立两轴及原固定发布补核approve；自己的CI43547736558八job／30必要步骤及原独立终核通过。[F10c2a](2026-11-14-retrospective-skill-candidates.md)已精确交付；[F10c3a](2026-11-14-retrospective-skill-adoption.md)最终本地／固定发布通过，自己的CI43553150941因Windows20分钟总上限取消（29／30），原历史保持，后继CI预算修正使用新SHA自身完整CI；[F10c2b1记忆候选](2026-11-14-retrospective-memory-candidates.md)最终r2独立本地两轴approve／开放0／0，CI依赖具体调整见活动片。流程候选与d后接|
|F10d 页面与完整旅程|在原正式任务、记忆、Skill、资料页呈现可选材料、来源／到期／容量、冻结差异、原评价和明确采用／回退。采用受约束表单，不做通用UI DSL。|已开始run保持旧资料；新run只使用用户选定且有效的当前资料；候选／失败／采用／回退一条实际旅程与断线恢复，跨项目隔离和三宽UI。|依赖前片；接G1公开旅程|

## F10a实施前的约束

有效期以服务端UTC判定，在每次新检索／构建context的边界核对；明确返回的观察时刻不是未来仍有效的保证。失效不删除历史，不改变旧运行归档；删除沿原清空与备份保留规则，不宣称抹除已导出的材料。旧调用不带expires_at保持现行为；新接口对可见的失效／删除资料仅作审阅，不把catalog当召回结果。

迁移优先沿原State版本与writer fence；在实现前核实所有表／触发器及备份门禁的真实消费者，仅作所需语义升级，不顺带重构迁移框架。ReMe watcher可见性仍是eventual；本地有效性才决定返回内容，不声称远端删除同步即刻完成。不增加定时过期daemon、后台重试或模型自动续期。

F10a先做持久有效性／检索／呈现，不将`--recall`扩写为正式Task新协议，也不悄悄加入自动资料选择。F10b再冻结正式任务字段、资源身份与恢复合同。每片的新文件／抽象先找真实生产消费者；有单一owner时留在现有模块。

## 执行与未验范围

- [x] 核对memory／Skill／recall／组合资源／正式准入／State原owner和总合同。
- [x] 固定[F10a细化合同](2026-11-14-memory-validity.md)、旧客户端拒绝规则及原件保留基线。
- [x] F10a实现、适量真实反例、最终非editable包／CLI／HTTP／页面、自身模板和新fresh-context独立终核。
- [x] C3自己的CI43539314720八job／30必要步骤终态成功且原结构轴终核通过，后续产品可普通发布。
- [x] F10a普通发布a2899e8／完整Ref／自己的CI43542024437八job／30必要步骤及原独立终核通过；保留各候选自己的CI身份。
- [ ] F10b／c／d逐片推进；最终G1统一文档／新安装／升级回退／跨机重建。

F9d完整控制旅程、真实B3／GPU与完整Forge C2的外部条件继续分别保留；本计划不以合成回归关闭这些范围。F10a／b及F10c1各按其交付记录；F10c2a精确交付闭合，c3a自己的CI另核，c2b1本地最终证据与独立补核按活动片记录；流程候选和d仍待。合成合同／模型null不当作真实改进效果。

## F10b接缝盘点（F10a验收期间，仅设计）

直接核对的正式输入有两种版本号：`task-definition-v1`–`v6`是用户定义；`task_envelopes` v2–v10是已冻结执行输入。既有v7指工单来源envelope，不存在task-definition-v7；不能混称。最新v6用户定义对应原预算／原生六阶段envelope v10，完整材料路径已经覆盖inventory／plan／work／review。

原链为`tasks._budget_project → reference_creation_process.task_preparation → reference_task_creation.preparation_worker → tasks._definition → 原compile／wrap → 原prepared／creation intent`；冻结后恢复由原record所有。`WorkflowInput.stage_material`／`evidence_contract`已是额外冻结数据与离线证据的真实接缝；`reference_executor`沿这些接口组materials，再经原`prepare_input_from_manifest`完整容量校验。不要在orchestrator按后端或新资料类型分派，也不直接拼prompt。

下一片先比较两种实现，再固定合同：

- 只向materials塞正文及Skill路径会绕过原资源URI的read覆盖、Skill附件交付与ancestor容量核对，不能选。
- 优先沿原definition资源修订／manifest冻结，把用户明确选择的精确memory修订和当前Skill head目录复制为原根资源，保留原图路径与权限／limits；新资料不能自动放宽read。原根版本变化和所有来源身份需明确展示，不悄悄改已冻结manifest。选择元数据与产生资源的关系要进入新正式版本并可离线核，不引入另一资源库。

必须先解决的细节：精确memory修订／正文身份／来源与expires_at；Skill name／活动head revision／目录digest／完整附件；同名祖先Skill冲突；根资源修订后的URI覆盖及容量；prepare后preview与首次publication之间的更正／到期／删除／head变化应拒绝旧选择；持久creation intent已保存后的resume必须使用原件，不重编译、不续预算、不改资料。原SQLite写预留和原publication锁是最终准入位置，不能让前置preview成为授权或把远端RPC放进写事务。

这只是已核调用链与待定选择，不声明task-definition-v7／envelope v11已实现；正式确定版本、字段和分片验收后再动产品。F10a自己的CI运行期间可继续该设计，不应为便于接资料先重写整个输入协议。

F10b调用链比较已结束，正式合同与分步进度见[独立分片计划](2026-11-14-task-context-selection.md)；本页上文的“待定”仅保留当时盘点过程，不覆盖新合同。

## F10c后续顺序调整

F10c2a闭合最终独立验收与发布后，先做F10c3a：一条标准Skill候选的显式落盘／导入、同一可信suite基线／候选评价、明确采用与原回退旅程。这样先让现有候选输出具有可直接使用的完整出口，再扩展F10c2b记忆／流程候选；后两者必须沿自己的原版本／批准合同，不能套用Skill评分假称通过。原范围全部保留，不因顺序调整删减。F10d页面在对应完整用例有明确合同后接入。每个具体实现片仍先固定自己的完整baseline与验收计划。

## F10d后续分片

F10d1原生表单已精确交付，F10d2资料选择已普通发布、自己的CI另核。复盘页面缺少共同的完整证据入口，先做[F10d3a](2026-11-14-retrospective-evidence-console.md)，再d3b三类候选prepare/check/export，随后接原单叶调用页面和完整评价／明确采用回退。现有Skills页已有评价／采用owner，但组合单叶尚无HTTP入口，不能用普通role prompt调用替代冻结input或声称图已自动执行。原完整旅程范围保留，按原所有者逐片验收。
