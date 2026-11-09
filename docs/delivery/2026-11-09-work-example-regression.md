# WA-CI1：专长示例数量回归

固定基线 `8a856f54c0e0d16b762f5c62ca1b170eca2ddd9f`，属于[工作Agent纵切片](2026-11-09-work-agent-runtime.md)的同片CI修正。前片生产实现及本地双轴通过，原 [CI42599729729](https://github.com/626619403/Ergora/actions/runs/42599729729) 的 Windows 必要回归已实际失败：`test_complementary_examples_material_and_filtering_share_backend_without_sharing_identity`将全examples/agents目录库存固定为2，新validation专家使其为3。原job页记录1 failed /749 passed /572 skipped /16 subtests /439.33秒；完整run终态仍另核，不取消在途作业。

## 原失败与最小修正

作者用原R2非editable包重跑完全相同的原测试，**1 failed /0.54秒**，`3 == 2`；原日志保留。该测试的行为是比较architecture-reviewer和kernel-implementer的相同后端、不同身份、职能/专长过滤及完整资料，不应由整个示例目录数量决定。修正显式选择这对示例，独立digest数量按实际sources长度比较；其余原断言保持。没有将常数2改为另一个目录库存常数，也没有改生产源、示例、依赖、CI作业或超时。

原R2包运行整份 `tests/test_agent_definitions.py`，**54 passed /1 skipped /15.74秒**；跳过是真实Windows junction场景，本机Linux不能运行，Windows CI继续执行原测试。命令为原独立R2 Python的 `-I -m pytest -q -ra tests/test_agent_definitions.py`，basetemp在本片持久checks目录。私有 `ci-example-test-fix.json` 固定完整命令、实际测试SHA、原wheel SHA及两日志SHA。

[同片独立复核](2026-11-09-work-agent-runtime-review.md)检查原红/修后全组及实际差异通过；WA-CI1的本地修正与最终交付门禁分别记账。原8a CI失败不改写为通过；修正候选普通提交、自己的必要双OS CI和明确HTTPS远端身份仍待取得。当前下一片内置默认组合不夹带于此修正，不用其CI替代本修正候选。

## d8fc8ef 精确交付补核：通过

本节由新的独立交付核验者 `/root/work_runtime_delivery_closure` 补核，身份有别于原源码主审及其两个轴的审查者；不替代或冒称原 Spec / Standards 审查。固定候选为 `d8fc8ef2eee64b51a9eb5fa1925734e475965785`，唯一父对象为 `8a856f54c0e0d16b762f5c62ca1b170eca2ddd9f`。本轮只读 Git 对象、保留原件和官方交付状态，并追加本节；没有修改实现或测试、安装、执行测试/模型/服务、委派、提交或推送，当前 AC4.4 工作树不在范围内。

候选恰为三文件：`tests/test_agent_definitions.py`、本记录和原 runtime 独立审查记录。测试 Git 对象 SHA256 为 `4d75b81a856553b246c8ac5a34273ce0f1faa40bfd2e1904aae136c7eda58306`，与已复核修正及原 R2 包测试证据一致；Python AST 通过，生产源码、示例、依赖和 Portability workflow 与父对象完全相同。另核原独立对象记录 SHA 与全部 38 个父对象文件相符；其中 37 文件在 d8 保持原字节，仅原审查文档追加已记载的核验。保留 R2 wheel 的 SHA 仍为 `6fe8a5a663ef82fb9468e5d3eb24c6cb0f82a4f011e6f6e8c96743b5a13c1bdf`，**372 个包成员逐字等于 d8 Git 对象及原安装目录，283 个冻结文件相对 C1 基线无变化**。原红 `1 failed /0.54秒` 与修后 `54 passed /1 skipped /15.74秒` 两日志摘要也分别匹配。

独立取得的官方原页保存于 **2026-11-09 10:53:42–10:53:43 UTC**，离线核验于 **10:54:57.577398 UTC** 完成；[本候选 Portability run 42602114137](https://github.com/626619403/Ergora/actions/runs/42602114137) 为 **Success 终态**。完整 job-group 已取尽，run 的完整候选链接、workflow、实际 job 名称、`selectedJobId` 及每个必要步骤的精确 commit/check/log URL 均相符；**七个必要步骤全部 success，均带 job-completed 标记**：

| 官方 job / check | Build and install wheel | Packaged reference identity | Native application regression | Windows PowerShell 5.1 installer and upgrade |
|---|---|---|---|---|
| [Windows 3.12，129108868803](https://github.com/626619403/Ergora/commit/d8fc8ef2eee64b51a9eb5fa1925734e475965785/checks/129108868803) | [success](https://github.com/626619403/Ergora/commit/d8fc8ef2eee64b51a9eb5fa1925734e475965785/checks/129108868803/logs/4) | [success](https://github.com/626619403/Ergora/commit/d8fc8ef2eee64b51a9eb5fa1925734e475965785/checks/129108868803/logs/5) | [success](https://github.com/626619403/Ergora/commit/d8fc8ef2eee64b51a9eb5fa1925734e475965785/checks/129108868803/logs/6) | [success](https://github.com/626619403/Ergora/commit/d8fc8ef2eee64b51a9eb5fa1925734e475965785/checks/129108868803/logs/7) |
| [Ubuntu 3.11，129108869149](https://github.com/626619403/Ergora/commit/d8fc8ef2eee64b51a9eb5fa1925734e475965785/checks/129108869149) | [success](https://github.com/626619403/Ergora/commit/d8fc8ef2eee64b51a9eb5fa1925734e475965785/checks/129108869149/logs/4) | [success](https://github.com/626619403/Ergora/commit/d8fc8ef2eee64b51a9eb5fa1925734e475965785/checks/129108869149/logs/5) | [success](https://github.com/626619403/Ergora/commit/d8fc8ef2eee64b51a9eb5fa1925734e475965785/checks/129108869149/logs/6) | 平台条件不适用，skipped |

原 [8a 的 run 42599729729](https://github.com/626619403/Ergora/actions/runs/42599729729) 同轮官方读取确认为 **Failure 终态**，与历史 Windows 数量断言失败保持一致；d8 的成功不改写该失败。原本地 90 秒超时及其原样单项重验也继续按[原审查记录](2026-11-09-work-agent-runtime-review.md)保留。

**2026-11-09 10:53:41.016300→10:53:42.565367 UTC**，在仓库外禁用系统/global Git 配置和凭据助手、避开仓库局部配置，明确对 `https://github.com/626619403/Ergora.git` 执行只读 `ls-remote`；私有 trace 确认实际使用 `git remote-https`，没有被 URL rewrite 转成 SSH。远端 `refs/heads/refactor/architecture-foundations` 返回完整 SHA **`d8fc8ef2eee64b51a9eb5fa1925734e475965785`**，与候选一致。

私有补核原页、脚本、Git/包比对、原红/修后日志身份及 HTTPS 读取结果统一登记在 `closure-d8/closure-evidence.json`，SHA256 为 `005b68b49fa4934bdf4196d7fde95ebcabf8602896bf9cf9a03f5a8257e97321`；本轮原件另存，没有覆盖原 8a CI 目录。**本次补核结论：d8 的对象/保留包身份、自己的必要 CI 和明确 HTTPS 远端门禁全部通过，WA-CI1 精确交付终结。** 原本地双轴结论继续由原审查记录承担，AC4.4 与其后候选须各核自己的证据。
