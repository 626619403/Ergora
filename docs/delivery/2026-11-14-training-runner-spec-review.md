# F9b4b 可信 runner 登记：独立需求与正确性评审

日期：2026-11-14。评审者：fresh-context 独立 agent `runner_spec_review`。首轮固定基线与当时 HEAD 均为 `fe26796a54b3804aac9272a9ea86643320a7f0b3`；首轮评审对象为其上的未提交 F9b4b 变更，随后补核最终本地与固定发布身份。先读取原始验收要求和实际实现，再读取交付叙述。遵循仓库 `AGENTS.md`、`maintainable-project-delivery` 及其独立评审 brief。本轮仅做只读检查并写本文；未运行产品、argv、测试、安装或服务，未提交／推送。

**当前结论（本地与发布身份）：需求／正确性通过，开放 finding 0；本轴所查维护边界无新增 finding。** 相同产品身份的最终 noneditable 包、必要安装回归、真实 CLI／页面、SDK-free baseline、原件与收尾、自身模板及公开证据已补核。普通发布 `80236fe8957c0704a3c73c7ea1440f7f288ff563` 的固定 Git 对象／23 个 blob／原完整远端 Ref 已核；本片自己的 CI 仍待，详见文末。首轮待验记录保留其当时范围。

## 首轮代码结论

- **需求／正确性代码评审：通过当前检查范围，开放 finding 0。** R1–R3 的实现路径与合同一致，未发现需要修改产品的实证缺陷。
- **维护性：当前需求轴检查未发现阻断项，开放 finding 0。** 原登记／不可变 writer、注册校验、子进程与表单生命周期的所有权保持；本结论不代替另一独立结构轴的报告。
- **完整验收与发布：待补证据。** 本轮不据源码测试摘要将最终安装、真实浏览器、自身审查、固定提交发布或自己的 CI 判为通过。R4 尚不能由本文关闭。

## 检查身份与范围

已检查 `git status --short`、分支、最近五次提交、`git diff HEAD`，以及静态清单列出的全部 17 个 tracked／untracked 文件。17 件当前长度与 SHA 均与 `.ergora/checks/training-runner/static-review-r1.json` 一致；其中 8 个产品／测试／CI 路径也全部与 `install-r1/source-manifest.json` 的 overlay SHA 一致。清单记录的产品包身份为 `43634fafdf354cb60f212face64c28caa27e7d5f0979c32362dacfcf64f8f583`。

|实际检查的产品文件|SHA-256|
|---|---|
|`scripts/ci/linux-groups.json`|`dd1e00a876eb1dcda6da41e8c49fa2aebe4ec1d5d997656b533b180f1bad6f63`|
|`src/ergora/cli.py`|`98d91f0fea67e7b81793c9c3f900768346e5fca1392afdfc3dabf2c1d0aba44c`|
|`src/ergora/data/console/training.js`|`48608648884a10e2036e595b8db53864459faa18935c9d164f0dcf0cd7774793`|
|`src/ergora/reference.py`|`c4034b8f619365a5044aa3f6d0b1c601de40145c7260e20789a224d230ce0ea4`|
|`src/ergora/reference_training_setup.py`|`d5925312331160d10dcbadaafe43b093c6d27e655c1bfe018d7542191ef191ff`|
|`src/ergora/training.py`|`c8f29467a4e8f9f3c04dd66a89d98ec688c218d85a8f9bed1e4e78c7bcdcff1c`|
|`src/ergora/web.py`|`be84d0092d26e2a007b2faa4255a7ece80b0cef215738eede31e909a5676b2c6`|
|`tests/test_training_runner.py`|`3e557af8d22e86917fb40a3457cb09ee3819dd53b2e60654c3147e598d8a39a1`|

其余检查文件是 README、当前计划、训练／Windows／架构手册、前片两个发布身份补核记录和本片计划／交付。原始合同见[实施计划](../plans/2026-11-14-training-runner.md)，当前实施状态见[交付](2026-11-14-training-runner.md)。

