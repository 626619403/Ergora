# B3.3b 原生锁内准入来源协议：独立产品审查

日期：2026-11-15。评审者为新的 fresh-context agent `training_executor_protocol_product_audit`，未参与设计或产品实施。先读原始要求、固定 r2 合同、原 reference／native owner 和仓库规则，再读候选与作者交付；使用 maintainable-project-delivery 独立审查 brief 和 ergora-codebase-quality 三项引用。本报告评价来源准备及原锁内接缝，和此前[独立计划审查](2026-11-15-training-executor-protocol-plan-review.md)分开。

|范围|需求符合|结构维护|
|---|---|---|
|固定 r1 产品与本地验收|approve；开放 0|approve；开放 0|
|最终作者三份状态文档 r2|approve；开放 0|approve；开放 0|
|最终暂存与 patch 仓库元数据|approve；开放 0|approve；开放 0|
|精确发布与自己的 CI|approve；开放 0|approve；开放 0|

本次范围内没有发现需要修正的可达产品或维护性问题。本片的固定发布、自己的必要 CI 与同片终核已闭合；后继受管执行、全后代停止或自动循环继续按 c 片合同办理。

## 固定审查身份

实施基线为 `75bc99d788a9cef292b7c41eb7e01ac03d13de47`；相对原设计基线 `5182bfa03f536d4090b91014f97eedda1c5d2d3a`，该前置提交只有测试观察等待及记录变化，产品保持。原始要求 SHA256 为 `52f3556a4fa8f0ff846cfc0761146fcd64dd53c0fe949deac5f65f35aed9560d`；固定 r2 设计 scope 为 `f8200b5fc9e22e23336eb66ef3b8c56a2d49d3fc69d060fb4bfd759203c3b040`。

产品候选为 ignored `.ergora/checks/training-executor-protocol/product-scope-r1/`，scope SHA256 `1c9b7b80172258d6697a2e5d752c38abefb81aaf84019803ba2a20425e881287`，14 份全文逐项符合清单，完整 tracked diff SHA256 为 `1919a746a3f528a2ac95ad6170bab38d2b302cf8d3c70069ebf770f1f45c0931`。三份新文件由全文单独覆盖，没有只审 tracked diff。

产品／测试范围为 `src/ergora/reference.py`、`cli.py`、两个 `data/native-runtime/training-executor-admission-v1` 资源、原 `test_reference.py`／`test_training_runtime.py` 和新 `fixtures/training_executor_client.py`；文档为总计划、本片计划／交付、训练手册、两份架构文档及前置发布记录。另追查 `training`、`registrations`、`services`、`tasks`、两类 reference worker、原 `agent_platform.training.run-local`、core／Sandbox、原实验 fixture 和显式 CI 分组。根、源码和 tests AGENTS 及组件变更协议均已读。

## 产品与维护性依据

