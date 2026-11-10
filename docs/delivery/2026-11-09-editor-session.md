# AC5 C2：工作单元编辑会话

固定基线`61ccc2cce8bfcc3a46b4a069c78ea660f76063d9`，分支`refactor/architecture-foundations`。[C1](2026-11-09-definition-console.md)已普通提交推送，本地出口通过；自己的CI42612128319已Failure（研究耗时浮点比较）、HTTPS同SHA通过；仅测试修正03f1f58自己的双OS CI42616678385七必要步骤及独立明确HTTPS同SHA已终结；C2仍核自己的交付身份。[AC5计划](../plans/2026-11-09-composition-console.md)为范围入口，C3标准定义编辑和C5正式任务交接继续独立。

## 原问题与所有权

原`console/workflow.js`只有一个工作流生命周期所有者，但单元表单、完整JSON和草稿ID的输入只递增请求世代，未保留文本；选择节点/重绘从旧`input`重建，下载和保存也读旧`input`。图每次用breadthfirst重建，拖动位置丢失。这些为源码观察，须用固定安装包实际复现后记录原红。

继续使用原`workflow.js`、Cytoscape、`drafts.save`和`reference.validate_input`；本片先不抽取共享编辑框架。唯一语义输入与表单/JSON原始文本分别保存；未应用、无效文本有明确状态，不能静默保存或下载较旧输入。原编译器拥有完整合同、环/路径/数量/修订校验，浏览器只处理交互及必要的引用一致性。不更改283冻结文件、六阶段、正式批准、运行调度或存储schema。

## 可验收子节点

|节点|交付与证据|状态|
|---|---|---|
|E1 原包反例|固定C1安装包实际表单/JSON输入后选择节点或切页，观察文本/下载与输入不一致；保留原包、原日志和精确脚本|原包实际Chromium四项均false，精确loop红，原下载保留|
|E2 统一会话|一个语义输入、独立未应用文本、所选单元/草稿ID/修订与请求世代；按项目和控制目录保存缓冲，切换/重绘/刷新保留文本；载入替换或丢弃必须明确|R7实际浏览器验证通过；精确交付待结|
|E3 有界编辑命令|应用单元、改名及引用修正、依赖、增删、完整JSON应用可撤销重做；有界历史和明确未应用状态；保存/下载消费同一明确快照|R7实际浏览器验证通过；精确交付待结|
|E4 独立布局|位置与视口保留，拖动不改语义输入/批准摘要；可显式重新排布，表单可替代图选择|R7实际浏览器验证通过；精确交付待结|
|E5 回归与交付|原Web/架构检查、最终独立包、真实两域编辑/下载/保存及迟到回复旅程；新独立结构/测试价值/性能审查、真实自身模板、自己的精确CI/HTTPS|本地完整出口通过：S1–S8关闭，第四轮模型approve/公开终核通过；本候选CI与HTTPS待验|

缓存和历史仅是本地编辑便利，不替代服务端持久草稿或正式输入。新修订仍由原save的expected revision控制；迟到保存只登记原提交快照的事实，不覆盖当前更晚文本。未通过应用/校验的文本不能被静默解析成正式任务。训练模板继续是原文件与可信实验入口，不把它包装成已支持的可执行开发DAG。

实施前先完成E1，然后选择最小必要状态形状和本地历史上限，记录实际行为。重大节点各更新本记录和PLAN；C1自身模板和CI不替代C2验收。

## E1原安装包反例

直接使用C1最终R4非editable包（SHA `7c122ff9979b224bfbcf67defea1dadf935a6609043039628e2f3431f9c89b63`），新持久控制目录和两个本地Git项目。实际浏览器载入大型开发模板后：未应用任务说明在切换单元后还原，未应用JSON在切页后还原，草稿ID在切页后还原，无效JSON在页面上时仍可下载旧input。精确脚本记录 **formPreserved/jsonPreserved/draftIdPreserved/downloadBlocked全部false**，最后断言红。原日志、返回值、原下载和C1安装包保持，未用源码分析替代实际失败。

准备脚本首轮把venv Python路径resolve到全局解释器，导致No module named ergora；原失败入口/日志保留，改为保留venv入口路径后正常启动，没有修改产品或安装依赖。原浏览器仍在，用于布局反例与原包比较；后续按PID/starttime仅清理owned入口。

## E2–E4实施选择

