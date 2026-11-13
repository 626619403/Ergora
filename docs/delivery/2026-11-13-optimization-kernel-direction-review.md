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

## 精确发布补核：41dd5aa3

同一独立评审者获同片后续授权，仅作离线发布补核。候选为 `41dd5aa30f589b5c27a1cc3f09db59d66005a40f`，唯一 parent 为 `d683c018344fb604be115a3ed2a02bd9d50d4eff`，tree 为 `3e9b538bc88c2896f28329dfb570f90280a418b3`，分支 `refactor/architecture-foundations`。补核时 HEAD 等于候选；工作树已有 B2h 后续终核记账及未提交 U3 文档，全部产品身份与链接检查因此只取本候选 Git 树。

最终 r4 manifest 共 17 文件，SHA-256 为 `43ba27003f21f50f0d8640a794259a7aa69e02da2cd8b0fbcc3559fa0405a748`。已逐项核准基线至候选的完整文件集、Git blob 字节／长度／SHA-256、object ID、r4 保存原件及 ready 记录的 staged object，全部一致；原 commit 对象摘要、parent／tree 也一致。提交内本报告为 6,320B，SHA-256 `dcd05113bc65b13d443527b9dc15d0e93dc6a129d58e7e0cb13e0b415aac69a7`，等于原审查与 ready 身份。r3→r4 已完整读差异：增加原报告、更新验收／B2h 状态并记录 U3 下一步，不改变五产品／测试或公开证据投影。

从候选 Git 树重新核准全部 551 产品与原构建源／wheel／installed 字节一致；wheel SHA-256 仍为 `34e6b375c8771fa67bb1b02a71070f289ec72d5b0c99badac3afd28373fee208`。559 wheel 文件、两份 RECORD、564 行安装记录、283 冻结文件、6 个构建 overlay 与当前 README metadata 均保持。候选内 13 份 Markdown 的本地链接检查覆盖 289 个目标／65 个锚点，无缺失；基线至候选的 `git diff --check` 通过。

原 commit 回执退出 0、17 文件；push 回执退出 0，实际 argv 为普通 `HEAD:refs/heads/refactor/architecture-foundations`，没有 force，回执记录 d683c01→41dd5aa。作者随后 SSH `ls-remote` 退出 0，完整 stdout 精确为候选 SHA、tab、该分支完整 Ref 和换行。由此核准普通提交／推送、精确 Git 身份及作者 SSH Ref 原件；本次未发起独立网络探测，不能称为独立联网核准。私有 `independent-reviewer-r1/publication-r1.json` 的 SHA-256 为 `f44030314c75cadbd99641a85dec35b94abcab32fc2cc3207ff11e835a9cb2db`。

需求符合性／可维护性通过、SP1 关闭与开放 0／0 保持。上文普通发布及精确身份的待做项由本补核关闭；**41dd5aa 本候选自己的完整 CI 及相应独立终核仍开放**，不借已另行终核的 B2h CI 关闭。没有重新安装、运行 suite、调用模型、联网或检查 U3 安装实施；真实 GPU／原生完整嵌套等未验范围保持。本追加章节尚未提交，不属于 41dd5aa 已发布的报告字节。


## 本候选 CI 终核：43459951488

同一独立评审者获本片终核授权，只读核对已发布候选 `41dd5aa30f589b5c27a1cc3f09db59d66005a40f` 的 Git 树和保存的官方 CI 原件。完整读取候选 `.github/workflows/portability.yml`、`scripts/ci/linux-groups.json`、`scripts/ci/run.py` 与 `scripts/ci/pytest_phases.py`，记录四份 Git blob／字节／SHA-256。六 Linux 组分别有 12／13／13／14／12／11 个文件，共 75 个唯一配置路径，全部存在于候选树；矩阵为 Ubuntu／Python 3.11 的六组及 Windows／Python 3.12 的 all。plan 保持 5 分钟、native 保持 20 分钟和 fail-fast:false；安装版选择、reference 附加范围、分组完整性拒绝与观测出口均沿原 owner，未执行 collection 或 suite。

