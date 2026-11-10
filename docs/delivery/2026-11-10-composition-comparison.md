# AC5 C4b.2：精确已发布组合比较

基线`8ce9aba51c54e368aa8625e6c6535e4ac6ccaa19`，工作分支`refactor/architecture-foundations`。[计划](../plans/2026-11-10-composition-exploration.md)第二片拥有两个精确已发布preview的只读比较。前片折叠/查找已普通推送；独立精确Git与一次HTTPS身份通过，自己的CI42825342126第三样本及原评审精确终核通过，不转授本片验收。

## V0 接口与实现决策

`definitions.js`仍拥有版本选择、显式grant、请求世代、编辑会话及图生命周期。成对比较复用其原预览路径，向原`/api/composition/preview`分别提交两个固定版本和同一份grant；两个结果均通过且仍属当前请求后才展示。更改比较目标不切换编辑基准或发布定义；权限失败保留原错误，不能自动扩大grant。

比较展示计划放在内聚私有`composition-comparison.js`，实际唯一调用者为定义视图：其算法与文本inspector只消费两份已编译preview，没有网络、编译、持久会话或可替换实现。该模块承担完整路径配对、差异分类与按需完整详情，避免把比较算法加入图生命周期或现有定义编辑流程。原图模块及编译器保持。

原库在新隔离状态的设计探针证实：相同资源正文/内容摘要可以因来源定义版本改变而得到不同sources、装配prompt和preview摘要。因此分别比较资源内容身份与顺序、来源/声明元数据以及装配提示身份；不能把引用摘要变化误报为所有Skill内容变化。普通事实逐字段比较；对象键序无差异，数组保留原顺序，不推断权限包含或重写依赖。

V1/V2产品已实施，V3按以下实际结果更新；尚未授予页面、自身模板或独立审查通过。未发布草稿全图、正式交接和容量仍属后续片；本片不增加Python/schema/依赖/CI或永久测试。


## V1/V2 实现与安装

两个产品文件已实现：原`previewDefinition`按同一grant成对调用原入口并核完整根ref，目标变更复用原preview请求世代；内聚私有展示模块按完整路径比较普通事实、资源内容/来源及提示身份，并按需显示完整原实例/两份下载。原图、Python、schema、依赖和CI未改。两份定义手册、USAGE及架构已更新，JS语法与空白检查通过。

R1离线wheel构建/新venv/非editable安装分别10.09/0.05/5.79秒通过；437源/wheel/安装文件及两份RECORD一致，283冻结保持。wheel SHA256为`445570cd62d462beb6af222265e5b41ad30dbc256faea84b12ddead4cf371fc7`。不重复未变的Python/编译器回归。

私有fixture准备前三次失败均保留：首次误用未支持职能`auditor`；第二次误用未支持逻辑挂载`artifacts`；第三次在读取完整索引前就移走新子对象，原库按合同拒绝读取。修正为现有`inspector`/`reviewer`职能、`workspace/extra`及在浏览器显式故障阶段移动/恢复新隔离子对象，第四次准备成功；没有放宽产品准入。失败输入分目录保留，未启动服务/模型。当前开始按Playwright skill通过独立安装的实际页面验收。


## V3 主页面与下载

实际非editable安装页面主旅程4.20秒通过：三域16/19/9实例，分别核所选完整叶；仅来源版本变化未误报资源内容变化。重复子工作流新增三路径而不合并同ref实例；富差异覆盖增删/引用/职能/审查职责/后端/权限/预算与usage/并发/依赖/端口/层级、声明数组顺序。默认共同grant按原shell上限拒绝且未扩张，人工输入目标定义的上限后两个版本均通过；缺失新子对象时显示原拒绝并在私有fixture恢复。键盘选择的完整原实例保持全部资源/来源/prompt，三域的未应用版本文本和编辑基准保持。两份下载已复制到持久验收目录并核完整JSON等于原preview。

后续生命周期首段驱动误引用fixture中不存在的结构审查1.0.74而失败，未发出成对预览；修正为实际存在的1.0.90，新段在途。原失败及脚本保持，不据此修改产品。自然BFCache、跨浏览器与C6容量不在本片新增范围。


## V3 生命周期与视口

第二段83.52秒在索引注入检查前停止，整体保留失败：此前四次受控延迟原preview均经真实requestfinished与页面帧等待，target/grant/root/home切换后没有恢复旧比较；tab往返保留比较和未应用编辑缓冲，旧图销毁；同一preview的对象键序反转未制造差异。失败原因为驱动只等待网络响应、未等待新选项装入就读取旧选项，不修改产品。该段不能称为完整passed旅程；原driver/held回执/原HTTP与到达检查点保留，后续只补受影响段。