|边界|实际检查与结论|
|---|---|
|原来源与兼容|原 manifest SHA256 仍为 `1f39b63b9c4966a0cd3d870047818924238615d10dcf7b85945814f7c8074943`，283 文件逐项相同，其中 platform 279。legacy 仍按原用途选 Python，保持规范化 Path 返回；探针确认非 Python 与仅 training 才选的模块没有被偷偷扩大到普通 legacy 校验。|
|准备与中断|[reference.py](../../src/ergora/reference.py) 第 140 行起只准备新目录；复制前独占创建空 descriptor，实际先 fsync 文件及新目录。固定 Git check／apply 后核完整 279，再写、同步最终 descriptor 并重新完整核验。首 copy 前、完整 base 后 Git 前、最终 descriptor 半写三种实际故障注入均被 validator 拒绝，完整 base 不再回退为有效 legacy；设计 R1 的产品修正已成立。|
|来源声明与完整文件|同文件第 92 行起只接受内置 descriptor 原字节，限长、lstat／no-follow／fstat 拒绝链接及特殊文件；无效声明没有 legacy 分支。descriptor SHA256 为 `d7e2b706599c6fcbb874a1a1dbec8b9875df817dc71ffa455801e48c240c2c55`，delta 为 `45af28237aff0ffd066fe4a91064831facfaf5f6d8d50945081a5214907c93b9`，唯一派生 executor 为 `feed0fa7574ad67e9d866adf41659d3288d1e4cc90178be2db830ea124388bca`。新协议即使 `training=False` 也核全部 279，非 Python requirements 篡改会拒绝。|
|同锁与错误归属|[固定 delta](../../src/ergora/data/native-runtime/training-executor-admission-v1.patch) 第 16 行起保留原 flock，result 先返回，随后在原业务 try 之前拒绝不确定 started／无 hook 接管 managed 命名空间，再调用 callback。拒绝直接传播，未生成业务 started、Git 或 result。新检查保护持久身份与并发交错，放在持有该不变量的原 native owner。|
|原算法保持|将派生完整模块仅去掉新增 import、keyword 参数及两个新增 guard 语句后，完整 AST 与原模块相等；Git、两臂、Sandbox、archive、track、result 没有第二份实现。已有 result 的早返不运行 callback，也不被解释成受管 stopped。|
|调用者与职责|准备接口的真实消费者为薄 CLI；原 validator 已由登记、服务、任务、训练和 worker 使用。完整文件校验 helper 同时服务准备与读取，descriptor helper 隐藏声明的读取／身份义务；均是原 owner 内聚的私有算法，不需要额外协议类族、包装模块或全局总线。CLI prepare 分支未构造 State，也未调用安装器、实验或执行器。|
|权限及后继|生产源码没有新增调用 `process(..., admit=...)` 的受管消费者，也没有修改 budget owner／intent 或能力 schema。来源识别不会给旧 owner 执行权；显式执行请求、出生能力、原 run/history/memo/request 最终 admission、attempt／ack／stopped 和全后代停止仍属于 c 片。新独立 native 状态目录及所有 writer 同协议的前提已写明；kernel 原 v3 提案路径保持。|

## 实际验证与测试价值

作者原件并非仅凭汇总接受。本次独立核对了 30 项 evidence-index 的字节数／摘要，index SHA256 为 `f6830856a86b6a286d2b493c530a67f592a81f3b92fb8788f80d9a63bf1c8878`；安装测试 174 份冻结输入符合 scope，产品／测试与候选一致。

|证据|核实结果及范围|
|---|---|
|源码原两 suite|39 passed／75.63 秒，外层 77.210 秒；原命令、XML、stdout／stderr 一致。|
|新非 editable wheel 与两安装|wheel SHA256 `cf9c1caed3bb5b0bff70f198872484cdaf63b29a5193f136cbc8805fe635a676`；650 源码／wheel／core／SDK site-packages 文件逐字相同，无源码 editable 路由。另实际校验 wheel RECORD 657 项、每套安装 RECORD 662 项；两套 283 PASS 与 `uv pip check` 成功。core 无 Temporal，SDK 为 1.34.0。|
|安装回归|129 passed／137.80 秒，外层 138.984 秒，零失败／错误／跳过。共五个 suite：reference 18、training_runtime 21、registrations 61、training 13、完整 architecture_boundaries 16；源码通过与安装通过分别成立。|
|真实 core CLI|四命令／2.960 秒：原 verify、含空格新目录准备、来源复核、重复目录拒绝。实际 280 文件含 279 来源与 descriptor，重试字节保持；无控制 State／venv／SDK／服务或 runner。|
|自身原模板|`ergora-structure-review@1.0.0` 实际 Codex 75.791 秒、两轴 approve；20 全文 393946B 与三份祖先资源完整进入原 stdin。原结果 SHA256 `dc78a345f7abbba712dfe20ff0d66c587b000911a466b487b7ad40844328ef10` 与实际 run 相同。它只审完整供应文本，不代替本次原件、安装或 CI 核验；未宣称异后端。|
|独立便宜检查|`python3 -I -S -B` 下两个 stdlib 脚本分别 1.242 秒、4.447 秒通过；包括上述三种准备中断、真实 fsync 顺序、legacy／新协议范围、完整 AST、六种 started／managed 文件／目录／悬空链接、callback 持原 flock 且拒绝无业务结果、已有 result 先返。相关 changed-file `git diff --check` 通过。|

