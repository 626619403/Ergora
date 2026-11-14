# F10a 记忆有效期：独立结构审查

日期：2026-11-14。审查者：fresh-context `memory_validity_structure_review`；未继承实现对话。固定基线为 `f47cd50fcce600fba92f64aff73982012f6e31c9`，审查对象为其上的未提交 F10a 工作树。依据 [原合同](../plans/2026-11-14-memory-validity.md)、`AGENTS.md`、本地 `maintainable-project-delivery`（含 independent-review brief）及 `codebase-design`。本审查仅写本报告；未修改源码、安装、执行外部写入或提交。

## 分轴结论与范围

- **Compliance：最终本地 approve。** 有效期、继承／明确清除／恢复、默认有效列表、显式目录、ReMe 在途过滤及 schema v5 的职责符合原合同；最终安装、实际旅程、自身模板与收尾原件已由本轴补核。未发现需要源码修复的实证 finding。精确发布及自己的CI尚待，不能据此关闭发布验收。
- **Maintainability：最终本地 approve。** 语义集中于原 memory／State owner；未引入第二记忆权威、调度器、插件 seam、新依赖或额外表。新增函数／局部辅助有实际调用或明确的内聚职责；最终产品与源码审查身份相同。必要性能静态检查未发现新增阻塞项；不代表规模性能实测。
- 当前开放 finding **0**；本片精确发布／自己的CI待补核，Windows原生尚未作为本候选通过范围。

直接审查五份生产文件 `src/ergora/{memory,state,cli,web}.py`、`src/ergora/data/console/memory.js`，四份回归 `tests/test_{memory,state_migrations,state_backups,web}.py`，以及 F10a 新计划／交付、F10 总计划、`docs/PLAN.md`、使用手册和当前架构。读取邻接的 `agent_runs.py`、控制台 `app.js`／`api.js`／`ui.js`、CI 分组和迁移／备份调用。C3 文档变化仅作为上一片发布账补核识别，不在本片产品行为结论内。

九份生产／测试文件与提供的初始 `review-r1` SHA-256 记录逐一相同；实际读取了其后更新的计划与交付，未用旧文档快照替代。生产身份如下，供后续补核比较：

|文件|SHA-256|
|---|---|
|`src/ergora/memory.py`|`d1be8d9e4199ce1e87ea487a5a06badd1a84e5a7979f27a99cbee4d692fd7475`|
|`src/ergora/state.py`|`4bb638c9435a0c39e306109b628c6c79b96f1d8381b84140d78be188ed68f0f9`|
|`src/ergora/cli.py`|`e7ff0f4ac177fbe417b66b96efbc94bb9384a208bd9116469d44b2091b60c6de`|
|`src/ergora/web.py`|`376164391f9660c4bc4e7b2be077e14a5a5a23c291779e57522097fbffeffb02`|
|`src/ergora/data/console/memory.js`|`637324029b5a741dc84224f23c4c4f4ee20d8df4d2051aac9f4a36d8350f4bde`|

## 调用、控制流与维护性证据

`memory._expiry`（14行）统一负责输入校验、UTC 归一和持久字段解释；save 与 `_validity` 实际调用。类型／语法／无时区及 UTC 范围溢出均有可达外部输入，统一转换为已有 CLI／HTTP 能处理的 `ValueError`，无需再在调用者重复日期 guard。`_validity`（26行）由 catalog 和 sync 调用；sync 逐镜像重新观察时间，保护前面远端请求耗时后才到期的后续镜像，不能简单删除为重复判定。

`catalog`（33行）向 CLI、HTTP 两个生产文件提供显式读接口，且被原 records／sync／search 消费。它在一次资料读取后取一个服务端观察时刻，再统一分类；records 和检索只取 valid。完整目录没有直接接入 agent recall；`agent_runs.run_agent` 仍只通过原 search 获得过滤后资料。历史读取不调用过滤、不因时间流逝改写修订。

save 的 Ellipsis 默认值（61–90行）承担「未传」语义；直接 `None` 只表示清除。更正继承在原 `BEGIN IMMEDIATE` 内按最新 revision 读取，避免上游读取再写入的竞争。CLI 使用 `argparse.SUPPRESS` 和互斥选项，仅在字段存在时转交；HTTP 使用 `exclude_unset=True`，未把默认 `None` 当成显式清除。restore 显式传所选历史的期限，包括缺失与已过期时间，避免恢复时继承错误的新期限。