必要邻居包括 `reference_training_context.py`、`reference_training_submission.py`、原生 `agent_platform/training.py` 的 registrar／executor、`agent_platform/core.py` 的不可变 writer、`dev_platform/adapter.py` 的路径／原件 reader，以及控制台 `api.js / ui.js / app.js`、原 baseline 测试。`git diff HEAD -- src/ergora/data/reference` 为空；未发现本片修改冻结参考文件或业务试用项目的路径。

## 合同核对

|合同|代码证据与判断|
|---|---|
|仅当前已登记训练项目／同 Git 根|`training.py:114–118` 保留已发布 registration 与模板选择门槛；`reference_training_context.py:24–40` 核 canonical 执行目录、注册原件与 control home；`reference_training_setup.py:76–81` 核输入项目／repo 及与正式 start 一致的整数 schema。后续仍由原 registrar 校验字段、Git 根、argv 和 timeout。|
|完整规范化预览，不写真实 config／state|`reference_training_setup.py:82–95` 只在隔离子进程中把原 module 的 `CONFIG` 指向临时目录，调用原 `register_runner` 后读取其完整产物，并在 `finally` 恢复。真实 config 在该阶段只经 safe reader 检查；没有调用 executor、registry lock 或创建训练 state 的路径。|
|规范化 canonical SHA 与 revision 确认|`reference_training_setup.py:95–97` 对原生规范化对象计算 SHA，确认不匹配先拒绝；`training.py:122–131` 复用本地 DB 预留核当前 revision，预留期间无远端 RPC。发布输入再写为已验证的规范化 repo，避免重新依赖可变 alias。|
|不可变发布，同内容重试保留原字节|`reference_training_setup.py:109–120` 冲突拒绝后调用原 `native.register_runner`；原 `core.write:33–53` 以 link 竞争创建，同内容仅 canonical 对比，不替换原件。发布后重新读取目标并核内容 SHA。丢回复没有引入自动重发；页面要求重预览原件后显式重试。|
|同 ID 异内容／共享 config 外项目 ID|`reference_training_setup.py:98–111` 在返回 `current_runner` 之前核其项目与 repo；外项目占用只返回固定错误，未拼入命令。登记竞争仍由原不可变 writer 拒绝异内容；其冲突错误仅包含路径。|
|容量与路径边界|`cli.py:928–937` 在解析前限制原文件 1MiB；`reference_training_setup.py:16–20` 限制原生序列化字节；规范化与当前原件沿有界 safe reader，真实发布前已检查目标路径。新增测试覆盖大输入、注册漂移和 symlink 目标。|
|Linux／WSL2＋可选 SDK，无需服务|`reference.py:365–371` 仅 runner 两操作要求 Linux 并以 `sdk=True` 进入原子进程入口。SDK 检查只做可用性检查；登记函数未连接服务。baseline 仍走局部 `_baseline`，不导入原 training module；Windows baseline preview 的平台分支保留。真正无 SDK 环境和原生 Windows 的运行证据不能由源码路径替代。|
|CLI／HTTP／页面同一入口|`cli.py:467–475, 928–937` 与 `web.py:490–496` 都调用 `training.preview_runner / register_runner`。HTTP revision 严格整数及 SHA 格式由 payload owner 校验。页面调用同名 HTTP 路径，无另一登记协议或 runner 数据库。|
|编辑／切项目迟到结果与双击提交|`training.js:24, 32–43, 56–81` 以 view／project／tab／home 活跃性与局部 sequence 核响应；编辑先失效旧结果。确认动作在第一次 await 前设置 `sending` 并禁用控件，第二次点击不会再次发布。两表单实际共用 `setupDocument` 的生命周期；只读预览可重复请求，旧响应不会覆盖新内容。此处“双击一次”按确认发布解释。|
|原 baseline 与范围保持|baseline 主体从原入口机械收为 `_baseline`，其原发布锁、同内容跳过写入、Git／容量门槛均保留；未修改 prepare／job／fence／start／executor、evidence 批准或 GPU 工作包。|

