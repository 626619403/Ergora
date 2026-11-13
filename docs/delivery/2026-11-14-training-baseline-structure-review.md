# F9b4a 独立结构／维护性审查

审查者：fresh-context 独立结构轴 `baseline_structure_review`；日期：2026-11-14。未继承实现对话；先读项目 `AGENTS.md`、[当前计划](../PLAN.md)、[原始准备合同](../plans/2026-11-14-training-preparation.md)，再查原训练／发布／读取 owner、实际差异和新增文件全文，最后读[作者交付](2026-11-14-training-baseline.md)。采用 AIHERO 索引中的 maintainable-project-delivery、codebase-design 及 code-review 的职责、耦合和冗余标准；本轴本身是该方向的新独立审查，不递归委托审查。

**当前最终本地结论：结构／维护性通过，开放 finding 0；首轮 1 个 P2 已经最小修复及 r2 安装补核关闭。** 精确 r2 产品、实际浏览器生命周期、保护原件、收尾、自身原模板和公开证据已完成本轴补核；所查需求符合性中的 CLI 输入容量缺口已关闭，完整需求／正确性结论仍归[独立需求轴](2026-11-14-training-baseline-spec-review.md)。普通发布／远端 Ref 与本片自己的 CI 仍待。以下保留首轮身份、finding 和当轮待验范围，最终本地结论见末节。

## 固定范围与身份

基线及审查时 `HEAD` 均为 `fad53478c9261157b3016563b410b9d4b4d85b9d`，候选未提交。实际 `git diff <baseline>` 与 `.ergora/checks/training-baseline/review-r1.diff` 逐字相等；14 个 tracked 改动和 5 个 untracked 新文件共 19 路径，长度及 SHA256 全部与 `static-r2.json` 相等。该清单自身 SHA256 为 `37f5263d00e782ceca316723085bd84856654331aab823f6c08bc28770f852e1`。

11 个产品／测试／CI 路径的实际组合 SHA256 为 **`a31f8d95e7943ea4b841cd759868a958cc99b36bba49df06ccd0e8c00e1096cc`**，已按清单路径、NUL、文件完整字节、NUL 的顺序独立重算：

- `src/ergora/{cli.py,reference.py,reference_training_context.py,reference_training_setup.py,reference_training_submission.py,training.py,web.py}`。
- `src/ergora/data/console/training.js`、`scripts/ci/linux-groups.json`。
- `tests/test_architecture_boundaries.py`、`tests/test_training_baseline.py`。

另查 README、`docs/PLAN.md`、`docs/TRAINING.md`、`docs/WINDOWS.md`、本片计划／交付，以及旧 F9b3 的需求／结构审查报告差异；后两份仅追加其原发布身份／Ref／CI 待验记账，没有重写本片产品。5 个新增文件均已全文读取。原参考目录无差异，未修改 283 冻结资料。

## Finding

### P2：在 CLI 输入 owner 限制原始 baseline 文件读取

