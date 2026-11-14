# Q1.1：精确本地审查包交付

日期：2026-11-15。原始要求、范围及验收见 [具体计划](../plans/2026-11-15-local-review-packets.md)与 [Q 总计划](../plans/2026-11-15-domain-review-optimization-quality.md)。固定基线 `eecd90aa70c9268144af1161ade9076790dabf92`；分支 `refactor/architecture-foundations`，开始时工作树干净。

|步骤|实际状态|
|---|---|
|恢复与计划|已复核 AGENTS、PLAN／Q0 交付、Git 状态、原完整材料与 CLI／发布／Schema／CI owners；应用既有工程与代码质量 Skill。具体片计划已写。|
|用户补充|Q 总计划保留 kernel 专家评估节点，允许无需算子干预；历史研究、旧 v2 模板与原任务保持。|
|实现|state-free prepare／verify／read、严格 Schema、完整三提交源／diff／显式上下文与祖先规范、原子不覆盖发布已实现；共享读取迁至正式 executor，原 full 材料安装回归通过。|
|验证与安装|r1 原四 suite 70 项通过；修后 r2 安装 38 项通过，614 源／wheel／安装逐字相同，283 参考 PASS；自身原模板 Codex r2 approve。环境使用 system-site-packages，不称 clean 安装；Windows 待当前候选自有 CI。|
|独立审查与发布|新 fresh-context 两轴 r2 最终本地及固定发布 approve；R1／R2 关闭。原 ad16881 Windows 两项 fixture 删除只读 Git 对象失败保持；最小修正经原独立两轴通过并单独发布 a38dd21，其自有 CI 八 job／30 必要步骤全成功，原独立终态两轴 approve／开放0／0。|

本片不会关闭真实 B3、完整 Forge、领域 PR／MR 检出能力或多轮训练优化。下一步构建安装件并回归原六阶段完整材料，之后进行自身模板和新独立审查。


## R1 验证与审查发现

r1 wheel SHA256 `23ea59fd386d7d08dc70e21ebb83c63a483ab8cf36f125628bc3234c7615cbaa`，614 产品文件与源码逐字相同；安装四 suite 为新包、导入边界、原完整阶段材料与原 executor。70 项通过／234.20 秒；这保留 r1 身份，不自动证明修后包。

原结构模板真实 Codex 调用 `a843741846a14c778e07ed35e875bd70`，100.280 秒，`succeeded / request-changes`；完整 23 文件／602,080B、任务与所有声明父叶资源均核对在实际 stdin。与新独立评审各自发现：

1. evidence 在最终总容量校验前逐份最多读取 10 MB，聚合可过量。公开 prepare 回归在旧源码实际读入 12,000,035B，超过 10,000,001B 边界，实红；改为先核数量、需求与 evidence 共用剩余预算，定向修后 1 项通过／0.25 秒。最终 JSON 仍有独立硬限。
2. 同一 commit 的不同标签可有互相矛盾的文件表。旧源码回归实红；已在原离线 owner 核同提交表相等，待修后完整验证。独立补查 diff 的离线边界后，给本地包增加 diff 正文摘要与原容量核对；不造 diff 重放器，不扩大为来源／Git 树关联认证。正文和对应摘要一同重制仍需独立整包摘要识别。

旧失败与模型原结果保持。当前源码已修两项，并补 diff 摘要／限额反例和使用说明；源码新包／导入边界 37 项通过／3.68 秒。同提交和 diff 两条新回归在旧源码各实红，旧结果保留。r2 安装回归在途，之后重跑自身模板并交[原独立评审者](2026-11-15-local-review-packets-review.md)复核。


## R2 安装与回归

修后 wheel SHA256 `6a9f36c230955f67649f82d9eb1b7b5b92f2c2c633dc86cae5a993d98b94b48c`；相对 r1 只变更本地 packet owner 和 Schema 两个产品条目，共有 reader／正式 executor 保持 r1 字节。614 个源文件／wheel／安装文件逐字相同，283 冻结参考 PASS。在原验收 venv 升级非 editable 安装，不称 clean 安装。

r2 运行新包、导入边界和原完整材料 full 旅程 **38 项通过／36.01 秒**；源码 37 项保持原记录。包测试包含实际 CLI prepare／verify／read，空 PATH 的离线读回、不创建 home、已有／空目录不覆盖、源仓库移除、真实 SHA1／SHA256 对象、禁 replacement／外部 diff／textconv／filter／lazy fetch、变动预算及两项 finding 的公开入口回归。原 full 旅程仍沿原阶段／任务／权限／回执；确定性测试后端不冒称真实模型开发或 GPU 训练。未改变的其他原正式路径保留 r1 四 suite 70 项的证据，未为无关路径重复全套。

文档初核为九份 Markdown／393 个本地链接或 fragment／零错误；tracked 空白检查通过，含全部新文件的暂存检查尚待执行。原自身模板 r2 已通过，独立终核待到达；Windows 须后续当前发布自己的 CI，不能沿用 r1 或此前产品 CI。


