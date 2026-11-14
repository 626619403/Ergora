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
