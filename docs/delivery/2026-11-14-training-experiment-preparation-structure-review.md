# F9b4c C1：独立结构与维护性评审

日期：2026-11-14。评审者：fresh-context 独立 agent `preparation_structure_review`。未继承实现对话；先读原始验收、仓库 `AGENTS.md`、maintainable-project-delivery 及其 independent-review brief、codebase-design，再查实际实现和原 owner，最后对照作者记录与原件。本次仅只读检查产品／测试／私有证据，并写本文；未运行 suite、安装、服务、模型、训练、GPU 或远端操作，未修改产品、业务试用仓库、提交或推送。

**最终本地结构／维护性通过，开放 finding 0。所查 C1 需求符合性在最小修复后通过；最终 r2 包、受影响安装检查、实际 CLI／HTTP、SDK-free、原件／收尾和自身模板原件已补核。** 普通精确提交／推送、完整远端 Ref 及本片自己的 CI 尚待；这些不由前片 runner 的 CI 关闭。

## 身份与实际检查范围

固定基线与评审期间 HEAD 均为 `80236fe8957c0704a3c73c7ea1440f7f288ff563`，分支 `refactor/architecture-foundations`；对象为其上的未提交树。首先核 `git diff --name-only HEAD` 加 `git ls-files --others --exclude-standard`，首轮为 16 件 tracked／5 件 new，共 21 件。补核期间增加本片公开证据、原 runner 的 plan／delivery／公开证据状态补记及本片需求报告；写本文前完整范围为 19 件 tracked／7 件 new，共 26 件。未将 new 文件排除在产品审查之外。

实际检查的本片产品／测试／CI 为以下 11 件。末列是修后当前文件 SHA-256；以路径排序后逐件拼接 `path + NUL + bytes + NUL` 的组合 SHA 为 `4414d4f7f8fba705e18373c53a827f6eca0691d2a04fd5a48a452208dfa0e983`。

|路径|字节|SHA-256|
|---|---:|---|
|`scripts/ci/linux-groups.json`|3,461|`b3a2ac6610b225c419824f70cab5b81340eb6c7c58bf0c428906f9c6fe18c5a5`|
|`src/ergora/cli.py`|74,389|`728d737b290276e6ffb28607c5e925444829e227c1a1280ec451fb2f2d470b6c`|
|`src/ergora/reference.py`|45,042|`85ac4a38b5302e9595379ec4940736e7043aba70265720bd5d83cda748b70609`|
|`src/ergora/reference_training_context.py`|2,231|`852f5422067be11fabd22e754942b4986877f1dc3a63e400e9781966833b5b04`|
|`src/ergora/reference_training_preparation.py`|12,809|`89b9d129ab2d62d108281041d0a2c92a6a9cf638f622a933488a25d974ae878f`|
|`src/ergora/reference_training_setup.py`|7,763|`0380aeaea8f5f1606a7ded772d0646aa9d89bf4d33fc73549a5527c6d8d52ff1`|
|`src/ergora/training.py`|12,844|`5ab0caeb0bbc59d9576f3ca47911bd43197b9ae8c770f1286b67729b6c7f050e`|
|`src/ergora/web.py`|43,427|`619132feffcf14ecfeec386397a6b109d90b26ca95fa30226a61bb802e7e85ed`|
|`tests/fixtures/training_preparation_process.py`|815|`f8dfa44dbd4bd12cfbf3c5c5d71143e629092412c2b79f1c488081ee1517b5f9`|
|`tests/test_architecture_boundaries.py`|3,634|`3f9f624bdeccbf06c703a033f37ddb76c9e7d4ca7690fa86c0fd55fc779d938c`|
|`tests/test_training_preparation.py`|14,600|`bd7d1d9c106806c43f640f0a764a1a4fcfbfd018031a2ec8dcd3038233759935`|

另读本片 README、`docs/PLAN.md`、TRAINING／WINDOWS 手册、两个 architecture 文档、[原准备总计划](../plans/2026-11-14-training-preparation.md)、[本片计划](../plans/2026-11-14-training-experiment-preparation.md)、[交付](2026-11-14-training-experiment-preparation.md)及[公开证据](evidence/2026-11-14-training-experiment-preparation.json)。原 runner 的两份 review、plan、delivery 和公开证据均查其 diff，属于原固定候选的发布／CI 状态补记；不将其旧通过当作本片验收，也未另取远端 CI。需求轴报告仅用于记录同片 finding 的修复和复核，不递归审查评审记录。

沿调用链实际读取原 `agent_platform.training.register_runner/prepare`、`core.write/git/slug`、`perfctl.validate/baseline_ok`、`Binding/Experiment.validate`、`dev_platform.adapter.safe_file/read_raw`、canonical SHA、既有 `_training_records`／submission preflight、`state.file_lock`、reference 子进程装载及 `processes.run` 的退出／进程组收尾路径。以下结构判断基于这些实现，而非测试通过或作者的交付措辞。

## 模块深度、所有权与复用