原自身结构模板 r2 真实 Codex 调用 `9564e184230a41b8abe619657ee64fd6`：56.430 秒，`succeeded / approve`。23 份完整文件／608,241B，原任务、所有内联正文与声明父／叶资料均在实际 stdin，准备 prompt 与 stdin 逐字相同。input digest `35a6ad4be3cafd52ea7749b015989b474d636d7e63311faac95a35a5a2f0ff88`，原结果 SHA256 `f8f9a380d1703ed5525eb28b1879cfb6e6702b9143b9554b8bac996a53f7e6df`。按原授权采用 Codex，理由为此前较大 Claude 审查超时；本片没有新的 Claude 失败或异后端成功声明。只审所供完整文本，不声称它观察了安装、Windows、远端或 CI。


## 最终本地独立审查

[新独立报告](2026-11-15-local-review-packets-review.md)已核最终 r2：17 个 tracked／untracked 冻结文件，614 源／wheel／安装逐字身份，38 项 XML 的实际分组为包 22＋架构 15＋原 full 1，零失败／错误／跳过。评审者另以安装解释器 `-I` 独立重跑聚合预算／同提交表／diff 篡改／diff 预算四项，4 passed／0.97 秒；501 份超数 evidence 的旧复现修后在 **0 次 document read** 时拒绝，不发布。

评审者直接核原自身 r2 的任务、23 份全文与三份父叶资源、准备 prompt＝实际 stdin 和结果摘要；需求符合性与可维护性两轴最终本地 `approve`，R1／R2 均关闭，开放实质问题 0／0。该结论不提前证明发布、Windows 或适用 CI；下一步完成普通提交和精确推送，再核自己的 CI。


## 精确发布与真实本地包旅程

已普通推送 `ad168810b6caa9ed435d0b3fef833856c286edf9`，唯一父为固定基线，17 个文件，完整远端 Ref 相同，发布时工作树干净；不合 main。全部新增文件已纳入暂存后的 `git diff --cached --check`，通过；九份文档／394 本地链接或 fragment／零错误。首次网络推送遇代理 407，保留原失败；随后原 SSH 配置下普通推送成功，没有修改认证或绕过审批。

安装后的 CLI 对原基线 → 该提交实际执行 prepare／verify／read：17 个变更全部纳入，31 个去重 blob，base／diff-base／head 文件表为 14／14／22，包 1,264,589B，未创建指定的控制 home。原包 SHA256 `304aa55b91007627f0fee3db2ae8dd2f393133491698ca9db31abf6e791e43c3`；显式上下文和实际 r2 检查输出均完整保存，但包内仍按合同声明 evidence 是操作员提供、不会自动升级为可信结果。

自己的 [Portability 43618045174](https://github.com/626619403/Ergora/actions/runs/43618045174) 已由官方页面核到完整 SHA `ad168810b6caa9ed435d0b3fef833856c286edf9`，当前在途；尚未声明 Windows 或整矩阵成功。匿名 API 返回 rate limit 403，后续读取官方 Actions 页面，不由接口受限推断测试终态。固定发布独立补核和 CI 终态仍待。

## 原发布 CI 失败与 Windows fixture 修正

上述在途记录由本节终态覆盖，原失败保持：[43618045174](https://github.com/626619403/Ergora/actions/runs/43618045174) 的八 job 中 plan／六个 Linux 分组成功，Windows 回归失败，Windows PowerShell 安装／升级成功。30 个必要步骤中 29 成功、1 失败。官方 job annotations 保存完整结果：**2 failed、1108 passed、788 skipped、16 subtests passed／1080.19 秒**。两项失败均在本片测试主动删除 Git 只读 loose object 时产生 Windows `PermissionError`：移除源仓库和人为制造缺失 promisor blob。它们发生在测试 setup／cleanup，不是采集器报错。匿名完整 step 日志接口返回 404；原因与计数来自可读取的官方 annotation，不伪称下载了完整日志。

最小修正只在这两处删除前给测试拥有的 Git 对象设置 `0o600`，不修改产品、权限合同、CI 矩阵或跳过测试。使用原 r2 非 editable 安装解释器重跑完整 packet suite：**22 passed／4.15 秒**。此本地 Linux 结果不证明 Windows 已修；待原独立评审补核、单独普通发布该测试修正并核新 SHA 自己的 CI。Q2 领域模板仍为本地独立在途范围，不纳入这次测试修正发布。

## 修正提交自己的 CI 终态

最小修正已单独普通发布 `a38dd21891ac200c575e8520c49cc82f97c9d478`，唯一父为原 `ad168810…`，仅三个文件：测试五行及原 Q1 交付／评审记录；产品保持 r2 身份。完整远端 Ref 当时相同，完整已提交差异的空白检查通过。

该修正自己的 [Portability 43620231340](https://github.com/626619403/Ergora/actions/runs/43620231340) 已由官方完整 run／job 页面与分页终态核对：full SHA 一致、八 job 全成功、`hasMore=false`，**30 个必要步骤全部成功**，包括 Windows 应用回归与 PowerShell 安装／升级。原 `43618045174` 的两项失败不改写；新成功只属于固定修正提交。随后 Q2 才普通发布下一提交，未取消该终态验收。[原独立审查者](2026-11-15-local-review-packets-review.md)已重解析八份官方 job 原件并逐项核30步骤、日志URL完整 SHA／jobID、固定发布及其远端历史和后继祖先；最终两轴 approve，开放0／0。Q1.1 精确交付闭合，真实 B3／完整 Forge 等出口保持。
