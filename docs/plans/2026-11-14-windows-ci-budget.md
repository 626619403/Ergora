# Windows完整CI时间预算修正

日期：2026-11-14；基线 `c4aa7acb555a5d55fec7e7a483544834e8afe44f`。本片只改Portability的Windows job时间上限，作为F10c2b1普通发布的必要CI修正分别审查；不改变原应用、测试分组、断言、安装脚本或必要步骤。

## 原始证据与修正

固定c4aa7ac的CI43553150941，八job／30必要步骤中29项成功；全部Linux、Windows build／reference／application regression和upload成功，唯一installer为cancelled。官方Windows job132319976802的r5 HTML明确注释“exceeded the maximum execution time of 20m0s”；原应用步骤03:45:40Z–04:04:00Z（18分20秒），installer04:04:00Z–04:04:31Z后被总job截止截断。不能把该候选记成完整CI成功。

`.github/workflows/portability.yml`的native timeout仅改为Windows30分钟、Linux20分钟。保留八job／30必要步骤及完整Windows应用suite／PowerShell5.1安装升级。时间上限不预留固定花费，正常完成仍立即结束；本片不通过删测试或分担覆盖掩盖取消。

## 发布与验收依赖调整

此前F10c2b1发布等待c4aa7ac自己的全成功CI。现在其CI已终态取消，剩余检查需要新的workflow配置才可能完成；workflow配置修改须由新的完整SHA承载；当前沿已配置的SSH普通推送入口发布。记录原候选失败及原reviewer的终态原因核查，再将一行预算修正与已独立本地验收的记忆产品一并普通发布，使用这个新完整SHA自己的全部必要CI验收。新成功只属于新候选，不能重写c4aa7ac或继承其成功身份。

这是发布依赖的具体调整，未放宽完整CI验收门槛；新候选CI成功及原reviewer终核之前，均不称最终交付完成。该小CI修正用新的fresh-context reviewer审原YAML差异、原HTML／回执与预算来源，不重复模型／应用suite；原记忆片仍由原reviewer作本片发布／CI补核。

- [x] 读原取消HTML／30步骤及workflow20分钟上限，确认实际原因。
- [x] 保留全部检查，仅调整Windows上限；原YAML解析／差异静态核。
- [x] 新独立CI范围两轴approve／开放0／0；原F10c3a reviewer已核原取消终态／原因与installer未通过范围，原66引用保持。
- [ ] 与F10c2b1普通发布；新完整SHA／自己的全部必要CI及原独立终核。

实际结果写[交付](../delivery/2026-11-14-windows-ci-budget.md)。

已共同普通发布`0f01fdd9736fc456cf1cdcc8d77e64dac916e8a0`，30固定blob／完整远端Ref同一。记忆固定259／发布后263引用及CI预算固定23／发布后27分别保持；原固定发布补核和新SHA自己的全部必要CI待，不覆盖旧c4aa7ac取消历史。

原记忆与CI预算reviewer已分别固定发布补核approve／开放0／0；新候选自己的CI43555532175在途，所有必要检查与原终核待，旧取消身份保持。

新SHA0f01fdd自己的CI43555532175已由官方最终run／八job原HTML记录为Success：30必要步骤全部成功，包含完整Windows应用、PowerShell5.1安装升级与上传；另列68条CI原引用，不改原固定／发布后引用。原reviewer终态补核待；旧c4aa7ac取消历史保持。

原CI reviewer已完成同一固定候选的终核：两轴approve／开放0／0，实际Windows约21分17秒完整完成（应用19分24秒、安装60秒），本次30分钟预算已获实际验收；原23／27与另68CI引用全部保持，旧20分钟取消保持。
