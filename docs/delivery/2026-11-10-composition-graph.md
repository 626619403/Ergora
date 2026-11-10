# AC5 C4a：已发布嵌套关系图

基线 `45c2de47e9119d1f07616b3307331321d38155a4`，当前分支 `refactor/architecture-foundations`。[计划](../plans/2026-11-10-composition-graph.md)限定只读已发布preview、完整实例与三类关系、图/键盘选择和原编辑入口。实现、行为验证、实际自身模板及完整26文件独立两轴通过，开放finding 0，本地出口完成；精确提交交付待核。

## V0准备

已核原Workflow编译器的`parent`、`depends_on`、局部具名`inputs/outputs`、`levels`、权限、预算/usage、资源来源及prompt字段；不新增后端字段或权限算法。原页面可同时保留未发布草稿和已发布预览，因此必须明确标识图来源。原`app.js`重绘销毁工作单元图；新定义图沿同一显式mount/dispose生命周期接入，grant输入的局部清除路径也需销毁。

完整实例路径作为选择/节点身份；相同完整ref不合并实例。原Agent列表含版本/digest/专长，精确匹配足以投影，不增加latest查询。图布局会话只保存在页面内存，不改编译器摘要或定义持久格式。C3d自己的CI42807885966首份样本In progress，精确补核进行中；本片暂未执行新产品旅程。

恢复入口同时精简：旧PLAN原字节保存在`docs/PLAN-history-2026-11-10.md`，原四标题和相对链接目录保持，最新状态留在短PLAN，避免恢复时重读逐片长日志。此整理没有产品或测试变更。

## V1实现与R1安装准备

已接通私有组合展示模块、定义视图与app显式mount/dispose，以及grant局部清除。图使用原完整实例路径和levels，工作流端口只是显示锚点；图/键盘选择共享完整inspector，精确元数据与独立/父定义跳转保留旧缓冲。源JS语法与空白检查通过；尚不据此宣称浏览器完成。

R1离线构建/新环境非editable安装通过，436源/wheel/安装/RECORD逐文件身份与283冻结资产通过；两份原HTTP/定义库回归**28 passed / 33.41秒**（外层35.87秒）。没有新增依赖、Python产品/schema、CI或永久测试。首轮私有fixture误读revise顶级id而KeyError，保留原State/驱动/stderr；改从definition取id/version，在新隔离输入目录完整重新准备，无产品修改。

前片CI第四份官方样本Success，双OS七必要步骤全部success/completed，原评审者正做同片离线终核；前三份In progress原件保持。独立C4a两轴静态审查进行中，Standards暂未发现实证问题，Spec要求核pagehide/BFCache恢复；真实页面旅程正在运行。

## V2 R1页面与CG-1

原R1安装包主旅程第二段**4.90秒通过**：治理16、大型开发19、训练提案9、重复实例治理19个实例的结构/依赖/具名数据与端口一致，22次叶inspector的完整事实/资源/prompt均一致，精确索引未采用较新Agent元数据；真实鼠标点击/拖动、键盘选择、切页布局/销毁、精确跳转保留未应用字段、grant局部销毁及组件缺失表格均通过。第一段4.37秒只因私有驱动在表格滚动后未先滚回画布便使用鼠标坐标而失败；修驱动后无产品变化，原回执保持。

原R1生命周期旅程**33.19秒**：原回执记录了双目录/迟到回复三个true，但该段与误发第二驱动有重叠，不把它们作为独立隔离验收；最终范围改用严格顺序R3。最后明确派发synthetic persisted pagehide/pageshow，复现旧图已销毁而未恢复（CG-1）；不是自然BFCache命中或完整跨浏览器证明。修正仅在原app生命周期owner中对persisted pageshow调用原render，重新挂接图，未新增后台监听器框架。原红保持，R2安装及受影响复测待验。作者误在首段尚未收回时发起的冗余第二段看到了被首段销毁的图，原失败也保留；后续严格顺序调用，不算第二产品finding。

C3d精确CI/原评审终核已终结；本片R2/真实自身模板/完整fresh-context独立终核/精确交付仍待验。

## V2最终R3受影响出口

R2宽范围恢复修正经真实资料页合成persisted事件复现CG-2：未提交URL清空、budget从4321重置1000000（**2.74秒**，未提交/抓取资料）。最终仅在definitions tab恢复时重绘，R3重新离线构建/安装，436文件/RECORD及283冻结通过；较R2仅app.js收窄条件，其他产品未变。

R3恢复旅程**4.98秒**同时证明旧图销毁/新图挂接、资料页未提交URL与budget原样保留。严格顺序R3双home/迟到回复/修改grant/恢复旅程**13.97秒**整体通过，无页面异常。原R2 43.11秒换home选择超时保留；诊断证实私有驱动在新库完整读取前操作旧选择，改等待本次presets响应和库就绪后再选，无产品修改。R2未涉及persisted事件的主旅程**5.39秒**保持原范围，不重复运行未变图算法/原Python回归；CG-1/2待独立终核关闭。

图视口/自然前进后退观察、完整库原树保持/owned清理、真实自身模板与最终独立候选仍待核。

## V2原件复核与R4

R3桌面/移动宽度初始脚本的pageOverflow=false仅核文档宽度。实际截图发现缩放后立即适配使用旧renderer宽度，原R3探针为容器246/renderer1076，稍后原库100ms debounce恢复246/246。因此CG-3限定为**窗口变化后立即fit使用旧尺寸**，不是永久画布越界。随包Cytoscape已拥有ResizeObserver/resize监听与销毁清理，复用原接口，仅在三个显式fit前调用resize；不添加第二个observer。原R3截图/同步探针/稍后同步诊断保持，R4安装436/283通过，相关页面复测待验。

