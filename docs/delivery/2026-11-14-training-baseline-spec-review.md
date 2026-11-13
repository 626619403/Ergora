# F9b4a 独立需求／正确性评审

日期：2026-11-14。评审员：fresh-context 独立需求轴；先读原始要求、原 owner 和候选源码，随后读取作者交付与验收原件。本次只读源码／证据并写本报告，未改产品、安装、启动服务、运行训练或提交。

当前结论（本地与发布身份）：**需求／正确性通过，首轮 2 个 P2 已关闭，开放 finding 0。** 本轴所查维护边界也无额外 finding；完整独立结构轴另见其报告。r2 包／必要安装回归、实际 SDK-free、完整真实页面与原件／收尾、原模板自身聚焦调用均已补核。普通发布 `fe26796a54b3804aac9272a9ea86643320a7f0b3` 的固定 Git 对象／27 个 blob／保存的完整远端 Ref 已核；本片自己的 CI 仍待终态，不借 F9b3 CI 关闭本片。以下首轮问题、失败和较早待验状态均保留其当时范围，以文末补核为准。

## 首轮结论与身份

**需求／正确性：request-changes，2 个 P2。维护边界：除 CLI 输入限读缺口外，无额外 finding；完整独立结构轴另有报告。** 结论限于下述候选，未关闭仍在途的浏览器、发布和本片 CI 验收。

- 原始要求：[项目规则](../../AGENTS.md)、[总进度](../PLAN.md)、[本片计划](../plans/2026-11-14-training-preparation.md)及其引用的 F9 工作台合同。
- 固定 baseline／当时 HEAD：`fad53478c9261157b3016563b410b9d4b4d85b9d`；候选未提交。tracked diff 为 `.ergora/checks/training-baseline/review-r1.diff`。
- 完整候选 19 件的长度／SHA 由同目录 `static-r2.json` 的 `files` 固定；本评审逐件只读复算，全部一致。11 件产品／测试／CI组合 SHA 为 `a31f8d95e7943ea4b841cd759868a958cc99b36bba49df06ccd0e8c00e1096cc`。
- 产品／测试／CI：`src/ergora/cli.py`、`data/console/training.js`、`reference.py`、`reference_training_context.py`、`reference_training_setup.py`、`reference_training_submission.py`、`training.py`、`web.py`（以上均属 `src/ergora/`）、`tests/test_training_baseline.py`、`tests/test_architecture_boundaries.py`、`scripts/ci/linux-groups.json`。
- 文档：`README.md`、`docs/PLAN.md`、`docs/TRAINING.md`、`docs/WINDOWS.md`、本片计划／交付，以及旧 F9b3 的两份评审报告。后两份只认作发布后记账，不用于证明本片产品。5 件 untracked 新文件均已读全文。

## Findings

### P2-S1：原生 Windows 的预览仍进入 Linux 专用 Git 调用