索引/视口补段首次3.82秒：索引摘要与实际根不符时页面明确拒绝；恢复索引后不可用目标清除，之后即时窄屏宽度断言失败，整体保留失败。后续只读诊断时页面390/390，未复现持续溢出，不能据此推定瞬时原因。最终补段3.48秒等待原Cytoscape尺寸更新后通过上述索引/恢复及1440×1000、390×844检查，文档宽度/scrollWidth分别1440/1440、390/390；两张截图已实际查看。测试等待原异步布局完成，无产品CSS或布局变更，不声称瞬时resize无变化、自然BFCache或跨浏览器覆盖。

浏览器与两个HTTP服务已关闭，10个采样owned身份均gone。完整原HTTP/原owner、原对象树/零run与两个下载离线审计已通过，详见下节；本片新独立审查在途，不重验第一片。


## 原件审计、实际自身模板与公开投影

离线核122对原HTTP的大小/摘要，34份成功preview逐份等于原owner；五份实际安装静态资产等于当前源。68个完整原对象树（含文件/执行位/目录）不变，两个UI home的全部agent_runs为0。受控缺失子对象已恢复；路由键序/摘要故障只改变客户端交付，上游原件与定义保持。两个下载为完整原preview对象，不把序列化后的字节称为原HTTP字节。

实际非editable安装的内置`ergora-structure-review`通过证据专用修订1.0.78运行，Codex/gpt-6.1-sol/high，run `dc6d043dcf0149a881969981ecd6be49`，120.05秒**succeeded/approve，Spec/Standards均通过，无finding**；外层CLI退出0。原结果SHA256为`1793c4f46571c959fe7a4339a43bc7ec2c1de91add83b251a86884e956b87d79`。用户授权的Codex回退只表示不同上下文，不宣称不同模型独立或正式owner批准。

完整输入含源码/驱动与明确省略大pair/路由map的原件身份绑定投影；模型不声称检查了省略原件。离线核manifest/prepared/actual input、stdin/prompt、native MCP及结果身份；全部五scope完整读取，191351字节候选经9个连续成功UTF-8页至next_offset null，两个base64窗口在同offset缩小重试，失败read0。14份完整冻结证据和五份受保护源保持。完整交付不证明理解质量；省略原件由独立主审单独核。

初次私有自审准备中，上游投影器误将build-install列表当字典而失败，缺少投影文件；作者随后误启动依赖它的准备驱动，在建立manifest/调用后端前停止。依赖准备驱动的原代码/stderr/空准备目录保持；首个投影器错误仅为当时工具回执中的作者历史说明，没有单独保存projector stderr。修正投影类型并在新目录启动；实际模型仅运行一次，没有把准备失败算为模型拒绝。模型/CLI四个采样owned身份均gone。

后端自报input796802，已含cached689024；output2477，另报reasoning934，不重复叠加。这是自报用量，非账单。

公开资料保存原件bytes/SHA并列明省略/路径与端口替换：

- [浏览器与原件审计](evidence/2026-11-10-composition-comparison-browser.json)
- [非editable安装与冻结身份](evidence/2026-11-10-composition-comparison-package.json)
- [实际自身模板原结果](evidence/2026-11-10-composition-comparison-self-review.json)
- [全部scope及连续读取](evidence/2026-11-10-composition-comparison-reads.json)
- [采样清理与自报用量](evidence/2026-11-10-composition-comparison-cleanup-usage.json)
- [桌面截图](evidence/2026-11-10-composition-comparison-desktop.png)、[窄屏截图](evidence/2026-11-10-composition-comparison-mobile.png)

完整原pair、路由索引与逐文件map私有保留，不把投影当完整原件；两个PNG为实际截图原字节。完整最终范围的本片独立两轴、普通提交/推送、自己的CI与精确Git/HTTPS交付仍待完成；不据本片授予C5/C6或整体完成。


## 完整候选本地出口

原主审及本片两独立轴已核完整20文件最终候选，Spec/Standards开放finding均为0，本地出口通过；[独立报告](2026-11-10-composition-comparison-review.md)记录精确范围及原件身份。最终固定后只有报告终态和一处准备失败证据归属澄清，两个产品文件、五公开投影及两原PNG保持。当前进入ready固定及普通提交/推送；自己的CI、原评审精确Git与一次独立HTTPS交付仍待验，不据此授予C5/C6或整体完成。
