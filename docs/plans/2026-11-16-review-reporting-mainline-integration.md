# BR 主线联合整合计划

日期：2026-11-16。固定实施基线 `d5b58912e4f20c96a52f7c0138b8c7c3d1a97b50`。

## 范围与验收

导入已独立两轴通过的隔离组合精确变更／新增文件、README 及原审查，排除隔离 docs/PLAN.md。保留主线 c1b1 五产品和训练测试；本片唯一测试改动为 tests/test_presets.py。沿既有 DefinitionLibrary／manifest／prepared input／CLI，已发布版本保持不可变。

新非 editable core／SDK 联合安装须核 source／wheel／site 产品字节／执行位、283 reference、core 无 SDK；216 旧资源、既有 manifest／对象／输入保持。运行 BR 原适用 50 用例及新资源／CLI 实际导入，主控 fixture 落定后冻结 tests／examples。禁止改 c1 文档、训练测试、CI、其他树；不重跑 c1b1 总 suite、模型或浏览器。旧 390px HTML 溢出保留。

## 进度

- 已读规则、协议、隔离交付及独立两轴审查；实施前主树干净且 HEAD 为固定基线。
- 28 项精确导入及 d5b 完整 binary patch 已冻结；core／SDK 新非 editable 安装各 663 文件字节／执行位相同、reference 283 PASS、依赖通过、core 无 SDK。
- 216 旧资源／旧对象／manifest／八份输入不变式通过；新报告资源完整 prepared input 与 CLI verify 通过。
- 已冻结 178 tests／examples 与 228 preset data，原 BR 50 项联合安装回归通过（50 passed／208.52 秒）；三个新 preset CLI install／report show 与 verify-input 通过。
- 验证后导入28项及178输入 SHA 不变；本片30文件最终scope／完整patch／正文冻结完成。实施和本片安装验证已完成，自身模板及 fresh 联合审查仍由主控安排，未宣称整体完成／发布。

详见[本片交付](../delivery/2026-11-16-review-reporting-mainline-integration.md)。

主控联合收尾：同一冻结输入实际8项CI／候选精准接缝106.07秒通过；自身原结构模板真实Codex29.200秒approve。两套结果各属自己的命令／JUnit，非单次58项suite。当前等待完整联合fresh-context两轴，提交／推送及自身CI另验；后继服务在隔离分支实施，不改本片安装身份。

私有原件位于项目 ignored `.ergora/checks/review-reporting-mainline/`；隔离历史结果保留原归属。

联合fresh-context两轴已approve／0；本地门禁闭合，固定提交与发布／自身准确CI继续。[独立报告](../delivery/2026-11-16-review-reporting-mainline-integration-review.md)保存范围与限制。
