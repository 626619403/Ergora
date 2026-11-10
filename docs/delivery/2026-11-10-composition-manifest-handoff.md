# AC5 C5a：当前静态预览的完整manifest交接

基线 `a2c89a5b4b5ca49bf0c3f28a4f35efaec539bd3c`；[C5计划](../plans/2026-11-10-composition-handoff.md)拥有本片范围。C4b.2自己的CI与原评审精确交付已终结。本片完整本地出口通过；普通提交、自己的CI与精确远端交付待核。

## 实施前核对

原`prepare_manifest`/`_prepare_bundle`拥有完整树、原资产和原子不覆盖发布；`inspect_manifest`从原附件重编译并核完整身份，不要求源定义库或今天的后端准入。原`tasks._composition`已经重新核manifest、当前后端/权限、逐叶override、diversity与work assignments；当前页面只构造schema-v1，正式选择留C5b。

隔离原owner设计探针中，治理/大变更/训练manifest分别31/37/22文件、73698/95918/49141字节；原preview完全相等，源库移开仍可核验。只作为设计证据，不计C5产品、HTTP、页面或任务验收。初探针误读返回字段的准备失败保持，未修改产品。

本片新增用例固定当前preview摘要并持久保存原完整包；CLI/HTTP复用，页面显式保存与按原摘要只读确认。没有正式任务、批准或执行副作用。以下记录分轮保留实现、运行验证及独立审查，终态见末段。


## 实现与安装检查

四个产品文件已接入：workflow定义用例复用原完整包发布/核验；CLI增加`freeze-manifest`/`show-manifest`，HTTP增加显式保存与按摘要读取；定义页保存当前preview并以home/原preview对象身份保护迟到结果。新增两个合同测试覆盖摘要绑定、并发/重试不覆盖、损坏拒绝、CLI/HTTP身份及无活动库的历史读取。没有新schema、依赖、数据库或CI。

R1非editable首轮43项中41通过、2失败，分别发现新用例取出未带defs上下文的schema引用，以及HTTP的id关键字与identity形参不符；完整原trace在当时工具回执，另存结果摘要，没有独立stdout文件。修正schema取实际digest定义、HTTP显式传参后，R2新安装只补两受影响项：2通过，pytest6.39秒/驱动7.98秒。41项未变邻居不重复；不把R1整体改称通过。

R2离线构建/新venv/非editable安装7.13/0.04/4.32秒；437源/wheel/安装文件、两份RECORD与283冻结身份通过，wheel SHA256 `d575678b1120649561efcd4e1dd8b44ed40ab3519654be51b6834db42e097e40`。JS语法通过。此安装检查阶段后继续真实页面及独立审查，结果见下文。


## 真实页面与原件

R2实际安装页面15.33秒旅程通过：三域16/19/9实例，键盘明确保存/按摘要读取，刷新后重新预览读回原完整包；未应用版本字段保持。受控丢弃一次已成功保存的原HTTP回复后，页面保留原摘要，随后只读查询找回同一包；三个真实延迟的原保存回复经requestfinished及页面帧后核root/grant/home切换不恢复旧结果。比较两组合后保存仍指当前所选根；tab往返保持当前结果。1440×1000与390×844等待原图resize后宽度分别1440/1440、390/390，两截图已实际查看，仅证明所截保存区域。

首旅程3.87秒在第一次保存后失败，原因是驱动用JSON键序判断相等，原manifest排序与原preview不同；修正为按字段核根身份，产品未改。首失败与完整驱动保持，不能改称通过。离线核94对原HTTP字节/摘要，12份成功preview及14份成功manifest回执逐份等于原owner；18种实际静态资产等于当前源，48棵完整旧对象树保持，两个home的项目与agent_runs均为0。浏览器及两HTTP服务已关闭，三份采样HTTP身份均消失；浏览器PID仅来自CLI启动回复，未记录starttime，不作同等身份保证。

