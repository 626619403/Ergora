# AC4.4 内置领域组合独立审查

当前结论：**R2 候选本地 Spec / Standards 两轴与证据终核通过，DP-S1 已关闭，开放 finding 0**。修后自身模型复审及最终本地范围已核；本候选自己的必要 CI / 明确 HTTPS 远端身份仍待 P5，不据此标记整片精确交付完成。

审查者 `/root/domain_presets_review`，以全新上下文开始；依 AIHERO 索引应用 code-review、maintainable-project-delivery 及 codebase-design。另启全新上下文的 `spec`、`standards` 两名子审，分别检查规格和规范，再独立复核实证问题。本记录与实现者的自身模型审查分别记账。

固定基线和初审 HEAD 均为 `d8fc8ef2eee64b51a9eb5fa1925734e475965785`。`git diff d8fc8ef2eee64b51a9eb5fa1925734e475965785...HEAD` 和对应提交列表均为空；本次明确审查工作树的 **76 文件**，包括新文件正文。初审 `review-scope.json` SHA256 为 `9cf0efe3ad164bbef4bb12bf3351c2411591c0fd8578c19f2f14a15b4878bda7`，`review-scope.diff` 为 `d64a45f3e56f02491eb90b12532126078aa002d0f8a4e40fcb07de23e6160922`；逐文件当前摘要全部匹配。完整范围与原始要求在本片私有 checks 中保留。

原始要求、[总组合计划](../plans/2026-11-08-agent-composition.md)、[工作运行合同](../plans/2026-11-09-work-agent-contract.md)、[本片计划](../plans/2026-11-09-domain-presets.md)、AGENTS、当前架构与 ADR0002/0004/0005 为审查依据；作者的[交付记录](2026-11-09-domain-presets.md)只作为实际证据索引。

## Standards

**初审通过，所查范围内硬规范违规 0，具有实际后果证据的 possible smell 0。**

生产修改仅为原 `workflow_definitions` 的随包目录与顺序导入用例及原 CLI 分派；定义当前准入、完整资源摘要与不可覆盖发布仍由原 Agent/Workflow 库负责。未新增调度器、账本、后端厂商分支、依赖或 CI。13 份专家均有实际默认图消费者，11 份子工作流通过原 Interface 组合；实例后端仍交原覆盖与多样性政策选择。

六项新增测试消费实际随包数据和原 template units，检查导入顺序、同身份重试、完整祖先材料、脱离源定义库后的 manifest、离线 CLI 与正式创建。它们能暴露旧通用夹具没有覆盖的发行数据失配；未发现可据证删除的重复测试或上游重复防御。原预算与祖先权限检查继续由现有所有者执行，未见新增性能承诺。

## Spec

**初审要求修正：1 项 P2。** 其余所查默认组合未发现范围蔓延；治理保持两个原并行 unit，大型变更保持 contract → server/client → integration-tests 的传递依赖，开发总审查覆盖全部 required 分支。训练仅提供完整静态组合与显式只读提案叶，原 runner/gate 与 F9 分开。

**DP-S1 / P2：三份审查子模板无法单独作为正式 review。** [总计划](../plans/2026-11-08-agent-composition.md)第 30 行要求“结构/正确性/冗余检查子模板可单用或并行组合”，[使用手册](../WORKFLOW_DEFINITIONS.md)第 28 行也说明三份子模板可单独使用。但 [结构审查](../../src/ergora/data/presets/workflows/ergora-structure-review/workflow.json)、[正确性审查](../../src/ergora/data/presets/workflows/ergora-correctness-review/workflow.json)、[测试价值审查](../../src/ergora/data/presets/workflows/ergora-test-value-review/workflow.json)在第 32 行直接把 terminal 输出指向 Agent，未提供 schema v2 正式审查所需的显式 all-join。