独立原HTTP复核只证实R3跨home请求46被held，第二个grant请求没有held标记；原true字段不足以证明迟到grant，撤回其完整验收含义，原因未确定。R4私有代理增加no-store、控制请求/响应原件，新驱动等待marker之后的具体未完成held请求并返回请求编号；它不改变产品协议。此前R3 13.97秒的合成恢复与目录范围分别保留，但第二迟到grant只以新原件为准。

R3自然back/forward观察为重新加载，未观察persisted pageshow，故合成恢复旅程不升级为自然BFCache验收。最终R4截图和自然导航范围单列，未变Python/三域完整图不为此重跑。

## V2最终验收原件闭环

R4两次真正延迟的请求为**94和103**，均保存held/gate_released及原请求/响应/控制命令：新有界异步轮询旅程**13.85秒**整体通过。旧异步waitForFunction谓词会把Promise视为truthy；原诊断以async()=>false在18ms返回false实证，因而旧true字段不能证明等待。已修私有驱动为page.evaluate内实际await轮询，不修改产品协议；R4第一受控重试因过早release失败原件也保留。

最终R4即时尺寸旅程**2.86秒**桌面1076/1076、窄屏246/246，恢复/其他页面未提交表单旅程**2.60秒**通过，双视口与自然导航观察**2.05秒**通过。自然back/forward重新加载，未观察BFCache命中。最终截图已人工查看，窄屏画布尺寸正确，图的全览需缩放/定位才能读标签；折叠与搜索属C4b。

离线核287对原HTTP字节/元数据，R4所有preview逐份与原编译器一致，四份实际安装静态资产与当前源一致；54个完整原包对象/目录不变，两个私有UI项目的Agent run数量0。树审计首段原生tuple与保存JSON list直接比较失败，改做JSON数据模型比较，原脚本/诊断保持，无产品变化。四轮owned HTTP管理器/服务及浏览器共40个采样进程身份已消失，清理只覆盖观察范围。

V1/V2本地行为出口完成；实际自身模板和完整新独立审查/精确交付尚未完成。

## V3 实际自身模板与公开证据

最终R4非editable安装的内置`ergora-structure-review`以证据专用修订`1.0.71`实际启动一次，run `0a28acda087d4a76b48fa84515532c24`，Codex / gpt-6.1-sol / high，**201.64秒，succeeded / approve**，Spec和Standards均approve，finding 0。此处沿用户授权使用Codex回退，不声称不同模型独立或正式owner批准；未重复模型调用。原结果SHA256为`a7a72bfbfd6222b98b0a132e2e0d208ba63bac2a6bc6fc7eb0104e2c5c028d5a`。

离线核实际stdin、prompt、manifest、原回执及原生MCP事件：五个scope文件全部完整读取，321,066字节候选附件用14个连续成功UTF-8页读至`next_offset:null`；offset 24,000的一次base64窗口以同offset较小UTF-8窗口重试，原件保留。六份受保护源及必要原件身份不变。读取审计只证明材料实际完整交付，不推断理解质量；后续计划/交付的状态续记不倒改冻结输入。

后端自报input 1,360,988、其中cached input 1,204,480、output 3,889，另报reasoning output 1,903；cached已含在input，不能重复加总，也不当账单。模型调用四个采样owned进程身份均已消失，连同页面40个采样身份只覆盖观察范围，没有未知进程清理承诺。

可携带公开投影及原件bytes/SHA索引：

- [真实页面、历史失败和最终受影响验证](evidence/2026-11-10-composition-graph-browser.json)
- [四轮安装身份与原28项回归](evidence/2026-11-10-composition-graph-package.json)
- [实际自身审查身份及原结果](evidence/2026-11-10-composition-graph-self-review.json)
- [五scope与完整逐页读取审计](evidence/2026-11-10-composition-graph-reads.json)
- [采样清理与后端自报用量](evidence/2026-11-10-composition-graph-cleanup-usage.json)
- [桌面截图](evidence/2026-11-10-composition-graph-desktop.png)、[窄屏截图](evidence/2026-11-10-composition-graph-mobile.png)

投影替换机器路径/本地端口，明确省略重复屏幕文字、布局/完整文件哈希表与PID；完整原HTTP、安装、模型事件及驱动留在私有验收目录。两截图逐字节复制，不改图内容。最终wheel SHA256为`9d8e0a423859697f876fc5dc0a9d89bc6a7a6893f10c577f335f223d71534aad`，436包文件与283冻结资产已由独立评审复核。

本次产品范围只有`console/{composition-graph.js,definitions.js,app.js,style.css}`，其中第一份为新增私有展示模块；其余为必要手册/架构、当前与前片状态续记、原PLAN归档及证据。完整候选继续由原fresh-context评审者补核，不重复已通过产品或模型运行。后续折叠/查找与精确版本比较按[下一片计划](../plans/2026-11-10-composition-exploration.md)分别验收；C4、AC5及整个项目仍未完成。

## V3 完整本地出口

原fresh-context评审者及原Spec/Standards两轴对固定26文件最终候选补核通过，两轴开放finding均0；历史CG1–3保留并按最终R4范围关闭。主审独立核实际输入/原生回执及完整读取，在内存重建五JSON和两PNG，与候选逐字节相同。详见[独立报告](2026-11-10-composition-graph-review.md)。作者三JS语法、diff空白、275本地链接/锚点、五JSON解析及可用凭据值/模式扫描通过，原PLAN归档逐字节相同。

至此C4a本地出口完成；本段及计划的最终状态续记与评审记账不改变四产品文件或冻结证据。下一步普通提交/推送本工作分支，保留ready身份，由原评审者核精确Git对象、一次独立HTTPS及本提交自己的官方CI；尚不声称精确交付完成。
