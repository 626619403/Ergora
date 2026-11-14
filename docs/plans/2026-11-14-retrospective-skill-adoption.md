# F10c3a：显式导出 Skill 候选与原评价采用闭环

日期：2026-11-14；基线 `a60a8f68513a46ef7e6c18add0832f8bcee3eccc`。[F10总计划](2026-11-14-evaluated-improvement.md#f10c后续顺序调整)／[上一片](2026-11-14-retrospective-skill-candidates.md)。本片先让已有Skill候选有可直接使用的出口，再扩记忆／流程；原范围保持。F10c2a自己的CI八job／30必要步骤全成功、原独立CI终核approve／开放0／0，前片发布依赖已关闭。本片最终本地独立审查已通过，接普通发布。恢复时核PLAN、此页、交付、Git和相邻原owner。

## 实际调用与合同

已有`retrospective check`只返回完整候选，用户仍需手工逐文件落盘。新增`retrospective export INPUT RESULT DEST --result-sha256 SHA --candidate-digest SHA`，离线核所选原结果与候选内容身份，再明确导出完整标准Skill目录。它不执行文件、导入库、查询State／实时源、评价或采用。

导出复用原check的单次有界结果读取与完整内存候选，先核两个显式摘要、非null候选和目录名；不重新打开可变结果。DEST必须是新的目录，其末级名称与Skill元数据name相同；拒绝写入冻结INPUT内部，既有／同时出现的目标一概不合并、不覆盖。完整UTF-8原字节与执行位先写同文件系统的私有staging，按原`asset_trees.digest_tree`核目录身份，再原子发布。无法保持执行位等原身份时明确失败，不修饰为成功；失败清理本次私有staging，已有目标保持。

返回原input／result／baseline／candidate身份、目标路径及`quality_evaluated:false`／`adoption_authorized:false`。回复丢失后先检查原目标字节及摘要，不覆盖它或自动重导。导出仅是可供原Skill库导入的文件；check通过、导出成功和模型approve都不是评价或采用批准。

原`skill import`持有版本、父基线和初次head；原`evaluation register/run/compare`持有可信suite和评价证据；原`skills.adopt`持有当前基线／head revision、eligible与理由；原`skill rollback`持有曾活动版本和明确理由。本片不新建评分器、活动head、采用日志或恢复状态机。正候选CLI验收可用明确标注的合成提案与fixture scorer证明合同，不当作真实模型改进／泛化质量或性能效果。

## 结构与复用

`retrospectives.export`是CLI消费的完整顶层用例，候选语义留在此module。标准文件集与内容身份继续复用本片前已有的check及原Skill owner。

原`workflow_definitions._publish_bundle`已有Linux renameat2／Windows不替换目录发布，消费者是manifest恢复和完整组合准备。导出是第二个生产module的同一真实需求：把原具体算法下沉到`asset_trees.publish_directory`，两者直接调用，删除旧私有实现及独占imports，保留原行为。无需另建平台发布器或转发兼容层。原并发空目录回归改在真实导入点注入，继续保护完整组合；不在每个消费者重写一套原子发布算法测试。

## 验收与进度

- [x] 核原Skill、评价、采用／回退、完整输入和原子发布的实际实现与调用者；固定此片合同和独立发布依赖。
- [x] 原导出／共享具体发布器实现；定向18通过／18.41秒覆盖完整文件、LF／CRLF身份及候选导入前后head保持，失败无部分目标与不覆盖已有目标。最终包另验。
- [x] 在原suite补必要回归并保留原并发空目录门禁；完整原工作流在最终五suite核，独立提示的原manifest恢复缺项另补14通过／8.59秒（同r1安装件）。不增suite／CI组或文案默认值断言。
- [x] r1非editable包586／两RECORD594／599／283，安装原五suite140通过／6平台跳过；实际14CLI完成完整合成候选检查→显式导出→原导入→同suite双方评价／比较→明确采用→原回退；原input/result/digest/run/revision与可信scorer身份保留，陈旧采用head不动。收尾与公开原件最终另核。
- [x] 原自身结构模板完整同input：Claude超时保留、授权Codex58.631秒approve；新fresh-context最终本地两轴approve／开放0／0，130原引用、原件和收尾已直接核。
- [ ] 上片CI／原补核完成后普通发布／完整Ref、本片自己的CI与原独立发布及CI补核；不合main。

每步结果写[交付](../delivery/2026-11-14-retrospective-skill-adoption.md)。记忆／流程候选、对应采用合同、F10d页面、F9d／G1、真实业务B3／GPU与完整Forge分别保留。

F10c3a已普通发布`c4aa7acb555a5d55fec7e7a483544834e8afe44f`，18个固定blob／完整远端Ref相同，固定130／发布后134原引用分列。新独立最终本地两轴approve／开放0／0保持；原固定发布补核和自己的CI待，后续记忆候选可先固定本地合同，发布继续等待前片闭合。

F10c3a原固定发布补核两轴approve／开放0／0：18blob／586固定产品、130→134引用及fullRef已核；自己的CI为43553150941，当前在途，与后续记忆候选分开记账。

自己的CI43553150941因Windows20分钟总上限取消，29／30必要步骤成功，installer未完成；原取消保留。后继具体[预算修正与发布依赖调整](2026-11-14-windows-ci-budget.md)不放宽必要检查，使用后继新SHA自己的完整CI；本候选不声明完整CI成功。
