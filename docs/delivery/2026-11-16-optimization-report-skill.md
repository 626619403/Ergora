# 优化报告 Skill 与版本化结构模板

2026-11-16。基线 `f8df8af90ae5ad2d9e64047b0b87197ce2bfb432`。资源与必要接缝、fresh-context 两轴独立审查、新非 editable wheel、一次原生合成报告及 Ergora 原结构审查模板均已完成；最终原件复核待根协调。产品资源与测试保持独审时字节，本次仅补状态。未提交、合并或发布；主线 PLAN／循环设计由根维护，本片不覆盖。

## 要求与实现边界

用户要求专门优化报告 Skill，报告直观、比较清楚并逐层递进；可参考指定内部文档的组织方式，仅抽取结构，不包含其中具体优化方法、实验数字／结果或私有业务正文。原件已用用户身份只读读取并私有保存，目录结构为空，实际为表格主导并内嵌原图；公开资源为重新编写、自包含的通用结构，不要求访问该来源。

报告先展示 scope／现状／目标，再完整呈现实际提供的算法、计算依赖、数据流及组件／张量冗余清单，再给 baseline 与可比逐步结果、诊断、候选决定和剩余瓶颈。已有 `training-flow-map` 继续拥有源码分析；报告不重做执行器或采集器，静态图不证明时序／收益。模板为明确的占位示意，没有测量结果。

## 版本、实际消费者与保留合同

- catalog 新增 `optimization-report`，指向 `ergora-evidence-report@2.0.0`，单叶 `root/author` 引用 `ergora-evidence-report-author@2.0.0`。原 `evidence-report` catalog／`@1.0.0` 两包及全部旧 catalog entries 保持原字节／配置。
- 新作者完整保留原通用 `ergora-evidence-report` Skill 字节，沿其来源、静态 HTML 安全与 `markdown/html/sources/limitations` 四字段 response 字符串；新增专门 `ergora-optimization-report` Skill 和占位模板。模板另声明为 context，完整正文直接进入实际冻结 prompt，不仅是未消费的附件。
- 原 `workflow_definitions.install_preset` → `DefinitionLibrary.import_bundle` → `preview` → `prepare_manifest` → `prepare_input_from_manifest` → `inspect_input` 是实际加载路径；原完整 bundle owner 保留文件、目录、摘要与执行位。没有新增 Python 产品实现、schema、数据库、MCP server、后端或工具权限。
- 根与叶均为 `read=[definitions]`、`write=[]`、`shell=false`、`network=[]`，`runtime=proposal-leaves`。报告不采集证据、执行前驱、运行实验或授予采用／release 权限；原六阶段与候选绑定证据 owner 保持。
- 可比范围保留阶段／精度／卡数／有效 work／更新语义／样本窗口与不确定性；不同范围分表。每行给本项配置与机制，完整保留继承组合，组合收益不拆造单项增益。MFU 仅在有适用口径时呈现；原图缺字节或缺测量须直说，实测／估算／假设／未验及负结果可追溯。

准确资源身份：

|资源|版本|完整包 digest|
|---|---|---|
|`ergora-evidence-report-author`|2.0.0|`1e67f2a71986cf37601fcc5671e6f4bf5768da0749caf15019883b06186aa70c`|
|`ergora-evidence-report`|2.0.0|`7792b1d05fa3684897f82444db4e6f43dca7607ee434a56ec4596a671df47ad5`|

## 实际检查

1. 复用既有 `tests/test_presets.py::test_readonly_analysis_presets_freeze_complete_material_without_changing_training_versions`，加新 preset 参数，并把旧报告根纳入保留身份对照。源码执行 **3 passed in 1.77s**；没有添加匹配 heading／措辞的测试。
2. 用候选源码导入执行完整包 inspect／import、幂等重复安装、旧根字节与全部旧 catalog 对照、原 preview、manifest freeze、删除原 library 后的冻结 input 准备／读回。两包全部文件 SHA256／执行位与冻结副本一致；通用 Skill 与原版字节一致。模板全文、两份 Skill 和祖先材料都进入叶 prompt；来源为 `root` 与 `root/author`。material **24,489 bytes**、含任务 prompt **24,667 bytes**。
3. 通过候选源码 CLI 实际 `composition presets` 与 `composition install-preset optimization-report`，列表含 34 entries，新根／摘要与库读回同一，`execution_authorized=false`；不是借用另一安装的旧 catalog。
4. 新增／变更文本按 UTF-8 解码、无 NUL；内部来源 URL／token 未进入公开材料。原图／表格正文与其元数据保留在私有证据中。相关相对链接、Python 示例语法与 `git diff --check` 单独核对。

原始 manifest、preview、冻结输入、CLI 输出、验证脚本／命令及 tracked／untracked 文件 manifest 由本片私有证据目录保留，交接时给根准确位置与摘要。公开记录不存机器专属路径或内部原文。

## 独立审查与新安装验收

[fresh 独立审查](2026-11-16-optimization-report-skill-review.md)已完成：需求符合性／可维护性两轴 **APPROVE，开放 finding 0**。reviewer 独立新 preset 冻结接缝 **1 passed, 2 deselected in 0.62s**，并核原 33 catalog entries、227 个旧资源及完整冻结资产。本结果只认证其已记录的资源／冻结范围；reviewer 编写的合成演示没有替代下述原生调用。

