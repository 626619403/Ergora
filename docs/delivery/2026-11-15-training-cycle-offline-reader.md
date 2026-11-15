# b2b0：训练循环离线读取整理交付

日期：2026-11-15。本地基线`d1c728087423d85ed55f06010ec81e5e1d4b2fd1`，分支`refactor/architecture-foundations`。[具体计划](../plans/2026-11-15-training-cycle-offline-reader.md)记录范围和验收；仅移除原读取函数对State对象的不必要依赖，不改原记录校验或执行／停止语义。

立项调查核过三生产owner和五私有函数，它们只使用State.root；State构造自身会创建home／取得schema锁／可能迁移SQLite，后继只读H无需承担这些义务。本片将原五函数改为显式Path并共同迁移调用，不新增reader包装、状态或公共入口；实际实现、安装／运行与审查状态在下文逐步记录。前片固定本地提交已核9份staged blob／tree；其远端门禁仍保持。kernel专家保持v3。

## 实现与首轮验收

原五函数现已接收Path，三个owner的全部调用已迁移；没有新产品文件或方法、wrapper、State变体或执行分派。`source-ast-r1.json`将Path参数与原State.root调用做唯一归一后，三个完整模块AST与d1原版本完全相同；原记录校验、读取容量、锁、clock及异常算法没有改动。`git diff --check`通过，未新增或改动tracked测试／CI。

新core／SDK两份非editable安装各652源码／wheel／site逐字相同，产品仅原三owner变化；原283及依赖检查均通过。原授权／ready、来源完整性、恢复、可见停止／排空、实际registry最后gate及完整架构已选择在新SDK安装运行，尚无终态。

实际新core解释器离线读取两份历史schema1／2原件时禁止State构造并持有真实schema排他锁；0.091秒完成，原home全部文件清单／字节保持，不存在的home也未被创建。此项只认证原记录读取，无重新授权、runtime查询或执行。初次选取的birth-consent夹具在原测试结尾故意保存了`confirmation=1`的坏授权，被同一原算法正确拒绝；随后选择未损坏的parent-drain原件，未修复／改写旧夹具或修改产品。原拒绝重现的stderr／SHA及有效原件观察分别保留在私有`offline-originals-r0-corrupted.*`与`offline-originals-r1.*`。

## 最终本地验收与审查接续

原新安装相关回归终态27通过／57.10秒（驱动58.688秒），包含11个展开授权／来源／恢复／stop／drain／实际registry用例和完整16项架构。JUnit／stdout／退出码一致，错误／失败／跳过0。`final-identity-r1.json`再核两个652产品与原manifest、177测试／示例冻结副本保持；源码只有原三owner变化。`owner-closure-r1.json`核本次1个原budget owner活匹配0、验收路径进程0；没有发送信号或全机器清理主张。

自身原`ergora-structure-review@1.0.0`真实运行20.475秒，16份完整文件／427,107B和三个祖先资源完整进入stdin，需求／维护性两轴approve；用户授权Codex回退，不声称异后端成功。供稿时回归在途，原回复只批准供稿范围；独立reviewer另核这里的实际终态和原件。新的fresh-context产品审查正在进行，尚无最终结论。kernel专家继续保持v3。

前片43d自己的官方CI最后可读时七job success／Windows在途，09:49 UTC匿名REST返回403／remaining0，reset10:23:02 UTC。原件保存在training-cycle-gates/ci-b1，不在reset前重复查询；没有把观察不到终态视为CI失败或成功。本地后继实现可继续，远端按原精确门禁接续，不将未核发布写为完成。

新的fresh-context[独立产品审查](2026-11-15-training-cycle-offline-reader-review.md)已最终本地需求／维护性两轴approve，开放0／0。原7,132B报告SHA256 `176bc9a8d4fbb2a5ae043ff5ed6711abf34af0dbcee32957f4eb55df4ef41214`保留；独立核完整八文件、三个原owner机械AST、652双安装／177测试副本、27终态与实际原件读取，并额外禁止State._open／sqlite3.connect，持真实schema锁检查完整目录／字节仍保持。唯一旧状态措辞已修，产品无需修正。本地可固定提交供后继b2b恢复；远端发布与自己的CI仍按前片准确门禁分别接续，不把本地approve写成已发布。
