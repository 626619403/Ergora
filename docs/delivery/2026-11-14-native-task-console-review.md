# F10d1 原生六阶段与预算页面独立审查

审查者 `native_task_console_review`，fresh context；先读原始要求、固定差异与相邻 owner，再核作者的运行记录。按 `review-pr`、`maintainable-project-delivery` 的独立证据要求及 `codebase-design` 分开审需求／行为和结构／维护成本；没有修改产品、启动模型、安装、提交、推送或发布外部评论。

## 固定范围与当前结论

基线与初审 HEAD 均为 `54fcd0b188f1f1dc46229dfe504f5dddb9c4aaea`，分支 `refactor/architecture-foundations`；本片是未提交工作区。初审产品为 `src/ergora/data/console/task-composition.js` 与 `tasks.js`，R3 后增加同目录 `style.css` 的局部任务表单修正；另审本片计划／交付、USAGE／WORKFLOW_DEFINITIONS、PLAN 与前片发布补核的记账差异。原服务端、schema、scheduler、283 reference 与 preset 不在修改范围。私有封存在 `.ergora/checks/native-task-console/independent/`。

初审产品等完整 r2 wheel `7f8d907842a5452e4f5ff780ca24068a9f7e99190d09559ac23665648a6dcc4f`：前者 14164B／SHA256 `5dbc8f0430cf3eca567c60effa2586fa2d1b5a2ec3cc961c46295aca07aa8065`，后者 84569B／SHA256 `16db1b3b963ff1efb1156c9e8208d585e4866bbaaa9ddac2e7a500434858b712`。`source-identity-r1.json` 与 `product-r1.diff` 固定其身份。

**最终本地两轴均 approve，需求／行为开放 0、结构／维护成本开放 0。** R1 低影响角色目录／字段语义、R2 低影响准备入口、R3 中等小屏布局均已在最终 r5 源码、安装件和对应实际页面证据中关闭。下述初审及中间包保留原身份；最终结论只覆盖末节所列本地范围，普通发布、完整远端 Ref 与本片自己的必要 CI 仍待。

## 需求／行为轴

### R1：准备成员的角色目录／字段默认不匹配（低，已关闭）

位置：初审 `task-composition.js:128` 的 `memberEditor`，`tools[writer ? "implementer" : "reviewer"]`。

inventory／plan 是原 `inspector`／`planner` 角色，但表单使用 `tools.reviewer` 创建其覆盖字段。原 bootstrap 已有 `tools.inspector` 与 `tools.planner`，`components.configuration` 按角色为声明能力的 `command` 后端生成不同默认值。选择 command 并填写结构化协议时，表单默认提交 `['independent-candidate-review']`，原 `CommandBackend.validate_binding` 先以缺少 inspector／planner 能力拒绝。它不是两个只读角色共享相同能力的问题。

独立在 r2 安装件调用原 `agents.validate_binding(..., formal=True)`：reviewer 默认能力用于 inspector、planner 均被拒；各自角色目录默认能力均通过此层验证，四项原件在 `preparation-catalog-probe-r1.json`。继续调用完整原 `_member` 后，`preparation-catalog-probe-r2.json` 又证实：command 仅支持 native，使用正确能力仍被后续 text-only 模式检查拒绝。因此不能把第一层通过称为完整准备准入，未证明当前一个支持的 native 准备配置被挡。初步“行为中等”判断已收窄为低影响字段语义／目录耦合问题，不作为行为阻塞。两探针均未执行任意命令、模型或准备。

最小修正按实际 `leaf.role` 复用原目录，保留执行者显式选择后端／信任规则；最终 r5 源码、安装件与独立 `final-fields-r5.json` 已核，作者实际旅程也核两角色 command 字段后切回受支持 Codex 才授权准备。该项主要属于结构／维护成本轴，不另作两个独立问题重复计数。

### R2：非 native 入口显示准备按钮，误点击会丢弃有效预览（低，已关闭）

位置：初审 `tasks.js:224`、`241`–`250`。project／review／delivery 也显示“准备原生六阶段”；点击先 `invalidate()` 清除已有冻结预览，再因缺 budget 报错。输入保留且不会误授权，但普通旧入口出现不能完成的操作。最小修正是由持有 source 的原 composition owner 控制该按钮可见／可用，准备请求与授权确认继续由 tasks owner 持有。

最终按钮已归原 native 预算 fieldset；独立 r5 实际 DOM 检查 project／review／delivery 下均隐藏且内部有效禁用，完整 native 载入后可用。原旧入口实际预览仍保留 definition1／2／3。

### R3：390px 下任务表单最小内容宽造成模态内容裁出（中等，已关闭）

位置：`style.css:879` 的 `.task-creation-fields` 及嵌套 fieldset。作者实际 r3 生命周期检查在 21 项交错检查通过后失败于 390px；reviewer 已直接查看原 `native-overflow-390.png` 和 `inspect-width.stdout`，确认 document390、dialog354、body352／scroll438，表单多个 grid child 宽411，右侧内容超出模态可见范围。这是实际三宽验收失败，不是仅按容器 `isDisabled()` 判断的调用器问题。

