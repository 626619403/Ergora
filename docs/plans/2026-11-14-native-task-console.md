# F10d1：原生六阶段与预算页面

日期：2026-11-14；固定基线 `54fcd0b188f1f1dc46229dfe504f5dddb9c4aaea`。[F10总计划](2026-11-14-evaluated-improvement.md)／[进度](../PLAN.md)。前片工作流候选已普通发布，本片可开发；发布仍需前片自己的必要CI及原独立终核。

## 现状与范围

正式Task v7的资料选择依赖原native六阶段、preparation和预算，但当前网页创建器只产生v1／v2／v3。先补真实前置入口，不把context字段塞进不支持它的旧版本。原任务表单样式继续归`style.css`，现有`taskComposition`和`tasks.creationDialog`分别持有组合表单与原预览／确认／unknown恢复；服务端原`tasks`、`native_six_stage.invocation`、`WorkDelivery`与预算owner继续准入，不加HTTP接口、调度器或新任务格式。

在原Agent来源中增加“原生六阶段（Linux／WSL2）”选项。用户按原预览SHA读取完整manifest，显式选择内部native调用、inventory／plan叶、执行和审查子流程及工作单元分配；完整准备源码路径与资料模式、总时间／清理时间／模型次数预算由用户填写。沿原逐实例backend编辑器展示准备、执行、审查成员；执行者仍明确选择可信边界与后端，审查差异策略保持。不按实例名／后端名猜能力，不在浏览器复制原图／权限／预算验证算法。

原编辑器一次返回组合和可选预算，唯一调用者按原合同产生v6；原生任务须先显式授权准备（此时开始预算），再读取原准备、预览与确认创建，创建传回原prepare_sha256。准备丢回复保留原ID并只查原记录，不自动重发；可选工单source与native共存时保留v6。原project／仅review／delivery继续产生原v1／v2／v3。原任务预览显示实际冻结准备成员、native父链与原授权预算／期限，明确确认才创建，启动仍另行操作。旧manifest／旧run不变；页面变更均使旧预览失效。延迟读取、切换来源／manifest／项目／home、断开与丢回复沿原sequence、DOM生命周期及unknown查原ID处理，不自动重试创建。

记忆／Skill选择留F10d2，在该原生入口上产生原v7；复盘候选页面与原评价／明确采用／恢复的完整旅程留后续受约束片，不做通用UI DSL。

## 验收

- [x] 盘点原v6／v7、唯一表单调用者、原native／preparation／预算与旧页面，固定范围。
- [x] 在原两个JS owner补字段／选择／返回值和冻结展示，原style owner限定任务fieldset宽度，原服务端及模板不改。
- [x] 最终非editable包与两RECORD／283，相关原suite；不为字段文案写平行测试框架。
- [x] 实际浏览器走原HTTP：合法native显式授权准备／原预算预览／明确创建／原ID读取、旧review／delivery入口；原服务端拒绝错误父链／预算／不完整准备，修改与迟到回复不恢复旧预览。核完整冻结字段／材料与新任务事实，无模型／服务启动。
- [x] 页面三宽与键盘可用、错误保留输入、进程／端口／浏览器收尾；原自身结构模板。
- [x] 新的fresh-context两轴最终终核：两轴approve／开放0／0，R1–R3关闭。
- [ ] 修复实证finding并终核，普通推送／完整Ref／自己的必要CI及原reviewer补核。

逐步结果写[交付](../delivery/2026-11-14-native-task-console.md)。Linux／WSL2原native准备与Windows原生限制保持；页面通过不证明真实模型／GPU／业务优化、完整Forge或F9d／G1完成。
