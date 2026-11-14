# Q2.3b1：原组合运行读取交付

日期：2026-11-15。基线`f1fc4501b8f15060eee7502caf6531c8f44a1b5f`，643产品／283参考；范围见[具体计划](../plans/2026-11-15-composition-run-inspection.md)。

|步骤|实际状态|
|---|---|
|合同／owner|已读agent_runs原存储／精确query／output、原完整input、agents原prompt／schema／结果保存及各后端实际传输；先固定合同。|
|实现|已在原agent_runs实现完整观察及精确记录共享，CLI只分派；WORKFLOW_DEFINITIONS／LOCAL_REVIEW补使用与覆盖，无新增schema、State或后端分派。|
|源码验收|原invocation suite32通过／4.18秒，含七新接缝：超过100历史／跨项目／搬迁／无后端／长回复／只读，及六类原件漂移／缺件／容量／未记录结果身份。原状态和可核其它原件保持。安装与相邻原回归待验。|
|安装／身份|r1wheel SHA256 `7eeee20d3e757476b87b7509bf05ea26071096d853d22ab63fd0cb61f0323510`，643源码／wheel／新非editable安装逐字相同，283参考保持；只改agent_runs／cli，无新增产品文件。|
|相邻回归|原invocation／agents／DeepSeek／web四suite安装72通过／23可选跳过／14.55秒，一项原Starlette warning。r1安装MCP extra后补原DeepSeek suite35通过／无跳过／21.96秒，含共享output归档／续接；不重复其它已验suite。|
|实际CLI|五条新进程命令，无Git／后端PATH并移除已知API变量：完整读取Q2.3a领域及自身原模型run、显式容量不足保留错误后按完整容量读、完整控制目录搬迁读回。两原run记录及原存储文件保持，无模型重发。|
|审查／发布|r1自身原结构模板及新fresh-context两轴request-changes／两个P2保持；r2已按实证修正，新包／安装／CLI及自身approve，同reviewer两轴approve／R1和R2关闭／开放0／0。本片固定发布／自己的CI及原终核待完成，前片未终核前不推后继。|

私有证据放ignored `.ergora/checks/composition-run-inspection/`，不改前片wheel、venv或原run。真实原run仅用于新读取入口的只读验收，不重复模型调用，也不扩大训练／GPU／质量／性能结论。

两条原run仍为`efd0fc2581d24d45a42e20d34b475c97`／`9606ae65ca07424a9d364153ab5b0eac`，完整result分别1,679B／1,150B；新reader保留原request-changes／approve和原SHA。前片实际stdin证据保持其原范围，本片共同protocol prompt观察不扩张为所有后端的传输认证。

## r1审查与r2修正

原自身结构模板run `51be70035a54488399a4a981866b1c8c`，65.388秒、21完整文件／434,085B／3继承资源均进入task及实际stdin。原input digest `265c3bfa7cb03a9666ca0898a8f9f10fa05cc57d0f36d261c2e3169c35783dce`，result SHA `2679ceebee29b70dbab5486ff65e0e36642f4752b223bfea951cd1ccded37739`，decision为request-changes。采用用户授权Codex回退，不声称异后端。

新独立reviewer在隔离副本实证同两项P2，见[原报告](2026-11-15-composition-run-inspection-review.md)：R1输入漂移会连带隐藏仍与原record SHA／bytes相同的prompt；R2深层request.json实际抛RecursionError而中断观察，其它完整result也丢失。r1原源码／wheel／安装／模型结果保持。独立复现为15,000层；新回归按20倍Python递归限额构造，输入及result两边均实际触发parser，result先同步原record摘要以免只测到SHA拒绝。

先保留未修源码上的红测试：扩展测试首轮7失败／1通过（四项只因新增input_compared字段尚不存在），再单独筛出两finding的实际路径3失败／31未选／0.70秒。最小修正在原inspect_run：prompt先按原record的完整input_request合同／SHA／字节数独立核，input可用时再逐字交叉核，以input_compared表示；input／result观察各自容纳递归解析错误，不改其它owner的JSON协议或原生命周期。修后原invocation源码34通过／4.00秒。

r2新wheel SHA256 `6a38e336970627e20ca1f6890bce3552166bcf681c5fbd9bea4fee1baff31956`；643源码／wheel／新非editable安装逐字相同，283参考保持。只改原agent_runs／cli，无新增／删除产品。安装原invocation及DeepSeek两suite69通过／无跳过／26.50秒，含归档／续接原接缝；r1其余原agents／web范围未受修正影响，不重复全量回归。

r2八实际CLI读取两条原真实run，继续核完整结果／原SHA、容量拒绝后明确完整读、迁移控制目录读取；另在隔离副本构造task漂移、递归input和递归result，三者分别仅影响对应观察，prompt身份／交叉核标记及其余完整材料保持。原两run全部文件与DB记录仍逐字相同，新模型重发0。首验收driver给隔离副本直接用裸SQLite构造result SHA时被原writer版本保护拒绝；保留原stderr，用State原writer修正同一副本，只续第八条读取，未改产品以绕过门禁、未重跑前七条。自己的新结构模板与独立复核在途，本片发布及自己的CI仍未完成。

r2自身原结构模板run `2714f6e314a24c17a5fa17cff88c2bdd`，45.809秒、21完整文件／439,899B／3资源完整进入实际stdin；input digest `83f3a21f1124ba6a3b0e25ecdc5de08fbe62e2a0c47ed309378a32199297f91d`，result SHA `fafca90f49a3e4f9183231f6327c59f4548eacdd48f12f0c3c402c881b3e8798`，decision为approve。同一fresh-context reviewer已接新冻结r2范围，独立复核结论待完成；不以模型意见替代其原件核验。

同reviewer已直接核新冻结13路径／diff、r2包、原红测试／新34及69项、八CLI原stdout／stderr／38与19原文件、完整新模型资料／input／prompt／stdin／result，并独立复现input漂移／整个input缺失／递归input／递归result、禁用后端及模型入口的读取。最终需求与结构两轴approve，R1／R2关闭、开放0／0，r1原报告前缀保持；[复核记录](2026-11-15-composition-run-inspection-review.md)是其结论。新包、源码和手册保持r2身份，后续只有结果记账。十Markdown的202个本地链接／片段核过；初次私有检查器未识别源码`:行号`后缀，保留失败原件并修正检查器后通过，不因此修改审查报告。当前完成本地验收，固定发布／完整Ref和本片自己的CI／原终核仍待。

## 固定发布

已建立并普通推送`96b4bb5454714a73e1d5f60b880a479c195e5269`，13blob，完整远端Ref相同。前片Q2.3a自己的CI及原终核通过后才推送本片；不合main。原reviewer已直接核13固定Git blob、全部643固定产品与r2wheel／安装及283参考，两轴approve／开放0／0；随后独立核远端Ref，并发现本片自己的Portability run `43638408686`／attempt1，CI终态在途。后继本地编辑不进入本片认证。

原reviewer已完成终核：自己的run `43638408686`／attempt1绑定完整`96b4bb5454714a73e1d5f60b880a479c195e5269`，官方run、精确attempt jobs及八官方job页交叉核八job／30必要步骤全成功；再次远端Ref完整相同。39次有界匿名GET／109捕获文件及全部SHA直接核验，私有终核汇总SHA `20513735ff01b4a87d29f9416891e12564ed961dcfd39135b669d0d3d696b461`。原[报告](2026-11-15-composition-run-inspection-review.md)追加最终两轴approve／开放0／0，精确交付闭合；本结论不认证后继b2工作树。