触发：将任一子模板冻结为独立根并选择 `review_instance=root`。主审使用保留 R1 安装包的原 `tasks.preview` 与 `execution_input.require_submission` 核验：三份模板在 v3 下均可预览，但提交形状被拒绝，错误为 `Parallel composition review requires an explicit all-join covering every reviewer leaf`；`dag-v1` 则在预览时被 `Review DAG terminal output must project an explicit all-join` 拒绝。共用 `ergora-delivery-review` 的两模式对照均通过。没有发请求或启动服务。公开 `run-input` 单叶调用仍可用，此 finding 仅涉及承诺的正式模板单用。

后果：用户不能直接选择某一领域审查子模板作为唯一正式审查。最小修正是在上述三份定义内各加入单成员 gather all-join、输出指向 gather，并沿父引用更新摘要；保留现有运行 gate。应以原包反例及修后公开准入检查验证，不扩展测量提案或修改运行合同。当前状态：**R2 已修复，同片复核关闭**，见下文；原问题与反例保持。

## R2 修正复核

三份子模板各增加单成员 gather，并把输出指向 gather；共用总审查及两开发根仅更新固定引用摘要。主审和 Spec 子审独立逐字比较 R1/R2 生产包，差异恰为这六份 `workflow.json`；Agent、提示、Skill、measurement 与全部运行 gate 保持。新增三参数回归经原 `tasks.preview` 和 `execution_input.require_submission` 检查 v3 / dag-v1；旧 R1 包 **3 failed / 5.45 秒** 的原件保留。

主审独立 R2 安装包套件 **9 passed / 26.22 秒**，包含三子模板的两协议公开准入、原完整祖先和两原 v5 创建检查；Spec 子审另以原 validator 核 **6 次子模板准入 / 2 次总审查对照**均通过，并重核三领域完整 manifest/input 与父引用。R2 source/wheel/noneditable install **434 文件**逐字相同，**283 冻结文件**和 d8 基线一致；wheel SHA256 `4f827c0d70e24299c5c2d8a65d635f3dc5d3130465d69cf3c71d2ca3fd37a66d`。

修后五组安装回归原日志已核终态：**204 passed / 1 skipped / 177.79 秒**，跳过仍仅为 Linux 无法执行真实 Windows junction。首次命令误写已有测试路径而零收集，原命令错误保留；纠正为原 `test_architecture_boundaries.py` 后才取得本组结果，未改测试或把首命令记成功。主审未重复这五组全量执行。

Standards 子审复核六份定义及新增测试：单成员 join 满足原正式合同，不增加模型或正式 job；新回归暴露此前静态预览成功而正式拒绝的具体缺口，未增加镜像断言或修改运行门禁。R2 增量硬违规 0、具有证据的 possible smell 0。**DP-S1 关闭，修后未发现新增 Spec finding。**

## 检查与限制

主审独立检查：R1 source/wheel/noneditable install **434 文件**逐字一致，wheel SHA256 `b11662bb0772c12b41a52f79db538778fdcdfc8b06b34b816115b150a0958980`，基线 d8 的 **283 冻结文件**与原 `reference.verify` 通过；安装包新增套件 **6 passed / 20.62 秒**。安装包隔离 CLI 按手册连续导入三领域并全部重试，得到 **13 Agent / 11 Workflow** 且身份保持，列表未创建 State，耗时 5.716 秒。DP-S1 的 **6 次拒绝 / 2 次通过对照**另存原件。

Spec 子审还独立核验三套移除源库后的 manifest/input 与两开发域 v5 信封、原 unit/传递依赖。原作者 6 项源码、141 项受影响回归和 201 passed/1 Windows junction 平台 skip 的安装回归日志已读；后两组未由主审重复运行。48 文档/281 链接/94 parser 为静态检查，不能代表服务或模型验收。

私有原件位于 `.ergora/checks/ac4-presets/independent/`：`review-initial.md`、`spec.md`、`standards.md`、`package-check.json`、`presets-tests.log`、`combined-cli.json`、`standalone-public-check.json`，以及修后 `package-check-r2.json`、`presets-tests-r2.log`。初审及 R1 原红均保留。

