# Windows CI预算修正独立审查

日期：2026-11-14。按[计划](../plans/2026-11-14-windows-ci-budget.md)与[交付](2026-11-14-windows-ci-budget.md)，以固定基线 `c4aa7acb555a5d55fec7e7a483544834e8afe44f` 审查当前工作树的 Portability 一行预算差异。已读 `AGENTS.md`、当前 `docs/PLAN.md`、原 workflow、完整 workflow diff 及原始 CI 证据。本 reviewer 为该 CI 小片的新 fresh-context 独立 reviewer；同工作树的 F10c2b1 产品、测试与既有产品独立结论不在本轮审查范围内。

## 原件与静态核查

- 原 run `43553150941` 的 `ci-run-html-r5` 与八个 job 的原 HTML／receipt 已逐份读取、校验 HTTP200、精确 URL、字节数与 SHA256。Windows 使用 `ci-job-132319976802-html-r5`；其余七 job 使用各自 r2。所有必要 step 的 log URL 均绑定完整基线 SHA 与对应 job ID，已与 `ci-observation-r5.json` 逐项比对。
- `ci-ui-metadata-r1.json` 及其原 `ci-job-batch-r1/body.json`／receipt 的来源 hash 相同；该 r1 只提供 job 身份和 run 路径，不能用于推断后来的终态。已读 `parse-ci-html.py`，未执行其写回路径；本轮另用纯内存 HTML 属性检查复核八 job／30 必要步骤。
- 原 run 终态明确为 **Cancelled**；30 项中 **29 success／1 cancelled**。Windows 应用回归 `03:45:40Z–04:04:00Z` 成功，安装升级 `04:04:00Z–04:04:31Z` 取消，随后上传成功。原 job HTML 的官方注释为 `The job has exceeded the maximum execution time of 20m0s`，另有安装步骤 `The operation was canceled.`。这些原件支持“总 job 时限截断 installer”，不支持“原 SHA 完整 CI 成功”或“installer 已通过”。
- 独立核对原／新 workflow 字节，确认当前文件恰为一行替换；SHA256 分别为 `ec2816e893c25ff3a7f96513e677bdf53f42d90b3cd79fe585e474a27c0121b2` 与 `4a23020b277de1fa3d07db42918314127a013e01cad8ebf0cd9e020109774b64`，与 `windows-ci-budget/static-r1.json` 相同。另独立用已安装 PyYAML 在内存解析两个完整 workflow，将新 `jobs.native.timeout-minutes` 恢复为20后对象完全相同。该检查证明 YAML 差异范围，未执行 GitHub 表达式。
- `scripts/ci/linux-groups.json`、`scripts/ci/run.py`、`tests/windows-installation.ps1` 均与固定基线逐字相同。六 Linux 分组加一个 Windows `group all` 和 plan 仍构成八 job；原30项必要检查、完整 Windows 应用入口、PowerShell5.1安装升级、上传及其条件均保留。

## 需求／行为轴

