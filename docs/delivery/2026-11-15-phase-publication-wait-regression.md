# B3.3a CI接续：final故障观察等待

日期：2026-11-15；基线为固定`5182bfa03f536d4090b91014f97eedda1c5d2d3a`。本片仅修改原测试等待与文档，不改任何产品／冻结283、预算或故障注入。

## 原失败与原因

自己的[Portability43670140205](https://github.com/626619403/Ergora/actions/runs/43670140205) Linux group5／job132678181529在原应用回归失败。官方HTML annotation明确两项`test_cycle_final_publication_is_bounded_and_dead_owner_recovers_only_the_same_fence[final-file-blocked / final-directory-blocked]`均报原owner未在等待内停止；同组468通过／13跳过／1599 deselected、776.01秒。完整日志没有取得，不能推断它们的具体进程时间线。原run已终态：七job成功／一失败、29必要步骤成功／一失败；Windows及PowerShell安装升级成功。完整原HTML和请求失败保存在前片私有CI证据目录，原独立报告保留R4（需求request-changes／结构approve／开放1／0）。

固定源码已证：测试给wall24／cleanup14，但从submitted返回后等待20秒，超时helper会SIGKILL owner再抛同一断言。该外部观察上限可能先于原合法总期限；本地慢启动时恰好通过不代表20秒足够。

## 修改与验收合同

仅将这两个参数化场景的等待改为原`authorized.total_remaining_seconds + 5`：依据实际授权快照覆盖原期限并给实际回收余量，不改变wall／cleanup、compute窗、owner／phase停止算法或默认值。保留真实final fsync marker、原件保持、公开submission、同fence恢复和唯一次start断言。沿原已有两个回归，不添加重复测试或CI分组。

在原最终r2非editable SDK安装上，冻结当前tests/examples、核其中173份tracked输入后精准运行这两个场景；精准安装结果为2 passed／67 deselected／65.44秒，外层66.446秒；两个真实fsync marker均实际出现，同fence恢复与原件／唯一次start断言保持。原CI的两项实红不改记成功。沿原648三方逐字／283产品身份，不为未改产品重建wheel或重跑模型／真实服务。新的fresh-context reviewer核原要求、固定差异、原CI annotation与实际精准结果后，再普通提交／推送并核该提交自己的CI。前片原失败保持，不改记为成功。

后继[B3.3b协议设计](../plans/2026-11-15-training-executor-protocol.md)r2独立两轴通过仅为文档，尚无后继产品；kernel专家留在原v3优化路径。

## 本地精确验收

私有原件位于本片ignored检查目录，包含实际argv／exit／XML／stdout／stderr、两个原owner和phase输出、marker、原授权与fence。此次复制范围含未使用的前端node_modules／构建产物（3101份总输入），另以`testscope-effective-r1.json`固定并逐字核173份tracked tests/examples；选中的Python测试未加载或执行多余前端文件。没有为此改变或重跑未改产品。本地通过只归该安装与测试，独立审查、普通发布与自己的CI仍待。

## 新独立本地审查通过

新的fresh-context reviewer已核固定七份作者来源、唯一AST等待改动、原官方CI annotation、原648源码／wheel／两安装及RECORD／283、173份tracked输入、精准2项、两marker和owner身份停止；需求approve／结构维护approve、开放0／0。[审查报告](2026-11-15-phase-publication-wait-regression-review.md)和私有`reviewer/static-audit-r1.json`记录范围。四份后续状态文字已另核，不替换原candidate-r1身份。

开始最终staged静态核与普通发布；自己的CI、固定发布独立补核仍待，不把原518失败改记成功。kernel路径与全部产品保持原字节。

## 固定发布与自己的CI待核

已普通发布`75bc99d788a9cef292b7c41eb7e01ac03d13de47`，parent518，tree`a66b45a205de85e0d9a9b9ae3f3164aa4d9d28d3`。九blob／完整staged diff-check／一测试AST和173个最终Git tree链接通过；产品／scripts／CI差异为空。普通push exit0／5.9066秒，完整SSH Ref同一，提交时工作树干净。同片新reviewer已接续核固定发布和它自己的CI，原518失败保持。

初次本地链接检查器把支持的`:行号`当作文件名，十个目标检查失败；原结果单列保留。修正检查器解析后173链接通过，公开文档及产品未因该检查器错误改变。此后在本地开始b1／b2产品，不在本接续自己的CI与终核闭合前推送后继产品。

## 自己的CI终态

固定75bc自己的[Portability43672292421](https://github.com/626619403/Ergora/actions/runs/43672292421)／attempt1已终态成功：八job／30必要步骤全部success，包含Linux group5和Windows／PowerShell5.1安装升级。官方完整navigation、每job必要步骤、固定commit链接及Actions列表相符；同片新独立最终需求approve／结构维护approve、开放0／0，精确接续门禁闭合，不借原518的成功项，原518七成功／一失败保持。
