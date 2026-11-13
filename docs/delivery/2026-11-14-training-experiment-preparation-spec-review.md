# F9b4c C1：独立需求与正确性评审

日期：2026-11-14。评审者：fresh-context 独立 agent `preparation_spec_review`。未继承实现对话；先读原始验收要求、仓库 `AGENTS.md`、maintainable-project-delivery 及其 independent-review brief，再读实际代码、原 owner 和相邻调用者，最后对照作者交付与私有原件。仅只读检查产品／测试／证据并写本文；未运行 suite、安装、服务、训练、GPU、模型或远端请求，未改产品、提交或推送。

**当前结论（最终本地与固定发布身份）：需求／正确性通过，首轮一项 P2 已修复并经最终 r2 原件补核关闭，开放 finding 0；所查维护性无独立阻断 finding。** 普通发布 `92e7c24dbeb6847fe20c00e69c89c04b17702d5e` 的固定 Git 对象／27 件 blob／完整远端 Ref 已核；本片自己的 CI 仍待发现与终态补核。不把 r1 的成功追认成修后 r2 运行成功，也不把 C1 文件准备合同当作真实训练验收。

## 固定身份与查阅范围

固定基线与首轮 HEAD 均为 `80236fe8957c0704a3c73c7ea1440f7f288ff563`，分支 `refactor/architecture-foundations`，对象为其上的未提交工作树。首轮先运行 `git diff --name-only HEAD` 和 `git ls-files --others --exclude-standard`，完整核得 16 个 tracked 修改、5 个 new 文件，共 21 件：

- 产品：`src/ergora/reference_training_preparation.py`（new）、`reference_training_context.py`、`reference_training_setup.py`、`training.py`、`reference.py`、`cli.py`、`web.py`。
- 测试／CI：`tests/test_training_preparation.py`（new）、`tests/fixtures/training_preparation_process.py`（new）、`tests/test_architecture_boundaries.py`、`scripts/ci/linux-groups.json`。
- 本片记录：`README.md`、`docs/PLAN.md`、`docs/TRAINING.md`、`docs/WINDOWS.md`、`docs/architecture/contracts-and-identities.md`、`docs/architecture/current.md`、`docs/plans/2026-11-14-training-experiment-preparation.md`（new）、`docs/delivery/2026-11-14-training-experiment-preparation.md`（new）。
- 前片发布补记：`docs/delivery/2026-11-14-training-runner-spec-review.md` 与 `docs/delivery/2026-11-14-training-runner-structure-review.md`。已读其 diff，属 runner 固定发布／CI 补记，不归作本片产品，也不借其通过验本片。

另读准备总计划、原 `agent_platform.training.prepare/register_runner`、`core.write/git`、`perfctl.validate/baseline_ok`、`dev_platform.adapter.safe_file/read_raw`、canonical SHA、原训练 reader／submission、state file lock 与 process 装载路径。283 冻结文件独立逐件重算匹配 manifest，未见本片修改。C2 页面、F9c／F9d、业务试用仓库不在本片范围。

## 需求／正确性结论

所查主路径满足 C1 的边界：CLI／HTTP 使用同一 training 应用入口；预览在专用子进程中临时替换原 training 模块的 CONFIG／TRAINING 并 finally 恢复，沿原 register_runner／prepare 生成计划；唯一输出映射为 spec 的 manifest URI，原 manifest 原始字节仍生成 Binding。新意图先由原不可变 writer 保存，再直接调用原 prepare 发布三件，未复制字段、别名、baseline、窗口或 Binding 算法。

完整计划固定项目／home／execution／registration、revision、完整 request、source 文档及原始字节 SHA。确认核当前 revision 与完整 preview SHA；已有意图的重复 prepare 仅读回。显式恢复重新暂存生成同一计划、比较 source 字节和已发布字节；冲突不覆盖，无意图的原生目标占用不接管。状态读不导入 native training 模块或 Temporal SDK，不查询服务；运行成功和准备成功分列。1 MiB 原文档与 16 MiB 聚合意图界限均有明确拒绝，无截断。

占用检测的实际范围是**本项目 manifest、共享 global manifest／spec 和同 ID 准备意图**。原始“孤立外项目 ID”措辞经本轮澄清后已在计划明确为此范围，不声称扫描其他项目仅存的 manifest 来重建人为删掉的全局登记。此为支持边界说明，不要求另建全项目索引或第二登记权威。

### P2：完整发布后的显式恢复绕过执行 checkpoint 拒绝