自身模板 R1 单叶调用的原件已由 Standards 子审独立核验，`self-review-audit.json` 的 27 项检查通过：完整冻结 input/manifest、原结果/只读持久记录一致，12 页逐字重组 **352511 字节**，80 份内嵌源码及 5 份验证附件匹配原身份。approve 与作者外层 **123.486 秒**计时分别保留；持久 run 时间差为 123.096213 秒。当前七份源码差异恰为六份定义与测试，未把旧模型意见当成修正后验收，也不由单叶调用推导正式审查准入或模型质量。

修后真实 R2 调用 `5cc709de7a404774b9a6e66b34cc44f3` 的原件由同一 Standards 子审另做 **38 项**核验，记录在 `self-review-r2-audit.json`：冻结 input/manifest、原生最终消息/result/protocol 及只读持久记录一致，**14 页连续重组 381146 字节**，80 份内嵌源码全部匹配修正后实际源码，并绑定上述 R2 wheel。approve 与作者外层 **146.535740 秒**计时分别保留；持久 run 跨度为 146.132482 秒。8 份当前验证附件和原 R1 静态报告附件按各自原身份核对，后续状态文档另列差异，没有把后刷的报告替换进旧调用。

主审另将 **8 份公开脱敏 JSON / 91592 字节**逐一与私有原件比对，30 项检查通过：R1/R2 输入和读取身份一致，公开意见与原生结果解析后逐字相等，原 native 结果 SHA 与公开重新排版文件 SHA 明确区分；[R2 包记录](evidence/2026-11-09-domain-presets-package-r2.json)及[DP-S1 原红/修正](evidence/2026-11-09-domain-presets-dp-s1.json)中的全部日志摘要匹配。公开证据不含 home/tmp 绝对路径；没有凭据或个人认证状态被引入默认定义。

## 最终本地范围

2026-11-09 **11:00:09.570514 UTC** 主审逐项核 `acceptance-scope.json/.diff`：**86 文件全部匹配，tracked/new 范围无遗漏**。两原件 SHA256 分别为 `cd0fe7bb35c31924ea29791024a5e1b15fa645b0fc257a86cb97fcf0ae152b35` / `e10d1944067a06a4209796537489cb7074660c0cd099cb9f02a5301db5a1406b`，详见 `independent/final-local-check.json`。此前 R2 的 85 文件快照 SHA 为 `14737ccf761f58571b1930e2c16d85fbdab2ea30a05815f1c07230b6af82fdad` / `234b8bf0d75741eecd7bd2bc7d74fc0a67f9775ce94e788224732a2a2a7843c1`，原件保留。

85→86 的新增项仅为前片 `work-example-regression` 的 d8 独立交付追加；另外三份变更是 PLAN、原工作运行交付和总组合计划的状态更新，未改变本片源码/测试/data。该前片追加只记独立核验者的结论，不重做或借用其 CI。作者最终静态记录为 **50 Markdown / 304 链接 / 94 parser** 通过；本报告此次终核追加及其后的 P4/P5 状态记账是审查输出，不触发递归审查或替代固定源/包身份。

本审未安装依赖、改实现、运行模型/服务/GPU、提交或推送；无新的模型质量、性能或 OS 隔离成功声明。**本地审查出口已通过，P5 本候选自己的必要 CI 与明确 HTTPS 远端身份尚待**。前片 d8 测试修正及其 CI 保持原范围，不当作本片新增代码 finding 或本片交付证据。

初审计数：Standards **0 finding**；Spec **1 finding，最高 P2（DP-S1）**。

R2 本地复核：Standards **0 finding**；Spec **0 开放 finding，DP-S1 已关闭**。

## P5 精确交付终核：通过

本节更新上文本地终核时尚待的 P5 状态。独立主审仅读取固定 Git 对象、保留 R2 包/安装目录与官方交付证据，未重新委派源码审查、运行测试/模型/服务、安装、提交或推送，也未取消或重跑 CI。当前 AC5 C1 的 Web、控制台和测试工作树修改全部排除；本节不为后片候选提供验收。

精确候选为 `d7ad71d37a1a3223b0cab3c93cbad1b522320377`，唯一父对象为 `d8fc8ef2eee64b51a9eb5fa1925734e475965785`，提交恰 **86 文件**，与原完整终核范围逐项相符。相对 acceptance 快照的差异仅为 PLAN、本片计划/交付记录和本审查报告四份已授权状态更新；重建快照并比较增量，源码、测试、data 与公开原件未漂移。DP-S1 原反例、R1 模型漏检及修后证据保持。