统一会话继续留在原workflow所有者：语义输入、每单元未应用表单、完整JSON原文、目标草稿ID与服务器修订、选中项和请求世代各有明确用途。按控制目录/项目在当前浏览器会话保留编辑缓冲；历史只保留本页有界命令，不把它当服务端持久草稿。无效原文不能被选择/刷新/迟到回复覆盖。存在未应用文本时，保存/下载/语义命令需先明确应用或放弃；单元选择仍可进行。

真实语义命令使用线性有界历史，最多50个快照且总计4MiB，先丢最旧历史；该本地历史界限不改变原编译器支持的输入范围。改名单次修正语义及未应用依赖引用；JSON应用仍须原服务端校验。位置/视口独立，拖动和重新排布不进入任务输入。迟到保存只更新原目标修订事实，不把更晚编辑替换成响应快照。缓存异常须可见并保留原文供恢复，不暗中采用损坏内容。

## E2 初轮安装包与迟到保存反例

R2非editable wheel SHA256 `9e7b14c878b5ab2ec83ae288fa2f9ad3fcf6b80d698a72bf64b3dc45958f101f`，435源/包/安装文件及283冻结身份通过，原Web/架构19passed / 10.81秒。实际Chromium运行E1相同脚本，四项由false变为true；仅该范围通过。

随后R2实际迟到保存检查：保存A的回执暂扣、载入模板B并编辑、切换到另一个项目后放行A的回复，再切回，实际B缓冲被旧A覆盖，`preserved=false`，记为 **C2-S1**。旧回复在会话已替换后仍可调用remember登记为该项目当前缓存。最小修正使startSession拥有登记新会话的职责，remember只保存该命名空间仍拥有的同一实例；回复的原服务端保存事实仍保留。原包/原脚本/原红日志保持，修后须新包重跑。

第一次包含confirm的多步CLI harness被模态对话中断而没有Result，第二次尝试在reload前清空sessionStorage又被原pagehide恢复，仍被confirm中断。两次均只算harness失败；改用新浏览器、干净载入和已保存草稿后，取得上述可重复的实际产品反例。未绕过产品替换确认。

R2真实语义命令检查已取得：改名后语义/其他pending依赖引用、其他缓冲保留、撤销重做、增删恢复、完整JSON命令撤销重做、保存快照与编辑器一致均通过，下载文件独立解析后与保存正文一致。该脚本首轮鼠标拖动没有实际移动，`actualDragMoved=false`，因未先滚动图到视口，不能据此声称移动后保持通过；另用真实pointer/wheel脚本补验。

## E3/E4 现有 R2 的补验与独立发现

实际pointer/wheel补验已通过：先将画布滚到视口，真实鼠标拖动、wheel缩放后，选择节点和刷新均保留位置与视口，任务JSON不变，七项true。首轮立即wheel等待超时原件保留；后续只读probe证明该轮已实际拖动，修正harness等待滚动稳定再wheel后取得完整结果，没有修改产品。

历史实测55个小命令后可撤销49次至第6步、重做49次，分叉后清除redo；每快照526165字节的大文本下可撤销6次，与4MiB预算的实际计算相同；单份4194321字符仅保留当前且不可撤销。真实浏览器存储配额异常已触发，界面显示警告、当前文本仍在内存。此项仅验证编辑缓冲与本地历史，不扩大正式编译器输入合同或声称整个浏览器进程内存不超过4MiB。

独立审查提出 **C2-S2**：合法工作单元外壳的缓存若含未知kind或损坏角色元数据，会绕过缓存恢复UI。R2实际未知kind缓存的恢复按钮计数为0（未捕获冒泡pageerror，不声称浏览器已测到TypeError）；源码只读状态探针另确认异常路径。最小修正仅验证浏览器检查点的kind、丢弃可从bootstrap重读的角色/validation元数据，不重写任务validator。

**C2-S3**：改草稿ID的save-as/已知修订语义需在界面和手册说明。保留安全策略：未知目标按revision0创建，已存在目标会冲突；不自动使用dashboard修订覆盖从未载入的草稿。修改既有目标需先从列表打开；实际载入/本会话保存回执的目标保持已观察修订。UI已补说明，后续真实冲突/缓冲保留待验。去掉未显示的validation缓存及成功回调的重复重绘，避免重复存储/画图。上述修正须用R3包复验，R2检查不自动继承为最终包结论。

## R3 安装包与核心复验

