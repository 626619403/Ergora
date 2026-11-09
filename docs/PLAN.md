# Ergora 实施计划与进度

最后更新：2026-11-09。本文件是恢复入口；状态按实现、验证、独立审查、提交/推送分别记录。详细规格和历史证据保留在下方链接，避免每次恢复重读全部日志。

## 当前检查点

- 仓库：`626619403/Ergora`，当前工作分支`refactor/architecture-foundations`；默认分支`main`已由维护者设置。只沿已授权工作分支普通提交推送，不自动合入main或强推。
- CR2b版本化提交/证据读取已交付，`8151a1c674fd6c664b4ce6aeba11a5fdf12be426`，29文件；自己的[双OS CI42538555105](https://github.com/626619403/Ergora/actions/runs/42538555105)七必要步骤成功，独立2026-11-09 00:20:12.521999 UTC核远端同SHA。[记录](delivery/2026-11-09-composition-transport.md)／[独立审查](delivery/2026-11-09-composition-transport-review.md)。前片CR2a精确25d83ec/双OS CI42537178771已终结，原c36 Windows失败保留。
- CR3a可信verify已普通提交推送`d8668a43abf5adcbabdf12d0ee5b1f570114262b`；R3包34项/113.18秒、368/283身份及真实自身模板105.42秒approve，独立本地终核通过。自己的双OS CI42540516079七必要步骤成功；独立00:48:33.728775 UTC核远端同SHA，首次代理407与直连超时保留。[记录](delivery/2026-11-09-trusted-verification.md)。
- CR3b内部执行已精确交付`6826047031aebddb7eb6c5fcf43cfe91ebb45ada`（27文件），自己的[双OS CI42545445322](https://github.com/626619403/Ergora/actions/runs/42545445322)七必要步骤全部成功；独立2026-11-09 01:38:46.457071 UTC核远端同SHA。22项原生、两组legacy各9项（五verify重复）、369/283身份及自身真实模板205.12秒approve分别保留原件；六项实证finding已关闭。[执行记录](delivery/2026-11-09-composition-review-execution.md)／[独立终结](delivery/2026-11-09-composition-review-execution-review.md)。
- CR3c有限单叶公开入口已精确交付`8948335ee2b2737bd8cc53e5c33f1fdd2f35ea94`（22文件）；自己的[双OS CI42548357813](https://github.com/626619403/Ergora/actions/runs/42548357813)七必要步骤成功，独立最终02:14:14.105685 UTC经明确HTTPS读取核远端同SHA。最终安装包134 passed/424.33秒、369/283身份、两v2加v1实际公开CLI/Temporal各六阶段与历史重放、自身模板119.66秒approve及新独立两轴通过。[本片记录](delivery/2026-11-09-composition-public-runtime.md)／[独立终结](delivery/2026-11-09-composition-public-runtime-review.md)。多成员/依赖输出仍明确拒绝。
- CR4[服务生命周期](delivery/2026-11-09-composition-lifecycle.md)基线8948335：真实Supervisor旧包旅程发现C1取消路径误用legacy身份，旧包2红/1绿与真实拒绝已留证；单行修复及三参数回归已实现，新包369/283身份通过，新包50项/320.19秒、真实四任务Supervisor旅程428.35秒/87产物/原claim及104观察进程清理通过，真实自身模板116.20秒approve及完整分页通过；新独立本地两轴通过、C1关闭/E1实证处置、8文档/91链接/75 parser通过，已精确交付`cee213a581895d491c1cd41b5fe79b23bfd09b59`（16文件），自己的[双OS CI42551052990](https://github.com/626619403/Ergora/actions/runs/42551052990)七必要步骤成功，独立02:41:50.465610 UTC明确HTTPS核远端同SHA。下一片联合备份恢复另记，不沿用此CI替代新候选。

## 下一可执行项

1. 当前[CR5研究HTTP回归信号](delivery/2026-11-09-research-deadline-regression.md)：原a4cc自己的CI42557137619最终失败，Windows成功抓取后2.281秒超过测试1.8秒阈值；原失败保留。最终父端固定时钟/真实响应头started精确预算与release前重定向事实检查已通过：11passed/1skip、延迟探针2passed、三个实际mutant均红、369/283身份保持；[新独立两轴复核](delivery/2026-11-09-research-deadline-regression-review.md)通过、CR5-1关闭。4538f4e精确8文件普通交付，自己的CI42559480219双OS七必要步骤成功；独立04:14:59.894943 UTC明确HTTPS远端同完整SHA。
2. [AC3c.4联合备份/同路径恢复](delivery/2026-11-09-composition-recovery.md)R2离线原控制+tar恢复/1,992项/五库/32Git及R4在线44.47秒/四原run/history/replay与scanner保持通过；自身模板首审166.23秒发现home限定问题，修后96.92秒approve；独立本地两轴通过、AR-1/AR-2关闭，10文档/208链接/79 parser通过。a4cc0b2普通推送/16对象及03:50:16 UTC明确HTTPS远端身份通过；原CI七必要步骤六成功一失败，不能记精确交付门禁通过，CR5结果不替代其原身份。
3. CR3c自己的CI/远端已完成；后片普通推送仍核自己的必要CI，不取消前片在途CI，不沿用旧身份。
4. [AC4.1必需并行审查](delivery/2026-11-09-parallel-reviews.md)已精确交付 `f9f4fc01546aa065f2fe32294a28c31387b2cf56`（29文件）；自己的[双OS CI42563729227](https://github.com/626619403/Ergora/actions/runs/42563729227)七必要步骤全部成功，独立2026-11-09 05:02:58.894557 UTC明确HTTPS核远端同SHA。[新独立终结](delivery/2026-11-09-parallel-reviews-review.md)保留原API限流及分页限制。[AC4.2a版本化审查职责](delivery/2026-11-09-review-requirements.md)已精确5580c8c交付，自己的CI42566831850双OS七必要步骤及独立05:37:09.274699 UTC HTTPS远端核验通过。[AC4.2b可信建议运行](delivery/2026-11-09-advisory-runtime.md)：R3包191项/四实际旅程与370/283身份通过，模型复审再发现ADV-2单成员汇合遗漏；原包两红/一绿复现、最小版本限定修复及三源码回归通过，R4包370/283、初轮192通过/两fixture失败后受影响4项通过、四新旅程429.34秒及新旧history通过，自身模板275.01秒approve，新独立完整35文件Spec/Standards通过，两finding关闭；已普通推送`91b09683aac9481d07a6cd1d2ea8da9777b25563`（35文件），自己的[CI42574624398](https://github.com/626619403/Ergora/actions/runs/42574624398)双OS七必要步骤成功，独立06:56:50.878067 UTC明确HTTPS核远端同完整SHA。[AC4.3a端口合同](delivery/2026-11-09-review-dag-contract.md)已完成三种关系与来源/版本/预算/恢复设计，新独立Spec/Standards门禁通过、DG-1/2消歧关闭；已普通推送`e9b682c4be4f19aa11aca4717a7f6d86050278ed`（7文档），独立07:09:15.760037 UTC核精确对象/102链接、Markdown路径过滤及明确HTTPS远端同SHA。当前[AC4.3b只读DAG运行](delivery/2026-11-09-review-dag-runtime.md)R2包372/283身份、十一组259项/604.60秒、额外3项原协议/memo恢复、架构登记修后11项、四实际旅程464.97秒及新旧history/128进程采样清理通过；RD-1原包两红保留，修后安装回归及独立源码复核通过。真实自身首审283.54秒request-changes要求补证，完整所有者/最终验收补齐后357.75秒approve；独立28条原请求/回执/claim与126产物核验通过、RD-1关闭，新独立最终34文件Spec/Standards通过、零本地阻塞，待普通提交/自己的CI/明确HTTPS远端终核。其后接执行者分配、三模板、AC5页面及AC6旅程。
5. 继续[总实施计划](plans/2026-11-01-all-in-one.md#5-执行节点及进度登记)剩余F6–F10、G1与按实际需要接入的D/X项；公共发行PUB1仍含维护者许可证选择。

AC4.2a 已精确交付 `5580c8ca154af3b58bd546315f0ec4812bd5c4b3`（23文件）：自己的 [CI42566831850](https://github.com/626619403/Ergora/actions/runs/42566831850) 双OS七必要步骤成功，独立2026-11-09 05:37:09.274699 UTC明确HTTPS核远端同SHA。当前 [AC4.2b 可信建议运行](delivery/2026-11-09-advisory-runtime.md) R2包188项/370与283身份、四原run旅程及九份新旧历史重放通过；自身Claude因上游400失败，Codex真实模板提出ADV-1（共同非法结果摘要被接受），独立14例复现成立。最小严格摘要修复与R3包191项/四新旅程通过；R3真实模板206.15秒仍request-changes，发现ADV-2单成员绕过新图显式汇合，原R3两红/一绿复现。最小graph v1快捷路径限定、三源码回归通过，R4包370/283、原八组192通过/两helper错误保留且修后受影响4项通过，四新旅程429.34秒/129进程清理和新旧九history通过；最终自身模板275.01秒approve，同片独立完整35文件两轴通过、两finding关闭；已普通推送`91b09683aac9481d07a6cd1d2ea8da9777b25563`（35文件），自己的CI42574624398双OS七必要步骤及独立06:56:50.878067 UTC明确HTTPS即时远端核验通过，各原失败与修后证据分别保持。建议意见、执行失败和清理未知保持不同语义。AC2c已做带/不带非空system的有界对照，均为同一上游400，暂无生产adapter补丁依据，继续已授权Codex回退；下一实施AC4.3b串行端口运行，再接执行者分配，不反复登录或放宽原工具权限。

## 持续执行与验收规则

- 用户已授权睡眠期间沿计划持续推进，完成可独立工作；不为每个子节点重复确认。每完成一节点更新本片交付记录和本文件当前检查点，具体日志保留在所属记录，不在本文件反复追加历史段落。
- 每个完整实现切片使用新的fresh-context独立审查者，提供原始要求、固定基线、tracked/untracked差异和实际验证；实证finding修复或有证据处置后复核。每个大节点同时检查结构、复用、冗余test/CI与实际性能。
- 每个大项用Ergora自己的审查模板实际启动Agent并保留精确输入、后端、原回执与限制；补充独立审查。优先不同执行/审查后端；Claude不可用时用户已授权ChatGPT/Codex回退，保留失败及理由，不冒称独立模型错误或双后端成功。
- API凭据继续引用外部环境变量；用户给定ChatGPT变量名`LINGZHI_API_KEY`。不把值写入定义、报告、模板或仓库。长期配置/数据/产物存home下持久目录，禁止依赖`/tmp`或`~/project/tmp`。
- 保留六阶段、原candidate/approval/memo/attempt-before-send/未知恢复、固定版本与283冻结文件身份。复用原Temporal调度、进程monitor和证据所有者，不建立第二套正式调度/账本。
- 祖先Skill/上下文完整继承并读取；MCP资源累加不扩大工具授权。子权限不越父模板；追加权限需父子共同修订，旧修订保持。容量不足拒绝，不截断后宣称完整。
- 当前容器是已接受的可信项目执行边界；不要求宿主权限，不把只读配置或MCP工具限制称为OS隔离。权限、平台与外部服务受限的未验范围明确列出，不阻断其他工作。
- 每片普通提交/推送并核远端精确身份，完成必要检查；不能用另一个候选的CI代替。公开内容不含密钥、个人环境状态或验收缓存。用户要求整个授权任务完成后推送GitHub；最终交接须自包含并说明交互与使用方式。

## 状态与设计来源

|范围|状态与权威记录|
|---|---|
|S0–S10初始工具、三模板、RSI、安装/手册、Windows|已交付；[原完整历史](PLAN-history-2026-11-09.md)、[Windows记录](delivery/2026-11-01-windows.md)|
|M1/M2、A0–A2、R1–R8主线与架构基础|已交付；[总计划](plans/2026-11-01-all-in-one.md)、[当前架构](architecture/current.md)|
|F1–F5及G0项目/安装/正式任务/控制台/证据/新用户旅程|已交付；各子片身份/验证见总计划链接；不等于后续新组合功能已交付|
|AC0/0b、AC1/2、AC3a/d/b、AC3c.1/.2与CR1|已精确交付；[AC计划](plans/2026-11-08-agent-composition.md)|
|CR2a/CR2b、CR3a/b/c、CR4已精确终结，AC3c.4恢复在途|见上方当前检查点及[运行桥总记录](delivery/2026-11-09-composition-runtime.md)；有限单只读review叶v2 start/status已交付，CR4修正并验公开取消路径|
|AC4–6、F6剩余编辑器、F7工单、F8 harness、F9训练、F10持续改进|待相应实现/验收；不能把已有适配/参考发行当完整新入口|
|更深MCP/A2A/隔离/搜索/互操作、团队/集群与公开发行|按总计划D1–D5/X1–X2/PUB1记录；不是本次已实现声明|

[调研与设计决策及逐日完整历史](PLAN-history-2026-11-09.md)保留原始失败、精确来源和限制；旧文本中“当前”“下一项”仅代表当时快照。恢复入口整理已由[新独立文档审查](delivery/2026-11-09-plan-continuity-review.md)通过：旧480行完整保留、165链接/3锚点有效；只做文档核查，没有借此增加应用测试。最新状态以本文件和当前切片记录为准。