## 测试材料与待验收项

已读新增七项 runner 测试和原 baseline 六项测试。用例调用真实 registrar／writer，覆盖规范化、同内容字节保持、SHA／revision／内容冲突、真实写完后的丢回复、并发同内容、共享 config 外项目 ID、原件漂移／容量／路径和 CLI／HTTP。它们保护合同中的静默错误，并未以 mock writer 代替不可变发布。

`source-r1-result.json` 给出源码调用命令；`source-r1-final.json` 报告 runner＋baseline＋架构 **27 passed／45.25 秒**，明确不代表安装包或 Windows 执行。保存的早期工具分块本身只是未完输出；本轮未独立重跑，也不把这些分块单独当完整通过证据。

交付尚需提供并按最终同一产品身份补核：

1. 最终 noneditable 包、两个 RECORD、冻结参考文件的逐件身份和受影响安装 suite 的完整终态。
2. 安装后的真实 CLI／原件／收尾；真实页面的编辑及切项目迟到、双击确认、长 argv／三视口、受影响 baseline 行为；真实 SDK-free baseline 检查。原生 Windows 未运行时继续明示未验。
3. Ergora 自身原模板的实际输入、后端、完整回复／结论与 finding 处置，以及另一 fresh-context 独立结构轴。
4. 固定提交／精确远端与本片自己的 CI；不能继承 F9b4a 或其他候选的通过状态。

上述为验收材料的开放项，不是已确认的代码缺陷。后续同片修复或最终证据到齐后可由本 reviewer 补核；如产品身份发生改变，本文当前源码结论只适用于上表 SHA。

## 最终本地原件补核

本次继续由同一 reviewer 只读检查实际原件，不运行 suite、安装、服务、浏览器、argv 或远端操作。HEAD 仍为上述固定 baseline；8 个产品路径逐件保持首轮长度／SHA，产品组合 SHA 仍为 `43634fafdf354cb60f212face64c28caa27e7d5f0979c32362dacfcf64f8f583`。补核时 `static-local-final-r1.json` 的 20 件源码／文档清单与工作树一致；较首轮新增的评审与公开证据属于本片验收记账。

**包与安装回归。** 直接打开 r1 wheel，重算其 SHA 为 `8d53c60ee378fecfdbbb994cbe174e6eda5657211bcede3fe46050ce59222860`。全部 570 个 `ergora/` 产品文件逐字等于当前源码、构建快照和非 editable 安装；wheel RECORD 的 578 行／577 个 hash、安装 RECORD 的 583 行／582 个 hash 全部按实际文件重算匹配。283 个冻结参考文件也逐项核当前源码／快照／wheel／安装与 manifest，无差异。完整安装 stdout 明确为 runner 7＋baseline 6＋原观察 13＋架构 14，共 **40 passed／65.54 秒**；stderr 为空，原 monitor 为 succeeded／退出 0、67.543 秒，600 秒界限未触。调用使用安装解释器 `-I -m pytest`，从构建快照运行；没有 pytest `pythonpath=src` 注入。分组原件为 **364／1817 collected、1453 deselected**，新增 runner 七项均在所属组；这是收集检查，不是 364 项执行或远端 CI 成功。

**真实 CLI 与 SDK-free baseline。** 已读 `native-r1.py`、各命令 argv／退出码与完整 stdout／stderr。真实安装 CLI 依次返回 `not_registered → registered → already_registered`；确认与重试的 canonical SHA 相等，原文件字节 SHA 均为 `2c2c1924d7c3edbb2d59b342671769000c6ecb59cb787fc63c78240b8a34a0cb`。错误 SHA 返回 2，脚本在该步核真实 runner 目录与 state 尚未创建。SDK-free 原件是实际 `-P -S` 进程：先核 sys.path 无 site-packages、Temporal 不可发现，经 spec 从已核安装包加载 Ergora，调用原 setup 完成首次 `initialized`，结束再次核 SDK 不可发现；不是把 find_spec mock 为 None 的替代证明。