R3 wheel SHA256 `885a8f1b7cf8be785bba9276da0ab3f827360ed908219723d894e2f811a77a8d`，435源/包/非editable安装文件相同，283冻结与03f1f58父片相同。原Web/架构/C1 HTTP共 **22passed / 17.29秒**。构建首试no-isolation缺setuptools，原日志保留，改用项目已有build-system的uv隔离构建成功；回归首命令写错architecture文件名没有运行测试，原日志保留，纠正为现有test_architecture_boundaries.py后取得上述结果，没有添加依赖/测试/CI。

E1四项同脚本全true；真实语义命令、实际pointer/wheel、下载与保存/编辑同一正文均通过。S1使用R2原late-save-away脚本，preserved由false变true；S2未知kind缓存原文保持、下载逐字相同、明确清除后回到起始视图均通过；S3实际新目标创建、未知已有B冲突、B正文/修订不变、当前A输入保留、重新选择已观察A成功r2均通过。非法JSON和依赖环均保留原文本，迟到合法JSON校验不覆盖新非法文本，也不偷偷应用旧输入。此处原件支持运行修复，finding最终由独立审查者关闭。

R2缓存检查早期使用pagehide写入与多个旧脚本混合，未证明浏览器冒泡异常；后用新浏览器导航到同源非应用JSON页再写缓存，未知kind仍无恢复入口（因原重复agents可使其继续渲染），损坏agents则停在读取视图且无恢复入口。两组原日志保持，源码探针的TypeError与实际浏览器观察分开记录。R3不再缓存角色元数据，未知kind走明确恢复。

## C2-S4 键盘选择焦点

R3实际keyboard-and-ids的选择/应用两项为false；另精确keyboard-focus脚本确认：原生select用Arrow改变选择后，重绘销毁控件，activeElement变BODY、selectKeepsFocus=false，后续键盘落在页面。最小修正仅在该同步change handler重绘后聚焦新select，不引入全局焦点框架。R3其他命令/保存/冲突/布局保持其实际范围，最终R4需同脚本复验并核新包。

治理域实际表单应用/持久保存/下载同正文已通过；训练域没有开发草稿保存按钮，切项目返回保留训练选择。初次getByRole下载文件计数0是closed details未进入可访问树，不能当没有文件；另打开details后下载实际文件复核，结果单独记。

## R4 核心验收（S5/S6 修正前）

当时源码SHA256 `07a9756708f2ba3a0b1e681267251fa3316b78972e3ccd1fd5650e1a1d23b592`。R4 wheel SHA256 `fb0568b8182965977e39f269f6620fe665e9415dddada1fb2fe9bb68deaa7cda`，435源/包/安装与283冻结相同，原Web/架构/C1 HTTP **22passed / 17.85秒**。当前没有新增Python测试、依赖、CI或schema。

R4重新运行完整两组12份浏览器脚本，每份原脚本/Result/日志均固定SHA。原E1四项、语义命令十二项、冲突/非法JSON/环/迟到JSON十项、pointer/wheel七项均通过。R3键盘脚本仅改变截图文件名后复用，选择/应用/撤销及字典保留五项全true、390px无横向溢出；另R3原焦点脚本逐字复用，active SELECT、selectKeepsFocus=true，关闭原BODY反例。历史55命令仍49undo/49redo，526132字节快照保留7份/6undo符合4MiB预算，单份超限只保留当前且quota警告可见。

R4的原late-save-away脚本、未知kind恢复/原文下载/明确清除、治理编辑/保存/下载、训练切项目与打开11份文件详情/实际下载均通过。四份实际磁盘下载已经独立语义或逐字比对；S1–S4由独立审查者复核关闭。第一次训练role下载计数0仅表示details闭合时按钮不在可访问树，打开后下载成功，不需要修改产品。

E5剩余同端口控制目录隔离/原home重开、owned清理、自身模板、最终独立范围/静态核对和自己的精确CI/HTTPS；不以03精度修正的CI替代C2。

## 同端口重开与控制目录隔离

在同一原浏览器/HTTP地址保存A的未应用表单、非法JSON与目标ID；按PID/starttime/完整argv核定owned服务，停止后以同端口、另一控制目录B启动同一R4包。B初始无A编辑，独立写入B标记；再以原argv/原home/同端口恢复，A三份缓冲逐字恢复，原已保存草稿列表与恢复前完整相同。三个入口PID不同，原/替换/恢复各自identity与停止记录保留。此项支持按控制目录命名空间和HTTP重开，不推导跨浏览器/永久会话保存或OS隔离。

