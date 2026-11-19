# 完整选择离线证据用于复盘

简体中文 · [English](../../improvement/retrospectives.md) · [文档目录](../../README.zh-CN.md)

基础安装还可读取原完整索引；无需控制库或在线服务：

```bash
ergora handoff read ./task-handoff.zip --sha256 EXPECTED_PACKET_SHA256
```

先在输出`index.jobs`中核对原`job_id`、回执和产物`name`，再将明确选择保存为JSON文件，例如：

```json
[{"job_id":"JOB_ID","name":"ARTIFACT_NAME"}]
```

```bash
ergora handoff read ./task-handoff.zip --selection ./selection.json --sha256 EXPECTED_PACKET_SHA256 > ./retrospective-evidence.json
```

最多选择32项。每件输出完整UTF-8正文、原job／receipt／artifact身份及字节数，保留完整原index、包／manifest／index摘要和原失败、取消、未知成本；不同job的同名产物分别选择。省略selection只读索引，不预读正文。全包仍先核验，正文沿同一份已核字节读取，不重开源路径、不提取或执行ZIP。非文本、NUL、缺失／重复选择或最终规范JSON超过1MiB均明确拒绝，不返回截断或部分成功；常规CLI缩进输出可能更大，实际Agent完整输入仍受原容量准入。

输出为版本1普通JSON`ergora-handoff-selection`；`sha256`是其余字段按UTF-8、键排序、无多余空格的规范JSON摘要。它可以作为原`composition prepare --task`的显式资料输入；原`execution_success: null`、`origin_authenticated: false`和核包范围保持。它不更新记忆或活动Skill，复盘候选、独立评价和明确采用仍为后续操作。

页面可选择“复盘改进”，填写控制台所在机器的交接包路径与下载时核对的整包SHA，再“读取交接包目录”。目录须与当前项目ID一致，默认不勾选；按原job／材料名称选择后，“读取选中完整材料”展示全部原文、来源和选择身份，支持下载CLI兼容的`selected-artifacts.json`以及完整`retrospective-evidence.json`。后者内部sha256仍是上述canonical身份，不是JSON文件的字节摘要。修改来源或重读目录使旧选择不可用；成功重读清空勾选，读取失败保留输入和失败状态。二进制、NUL和完整超容量沿原owner拒绝，不用窗口或截断绕过。候选准备、只读模型调用与结果导出分别明确提交；评价与采用继续按下文执行。

## 在页面准备完整复盘输入

在“复盘改进”读取选中的完整材料后，“准备复盘候选输入”表单才可提交。选择 Skill、项目记忆或工作流方向；Skill 要“读取当前基线”并明确选择活动 head，记忆要明确选择有效修订或“新建记忆”。工作流另填待改进的完整 target manifest、其 digest 和目标根的新版本；它与候选作者的 manifest 是两个不同的输入。

填写改进目标、已保存的作者完整 manifest 路径、作者实例、新输入目录和完整 prompt 字节上限，再点击“保存完整候选输入”。所需三个 preset 与作者 manifest 的准备方式见下文各方向。服务端重新核基线、证据和完整权限／资源／容量，已有目录不覆盖。保存成功只产生完整原 input；模型调用、原结果检查、候选导出、评价和采用按下文分别明确执行。

若准备报错、丢回复或页面已切换，保留原提交目录，在“复读已保存输入”填写该路径并明确读取。这里核完整原 input／请求／继承材料及所属项目，不根据新表单重建，也不自动重新准备。源 head 或记忆后来失效不改写已存输入；新的准备仍使用当前有效来源。换电脑时需要携带整个输入目录，不能只复制页面返回的 JSON。原 `ergora composition verify-input INPUT_DIRECTORY --material` 可离线核完整目录；实际 `run-input` 仍重新执行当前后端准入。

## 在页面明确调用冻结的只读叶

“工具绑定”与“复盘改进”均有“调用冻结的只读叶”。填写控制台所在机器的完整 input 目录及原 digest，选择冻结定义请求的后端，或明确指定后端／模型／原因及可选 Codex 推理配置路径，然后“检查当前只读准入”。界面展示原角色、请求与实际后端、全部资料身份和权限上限。检查是当前观察；调用前会重新检查，输入／后端改变后需重新核对。