最小修正将原任务 grid 的单列改为 `minmax(0, 1fr)`，并仅为 `.task-creation-fields fieldset` 设 `min-width: 0`。这两条在中间 r4 仍有 scroll395；最终 r5 再将该表单 legend 限为 `max-width: 100%`、`overflow-wrap: anywhere`，使长实例路径换行。没有通过隐藏／截断材料解决宽度，也未扩大到全局表单样式。新增 `style.css` 属本片第三个产品文件；最终实际 390px body352／scroll352，1440／960 均688／688，原三张截图已直接查看，r3 失败与 r4 中间身份保持。

## 结构／维护成本轴与自身模板意见裁定

唯一生产 caller 已同步 `{composition, budget?}` 返回形状；`definitionFrom` 合并两个实际调用所需的版本／来源构造，原 `bindingFields` 持后端字段，原 `tasks._composition`、`WorkDelivery`、`native_six_stage.invocation` 和 budget owner 持准入。没有建立新 endpoint、格式、通用表单 DSL、图执行器或第二意图账本。当前没有另立结构阻塞 finding；R1 直接复用既有角色目录即可修复。

真实自身 Claude 模板的原 `request-changes` 保持。其“跨关闭不能自动重建表单”意见已核原 preparation GET：该接口只有授权／状态／摘要，不返回 definition；原要求也未要求新增自动重建或持久表单。建议明确只读查询不装载创建表单，并在授权前及准备结果／unknown 提供原 definition 的完整下载，供原 CLI 恢复；不得暗示查询本身恢复表单或续预算。此处按可操作性／说明修正处理，不增加自动准备／自动预览。

三个 HTML `max` 与当前原 schema／`reference_budget.validate_policy` 的固有合法范围完全一致，未实证当前合法预算被挡；独立不把它定为当前错误或阻塞。作者可移除上限以减少同步点，由原 owner 返回上限／关系错误，相关原错误路径须补验。自身模板关于准备角色目录的疑问由 R1 的原 owner 实证确认字段差异，不能用“同只读能力”注释结案；完整模式检查同时限定了其实际影响，不声称支持的 native 后端被阻断。其余可选清理不作无证据重构要求。

## 已核证据与范围

独立静态追踪：原 `tasks._definition/_composition/prepare/preparation/preview/create`、`reference_task_creation`、`native_six_stage.invocation`、`WorkDelivery`、v6 schema、原 budget owner、`ui.form/modal`、`app` 的 view／home 生命周期及唯一 caller。v6 必须先显式授权准备；预览只读原 prepared 材料；创建带原 prepare／preview 双摘要，source+native 保持 v6，旧入口保持 v1／v2／v3。冻结展示覆盖准备／执行／审查成员、native 父链与原预算期限。

`package-audit-r1.json`：reviewer 对初审 r2 源／snapshot／wheel／installed 逐份比较全部 **602 产品**，逐行核两 RECORD 的 **610／615** 大小与 SHA，核全部 **283 reference** 摘要，无差异。没有重新安装或把该字节审计当运行验收。

独立命名浏览器仅向作者安装服务发 GET；所有准备、预览、创建及准备状态探针响应均在该浏览器内拦截模拟，未向共享 fixture 发 mutation：

- `ui-lifecycle-r3.json`：**23 项／3.48 秒**，核授权确认不发请求、修改预算废弃授权、准备在途每个内部字段有效 `:disabled`、在途预览不发请求、失联后原 ID 读取不重发、旧 v1／v2 形状、输入／manifest／预算变更与迟到预览不恢复确认、unknown create 锁定与双摘要。
- `ui-disposal-r1.json`：**12 项／2.80 秒**，持有准备回复时关闭模态、切页销毁 view、重开新表单，旧 503／finally 不改新 ID、不禁用新字段、不复活结果／确认、不重发。
- 探针 r1 的同项目刷新竞态超时、r2 未等待 manifest 设置重新启用的超时均为私有调用器问题，原件保持；未改产品迎合探针。独立浏览器 `close-r1.json` exit0。

## 最终 r5 独立终核

最终非 editable wheel SHA256 为 `4e6ff29ad9901a530dfc862a808214a0672c91da99d2becdfd98aaddd18db7cb`。`package-audit-r5.json` 重新逐件核全部602产品：当前源码＝最终 snapshot＝wheel＝installed；两 RECORD610／615 的大小与摘要、283 reference 均相符。三个产品身份如下，后续记账不改变这些产品字节。

|产品|字节|SHA256|
|---|---:|---|
|`task-composition.js`|14162|`4745791bfe8238e5f24abb6dc8d47a9bd9be14fc12c78c059fc8ec30b5fa1640`|
|`tasks.js`|85417|`e3df984af33a1f41a5bd79ce78abc958457d51f5aa78a045ceec7d0548936602`|
|`style.css`|20858|`81971acb8938ff8b9369f0099de6f90cc5209a2d871dc2d5b9c9b896f94104c4`|