## Owned 入口清理

八个本片浏览器会话已逐一按保存名称关闭；六份HTTP身份（含同端口原/替换/恢复）均核保存PID/starttime/完整argv后仅终止owned入口，最终对应进程不存在或已为zombie，全部端口关闭。首轮清理断言把端口关闭误当进程已退出，原最后入口仍在graceful退出而断言红；原脚本/日志保持，改为分别等端口关闭与进程退出后，最终清理通过，没有选择或终止其他进程。自身模板使用独立MCP入口，与上述UI服务不同。

## 自身模板首审与 S5/S6

原R4实际随包结构审查模板的证据修订1.0.1运行 **264.41秒、succeeded、request-changes**，run `14c126922e8745f28ef92cc1429a99bf`，13源文件/185096字节候选，原结果SHA256 `fb26dd0a9ad3ae0d26fe2804f6ac8ffddd9aec18c97dfc819b0216c85f392030`。该意见提出两条P2，不能以此前独立核心通过代替新finding处置。

**C2-S5**：真实R4浏览器先扣r1保存回复、刷新打开该r1、修改并保存r2，再放行旧r1。选项仍标r2，但重新打开读回旧正文，reopenedNewer=false；服务端r2及新正文保持。最小修正仅使同home/project/id的dashboard回执单调合并，不替换已经观察到的更高修订，不从dashboard自动更新编辑会话的expected revision。

**C2-S6**：形状合法但key不属于任何语义单元的缓存buffer绕过恢复后，所有可选单元均不能丢弃它，阻塞保存/下载/JSON。独立原安装状态探针和实际R4原包浏览器分别记录。最小修正在检查点恢复时核buffer key属于语义单元集合，走现有原文下载/明确清除；pending的unit_id仍允许不同于key，不能误拒绝未应用改名。原红和最小修后证据分开。

首审原流包含合法base64页（UTF8边界切断），旧私有审计假设全UTF8而失败，原失败保留。理解原encoding后逐页核全部185096字节、1次重复页、3份base64回执及所有祖先指令/Skill均完整相同；仅证明字节交付，不能声称全plaintext语义读取。后续新证据Skill会要求base64回执在同offset减小窗口重读至UTF8后再继续，最终模型复审另核。生产Task MCP协议未修改。

S5/S6最小源码修正已实现，须新R5包、原两反例、受影响回归、新模型复审和同片独立复核；当前仍不提交C2。

## R5 最小修正与复验

当前唯一生产差异仍在原 workflow 所有者；源码SHA256 `8427d68d5b59d2973e568d7e041182068c587fc888f4b96b512f0d6cc19bab75`，wheel SHA256 `2dd4478f4549059ac4dbb52198b94cebf9543f3e57efbf85db7ded077e87fdfe`。435源/wheel/非editable安装身份与283冻结身份相同。原22项 Web/架构/C1 HTTP回归 **22passed / 11.68秒**；没有新增永久测试、依赖或CI。

S5/S6使用原R4浏览器脚本逐字复用，R5分别取得 reopenedNewer=true、serverRevision=2/serverNewer=true，以及 recoveryAvailable=true、rawPreserved=true。额外真实下载孤立缓冲6256字节，与注入原文逐字节相等；明确清除回起始视图。再用正常表单作未应用改名，reload仍保留新ID与说明、语义原ID不变且保存仍阻止，明确应用后改名成功，未误拒绝合法pending rename。

完整12份原浏览器脚本在R5重新通过；历史/真实pointer/wheel/390px键盘/各类迟到回执/两域下载保存/训练文件保持原范围。大型开发与治理下载正文与保存结果语义相等，损坏缓冲原文及训练下载逐字节相等。R5准备过程先用了不存在的浏览器配置路径、错误URL端口和未切入工作流页，均为harness前置错误，原日志分别保留；纠正入口并验证原owned HTTP身份后使用同一包运行，没有为准备失败修改产品。

实际自身模板证据修订1.0.2正在运行，明确要求base64页在同offset减小窗口重读到UTF8，再跟随该明文next_offset；生产MCP协议不变。最终同端口重开、owned入口清理、公开投影、独立终核及本候选CI/HTTPS仍待结，不把历史R4或03 CI代替R5/C2门禁。

## 第二轮审查中断事实与 S7