新测试落在原来源与 native runtime 接缝，保护半成品被误认、错误来源、锁外预检竞态、重复执行和历史结果重入，未增重复 CI job。真实子进程 fixture 调用完整派生 process 和原 flock：手工入口写 started 后在 Git 接缝 `os._exit(73)`，待执行入口随后拒绝且不调用 hook。干净路径保留实际 Git clone／两臂 worktree 和 CPU `pass` 命令，替换 Sandbox 与 MLflow 叶；它证明原负 gate、negative-result 与 completed-read 路径可达。测试没有用 mock process 返回替代锁原子性。

独立检查原件在 ignored `.ergora/checks/training-executor-protocol/product-audit/`：`artifact-verification-r1.json` 和 `probe-results-r1.json` 记录准确边界；对应脚本也保留。探针中的 native 函数使用精确提取的完整 process 及原 core 读取／require，避免引入业务依赖；这部分只证明 guard 与锁顺序，真实完整模块／子进程集成另由上述已核安装测试覆盖。

未重新运行 pytest、安装依赖、启动服务、调用模型、训练或 GPU；未联网核前置 CI，未修改产品、提交或推送。原 Sandbox、MLflow、成功 archive、真实训练／质量／性能、断电后的文件系统保证、Windows 原生执行及后继受管生命周期均未在本次认证。新协议依赖当前可信用户边界，不承诺阻止不合作的旧 writer 或之后任意改写来源。

## 最终作者状态文档补核

另核 `.ergora/checks/training-executor-protocol/author-final-docs-r2/` 三份最终作者文档，scope SHA256 为 `f82f7963adc306edba3f6cd3ccfbe6b064f6eac16536c45c4c4654a123d6746d`：总计划 56685B／`bfc864f6b8c54ffaa378041ee809b8182c8ff9c0878d79a4908d356c2a357022`，本片计划 14400B／`cd675ba17d08873dbe13a0b4ec5f7d8f89f554dabeeb056d49e0875a6ba1076a`，交付 8448B／`08519642d8b91e17093ee9bec8c24402a5c21054e0dfbed7a9ea8c8d563ded04`。三份公开文件与冻结全文相同、148 个本地文件链接存在，七份产品／测试仍逐字符合产品 r1。

状态追加准确区分本地验收、前置 CI 接续与本片发布／自己的 CI，保持原失败和 c 片待办。补核指出计划第 38 行仍称安装／产品审查待验，作者已更正；r2 相对最终文档 r1 仅这一句变化，属于已关闭的状态同步。私有 `author-docs-verification-r1.json`／`author-docs-verification-r2.json` 保留两次身份与处置。文档检查器首次误用 r1 scope 字段出现 KeyError，原错误另存；改用已读的 r2 封套及原 r1 产品清单后通过，产品未为检查器改变。

## 最终暂存与仓库元数据补核

同片续核 `.ergora/checks/training-executor-protocol/publication-staged-r1.json`，scope SHA256 为 `4f164c0bca7c879235f772eeb35e00c1e9b7f21b721cc8121273dd63b4daace8`，暂存 tree 为 `b8eb6430de9f388895464a9fb6ecd10c1e87ad14`。17 份 Git blob、字节数与摘要和当前 index 全部相同，五份 Python AST、240 个 Git tree 文件链接及完整 cached diff-check 通过。七份产品／测试仍等于已验产品 r1，原 reference／manifest、scripts 和 CI 没有新差异；未暂存的 c 片草案不在这个对象内。

新增 [.gitattributes](../../.gitattributes) 仅在原规则后追加一条注释和 `src/ergora/data/native-runtime/*.patch whitespace=-blank-at-eol`。固定 delta 的三个空 context 行必须保留前导空格，原完整 diff-check 对此报尾空白，原失败保留。1.452 秒的隔离 Git 探针用同一 patch 字节复现原三处报告，再确认新规则只在该范围放行尾空白；patch 的 space-before-tab、blank-at-EOF，普通源码及范围外 patch 的尾空白仍会报错。规则不改变产品／wheel／安装或执行行为，无须重复已验安装。独立原件为 `product-audit/staged-verification-r1.json` 及脚本。