独立解析 19 份原正文及其 HTTP 200 回执（actions 一份、UI job batch 一份、run 五份、job 十二份），逐项重算原始 bytes／SHA-256、URL／final URL 和采样时间。Actions 原 embedded JSON 的同一行直接绑定 run `43459951488`、Portability、候选 workflow 路径、完整分支及完整提交链接，不依赖短 SHA 或作者发现摘要。初始 UI batch 的 totalCount=8／hasMore=false，提供 plan、六 Linux 组及 Windows 的精确 job 映射；其当时 in_progress 状态保持为历史，不作最终状态。

最终 `ci-run-html-r5` 于 `2026-11-13T16:23:58.031801Z` 保存，官方 [run 43459951488](https://github.com/626619403/Ergora/actions/runs/43459951488) 的 Workflow run summary 明确为 **Success**，全文 213,240B，SHA-256 `254c5d3073036e557f3babeabc392096bf3ecff1d65af229683efac9f870e95b`。最终 Windows 原页 `ci-job-132003979023-html-r4` 为 160,049B，SHA-256 `55ee038fbdd74791c32b713da7ad6c36aa920bcff484dccac66ec5042bdd2cb1`。最终 run 的实际 job 链接及各 job 原页／回执与以下八项一致：

| job | 矩阵范围 | 原页版本 | 回归秒数 |
| --- | --- | --- | ---: |
| 132003886500 | plan | r1 | — |
| 132003978875 | Linux group 0 | r2 | 278 |
| 132003978769 | Linux group 1 | r1 | 193 |
| 132003978867 | Linux group 2 | r1 | 218 |
| 132003978767 | Linux group 3 | r1 | 159 |
| 132003978870 | Linux group 4 | r1 | 163 |
| 132003978832 | Linux group 5 | r1 | 178 |
| 132003979023 | Windows all | r4 | 672 |

按候选 workflow 逐项独立核准 **30 个必要步骤**：plan 的显式分组 1 项，六 Linux 的 build/install、packaged reference identity、native regression、upload 各 4 项，以及 Windows 同四项加 PS5.1 installer／upgrade 共 5 项。全部原 `check-step` 均为 success，具 `data-job-completed`、非在途标志、有效有序起止时间；每条必要步骤的日志定位精确含完整候选 SHA、job ID 和 step number。七组上传全部成功；Windows PS5.1 安装升级为 41 秒。八 job 的 Complete job、checkout／setup 与 post 步骤同样核准成功；Linux 专属 Windows installer 的 skipped 符合原条件，不计作必要步骤成功。

前四 run 原页仍为 In progress；Windows r1／r2 的 regression 与后续步骤未完成，r3 虽已显示 regression success，但 installer 在途、upload 待做且无 job-completed。三份早期作者终态摘要 required_steps_passed=false 和对应原件全部保持，未追认早期样本成功。作者最终 `ci-terminal-r4.json` 的 SHA-256 `1277a1dcea15ad58d2163d621aa3f92f5fd83cc4372ea81759a683891cc29157` 与本次独立结论一致；本次没有执行作者 parser 或采信其 passed 代替原件。

私有独立审计为 `.ergora/checks/optimization-kernel-direction/independent-reviewer-r1/ci-independent-r1.json`，109,799B，SHA-256 `5c473669d1baa37224ee53096f2de8a0025f05268896c9e00ca9aa353771dbcc`，保留逐样本回执身份、逐步骤属性及最终 8／30 结果。**需求符合性：通过。可维护性：通过。开放 finding 仍为 0／0，SP1 保持关闭。** 本候选自己的完整 CI 及相应独立终核待做项由本追加关闭，结合上节已核普通发布／精确 Git 与作者 Ref 原件，本片精确交付验收终结。

本结论只覆盖已保存官方 HTML 状态和原件身份；没有独立联网、成功 REST、全量 raw CI 日志或上传 artifact 内容核验，也没有重装、重跑 suite／collection、模型调用或 GPU／原生实验。未检验并行 U3 的实际安装替换或 B3 实验；真实 oracle／梯度／wrapper／训练／服务收益、checkpoint／恢复及 C2 全部内部会话／权限／总预算／后代停止等原未验范围保持。追加前 8,956B 报告（SHA-256 `f9e1cb85cb24b062d67ae9e1eaaca8376f0162cbaa7170f69b7a4b29d59d29e6`）逐字保持；本追加尚未提交，不属于候选内已发布报告字节。