位置：[reference_training_setup.py:45](../../src/ergora/reference_training_setup.py#L45)、同文件第 47 行；被调用的冻结原 `platform/local/agent_platform/core.py:90`。

原合同第 23 行要求：“Windows原生预览沿现有no-follow reader；未实际测试的OS明确保留。” `docs/WINDOWS.md:120` 也公开提供 `baseline-preview`。但预览和初始化无条件调用 `context.core.git`，后者将可执行文件写死为 `/usr/bin/git`。普通 Git for Windows 的 Git 位于安装目录并经 PATH 提供；当前项目登记使用 PATH 的 `git`，因此能登记的正常 Windows 项目仍会在预览时先报 `FileNotFoundError`，拿不到完整 JSON 或内容 SHA。现有首个基线测试在进入 Linux 专用初始化分支之前就先调用预览，也会走到该路径。

可复现条件：在普通 Git for Windows／原生 Python 环境登记训练项目，准备有效 baseline 后执行 `ergora training baseline-preview PROJECT --baseline baseline.json`；预期返回预览，实际在 `/usr/bin/git` 启动处失败。本评审通过源码确认调用链，**未执行本地 Windows 验收**。

最小修复：仅在 setup 桥边界采用现有可移植的只读 Git 原语，例如 `harness.git_scope._run_git`（PATH Git、`os.devnull`、清理继承的 Git 环境），完成相同 Git 根／commit 检查；不调用其额外 task scope preflight、不修改冻结文件或扩展 Windows 初始化。Linux 原 `perfctl init` 的发布责任保持。

### P2-S2：CLI 在解析前没有执行约定的 1MiB 输入限读

位置：[cli.py:927](../../src/ergora/cli.py#L927)、同文件第 930 行；setup 中第 30–32 行只检查重新序列化后的内容。

原合同第 19 行要求：“输入与最终文件受原1MiB读界限约束，不截断。” 两个 CLI 操作均先 `read_text()` 读取整个输入，再 `json.loads()`；setup 只约束生成的 pretty JSON。给有效对象前置超过 1MiB 的空白即可绕过输入文件上限，文件会被完整读入并解析；生成的 baseline 足够小时仍接受。读入发生在有界 reference 子进程之外，原 process monitor 也不能覆盖这一阶段。这是实际外部输入边界缺失，不需要新增泛化校验层。

最小修复：在 CLI 两操作共用的现有分支中以二进制最多读取 `1_048_576 + 1` 字节，超限拒绝，随后解析完整已读 JSON；保留 setup 对最终原文件大小的检查。HTTP 已有 4MB 请求封套上限，应明确封套与 baseline 序列化后 1MiB 的不同角色，不将封套上限误称为原 baseline 文件上限。该 finding 与独立结构轴所见相同。

## 已核责任与行为

- CLI／HTTP 共用 `training.py`；初始化在项目 DB 写锁内核对 published 训练项目与 revision。setup 校验注册原件、control home、规范 config／state 路径、真实 Git 根和存在的完整 SHA；完整对象的 canonical SHA 与原文件字节 SHA 分列。
- `perfctl` 的 ident／commit／sha 检查由原 reader 机械提为共用函数；`_TrainingProject` 的初始化、document、registration 从原 submission 机械共享，除错误标签外未引入 task／start 语义。setup 与 submission 为两个真实消费者，取消仍从原 submission 取身份。
- 首次发布仍直接进入冻结 `perfctl.main(init)`，保留其锁、重复检查和原子写；已有相同内容不重写原字节，不同内容拒绝。未增实验账本、runner／prepare／start、批准或调度。
- 页面以 view/project/home／sequence 约束迟到响应；输入变化撤销旧预览；初始化发送前置 `sending`，错误 SHA 在发送前拒绝，成功重读原基线。源码支持这些路径，实际浏览器完整验收在首轮报告时仍未补核。

## 实际证据与限制

本评审只读复核了候选身份、原调用链和下列原件，未自行重跑测试或冒称完成全仓库／真实 GPU 验收。

- `source-r1.log`：19 passed／1 failed／7.23 秒；失败为测试只匹配 symlink 文案，原拒绝为 `Path escapes trusted root`。`source-r2.log`：修正该测试后，该项与原 training／submission／cancellation 共 38 passed／198.46 秒；两个范围分别保留。
- r1 非 editable wheel SHA：`186118240d553bd463d430e4dbd423ae13ef4bc0929992d648daea2ff04d0eed`。本评审独立只读比较 wheel／构建快照／安装目录的 570 产品文件，核对两 RECORD（578／583 行）及 283 冻结文件，均一致。
- 安装五 suite 的实际 `regression-r1/result.json` 与 stdout 已完成：57 passed／232.41 秒，监督进程 234.249 秒成功。只承认原 argv 中列出的五 suite，不扩大为单次全仓库通过。
- 原安装 CLI stdout 为 `not_initialized → initialized → already_initialized`；纠正环境后的真正无 site-packages／无 temporalio 的 `-P -S` probe 为 `initialized`。首 SDK probe 的环境断言失败原 stderr 保留，不记为产品通过。作者保存的 27 件受保护原配置／基线，本评审按 `protected-before.json` 复算，当前无变化。
- 自身原结构模板原件为 14 完整文件／245,707B，approve／49.805 秒；输入文件 SHA 与本候选产品一致，计划／交付是当时的较早记账版本。采用用户授权 Codex 回退，不冒称异后端成功，也不以该结果替代本评审。

待完成：修复并补核上述 2 个 finding；修后精确候选的新包身份、必要安装回归和适用 SDK-free 实证；浏览器完整迟到／跨项目／丢回复恢复／双击／三视口原件；更新计划与交付；本片精确提交／远端 Ref／自己的 CI。原生 Windows 未本地运行、真实训练／GPU／测量质量收益、runner 登记与 prepare、原 evidence 批准／采用继续明确开放。

## r2 源码修复补核

HEAD 仍为上述固定 baseline，候选未提交。按同一 11 产品路径只读重算，当前组合 SHA 为 `426d271430bdba818bd999be46c2ae5b06bdc6ec85c2b138e0318fe0712001ef`。相对首轮只有以下 3 件产品变化，其余产品逐字不变；本评审重新核过源码中的 283 冻结文件，仍全部匹配 manifest。

|文件|字节|SHA256|
|---|---:|---|
|`src/ergora/cli.py`|71,684|`bdca4eca5bd037f77ae8743efbe06af3261623c6d967ac23824ded5a8d0b1589`|
|`src/ergora/reference_training_setup.py`|4,488|`17711e73d50a6b152f368d5cd144ea9920abedae577d3cc90850afbe871dfea7`|
|`tests/test_training_baseline.py`|10,154|`df19d3a1dbd2299c4c878857d39c646233ade9752847ff439b5ed196706c9d67`|

- **S1 源码修复有效**：setup 第 18／46／48 行直接复用冻结 `harness.git_scope._run_git`，以 PATH 的 Git 和 `os.devnull` 执行原两项只读检查；该原语清理 Git 环境且不调用额外 task scope preflight。共享 context、reader 和原 `perfctl.main(init)` 不变。原生 Windows 实际运行仍未执行，不将移除已知路径障碍冒称为 Windows 实测。
- **S2 源码修复有效**：CLI 第 926–935 行将两操作收在同一分支，二进制读取最多 `1_048_577` 字节，超限在解析和调用应用前拒绝。小对象的大量前置空白不能绕过原始文件上限；setup 仍检查原生序列化后的大小。原容量测试追加同一真实输入场景，且两个 CLI 操作共用该路径，不需要复制测试。计划已分别写明 CLI 文件／原生文件 1MiB 与既有 HTTP 4MB 封套。

本次只核源码和已有原件，未执行或借用 r1 结果证明修后代码。r2 构建／安装、必要回归和页面尚待交付。作者另报告 r1 页面第二组因脚本对同一项目重复选择触发视图重建，操作落到旧 view 而超时；该轮失败保留，尚未核其完整原件，也不算产品通过。待修正脚本同步后在 r2 新独立项目补验。

## 最终本地原件补核

固定 baseline／HEAD 仍为 `fad53478c9261157b3016563b410b9d4b4d85b9d`，产品组合 SHA 仍为 `426d271430bdba818bd999be46c2ae5b06bdc6ec85c2b138e0318fe0712001ef`。补核开始时，`static-r3.json` 的 22 件完整文件长度／SHA 均与实际文件相符；其新增的本片评审／公开证据属于文档与状态记录。以下检查由本评审只读复算或直接核读实际原件完成，未重跑 suite、服务、模型或外部请求。

- **包身份与回归范围**：r2 wheel SHA 为 `e39866028ee7e4625f814e3fb23064ee7ea274d85cb2cd509c4f06d24af5ffeb`。独立逐字比较 570 产品与当前源码／r2 构建快照／实际安装目录，重算两 RECORD（578／583 行）及 283 冻结文件，均通过。再逐件对比 r1/r2 包和测试快照，产品确实只变化 `cli.py`／`reference_training_setup.py`，测试只变化 `test_training_baseline.py`。r2 实际安装的 baseline＋architecture 为 **20 passed／11.39 秒**，monitor **12.975 秒**成功；与原 r1 五 suite 57 passed 分列，未声称最终 r2 全新重跑 57 项。
- **S1／S2 关闭**：r2 安装用例已覆盖修后 Git 根／不存在 commit 拒绝、带超量前置空白的原始 CLI 输入拒绝，以及 CLI／HTTP 原发布与同内容重试；源码修复与所测 r2 包逐字相同。S1 不再经过 Linux 写死路径，S2 在解析前真正限读。原生 Windows OS 仍未实际运行，这一明确保留不扩大为本地支持实测。
- **实际 SDK-free**：核读 `sdk-free-final.json`、完整 stdout 和空 stderr；保存的 argv 为最终安装解释器的 `-P -S`，执行前后断言均无 site-packages／无 temporalio，退出 0，收到同一原 baseline 的 `already_initialized` 回执，原文件字节 SHA 保持。初次 r1 真正新建的 `initialized` probe 与其首轮环境断言失败分别保留，不混称最终包新建了另一基线。
- **真实浏览器行为**：r2 `baseline.stdout`／`lifecycle.stdout` 的 `### Result` 均为 passed。已将 stdout 中实际执行的完整代码与保存的两个脚本逐字比对：它们用 `route.fetch()` 取得真实服务器响应，再延迟或 abort；没有伪造预览／发布回执。三份实际 `initialized` 回执（普通初始化、丢回复后的原发布、跨项目迟到发布）还与 `requests.jsonl` 中对应真实 POST／200 的响应 SHA 各自匹配。错误 SHA 零 POST、编辑后的旧预览丢弃、双击恰好一次 init、不同内容不出现覆盖按钮、丢回复后重读并按同内容重试、跨项目迟到 preview／init 回执不污染新项目均有实际脚本与服务器记录。1440／960／390 三视口、390 未发送表单的 scrollWidth 均等于视口；未声称原生 Windows 浏览器运行。
- **保留失败与重验身份**：r1 lifecycle 原 stdout 确为 `locator.fill` 30 秒 timeout，未返回整组完成结果。直接比较两轮脚本，r2 只增加选择相同项目时避免重复触发重建、切换后等待对应 training 响应的同步，并换成新的独立验收项目；该次修正没有修改产品。r2 页面保留了刻意丢真实回复引发的预期网络错误，不声称零浏览器错误。
- **原件与收尾**：本评审再次按原 `protected-before.json` 重算 27 件既有原件，全部保持；8 个项目的原 baseline 完整内容一致，另一项目没有 baseline。原 manifest／spec／job／fence／approval／integration-ticket 路径未创建，验收 Git 仓库 status 为空。两份 browser close 回执退出 0、两份 web monitor cleanup 为 cancelled，与 process monitor 收尾路径一致；本评审只读检查两个原端口，仍均未监听。
- **自身模板与公开证据**：第二轮原结构模板为 5 完整文件／95,335B、approve／23.170 秒，原结果 SHA `f7a1fce083795dcfbf1aba2731c339a51136588e6a0c43845b4251134610a69e`。本评审独立核实际 prompt 与 stdin 相同、5 件完整材料长度／SHA及当前产品一致，祖先／叶的 3 件资源和叶 prompt 均在实际 stdin；不以脚本布尔值代替材料复核。公开 JSON 引用的 24 份私有原件长度／SHA 全部复算匹配，公开计划／交付区分了各包、失败、分段范围和未验平台。

**本地结论**：原始 F9b4a 的基线预览、精确 revision／canonical SHA 确认、原子且不覆盖的原 init、SDK-free、页面生命周期与原件保持已在上述范围通过；没有新增产品或责任边界 finding。后续只待本片普通精确发布、完整远端 Ref 及自己的必要 CI 补核。真实训练／GPU／质量或性能收益、runner 登记／prepare、原 evidence 批准／采用、原生 Windows OS 实测继续按原合同开放，不由本次本地评审关闭。

## 普通发布身份补核

本次全部产品身份从固定 Git 对象读取。候选 `fe26796a54b3804aac9272a9ea86643320a7f0b3` 的唯一父提交为原 baseline `fad53478c9261157b3016563b410b9d4b4d85b9d`。本评审以 `git cat-file blob COMMIT:PATH` 逐件重算 `static-final-r1.json` 的 27 件长度／SHA，并与该提交实际 changed-file 集合核对，全部一致。11 件产品／测试／CI 的组合 SHA 仍为 `426d271430bdba818bd999be46c2ae5b06bdc6ec85c2b138e0318fe0712001ef`，与前述最终本地验收候选相同。新增或更新的旧 F9b3 发布／CI记账仍只归其原片，不作为本片产品证据。

保存的 `commit-r1.json`、`push-r1.json`、`ref-r1.json` 均退出 0 且指向同一完整候选。原 push argv 是当前开发分支的普通 `HEAD:refs/heads/refactor/architecture-foundations` 推送，无 force／mirror／main 合并；原 stdout／stderr 记录 `fad5347..fe26796` 的前进。其后保存的 `ls-remote` stdout 精确为 `fe26796a54b3804aac9272a9ea86643320a7f0b3` 与完整 `refs/heads/refactor/architecture-foundations`，本评审未另发远端请求。

|发布原件|字节|SHA256|
|---|---:|---|
|`commit-r1.json`|1,084|`9df67f61c58f9ef98d87787ade898e917edd15d93150d7dd4afc03fe52dbf847`|
|`push-r1.json`|749|`a253af6172dee6445cb23871b68fbc656e84ea92e42d9cba7658dad11b2a873f`|
|`ref-r1.json`|738|`b8d1dc0ac46c0d8ef7e572d115f1bf83ee400589e81cfdb26bccccc960f1b786`|

**发布身份通过，开放产品 finding 0；本片自己的 CI 仍待发现和终态补核。** 此次仅补记原片发布身份，未将后续 F9b4b 工作树纳入候选，也未重跑 suite／服务或继承 F9b3 的 CI 成功。