**真实页面。** 已核 `runner / lifecycle / baseline` 三组 invocation 退出 0、原 stdout 的执行代码与保存脚本完整一致，结果均 passed；75 条真实服务请求日志与脚本、回执相互吻合。runner 与 baseline 的双击确认在服务端各只有 1 次 POST，错误 SHA 均未发送发布请求。延迟测试先 `route.fetch()` 取得真实服务回复再 hold；丢回执先取得真实登记成功回复再 abort。原件证明丢成功回执后重预览为 `already_registered`，显式重试保持文件字节 SHA；编辑输入迟到 preview、切项目后的 preview 与已实际发布的迟到回执均未污染新页面。外项目 ID 返回 400，没有展示原命令；异内容没有替换按钮。runner 长 argv／baseline 在 1440、960、390 的 document scrollWidth 均等于视口宽度，390 未发送表单也通过。这里核的是保存的实际浏览器行为与尺寸原件，本轮未另开浏览器或把截图存在当成交互通过。

首次 browser open 因默认 Chrome 缺失退出 1 的记录保留；随后使用已有 Chromium 配置真实 open／执行全部检查。console 仅有两个与脚本相符的预期错误：主动 abort 的真实登记回执，以及外项目 ID 的 HTTP 400；没有将首次 open 失败掩为成功。

**原件与收尾。** 逐件复算 `protected-before.json` 所列 32 份当前原件 SHA，无变化；现场四 runner 文件均等于相应规范化输入，两个 baseline 均等于原 baseline 输入。其他三个项目的 runner、外项目训练目录及 manifest／spec／job／fence／approval／integration-ticket 均未创建，执行 marker 不存在，验收 Git 仓库 status 为空。已读原 monitor 的 web 进程组取消终态、browser close 退出 0 和关闭回复，以及 `final-observations.py/json` 的原端口非监听检查；本轮未通过网络重新连接端口。上述仅证明本地登记／基线控制合同与其收尾。

**自身原模板。** 核实际 `ergora-structure-review` 输入、原后端 run、stdin、完整模型回复与结果。10 件完整文件 **214,529B** 在实际 stdin 中逐件重算匹配；其中 8 件产品等于当前源码，两件计划／交付为调用当时版本。准备 prompt 与实际 stdin 全字节相同，219,025B、SHA `0b2820733ef2325f080e924a7268e1eda91c6f527f91f83de5db8b98c7de3d97`；根 instruction、叶 instruction／Skill 这三件资源和叶 prompt 全部包含。原调用成功、53.359 秒、approve，实际结果与保存副本相同，SHA `b972a28c8ff913ff8d43e129da4eb98af8859a6749d383e80162a49f536b32d0`。实际 binding 为 Codex，原请求 Claude 的回退原因明确保留；不称异后端成功。模型回复明确表示未获得原 native owner，并保留当时运行证据待验；本 reviewer 首轮已实际读取 native owner，本次补核不扩大模型自己的审查范围。

**公开记录。** 补核的[公开证据](evidence/2026-11-14-training-runner.json)为 7,966B、SHA `7ad999676b6294e2a3690aa1d128288b21bdba47caf7193fa35cc6409593b260`；其 30 份私有原件引用长度／SHA 全部独立复算匹配。计划与交付的安装、实际交互、自身模板和平台／责任边界主张符合上述原件；后续独立评审状态更新不被当成产品重测。

