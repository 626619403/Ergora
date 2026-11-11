# AC5 C5b：正式任务的组合选择

基线 `f68d7390e0e65f8045158cb1d0270c4057c7a74d`。范围及验收见[本片计划](../plans/2026-11-10-task-composition-selection.md)。本片实现与独立本地出口通过；普通提交及自己的CI/远端精确交付待验。C5a精确交付已终结，不转授本片。

## 实施前核对

现有task schema-v2已支持manifest完整身份、审查/执行子树、原work_units分配、逐叶binding/reason与diversity。原tasks._composition负责manifest重新准入、实际后端模式和信任，原WorkDelivery负责成员完整覆盖/分配和传递依赖；原创建流程负责revision/预览摘要、intent-before-publication及原ID恢复。页面原入口只发schema-v1。新页面复用这些所有者。

两开发域的私有静态探针在缺writer信任时都由原owner明确拒绝；显式可信Linux设计binding后准入。这只是无项目/无调用的设计探针，不是本片正式预览、创建或六阶段验收。

为减少新表单规则，后端选项来自现有bootstrap组件configuration schema；binding字段由项目绑定和逐叶覆盖两个实际消费者共用。组合保存后的preview摘要作为显式读取入口，不新建索引或任务账本。训练优化保持独立只读proposal范围。

## 实现与安装

四JS产品文件：tasks原创建器增加明确来源；新task-composition负责单一组合表单子流程；binding-fields从tools提取，两个实际生产消费者沿同一catalog字段合同。页面选择只构造原task schema-v2，没有新接口、数据库、后端分发或调度。writer要求显式覆盖及原schema中的执行边界，不增加第二个授信开关。两手册、USAGE与架构已更新，运行与审查状态另核。

R1离线build/venv/非editable安装7.72/0.04/5.12秒，439源/wheel/安装文件及两RECORD一致，283冻结资产保持；wheel SHA256 `e61e2f554326ea576b345202dc8422d6b2ef423be82eeb18f9c4f604314b4c08`。浏览器fixture首准备因驱动给新草稿revision=None而失败，改0后两home准备完成；产品未改，失败目录保持。默认系统Chrome启动因该可执行文件不存在失败，随后沿已有headless Chromium配置启动，不新增安装或改变产品。均不计页面行为通过。实际页面、实际自身模板与新独立审查尚待完成。

R1页面首旅程75.12秒在草稿选择处因驱动使用getByLabel精确匹配包含option正文的隐式label而失败，改用现有select的name定位；第二旅程2.16秒抵达原预览后，驱动误用非数字工单ID，被原编译器正确拒绝。两原失败保持，尚无成功创建，不归为产品通过。工单字段标签改为原合同的正整数IID。另在实施自查中修正读取失败的配置保留：新摘要/正在读取使旧配置不可提交，失败保留输入和可见旧配置，同摘要成功重读恢复原手选；不同完整包才清空实例配置。产品改动后新建R2包，后续只验其实际行为。

R2包439文件/两RECORD/283保持通过，SHA256 `847292fd659a38d013f87c2c67488068e70e0492935f534f1016aa040fb80f00`。实际第三旅程3.72秒已通过schema-v1完整预览/发布、组合读取/手选保留/失败禁用/同包重读及缺writer信任拒绝；在测试不支持的writer时，另一未授信writer先被拒绝，驱动对错误文本的预期顺序错误而失败。第四补段32.64秒将其他writer先显式授信后，原owner准确拒绝mini-swe的workspace模式；接着组合预览服务端成功，但页面仍从旧spec.request取基线而抛错，属于产品错误。修正为读取共有compiled.spec基线，并在预览增加实际每成员的binding/mode/reason与完整policy/diversity详情；不将R2整体称通过。创建/未知恢复和余下页面旅程留R3受影响补验，既过行为不重复。

## R3受影响页面与原件

R3 build/venv/非editable安装7.40/0.04/4.69秒，439文件/两RECORD及283冻结通过，wheel SHA256 `f1a62824e0db346d661d3183bb239f1dcd2cb521725d229f8ba1dbf4c3a6d120`。第五旅程5.49秒已核组合预览展示、切回schema-v1不混入组合、require-distinct与同后端缺理由拒绝、显式理由回退以及输入变化后的真实迟到预览不恢复。首次创建实际成功且回复受控丢弃，驱动随后误用fieldset的isDisabled判断而失败；原断点保留，产品不变。第六旅程7.48秒从原未知状态继续，用实际任务控件核禁用、按原ID查回同一已发布合同；未重复创建。随后大变更组合与独立只读审查组合各自预览/创建通过；三个真实迟到manifest回复经requestfinished及双帧核摘要/来源/关闭再换home不恢复旧配置。共用字段表单的数字、数组和枚举保存沿原项目binding接口成功，未认证或调用这些演示工具。

R2已过的legacy合同创建/手动配置保留/缺信任拒绝与R3补段分别保持，不称整轮全部通过。两个home的隔离fixture沿同一原登记与冻结对象继续，未重建旧任务。离线核三轮144对HTTP原请求/响应字节与摘要，9次成功manifest读取等原inspector，9次成功任务预览等原信封与compiled.spec投影；4份实际发布记录逐份核原intent及全部7文件等所接受的原preview，其中治理组合只有一次POST，原回复确被丢弃。48棵旧对象树及目录清单不变，A项目不变，B项目仅两次明确binding保存至r3；两home均无Agent运行或提交/请求/回执/workspace目录。本片没有六阶段执行验收。

1440×1000/390×844下页面宽度1440/390，对话框宽度688/352，均无横向溢出。两原截图已实际查看，仅证明所截选择区；窄屏原生选择框显示不下的长路径仍在原option/服务端精确preview内，不能推为全页容量或全内容目视保证。浏览器及三轮HTTP/proxy已明确关闭，12份原采样PID/starttime身份随后均不在；只陈述采样范围。自然BFCache、跨浏览器、Windows实际页面与C5c运行仍未由本片证明。实际自身模板与新独立两轴待验。

