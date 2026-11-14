# G1d-CI 独立评审

评审者：`records_ci_scope_review`，2026-11-14，新 fresh-context。先读委托中的用户要求、切片合同及实际工作流／差异，再读作者交付叙述；未继承实现过程。遵循 `AGENTS.md` 与独立评审要求，仅检查原件并写本报告。

## 范围与身份

固定基线及检查时 HEAD 均为 `6c7c45f79e499dde83d9880043342710a28d7809`；候选是该 HEAD 上尚未提交的本片变更，不是已发布 SHA。

完整读取基线与当前 `.github/workflows/portability.yml`、两份新增完整文件 [具体合同](../plans/2026-11-14-records-ci-scope.md)／[交付记录](2026-11-14-records-ci-scope.md)，以及 `docs/PLAN.md` 中 G1d-CI 状态。另核 `pyproject.toml`、`scripts/ci/run.py`、`scripts/ci/linux-groups.json`、`scripts/ci/pytest_phases.py`、参考导入脚本及相关测试消费者。G1c 手册与 G1b 记录同处工作树，但不纳入本片批准。

|原件|检查身份 SHA-256|
|---|---|
|基线 workflow|`4a23020b277de1fa3d07db42918314127a013e01cad8ebf0cd9e020109774b64`|
|当前 workflow|`be814a956237b8a64258f396fa81a972ff764ceaa3ea16ffefa8e82be89a4353`|
|新增本片合同|`1433fa04072b737910f5d7e0dfa6ec07c2c4a95bf20e95435c2ef79c9838e6ed`|
|修后本片交付|`c597a59676bd14edc72f4d0965f0be2c95d889884ff87cf08d640c88c85361eb`|

## 需求符合性

**本地 approve；开放 finding 0。** 实际工作流差异仅第 6 行增加 `docs/delivery/evidence/*.json`。去掉此项后，完整配置解析结果与原件一致；当前字节也恰为基线的一次字面插入。产品、schema、测试、脚本、安装器、依赖与 CI 执行内容均无本片变化。