确认后填写超时，明确提交一次调用。执行中字段锁定，页面不会自动重发或续接。关闭窗口、切页或网络错误不表示原调用停止；重新打开窗口，明确“读取原调用记录”，按 input digest、后端和开始时间核对最近100条原记录。结果里的 status 是原运行状态，HTTP 成功返回也可能保存了 failed／timed_out；完整结果使用 result 文件与 SHA，诊断输出仅有界展示。

从“复盘改进”打开时，成功原记录可“带入原结果检查”，复制已保存的 run snapshot 目录、input digest、result 路径与 SHA。核对所属方向，再明确检查和导出；后继审查者输入按下文完整 checked JSON 另行准备，不会自动传递。作者与审查者尽量选择不同后端，回退时填写原因。本入口仅支持 text-only 只读叶；工具限制不提供 OS 隔离，也不授权正式任务、评价或采用。一般 input 的 task 正文没有统一项目字段，项目选择是该次 run 的归属；复盘检查另核其原项目声明。

## 在页面检查结果并导出完整候选

在“复盘改进”的“检查结果与导出候选”中，选择结果所属方向，填写完整原 input 目录及其 digest、原 Agent 结果文件及其原 SHA256，然后明确检查。可用本节上方的输入复读或原 `composition verify-input` 核对 input digest；原模型调用回执给出 result 文件与 SHA。这里不依赖当前上方证据选择，使用冻结输入中的原来源。

检查展示完整原请求和 Agent 回复，并可下载完整 `retrospective-checked.json`；摘要对应原 input／原结果／候选，而下载 JSON 的文件摘要另算。来源改变后须重新检查。null 候选无需导出；有候选时先审阅完整内容，再填写新候选导出目录并明确提交。Skill 目录的末级名称必须等于候选 name。

导出按同次选中的项目／input／结果／候选身份重新核对，再原子保存完整文件和执行位；已有目录不覆盖，不能导出到冻结 input 内。失败或丢回复保留上次目录且不自动重发，先按下文各方向的原 CLI 检查已有目标；不要删除目标来强制重试。导出不导入、评价或采用，后续继续按下面的原流程明确执行。

## 生成来源绑定的Skill复盘候选

先有一个已注册的项目、可核验的交接包，以及该项目已导入的基线Skill。`ergora skill list my-project`返回当前`active`中的name、digest和revision；首次导入只建立baseline，不代表测得改进。用上节的selection JSON选择完整来源，再写一个UTF-8的`objective.txt`说明本次要改进什么。

```bash
ergora composition install-preset retrospective
```

