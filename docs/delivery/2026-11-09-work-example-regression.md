# WA-CI1：专长示例数量回归

固定基线 `8a856f54c0e0d16b762f5c62ca1b170eca2ddd9f`，属于[工作Agent纵切片](2026-11-09-work-agent-runtime.md)的同片CI修正。前片生产实现及本地双轴通过，原 [CI42599729729](https://github.com/626619403/Ergora/actions/runs/42599729729) 的 Windows 必要回归已实际失败：`test_complementary_examples_material_and_filtering_share_backend_without_sharing_identity`将全examples/agents目录库存固定为2，新validation专家使其为3。原job页记录1 failed /749 passed /572 skipped /16 subtests /439.33秒；完整run终态仍另核，不取消在途作业。

## 原失败与最小修正

作者用原R2非editable包重跑完全相同的原测试，**1 failed /0.54秒**，`3 == 2`；原日志保留。该测试的行为是比较architecture-reviewer和kernel-implementer的相同后端、不同身份、职能/专长过滤及完整资料，不应由整个示例目录数量决定。修正显式选择这对示例，独立digest数量按实际sources长度比较；其余原断言保持。没有将常数2改为另一个目录库存常数，也没有改生产源、示例、依赖、CI作业或超时。

原R2包运行整份 `tests/test_agent_definitions.py`，**54 passed /1 skipped /15.74秒**；跳过是真实Windows junction场景，本机Linux不能运行，Windows CI继续执行原测试。命令为原独立R2 Python的 `-I -m pytest -q -ra tests/test_agent_definitions.py`，basetemp在本片持久checks目录。私有 `ci-example-test-fix.json` 固定完整命令、实际测试SHA、原wheel SHA及两日志SHA。

[同片独立复核](2026-11-09-work-agent-runtime-review.md)检查原红/修后全组及实际差异通过；WA-CI1的本地修正与最终交付门禁分别记账。原8a CI失败不改写为通过；修正候选普通提交、自己的必要双OS CI和明确HTTPS远端身份仍待取得。当前下一片内置默认组合不夹带于此修正，不用其CI替代本修正候选。
