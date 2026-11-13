# 同事试用入口与专家范围说明

日期：2026-11-13。用户要求将试用说明写入顶层README，并确认计划中的子Agent与模板是否全部补齐。

## 范围与基线

产品基线为`2d13c0ee76ddeb960365b6b8e77853801def14d5`，分支为`refactor/architecture-foundations`。开始时已有B2f发布记录与同片评审补核五份未提交文档；它们保持各自范围。本片只改README、PLAN、D2计划与本交付／独立评审报告，不修改产品、测试、依赖、参考发行或HTML。

验收要求：README清楚区分控制台安装与正式任务运行、可导入定义与实际原生执行，提供正确分支与CLI命令，列明已交付专家和15个细方向，明确cluster-resiliency／low-precision／kernel专门根及原生流程仍待完成；链接到完整手册和计划。原已验模型旅程只引用其原记录。

## 实施与检查

README已加入当前试用范围、开发分支、Linux命令与Windows入口、四个主要模板／十五细方向、共享专家和未完成项。原有部署／训练详细章节与手册链接保留；D2计划已按实际catalog标记剩余三个方向，PLAN已登记本片与下一片。

复用B2f已安装的非editable wheel，清除`PYTHONPATH`并使用本片全新控制目录，完成六条CLI检查：`composition presets`列出20项，治理导入、重构导入及重构重复导入均退出0，`serve --help`和`reference verify`退出0。原件见本片私有检查目录的`cli-checks.json`与逐命令stdout／stderr；未重装依赖、调用模型、启动服务或运行正式任务。

四份本片文档227个本地文件链接／Markdown锚点均存在，`bash -n scripts/install.sh`及`git diff --check`通过。这些检查不证明联网全新安装、Windows运行或端到端开发再次通过。

新fresh-context独立评审指出README把权限误列为AgentDefinition字段（SP1／P2）：实际独立Agent定义拥有职能／资源等字段，权限由WorkflowDefinition与Agent节点按项目grant及祖先上限约束。已将README改为工作流为实例声明权限，原评审已复核关闭；没有改动schema或运行行为。[独立报告](2026-11-13-colleague-onboarding-review.md)的需求符合／可维护性均通过，开放0／0，也覆盖PLAN第0条的过期状态修正。

初稿227目标和收口前225目标是各自检查快照；最终包含B2f结案与新评审报告的八份文档共239个本地目标／锚点，均有效，语法与diff检查通过。纯文档片沿既有push路径过滤，不触发产品CI；B2f自己的八job／30步骤只绑定原产品提交，不授本片新的产品／模型运行通过。

本片没有新增方向包或原生适配。下一实施片为D2-B2g集群／恢复只读资料子模板，随后低精度和独立kernel方向；真实训练、集群、GPU与Forge全部会话执行另按原计划验收。