## 自身审查与受影响修正

实际 bundled structure-review 的1.0.82证据修订通过原task-MCP启动，167.84秒返回`request-changes`：Spec发现`loadTemplate`在模板GET前清空已编辑JSON/所选草稿，读取失败会丢输入；Standards未报告结构/复用/冗余测试或CI问题。五个scope的完整UTF-8连续读取及244105B附件原字节、manifest/input/native/result身份已离线核对；附加两次重复读取保持，不把交付字节解释为理解或正式审批。该发现已确认可达，最小修正将input和draft的替换移至当前成功回复内，保留原invalidate与sequence。原R3页面结果保持原候选范围；R4非editable包、失败保留/成功替换/迟到回复补验及模型复核待验，新独立两轴仍进行中。

新独立初审完整15文件两轴：Standards开放0；Spec另发现成功重载work_units清空原手选（C5b-SP1），并确认模板读取丢输入（SP2）。SP1最小修正为同manifest/work下按unit ID保存手选，新增留空，原不同包/work清理和WorkDelivery准入不变。R4只有SP2修正，构建9.74/0.06/5.42秒、439/283身份通过，无页面或模型复验；R5同时含两修正，构建6.87/0.04/4.45秒，439文件/两RECORD及283冻结通过，wheel SHA256 `5b0e11fd31baa068a349493e4de9d996d528f3ca5e44d43522b2b894e77fae33`。R5初次私有HTTP启动因stdin非交互EOF退出并清理，未运行页面；改交互启动后复用原home继续，不改产品或夹具。

R5受影响实际页面2.94秒/22检查通过：模板失败逐字保留JSON和草稿、成功替换、原回复在新编辑之后抵达不覆盖；分配重复/增删/重排按ID保持、新增/重新引入已删除项留空、坏JSON失败保持、换work及切回不复活旧分配。失败是驱动在实际原GET200之后明确注入client503，未冒称服务端503。30对补段HTTP原字节、1份完整manifest和所服务R5资产已离线核，全部产品请求GET；两home原repo/合同/定义/manifest文件与清单/项目记录及零Agent保持，四份实际采样进程明确关闭后不在。原144对/4合同/48树没有重放或转授为R5整轮通过。实际自身模型复核与原独立审查续核待验。

## 修正后模型与公开证据

1.0.83证据修订用原实际结构审查模板复核，79.67秒`approve`，Spec/Standards均认可两修正且无新增finding。143890B附件包含四完整产品源、原request-changes及受影响驱动/原结果；全部五scope完整读取，附件6个连续UTF-8窗至null，原manifest/input/native/result身份等且源保持。首轮request-changes保持原事实，原独立审查另行核验，不能替代owner或不同模型独立。

已公开脱敏的[页面/两修正补段](evidence/2026-11-10-task-composition-selection-browser.json)、[五包身份及原准备失败](evidence/2026-11-10-task-composition-selection-package.json)、[两轮实际自身审查](evidence/2026-11-10-task-composition-selection-self-review.json)、[完整分页审计](evidence/2026-11-10-task-composition-selection-reads.json)、[采样清理及后端自报用量](evidence/2026-11-10-task-composition-selection-cleanup-usage.json)、[原选择区桌面图](evidence/2026-11-10-task-composition-selection-desktop.png)及[窄屏图](evidence/2026-11-10-task-composition-selection-mobile.png)。投影先标原件bytes/SHA与删字段，再替换仓库路径及15个私有origin；截图属R3选择区，修正后未重拍。input用量已含cached，output及单列reasoning不再相加；不是账单。原独立续核、完整最终候选本地出口、普通提交及自己的CI/远端身份仍待完成。

## 独立本地出口

[同片独立终核](2026-11-10-task-composition-selection-review.md)通过完整23文件：两个Spec/P2与状态文档ST1关闭，Spec/Standards开放0，阻塞0。主审独立核修正源、R5全部439文件/两RECORD/283、受影响22检查与30HTTP、两模型原完整scope/native链、35私有原件至36公开引用及两PNG精确字节；没有重跑原144HTTP或未变产品行为。当前PLAN与父计划已同步，不能再将R4未验误作当前R5。

最终静态出口234本地链接/锚点、5JSON、四JS语法与whitespace、四保护源及6环境敏感值扫描通过。私有预检先遇脚本行首分号SyntaxError；修后无边界`sk-`模式将`task-composition`文件名子串误认密钥，9文件逐一确认后加token边界，最终issue0。原失败/处置保留，没有改产品来迎合预检。普通提交/自己的CI/精确Git与独立HTTPS仍另验；C5c/C6未由本片证明。

已普通提交并推送 `fe45e8ff07c6cb5ec9048b506c03b6dfd4e838b3`，23文件；自己的CI及独立精确Git/发行包/283/HTTPS正在续核。未合入main或强推。[C5c后片](../plans/2026-11-11-composition-runtime.md)只先准备新隔离环境与两域实际运行，不改变本片候选。


## 精确CI终结

fe45e8f自己的CI42945800414第四样本（2026-11-11 02:40:55–02:41:00 UTC）双OS七必要步骤均success/completed；原评审者离线核五份HTTP200原件、URL/字节/摘要、精确候选/工作流/job/步骤通过。结合先前已过23Git对象/439包/283冻结和一次独立HTTPS同完整SHA，本片精确交付终结。首、第三样本TLS EOF且无状态、第二样本In progress均保持，未取消或重跑CI。C5c的新阻塞不回写为本片失败，也不把本片CI转授新候选。
