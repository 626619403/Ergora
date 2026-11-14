# F10b：正式任务明确选择与冻结上下文

日期：2026-11-14；基线 `a2899e84bc174c9abd331a7c9d01f7c7a63297ae`。[F10总计划](2026-11-14-evaluated-improvement.md)。F10a自己的CI43542024437八job／30必要步骤全部成功且原结构轴终核通过；本片发布的上一候选依赖已解除。

## 确定的合同

新增用户 `task-definition-v7`，在v6原预算／单次原生六阶段定义上要求显式 `context`：`root_version`、`memories`（项目内id／revision）与 `skills`（name／活动head revision／digest）。至少选择一项；不自动召回，不接受历史非当前修订或未成为活动head的候选。旧v1–6及原envelope保持原解释。新冻结envelope v11沿原预算、六阶段、创建／恢复／审批／执行owner，不新增调度或状态库。

准备时读取canonical项目记忆与活动Skill。记忆必须是最新、未删除且当时有效的所选revision，复制完整正文／来源／期限；Skill必须匹配活动head身份并核对完整目录，复制所有附件与原执行位。初次baseline是可选活动head，但不称测得改进。

原composition manifest经完整核验后，在原监督准备树内复制其assets，沿 `DefinitionLibrary.revise` 为**同一根id的新显式版本**追加一个来源上下文资源及所选Skill资源。保持原根所有其他字段、子引用、成员路径、grant与limits，不包一层新模板。所有叶继续通过原继承、同名Skill冲突、URI可读、附件交付、容量与输入准入；权限不足明确失败，不自动扩大父／子read。仅临时派生资源，完整新manifest随原prepared／intent归档，不导入全局活动库或改变Skill head。

预览展示原manifest身份、原根与派生根、完整来源资源、所选时刻／期限与原图逐叶材料字节。预览只是观察，创建前必须再次核canonical来源。最终检查放在原SQLite写预留、原task发布锁内、首次持久creation intent之前；过期、更正、删除或活动head变化均拒绝旧选择。不存在持久intent时，不允许借恢复绕过该检查。**已经保存完整intent后**，恢复继续原件，即使后来资料失效／删除／换head；不重编译、不重新选资料、不续预算、不改已开始运行。

CLI／HTTP沿现有 `task prepare / preview / create / resume-create`，无需第二上下文发布入口。图形选择表单属于F10d；本片先交付正式协议和实际材料消费。完整输入读取与离线证据保留标准库路径。

## 归属与新增代码理由

- 新 `task_context.py` 只拥有canonical来源选择及原根资源派生，生产消费者为 `tasks._definition` 与 `reference_task_creation` 的最终来源复核；复用memory、Skill、定义库和manifest，不新建资源库。
- `task_envelopes` 拥有冻结来源资源与新envelope结构的一致性验证，不能依赖应用层／SDK；`reference_inputs` 注册新输入，`reference_workflows` 仅声明继承原流程的新版本。
- `tasks` 沿原schema／预算分流，`reference_task_creation` 沿原prepared／intent与发布锁；不改业务项目、不修改283冻结参考文件。
- 新schema是公开版本接口；不为一处使用增加通用插件、配置注册器或第二套评价／权限抽象。

## 可验收步骤

- [x] 核对原调用链、资源修订实际格式、版本号与继承／发布责任，固定本合同。
- [x] 实现v7选择、完整资源派生、v11冻结验证及原运行消费者。
- [x] 回归预览后更正／删除／到期／head变化、原发布中断恢复、同名Skill／read／容量、旧版本和SDK-free读取；使用现有suite承载，避免新增CI分组。
- [x] 最终非editable包与完整产品／RECORD／283核对，实际CLI／HTTP及库存／计划／work／review输入交付、收尾；合成合同不作为GPU或质量改善。
- [x] 原自身结构模板及新的fresh-context需求／结构独立审查，修复后复核。
- [ ] 更新计划／交付／公开用法，普通提交推送、精确Ref与自己的CI及原独立补核。

每一步将实际命令、身份、失败与未验项写入[交付记录](../delivery/2026-11-14-task-context-selection.md)。F10c复盘候选、F10d表单、F9d／G1和外部B3／Forge条件继续独立保留。

最终r2包577／两RECORD585／590／283保持，安装229通过／6平台跳过／412.30秒；原九job七叶完整75,600B附件与stdin保持，实际CLI／HTTP及三反例按交付所列精确范围通过。原slow-Skill期限窗口已修复，先核Skill再观察memory。自身修后approve38.840秒，新独立两轴最终本地approve、开放0／0；发布与自己的CI尚待。首harness失败及零重复mutation续核分别保留，不冒称首轮无人干预成功。
