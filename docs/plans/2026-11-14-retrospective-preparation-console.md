# F10d3b1：准备三类复盘候选的完整输入

日期：2026-11-14。接 [F10d3a](2026-11-14-retrospective-evidence-console.md) 的最终五产品／r3；实施基线为其普通发布提交 `203973f9fbb2e6d97bf59961b49482cb875f2d0d`，完整远端 Ref 已核；自己的 CI 及原 reviewer 后继补核另行观察。已核 Git 与调用链，原 request 复读及四条 HTTP 入口、原view表单已完成；r1安装213项／实际页面84＋24／6次原CLI与自身模板均已过，最终本地独立补核待。[F10](2026-11-14-evaluated-improvement.md)／[当前进度](../PLAN.md)。

## 实际消费路径与分片

原 `retrospectives.prepare`／`prepare_memory`／`prepare_workflow` 已冻结完整原证据、当前 Skill head／有效记忆修订／完整目标 manifest，最后调用 `workflow_definitions.prepare_input_from_manifest`；该 owner 持有祖先资源、原 grant、容量、原子发布与新目录不覆盖合同。原 `check`／`export` 三个家族及其 CLI 已可用，页面缺少这些消费者。

F10d3b1 先完成三类准备与已落盘输入的明确复读，形成可直接交给原 `composition run-input` 的完整出口。F10d3b2 再接原结果检查与完整候选导出；它需要把项目、原 input／result 身份绑定到同一次检查和导出，不能先在 HTTP 读一次再由原 owner 重读不同文件。随后原单叶调用页面与原评价／明确采用／回退旅程另接。保留完整 F10d3b 范围，准备成功不等于模型执行、候选存在或已采用。

## 接口与实现位置

- 在原 web 增加项目绑定的三条 `retrospectives/{skills,memories,workflows}/prepare` POST，分别直调原三函数，不建立目标注册器、第二资料库或统一调度。基础表单 payload 共享原准备字段，专用 payload 只增加各自基线字段；不复制原容量／版本／资料校验。
- 使用原 Skill heads 与 memory catalog 读取基线，显示实际来源、revision／digest／有效性。流程目标显式填写完整 manifest 路径、digest 与新根版本；作者 manifest 和实例另外填写，不将作者图混作目标图。准备时原 owner 重新检查，目录观察不是租约。
- 为明确复读原保存结果增加一条 `retrospectives/inputs/inspect` POST。原 `retrospectives` 内收拢已有完整 input／task 读取，复用原 inspector、原三类 request schema 和同一 task 摘要核对；检查项目后才返回完整原请求和原 input 身份。新 helper 是该 inspector 与原 proposal reader 的真实共同消费处，既有 check／export 的离线合同保持。
- 表单留在当前 `retrospectives.js` view owner 内，复用已导出的 UI helper。准备只消费当前成功读取的完整证据及其精确选择；证据失效立即禁用新准备，不缓存或重新拼接正文。实际写入只由明确提交触发，执行中防重入；读目录、换选项、换类型、切页或复读结果均不发模型或准备请求。
- 保留上次明确提交的目标目录及原回复，输入变化不声称撤销已发布文件。失败或丢回复不自动重发；用户可明确复读原目录，看到完整原请求／身份后沿原 CLI 继续。复读是观察，不断言原失败调用未写入或将旧输入当作新表单成果。

新 input 仍通过完整材料与权限上限；子模板读取全部祖先资源，不扩大父授权。已准备输入保持原字节，新 head、有效期或图变化只影响新的准备。页面不写记忆、Skill head 或定义，不执行可信评分器，也不接管正式 Task 的预算／unknown 对账。

## 可验收节点

- [x] 固定基线、实际新增 caller／文件、旧 CLI／schema 兼容范围与上述唯一 owner。
- [x] 原完整 request 复读与项目绑定、三个薄准备入口及页面表单实现；页面真实 ESM 加载。
- [x] 最终非 editable 包／两 RECORD／283；相关原 suite和必要的跨项目／原 request 读取回归。
- [x] 实际 HTTP／CLI／浏览器三目标准备→复读完整 input；全部祖先资源／原 SHA／UTF-8／权限／容量；无模型或采用写入、原件字节／mode保持；workflow DB保持，Skill／memory仅按明确夹具控制更改。
- [x] 旧 head／过期记忆／错误目标摘要／超容量／已有目录拒绝；丢准备回复后明确复读、迟到读响应、输入和类型／项目／页面切换、三宽与服务收尾，未验矩阵如实标注。
- [x] 自身原审查模板和本片新的 fresh-context 两轴最终本地终核，逐步更新交付与 PLAN。
- [ ] 普通发布／完整 Ref／自己的 CI 与原 reviewer 后继补核分别记录。

本片不扩大真实 B3、完整 Forge C2、F9d／G1、真实隔离或全平台／质量／性能验收结论。F10d3a 自己的 CI 可以并行观察，未满足前片门禁前不发布后继片。

验收更新：r1非editable603／RECORD611／616／283，原五suite213通过；主旅程84＋生命周期24、65原HTTP／5迟到／1丢回复、6次原CLI完整同一及三宽／原件／收尾、自身原结构模板Codex35.137秒approve均已完成。本片新源码两轴0 finding，最终本地／发布／自身CI分开补核。

最终本地终核已完成：原fresh-context需求／维护性两轴approve／开放0／0，原374件保持，另4独立证明及5待发布调用器共383引用。前片43566484193自身CI及原reviewer终核已闭合，本片准备普通发布。

普通发布 `f7a4d28e82f2db99245885eaa24229299f7f73d7`／21blob／完整远端Ref相同，固定383／发布后387引用；原reviewer固定发布及自己的CI补核待。

自己的43568843549终态八job／30必要步骤成功；原reviewer CI终态补核待，固定发布补核已通过。

原主审／两轴CI终态approve／开放0／0，自己的CI与固定普通发布全部闭合。
