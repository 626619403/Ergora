# BR1：审查后端说明独立审查

日期：2026-11-15。Reviewer：fresh-context 独立审查 Agent；未继承实现会话。审查固定于分支 `docs/review-backend-guidance`、HEAD／基线 `f00bfdfd15173ceb0e961681679d6d3d62254bed`。只读产品、来源和验收原件；唯一写入为本报告，未安装、运行模型、提交、推送或对外评论。

|审查轴|结论|开放 finding|
|---|---|---|
|需求符合性|approve，限本片文档／配置源码范围|0|
|维护性|approve，限本片文档／配置源码范围|0|

未发现需要修改的实证 finding，无阻断源码问题。本结论不认证安装发行、厂商功能可用性或实际模型效果，也不关闭主控原有的自身模板／发布验收门。

## 需求、范围与身份

原需求是参考 Anthropic 指定 Code Review 文档和文章，把 Codex／Claude Code 等后端差异加入对应审查 Skill，使研究实际进入流程；同时保留已发布定义、旧 manifest、后端中立、权限、运行语义和人工发布边界，不自动调用厂商审查或评论接口。

先读本树合作规则、组件变更协议及原始变更，再对照来源、实际 owner 和作者检查；采用 maintainable-project-delivery 的 independent-review、ergora-codebase-quality 及 writing-for-agents。检查了完整 `scope.json`、`untracked.txt` 和包含新增文件的 `reviewable.patch`。独立核对 patch 为 **43,291B**、SHA256 `7b36de9a43ae41afbc5b75bf44b2c59da84970cd795c071264296c6cf2bef0f0`，12 个当前文件的字节数和 SHA256 均与 scope 相同：

- `docs/TRAINING_REVIEW.md`
- `docs/WORKFLOW_DEFINITIONS.md`
- `docs/delivery/2026-11-15-review-backend-guidance.md`
- `docs/plans/2026-11-15-review-backend-guidance.md`
- `docs/research/2026-11-15-review-backend-guidance.md`
- `src/ergora/data/presets/presets.json`
- `src/ergora/data/presets/workflows/ergora-pretraining-review-v1.0.1/workflow.json`
- `src/ergora/data/presets/workflows/ergora-pretraining-review-v1.0.1/instructions.md`
- `src/ergora/data/presets/workflows/ergora-pretraining-review-v1.0.1/skills/ergora-review-backends/SKILL.md`
- `src/ergora/data/presets/workflows/ergora-posttraining-review-v1.0.1/workflow.json`
- `src/ergora/data/presets/workflows/ergora-posttraining-review-v1.0.1/instructions.md`
- `src/ergora/data/presets/workflows/ergora-posttraining-review-v1.0.1/skills/ergora-review-backends/SKILL.md`

## 需求符合性证据

[共享 Skill](../../src/ergora/data/presets/workflows/ergora-pretraining-review-v1.0.1/skills/ergora-review-backends/SKILL.md)正文已进入两个新根的四叶完整提示，不依赖 reviewer 联网或自行发现研究文档。每领域均为 `root/domain/review`、`root/general/structure/review`、`root/general/correctness/review`、`root/general/test-value/review`；独立调用原 `inspect_manifest`／`inspect_input`，核八份新 prompt 均完整包含根 Skill 正文恰好一次，资源来源仅为 `root`。旧独立通用根及其他开发／优化入口未升级，手册明确说明该边界。

对照保存的官方全文／相关认证与 CI 段落，以及 `sources/index.json`，未发现能力归属或来源误引：

