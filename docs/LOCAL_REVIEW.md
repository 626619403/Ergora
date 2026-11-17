# 本地 PR／MR 审查材料

`ergora review` 将精确的本地 Git 变更保存成可以离线读取的完整材料包，也可读取明确的GitHub／GitLab PR／MR来源并绑定同一份源码包。材料采集和审查输入准备无需 Agent 登录、项目登记、数据库或 Temporal；实际模型调用沿既有组合入口。完整报告和远端发表意见的范围见 [实施计划](plans/2026-11-15-domain-review-optimization-quality.md)。

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

## 采集一个外部 PR／MR

先将明确的来源绑定保存为`tracker.json`，例如以下GitHub配置。GitLab使用`"tool": "gitlab"`、完整namespace/project，可选`api_url`指向自建站的`https://host/api/v4`。`token_env`只填写已在运行环境设置的凭据变量名；公开来源允许省略，凭据不会写进材料。

```json
{"tool": "github", "project": "org/project", "token_env": "GITHUB_TOKEN"}
```

```bash
ergora review collect /path/to/project \
  --binding ./tracker.json --number 42 \
  --requirements ./request.md \
  --context src/caller.py --context config/training.toml \
  --evidence ./candidate-check.txt \
  --directory ./reviews/pr-42-observation-01 > ./source-receipt.json

ergora review read-source ./reviews/pr-42-observation-01 \
  --sha256 SOURCE_SHA256 > ./complete-review-source.json
```

`--number`是这个GitHub仓库内的PR number或GitLab项目内的MR iid。采集对平台执行两个GET（仓库元数据、所选PR／MR），保存规范化原生观察、完整正文、真实native ID、原响应摘要及观察时间；不搜索列表、查询当前分支、读取平台diff／全部评论或自动获取CI日志。源码仍来自已经具有所需对象的本地Git库，不能用一个同名工作区代替完整对象；缺对象须由操作者明确取得后重新采集。

GitHub使用本次响应中的base／head SHA计算唯一merge-base；首版拒绝已merged的GitHub PR，因为当前base不能可靠重建历史合并前的比较。GitLab以`diff_refs.start_sha`为目标提交，核对其head与原`sha`相同，以及本地唯一merge-base等于`diff_refs.base_sha`；diff_refs尚未生成或观察不一致时拒绝，不自动重试／拼接不同时刻的字段。两平台首版只支持同仓库端点，fork或已删除的来源仓库明确失败。

目录包含`source.json`及`material/packet.json`。回执`source_sha256`是来源封套的字节摘要，封套再以`packet_sha256`固定原本地包；`read-source`核两层摘要、来源／原生仓库ID／请求地址／精确比较关系，并返回完整两层资料。原本地包的repository id使用`native-repository-sha256:`加来源及native仓库身份规范JSON的SHA256，完整身份仍在来源封套中；合法的长平台地址／项目路径不会被截断，也不从本地remote推定归属。可单独使用`review read`／`verify`读取`material`子目录，此时应提供回执中的`packet_sha256`。

新head或需求应写新目录，旧观察不变。复制时共享整个来源目录和独立取得的`source_sha256`；读回无需Git、凭据、网络、State或SDK。来源元数据与PR／MR是顺序观察，不是跨请求原子快照；本地缺对象／源容量／不支持文件规则与上文相同，完整来源封套另限2,000,000B。来源GET的响应摘要是采集时的观察回执，包不保存全部原始HTTP响应，也不离线重认证它。离线自洽不证明平台来源、当前head、目标本地库的远端归属或原检查真实。它没有正式候选／批准效力。

## 交给领域或专长审查叶

先按[领域审查手册](TRAINING_REVIEW.md)安装`pretraining-review`或`posttraining-review`，准备所选完整manifest及明确的grant。自定义审查组合沿[定义手册](WORKFLOW_DEFINITIONS.md)导入，不必修改Python。每个叶的专长、祖先Skill、上下文、MCP声明和逐级收窄的权限都来自这个冻结组合；后端在实际调用时逐叶选择。