另核总计划、本片计划／交付和前置交付的终态追加，符合原 reviewer 维护的[前置独立终核](2026-11-15-phase-publication-wait-regression-review.md)：固定 75bc 自己的 run 43672292421／attempt 1 八 job／30 必要步骤成功、两轴 approve／开放 0／0，原 518 失败保持。此处读取原评审者的终核与来源范围，没有替其重新联网认证 CI，也没有将前置成功授予本片。本次两轴结论保持 approve／开放 0／0；上述暂存补核的报告原文已纳入下述固定提交。

## 固定发布与自己的 CI 终核

本片固定提交为 `6c7e9d924f822e60a54ce8c0686a56758ae0359a`，父提交为原实施基线 `75bc99d788a9cef292b7c41eb7e01ac03d13de47`，tree 为 `47da648db4a690cb844382eaf577592237979b75`。最终 `publication-staged-r2.json` SHA256 为 `c84518216f43ebdb171b12e71deb764f932b75b8e7377d6e45da4c98735002f4`：17 份 Git blob、五份 AST、242 个固定 tree 链接和完整固定 diff-check 均通过；16 份非报告 blob 与已审暂存 r1 相同，提交内的本报告原文 SHA256 为 `9a3a930371e2029c5652ca5253011c4f8c35078ecb2df8e5d987a04745611457`。普通 push exit 0／5.574 秒，SSH 完整分支 Ref 返回同一完整 SHA。原 reference／manifest、scripts 与 CI 无该片新增差异。

按追加授权实际只读访问 GitHub 一方来源：commit HTML 的完整 oid／parent、branch HTML 的分支名／currentOid 和 Actions／run 的完整提交、run／attempt 身份均相符；17 份固定 SHA 的 raw 响应全部 HTTP 200，逐字等于最终 scope 及固定 Git blob。匿名 REST 的 commit／ref／runs／run／jobs 五次请求均为限流 403，原响应与头部保留，身份结论使用上述一方 HTML、navigation 和 raw 证据。tree 由本地完整 commit 对象绑定，没有把 REST 失败记为远端 tree 认证。

另以 `git ls-tree`／`git cat-file --batch` 读取固定 6c7 的完整 blob，在 1.567 秒内确认 650 份源码与原 wheel、core／SDK 各 650 份安装逐字相同，174 份冻结测试／示例输入、七份产品／测试和 283 份原 reference 也与固定发布相符。私有 `fixed-installed-verification-r1.json` 保存准确边界；此补核没有用后续工作树的来源或测试字节代表本片，也没有重跑 pytest、安装或业务执行。

本片自己的 [Portability #231](https://github.com/626619403/Ergora/actions/runs/43674493548)，run `43674493548`／attempt 1，精确绑定上述 6c7 push，GitHub 显示总时长 23 分 37 秒并以 success 结束。2026-11-15 04:19:51 UTC 的完整 navigation 为 `totalCount=8`、`hasMore=false`，唯一 job 名称恰为 plan、Linux Python 3.11 的 0–5 六组和 Windows Python 3.12 全量组，八项均为 completed／success。

2026-11-15 04:20 UTC 实际重新取得 run／Actions 及八份 job HTML，逐项核实 30 个必要步骤唯一出现且全部 success：plan 的显式分组读取一项，六个 Linux job 各四项，以及 Windows 的 wheel／reference／原生回归／PowerShell 5.1 安装升级／上传五项。八个 job 的显示头部与导航结论一致，步骤 log URL 均绑定精确 6c7 和对应 job；固定 workflow 与六组清单的一方 raw 也等于同一 Git blob。这里核实平台发布的步骤结论，没有下载完整日志或产物，也没有据此认证真实 GPU、训练质量／性能、原 Sandbox／MLflow 成功路径或后继受管生命周期。

独立原件位于 ignored `product-audit/ci-publication-r1/`：67 个只读捕获记录含 62 个 HTTP 200 与上述五个 403，所有响应字节／摘要已重新核对；`ci-originals-index-r1.json` 索引 104 份文件，SHA256 为 `9aa65860ac845881316ccbe4bdab4272a5d7d8137bd8fef2a712b4c591e4fb2a`。`final-ci-audit-r1.json` 保存 run／attempt、8／30 完整结果、固定 raw／workflow、身份依据和未获取全文日志／产物的范围。固定发布及自己的必要 CI 两轴 approve，开放问题 0／0，本片同片终核闭合；结论只归本节固定字节及其自己的 CI，后继产品继续独立验收。