- 完整固定 **810** 项源码／数据／测试／脚本／CI／构建元数据输入后，用已有构建环境制作新 wheel，以缓存依赖离线装入隔离新环境。wheel SHA256 为 `9743064d74a72d1836570efc58dc66f8d53d00447da7cf0b060160181fdff82e`。
- **678** 个运行时文件的字节／执行位与该候选源码及 wheel 全同，原 **283** 参考文件保持；实际导入来自新 `site-packages`，不是 editable 或源码回退。依赖检查通过，PyYAML 6.0.3／jsonschema 4.24.0；实际 `temporalio=false`、`mcp=false`，本次为 core 安装，不声称完成 SDK 矩阵。
- 新安装实际 CLI `composition presets/install-preset optimization-report`、完整 bundle 导入／重装／preview／manifest／冻结 input 读回及完整模板／祖先 prompt 消费均通过。810 项输入在运行后重新核身份保持。
- 初次私有包校验脚本将源码协作文件 `src/ergora/AGENTS.md` 误计为运行时文件，触发断言；原失败和脚本保留。修正校验集合为包 Python 文件及 data 后，沿同一已构建 wheel 继续；没有修改产品或重新构建候选来覆盖失败。

## 同一新安装的原生模型检查

两次均显式选择 Codex、配置 `gpt-6.1-sol/medium`，`codex-cli 0.167.1`，凭据只引用环境；每次模型预算 300 秒，无自动重试／续调，不称异后端成功。CLI、manifest、input／prompt、实际 stdin、native command／stdout／stderr、原结果及 `inspect-run` 完整观察均私有保留。

|检查|准确原 run|实际终态与时间|身份与结论|
|---|---|---|---|
|`optimization-report`／`ergora-evidence-report@2.0.0`，`root/author`，原 CLI text-only|`0d21cc331ece424e963210d2231a05d5`|exit 0，succeeded，149.034645 秒|实际 stdin 29,421 bytes；SHA256 `1912dade8d5eef909f271191729735e0a53875c91e9ee259ad9de703e4e653e3`。与冻结 prompt 相同，完整任务和全部资源在场。原结果 SHA256 `45e13b401a4d9e264fab7b2fbae71d615b716db43a39f1f5ca68f1d1f73aed36`。|
|原 `ergora-structure-review@1.0.0`，`root/review`，同安装原 CLI text-only|`0125866f2f144da787769f3cc711f517`|exit 0，succeeded，39.446412 秒|实际 stdin 354,120 bytes；SHA256 `0e2c25b3161a744a1f5d1ea81c9b909b83fa416dfc4b739776d9267aed62142d`。原结果 SHA256 `7d0bf68bd0712da9969feb2429c82cd16184c3af01b805f79005958e350aac7b`；模型两轴 APPROVE，无具体 finding。|

报告输入是明确标注 **synthetic** 的完整小型夹具，包含 baseline／双改动组合候选、缺单项消融／质量和一个硬件／有效工作不同的范围，不引用内部参考的方法或数字。原四字段响应 shape 通过；Markdown／HTML 五张表共 68 单元格在格式归一后相同；静态 HTML／CSP、无主动 URL 或外部 SVG 引用、来源脚本文本转义通过。作者逐项读回确认：组合收益未拆分、完整配置可恢复、quality／消融／MFU 缺项明确、不可比范围分表且无跨范围加速比、采用仍 pending，夹具自身输入 shape／有效工作映射的缺口也被保留。上述检查不是模型自检，也不把夹具数值当成实测结果。

原结构模板实际读取原 14 作者文件全文、独审记录、完整 tracked／untracked 差异、owner 协议及实际验证摘要，共 19 个完整范围文件、298,466 bytes。独审后仅本交付状态变化，未将状态修改冒充产品新版本。两次原生调用各采样到 2 个自有进程，其原 PID／starttime 身份终核均不存在；这是已采样进程的收尾记录，不承诺未采样进程的覆盖。

## 尚未验收

最终安装／原生产物尚待同一独立 reviewer 只读复核，由根协调，不为状态记账递归审查。单次原生合成报告只验证此次调用与检查到的输出属性，不认证模型稳定性、事实准确率、浏览器布局、真实 benchmark／GPU／训练质量或优化收益。未启动服务／GPU／业务训练，未改全局依赖；新 SDK 矩阵、CI、组合采用与发布未执行。原 @1 结果不转授 @2，模型 APPROVE 与真实证据验收仍分账。
## 根接纳与普通整合

根已核最终15文件scope，除原review报告的append-only最终接纳节外，逐项bytes／SHA／执行位均与final-r1原件一致；review新SHA256 `5723d25abbf83bdb4f43f79558d25a19a760286b7a0c6d32424086bb53371450`，其原7,416B前缀仍为b2faf6…，未覆盖原冻结报告。

准确源码提交 `71510045bccc94989002272a2fa5770d84406f0f` 已普通无冲突合入开发分支 `d1e19a8a86863c82123e73fc2e6f834a2a933b60`。合入src tree `5dcc41b5e15f55ddc27bb01db916fa50a1acb9d6` 与候选同一，preset测试同一，scripts／CI／pyproject未变，没有merge-resolution产品改动。本地源码／新安装／原CLI／原结构模板及同一fresh最终原件接纳门已闭合；普通发布和该准确公开候选自己的CI仍待分别核验，不借旧9f3绿CI。M6执行效果仍仅在隔离实现中，未由本报告模板开放。