以下示例使用本地包及预训练根`ergora-pretraining-review@1.0.2`。`review-grant.json`应包含所选根的`permissions`和`limits`，格式见[组合分享](WORKFLOW_DEFINITIONS.md#保存和分享完整组合)。`MANIFEST_DIGEST`取prepare-manifest回执的`digest`，`PACKET_SHA256`取原材料回执；两者须明确核对。

```bash
ergora composition install-preset pretraining-review
ergora composition prepare-manifest ergora-pretraining-review 1.0.2 \
  --grant ./review-grant.json --directory ./reviews/pretraining-manifest

ergora review prepare-input ./reviews/candidate-01 \
  --source-kind local --source-sha256 PACKET_SHA256 \
  --manifest ./reviews/pretraining-manifest --manifest-digest MANIFEST_DIGEST \
  --instance root/domain/review --max-prompt-bytes 1000000 \
  --directory ./reviews/domain-input > ./input-receipt.json

ergora review verify-input ./reviews/candidate-01 \
  --source-kind local --source-sha256 PACKET_SHA256 \
  --manifest-digest MANIFEST_DIGEST \
  --input ./reviews/domain-input --input-digest INPUT_DIGEST
```

外部PR／MR将材料目录换为整个外部来源目录，使用`--source-kind external --source-sha256 SOURCE_SHA256`，保留完整观察及其内部源码包。后训练根用`ergora-posttraining-review@1.0.2`，领域路径同为`root/domain/review`；两个根的通用叶为`root/general/structure/review`、`root/general/correctness/review`、`root/general/test-value/review`。一次prepare只准备所选一个叶，不运行其他分支或all-join。

新目录是原格式的完整composition input。`task.txt`包含原需求、全部源码／显式上下文／祖先规范／检查、外部观察及所选来源与manifest身份；`prompt.txt`再加入模板完整祖先资料。`input_digest`取新回执；完整prompt（含JSON编码和资料）最多1,000,000B，`--max-prompt-bytes`可设更小。超限明确失败，不截断材料。需要未运行前驱、具有write／shell／network权限或无权读取任一包内源码的叶也会拒绝。

`verify-input`按独立来源摘要重新读取完整材料，再与固定输入的task和`input_digest`核对。`manifest_digest`在task中保留原选择声明；该命令不重新读取原manifest，不单独认证其来源。首次prepare会直接核原manifest及编译图，分享时同时提供可信的输入摘要。仅剩输入目录时可用`ergora composition verify-input`核其自身完整性，此时没有重新核原来源包。

实际调用先按[单叶调用](WORKFLOW_DEFINITIONS.md#调用一个准备好的叶子)登记项目并配置可用后端，再执行原`composition check-input`／`run-input`。例如已登记项目`demo`可显式选Codex：

```bash
ergora composition check-input demo ./reviews/domain-input \
  --mode text-only \
  --backend codex --backend-reason "Operator selected an available review backend"
ergora composition run-input demo ./reviews/domain-input \
  --mode text-only \
  --backend codex --backend-reason "Operator selected an available review backend" --timeout 240
```

后端认证、支持模式和实际能力仍由原准入检查。运行回执的`input_digest`应与所选输入回执一致。执行者与审查者优先使用不同后端；回退须记录实际原因，不把同后端调用称为异构审查。结果和完整冻结输入仍保存在原run中；失败或unknown先读取原run，不自动重复调用。此入口只负责单叶审查输入，不授予正式候选或平台批准。

完成调用后可用`ergora composition inspect-run demo RUN_ID > ./original-run.json`[按精确ID读取](WORKFLOW_DEFINITIONS.md#按精确-id-读取原组合运行)完整原输入和result，核`run.input_digest`与所选回执一致，以及各项`available`／原状态；不会自动补跑其他分支或重新调用模型。

## 汇总完整的多分支审查

用同一来源包和同一manifest，分别为需要的叶执行上述prepare／check／run-input。把原回执中的精确run ID写入`review-runs.json`；预训练和后训练根均可使用以下四个路径：

```json
{
  "root/domain/review": "DOMAIN_RUN_ID",
  "root/general/structure/review": "STRUCTURE_RUN_ID",
  "root/general/correctness/review": "CORRECTNESS_RUN_ID",
  "root/general/test-value/review": "TEST_VALUE_RUN_ID"
}
```

然后生成完整JSON，或由同一观察生成Markdown：

```bash
ergora review report demo ./reviews/candidate-01 \
  --source-kind local --source-sha256 PACKET_SHA256 \
  --manifest ./reviews/pretraining-manifest --manifest-digest MANIFEST_DIGEST \
  --runs ./review-runs.json > ./review-report.json

ergora review report demo ./reviews/candidate-01 \
  --source-kind local --source-sha256 PACKET_SHA256 \
  --manifest ./reviews/pretraining-manifest --manifest-digest MANIFEST_DIGEST \
  --runs ./review-runs.json --format markdown > ./review-report.md
```

外部PR／MR同样选择整个来源目录、`--source-kind external`及SOURCE_SHA256。报告按明确manifest的全部Agent叶列出预期成员，核每份原input的实例／完整编译图／来源task、原prompt及result SHA，再按可信reviewer结果合同解释意见。单独叶或自定义嵌套只读审查模板也可用；每个叶都须直接读取根task，不能跳过串行前驱。定义中的专长／后端与原run实际binding／选择原因分别保留，历史读取不要求当前后端、认证、Git或网络。

`coverage`分别给出expected、selected、verified和completed；complete要求全部预期叶的证据可核且原status为succeeded。只有完整覆盖且全部approve才总体approve；任一request-changes都保留并使完整报告为request-changes。漏选、未知run、失败／运行中、错源或坏原件使总体为incomplete，`request_changes`仍列出已核反对分支，完整回复与错误继续保存在branches中。未知实例或重复run映射直接拒绝，不能用同一run填满多位专家。

报告成功返回观察时exit0，脚本应检查`coverage.complete`、`decision`及各分支原状态。默认每份result最多8,388,608B，可显式提高`--max-result-bytes`后重新读取；超限返回对应分支不可核，绝不截断。重复生成只读原run，不补跑缺叶、重发失败／unknown、写平台或授予正式批准；正式六阶段任务仍使用原runtime。Markdown含每份已核回复及完整JSON观察，分享时保留项目原有源码访问范围。

原run记录和result的JSON观察还要求有限数字，并使用定义文档原有的64层／100,000值结构容量；NaN／Infinity、指数溢出或超出结构容量均明确不可核，不让一个分支破坏整份导出。该容量与结果字节上限分别检查，提高字节上限不改变结构容量；原始文件和摘要保持，不截断、重写或自动重新调用。

## 覆盖、限制与后续审查

- Git 读取禁用 replace objects、hook、textconv、外部 diff 与隐式 lazy fetch，剔除继承的 `GIT_*` 变量，不 checkout 或执行目标脚本。文件正文和其中的指令只是待审材料，不授予权限。
- 首版只收普通 UTF-8 Git 文件和可移植相对路径。二进制／无效 UTF-8、符号链接、gitlink／子模块、LFS 指针及缺少对象都会拒绝整个包，不会自动读取它们指向的工作区或远端内容。
- 默认完整 Git 材料上限为 1,000,000B，可用 `--max-source-bytes` 调整到最多 10,000,000B；它限制每次 Git 输出和去重 blob batch 的总字节（含 batch 头）。需求与全部 evidence 在读取时共用 10,000,000B 预算，最多 500 份 evidence；最终 JSON（含 diff、需求和 evidence）还受独立的 10,000,000B 上限，选择最多 500 个路径。超限不截断、不发布部分成功包；已获得清单时错误列出本次不承诺覆盖的全部选择。调整选择、容量或候选后重新生成新包。
- evidence 是操作者提供的原件，当前命令不运行检查、不确认检查绑定的提交、执行环境、签名或真实性；省略时为空。检查可信性、必要资料是否齐备和哪些运行还缺失，由后续审查和既有可信验证流程判断。
- 采集和输入准备本身没有模型审查、正式候选批准或平台 approve。领域专长可按上述入口显式调用，再按原run生成完整跨分支建议报告；源码材料和模型意见不能证明预训练／后训练语义已经验收。

Linux 支持原子目录发布；Windows 的原生实现随同一 CLI 提供，实际平台验收记录见 [Q1.1 交付](delivery/2026-11-15-local-review-packets.md)。完整正式开发执行的 Linux／WSL2 约束不因这一独立入口改变。材料包含完整项目源码和检查信息，应只通过该项目已授权的存储和审查渠道分享。