ReMe search（203–221行）保留请求前 revision 集合，请求后重读本地目录及时间，同时核路径、去重、当前有效性和 revision 相同，只返回当前本地正文；远端正文与后来的替代修订不被旧命中授权。sync 的跨进程文件锁保持原项目投影串行；每个 SQLite context 均在 `_job` 前退出，没有 SQLite 写事务跨 RPC。远端清理仍是显式同步与 watcher 最终可见性，不宣称远端瞬时撤销。

`_schema_v5` 是 State 迁移序列的必要固定步骤，沿原事务／离线备份替换21表围栏，不为一次迁移引入通用 registry 或第二存储。旧 reader 无法撤销的限制与停旧进程升级要求已写入合同、用法和交付。

页面 `read`／`readSequence` 是 view 内的私有算法，供检索、目录、历史读取调用；它同时丢弃逆序回复与已脱离 DOM 的回复，错误路径也受同一世代限制，避免原 ui 统一错误通知把迟到错误显示到新 view。原 app 的每次 render 替换 view 节点，与 `cards.isConnected` 的判断相容。`expiry` 只封装两处相同展示，未扩展成全局日期模块。时间表单使用文本并预填服务端原期限；清空显式传 null。到期仍可更正／查看历史，删除态只保留读取入口；无后台轮询。

新增两项 memory 回归保护到期边界、继承／清除／恢复与在途静默陈旧命中；原 HTTP 旅程补字段缺失和 null，原完整备份夹具直接带过期字段，原迁移 suite 加独立 v4 夹具并扩展既有参数矩阵。未新增 CI 分组或重复执行框架；表／触发器断言依据当前表集合，未把本片默认规模写成新的通用限制。

## 只读检查与未验项

本审查使用 `python -B`，所有小例只在 SQLite `:memory:` 和进程内改动，没有创建 runtime home：

1. 直接调用原 owner，确认时区归一、保存省略继承／null 清除、历史恢复原期限；`observed == expires_at` 时 records 排除而 catalog 为 expired。无时区、非字符串和 UTC 转换上下界越界均为 `ValueError`，两个 UTC 范围边界小例确认最终 `OverflowError` 转换有效。
2. ReMe 小例同时包含稳定、到期、删除、更正、重复命中；远端请求中改变本地状态，结果仅保留稳定记录的本地正文与正确 observed_at。
3. 内存顺序执行原五步迁移，实际21表／63个v5触发器；以v4 writer函数插入21表均被围栏拒绝。
4. `EXPLAIN QUERY PLAN` 确认 catalog 使用原 `(project,id,revision)` 索引和相关子查询的 covering index；排序临时树与 SQL 都是基线已有行为。省略继承仅增加事务内一次点查；远端搜索保留三次资料读取，把原无用途的请求前读取替换为返回后的必要重核。未见理由预建新索引／表／缓存或调度。
5. 实际解析 CLI 三种字段状态：省略无属性、`--no-expiry` 为 None、`--expires-at` 为输入字符串。当前系统 Python 无 FastAPI，HTTP模型小例明确未执行；未安装依赖补齐。

保留并核读开发记录：最初旧安装包误跑的7失败／19夹具错误和源码首轮 collection 失败均未被标成功；随后源码六 suite **78 passed／1 skipped，14.22秒**，但早于最终 OverflowError 转换。该记录不是本审查重跑，最终包不得继承其完整验收身份。JS语法及diff检查是实现方已报告的静态结果，本审查未将它们当浏览器交互证据。

源码审查时待在同一审查追加补核：最终非editable包及283冻结身份、最终安装回归、真实CLI／HTTP／页面与三个宽度、页面读取交错的实际证据、自身原审查模板，以及本片精确发布和自己的必要CI。以下补核关闭前述本地证据项；精确发布／自己的CI仍待。未执行真实ReMe部署、Windows、规模性能、GPU／训练／质量或F10b正式Task冻结；本审查不代替这些范围。

## 同轴最终本地补核（2026-11-14）

同一原审查者读取更新后的合同／交付及[公开证据摘要](evidence/2026-11-14-memory-validity.json)，逐项直接读取其 **86份**原件，大小和SHA-256均相符。五份生产文件仍为上表身份；按「排序UTF-8路径＋NUL＋原字节＋NUL」重算聚合为 `d716290cb8293ae4f34e152f37cda0186e65eb2bfe13c2fbbf8d85bca6eb24db`。本次只读原件、内存验证和图像查看，仍仅修改本报告；未重跑验收或生成替代成功记录。