`reference_training_preparation` 的接口承载完整暂存计划、不可变意图、逐件状态和显式恢复；复杂度留在同一私有模块，CLI／HTTP 只传完整输入与确认身份。`_Preparation` 及其 `path/load/sources/plan/status/ensure_unstarted/publish/run` 是这一状态机的内聚私有算法；唯一生产入口是 reference 专用子进程中的 `main`。单入口在这里有具体理由：原模块的 CONFIG／TRAINING 是进程全局，暂存必须与 Web／CLI 及其他项目隔离。没有为调用者数量另造 wrapper、后端接口或假想扩展点。删除该模块会将恢复状态机重新散入 setup／入口层，不能消除这些职责。

新 `_native_bytes` 从 setup 移到既有 context，被 setup 与 preparation 两个生产文件实际调用。默认 1 MiB 编码与原格式相同，只有准备意图显式使用 16 MiB；限制保护原 reader 能完整读回，而不是调整配置以满足测试。`_TrainingProject` 继续集中注册、home、规范目录及有界读取，未把 setup／prepare 依赖到 start、Task 或外部调度语义。

`training._setup` 仍在应用层持有短本地 revision 预留；新 callable 参数只复用实际 setup 与 preparation publisher，不按具体类型分派，不新增注册框架。四个新增应用函数都有 CLI 与 HTTP 两个生产入口。reference 继续只负责已注册安装、环境、可选 SDK 和进程生命周期；子进程在 `finally` 恢复 native CONFIG／TRAINING，status 不导入 native training 或 Temporal SDK。

manifest 字段、commit 别名、项目／runner／窗口补齐、baseline／比较器检查、Binding 和实际三件发布都直接来自原 `prepare`。暂存输出唯一映射为 spec 的 `manifest_uri`，manifest 字节未改；最终读回复用原 `_training_records`。意图由原 `core.write` 不可变保存，原 native registry lock 仍由原 owner 使用，本地非阻塞 file lock 仅协调同 ID 准备意图。未复制 native 发布、Binding 或字段算法，未新增实验数据库、服务、训练执行器或第二实验状态权威。

## 必要控制流与测试价值

已逐组检查新增 guard／branch／handler 的可达失败与责任位置：

|位置／不变量|可达失败与保护行为|
|---|---|
|context 路径／注册；preparation `load`|注册投影漂移、不同 home／project／execution／intent、损坏的持久结构或目标集合；拒绝把另一原操作解释成本操作。|
|`sources` 与 `plan`|共享 runner 属于外项目／Git 根，source 非对象或超量，布尔 runner schema 不能用于正式 start；原 `value or default` 会将明确 0／False 当省略。其余 draft、Git、baseline、比较器与窗口关系仍沿原 owner。|
|`status`|无意图的原生目标占用、缺件、部分发布、精确匹配或字节冲突；只报告事实，不补文件，也不披露外项目材料。|
|`publish`|已有 job／fence／start、部分文件冲突、source 在暂存／锁之间漂移、原发布与冻结计划不符；拒绝继续或保留可对账的原件。三件不是原子事务，没有以请求失败推断零写入。|
|`run` 的确认与锁内重读|错误 SHA、旧 revision、不同 request、并发保存意图、无意图原文件、锁前后 intent 变化；新意图先保存，再进入原三件发布。resume 重建同一原计划，不能更换 ID／source 或覆盖冲突。|
|容量、safe_file、异常与 finally|超过原 reader／聚合意图容量，目标或 lock 的 symlink／逃逸，原校验／Git／文件失败和子进程中断；明确失败、完整保留 checkpoint，并恢复临时 native 全局。|

source 在暂存后、锁内及进入原 publisher 前的复核针对不同时间窗口；锁内 intent 再读针对跨进程竞争。未见需要删除的重复 validator、无关参数检查或为复用额度添加的 guard。占用检测明确限于本项目 manifest、共享 global manifest／spec 和同 ID 意图；不为人为删除全局登记后仅存于其他项目的 manifest 建立新全项目索引。

新测试通过应用接口检验合同。fixture 在原 `core.write` 成功后对真实子进程执行 `os._exit(73)`，四个边界包含 intent／global／project／spec，之后由新进程读取并显式恢复。它没有复制发布算法或在产品加入测试分支。来源漂移、外项目占用、symlink、丢成功回复、错误确认及字节保持保护的是可能静默接受或损坏的情况；修后三类 checkpoint 参数化回归保护早返路径。未发现需要增加额外 tests／CI／assertions 的实证理由。CI 仅把新 suite 接入既有 Linux group 5，未增加新的 job 或第二套检查流程；原 architecture 测试仅加入这个实际 native 适配模块。

## 同片需求 finding 的修复复核

需求轴首轮 P2 位于原 `publish` 的完整状态早返：成功 prepare 后出现 job／fence／start，再显式 resume，会先返回 prepared 而未执行约定的拒绝检查。后果是静默接受已进入执行阶段的恢复请求；不会因此启动训练，但违背了明确拒绝条款。