位置：[src/ergora/cli.py:927](../../src/ergora/cli.py#L927) 和同分支第 930 行。两个新增命令均先执行 `args.baseline.read_text()`，读取并解析整份用户文件，然后才进入 `training`／受监控的 reference 子进程。setup 第 30–32 行限制的是按原 writer 重新序列化后的对象；它不能限制 CLI 已读入的原始字节。例如在有效 baseline 前追加超过 1 MiB 的 JSON 空白，完整读取、解析后对象仍很小，预览与初始化都可接受该超限源文件。

这违反原计划“输入与最终文件受原 1MiB 读界限约束，不截断”的输入约束，也把无界内存／读取工作留在 process monitor 之前。普通配置错误最终可见，不能替代此处的容量约束。最小修正是在既有 CLI 的两个 baseline 操作中共享一段局部解析：以二进制方式最多读 `1_048_577` 字节，超限直接报错，再 `json.loads`；无需新增 helper 或第二套验证器。HTTP 的既有 4 MB 请求封套和 setup 对原 writer 格式的 1 MiB 容量检查分别保留，并在手册写清两者含义。本轴未修改产品，待修复与原件补核。

## 职责、复用和必要控制流

`training.preview_baseline`／`initialize_baseline` 分别被 CLI 与 HTTP 两个生产入口实际使用；它们保留发布项目／修订 owner，Web payload 只承担输入 schema。`reference.training_setup` 属于既有 reference 进程 seam：复用 `_training_process` 的安装身份、每项目 config／state 环境、有界运行及收尾，不将初始化引入 Task、runner 或 start 路径。

新 `_TrainingProject` 的两个生产消费者是 `reference_training_setup.py` 的实例和 `reference_training_submission.py` 的 `_Submission` 子类。构造、`document` 和 `registration` 对照固定基线均为机械提取，仅错误文字从 submission record 放宽为 training record；原 16 MiB intent 特例仍由 submission 调用参数保留。其职责是共同的 canonical 执行路径、原有界 no-follow JSON 读取及注册／control-home 核对，没有携入实验提交身份或调度语义。取消继续借原 submission 读取 start 身份，未复制该算法。未要求其他无关消费者加入这一提取。

`reference._validate_training_baseline` 有原 reader 和新 setup 两个生产消费者，仍调用原 `perfctl.ident/commit/sha` 原语；没有建立平行 schema。setup 的完整对象与可读容量、Git 根／commit、canonical 内容 SHA、当前内容冲突、锁路径检查和发布后重读各有实际输入或持久状态路径。首次写入直接调用原 `perfctl.main(init)` 的 `.registry.lock`、锁内重复检查和原子单文件发布；同内容读取后返回，保留原字节，不新增账本或替换算法。发布后的内容核对保护真实回读，不能以预览结果代替。

`baselineSetup` 留在训练页内，只有这一页面消费者；局部函数隔离输入、预览和确认控件的生命周期，没有为假想复用另建模块。原 `ui.js`／`api.js` 已承担 DOM 文本输出、可见异常和 HTTP 错误，本片直接复用。`sequence`、输入原文、`active()` 和 `sending` 分别保护编辑后旧预览、项目／tab／home 变化、迟到回复和双击发布；普通 JSON 解析异常沿原 `button` 通知路径可见，无需重复 fallback。

新增 6 个测试沿真实 training／CLI／HTTP seam，复用原 registration 和 installation 夹具，保护同内容原字节、回执丢失、修订／完整内容确认、原注册漂移、跨项目目录及外置锁路径。没有以默认数值限制有效配置，没有为普通文案增加独立测试框架。CI 仅将新 suite 加入既有显式 Linux 分组；架构检查只登记两个实际 reference owner。未见应删除的单用抽象或重复 CI 层。

## 已核证据与限制

本轴只读源码／原件并写本报告，没有安装、执行大 suite、启动服务、提交、推送或外部写入。实际执行的轻量检查为完整 tracked `git diff --check`、5 个新文件的 no-index whitespace、68 个本地模块的 AST 依赖无环、JS 语法、19 路径身份及 196 个本地 Markdown 链接检查，均通过。no-index 对新文件返回 1 且无 diagnostic，只表示文件新增。

- 原源码 `source-r1.log` 为 **19 passed／1 failed，7.23 秒**；失败仅为测试要求 symlink 文案，而原 guard 已返回 `Path escapes trusted root`。`source-r2.log` 为修正该 matcher 后该项加原 training／submission／cancellation **38 passed，198.46 秒**。保留这两轮的实际范围，不称一轮全套。
- r1 wheel SHA256 为 `186118240d553bd463d430e4dbd423ae13ef4bc0929992d648daea2ff04d0eed`。本轴直接读取 wheel、构建快照、当前源码和非 editable 安装：全部 **570** 产品文件逐字相等，wheel **578** 行与安装 **583** 行 RECORD 哈希／长度均相符，**283** 冻结文件均符合 manifest。
- 安装 `regression-r1/result.json` 已落 `succeeded`／returncode 0，原 stdout 为 **57 passed，232.41 秒**，监控耗时 234.249 秒，600 秒界限未触发。实际五 suite 是 baseline、training、submission、cancellation 和 architecture_boundaries；不含 training_runtime，也不代表整个仓库通过。
- 已读原安装 CLI preview／init／retry／list 输出及错误 SHA stderr，状态依次为未初始化、初始化、同内容已初始化；canonical 内容 SHA 一致。实际 `-P -S` 无 site-packages 探针的修正轮返回初始化成功、stderr 为空；首轮环境搭错导致的断言失败仍在。它不是 Windows 或真实服务验收。
- 原结构模板实际 prompt 与输出目录 stdin 逐字一致，14 份完整内联文件逐项 SHA 相符，共 **245,707B**；原回复为 `approve`，结果 SHA256 为 `983361a519462f19f5498d409290216d7226bd7fc094f5c7f381680e5889260f`，记录耗时 49.805 秒，使用授权 Codex 回退。自身模板回复不代替本轴 finding。
- 浏览器 r1 的 `baseline.stdout` 原 `### Result` 已为 passed：错误 SHA 零 POST、编辑后迟到 preview 丢弃、双击 init 仅 1 POST、冲突无初始化按钮，1440／960／390 三视口的 scrollWidth 等于 width。已读实际脚本；该轮没有覆盖切项目后的迟到 init 回复，也未由本轴目测截图、核 27 件保护原件和服务收尾，不能据这段 stdout 关闭完整页面验收。

首轮唯一阻断项是上述 CLI 原始输入容量。修复后仍需核精确产品身份及受影响检查／安装；页面剩余原件、自己的普通发布／完整远端 Ref／必要 CI 另待。Windows 原生实际预览、runner 登记、prepare、F9c／F9d、真实训练／GPU、测量质量、性能收益及证据批准／采用均不在本轮通过主张内。

## r2 最小修复补核：结构通过，页面收尾／发布仍待

本轴重新读取实际修复和原 `harness.git_scope._run_git`，当前 11 路径的产品组合 SHA256 为 **`426d271430bdba818bd999be46c2ae5b06bdc6ec85c2b138e0318fe0712001ef`**。相对首轮只改变 3 个产品／测试文件：

|路径|字节|SHA256|
|---|---:|---|
|`src/ergora/cli.py`|71,684|`bdca4eca5bd037f77ae8743efbe06af3261623c6d967ac23824ded5a8d0b1589`|
|`src/ergora/reference_training_setup.py`|4,488|`17711e73d50a6b152f368d5cd144ea9920abedae577d3cc90850afbe871dfea7`|
|`tests/test_training_baseline.py`|10,154|`df19d3a1dbd2299c4c878857d39c646233ade9752847ff439b5ed196706c9d67`|

CLI 的两个 baseline 操作现共用局部二进制限读：读取上限为 1 MiB＋1，超限在解析及创建 State 之前拒绝，随后才解析并分派。原 capacity 测试中补入超过上限的空白包装 baseline，验证 CLI 非零返回及原 registry 仍未创建；没有新增 helper、suite 或第二验证算法。计划和训练手册已区分 CLI 原始文件、HTTP 4 MB 封套及原生序列化容量。**本轴 P2 关闭。**

需求轴提出的 Windows 预览 Git 路径问题也已查实际修复：setup 的两条只读命令改用既有 `_run_git`，从可信 PATH 选择 Git，保留其清理继承 GIT 环境、禁用 replacement／lazy fetch／协议、禁用 hooks／fsmonitor 的原行为；复用原 primitive，没有建立平台分派或复制 Git 执行器。该依赖仍只位于 reference 进程层，不引入 SDK、Task 或提交 owner；context、reader 和 perfctl 发布算法均未变化。没有新增结构 finding，亦不把源码可移植性当作 Windows OS 实测。

已只读重算 r2 wheel SHA256 **`e39866028ee7e4625f814e3fb23064ee7ea274d85cb2cd509c4f06d24af5ffeb`**，570 产品逐字等于当前源码、构建快照及安装目录，wheel 578／安装 583 行 RECORD 哈希／长度与 283 冻结文件均通过；两个受测 suite 的快照文件也等于当前测试。安装 `regression-r2/result.json` 为 succeeded／returncode 0，原 stdout 为 **baseline＋architecture_boundaries 20 passed，11.39 秒**，监控耗时 12.975 秒。r1 五 suite 的 57 项是先前候选的原运行，不能改称 r2 单次五 suite 通过。本轴没有重新安装或执行这些测试。完整 tracked whitespace 复核仍通过。

浏览器 r1 的后续 `lifecycle` 验收脚本在最后的重复选择当前项目／视图重建处失败，未产生整次成功回执；前段断言已经执行也不能替代完整成功。本轴保留原失败，不要求改变页面来适配该脚本。新包的实际页面生命周期、27 件保护原件和服务收尾仍待最终原件；r2 SDK-free 实际初始化和本片自身模板若补跑，也须各自按真实证据记账。

**当前结构／维护性验收通过，开放 0。** 这一结论覆盖精确 r2 产品及上述最小修复；完整本地运行出口、公开证据、普通发布／远端 Ref 和本片自己的必要 CI 仍待，不借 F9b3 或旧候选结果关闭。

## 最终本地原件补核：通过，开放 0

重新核对 `HEAD` 仍为原基线，11 个产品／测试／CI 路径逐项 SHA 与 `static-r3.json` 相符，组合仍为 **`426d271430bdba818bd999be46c2ae5b06bdc6ec85c2b138e0318fe0712001ef`**。该静态清单自身 SHA256 为 `4bbb1cfddeaa656863e63b76459d832e86b3670a135f964182d626f2db3dab99`；它生成后的本片评审、公开证据状态和 F9b3 发布／CI 记账不构成新产品候选。本轴直接比较 r1／r2 两个 wheel：实际仅 `ergora/cli.py` 和 `ergora/reference_training_setup.py` 改变，其余 **568** 个产品逐字相同。先前核过的 r2 570／两 RECORD／283 和 20 项受影响安装检查范围保持，不重写为单次最终 57 项全套。

已全文读取 r2 两份实际浏览器脚本、原 stdout、执行回执及 HTTP 捕获。两脚本退出 0，均有 `### Result` passed。错 SHA 零 POST、双击仅一次、编辑后旧 preview 丢弃及冲突无覆盖控件的断言沿真实页面执行；三视口记录为 1440／960／390 的 scrollWidth 等于 width。另已目测该三张原截图和 390 未发送表单截图，本片输入、预览、确认控件可见，无横向溢出。

生命周期脚本先 `route.fetch()` 取得真实服务的成功发布回执，再 abort 回复；页面显示未取得确认，重读原文件后以相同内容显式重试，返回 already_initialized 且字节 SHA 不变。迟到 preview 和 init 场景也先取得真实回复，持有到切换项目后才放行；新项目未出现旧确认控件／成功回执。服务器原捕获中，r2 常规项目 init 恰 1 次、丢回复项目恰 2 次、迟到 init 项目恰 1 次，另一项目 init 为 0，均与脚本原回执相符；没有靠伪造成功 JSON 替代发布。预期控制台网络错误只来自刻意 abort。r1 lifecycle 的 34.225 秒 timeout 原件保留，不能算作先前已整组通过；r2 只是修正验收同步并用新独立项目重验，产品页面字节未变。

已读 `final-observations.py` 和原 JSON，并独立只读复算：**27** 件原配置／基线 SHA 全部相同，**8** 个验收项目 baseline 内容等于确认输入且原文件字节 SHA 一致，另一项目无 baseline；specs、manifests、jobs、fences、approvals 和 integration-tickets 均未创建。验收 Git 仓库以 no-optional-locks 读取 status，输出为空。两份浏览器 close 回执退出 0 且 stdout 确认关闭；原 monitor 收尾回执均为 cancelled，两原端口在本次只读检查中也没有 LISTEN。此项是本地 web／浏览器收尾，不是训练作业停止或真实服务成功主张。

最终 SDK-free 原 argv 使用 **`-P -S`**，断言 sys.path 无 site-packages、temporalio 不可用，再仅按 spec 装载安装包并进入 setup，调用前后均检查 SDK 不可用；退出 0、stderr 为空，原 stdout 与记录 receipt 一致。该轮实际状态是 **already_initialized**，核 Git、同内容回读及原字节保持；首次无 SDK 初始化另由 r1 的原 initialized 回执证明，二者没有混称。

最终自身模板为授权 Codex 回退，原 requested binding 与 actual binding 分开保存。实际 **99,376B** prompt 与执行目录 stdin 逐字相等，5 份完整内联文件逐项哈希正确，共 **95,335B**；3 份继承资源来自 `root` 和 `root/review`，完整原文均在实际 stdin。原 result 与保存副本逐字相等，decision 为 approve，SHA256 **`f7a1fce083795dcfbf1aba2731c339a51136588e6a0c43845b4251134610a69e`**，原记录 23.170 秒。该轮覆盖最终最小修复，不将模型回复当成测试、Windows OS 或异后端成功。

本次检查的[公开证据](evidence/2026-11-14-training-baseline.json)为 **11,613B**，SHA256 **`c3bfb0cf989d5f1bb6c2ab68dd0ffcb3ef52debdfcc34611d27a4b21be92c8c3`**；其 **26** 份私有原件引用已逐项重算长度／SHA，全部相符。公开结果对 r1 原失败、r1 57 项与最终 r2 20 项、最终同内容 SDK-free 回执、页面、两轮自身模板及未验维度的区分与原件一致。其评审状态字段在报告写入后的常规更新不被当成产品变化。

**最终本地结构／维护性验收通过，开放 finding 0。** 未发现还需修改的所有权、依赖、复用、单用抽象、防护或测试问题。本轴未重跑 suite、安装、模型、浏览器或服务，未进行远端查询／写入；普通提交／推送、精确远端 Ref 及本片自己的必要 CI 尚待发布后原件。F9b3 的终态 CI 只属于其原候选，不关闭本片发布出口。Windows 原生 OS 实测、runner 登记／prepare、F9c／F9d、真实训练／GPU、质量／性能、证据批准及采用继续保持原边界。