页面阶段后的实际自身模板、完整读取与独立审查结果见后文。自然BFCache、跨浏览器、C6容量、正式任务v2选择及六阶段运行未由本片新增验证。


独立审查指出计划初稿把空目录称为“目录身份”过强：原`asset_trees`摘要仅绑定文件路径/字节及执行位，空目录正常复制，但稳定增删空目录不改变digest。当前沿用已有公开身份合同，已澄清本片计划与手册，不默改旧摘要或引入新格式；损坏拒绝限原完整核验所覆盖的文件/定义/材料身份及稳定读取。源对象保持的48树检查另包括实际目录清单，不转授manifest目录身份保证。


## 实际自身审查与完整读取

本片实际使用非editable内置`ergora-structure-review`，证据修订1.0.81；通过新增freeze用例保存完整审查包，移开活动定义库后从包准备只读输入。Codex/gpt-6.1-sol/high，run `e7cf62b73ef34833b610e8bf5268170b`，160.37秒succeeded/approve，原结果分别给出Spec/Standards approve，外层CLI退出0。结果SHA256 `53a56620aae84fe73ecb77896c3df7f33cdd08f53818e7b3d09dc1d5d7b36bc5`。这是已授权Codex回退的独立上下文，不宣称不同模型独立或正式owner批准。

原manifest/prepared/actual/stdin/protocol/MCP/result身份通过；全部五scope完整读取。314712字节候选有14个连续成功UTF-8页直到null，1个base64窗口在原offset缩小重试，无失败read；13份冻结全文及六份产品/测试源码保持。模型读完整源码/测试/驱动与明确省略大map的身份绑定投影，不冒称看过被省略的94HTTP/437文件map原件；原独立主审已单独核。完整交付不证明理解质量。四个运行期间采样owned身份均gone。

后端自报input1141681（已含cached1011200），output2893，另报reasoning1307，不重复叠加；不是账单或容量性能指标。本片新独立两轴实现审查开放0，C5a-SP1目录措辞已澄清关闭；完整最终候选及上述模型/公开投影的原独立两轴补核通过，见末段。

公开原件身份与投影：

- [页面原旅程与94HTTP审计](evidence/2026-11-10-composition-manifest-handoff-browser.json)
- [安装包及分轮回归](evidence/2026-11-10-composition-manifest-handoff-package.json)
- [实际自身审查与结果](evidence/2026-11-10-composition-manifest-handoff-self-review.json)
- [全部scope与连续读取](evidence/2026-11-10-composition-manifest-handoff-reads.json)
- [采样清理与自报用量](evidence/2026-11-10-composition-manifest-handoff-cleanup-usage.json)
- [桌面](evidence/2026-11-10-composition-manifest-handoff-desktop.png)与[窄屏](evidence/2026-11-10-composition-manifest-handoff-mobile.png)原截图

投影列明私有原件字节/摘要、路径和端口替换及省略；完整原件私有保留，两PNG为实际截图原字节。正式任务选择、writer信任页面及原六阶段旅程分别属C5b/c，本片不授予完成。

## 本地验收终态

新fresh-context主审与原Spec/Standards两轴已完成完整22文件最终候选补核，开放finding均为0，本地出口通过；[原评审报告](2026-11-10-composition-manifest-handoff-review.md)保存实现审查及最终增量的各自范围。原件另核437源/wheel/安装身份与两RECORD、94HTTP/14manifest/48旧树/18静态资产；模型全部五scope及连续读取、13份全文附件、五投影所引14原件、两份原PNG字节与实际目视通过。目录措辞finding保持准确关闭，原R1及页面首失败不回写。

这里只关闭本地出口；待普通提交/推送后由原主审核精确Git文件、包及283冻结身份、一次独立HTTPS远端同SHA，以及本提交自己的双OS七必要CI步骤。C5b正式选择与C5c纵向六阶段继续原计划，不重复本片已过页面、模型和回归。
