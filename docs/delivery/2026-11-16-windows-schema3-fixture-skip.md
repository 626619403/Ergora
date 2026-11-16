# M1b：Windows schema3 fixture 前置跳过修正

2026-11-16。状态：最小四行修正、局部边界检查及fresh独立两轴审查闭合，已固定并普通导入；已普通推送，自己的准确CI八job全success。原候选`833966d4ba21fa7bcb6670e9908d05f058cf8fdd`自己的[43773202173](https://github.com/626619403/Ergora/actions/runs/43773202173)准确push／attempt1已completed／failure：plan与六Linux全success（group2 9分40秒、group5 15分45秒，原20分钟限制），Windows 15分55秒，应用回归失败；wheel、283参考、PowerShell5.1 installer及upgrade与观察件上传均success。

原Windows官方check annotations为HTTP200，原件在本片前置M1b ignored `publication-r1/windows-failure`。摘要是**1214 passed／995 skipped／5 errors／16 subtests passed，877.59秒**；没有取得完整日志，不以annotations冒称读取过所有trace。五错来自`tests/test_training_cycle_controller.py`四个新增测试：`test_schema3_native_callback_refuses_before_executor_effects_and_keeps_completed_read`、`test_schema3_birth_retains_sources_bytes_and_one_clock`、`test_schema3_intent_is_local_and_all_execution_entries_remain_closed`、`test_controller_original_type_is_authenticated_read_only`（后者两参数）。均在setup先进入原Linux-only native source preparation／submission，来不及到body的SDK跳过或条件判断；不是Windows超时或安装失败。

最小实现：仅给这四个原测试添加与同模块既有方式相同的Linux／WSL2前置platform mark，在fixture setup之前跳过；不跳整个模块、不改fixture／生产／参数／断言，不减少Linux保护、不延长job或改CI分组。沿原收集／mark接缝检查准确五节点、Linux选择保持及Windows早skip条件，真实Windows候选CI仍单独验证。纯平台mark无需为原测试再增加复制标记字面量的新测试。源码只在`fix/windows-schema3-fixtures`隔离分支，从准确公开候选833966d建立；在途M2源不混入。

完成后新fresh reviewer核原官方失败／准确四行diff／实际检查，再普通导入开发分支、推送和绑定新候选自身CI；原833失败保留，不以Linux或先前59b74ce全success代替修正后的Windows结果。


## 隔离实现与机械边界检查（2026-11-16）

实现基线准确为`833966d4ba21fa7bcb6670e9908d05f058cf8fdd`，隔离分支`fix/windows-schema3-fixtures`。仅在上述四函数的参数化标记前添加`@pytest.mark.skipif(sys.platform != 'linux', reason='Controller consent requires Linux/WSL2 clocks and flock')`；理由逐字沿用同模块既有controller consent标记。完整源码diff为4行增加、0行删除；fixture、body、参数、产品及CI均未改，也未新增测试文件。测试文件SHA256修前`3db640cd63890dd8370b8a7447b2602ee253327baa94ccb2083fdec0dd4ced35`，修后`c58f14558427fba3b4dff38e1cece97ad9f46bad177d1ee5033442607a4f8de3`；源码diff SHA256为`c390efec69da51acbc973aba25d525fa38c5a12438b99b9277e48dced7ad1305`。逐一移除新增四行后与准确基线测试文件逐字节相同，`git diff --check`通过。

持久ignored证据位于`.ergora/checks/windows-schema3-fixtures/`：`implementation.diff`、`summary.json`、`commands-before.json`、`commands-after.json`及各阶段`.log`／`.json`。解释器为既有开发环境Python，先确认pytest9.2.0和Temporal SDK真实可导入；复用前片`check_boundary.py`，适配本模块和四目标，并允许指定单个node。工具只在模块decorator求值时模拟`sys.platform='win32'`，随即恢复host Linux，再调用真实pytest；fixture setup hook抛sentinel，任何fixture body均不执行。每个实际subprocess argv及退出码在两个commands文件逐项保存，pytest参数为`-q -p no:cacheprovider`＋原四目标／单node，Linux另加`--collect-only`。

修前准确五个参数化node分别用独立pytest进程运行，各自收集1项、fixture setup hook调用1次并以同一sentinel出现1个setup error，退出码均1；原无platform mark。修后同四目标合跑**5 skipped／0.05秒**，五项均在setup阶段skip、无call报告、fixture setup hook调用**0次**、退出码0。Linux修前／修后均收集同序同名5节点，修后新增skipif条件全部false；修后**5 tests collected／0.04秒**、退出码0。四函数的原参数化保留，包括original-type两项；未运行昂贵Linux原生body，也未进行安装、全量、服务、训练或额外矩阵。该模拟仅证明提前skip接缝，真实Windows仍待新候选自己的CI。

旧helper初次在pytest9合跑修前节点时，第一个session fixture到达sentinel，后续因helper未缓存异常触发pytest内部finalizer断言；原件`helper-initial-before-windows.log/json`保留。此为验证helper机制限制，不是新增产品故障；后续按五个独立进程逐项验证消除共享fixture状态影响，五项均只见预期sentinel。未以该初跑冒充五个独立sentinel成功。

本节点仅完成实现和上述源码机械检查，尚未独立审查、提交、导入、推送或发布。下一步由新的fresh reviewer核准确基线、四行diff、原官方失败和本次原件；通过后再按既有授权普通发布并绑定新候选自身CI。833966d原官方failure保持。

## 独立审查与固定导入

[fresh独立审查](2026-11-16-windows-schema3-fixture-skip-review.md)核完整四行diff、原官方annotations、真实fixture闭包与原五节点检查，需求和维护性均approve、开放0。sentinel只证明setup先于测试body，具体Linux-only故障来自原官方annotations和源码；未运行的原生Windows／Linux body仍保留。

隔离提交`1351e78dc1c6775fa3958411e24262ef0a6cfc5e`已按同一四行固定，普通cherry-pick导入开发分支`6493f300041e2f9d116fdfcab718551a436f74bf`；没有强推或自动合main。原产品和CI不变，在途M2／M3源码未包含。下一步随公开进度记录普通推送并核精确远端与自己的官方CI，833966d原failure保持。

公开文档候选`610f111f0755edcfd8b4c582a7644ff79621c8ce`已普通推送本开发分支，精确远端同一；本片ignored `publication-r1`留完整push／remote argv、退出码与输出。初次官方HTTP200未观察到run，后续自己的准确push／attempt1 [43777200480](https://github.com/626619403/Ergora/actions/runs/43777200480)已确认in_progress；不预记最终成功。该候选包含本四行修正和进度／已审设计快照，没有在途M2产品，也没有后继CI再平衡。

## 自己的官方CI终态

官方HTTP200已核610f111自己的准确push／attempt1 run43777200480为completed／success，plan／六Linux／Windows八job全部success；group5为15分46秒、Windows24分42秒，原20／30分钟不变。原run／jobs完整响应留在publication-r1，原833五setup errors仍为failure。仅此候选包含本四行修正；后继M2／M3与CI再平衡不继承它的成功。
