# D2-B3a 提案交接独立评审

日期：2026-11-14。评审者：fresh-context 独立代理 `/root/proposal_handoff_review`。仅接收原需求、范围、固定候选与证据路径，未继承实现对话；按 AGENTS.md 和 maintainable-project-delivery 的独立评审要求，直接核对文档、原始产物与源码。

## 结论

|评审轴|结论|适用范围|
|---|---|---|
|需求符合性|通过；开放 finding 0|B3a 的字段说明、人工交接及原产物离线走查|
|可维护性|通过；开放 finding 0|沿用现有训练手册及原执行、证据、评价和批准所有者|

本范围内未发现需修正的问题，最小修正为无。结论不关闭完整 B3，也不批准任何候选、模型/GPU 运行或采用。发布仍按本片原出口另行记录。

## 固定候选与边界

源码基线与评审时 HEAD 均为 `41dd5aa30f589b5c27a1cc3f09db59d66005a40f`，分支为 `refactor/architecture-foundations`。评审对象是未提交六文件快照，快照 manifest 的 SHA256 为 `edc0ee2df7320e6d2323f1b46cfd5b17997fedf32fc1fb19dd2d2584d10dcf59`；逐文件核对其 bytes/SHA，六文件均与当前工作树相同。

- `docs/TRAINING.md`：仅新增“从专家提案填写原实验合同”一节；完整文件 SHA256 为 `cb8166b275d8f0c8a532d70767943f0ca3019d424edb6fb5050a65aa34997d16`。
- `docs/plans/2026-11-14-proposal-experiment-handoff.md`。
- `docs/delivery/2026-11-14-proposal-experiment-handoff.md`。
- `docs/delivery/evidence/2026-11-14-proposal-experiment-handoff.json`。
- `docs/plans/2026-11-13-specialist-presets.md`：仅 B3a 补充与相关链接。
- `docs/PLAN.md`：仅 B3a 检查点与相关链接。

已阅读固定 tracked.diff 和三个新文件的完整内容。当前工作树中的 B2h/B2i 发布记账、U3 备份及安装计划不属于本次评审；共享计划中的这些状态也未纳入通过结论。

## 判断依据

1. [手册](../TRAINING.md#从专家提案填写原实验合同)第 37–60 行覆盖原 experiment 的 22、baseline 的 6、runner 的 6 个顶层字段，并说明 workload 的实际来源。自由文本提案、模型后端名称、示例指标、公式和代码片段均未被提升为真实代码/配置/数据/初态身份；缺项须先补齐并保留未验。
2. 直接阅读原 `local/agent_platform/training.py` 第 58–103 行，确认 runner 的六字段、Git 根及 argv、独立 walltime、canonical/alias 一致性、commit 存在性、当前 baseline、固定比较器和 prepare 返回的最终 manifest SHA。手册未把 draft SHA 当执行绑定，也未把排队加执行窗口当总搜索成本控制。
3. 直接阅读原 `upstream/perfctl.py` 第 56–75、93–161 行及 `compare_runs.py` 第 65–229 行。`baseline_ok` 只匹配表中前四项；URI/质量文字仍由人核查。检查列表为可配置的非空唯一列表；E 的质量要求显式决定，N/A 必须为 true。手册没有固定模板中的 JVP、样本数、重复数、阈值或统计 seed，最终配置按实际版本与消费者选择。
4. 原 gate 校验结构、摘要与候选绑定并重算比较；它不认证执行者或证明真实训练。手册第 50、52、60、72 行明确身份真实性、指纹内容与人工追溯的责任，没有声称 validator 自动核验 notes/追溯表或原提案到实验的关联。独立评价与精确 evidence SHA 的人工采用仍保留。
5. 邻接的原 `training_executor.py` 第 51–129 行与原训练手册确认：显式 run-local 使用冻结 manifest、原 job、两臂 worktree 和受信 runner；证据归档/门禁、负结果、MLflow 与 Temporal 仍在原所有者。新增文档未建立第二执行器、转换器、schema、账本或调度路径，普通 Markdown 表只承担人工记录。
6. 原四份完整 result 的响应均直接阅读；设计、profile、kernel 和 measurement 都将输入和数值标为 synthetic/hypothetical，并列出缺失的真实候选、oracle、配置、环境及测量。measurement 的 `request-changes` 保持。公开字段追溯中的两候选/18 分钟限制是原合成任务的条件，没有变成新实验预算或实际执行结论。

## 独立检查与限制

独立重算公开投影：8,212B，SHA256 为 `8c216f5f05ce593575320b52d489cf7fa437c3d13098dfb02c02dbfcc76cc0c8`，与 [公开证据](evidence/2026-11-14-proposal-experiment-handoff.json)、私有 trace 去除时间字段后的内容一致。

逐项匹配四份原 native 记录的 run ID、input digest、实际 Codex binding、回退说明与 result SHA；重算四份完整 input 树摘要，核 task/prompt 字节、运行保存副本、原 result 保存副本及 native MCP 回执摘要。kernel task 含 design/profile 两份完整原 result；measurement task 含三份完整原 result，均逐字存在且前驱 SHA 一致。实际记录不声称不同后端成功，本次也未补造未记录的模型身份。这些是保留产物的一致性核查，不是对模型提供方、执行者或独立性身份的认证。

八份原合同来源（四模板、training.py、perfctl.py、compare_runs.py、evidence-format.md）逐字等于基线 Git，并匹配公开投影的 bytes/SHA。参考 manifest 本身等于基线，283 冻结文件逐项 SHA 通过。B3a 相关 23 个本地目标/10 个锚点及当前 `git diff --check` 通过。独立审计保存在本片私有 `reviewer-r1.json`；没有执行作者检查脚本。

作者的 195 目标/14 锚点及四个凭据值检查覆盖更大的当时工作树；本次没有重读秘密环境值，也没有把作者记录当成独立结论。没有安装依赖、运行模型、训练/GPU、参考执行栈或 suite，没有联网或提交。

完整 B3 仍缺真实 workload、baseline/candidate、有效配置、数据/初态、受信 runner 和独立评价材料。后续需把一份真实提案逐字段交给原冻结 manifest，在同一原实验与候选身份保留真实结果、失败/no_gain/unknown 和成本，再核独立正确性/质量/统计及适用的精确证据批准。本次资料通过不能代替该验收。