- `CodexBackend.command` 实际使用 `codex exec`，`ClaudeCodeBackend.command` 使用 `claude --print`／JSON；Skill 没有把它们表述为原生 review、插件或托管调用。text-only、task-MCP 及 Claude bare 认证说明与 driver 的现有合同一致。
- Codex CLI `/review` 的 transcript／工作树行为，与 GitHub 云审查发评及独立 GitLab MR beta 分开。GitLab.com environment、自管／Dedicated service account 和 webhook 前提、手动与自动 severity 差别均有官方正文支持；未把 GitHub 接入当作 GitLab 授权。
- Claude 内建 `/code-review`／`/review`、固定公开插件、Actions／GitLab CI、Anthropic 托管服务分别说明。默认报告与 `--fix`／`--comment` 的副作用、GitLab 发评的版本／`glab` 条件、托管服务的 Team／Enterprise／Owner／GitHub App 与独立计费均与来源相符。固定插件 commit／manifest 和实际 command 分开，未以 README 的旧描述覆盖 command 行为。
- 指定三月文章同时保留 research-preview／旧费用与耗时叙述和 GA 更新；研究正确以当前服务文档核可用性与计费，没有把文章估计变为今日保证。托管服务不 build/run、不 push，但会写评论／check、处理自己的旧线程；“不 approve／block”没有被误写成“无平台副作用”。

Skill 要求沿原结果合同报告实际 backend、mode、独立会话、候选身份与覆盖，保留同后端回退原因；把本地 advisory `approve` 和平台 review／批准分开。正文是能力解释与授权边界，没有安装、启用服务、发评或修复代码的执行步骤。

## 维护性与兼容性证据

新增内容归根定义资源，实际复用原祖先继承、完整包和 preset owner，没有新增 runtime 分派或第二套调度。两个可独立分享包保存同一 Skill 的相同字节，长比较仅在研究文档维护；此处封装副本有实际完整包消费者，不是每个叶分别维护矩阵。

独立只读复核得到：

- 基线 **216 个旧 preset 文件**字节／执行位不变；32 个 preset 名称保持，30 个无关 catalog 条目保持。两相关条目仅切换新 root 路径并追加其导入依赖。
- 两个新 workflow 还原 version 并移除新增 Skill 资源后，与旧 definition 完全相等；instructions 字节保持。原图、required／all-join、叶引用、backend、权限和 limits 保持。八叶仍为无写入、无 shell、无 network。
- 新根经原 bundle inspector 核得 pretraining digest `654b5c49875556a31e6982e33a066623106980d9bbc73366d5a45f4eaf4a118a`、posttraining digest `7023d0de86de0c61811b644bea6cd782057e3ee538ceba52c3c98f173b04bbca`；两 Skill 完整目录 digest 同为 `05cf4cbad8ec9a6971b0695c7c48611566bd17e4581e164a8bce5647092cd6f3`。
- 两领域旧 manifest 均通过原 owner 重新检查；各 **24 个旧 object 文件**与其 state 中保留对象的字节／执行位一致，旧 index 映射均仍存在。八份旧 input 与各自 `again-*` 输入的全部文件字节／执行位一致。没有把可追加 index 本身误认作不可变对象。
- `sources/index.json` 的 **24 项**保存原件均独立核过字节数与 SHA256；研究表中的 12 项正文身份与其对应。`git diff --check` 通过。

检查脚本和原件位于 `.ergora/checks/review-backend-guidance/`。已读原 pytest 工具结果（适用领域 preset 测试 **2 passed／8.73 秒**）、docs-check 结果、r1／r2 验收脚本及失败／成功输出。r1 的失败来自把追加后的 index 文件整体当作不可变对象；r2 改核旧 object 与旧映射，修正的是验收口径，产品变更未扩大。作者报告的两项 Skill quick_validate 通过与独立 owner 完整包检查分开看待；本 reviewer 未重跑 pytest 或模型 suite。

## 限制与交接

本审查基于固定保存的官方来源，未重新调用 GitHub API，也未核线上文档后续漂移。CLI 安装／认证、账户套餐、组织设置、实际 host 可达性、新非 editable wheel、新安装／升级旅程、真实后端／原生／插件／CI／托管 review、Ergora 自身模板均未由本片运行；任何质量、训练、分布式或性能主张均不在结论内。

未发现需最小修正的 finding；本范围无需源码修复或 finding 复审。主控仍应按原交付门记录独立审查状态及尚未执行的自身模板／安装／发布检查，不能将本报告的源码 approve 换成这些检查已通过。