新组合的根为`ergora-skill-retrospective 1.0.1`，包含只读作者`root/propose`与后继审查者`root/review`，均默认Codex gpt-6.1-sol high。按[完整manifest步骤](../../definitions/workflows/compose.md#freeze-the-current-preview-into-the-persistent-control-directory)给这个根准备manifest目录；grant需显式允许读取`workspace`／`definitions`、空write／network且shell为false，并给出根需要的limits。导入、manifest和下列准备均不发模型请求。

```bash
ergora retrospective prepare my-project ./task-handoff.zip --selection ./selection.json --packet-sha256 PACKET_SHA --skill SKILL_NAME --digest BASELINE_DIGEST --head-revision HEAD_REVISION --objective ./objective.txt --manifest ./retrospective-manifest --instance root/propose --directory ./retrospective-author-input --max-prompt-bytes 500000
ergora composition run-input my-project ./retrospective-author-input --backend codex --mode text-only --timeout 240
```

准备核同项目的完整原来源与当前活动Skill，冻结其全部UTF-8文件和执行位、精确digest／head revision、原失败／未知成本、目标和响应schema。Skill原文件总量最多1 MiB，完整prompt另按所给限制核验；超限明确拒绝，需要减少显式选择或更小的Skill，不截断参考资料。已准备的input继续原快照，新准备重新核当前head。prepare／check面向输出提案JSON的只读叶，也可选择自己定义的叶与受支持后端。

调用回执给出原`result`文件路径和`result_sha256`。保存它们后检查该份原结果：

```bash
ergora retrospective check ./retrospective-author-input AUTHOR_RESULT --result-sha256 AUTHOR_RESULT_SHA > ./retrospective-checked.json
ergora composition prepare-from-manifest ./retrospective-manifest root/review --task ./retrospective-checked.json --directory ./retrospective-review-input --max-prompt-bytes 500000
ergora composition run-input my-project ./retrospective-review-input --codex-config ./inference.toml --mode text-only --timeout 600
```

作者的普通`artifacts.response`必须是符合冻结proposal_schema的JSON，包含对应来源SHA、基线digest／revision、选中材料的精确引用、负结果、成本／不确定性，以及完整标准Skill文件建议。没有充分依据可返回`candidate:null`。检查输出完整原请求与原Agent结果，核候选的便携路径、元数据、目录内容身份和引用；它离线执行、不创建State，源包或原Skill以后丢失仍可核。`quality_evaluated:false`、`adoption_authorized:false`、`origin_authenticated:false`明确保留，结构关联通过不是质量证明。

check有界读取最多8 MiB的原结果，给完整文件在response字符串中的嵌套JSON转义留出空间。后继审查沿上面的原composition准备命令显式接收完整checked JSON；该preset审查叶返回文字审查，不再调用retrospective check。后继完整prompt仍须单独通过原容量门禁，大结果可离线检查不代表它能放进任意后继prompt。静态depends_on本身不会自动执行端口。内置作者／审查者使用独立Codex会话并满足定义下限；上述`inference.toml`由操作者提供可信provider配置及环境凭据引用。其他后端示例仅适用于未声明该下限的自定义定义，覆盖仍须经过实际准入；同后端会话不构成异后端成功。检查或模型调用失败先保留原input、run和reply，不自动重发；原Agent记录是调用事实的权威。

有非null候选并审阅完整内容后，从check返回值取得`candidate_digest`，明确导出到末级名称等于Skill name的新目录：

```bash
ergora retrospective export ./retrospective-author-input AUTHOR_RESULT ./candidates/SKILL_NAME --result-sha256 AUTHOR_RESULT_SHA --candidate-digest CANDIDATE_DIGEST
ergora skill import my-project ./candidates/SKILL_NAME --hypothesis '填写可检验的改进假设'
```

导出重新核原input和两个显式摘要，保存完整文件原字节及执行位；不执行文件、不创建State、查询实时来源或导入／采用。目标存在、位于冻结input内部、身份无法保持或结果无候选时拒绝；发布不会替换同时出现的空目录。失败清理本次私有staging，已有目标保持。回复丢失时先保留原input／result／候选摘要，检查已有目标；不要覆盖或删除它来绕过拒绝。明确import后的返回digest必须与选定候选一致；初始基线已存在时，import只登记候选，活动head不动。

使用维护者预先准备的可信评价器和评价集，给基线与候选运行同一suite；不能把模型提案的evaluation_plan或自报评分直接视为可信suite：

```bash
ergora evaluation register my-project ./evaluation.json
ergora evaluation run my-project BASELINE_DIGEST --suite SUITE_DIGEST
ergora evaluation run my-project CANDIDATE_DIGEST --suite SUITE_DIGEST
ergora evaluation compare my-project BASELINE_RUN_ID CANDIDATE_RUN_ID
ergora skill adopt my-project --baseline-run BASELINE_RUN_ID --candidate-run CANDIDATE_RUN_ID --revision HEAD_REVISION --reason '填写审阅评价证据后的采用理由'
ergora skill rollback my-project SKILL_NAME BASELINE_DIGEST --revision ADOPTED_HEAD_REVISION --reason '填写回退理由'
```

用register和两次run返回的精确suite digest／run ID填入对应占位符。compare的eligible、完整可信证据、当前head和显式理由共同决定采用；head变化时原采用会拒绝，应重新选当前基线并评价，不能只改revision强套旧结果。rollback使用采用后原head的revision，追加历史而不删除候选或旧评价。null候选无需导出或强造改进。详细suite合同见[Skill候选评价与采用](../../improvement/skills-and-evaluation.md#skill-candidates-evaluation-and-adoption)。

## 生成来源绑定的记忆复盘候选

用同项目的完整交接包和selection准备记忆建议。安装`memory-retrospective`，再按[manifest步骤](../../definitions/workflows/compose.md#freeze-the-current-preview-into-the-persistent-control-directory)固定其根`ergora-memory-retrospective 1.0.2`，保存到`memory-retrospective-manifest`。该模板的`root/propose`与`root/review`均默认Codex gpt-6.1-sol high；权限与显式调用方式同上，所有叶读取全部祖先资料。

```bash
ergora composition install-preset memory-retrospective
ergora memory catalog my-project
ergora retrospective prepare-memory my-project ./task-handoff.zip --selection ./selection.json --packet-sha256 PACKET_SHA --memory-id MEMORY_ID --revision MEMORY_REVISION --objective ./objective.txt --manifest ./memory-retrospective-manifest --instance root/propose --directory ./memory-author-input --max-prompt-bytes 500000
ergora composition run-input my-project ./memory-author-input --backend codex --mode text-only --timeout 240
```

更正必须选catalog中当前有效的精确ID／revision，陈旧、到期、删除或其他项目记录会拒绝。新建建议将`--memory-id MEMORY_ID --revision MEMORY_REVISION`替换成`--new-memory`，其基线明确为null、revision为0。prepare先核完整原证据，再观察canonical记录，冻结完整正文、来源、有效期和观察时刻；该时刻不保证未来仍有效。原prompt容量另核，超限明确失败，完整正文不会截断。

取得作者回执的原`result`与`result_sha256`后，离线检查，并把完整checked JSON交给原审查叶：

```bash
ergora retrospective check-memory ./memory-author-input AUTHOR_RESULT --result-sha256 AUTHOR_RESULT_SHA > ./memory-checked.json
ergora composition prepare-from-manifest ./memory-retrospective-manifest root/review --task ./memory-checked.json --directory ./memory-review-input --max-prompt-bytes 500000
ergora composition run-input my-project ./memory-review-input --codex-config ./inference.toml --mode text-only --timeout 600
```

作者按冻结schema提供完整候选正文（最多100000字符）、假设、适用范围和验证计划，也可返回null。原失败、未知成本和每项观察的精确材料引用保持。模型不能选来源、有效期或修订；check的`save`只包含可供原记忆接口使用的完整正文、由整包SHA与选择SHA派生的固定来源，以及原ID／expected_revision。candidate_digest绑定完整save内容和基线身份；离线检查不创建State、查询实时记忆或认证来源作者，也不证明当前有效或质量提升。原结果上限8 MiB，审查完整prompt仍另核容量。后端不可用时可按前节显式回退并记录原因。

有非null候选、审阅原证据及验证计划后，明确导出：

```bash
ergora retrospective export-memory ./memory-author-input AUTHOR_RESULT ./candidates/project-memory --result-sha256 AUTHOR_RESULT_SHA --candidate-digest CANDIDATE_DIGEST
```

新目录含完整UTF-8原字节的`memory.txt`及`receipt.json`，命令也返回receipt。其`save.source.uri`、`save.source.revision`、`save.memory_id`和`save.expected_revision`分别填入以下原保存命令；项目必须与receipt.project相同。`memory save --text`保留原换行和全部Unicode字符，包括开头的U+FEFF；读取人工文本时也不自动移除该字符。目录发布拒绝既有目标或冻结input内部，不自动保存，不改变原记忆或ReMe投影。回复丢失先核原目录／receipt和文本SHA，不覆盖重导。

也可在控制台选择同一项目的“长期记忆”。新建候选用“新增记忆”；更正候选须先核对回执中的原ID／revision，再在该记录上点“更正”。在“正文 UTF-8 文件”选择导出的 `memory.txt`，它优先于输入框，保留完整BOM和换行；按回执填写来源URI和来源版本，明确核对有效期后保存。无效UTF-8会留在表单中报错。人工编辑输入框使用浏览器换行；未编辑的已有正文保持原字符串。

保存后窗口显示本次提交与原返回记录，由用户点右上角“刷新”读取新状态。历史窗口显示完整正文／来源和期限，可单选一条旧修订并明确恢复；恢复追加新修订，保留所选历史的期限。更正冲突或回复异常时先刷新并核对原目录、ID和revision，再决定是否重新打开表单；请求可能已执行，页面不会自动重发。删除会清空全部历史正文／来源且不能恢复；同步和重建投影在独立表单中明确提交，远端可见性继续由所配后端决定。

```bash
ergora memory save my-project --text ./candidates/project-memory/memory.txt --source SOURCE_URI --source-revision SOURCE_REVISION --id MEMORY_ID --revision MEMORY_REVISION
ergora memory history my-project MEMORY_ID
ergora memory restore my-project MEMORY_ID --from-revision BASELINE_REVISION --revision CURRENT_REVISION
```

新建时省略`--id`和`--revision`，使用原save返回的新ID。更正省略expiry参数，沿原owner保留原有效期；即使候选生成后已经到期，保存也不会续期或使其进入召回。用户需续期时在原save另作显式选择。原修订变更或删除会拒绝陈旧保存，应重新选择基线；save回复不确定时先核catalog／history，尤其新建不能自动重试。恢复追加原修订并保留其有效期，已删内容不可恢复。这里没有Skill的可信suite采用门禁，模型approve只审阅提案；验证与明确写入仍分别进行。流程候选另接原definition修订合同。

## 生成来源绑定的工作流复盘候选

安装`workflow-retrospective`，再按[完整manifest步骤](../../definitions/workflows/compose.md#freeze-the-current-preview-into-the-persistent-control-directory)为根`ergora-workflow-retrospective 1.0.1`保存`workflow-retrospective-manifest`。另为待改进的根保存完整`target-manifest`，记录原检查返回的完整digest。前者是作者／审查图，后者是目标图。handoff、selection与objective沿[Skill候选](#生成来源绑定的skill复盘候选)步骤准备，均须来自同一项目。

```bash
ergora composition install-preset workflow-retrospective
ergora retrospective prepare-workflow my-project ./task-handoff.zip --selection ./selection.json --packet-sha256 PACKET_SHA --target-manifest ./target-manifest --target-digest TARGET_MANIFEST_DIGEST --next-version 1.0.1 --objective ./objective.txt --manifest ./workflow-retrospective-manifest --instance root/propose --directory ./workflow-author-input --max-prompt-bytes 1000000
ergora composition run-input my-project ./workflow-author-input --backend codex --mode text-only --timeout 240
```

`--next-version`须选择尚未占用的不可变根版本；既有版本不能覆盖。目标整包的全部递归定义、资源正文、执行位与目录（含空目录）完整冻结，文件合计至多1 MiB；二进制、NUL或超限拒绝，不截断。target-digest使用原manifest的文件／执行位身份，冻结baseline.digest还绑定完整目录；导出回执同时保留两种身份与目录。准备成功后目标源消失不影响离线检查。提示的总容量仍单独核对，可按实际后端上限调整`--max-prompt-bytes`。

```bash
ergora retrospective check-workflow ./workflow-author-input AUTHOR_RESULT --result-sha256 AUTHOR_RESULT_SHA > ./workflow-checked.json
ergora composition prepare-from-manifest ./workflow-retrospective-manifest root/review --task ./workflow-checked.json --directory ./workflow-review-input --max-prompt-bytes 1000000
ergora composition run-input my-project ./workflow-review-input --codex-config ./inference.toml --mode text-only --timeout 600
```

作者、审查者读取完整祖先资料和完整前驱。后端选择／失败保存与上述Skill候选相同；静态依赖不会自动执行端口。检查允许`candidate:null`，否则核原preview、完整资源、图及原grant；只在自动清理的私有临时目录写入，不读写活动State。首版只允许根description、已有声明资源的无NUL UTF-8内容与额外依赖边，保留原节点／引用／端口／权限／审查要求及已有依赖；改变这些结构仍走原手工版本修订。

核对完整`revision_preview`与来源后，显式选择check返回的`candidate_digest`。没有候选时不能导出。

```bash
ergora retrospective export-workflow ./workflow-author-input AUTHOR_RESULT ./candidates/workflow-root --result-sha256 AUTHOR_RESULT_SHA --candidate-digest CANDIDATE_DIGEST > ./workflow-export-receipt.json
ergora composition check ./candidates/workflow-root
ergora composition import ./candidates/workflow-root
```

导出目录须为新目录，完整根bundle及引用身份保持；stdout回执另存，目录内没有额外receipt污染包身份。其他机器须先具备相同子定义，原 import 会核依赖与 ID／版本冲突。导入成功后用原步骤为新版本准备manifest并明确选择；回退时重新选原根／manifest，旧run始终保留旧快照。导出、模型approve及图准入都不等于质量／性能评价或采用授权；效果比较仍需相同可信workload和独立验证。
