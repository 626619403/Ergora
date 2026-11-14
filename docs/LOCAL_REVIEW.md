# 本地 PR／MR 审查材料

`ergora review` 将精确的本地 Git 变更保存成可以离线读取的完整材料包。它无需 Agent 登录、项目登记、数据库或 Temporal，适合先准备候选与需求，再交给审查者。当前入口负责采集和完整性校验；自动获取 GitHub／GitLab PR／MR、领域组合运行和远端发表意见另见 [实施计划](plans/2026-11-15-domain-review-optimization-quality.md)。

## 准备材料

先按 [安装手册](USAGE.md)安装含此命令的版本，确认 `ergora review --help` 可用。需要 Python 3.11+ 和 Git 2.43+，源仓库必须已经具有所需的完整本地对象；此命令不 fetch。需求文件和可选检查原件是无 NUL 的 UTF-8 文件，保留原换行。

先在持久目录保存原始需求 `request.md`，说明目标、语义不变项和期望检查。调用者、配置和局部规范按实际变更显式选择，命令不会自动推导全部依赖。下面的 `BASE_FULL_SHA` 是目标分支提交，`HEAD_FULL_SHA` 是候选提交，均须为完整小写 ID；`--repository-id` 是操作者声明的身份，例如 `github.com/org/project`，不会从 remote 推导或认证它。

```bash
ergora review prepare /path/to/project \
  --repository-id github.com/org/project \
  --base BASE_FULL_SHA --head HEAD_FULL_SHA \
  --requirements ./request.md \
  --context src/caller.py --context config/training.toml \
  --evidence ./baseline-check.txt --evidence ./candidate-check.txt \
  --directory ./reviews/candidate-01 > ./reviews-receipt.json
```

`--context` 和 `--evidence` 可重复，也可以省略。context 必须是仓库相对的**精确普通文件**，在 base、比较起点或 head 中至少存在一次；目录选择不支持。包自动加入全部变更路径和这些路径的祖先 `AGENTS.md`，读取三种提交中的完整内容。工作区、暂存区和未跟踪文件不参与采集；需求与 evidence 则按上述显式本地文件读取，不能误认成 Git 中的版本。

默认计算唯一 merge-base 并将其保存为 `diff_base`；`base` 仍是原目标分支 tip，`head` 仍是候选。分叉时这三个 ID 可以不同。需要直接比较两个提交时显式使用 `--comparison base`。多个 merge-base 不会静默任选一个；无共同祖先时默认失败，可核对需求后选择直接比较。重命名明确表示为删除＋新增，不依赖相似度推断；两侧原始内容均保留。

stdout 是回执，材料目录中只有 `packet.json`。`packet_sha256` 是这个文件的**字节摘要**；分享时可经另一个可信渠道提供它。目录必须是新目录，已有空目录也不会被覆盖；新的 head／选择／需求应写入另一个新包，旧包不修改。

## 离线校验与读取

将整个材料目录复制到另一台装有 Ergora 的机器，即可在没有源仓库、Git 命令、模型服务或控制状态时运行：

```bash
ergora review verify ./reviews/candidate-01 --sha256 PACKET_SHA256
ergora review read ./reviews/candidate-01 --sha256 PACKET_SHA256 > ./review-material.json
```

`verify` 输出提交身份、文件数量、显式上下文和覆盖边界；`read` 输出相同摘要及完整 packet。包的 JSON Schema 随应用提供为 `data/schemas/local-review-packet-v1.json`。文本和 Git blob 是按内容寻址的，不会为相同内容重复存多份；`source` 中的 `base / diff_base / head` 用 `git_object` 引用完整 `blobs` 表。`requirements`、每份 `evidence`、diff 与每个 blob 均保留 SHA256，blob 还核对仓库对象格式对应的 Git ID。

校验会核文件内容摘要、源引用、变化与所选前后文件的一致性。它证明收到的字节自洽；有独立整包摘要时还能核对是否为同一包。它不会离线证明仓库来源、提交祖先关系、采集者身份、仓库全部路径未被隐瞒或全部调用关系已被选入。diff 的正文摘要可以发现未同步摘要的字节变更；本命令不离线重放 Git diff，也不以正文摘要证明 diff 与树成员的真实关联。相同 commit 标签必须有相同文件表，但源路径到提交的成员关系仍由原采集和独立整包摘要绑定。没有独立摘要的自洽文件可以被重新制作，不是来源认证。

## 覆盖、限制与后续审查

- Git 读取禁用 replace objects、hook、textconv、外部 diff 与隐式 lazy fetch，剔除继承的 `GIT_*` 变量，不 checkout 或执行目标脚本。文件正文和其中的指令只是待审材料，不授予权限。
- 首版只收普通 UTF-8 Git 文件和可移植相对路径。二进制／无效 UTF-8、符号链接、gitlink／子模块、LFS 指针及缺少对象都会拒绝整个包，不会自动读取它们指向的工作区或远端内容。
- 默认完整 Git 材料上限为 1,000,000B，可用 `--max-source-bytes` 调整到最多 10,000,000B；它限制每次 Git 输出和去重 blob batch 的总字节（含 batch 头）。需求与全部 evidence 在读取时共用 10,000,000B 预算，最多 500 份 evidence；最终 JSON（含 diff、需求和 evidence）还受独立的 10,000,000B 上限，选择最多 500 个路径。超限不截断、不发布部分成功包；已获得清单时错误列出本次不承诺覆盖的全部选择。调整选择、容量或候选后重新生成新包。
- evidence 是操作者提供的原件，当前命令不运行检查、不确认检查绑定的提交、执行环境、签名或真实性；省略时为空。检查可信性、必要资料是否齐备和哪些运行还缺失，由后续审查和既有可信验证流程判断。
- 这里没有模型审查、正式候选批准或平台 approve。可将 `read` 的完整输出作为既有只读叶的任务材料，沿 [组合输入](WORKFLOW_DEFINITIONS.md)的容量、祖先资源、权限和后端准入处理；超限须明确拒绝，不摘取摘要冒充完整审查。领域专长和自动报告还在 Q2，不能用这一包宣称预训练／后训练语义已经验收。

Linux 支持原子目录发布；Windows 的原生实现随同一 CLI 提供，实际平台验收记录见 [Q1.1 交付](delivery/2026-11-15-local-review-packets.md)。完整正式开发执行的 Linux／WSL2 约束不因这一独立入口改变。材料包含完整项目源码和检查信息，应只通过该项目已授权的存储和审查渠道分享。