2026-11-10恢复时，第二次审查run `c504c48db20e495e8f7acbb25442df65`的模型原stdout已有turn.completed和协议result，decision=request-changes，但外层运行记录仍为running、没有返回给原harness；外层进程已不存在。不把原记录手工改成succeeded，也不臆测完整耗时。原协议结果、模型stdout、固定输入和原库状态保留，意见与运行完成分别记账。

**C2-S7**：首轮S5修复只保护保存回执；原app.refresh仍可能把迟到的dashboard r1安装到已观察r2的页面。独立源码确认后，原R5实际浏览器暂扣GET r1、编辑保存r2、放行旧GET、重新打开，reopenedNewer=false，而服务端r2与新正文保持。最小修正在原refresh所有者合并同控制目录/项目的draft高修订，其他dashboard字段仍使用新回复。局部dataControlDirectory随成功data安装更新，避免更换控制目录后bootstrap成功/dashboard失败使旧data被误认为新目录；不从dashboard更改编辑器expected revisions。原S7红保留，R6复验和新实际自身模板待验。

## R6 当前候选验收

R6 wheel SHA256 `fa7a42a7fb83f61dd302ac9b5c705f3aac782d0ebaaa1f30eadddc0f47f7398e`，435源/wheel/安装和283冻结身份保持；本片生产最终涉及原 workflow 和 app 两个所有者。原22项回归 **22passed / 13.28秒**。完整12份浏览器脚本再次通过；S5/S6/S7原反例脚本及合法未应用改名恢复分别通过。S7原R5错误正文与服务端r2事实保持，R6同脚本reopenedNewer=true/serverRevision=2/serverNewer=true。

独立审查另执行实际refresh函数的内存HTTP探针：同home最高修订/新ID保留、其他dashboard字段刷新、A数据→B bootstrap成功/GET失败→B再次成功不混入A、切项目不混用均通过；这些不是实际跨home浏览器检查。R2原意见附补充只读审计：10连续UTF8页/211082字节、四祖先指令Skill全等、protocol原结果SHA256 `456c721daa641013e33ef8b6acc170a7cf775b16a0d3997455962d72252ceab1`，外层仍running。此审计只核原件，不修改原运行或推断耗时。R3新实际模板1.0.3在途。

## 第三轮实际自身审查与 S8

R3 run `58be8da38be344efb73690f511b65239`，**253.61秒、succeeded、request-changes**，原结果SHA256 `aeff24dcffa8278d8bcc40cfe37866954df88f0a492ddabec3652f399e95aa19`。217942字节候选有10连续UTF8成功页和4份同offset base64重试，五固定scope文件、四祖先指令Skill和实际prompt均经独立核相等。该读取已覆盖完整明文，不等于推理或正式批准保证。

**C2-S8**：S7的data目录身份只保护成功合并，bootstrap B成功/dashboard失败时仍会渲染B元数据与A旧草稿。原R6实际同端口换home，在B的dashboard单次500后仍出现only-a/shared两个A选项、retainedDraftControls=1、hiddenForeignDrafts=false、failureView=false；实际B两个保存草稿本身保持。独立实际函数探针也证明从旧条目可建立B namespace/A正文/revision1，若B同修订保存会通过。旧内存探针只覆盖B再次成功后的隔离，没有覆盖失败停留的可操作性。

最小修正在原refresh成功解析bootstrap、确定最终项目后，若data所属目录/项目不匹配就清除data并同步绘制原loading/error视图，再等待dashboard；保留原A编辑会话/缓存，未重置全部状态。R7安装包复验、原S8脚本/旧缓冲恢复、新实际自身模板和同片独立终核待验。历史R6清理已完成15 HTTP身份/9新增浏览器；为S8新增服务/浏览器须另记最终owned清理。

## R7 修后验证与第四轮准备

R7 wheel SHA256 `722ece41c54347d60f3216a27d8b1b66c09cebc582c2ede1396e3f9f2e90b796`，435源/wheel/安装和283冻结身份保持；22原回归 **22passed / 12.85秒**，完整12脚本及S5–S7原反例/合法改名全部通过。S8原脚本逐字复用，换home后的单次dashboard500现在显示原失败视图、草稿控件0/hiddenForeignDrafts=true；重试只显示B库，返回原home无需reload即恢复A未应用表单和非法JSON。原R6同脚本的A库混显红保留。B原保存正文/修订不因失败路径更改。

