# AC4.3c.1：专长执行者合同设计

日期：2026-11-09。固定基线`0fd881e4f21d2814eaf7ce0db47a7fd3c28c4144`，前片只读DAG已精确交付，自己的CI42584734023双OS七必要步骤及独立08:40:39.414164 UTC明确HTTPS完整远端核验通过；本片不沿用其验收证明新的写支持。

## 范围和现有所有者

根据用户对专长化实例、嵌套串并行、全部祖先资源及权限收窄的要求，制定[工作Agent合同](../plans/2026-11-09-work-agent-contract.md)。本片只有设计、原计划细分及独立审查，不新增schema、模式、队列、执行代码或可start的v5。

主代理已追踪原`DevelopmentWorkflow.units/context/stage`、`Executor.prepare/execute`、选择执行器、`stage_driver`、backend Interface、当前完整输入及原review协议。原units拥有依赖调度；原每job checkout、claim、路径gate、检查、fence与commit继续拥有副作用。当前只读`run-input`显式拒绝写/shell/network，不能直接称为正式执行者入口。

拟由固定分配将每个原unit交给一个冻结implementer实例，原unit与静态模板的传递顺序需一致，结构资源完整装载。新workspace模式必须与原只读模式区别，后端构造/能力差异归其自身；跨阶段work输出只能在原integrate/verify之后进入review，权限、MCP与OS保证分别说明。旧v1-v4保持，完整v5消费者接通前不能保存伪运行配置。

## 节点和验收

|节点|状态|
|---|---|
|C1a原调用链与初稿|已完成；合同给出固定选择、映射/端口/权限/副作用及恢复所有者|
|C1b静态与新独立两轴|新fresh-context Spec/Standards均通过、0finding；平台增量复核通过；6文档/79链接/82 parser通过|
|C1c普通文档交付|C1b及前片精确交付已通过；本片最终文档范围/静态检查通过后普通提交；Markdown路径过滤适用，不新增应用CI|

静态校验、独立结果、最终范围、普通推送和明确HTTPS远端按实更新。本设计不证明可写CLI工具组合、真实推理、训练/GPU或跨阶段运行；这些是合同中后续C2–C5的实际验收。


## 设计门禁通过

[新独立评审](2026-11-09-work-agent-contract-review.md)核完整tracked/new五文件与追加平台范围，再由两位fresh-context分轴检查，**Spec/Standards均通过，0finding/0设计阻塞**；含报告后的6份Markdown/79本地链接与锚点/82条现有CLI parser及完整空白检查通过。原实际调用链和平台限制由独立源码核对，CLI help只当后续调用语法资料，没有运行模型或应用测试。

合同补充第一workspace-task-mcp与现有原执行器/固定资源机制一致，为Linux/WSL2；Windows已有支持保持，包CI不能替代新写路径原生旅程。设计门禁同时约束C3/C4：必需来源/未知恢复消费者未完整接通时不能先宣布v5可用；需要合片时更新节点，不延后安全合同。前片精确交付已终结，本片待普通文档提交后的精确对象和HTTPS远端核验。


## 文档交付前收口

最终包含合同、计划、设计报告与前片精确交付记账，共7份Markdown；以本仓库源码运行现有检查得到 **98本地链接/锚点、82 CLI parser全部通过**，diff空白检查通过。一次误用旧开发venv的已安装CLI，因其缺少当前`task evidence`子命令而解析失败；改用显式`PYTHONPATH=src`后通过，没有改生产代码或测试。原记录分别保留，不以旧安装覆盖当前基线。合同与已审平台段无实质修改；后续状态记账不构成新的运行能力。

普通文档提交后由同片设计评审者核精确对象、Markdown路径过滤和明确HTTPS远端身份；不运行模型或应用测试来证明文档交付。