**最终本地需求／正确性通过，开放 finding 0。** 未发现需要修改产品、补 guard／抽象或扩大测试的实证问题。普通精确提交／推送、完整远端 Ref 和本片自己的必要 CI 尚待固定发布原件。原生 Windows OS、prepare、真实训练／GPU、质量／性能、evidence 批准与采用继续按原合同开放；本次 CPU 控制合同不关闭这些责任。

## 固定 Git 发布身份补核

本次全部产品从不可变 Git 对象读取，未读取后续片产品工作树，也未运行 suite、服务或远端请求。候选为 **`80236fe8957c0704a3c73c7ea1440f7f288ff563`**，其唯一父提交为原 baseline **`fe26796a54b3804aac9272a9ea86643320a7f0b3`**。直接以 `git cat-file --batch` 读取该候选：父→候选恰为 23 个改动路径，与 `static-final-r1.json` 集合相同，23 件 blob 的长度／SHA 全匹配。8 件产品／测试／CI 按路径＋完整内容重算组合 SHA 仍为 **`43634fafdf354cb60f212face64c28caa27e7d5f0979c32362dacfcf64f8f583`**。

原 r1 wheel 的全部 **570 个产品文件**已逐字对照该固定提交的 Git blob，全部相等；wheel SHA 仍为 `8d53c60ee378fecfdbbb994cbe174e6eda5657211bcede3fe46050ce59222860`。因此发布产品与前述本地原件所验产品一致，未继承后续工作树的行为。候选内本轴报告恰为最终本地版 14,641B、SHA `555cae405c8b363f5caf8c9618eb1227a59f109bf8ee45ca7de7a158a6e6fafe`。对两个固定提交运行完整 `git diff --check` 退出 0；按候选 Git tree 核 245 个本地 Markdown 链接均存在，23 个改动 blob 未含原静态检查列举的私有机器字符串。

已读原提交／发布脚本及 `commit-r1.json / push-r1.json / ref-r1.json`。提交记录退出 0，绑定同一完整候选，保存了精确 23 个 staged 路径、完整 whitespace check、提交后逐件 Git blob 一致和当时工作树 clean 的检查。原 push 退出 0，目标为 `HEAD:refs/heads/refactor/architecture-foundations`，argv 无 force／mirror／main 合并；原回复记录 `fe26796..80236fe` 的前进。随后原 `ls-remote` 退出 0、stderr 为空，stdout 精确返回完整候选和完整 `refs/heads/refactor/architecture-foundations`，未仅用短 SHA 或本地 tracking ref 代替。

|发布原件|字节|SHA-256|
|---|---:|---|
|`static-final-r1.json`|4,938|`5b68aae6a5ae6db4e4d616d246b96e201f79cb35552215688e4be1c5aefac409`|
|`commit-r1.json`|949|`a248c55525fbb11b41d9cc98e350ecd5f4d272c9a84f0e7e075968d7e1754514`|
|`push-r1.json`|750|`90bf3f156226d46b28f3e3e8ce474b2cb9cacd98376486d6105a05d82b16d281`|
|`ref-r1.json`|738|`47c2cbe39f1d775f47d841bd6d4d3395400776c032634d5eeea34c55950f331f`|

候选内 runner 公开证据为 8,173B、SHA `c2df66a9b8a714779bcc2d4e372bb09d0025534420038d2588e97a3764d37e91`，30 份私有引用重新复算全部匹配；其 `publication` 当时仍标 not_committed，符合提交前记录，不被追认成提交内已知发布结果。该提交同时携带 F9b4a 的发布／CI 状态记账，其候选与 run 均明确属于原 baseline 片；这些文档更新未改本片产品，也不构成本片 runner 自己的 CI 通过证据。

**固定产品／普通发布／原完整 Ref 身份通过，开放 finding 0；本片自己的 CI 仍待发现与终态补核。** 本地回归、分组收集、F9b4a CI 及只有 runner run ID 都不能关闭该待验项。此次仅补本报告，不提交／推送，不以当前或后续工作树代替固定发布对象。
