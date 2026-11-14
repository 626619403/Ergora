# F10d2：正式任务的记忆与 Skill 选择页面

日期：2026-11-14；固定基线 `0a311eeb2a46d0db48ec44515a8413239e0c772c`。接[F10d1原生表单](2026-11-14-native-task-console.md)，对应[F10总计划](2026-11-14-evaluated-improvement.md)的资料选择旅程。前片已普通发布，自己的CI八job／30必要步骤及原独立两轴终核均已通过，发布前置依赖已满足。本片仍需自己的最终交付终核和发布／CI，不借前片证据预批。

## 原 owner 与范围

`task-definition-v7`／input11、`task_context`、原prepare／preview／双摘要create已经拥有精确来源、根资源派生、完整祖先材料、有效期／head变化检查与原意图恢复。本片只补正式任务页面的显式选择，不改上述合同／资源库／权限／预算／评价／采用，不把选中记录直接拼进prompt。

沿原`task-composition.js`收集可选context，原`tasks.js`唯一调用者按有context的原生任务产生definition7，可选source共存时仍保留7。未启用资料选择保持原definition1／2／3／6。原生字段内增加“仅继承模板资料／追加项目资料”，默认前者；全部父模板资源始终继承，不提供移除或扩大权限的入口。用户明确填写派生根精确版本，选择当前有效memory的id／revision与活动Skill的name／digest／revision。目录只代表读取时快照，原prepare／preview／首次publication会再核当前来源和完整附件。

读取沿现有`GET memory-catalog`。Skill head目前只有完整dashboard返回；该路径还会调用工具诊断并读取无关账本，因此增加实际页面需要的轻量`GET skills/heads`，直接调用原`skill_assets.versions(heads_only=True)`，不建新仓库或索引。目录由用户明确读取；失败不自动回退或把旧选择当新目录。显示完整memory正文／来源／有效期与不可选原因，Skill完整精确head身份；资料选择数量可见，上限和容量仍由原schema／资源准入核对。Skill资料模式需求由原owner拒绝，不自动换后端／扩大权限／截断附件。

沿原sequence、active与输入变更失效规则，处理迟到目录／来源切换／manifest变动／对话框销毁／项目切换；刷新目录后须重新明确选择。原授权输入下载包含完整context，准备读取与创建仍使用原身份，未知操作不自动重发。冻结预览增加原context来源、根派生和完整附件元数据，显示实际服务端结果，不用当前目录补写历史。

## 可验收节点

- [x] 核原v7／input11、当前两个JS owner及memory／Skill读取路径，固定范围和新轻量读入口的实际消费者。
- [x] 实现原owner中的可选资料表单／原v7选择、轻量head读取、冻结展示；旧入口与原服务端准入保持。
- [x] 最终非editable包／两RECORD／283与相关原suite；实际浏览器走原HTTP：显式memory＋完整Skill→prepare→preview→双摘要create，准确source/root身份，旧无context分支保持。
- [x] 更正／删除／到期／head变化／错误根版本等原准入反例、失败保留输入、目录迟到／来源切换／销毁与跨项目；原HTTP只发送明确操作，三宽／键盘、完整下载及进程／端口／浏览器收尾。
- [ ] 自身原审查模板、新fresh-context独立两轴、finding修复与终核；普通推送／完整Ref／本片自己的必要CI及原reviewer终核。

每个节点写[交付记录](../delivery/2026-11-14-task-context-console.md)和[当前计划](../PLAN.md)。本片不关闭复盘候选／评价／采用／回退完整页面旅程、F9d／G1、真实业务／GPU、完整Forge或原生Windows模型验收。

最终本地安装／实际页面与原HTTP／自身模板、新fresh-context两轴终核均通过，开放0／0，R1关闭；875份固定引用保持。普通发布、完整Ref、本片自己的CI与原reviewer后继补核仍待，最后节点未提前勾选。

普通发布6b7ebcc／16blob／完整Ref一致，固定875／发布后879原引用；固定发布及自己CI的原reviewer补核继续单列。

自己的CI43563900923已获原reviewer终态两轴approve，八job／30必要步骤成功，开放0／0；完整记录见原交付与评审的CI终态补核。
