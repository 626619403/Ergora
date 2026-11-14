# Q1.1：精确本地审查包交付

日期：2026-11-15。原始要求、范围及验收见 [具体计划](../plans/2026-11-15-local-review-packets.md)与 [Q 总计划](../plans/2026-11-15-domain-review-optimization-quality.md)。固定基线 `eecd90aa70c9268144af1161ade9076790dabf92`；分支 `refactor/architecture-foundations`，开始时工作树干净。

|步骤|实际状态|
|---|---|
|恢复与计划|已复核 AGENTS、PLAN／Q0 交付、Git 状态、原完整材料与 CLI／发布／Schema／CI owners；应用既有工程与代码质量 Skill。具体片计划已写。|
|用户补充|Q 总计划保留 kernel 专家评估节点，允许无需算子干预；历史研究、旧 v2 模板与原任务保持。|
|实现|state-free prepare／verify／read、严格 Schema、完整三提交源／diff／显式上下文与祖先规范、原子不覆盖发布已实现；共享读取迁至正式 executor，原 full 材料安装回归通过。|
|验证与安装|r1 原四 suite 70 项通过；修后 r2 安装 38 项通过，614 源／wheel／安装逐字相同，283 参考 PASS；自身原模板 Codex r2 approve。环境使用 system-site-packages，不称 clean 安装；Windows 待当前候选自有 CI。|
|独立审查与发布|新 fresh-context 两轴 r2 最终本地 approve；R1／R2 修复后关闭，开放实质 0／0；待普通发布、精确 Ref 与当前候选自有 CI。|

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