从候选 Git 对象读取的 **434 个包文件**，与保留 R2 wheel 及原非 editable 安装目录逐字相同；wheel SHA256 仍为 `4f827c0d70e24299c5c2d8a65d635f3dc5d3130465d69cf3c71d2ca3fd37a66d`，**283 个冻结文件**与父对象逐字一致。本次计数为 434，未计入后片新增控制台文件。Portability workflow 也与父对象相同。

独立官方新采样保存后，于 **2026-11-09 11:20:26.338964 UTC** 终核 [本候选 run 42605934103](https://github.com/626619403/Ergora/actions/runs/42605934103) 为 **Success 终态**。完整 job-group 已取尽，run 的完整 commit、workflow、两个实际 job 名称和 `selectedJobId` 相符；七个必要步骤全部 **success**，各有 `job-completed` 标记及精确候选的 check/log URL：

| 官方 job / check | Build and install wheel | Packaged reference identity | Native application regression | Windows PowerShell 5.1 installer and upgrade |
|---|---|---|---|---|
| [Windows 3.12，129121817328](https://github.com/626619403/Ergora/commit/d7ad71d37a1a3223b0cab3c93cbad1b522320377/checks/129121817328) | [success](https://github.com/626619403/Ergora/commit/d7ad71d37a1a3223b0cab3c93cbad1b522320377/checks/129121817328/logs/4) | [success](https://github.com/626619403/Ergora/commit/d7ad71d37a1a3223b0cab3c93cbad1b522320377/checks/129121817328/logs/5) | [success](https://github.com/626619403/Ergora/commit/d7ad71d37a1a3223b0cab3c93cbad1b522320377/checks/129121817328/logs/6) | [success](https://github.com/626619403/Ergora/commit/d7ad71d37a1a3223b0cab3c93cbad1b522320377/checks/129121817328/logs/7) |
| [Ubuntu 3.11，129121817823](https://github.com/626619403/Ergora/commit/d7ad71d37a1a3223b0cab3c93cbad1b522320377/checks/129121817823) | [success](https://github.com/626619403/Ergora/commit/d7ad71d37a1a3223b0cab3c93cbad1b522320377/checks/129121817823/logs/4) | [success](https://github.com/626619403/Ergora/commit/d7ad71d37a1a3223b0cab3c93cbad1b522320377/checks/129121817823/logs/5) | [success](https://github.com/626619403/Ergora/commit/d7ad71d37a1a3223b0cab3c93cbad1b522320377/checks/129121817823/logs/6) | 平台条件不适用 |

**2026-11-09 11:19:33.587839→11:19:35.491672 UTC**，主审在仓库外禁用 system/global Git 配置、清除 Git 环境覆盖并禁用凭据助手，对 `https://github.com/626619403/Ergora.git` 明确执行只读 `ls-remote`。原 trace 确认实际使用 `git remote-https`，无 SSH rewrite；远端 `refs/heads/refactor/architecture-foundations` 返回完整 SHA **`d7ad71d37a1a3223b0cab3c93cbad1b522320377`**，与候选一致。

私有对象比对、允许状态增量、此次官方原页及独立 HTTPS 结果保存在 `independent/commit-closure/`，汇总 `closure-evidence.json` 固定原件身份；没有覆盖作者早先 In progress 采样。**本候选 P5 的对象/保留包、自己的七必要 CI 与明确 HTTPS 远端门禁全部通过，AC4.4 精确交付终结。** 本节后续状态记账不改变原候选身份，也不替代 AC5、AC6 或 F9 的独立验收。

本轮汇总原件 SHA256：`c8aab0797612e45b1853b7fe93881379ddb2e7915df9b514ca45a62267cdb36a`。另只读确认 HTTPS 读取所在目录不属于任何 Git 仓库，原 trace 中 `git-remote-https` 的两个 URL 参数均为上述明确 GitHub HTTPS 地址。