首轮位置：[reference_training_preparation.py](../../src/ergora/reference_training_preparation.py#L135)，原 `publish` 在 `observed.status == prepared` 时先返回，`ensure_unstarted()` 在后。可达场景：先成功 prepare，再有原 job 目录、fence 或 start intent，随后用原 intent SHA 与当前 revision 显式 resume。首轮会成功返回 prepared，跳过约定的“已有 job／fence／start 明确拒绝”。它不会启动训练或覆盖文件，但静默接受了已进入执行阶段的恢复请求；已有测试只保护首次 prepare 前的 fence，未覆盖这条早返。

最小修复：把原 `ensure_unstarted()` 移至完整状态早返之前；保留 `status` 和重复相同 prepare 的只读路径，完整且未 start 的同意图仍可读回。以三种后续 checkpoint 的参数化回归确认显式 resume 拒绝，且原意图／三件原文件保持。

**修后代码及最终 r2 补核：已关闭。** 当前第 135 行先调用原检查，再在第 136–137 行处理 prepared；未增加新 validator、流程或调度。计划与训练手册明确了显式 resume 和只读读回的差别。修后准备 owner SHA 为 `89b9d129ab2d62d108281041d0a2c92a6a9cf638f622a933488a25d974ae878f`，测试 SHA 为 `bd7d1d9c106806c43f640f0a764a1a4fcfbfd018031a2ec8dcd3038233759935`。新增三类 checkpoint 回归已读代码及最终安装原 stdout，均 PASSED，并核其原件保持与只读路径。首轮 owner SHA `c64eca0411e4ffd12d17d85e9f2ccdc4a8986d4e82f800880851d55926a1e7f6` 的 r1 验收保持旧范围；关闭依据为下节修后 r2 证据。

## 维护性结论

本轴所查范围无独立结构阻断项。`reference_training_preparation` 的单一职责是原三件发布的计划／恢复状态机；动态 reference 子进程入口是其实际生产消费者，类内私有算法无需另造调用者。serializer 从 setup 移至 context 后被 setup 与 preparation 两个生产模块实际复用；共享项目 context 继续拥有注册与路径不变量。training `_setup` 的 callable 参数服务实际 setup／preparation 两条入口，没有扩展成通用插件框架。

新增检查主要保护外部输入、保存意图、跨项目归属、路径、source 漂移和恢复状态，处于原不变量的责任边界。原 native writer／registry lock 仍拥有不可变发布；本地非阻塞 intent lock 与短时项目 revision 预留未引入远端 I/O。所查测试的四个真实中断点、丢成功回复、source／文件漂移与原件保持保护的是可能静默损坏，未发现为实现细节或普通可见错误堆叠测试的阻断问题。

## 独立核验与证据限度

私有原件根为 `.ergora/checks/training-preparation/`，以下为本轴实际读取／重算，不只接受作者结果 JSON：

- 已读源码首轮 `source-r1.stdout` 的 38 passed／1 failed（95.88 秒）及修正 runner 归属检查后的 `source-r2.stdout` 39 passed（64.93 秒）；保留失败的原范围。
- 亲自读取 r1 wheel、安装包和构建快照，逐件核 571 产品、wheel 与 installed 两份 RECORD 的 hash／size，以及 source／installed 各 283 冻结文件。wheel SHA 为 `cd3e98c1bcce0448efaeb38839f0f1a75509e88dff7a43ac7281a57a3498691e`，非 editable。P2 修正前当前源与 r1 的产品差异仅 training.py 一行注释；P2 修后不再宣称同一产品。
- 已读安装 r1 六 suite 的原 `process/stdout.txt`、空 `stderr.txt` 与 monitor 结果：65 passed／212.14 秒，monitor succeeded／0／214.042 秒。未称全库运行。
- 已读真实安装 CLI 的 11 条 argv、原 stdout／stderr 与执行脚本，核错误 SHA 的非零退出和零发布检查、同意图重试／恢复及原 reader；已读实际 `-P -S` 脚本和 status 输出，其中明确断言无 site-packages、找不到 Temporal SDK。
- 亲自复算 CLI 与 HTTP 两份意图的 canonical SHA：`062018fc69fb0ceb58ed232b95da16e198a4c142d8c6f1ca85510df144a980e7`、`7aff96a19e614d7684a8884bc10cf6c106790a00538c4533343d071316bb9f00`。各三原文件逐字等于意图；spec URI 指向真实 manifest，Binding SHA 等于该 manifest 原始字节 SHA，runner／baseline 原始 SHA 和文档均匹配意图。
- 已读实际 HTTP client 的发送后关闭 socket 流程、原 requests.jsonl 的服务端 prepare 200，逐件重算已保存 response body 的长度／SHA；GET、错误 intent、显式 resume 与同 prepare 的原件相符。该证据来自实际 loopback，不以 TestClient 代替。
- 亲自复算 protected-before 的 8 件原配置／baseline 字节保持；确认两实验外无 job／fence／submission／approval／命令 marker，验收 Git 工作树 clean；检查原 HTTP 端口已关闭，并读取 process cleanup 记录。
- 读过自身模板的实际 15 件输入清单和原始结果身份，其 approve 仅属作者自身模板范围，不作为本轴独立结论。

本轴仅运行只读标准库核对、AST／JSON 解析、完整 tracked whitespace 检查和本地端口连接检查；没有另跑 suite、安装或产品操作。修后 11 件产品／测试／CI 的路径→SHA 映射，按 sorted compact JSON 编码重算摘要为 `457c85c85e14fc9cd143dfae2c2e34921e0b51a3c10a0dac41b3b87a8ccf1b69`；这不是作者采用其他字节拼接规则的 packet 摘要。

首轮当时待验的 r2 包／当前产品身份、修后三 checkpoint／四中断边界及最终原件现已补核，见下节；未将当时在途状态改写成首轮已完成。

## 修后最终 r2 本地补核

再次运行完整 tracked／new 清单，补核时共 26 件，包括本文、公开准备证据，以及后来新增的三件前片记账（runner 的计划／交付／公开证据）。已读后三件 diff，仅补其固定发布与自己的 CI，不改本片 11 件产品／测试／CI。亲自按作者算法 `路径 + NUL + 完整字节 + NUL` 重算这 11 件的组合 SHA，等于 `4414d4f7f8fba705e18373c53a827f6eca0691d2a04fd5a48a452208dfa0e983`；与 `product-current-r2.json` 一致。测试／CI 当前字节也等于实际运行的 r2 快照。

**最终包身份通过。** 直接读取 r2 wheel、安装目录、构建快照和当前源码，571 产品文件逐字全等；逐行重算 wheel 579 行与安装 584 行 RECORD 的 hash／size、283 冻结文件及非 editable direct_url。wheel SHA 为 `cc96e63433d647a0e9db33f2de52ff056090d274ae211863c36e591606df0935`。原私有 setup 在选择不存在的旧依赖缓存 r2 interpreter 时 venv 退出 2，原 setup／stderr 保留；已读 recovery 脚本及两条成功原 argv，改用既有固定 r1 缓存离线安装已经构建的同一 wheel，无产品或依赖变更。没有把失败称为首次安装成功。

**受影响安装运行通过。** 已读 `install-r2/regression-r2/process/stdout.txt` 全文、空 stderr 及原 monitor result：15 passed／69.67 秒，monitor succeeded／returncode 0／71.393 秒。三种后续 job／fence／start intent、四个实际 `os._exit(73)` 中断点、source／文件冲突及 CLI／HTTP 丢回复恢复全部列明 PASSED。原 r1 六 suite 65 项仍只代表修前产品，未声称最终全库重跑。

**最终实际 CLI／HTTP 与原件通过。** 已比对 r1／r2 验收脚本差异仅输出环境根，逐件读 r2 的 11 条安装 CLI argv／stdout／stderr（错误 SHA 唯一非零退出 2），以及真实 `-P -S` 无 SDK status 输出。重算 r2 CLI／HTTP 两意图 canonical SHA 分别为 `32949ddf1838b161be5a17ca506f18e49937f5bb3b1ffc08e10d5acdce1e0c03`、`7f254915d0f76854eea97bdc28d94fa3696a878c3f72906e5ad5869578417c1f`，与预览／读回一致；各三件逐字匹配，spec URI／manifest Binding 与原 source SHA／文档均一致。已读真实 HTTP client／steps／requests.jsonl，服务端原 prepare 200 与后续 GET／resume／同 prepare 的 9,794B body SHA 相同，逐件核其他 body 的长度／SHA。8 件 protected 原件保持，无 job／fence／start／批准／命令 marker，验收 Git clean；读取原 monitor cleanup 并实际检查原端口已关闭。

最终自身模板实际 stdin 与冻结 prompt 逐字相等，SHA `ba2efbb5947ed7169eda785a4624eb873bb5125d15c97a21b469d4d1da150bdd`；亲自从 stdin 按 15 件索引提取完整 265,212B 并重算各 SHA，父／叶 instructions 与 Skill 原文均在。原结果 SHA `b7c4144e5e198f7d878a86088cf611407d408a3ebabdab08bd3b1b9e6f8bc0c4`，approve／33.487 秒，仅记录作者自身模板范围。补核时公开准备证据 13,177B、SHA `58c2ba99b853b879319fd219a68671e146569e16de8ab312e13d4ab0fce1686a`，52 份 r1／r2 私有引用的长度／SHA 全部独立复算相符；之后评审状态记账不构成产品重测。

**最终本地需求／正确性通过，开放 finding 0；所查维护性无新增 finding。** 完整 tracked whitespace 及本文本地链接已检查，行号链接改用 GitHub `#L135`。仍待普通精确提交／推送、完整远端 Ref 及本片自己的必要 CI 固定身份补核。C2 页面、原生 Windows OS、真实训练／GPU、质量／性能、evidence 批准与采用继续保持原未验范围。

## 固定 Git 发布身份补核

本轮仅只读固定 Git 对象与保存的私有发布原件，没有读取后续 C2 产品工作树，没有发出远端请求或运行 suite／安装／服务。候选为 **`92e7c24dbeb6847fe20c00e69c89c04b17702d5e`**；直接读取 commit 对象确认唯一父提交为原基线 **`80236fe8957c0704a3c73c7ea1440f7f288ff563`**。父→候选恰有 27 个改动路径，与 `static-final-r1.json` 完整集合一致；用 `git cat-file --batch` 读取这些固定 blob，逐件重算长度／SHA，27 件全匹配。候选内本报告恰为前述最终本地版 13,250B、SHA `8cee91d141fde2e89b5d706f88bc8133bae89e7846ec0b30c9d6a2f1a536c004`；后补状态不改变该候选。

原 r2 wheel 的全部 **571 个产品文件**与固定候选 `src/ergora/` 路径集合及 Git blob 逐字全等，wheel SHA 仍为 `cc96e63433d647a0e9db33f2de52ff056090d274ae211863c36e591606df0935`。直接从固定 blob 重算 11 件产品／测试／CI 的组合 SHA，仍为 **`4414d4f7f8fba705e18373c53a827f6eca0691d2a04fd5a48a452208dfa0e983`**；候选内 283 冻结文件也逐件匹配其 manifest。因而发布产品与前述修后 r2 安装、交互及原件证据的产品相同，未以之后工作树继承旧运行结论。

已读原 `commit.py`、`publish.py` 及三份发布回执。提交脚本约束原父提交、开发分支、完整 27 个 staged 路径、staged whitespace 和提交后固定 blob 一致，原 commit 退出 0 并记录同一完整候选。原 push 退出 0，目标为 `HEAD:refs/heads/refactor/architecture-foundations`，argv 无 force／mirror／main 合并；原回复记录 `80236fe..92e7c24` 前进。随后原 `ls-remote` 退出 0、stderr 空，stdout 精确为完整候选加完整 `refs/heads/refactor/architecture-foundations`。该结论绑定原保存回执的当时远端事实，没有额外查询当前远端。

|发布原件|字节|SHA-256|
|---|---:|---|
|`static-final-r1.json`|6,152|`3454e506a9a3f47d676db8386f6717a619362f238701b7d10a3dd4bae54e72ab`|
|`commit-r1.json`|1,174|`e01d74d3b5659bfd90da53acaca03c1b5572c4849fcbdff7d3af022b16856f0b`|
|`push-r1.json`|750|`f25bd1b7bba27994bd1d157ee882ad1fd9122fd5629a356d1c42890f6ce80ec6`|
|`ref-r1.json`|738|`3a64b9bc443ba74ba6f85196a3a3f9365733ba3f1743dd10409190ff621598c1`|

对两固定提交运行完整 `git diff --check`，退出 0；按候选 Git tree 核 242 个本地 Markdown 链接均存在。候选内准备公开证据为 13,183B、SHA `9bb31d49c81c04a64bddc06f6875000b5926371be1442fa87192d284e58c2559`，52 份私有引用长度／SHA 全部重算相符；其 `publication: not_committed` 是提交前的历史状态，不追认成该文档当时已知发布结果。原 runner 发布／CI 记账属于原片，不作为本片 CI 通过证据。

**固定产品／普通发布／原完整 Ref 身份通过，开放 finding 0；本片自己的 CI 尚待发现及官方 run／必要 job／step 终态原件。** 本次仅补本文，不提交／推送。C2 页面及既有 Windows／真实训练／GPU／质量／性能／批准等未验范围继续保持。
