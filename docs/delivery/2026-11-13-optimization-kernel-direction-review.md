# D2-B2i 独立 kernel 方向审查

审查者：Codex fresh-context reviewer `/root/kernel_direction_review`。日期：2026-11-14（Asia/Shanghai）。按项目 AGENTS、maintainable-project-delivery 及 independent-review 双轴要求，先读原始需求、实际变更与邻近消费者，再读作者叙述；未继承实施会话。

基线与审查期间 HEAD 均为 `d683c018344fb604be115a3ed2a02bd9d50d4eff`，分支 `refactor/architecture-foundations`。核准 r1 的 15 文件快照（manifest SHA-256 `4947f8f242fd76ceafb4d410a4135276b060a5e5ec0a13cc5d0b775443eb69f9`），并逐差读 r2、r3。最终判词绑定 r3 的全部 16 文件，manifest SHA-256 `436c76b042dfafbee47523bdadc59fa926aee1f4a499ba66aeb057e1a438d517`；五产品／测试及 README 从 r1 保持。范围包含新增三文件、catalog、原 preset 参数测试、README／两手册、本片及专家计划／交付、公开证据投影和 B2h 发布记账；不将并行后续状态写入混为该快照。

**需求符合性：通过本片只读资料与手动交接的本地出口。** `optimization-kernel` 指向 `ergora-opt-kernel-proposal@1.0.0`，精确复用原 analysis／measurement v2 与四位 v2 专家，四叶形状正确。每叶保留完整结构祖先资料及自身 Skill／附件；权限均无 write、shell、network，依赖边不增加权限或自动执行。kernel 接两份、measurement 接三份完整原结果的手动合同与实际交接一致。真实 operation、shape／stride、数值、所需梯度、wrapper、公平 compiled 基线、条件 Amdahl、独立 oracle 和局部／整体差异均有明确约束。原生准入条件没有冒称已执行能力。

**可维护性：通过。** 新配置沿原 `workflow_definitions` 所有者供 CLI 与 HTTP 消费，不加 Agent 类、执行分派、依赖、搜索循环或候选账本。新根只持有方向资料及已有精确组合接口，专家／后端不被复制或改写；原 runner、native campaign、独立评价与项目采用保持各自所有者。测试仅扩展已有方向合同，验证新增根安装、四叶、完整 context 和权限，不复制一套测试框架。开放需求／可维护性 finding 为 **0／0**。

本轮发现并关闭 **SP1／P3（来源定位准确性）**。r2 的 `docs/delivery/evidence/2026-11-13-optimization-kernel-direction.json:172` 及私有研究 manifest:92，将 13,068B、SHA-256 `e8eca327…` 的 Python judge 保存快照定位为另一份 `docs/design/v1-launch.md` 正文。R1 saved_files 证明保存字节，不能证明它们是该文档字节；后续按 URL 复核会落到不同文件。最小修正已把本片该项改为固定研究 repo tree，并明确 tree 仅定位同一 snapshot、精确字节身份来自 R1 索引，不虚构新 HTTP 或具体源码路径。r3 复核仅该来源元数据及交付说明变化，21 正文、产品、wheel、输入和结果均保持；旧 manifest 与旧投影 `83f187d1…` 原字节已归档，修正后公开投影 SHA-256 为 `789b6b5e5ba3c311163958b0afbc125729c5db1b04cfe8d545a0c3a0214a45f9`。SP1 关闭，无其他已证实 finding。

实际检查均为离线独立读取／重算，没有执行作者的安装、模型或投影脚本，也未重跑 suite：

- 21 份研究正文共 920,972B：10 份逐项匹配 R1 原 saved_files，11 份匹配原 X2 正文、HTTP 200 回执及索引。直接核 KDA 流程／许可、Forge 原 pin／Claude／黑盒政策与 judge、KernelAgent 测试／worker／Fuser、GEAK 实际 kernel_lane 调用与结构结果、AKG 默认截断／会话及 robust-kbench evaluator 原文。固定研究快照与当前安装／支持明确分开；新增研究请求为 0。
- 548 个旧产品除 catalog 字节保持，22 个旧 catalog 项保持；7 个定义与 6 个精确引用摘要核准。551 产品在工作树、构建源、wheel、installed 四路逐字一致；559 wheel 文件／RECORD、564 行安装 RECORD、283 冻结文件、6 个构建 overlay 和当前 README metadata 均核准，noneditable。wheel SHA-256 为 `34e6b375c8771fa67bb1b02a71070f289ec72d5b0c99badac3afd28373fee208`。
- 原安装版 preset suite stdout 明确为 30 passed／119.64 秒，controller 121.164 秒、原上限 600 秒。已核环境、命令、当前测试字节与原结果，未把它称为全 suite 或七组 collection。
- 四真实 task-MCP 原 run、不同 thread、完整输入树摘要、冻结 manifest、scope、实际 stdin、native stream／receipt／result 均相符。23 份资源共 66,552B，23 次 read 全部连续 UTF-8 至 `next_offset:null`，与当前定义完整原字节一致；kernel 两份及 measurement 三份原 JSON 在 task／prompt／实际 stdin 中逐字完整，结果 SHA 链保持。四次成功、无重试，240／290 秒原调用上限保持。四份回复均全文阅读；synthetic 的错误 eager 4×、公平 compiled 2×、条件 Amdahl 1.25×、wrapper 慢 20% 与真实未知分开，measurement 保留 `request-changes`。全为显式 Codex 调用，不称异后端复验。
- 自身原结构模板 `afc02523a0ee484eb8b12877fd42412e` 为 29.578 秒、approve；五原文件全文 49,861B 及三份祖先／自身资源在实际 prompt／stdin 完整，结果身份一致。其范围只是 text-only 结构审查。最终公开投影逐字段与原件相符；r3 的 12 份 Markdown 覆盖 288 个本地目标／65 个锚点，无缺失，`git diff --check` 通过。

私有独立审计保存于本片 `independent-reviewer-r1/`，包括 source-identity、package-identity、self-review、real-leaves、input-and-projection 与 final-r3；检查证明实际交付字节与已记录行为，不证明模型理解或普遍专业能力。一次调用后 `/proc` 观察只保留其限定范围，不升级为全程后代清理或 OS 隔离。

普通发布、精确 Git／远端身份、本候选自己的完整 CI 及相应独立终核仍开放。r3 中 B2h 自己的 CI 在途，由其原评审另核；不借 B2g／B2h 结果关闭本片。真实原生工具／编译／GPU、独立数值与梯度、wrapper／训练／服务质量与收益、checkpoint／恢复，以及全部内部会话父材料、权限、总预算和后代停止均未验，继续留 B3／C2。研究、synthetic fixture、提案和本报告均不授予这些通过状态。