第四次模板准备时，完整任务/计划/审查记录装配78913字节超过私有harness原选70000字节容量，原prepare错误和未运行快照保留；按支持合同显式选择100000字节后重新准备，没有截断祖先资源或任务、没有修改生产协议/库/共享默认。此轮实际模型仍在途，准备失败不算Agent失败或模型审查完成。最终同端口成功旅程、owned清理、公开证据、模型/新独立终核与精确交付仍待核验。

R7成功同端口换home/恢复也已另跑：A的未应用表单/非法JSON/目标ID逐字恢复，保存草稿before/after字节相同。最终25份owned HTTP进程身份逐一核PID/starttime/argv，仅关闭本片入口，全部端口已关闭；浏览器原8份关闭记录加后续15个已知会话的最终关闭/已不存在记录保持。模型审查入口是另一类owned子进程，不把UI清理当模型运行成功。

## 最终模型与公开交付证据

第四次实际运行 `af764f526e3e4cc6a9fb9bec850ff966`，证据修订1.0.4，**214.22秒、succeeded、approve**。13份受保护源/配置/测试完整候选224857字节、10连续UTF8页、base64重试0、失败读取0；四份祖先指令Skill、固定manifest/input/实际prompt和原结构化结果均匹配。原结果SHA256 `4ba458a46ba97f7cc01d741a636f3189a4a2ef4c5f599c3c0e1db7743f9e081c`。模型只读取固定候选，没有运行仓库代码或替代正式批准。使用用户已授权的Codex/ChatGPT回退，不宣称执行与审查模型独立。

对外归档13份JSON和桌面/窄屏两张实际截图：[最终包/冻结身份](evidence/2026-11-09-editor-session-package-r7.json)、[浏览器/原反例/下载/目录切换与清理](evidence/2026-11-09-editor-session-browser-r7.json)、[首审原request-changes](evidence/2026-11-09-editor-session-self-review-r1-result.json)、[第二轮中断事实](evidence/2026-11-09-editor-session-self-review-r2-interruption.json)、[第三轮request-changes](evidence/2026-11-09-editor-session-self-review-r3-result.json)、[最终原意见公开投影](evidence/2026-11-09-editor-session-self-review-r4-result.json)和[最终读取审计](evidence/2026-11-09-editor-session-self-review-r4-reads.json)。JSON为路径清理/格式化的公开投影，result_sha256固定原native字节，不等同于公开文件SHA。原始缓存正文不公开，私有原下载保留供逐字复核。[桌面](evidence/2026-11-09-editor-session-desktop.png)与[390px窄屏](evidence/2026-11-09-editor-session-narrow.png)为显式重新排布后的展示截图，实际pointer/wheel/键盘旅程另有原日志；截图前后语义输入不变。

边界：本片没有新增Python永久测试/依赖/schema/CI。验证为Linux当前可信容器内的本地编辑器、原HTTP/架构用例和实际Chromium交互；未证明跨浏览器永久保存、全平台浏览器、OS隔离、GPU/训练结果、C6图容量或整框架性能。C3标准定义编辑、C4嵌套图、C5正式交接、C6容量继续原计划。最终25文件的完整独立本地两轴终核通过、开放finding 0；13公开JSON/两截图/模型明文及owned清理已独立核原件。8文档138链接/94 parser检查通过。本候选普通提交/自己的必要CI和明确HTTPS远端身份仍另核。


## 精确候选远端与 CI 终态

C2 已普通提交推送 `0a495aaaa489f838c009820b7cd978bbed0c5e37`（25文件）。自己的 [CI42747066139](https://github.com/626619403/Ergora/actions/runs/42747066139) 前两采样在途；2026-11-10 03:28:04 UTC 新官方原件显示 **Cancelled**：Ubuntu 原生回归步骤取消，原 job 注释明确超过20m0s；其构建/冻结身份及 Windows 四必要步骤全部 success，共六项通过、一项取消。没有取消或重跑请求，不能把本地22项与浏览器绿灯替代整套CI，也不以Windows通过推断Linux通过。原失败保留，另做[CI时长审计](2026-11-10-ci-duration-audit.md)，无实证前不删测试、放宽断言或改变时限。明确HTTPS读取仍为同完整SHA；[独立报告](2026-11-09-editor-session-review.md)记录精确范围与复核。本地功能门禁通过和普通远端交付保持，精确CI门禁未通过。