最小修正已落实于 [reference_training_preparation.py](../../src/ergora/reference_training_preparation.py#L135)：将原 `ensure_unstarted()` 移至完整早返之前，未新增检查或流程。`run` 中相同 prepare 与独立 status 仍只读返回。已读 [参数化回归](../../tests/test_training_preparation.py#L90)，并从最终 r2 的原 stdout 核到三个 later checkpoint 用例及原四中断边界全部通过。修后 owner／test 的身份见上表。**本项同片复核关闭；本结构轴无新增或开放 finding。**

## 实际证据补核与限度

私有证据位于 `.ergora/checks/training-preparation/`。本轴读取脚本、argv、原 stdout／stderr 和真实文件，并自行复算相关长度／SHA；没有只接受结果 JSON 的布尔值。

- 保留源码首轮 38 passed／1 failed／95.88 秒，失败是外项目 runner 检查晚于缺失 baseline 的错误顺序；修正后源码 39 passed／64.93 秒。r1 noneditable 包及六 suite 的 65 passed／212.14 秒、monitor 214.042 秒只代表修前版本，未追认为修后全库运行。
- 最终 r2 wheel 为 `cc96e63433d647a0e9db33f2de52ff056090d274ae211863c36e591606df0935`。亲自读取 wheel、安装与构建快照：571 件产品与当前源码逐字相同；wheel 579 行、安装 584 行两份 RECORD 的每条 hash／size 均匹配；当前与安装各 283 份冻结参考文件均匹配 manifest；4 件测试／fixture／CI 文件与最终快照相同。
- r2 私有 setup 首次误用不存在的旧依赖缓存 r2 interpreter，原 `setup.json`／`venv.stderr` 保留失败。已读 `setup-recovery.json`：沿既有固定 r1 interpreter／依赖缓存安装已构建的同一 r2 wheel，两步退出 0；上述全文件／RECORD 身份核对覆盖恢复后的实际安装，没有将失败改写为成功或改变产品／依赖合同。
- 读最终 `install-r2/regression-r2/process/stdout.txt`、空 stderr 和 monitor 结果：**preparation 15 passed／69.67 秒，monitor succeeded／0／71.393 秒**，包含三个修正回归与四个真实中断点；没有另跑或声称最终全库测试。最终 group 5 收集原件为 379／1832、1453 deselected，仅证明收集与归属。
- 读 r2 实际安装 CLI 11 条 argv 与结果，包括错误 SHA 零发布、原 prepare、相同 prepare、status、显式 resume 和原 reader。读实际 `-P -S` 脚本与输出，其断言无 site-packages、找不到 Temporal SDK，仍成功读 preparation；不以移除应用 SDK 检查的 mock 代替这份证据。
- 读 r2 真实 loopback HTTP client／service、8 个步骤和 8 条服务端原记录，并逐件复算保存 body 的长度／SHA。原 prepare 200 在 GET 前被服务端记录，客户端发送后关闭 socket 且不消费回复；随后 GET、显式 resume 和相同 prepare 读回同一 intent。这里的真实网络证据与测试中的 TestClient 区分记录。
- 亲自复算 r2 protected-before 的 8 件配置／baseline 原件保持；CLI／HTTP 两实验各三文件与意图逐字相同，spec URI 指向真实 manifest，Binding SHA 等于该 manifest 原字节 SHA。两个 canonical intent SHA 为 `32949ddf1838b161be5a17ca506f18e49937f5bb3b1ffc08e10d5acdce1e0c03`、`7f254915d0f76854eea97bdc28d94fa3696a878c3f72906e5ad5869578417c1f`。实际目录未见 job／fence／submission／approval／integration-ticket 或 runner 命令 marker；已读原 Git clean／进程组 cleanup／端口关闭的收尾脚本与记录，未再启动服务或重跑旅程。
- 读 r2 自身原结构模板输入清单、实际 prompt／原回复和身份：15 件完整文件、265,212B、33.487 秒 approve，结果 SHA `b7c4144e5e198f7d878a86088cf611407d408a3ebabdab08bd3b1b9e6f8bc0c4`。产品／测试／CI 与当前树身份匹配，完整快照内容存在于原 prompt；含原 native owner 与祖先／叶资源。不将内联存在称为阅读理解，不称异后端成功，也不把自身模板代替本轴独立评审。

补核时公开证据为 13,177B、SHA `58c2ba99b853b879319fd219a68671e146569e16de8ab312e13d4ab0fce1686a`，所引 26 件 r1 与 26 件 r2 私有原件共 52 件，长度／SHA 全部独立复算匹配。计划、交付与手册已区分 r1 旧版本和 r2 修后合同，以及显式 resume 拒绝与相同 prepare／status 只读的区别。公开评审状态随后更新属于记录补记，不构成产品重测。

本轴执行的检查只有只读文件／JSON／AST／RECORD／SHA 核对与 `git diff --check HEAD`，后者退出 0；没有另跑 suite 或产品操作。**最终本地结构与所查需求通过，开放 0。** 尚待普通精确发布、完整远端 Ref 与本片自己的必要 CI 原件；C2 页面、原生 Windows OS、Temporal 服务、真实训练／GPU、质量／性能、原 evidence 批准与采用仍不在本次验收范围，继续归原 F9c／F9d／B3 责任。
