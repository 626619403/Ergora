# C5b 正式任务组合选择

基线 `f68d7390e0e65f8045158cb1d0270c4057c7a74d`，分支 `refactor/architecture-foundations`；接续[C5总计划](2026-11-10-composition-handoff.md)。C5a本地出口通过、已普通推送，自己的CI与精确远端交付已终结；不转授本片。原tasks._composition、WorkDelivery、task_creation保持唯一所有者。本片开始实施。

1. 保留项目角色schema-v1入口；组合schema-v2显式输入已保存preview SHA，通过原GET material=true核完整包。暂不加未验元数据列表；读取不授予正式运行。
2. 从返回图选择review工作流与可选work工作流。review模式text-only/task-mcp、dag-v1显式；work固定原workspace-task-mcp协议。
3. 从当前input.work_units显式载入assignment选择器，保留原输入及手选；unit/path/依赖精确关系只由原WorkDelivery核验。
4. 沿定义或逐叶覆盖后端；复用组件configuration schema，并抽取到实际有项目绑定/逐叶覆盖两消费者的小型字段模块。所有覆盖要求理由。不得将定义中声明的current-container当自动信任。
5. 每writer的current-container声明不能被静态定义自动授信。页面要求为writer显式覆盖后端、填写理由并选择该后端支持的执行边界，采用原配置schema，不按工具名分发；不额外添加与原sandbox字段重复的授信开关。原owner拒绝不支持的模式/非Linux可信绑定。审查默认prefer-distinct，同后端须说明理由；保留require-distinct及allow-same现有合同。
6. 使用原sequence/creationLocked/原ID恢复。组合字段变化撤销原预览；慢manifest/preview/create回复不得恢复旧选择。preview只编译，create只发布。
7. 非editable包/283冻结身份；实际浏览器覆盖两开发域schema2与原schema1、原owner拒绝、逐叶字段/信任/理由、草稿/输入保持、迟到回复和丢创建回复的原ID查询；不增加第二份编译器或重复单元测试。
8. 两份手册及USAGE/架构/PLAN更新；自身模板实际审查、新fresh-context独立两轴；普通提交推送/本候选CI/远端核。C5c另做两域六阶段真实运行，训练保持proposal范围。

新文件所有权：binding-fields.js给tools.js和task-composition.js共同使用，只处理已有schema支持字段的展示及取值；task-composition.js拥有较完整单一表单子流程及异步读取生命周期，tasks.js继续拥有整体合同创建/未知恢复；无新后端API/schema/数据库/依赖。

## 状态

- S0：原所有者/两开发域静态准入探针已读；不计正式任务或运行验收。
- S1：页面组合选择、逐叶字段复用及生命周期已实现；四JS语法通过。
- S2：R3非editable包439文件/两RECORD及283冻结身份通过；实际两域schema2及审查组合创建、原schema1/切回、拒绝/配置保留/未知恢复/迟到回复及144HTTP/48原对象保持通过，分轮驱动失败与产品修复保留。
- S3：实际自身模板167.84秒request-changes，完整五scope/244105B连续读取已核；新独立完整15文件两轴Standards0、Spec两P2均已最小修正。R4仅首修正包无行为通过；R5包439/283及受影响实际页面2.94秒/22检查、30HTTP/旧记录保持通过；实际自身复核79.67秒approve/五scope与143890B连续读取通过，五公开投影/两原截图已发布。完整23文件独立两轴/全部证据终核和本地出口通过，SP1/SP2/ST1关闭、开放0；精确提交/远端/CI待验。

[C5b交付记录](../delivery/2026-11-10-task-composition-selection.md)按每一状态更新。仅本片创建入口，不声称C5c六阶段或项目全部完成。