**最终安装。** 直接解读wheel，独立复算wheel／安装的每行有hash的RECORD条目：wheel583项／RECORD583行、安装RECORD588行，全部hash和大小相符。575份产品在wheel、安装、构建源码快照和当前源码逐字相等，文件集合也相同；283份参考文件逐一符合冻结manifest。安装metadata指向本地wheel且无editable标记。候选wheel SHA-256为 `493e735b49e3741430211d07999754f058cd3968c3083a6015334c0aed82d3b2`。

安装回归原命令以最终venv的 `python -I -m pytest` 在源码快照测试目录执行原七suite，日志收集85项并记录 **78 passed／7 skipped，48.96秒**；原monitor为50.538秒、退出0。七跳过为Linux上的平台范围，未改称Windows成功。补用最终安装环境 `-I -B` 只构造HTTP模型，实证缺失输出 `{}`、null输出 `{"expires_at": null}`、新字符串原样转交，关闭首次源码审查中系统Python缺FastAPI的小例未验项。

**迁移与CLI原件。** 读取原commands／stdout及schema4备份、before-restore、完整snapshot和最终control数据库，均用只读immutable连接，不构造State。固定旧State源码与基线git原字节的SHA一致；schema依次为4／5／5／5。原legacy记忆的整条数据库原行保留；before-restore与snapshot全部memory原行相同，且这些行在页面旅程后的control中仍保持。CLI到期记忆修订1–4保持，最终原期限修订与CLI输出相同；原legacy仅一个修订，beta无memory行。18条命令记录均退出0，其中包含Git、旧／新CLI，未视为18次memory命令。原升级记录保留旧重开拒绝、已开writer被fence拒绝及旧reader仍可读取的结果；原v4备份hash、schema和原行均直接核对。完整离线备份、verify及原home恢复的实物与原期历史对应。

**实际页面与失败续接。** 直接核对capture源码和原requests：62条HTTP均200，其中33份API正文可按原JSON编码独立还原并吻合各自字节数／SHA。mutation严格只有四条，方法POST／POST／POST／DELETE、同一id修订1–4；期限分别为原到期、清除、恢复原到期、删除。最终数据库该id全部四个修订正文和来源均空且status deleted；原CLI过期history和legacy原行未变。

首个basic原stdout确为 `Error: renewed memory visible by default`；后续continuation从已成功的修订2继续，只读确认无限期显示后完成原恢复／删除／检索，没有再次save。这与四条mutation及连续revision吻合。接受合并旅程的实际行为证据，保留首脚本失败，不据wrapper退出码把它改成首脚本无人干预成功。

直接读取三类lifecycle脚本与原返回：拦截器先 `route.fetch()` 取得真实服务端响应，再延后交还原响应；已实证旧catalog不覆盖后发search、切项目后旧history不弹modal、切tab后旧catalog不覆盖新页。未用替代JSON伪造成功路径。六张1440／960／390目录和更正表单截图均实际目视：状态／观察时刻／原期限可读，危险HTML样例呈文本，已删除卡片仅有历史入口，表单及页面无横向溢出；原测量与截图一致。console原件为零error／warning，关闭记录、stop文件及原monitor收尾对应；补核时loopback端口仍关闭、所记浏览器daemon进程不存在。

**自身原模板。** 用最终安装的只读 `inspect_input` 对原prepared input及实际run input重新编译／校验，两者均为摘要 `ee3a6d7153ba7abd697c98c909628af9dacc7f80c7b30fa7615ad035127cdf7c`。10份完整文件215,539B分别与构建快照／packet-index的大小和SHA相符，全部原字节位于task，完整task位于prompt。root及root/review的全部三项祖先／叶resources位于实际stdin，prompt与stdin逐字相同；prompt SHA `59c8e13c39be76e08dab3faeb7aecd5510395b61598fa1fa043f6febf2a6cbe9`，实际run结果与保留original-result逐字相同，结果SHA `700c49fdba308eab776980f85097f5c379a21d121aa488a666f20c7c26f87d29`，decision approve。原34.835秒调用binding为Codex，授权fallback记录明确，未计作异后端或替代本独立轴。其输入文档保留当时尚未完成UI／独立评审的状态；生产文件与最终候选相同，没有把历史模板输出扩大为后续旅程实测。

最终本地补核未产生新的compliance或maintainability finding，开放 **0／0**。可继续本片普通发布与精确远端、自己的必要CI核对；此时发布／CI尚未发生，C3的CI成功不用于本候选。ReMe外部部署、Windows原生、规模性能、GPU／训练／质量、正式Task新冻结及后续真实业务采用继续保持未验范围。