**本地审查 approve；确证 finding 0，开放 finding 0。** [workflow 第46行](../../.github/workflows/portability.yml#L46)仅把 native 上限从统一20分钟改为 `${{ matrix.os == 'windows-latest' && 30 || 20 }}`。现有矩阵明确生成 `windows-latest`／`ubuntu-latest`，该条件与所需 Windows30／Linux20一致，直接针对原总时限原因；没有更改测试选择、步骤断言、安装入口或成功判定。

发布依赖从“先取得原 SHA 全成功”调整为“保留并由原 reviewer 核原取消原因／未通过范围，CI 小片独立审查后与已独立本地验收的 F10c2b1 一并普通发布，再验新完整 SHA 自己的全部 CI及原 reviewer 补核”，在这些约束下不实质削弱验收。它改变承载 workflow 修正的候选和发布顺序，没有把原29项成功补写成30项，也没有让旧结果替代新候选的必要检查。本轮不代替 F10c2b1 reviewer 或原产品 reviewer 作产品／发布／CI批准。

## 结构／维护成本轴

**本地审查 approve；确证 finding 0，开放 finding 0。** 单一 owner 内的一行矩阵条件已经表达完整差异，不增加调度器、分组或重复 workflow。Linux上限仍20分钟，plan仍5分钟；现有唯一 Windows job 的最坏允许运行时长增加10分钟，其他 job 不因本修正增加上限。正常完成即可结束，不固定多耗10分钟。

30分钟是针对已观测总时限不足的有界余量。原证据未测得 installer 完整耗时，本轮也没有证明新产品在30分钟内必然完成；这属于新候选的真实 CI 待验项，不应通过减少覆盖或把取消当成功来关闭。

## 仍须完成的真实验收

1. 原 F10c3a reviewer 对原 `c4aa7ac` 的 Cancelled、唯一未完成 installer 及依赖调整作补核；原候选始终不称完整 CI 成功。
2. CI修正与另片产品按各自独立结论普通发布后，绑定新的完整 SHA、实际发布内容和完整远端 Ref；本报告当前绑定工作树 workflow hash，未预批尚未产生的新 SHA。
3. 新完整 SHA 自己的 Portability 必须终态 Success，原八 job／30 必要步骤全部成功，包含完整 Windows 回归、PowerShell5.1安装升级和上传；核实际 GitHub 表达式生效、job时限与原始 run／job 证据。原29项成功不能抵扣新检查，30分钟再次不足时仍须如实保留失败并处理。
4. 完成新候选原 reviewer 的固定发布／CI终核后，再更新所属交付状态。本轮零 finding 只关闭一行 CI 修正的本地独立审查，不关闭这些门槛。

本轮仅本地读取、廉价内存 YAML／HTML／hash／属性比较，并写此报告；未联网、安装、运行 suite、修改产品或 workflow、提交或推送。

## 固定普通发布补核

固定候选为 `0f01fdd9736fc456cf1cdcc8d77e64dac916e8a0`，唯一父提交精确为原基线 `c4aa7acb555a5d55fec7e7a483544834e8afe44f`。补核时 HEAD 与该候选相同，分支仍为 `refactor/architecture-foundations`；当前差异为发布状态文档。此节只核 CI 小片在共同发布中的身份、原必要脚本及发布证据，完整30个变更 blob 与 F10c2b1 产品验收由该片原独立 reviewer 补核。

直接读取固定 Git object 的 workflow、本报告本地版本、CI计划、CI交付与CI公开 evidence 五份 blob，字节数／SHA256 均与原 `retrospective-memory-candidates/static-final-r1.json` 对应条目相同。固定 workflow 为 **3,056B**／SHA256 `4a23020b277de1fa3d07db42918314127a013e01cad8ebf0cd9e020109774b64`，等于前述独立已审版本与当前文件；本报告的固定本地版本为 **5,304B**／SHA256 `63faa9219c14897e34c48acac8476ed854cca1ac50ff44b2c60c703234a9f265`，等于本次追加前原字节。固定 SHA 到基线的 CI 差异仍仅为 native timeout 一行 Windows30／Linux20；`scripts/ci/linux-groups.json`、`scripts/ci/run.py`、`tests/windows-installation.ps1` 在固定 SHA、基线和当前工作树逐字相同，八 job／30 必要步骤及原完整 Windows 回归／安装升级门槛保持。

已读原 F10c3a reviewer 的[终态与取消原因补核](2026-11-14-retrospective-skill-adoption-review.md#自己的-ci-终态与取消原因补核)：明确原 `c4aa7ac` 的 run `43553150941` 为 Cancelled，29项 success／唯一 installer cancelled，原因是原20分钟总 job 截止，完整 CI不通过。前述“原 reviewer 核取消原因／未通过范围”一项现已完成；原 installer 尚未成功的历史和新候选完整 CI门禁继续保留。

已直接读取原 `commit-r1.json`、`push-r1.json`、`ref-r1.json`，三份 exit 均为0，candidate 均为上述完整新 SHA。普通推送命令精确为 `git push origin HEAD:refs/heads/refactor/architecture-foundations`，无 force 或 main 目标；保存的完整 Ref 回执 stdout 精确为 `0f01fdd9736fc456cf1cdcc8d77e64dac916e8a0\trefs/heads/refactor/architecture-foundations\n`，stderr 空。本 reviewer 核的是保存的原回执，未重新联网查询。

固定 Git blob 内的 CI公开 evidence 含 **23** 份原引用，`private_base` 为 `.ergora/checks/`；发布后列表前23项与固定列表逐项相同，仅追加上述 static-final／commit／push／Ref 四份原回执，合计 **27** 项。已逐份重新读取27份原件，路径唯一，bytes／SHA256 全部一致，无缺失或差异。公开 evidence 的其他变化仅为 publication 字段，仍明确 `new_candidate_full_own_ci_required:true` 和自己的 CI `pending_discovery`；计划／交付的发布后变化只追加固定发布、完整 Ref和23→27关系，没有新增 CI成功主张。

**本固定发布补核：需求轴 approve；结构／成本轴 approve；确证与开放 finding 均为0／0。** 该结论只把已审 CI小片绑定到实际普通发布的新完整 SHA。新候选自己的 CI尚待发现，原八 job／30 必要步骤必须全部成功，并完成原 reviewer 的新候选固定发布／CI终核；本节未执行 GitHub表达式、未证明30分钟充分、未预批运行，也不重写旧 `c4aa7ac` 的取消历史。本轮仍仅读取固定 Git／原回执并追加此报告，未联网、安装、运行 suite、修改产品、提交或推送。

## 固定新候选自己的 CI终核

本节核固定候选 `0f01fdd9736fc456cf1cdcc8d77e64dac916e8a0` 自己的 run **43555532175**，取代前述该候选 CI待发现／待终核状态。核查时 HEAD仍是该固定 SHA，但工作树已有后继产品变化；这些变化不在本次补核范围，也不作为该固定候选的运行依据。

直接读取官方 `ci-run-html-r6`、Windows `ci-job-132327455188-html-r6` 和其余七个 job 各自 r2 HTML／receipt，核 HTTP200、精确官方 run／job URL、原字节数及 SHA256。run原页面明确为 **Success**，完整 commit链接精确指向上述 SHA，页面分支为 `refactor/architecture-foundations`。run HTML SHA256 为 `3b1b7637361d9360b15aa46c3a37fc7f3b95d0337b1b80b6bed376ba4581f75f`；Windows HTML SHA256 为 `db8f636ebb63ac7120785fbefac28e0e4307340c15ea61c80c7f069e91f6f493`。

原 `ci-ui-metadata-r1.json` 的八 job ID／名称／路径已与原 UI JSON batch逐项比对，batch receipt／hash及最初 run summary的完整 SHA链接均相同。该 r1当时的 in_progress状态只保留为早期采样；本轮终态从各自原 r2／r6 HTML独立读取，没有将旧采样改写成成功。

独立从固定 SHA的 workflow及六组 `linux-groups.json` 导出必要步骤，再在原 HTML内逐项核查：plan **1项**、六个 Linux job各 **4项**、Windows **5项**，共 **八 job／30必要步骤全部 success**。每项均有 `data-job-completed`、非空开始／结束时刻，以及精确绑定此完整 SHA和本 job ID的原 log URL；开始不晚于结束，结束不晚于对应 receipt取得时刻。八个原 `Complete job` 步骤也全部 success，各 job原步骤未见 failure／cancelled。独立投影与 `ci-observation-r6.json` 逐项相同，`required_steps_passed:true`。

Windows五项必要步骤的原时间如下，均为2026-11-14 UTC：

|必要步骤|原时段|原 conclusion|
|---|---|---|
|Build and install wheel|04:13:32–04:14:12|success|
|Packaged reference identity|04:14:12–04:14:13|success|
|Native application regression|04:14:14–04:33:38|success|
|Windows PowerShell 5.1 installer and upgrade|04:33:38–04:34:38|success|
|Upload regression observations|04:34:38–04:34:39|success|

应用回归用时 **19分24秒**，之后安装升级 **60秒**成功；原 `Set up job` 为04:13:25，`Complete job` 为04:34:42，可见流程约 **21分17秒**，超过旧20分钟仍完整完成。固定 workflow已在此精确 run中被 GitHub接受执行，30分钟预算足以完成本次完整 Windows门禁；这不是对未来 suite增长或运行波动的时长保证。

又从固定 Git object复核 workflow SHA256仍为 `4a23020b277de1fa3d07db42918314127a013e01cad8ebf0cd9e020109774b64`，相对 `c4aa7ac` 仍恰为 native timeout一行 Windows30／Linux20。内存解析完整 YAML，复原该值后对象完全相同。原 `scripts/ci/linux-groups.json`、`scripts/ci/run.py`、`scripts/ci/pytest_phases.py`、`tests/windows-installation.ps1` 在基线与固定新 SHA逐字相同；原矩阵、全部必要步骤、Windows全量入口、安装升级、上传及其失败条件没有缩减。

公开 CI evidence的 `raw_evidence.ci_references` **68项**已逐份读取核 bytes／SHA256，路径唯一且全部位于既定 `private_base: .ergora/checks/` 下的 `retrospective-memory-candidates/`，无缺失或差异。此 CI列表与原发布引用列表无交集。固定 **23项**仍与发布后 **27项**的前23项逐项相同，后四项仍只有原 static-final／commit／push／Ref回执；27项也已全部重新核 bytes／SHA256。新 CI的多次早期采样与终态分别保留，没有混充固定23项或覆盖原证据。

**本 CI终核：需求轴 approve；结构／成本轴 approve；确证 finding 0／0、开放 finding 0／0。** 此 CI预算小片的固定发布和新候选自身八 job／30必要步骤门禁已核实关闭；与其共同发布的产品其他验收沿该片原独立报告，不由本节扩大。成功仅属于新 `0f01fdd`／run43555532175；旧 `c4aa7ac`／run43553150941仍为 **Cancelled、29项 success、installer cancelled**，从未取得完整 CI成功，不因新候选通过而重写。

本轮仅本地读取固定 Git、原 HTML／回执及廉价内存解析，并追加此报告；未联网、下载或声称读取 artifact archive／完整远端测试日志，未另报远端 pytest数量，未安装、重跑 suite／模型、修改产品、提交或推送。