最终安装件原 `tests/test_web.py` 为 **9 passed／11.87秒**，原监控13.4207秒、exit0。初始完整 r2 六 suite 为 **87 passed／504.46秒**、监控506.4359秒；后续只改前端，原服务端 owner 未变，但这87项不记作 r5 执行。

作者最终实际浏览器 `browser-main-r5.json` **58项／13.7815秒**、`browser-lifecycle-r5.json` **26项／9.4414秒**，均无页面错误；原 HTTP 操作不是 reviewer 的拦截模拟。核显式准备授权、prepared 后预览、完整冻结准备／执行／审查成员及 binding／理由、原生父链、预算实例与期限、完整 source、双摘要创建和原ID读取；旧 v1／v2／v3 与错误父链／准备叶／相对预算拒绝保留。六次实际延迟回复分别覆盖来源与摘要变化的 manifest、预算修改的 preview、关闭换表单的 prepare、改ID的准备读取、跨项目的 preview，旧授权／确认未复活。在途字段按内部控件实际 `:disabled` 核，而非只看 fieldset 的 Playwright 判断。三宽尺寸见 R3；键盘只核盘点→计划和总时间→清理时间两段 Tab 顺序，不称完整无障碍验收。

独立最终 `final-fields-r5.json` **11项／2.76秒**，仅5次真实GET，核 R1／R2、三个 HTML max 已移除；未执行 command 或模型准备。早先23项生命周期与12项销毁模拟仍只属于 r2 的截获响应探针，不能转称 r5 原HTTP验收。home 切换与迟到 create 回复在本片仅静态追踪原 active/current 守卫，没有真实HTTP动态复验。

`http-audit-r5-final.json` 独立核最终 **111份**原 request／response 大小与SHA，追踪数也为111；包含10次成功预览。六次明确准备请求与两次明确创建，各原ID仅一次；其中无效预算原HTTP400，其余五次原准备操作保留 prepared／failed 实态。source 的 prepare 与 create 原服务端200、交付503及后续原ID读取分别核对，没有把503改写为成功送达或自动重发。两份实际 published 合同的全部冻结JSON逐份等于各自原预览；原定义、成员选择／覆盖、父链、source、budget definition摘要／instance摘要与两次create的prepare／preview摘要均相同。`download-audit-r5.json` 核4409B完整授权下载（SHA `6b03819b992cc34e8e60a01308907ce17b6e249e3f93af94932c8006acc0d96d`）解析后等于原第7份prepare输入的definition6。

自身原结构模板最终采用已授权 Codex 回退，run `9eca0959379f4273b805cff3ccc6ee3b`，**93.1586秒／approve**。独立 `self-review-r3-audit.json` 按实际封包索引逐字节核六文件135282B，最终三产品和未改 `ui.js` 与当前相同；完整 prompt139674B、SHA `7f6ddf8bb78bf20e4ada57747edc02af36507e9ed0275e15d990ac9f798802bb` 与实际stdin／协议副本相同，全部祖先与自身instructions／Skill均在实际输入；原结果SHA `575278c081471b54a90080016da33d64e3f5e7fb785d099d63c381fb41c342a9` 相同。初次Claude134.0579秒request-changes、第二次Claude240.5395秒timeout均保留，不能称Claude批准。该调用只审所供文件，不能替代实际页面／安装检查或独立审查。

`closeout-audit-r5.json` 独立只读核最终SQLite：github／gitlab／manual各两份原来源快照（含正文和首次时间）完整不变，三棵原manifest树的全部文件、目录、执行位相同；两fixture Git干净。agent_runs、issue_task_links、candidate_review_links、issue_writebacks全0，两个runtime均无submission／ingress／workspace／request／receipt执行目录；与原HTTP无start事实相符。三组原服务PID＋starttime均已消失，六个原loopback端口连接拒绝；主浏览器与本reviewer命名浏览器全部close回执exit0。作者可访问proc cwd扫描无本片残留、11项不可读仍未验，不扩大为宿主隔离或全部进程认证。

公开[证据索引](evidence/2026-11-14-native-task-console.json)在终核时有 **680引用／33,839,213B**，独立逐项bytes／SHA相符、无重复。终核投影131878B、SHA `244679aef0d3b9b8dbd635eeddb0ea784638d138c337039797eaffe9273f62d9`；原679条与新增未执行发布脚本分列，package／HTTP／产品等公开事实对应私有原件。公开manifest键改为相对路径、交付首段当前状态已纠正，私有原记录不改；随后新写的独立closeout脚本／结果不在该680中，后续追加另核。该索引在此刻仍正确标明独立终核在途，最终状态记账由本报告结论更新。

**最终裁定：需求／行为 approve，结构／维护成本 approve，开放0／0；R1–R3均关闭。** 本片本地验收可进入原普通发布流程。没有执行或证明真实任务模型／Temporal／GPU／质量／性能、原生Windows、完整Forge、F9d／G1、F10d2资料选择；未提交／推送，也未核本片固定远端Ref或自己的必要CI。前片54fcd0b的CI与原审查已单独闭合，不转授本片。
