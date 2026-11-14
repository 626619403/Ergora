# F10d3b2：原结果检查与完整复盘候选导出页面

日期：2026-11-14。接 [F10d3b1](2026-11-14-retrospective-preparation-console.md)；实施基线固定为其普通发布 `f7a4d28e82f2db99245885eaa24229299f7f73d7`；完整Ref已核，前片自己的CI及原固定发布补核分别跟进。原reader可选身份／六条薄HTTP／原view结果与导出表单已实现，最终r1安装213项／实际页面94＋21／CLI与原件收尾已通过，已完成最终本地独立终核，准备普通提交／发布；不继承前片包／测试／CI。每步更新本文件、所属交付与 [PLAN](../PLAN.md)。

## 行为与原调用者

已有三个 `retrospectives.check*`／`export*` 家族，由原 CLI 使用；Skill／memory 通过同一次 `_read_proposal` 保存完整 input、原 task、原结果字节摘要与候选，workflow 通过原 `_workflow_proposal` 私有 scratch 的 restore／revise／compile 校验。页面应直连这些 owner，读取原完整结果并明确导出，不运行模型、可信评分器、正式 import／save／采用或回退。候选为 null 是有效结果，不能构造空候选来导出。

HTTP 项目路径、显式选中的完整 input digest、结果文件 SHA 与导出候选 digest 必须绑定同一次原 owner 读取。不能在 web 先 inspect 一次，再让 check／export 重读另一份 input。为已有原接口增加可选的项目／input 身份约束，并传到共同私有 reader，在该次检查取得完整 input 后核身份；原离线 CLI 默认行为与 schema 保持，不增加 State 或后端准入。每个方向保留原专用检查／导出，不新增目标注册器或第二状态机。

## 小节点与验收

- [x] 固定前片发布基线、实际 diff／caller，复核原函数和已有离线测试。
- [x] 在原 input reader 内核可选项目与 input digest；三个原 check／export 传入同次上下文。新增必要回归，证明结果／候选身份相同仍不能换项目或换 input；原 CLI 不带新约束仍可离线复读。
- [x] 原 web 增加三条薄 check 与三条薄 export POST；共享传输字段，导出必填结果 SHA、input digest、候选 digest 和新目录。所有源／格式／容量／不覆盖／scratch cleanup 仍归原 owner。
- [x] 原复盘 view 内新增结果操作表单。明确选方向、完整 input 目录与 digest、原结果路径与 SHA，然后检查，显示并允许下载完整原检查对象。输入改变或读失败立刻使旧检查不可导出；迟到旧读／已卸载 view 不恢复旧状态。
- [x] 有实际候选后，用户明确输入新目录并提交导出。执行中防重入，保留原提交目录；失败或丢回复不自动重发。来源变化中的完成结果标为上次检查，不能冒充当前来源。完整文件仍由原 exporter 原子落盘，不在 JS 拼接候选或写入定义库／memory／Skill head。
- [x] 最终非editable wheel／两RECORD／283，运行受影响原suite。真实浏览器／HTTP三方向正候选与null检查、完整下载及原CLI同一、完整导出／mode／空目录、跨项目／换input／换result／错candidate／已有目录与input内部目标拒绝、延迟响应／来源变更／切页、三宽及原件／收尾；未验排列单列。
- [x] 使用自身原结构审查模板，保存完整实际输入／继承资源／原后端回复；新fresh-context需求／维护性两轴终核，修复实证finding。
- [ ] 前片自身CI与原独立终核闭合后普通发布当前分支；完整远端Ref、本片自己的CI及原reviewer发布／终态补核分别记录，不自动合main。

## 后继与限制

随后接原 `composition run-input` 单叶调用页面，再连接可信评价、明确采用／回退旅程。现有执行层的异后端偏好、祖先资料累加／父权限上限、完整资源容量拒绝及unknown对账保持。完整F10、F9d／G1、真实B3与完整Forge C2仍按各自条件验收。

实际验收更新：r1非editable603／RECORD611／616／283、原五suite213通过／118.08秒，页面94＋21项、71原HTTP／5迟到／1丢回复、3完整实际下载／6原CLI和6页面导出目录同一、三宽／原件／SQLite只读／收尾均通过；自身原模板Codex45.702秒approve，新源码两轴approve／开放0／0，最终本地补核待。

最终本地独立终核approve／开放0／0，原480＋10独立证明＋5发布调用器共495引用；本地提交可先固定结果，外部普通push仍等待前片自身CI原reviewer终核，自己的CI与发布补核不预批。