直接读取 [GitHub 官方路径过滤说明](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#example-excluding-paths)及[文件路径模式说明](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#patterns-to-match-file-paths)：模式从仓库根匹配完整路径，`*` 不跨 `/`；全部变更路径被忽略才省略 workflow，任一路径未被忽略仍运行。因此：

- 在原有分支过滤条件下，直接子级交付 JSON 与已有忽略项组成的纯记录 push 可以省略矩阵。
- 嵌套 JSON、其他文档资源，以及产品／schema／例子／测试／脚本／依赖／工作流自身的变化仍保持原触发；混合 push 不会因包含交付 JSON 而跳过。
- `pull_request` 与 `workflow_dispatch` 保持原入口，权限、concurrency、artifact、时限、完整 jobs 与步骤保持。原六 Linux 分组加 Windows 和 plan 仍为八 job，原 30 必要步骤未削减；这不是本候选已运行成功的主张。

生产／测试／脚本及依赖文件中未找到该证据目录消费者；包数据仅来自 `src/ergora/data`。邻近的文档读取是安装帮助或参考 HTML 导入，不读取该 JSON 目录。现有实际边界支持把它视为交付摘要，而不是随包资源或测试输入。

## 可维护性与冗余

**本地 approve；开放 finding 0。** 改动位于拥有触发语义的现有 workflow，复用 GitHub 原生过滤；没有新包装层、过滤脚本、CI job、产品断言或镜像实现的测试。完整 jobs 与分组消费逻辑未变，必要真实行为覆盖保持。

私有一次性静态检查只证明语法、原件身份及范围，没有接入产品或另造 glob 解释器。减少纯记账触发的收益可由官方规则推导；本评审未测量 CI 时长、额度或产品性能，不据此扩大性能结论。未来若接入该目录为实际输入，合同已要求同步修订触发边界。

## Finding 与处置

**R1／P3，已关闭。** [交付记录](2026-11-14-records-ci-scope.md)第 5 行初稿仍写“尚未修改配置”，与第 9 行及实际差异冲突；恢复工作时会混淆本地实现与发布状态。最小修正是明确“配置已在本地修改，尚未普通发布或实测云端触发”。作者已按此修正，评审者直接复读完整文件并核上表修后身份；无开放项。未发现本片其他需求或维护性问题。

## 已检查与限制

- 独立核完整基线／当前 workflow、tracked diff、两新增文件及相邻消费者；产品／测试／脚本／依赖 diff 为空。
- 使用现有 PyYAML 6.0.2 `BaseLoader` 独立核配置与字节差异；完整 jobs 相等，六 Linux 分组和 Windows 选择保持。
- 只读核私有 `records-ci-scope` 域中的 `static-r1.py`、`static-r1.json`、`workflow.diff`；保存的基线／当前／diff 指纹与现场相符，diff 指纹为 `d735ce469edb676c115b00ab2fc1f3c48fd59e3a79095fe1ba3d44f4ad5b2aff`。未重跑会写产物的原脚本。
- tracked `git diff --check` 返回 0；两新增完整文档的 no-index 检查均无空白诊断。未安装依赖、运行产品测试、取消 CI、提交、推送或外部写入。

本结论只批准上述本地切片。静态解析和官方规则核对不能替代 GitHub 实际触发与最终候选 CI，也不批准 G1c 或整个工作树。

## 尚缺的终核材料

1. G1b 自己的 `43589988699` 终态原件及原 reviewer 闭合。委托与记录将其列为在途，本评审未查询远端最新状态，也未取消它。
2. G1c 分别审查后共同候选的精确提交、完整含新增文件的发布范围、普通推送与完整远端 Ref，以及本 reviewer 的固定发布补核。
3. 该共同候选因变更 CI 文件而产生的自身原八 job／30 必要步骤终态及原 reviewer 终核；不能借 G1b 或其他候选的成功。
4. 完成该候选后，最终纯记录同步的实际路径适用性、普通推送与完整 Ref 核验；保留前述候选真实 CI 原件，后续无新 run 不构成产品通过证据。

以上材料到齐前，本片不能标记精确交付闭合，本报告不预批未来运行。

## 最终本地汇总身份补核

2026-11-14，同一 reviewer 复核新增[公共摘要](evidence/2026-11-14-records-ci-scope.json)、更新后的本片合同／交付全文与四份固定原件。HEAD 仍为 `6c7c45f79e499dde83d9880043342710a28d7809`，workflow 仍为上表 `be814a…`，产品／测试／脚本／依赖 diff 为空。

|本次本地记录|SHA-256|
|---|---|
|本片合同|`79ffaf481f226fda35285e7056862bea06cfd4890c7bfe6e5923070d189ab897`|
|本片交付|`4f6478b26a9622094db0812cf1103dd9ce4233ade2e57d67b75546c2dd83b101`|
|公共摘要|`092070970fe59358ce3e6e10de58112efd830a1fc4c694ccbfdbe10de9bd5f2e`|

摘要的 `validation` 与原 `static-r1.json` 完全相等；本地两轴结论、开放 0／0 和 R1 关闭均准确投影原独立报告。四个不同引用逐件核字节与 SHA-256：`static-r1.py` 2,570B、`static-r1.json` 1,176B、`workflow.diff` 534B、`independent-local-r1.md` 5,871B，合计 **10,151B**，全部匹配摘要。独立快照身份 `84dff15a1e601e3d05a9cb0ac1f667503957394f6b41ad7d223fb7e554a9393c` 与追加本补核前的完整报告相同；追加内容不冒称已经包含在旧快照中。

本片合同仅新增勾选本地独立审查，交付保留 R1 修后句并追加实际结论和原件索引；固定发布、自身 CI 与最终记录同步在合同和摘要中仍为待验。三份记录的完整新增文件空白检查无诊断，没有新增测试或外部操作。

**最终本地需求／维护性均 approve，开放 0／0。** 上述终核缺项保持；G1b 的 CI 仍按提供材料记为在途，本次未查询远端，也不预批后续共同候选、自己的八 job／30 步骤或最终纯记录同步。

## 固定普通发布补核

2026-11-14，同一 reviewer 只读补核共同候选 `77d173675f3eb65e6821ebe57ce9087a05e4caaa`。直接读取固定 Git 对象、发布原件及前继终核材料；仅追加本报告，未联网、安装、运行测试或执行发布脚本。

|审查轴|本次固定发布结论|边界|
|---|---|---|
|需求符合性|approve，开放 finding 0|本片固定 workflow、前继门禁、完整发布身份和普通 push／Ref 原回执|
|维护性|approve，开放 finding 0|原四引用保持，八共享发布件可重建，产品／测试／脚本／依赖与 CI 执行内容保持|

- 固定候选唯一父为 `6c7c45f79e499dde83d9880043342710a28d7809`。完整差异为 22 路径，全部固定 blob 的字节数／SHA-256 与 `static-final-r1.json` 相符，未借当前工作树补足已发布内容。共同清单包含 G1c 文档、G1b 终态与状态记账；本节只核其发布身份，不批准 G1c 文档语义。
- 固定 workflow 仍为 `be814a956237b8a64258f396fa81a972ff764ceaa3ea16ffefa8e82be89a4353`，相对唯一父仍恰好插入原定 `docs/delivery/evidence/*.json`。独立解析并去掉此项后完整配置相等，jobs 完全相等；其他 `.github` 文件未变，`src`／`tests`／`scripts`／`pyproject.toml` 差异为空。PR、手动、矩阵、必要步骤、时限、权限和 concurrency 保持原结论。
- 原发布脚本先暂存完整 22 路径，再核完整 index 与字节，保存的 `staged_full_diff_check` 为 exit 0、无诊断，包含全部新增文件。本次对唯一父到固定候选再做完整 `git diff --check`，返回 0。原 `check-docs-r3.json` 的 18 份文档身份也全部等于固定 blob，记录 585 个本地链接／片段且无错误；这一静态检查不替代 G1c 实际语义评审。
- 前继 gate 绑定 `6c7c45f…` 自己的 run `43589988699`；其 `terminal_sha256` 与实际 13,357B 终态投影 `04cea53985e0e0d1933be1e740ceb60425fae4516cefbd700931c00acdab03dc` 相同。原终态为 Success、八 job／30 必要步骤通过。直接读取已提交的原 reviewer 终核及其 19,465B 固定快照，两者逐字相同，均为两轴 approve／开放 0／0；前继公共摘要的完成状态与之相符。gate、完整暂存核对、commit、push、Ref 原回执依次发生，未倒置前继闭合门禁。
- `commit-r1.json` 成功生成本唯一子提交。`push-r1.json` 的完整命令为普通 `git push origin 77d173675f3eb65e6821ebe57ce9087a05e4caaa:refs/heads/refactor/architecture-foundations`，exit 0，没有 force 或 main 目标；其后 `ref-r1.json` 在 11:47:13.818157 UTC 保存的完整 stdout 精确对应本 SHA 与该分支，exit 0。本次核原回执，未重新观察远端当前状态。
- 当前公共摘要的八项 `publication_evidence` 逐件重算字节／SHA-256 均匹配，合计 **19,796B**；原四项 **10,151B** 引用数组与固定提交相同，`validation` 原投影也未改。已发布本报告保留本地补核完整身份 `0b1027a368181bc24c8f65633da430d14e5939b48b008754a0535cd4869a79b5`，本节只在该前缀后追加。

上文尚缺材料中的前继闭合与 G1d-CI 固定普通发布现已核实；R1 继续关闭。**本 SHA 自己的原八 job／30 必要步骤及原 reviewer 终核、最后纯记录同步的实际范围／普通 push／完整 Ref 仍待。** 本节不借前继 CI 成功预批本候选，不以配置静态正确或尚无新 run 宣称它已通过，也不批准 G1c 语义。

## 精确候选自身 CI 终核

2026-11-14，同一 reviewer 离线独立核共同候选 `77d173675f3eb65e6821ebe57ce9087a05e4caaa` 自己的 [run `43591668528`](https://github.com/626619403/Ergora/actions/runs/43591668528)。读取固定 workflow／分组、保存的官方 HTML／UI JSON、响应回执及原投影，未执行原 fetch／parser／collector 脚本，未联网、安装或运行产品测试；仅追加本报告。

|审查轴|自身 CI 终核结论|边界|
|---|---|---|
|需求符合性|approve，开放 finding 0|精确 SHA、分支和 Portability workflow 的原八 job／30 必要步骤均成功且完成|
|维护性|approve，开放 finding 0|原件身份可重建，早期在途样本与私有查询错误保留，原本地与发布证据保持|

**独立重建结果。** 从列表页面 embedded JSON 定位唯一完整 commit anchor：run `43591668528`／number 209、`.github/workflows/portability.yml`、`refs/heads/refactor/architecture-foundations` 和 pushed 动作完全对应。初始状态为 in progress，仅用于发现；实际 UI job batch 的 `totalCount=8`、`hasMore=false`，八个 job ID 唯一，名称及 run／job 路径与 metadata 相同。按固定 workflow 和六个 Linux 分组重建预期矩阵，与这八个实际 job 集合相等。

最终 `ci-run-html-r12` 的实际页面 Status 为 **Success**，保留同一完整 commit anchor。原 URL 与 final URL 均为本 run、HTTP 200；回执时间 12:09:05.739680 UTC，正文 213,397B，SHA-256 `7e23075071b07f67a3d1e29346d7d5335b46674fa654afa4e64aafff230763dd`，与实际正文及终态投影相符。

独立使用 HTMLParser 读取各最终页面的 `check-steps`／`check-step` 属性：所有 job 均为 completed，且有唯一成功的 Complete job。必要步骤直接来自固定 workflow 的命名步骤并按 Windows 条件选择，包含观察上传的 `always()`，共 30 项；其完整名称、状态、时间、日志路径与原终态投影逐项一致。

|Job|实际 ID|最终页面样本|必要成功步骤|Complete job UTC|
|---|---:|---|---:|---|
|plan|132437516961|`ci-job-132437516961-html-r1`|1|11:47:20|
|Linux group 0|132437548232|`ci-job-132437548232-html-r3`|4|11:53:01|
|Linux group 1|132437548220|`ci-job-132437548220-html-r3`|4|11:52:59|
|Linux group 2|132437548238|`ci-job-132437548238-html-r2`|4|11:51:00|
|Linux group 3|132437548244|`ci-job-132437548244-html-r1`|4|11:49:38|
|Linux group 4|132437548235|`ci-job-132437548235-html-r2`|4|11:50:52|
|Linux group 5|132437548243|`ci-job-132437548243-html-r3`|4|11:53:11|
|Windows all|132437548222|`ci-job-132437548222-html-r9`|5|12:08:19|

30 项包含 plan 分组读取、七个执行 job 的 wheel 构建安装／包内参考身份／原应用回归／观察上传，以及 Windows PowerShell 5.1 安装升级。全部 76 个 success 步骤的日志 URL 均精确包含本完整 SHA、对应 job ID 和 step number；开始不晚于完成，完成不晚于该 job 的 Complete job，后者不晚于原响应回执。另六个 skipped 恰为六个 Linux job 的 Windows 安装步骤，没有额外失败或跳过。这里核官方步骤状态，不推断测试 case 数，也未读取日志正文或 artifact 归档。

**原件与保持范围。** 89 个 CI 引用路径唯一，逐件重算长度／SHA-256 全部相同，合计 **6,803,890B**；规范引用数组 SHA-256 为 `6fc04ac5f152022b5196ae160f96f0f530db5614177b1836d74fcdcf68a79ff4`，与 `ci-collection-r1.json` 相同。两份公共 JSON 的 `ci_evidence` 完全相同。38 组官方正文／回执均为 HTTP 200，原 URL／final URL 对应唯一的本仓库列表、本 run、batch 或八个 job，正文长度与 hash 均直接重算匹配。

终态投影为 13,358B，SHA-256 `4e98fc3f8018bf65a584fe8615419669c3c99a11d128ded3c1aa6d1098c4a69e`。原四项本地引用 **10,151B**、八项共享发布引用 **19,796B** 均再次逐件匹配，三个证据路径集合互不交叉；原四引用数组与固定候选相同。发布快照为 11,041B／`3a3d0de227292474e423113d79070d555b0ea0b3a7d5c5cae9ce08a442fa7066`，与追加本节前报告逐字相同。固定及当前 workflow 仍为 `be814a…`，当前产品／测试／脚本／依赖 diff 为空。

**保留的查询错误。** `ci-discovery-launch-r1.json` 的 566B 原记录已包含在 89 项中：首次私有 parser 在 fetch session 尚未结束、页面文件未就绪时提前启动，以 FileNotFoundError／exit 1 结束；后续 fetch 保存 HTTP 200，顺序重启后生成了本 run 的 discovery、batch 与 metadata。该记录与早期在途页面均保留；这是交付查询编排错误，没有被包装为产品、模型或本 CI run 失败，也未用在途状态代替终态。

本节关闭 **G1d-CI 精确候选自身 CI 门禁**；本地、固定普通发布与本候选必要 CI 的两轴均 approve，开放 0／0，R1 保持关闭。公共摘要可据本节同步原 reviewer 终态。**最终纯记录同步尚未发生**：实际受限路径、普通 push、精确提交／完整 Ref 及官方列表观察仍须另核，本报告不预批该同步，也不把随后无新 run 当作产品验收证据。

## 实际纯记录同步与合同最终终核

2026-11-14，同一 reviewer 只读核已普通发布的记录提交 `5cc463b31b9df22f6306dbe07a9c9e5f9defae80`、发布原件与一次官方列表捕获，仅追加本报告；未联网、安装、运行测试或执行同步脚本。

|审查轴|最终结论|范围|
|---|---|---|
|需求符合性|approve，开放 finding 0|实际受限记录路径、原生忽略适用性、原两 reviewer 的 CI 门禁、普通 push／完整 Ref 和有界列表观察|
|维护性|approve，开放 finding 0|沿现有过滤和记录入口，原证据保持，记录同步与产品 CI 身份分列；R1 保持关闭|

固定提交唯一父为已验候选 `77d173675f3eb65e6821ebe57ce9087a05e4caaa`。直接从 Git 对象读取全部 11 个 blob，字节数／SHA-256 均等于 `record-sync-r1-static.json`；路径集合完全相同，且全部已存在于父提交。九份计划／交付／评审 Markdown 均位于 `docs/`，适用原 `docs/**.md`；另外两份为 `docs/delivery/evidence/2026-11-14-portable-usage-handoff.json` 和 `docs/delivery/evidence/2026-11-14-records-ci-scope.json`，均为该目录直接子级，适用原 `docs/delivery/evidence/*.json`。没有嵌套 JSON、其他资源或产品路径混入。

相对父提交，`src`／`tests`／`scripts`／`.github`／`pyproject.toml` 无差异，workflow 仍为 `be814a956237b8a64258f396fa81a972ff764ceaa3ea16ffefa8e82be89a4353`。原完整暂存检查 exit 0；本次对两个固定提交再做完整 `git diff --check`，也返回 0。`check-docs-r4.json` 实际只覆盖这 11 路径中的 **9 份 Markdown／263 个本地链接或片段**，无错误，九文件身份全部对应固定 blob；该结果与先前 r3 的 18 份／585 项分列，不扩大为再次检查全部手册。

同步脚本在 commit 前明确检查接受的产品候选为完整 `77d1736…`、其 run 为 `43591668528`、八 job／30 必要步骤通过，并检查两片原 reviewer 的固定发布及自身 CI 均 approve。直接核固定记录中的两个 `ci_terminal_snapshot`：均与已提交的原 reviewer 完整终态报告逐字相同，长度／SHA-256 匹配；两份公共摘要明确绑定 `exact77d1736 own43591668528` 两轴 approve／开放 0／0。由此确认 CI 与原 reviewer 门禁先于记录提交满足，不借另一个候选或本次无 run 代替。

原 commit／push／Ref 回执依次成功。push 的完整 refspec 为 `5cc463b31b9df22f6306dbe07a9c9e5f9defae80:refs/heads/refactor/architecture-foundations`，exit 0，没有 force 或 main 目标；其后 12:16:26.637055 UTC 的 `ls-remote` 原回执完整 stdout 精确对应本 SHA 与该分支，exit 0。本次仅读原回执，未重新查询远端。

两份公共 JSON 的 `record_sync_evidence` 相同。原七份同步材料逐件重算字节／SHA-256 均匹配，合计 **13,596B**，规范引用数组 SHA-256 为 `ccbddf52b129a8ece223ff279807afabbbb4474f88446d81cfba5f8d18fbbfeb`。原四项本地、八项共享发布、89 项 CI 证据均再次逐件匹配；三个原投影与本记录提交中的数组相同，没有用新同步回执改写原验收事实。

**有界官方观察。** 直接读取 `record-sync-r1-actions` 的原 receipt／body 和 `record-sync-r1-observation.json`。原 URL 与 final URL 均为 `https://github.com/626619403/Ergora/actions`、HTTP 200；body 为 317,912B，SHA-256 `98d61b751abaab0ed643c5a79bd6198796dcd08bbee5e43c451aae801d80e747`，receipt SHA-256 为 `b6abc683e9c1b958eb5e3b30bf6114441ff7b1b9f17ac9b73d6b7b45d52f4214`。独立解析实际 embedded JSON 的 **25 条记录**，按完整 commit anchor 及 workflow 路径匹配，`5cc463b…` 的 Portability run 为 **0 条**；同一列表中完整 `77d1736…` 的 `43591668528` 为 completed／success、分支正确。重建结果与 12:18:06.246625 UTC 的本地观察记录一致；三份观察件共 **324,614B**，逐件身份与公共投影相同，原七引用保持。

这只说明该次捕获时点及 25 条列表范围内未见本记录 SHA 的 Portability run；不承诺全历史或未来不存在 run，也不构成本记录提交或产品的新 CI 成功证据。接受的产品 CI 仍归完整 `77d173675f3eb65e6821ebe57ce9087a05e4caaa` 自己的 `43591668528`。

**G1d-CI 原合同各独立门禁现已闭合，需求／维护性两轴最终 approve，开放 0／0。** 本报告原 16,198B 终态前缀在 `5cc463b…` 中保持，本节是该提交之后的新增评审记账。随后报告及完成状态的普通同步由实施者依原授权核实际范围与完整 Ref；本节不称该后续同步已经执行。依 `AGENTS.md`，报告和状态记账不触发递归评审，不因此增跑产品回归。
