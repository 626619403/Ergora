# 可组合工作流定义

简体中文 · [English](../../../definitions/workflows/compose.md) · [文档目录](../../../README.zh-CN.md)

工作流包把精确版本的专家或子工作流组合成有界 DAG。可以单独使用结构审查模板，也可以把结构、正确性、测试价值三个模板并行组合，再串接执行模板。结构父链决定继承；工作依赖只通过具名端口传递数据。

`composition` 提供静态检查、不可覆盖的版本库、完整预览、可携带的静态组合包与显式单叶调用。预览不调用模型；`run-input` 可将准备好的输入交给所选后端。正式开发按[六阶段流程](../../development/tasks.md#正式任务的操作顺序与恢复)执行，审查阶段可运行嵌套的只读串并行分支并作显式all-join汇合，具体配置见[正式审查组合](../../development/preparation.md#为正式任务冻结审查组合)。只读审查的数据端口见[正式DAG协议](contracts.md#正式只读审查的数据端口)；专长执行者分配使用下文的[work-units-v2协议](contracts.md#专长执行者与原工作单元)。

Web控制台的“Agent 与组合库”复用同一版本库、导入和preview用例，无需先注册项目。选择精确工作流版本，检查根声明初始化的静态上限后明确预览，即可查看每个实例的结构父链、先行依赖、具名端口、完整资源来源及装配提示；详见[页面操作](#在页面浏览与预览定义)。静态上限不构成项目授权，后端字段仅为请求。页面下载的定义JSON和预览JSON用于阅读与比较；分享完整资源和精确依赖应使用下文`export`、`prepare-manifest`或[固定当前预览](#固定当前预览到持久控制目录)。标准正文可在页面[明确修订](revisions.md#在页面修订工作流)；嵌套画布与正式交接见[工作流指南](../../../definitions/workflows/revisions.md#view-published-nested-relationships)。

导入、预览和固定 manifest 提供静态图产物。[独立图命令](#运行独立工作流图)显式执行受支持的只读工作流。一般 Repeat 和任意混合节点图执行仍未实现。已登记设计政策目前只保存要求，并明确拒绝不支持的执行；可信人类通道不可用。有限训练控制器须[明确授权](../../../training/controllers.md#start-a-local-training-budget-and-recover-original-authorization)。见[当前计划](../../../PLAN.md)和[设计政策执行门禁](../../../../src/ergora/development/design.py)。

## 运行独立工作流图

普通项目可用完整 manifest 和摘要运行图。输入 JSON 的键须与根端口完全一致，例如根端口是 `task` 时，填写 `{"task":"阅读所给资料并梳理依赖。"}`。

```bash
ergora composition run-graph my-project ./complete-manifest --manifest-digest MANIFEST_DIGEST \
  --inputs ./graph-inputs.json --directory ./original-graph-run --max-prompt-bytes 150000 --timeout 300
```

命令按依赖与冻结的并发上限调度就绪叶子，沿具名端口传递完整结果。子工作流可以嵌套，all-join 按完整实例路径汇集声明的前序输出。每个叶子使用支持纯文本的后端和只读权限，启动与等待共享一个总体截止时间。正式代码交付使用现有审批和验证流程。

运行目录的 `run.json` 记录原 manifest、输入、已尝试叶子的 ID 和具名输出。可用 `composition inspect-run` 查询各叶子。整图保留的完整叶子结果累计上限是 8 MiB，最终输出也遵守 8 MiB 上限。超限时保留原叶子记录并返回失败。Ctrl+C 通过原进程所有者请求取消，Linux/WSL2 上的 SIGTERM 也走同一条路径。中断后沿原记录核对，执行命令要求一个尚未使用的目录。

### 在声明的分支失败后继续独立工作

仅由 Agent、子工作流和 all-join 组成且没有 FlowMap 门控的独立 Workflow v2，可在根定义中声明以下策略。这里 `dependency` 是根的直接 Agent，`review` 是依赖该 Agent 的汇合输出，`structure` 是必需的结构审查输出。

```json
{
  "completion": {
    "continue_after_failure": ["dependency"],
    "optional_outputs": ["review"]
  }
}
```

协调器核实原进程正常退出且退出码为 1 至 255 后，可以继续独立工作。失败尝试、原运行摘要和退出码保留在原记录中。依赖该 Agent 的消费者被阻塞。所有必需输出就绪时，图以 `succeeded` 交付已有输出，并用 `unavailable_outputs` 记录缺失可选端口的生产者和原失败实例。此例可取得 `structure`，配对的 `review` 仍未完成。若 `review` 为必需端口，图返回 `failed`，可按原 Agent ID 读取已完成的结构审查。正式审查沿用候选绑定的必需与建议职责。 [正式审查合同](../../../definitions/workflows/contracts.md#static-required-and-advisory-review-declarations)

默认首个失败会停止派发。取消、到期和证据无法核实时，协调器继续按原范围围栏。恢复核对原运行、输入、提示、预留、截止及已记录的失败证据，只有尚未预留的叶子可以启动。 [原图恢复](../../../definitions/workflows/compose.md#resume-an-interrupted-graph)

### 确认是否启动建议的专家

在 Linux/WSL2 上，为原始 `run-graph --recoverable` 命令加 `--pause-before-route root/choose`，使用冻结图中一个 `choose-agent` 的精确实例路径。分析专家建议启动后续专家时，图等待已启动的工作收尾，返回 `awaiting_route_decision`，退出码为零。分析专家给出 `none` 时，按图的声明完成该节点。

从 `inspect-graph` 取得 `recovery.route_checkpoint.sha256`、推荐分支和原分析运行 ID。读回原分析后，在原图上提交决定：

```bash
ergora composition resume-graph PROJECT ./original-graph-run --manifest-digest MANIFEST_SHA256 \
  --route-checkpoint CHECKPOINT_SHA256 --route-action follow-up
```

`follow-up` 采用原建议，`finish` 跳过条件专家。等待期间原截止时间继续计算，决定沿用原项目、manifest、输入和权限。

自动分流的读回与恢复使用原分析结果和冻结分支。监督者选择跟进或结束时，还会核对原检查点和原决定，再恢复有效分支或跳过状态。

若回复丢失，先对原运行目录执行 `inspect-graph`。检查点仍为 `awaiting` 且原图可恢复时，提交相同的摘要和决定。`decided` 状态会给出已保存的原决定及其摘要，原图仍可恢复时可用普通 `resume-graph` 继续。终态继续通过 `inspect-graph` 读取。

## 使用内置领域组合

仅安装wheel即可导入默认专家及其全部子工作流，不需要先下载仓库examples，也不调用模型或启动服务：

```bash
ergora composition presets
ergora composition install-preset repository-governance
ergora composition install-preset large-change
ergora composition install-preset training-optimization
ergora composition install-preset refactoring
ergora composition install-preset optimization-performance-diagnosis
ergora composition install-preset training-flow-map
ergora composition install-preset evidence-report
ergora composition install-preset optimization-report
ergora composition install-preset pretraining-review
ergora composition install-preset posttraining-review
ergora composition show ergora-large-change-delivery 1.5.8 --material
ergora agent definition show ergora-server-implementer 2.0.2 --material
```

[预训练／后训练审查](../../../review/training.md)复用通用三路审查并增加领域专家，独立叶调用和正式 all-join 分开说明。

[证据报告作者](../../review/evidence-reports.md)提供独立只读 `root/author`，从完整提供的材料生成 Markdown 与静态自包含 HTML 阅读视图。它复用下文的 manifest／单叶输入／原 run 读取，不采集证据、执行前驱或授予批准。

`presets`只读发行内容，不创建State。`install-preset`沿依赖顺序导入精确版本；重复执行保持同一身份，已有同ID/version的不同内容会拒绝。各定义分别原子发布，整套安装不是跨库事务；中断后可重试。安装不改变项目绑定或权限，不安装/认证Agent CLI，也不授予执行或批准权限。新默认库的权威资源在 [data/presets](../../../../src/ergora/data/presets/presets.json)，可以沿原export/new-version/import流程替换专家及子模板；已有examples的身份保持。

冻结前，监管者按任务选择成员和依赖。开发为每个获批工作单元明确负责人、写入范围、依赖和验收标准。PR 审查按适用范围及所需证据选择审查者。派发已授权的就绪工作，在已有写入权限范围内将负责人、状态、受影响文件、卡点、下一步和原 Job 或运行 ID 写入持久任务清单。会话中断后按原身份核对外部 Job。保留正式审批、冻结候选、权限、预算、截止、停止和清理约束。训练优化的人员安排见[优化 Skill](../../../../src/ergora/data/presets/workflows/ergora-training-proposal/skills/ergora-bottleneck-optimization/SKILL.md#specialist-execution-and-supervision)。

监管者在已授权范围内安排执行成员。其他 AI Agent 在原项目／协作周期内至多创建一个不同的直接助手，该助手不能再创建 AI 子代理。继续同一助手仍消耗原预算。任务编号、名称、重试、工具／后端别名或助手已结束都不能重置名额。更多需求回交原监管者准入或排队。训练 rank、DataLoader worker、系统进程和可信执行者已冻结的图分支沿用各自的运行合同。启动权限与实际强制范围以原授权和运行能力为准。

审查以[当前阶段／目标与可整合批次](../../../review/invoke-and-aggregate.md#choose-review-scope-and-granularity)为单位：日常由负责当前工作的专家按需自检，优化阶段关注正确性、真实性能证据、资源与停止边界，不为无关风格／目录／抽象打磨额外阻塞试验。准备、环境绑定、文档或小修不各自安排常驻审查者；整合／合并时才按需审查完整目标批次，原生 FinalReviewDAG 是该批次的一套门禁，不再叠加同轴外部审查。保留实际必需测试、质量与证据契约，同批次修复／复核后释放审查者，状态记录不递归审查。

|组合|当前随包根身份|默认关系与使用范围|
|---|---|---|
|repository-governance|`ergora-governance-template@1.1.8`|知识地图、架构回归两个专家并行，再经可信integrate/verify接三审查；包含独立盘点／规划与原工作／审查阶段|
|large-change|`ergora-large-change-template@1.1.10`|接口合同 → 服务端与客户端并行 → 集成/兼容验证 → 三审查；包含独立盘点／规划与原工作／审查阶段|
|training-optimization|`ergora-training-proposal@4.2.12`|只读提案；独立设计与诊断并行，诊断在派发前检查原 FlowMap。支持独立图和显式单叶调用。 [提案输入与原证据](../../../training/proposals.md#organize-complete-proposals-around-bottlenecks)|
|refactoring|`ergora-refactoring-template@1.3.8`|普通父 → 原生六阶段：准备 → rewrite／compatibility串行工作 → 三类独立审查；正式task type沿用large-change，显式schema8／input12|
|optimization-performance-diagnosis|`ergora-opt-performance-diagnosis-proposal@1.2.2`|同症状复现与兼容报告 reader；只读 design／profile→measurement 提案叶，原 runner 保留实验执行|
|training-flow-map|`ergora-training-flow-map@1.1.1`|只读 `root/map` 分别产出算法／执行依赖图、状态生命周期和可证伪冗余假设；不自动运行后续专家或训练|
|evidence-report|`ergora-evidence-report@1.0.2`|只读 `root/author` 生成来源绑定的 Markdown／静态 HTML 报告；原证据、运行记录与独立审查／release 保持|
|optimization-report|`ergora-evidence-report@2.0.2`|原只读作者接口，新增专门优化 Skill 与完整模板 context：源码流程／冗余 → 可比结果 → 诊断／决定；仅使用明确提供的证据|
|pretraining-review|`ergora-pretraining-review@1.1.7`|原通用三路与预训练专家并列 required／all-join；共享后端说明由四叶继承；领域叶可独立调用|
|posttraining-review|`ergora-posttraining-review@1.1.7`|原通用三路与后训练专家并列 required／all-join；共享后端说明由四叶继承；领域叶可独立调用|

开发delivery祖先提供语义归属、当前接口、可达失败验证、最小提交范围和候选绑定证据的共同规则；各写者在返回前复核自己的改动。开发组合共用 `ergora-delivery-review`，它引用结构、正确性、测试价值三份可单独使用的子模板。每份专家有独立初始指令、专长和Skill，沿自己的结构父链完整装载资料。全部内置专家默认Codex gpt-6.2-sol并按[定义下限](../agents.md)验证model／effort；逐实例覆盖须满足下限。实际可用性和认证仍由调用准入核验；同后端选择需遵守多样性政策并记录原因。

在明确的preview grant下，按[完整组合分享](#保存和分享完整组合)执行`prepare-manifest`，把上面的根ID/版本换入即可。开发正式选择沿[work-units-v2](contracts.md#专长执行者与原工作单元)，使用`root/development/work`和`root/development/review`；unit ID映射真实执行叶，例如`contract`→`root/development/work/contract`。原`templates copy`取得的领域input包含对应unit ID、路径和依赖；改变原units关系时，应同时修订对应工作子模板。workspace写调用仍要求每个writer显式选择可信current-container；导入组合不会自动选择此边界。

`refactoring`使用[原生六阶段选择](../../development/preparation.md#使用重构配方)：实例为`root/development`，work／review在其内部，准备阶段也由独立专家会话承担。其[完整任务示例](../../../../examples/composition/refactoring/task.example.json)提供schema8、unit分配、预算与显式writer信任；需要替换真实baseline、caller、范围、验收和manifest。父Skill提供目标仓库规范、真实调用者与测试接缝指导；原任务类型保持。catalog的`development-v5`是既有页面的开发类别标签，真实执行合同由任务定义选择；该标签不会把新任务降为input5。图形任务向导可按下文选择原生六阶段、准备阶段与预算，并沿当前schema8生成input12合同。

训练组合的`root/analysis/design`、`root/analysis/profile`、`root/kernel/assess`和`root/measurement/review`可按[单叶调用](leaf-calls.md#调用一个准备好的叶子)使用；操作者需要在任务文件中提供完整workload、baseline和相应前驱输出。独立`run-input`不执行图前驱。生成的提案/代码文本及模型review不是实验结果或采用批准，真实CPU/GPU、Forge候选和测量仍按[训练手册](../../../training/overview.md)使用原可信runner/gate。目录中的`runtime`只描述本发行支持的使用范围，不表示后端、服务或硬件已经就绪。

当前训练根包含源码图谱、跨域规划与诊断、kernel 实施方案评估、独立测量审查和库／环境选择。叶子保持只读、shell=false、network=[]。Skill 附件调用使用受支持的 task-MCP。[独立提案图](../../../training/proposals.md#organize-complete-proposals-around-bottlenecks)在派发诊断前检查原 FlowMap，保留独立设计的结果。Kernel 和测量审查沿用操作者提供的证据。异构验证、环境兼容和实际收益仍由各自的原证据确定。

## 运行示例

先按[使用手册](../../install/linux.md)安装基础 Ergora；这些命令不需要模型密钥、Web、工单或 Temporal 服务。示例文件在仓库 [examples/composition](../../../../examples/composition/README.md)。在仓库根执行，导入依赖后再导入引用它的工作流：

```bash
ergora agent definition import examples/agents/kernel-implementer
ergora agent definition import examples/agents/architecture-reviewer
ergora agent definition import examples/composition/agents/correctness-reviewer
ergora agent definition import examples/composition/agents/test-value-reviewer
ergora composition check examples/composition/parallel-review --material
ergora composition import examples/composition/structure-review
ergora composition import examples/composition/correctness-review
ergora composition import examples/composition/test-value-review
ergora composition import examples/composition/parallel-review
ergora composition import examples/composition/kernel-delivery
ergora composition list
ergora composition show kernel-delivery 1.0.0 --material
ergora composition preview kernel-delivery 1.0.0 --grant examples/composition/preview-grant.json
ergora composition export kernel-delivery 1.0.0 ./shared-kernel-delivery
```

`check` 检查单包的 schema、资源、路径和本地图；不解析库中依赖，也不创建 State。`import` 还解析完整依赖树并检查端口、继承、权限与本定义预算；引用缺失或摘要漂移会失败。`preview` 额外使用明确提供的项目授权上限，读取库但不创建或迁移 State。`show` 展示本包材料；预览里的叶子 `resources` 和 `prompt` 才包含整条祖先链的完整静态材料。

示例展开成10个实例：一个根、一个执行 Agent、一个总审查工作流、三个审查子工作流、三个审查 Agent 和一个 all-join。`root/implement` 在 `root/review` 前完成；总审查内三支就绪分支可并行，`root/review/gather` 等待全部三支。相同子工作流可引用多次，每次产生不同路径实例。

示例 Agent 使用 Codex 与 Claude Code，预览只显示请求的后端，不检查安装或认证，不承诺模型效果或错误相互独立。持久改变后端需创建新Agent版本并更新沿途引用；单叶调用也支持明确记录的本次覆盖。项目角色调用另见[Agent入口](../../agents/backends.md)。

## 保存和分享完整组合

导入示例后，可以把根工作流及全部递归依赖一起保存：

```bash
ergora composition prepare-manifest kernel-delivery 1.0.0 --grant examples/composition/preview-grant.json --directory ./kernel-delivery-manifest
ergora composition verify-manifest ./kernel-delivery-manifest
ergora composition verify-manifest ./kernel-delivery-manifest --material
```

分享整个输出目录，接收者安装基础Ergora后即可运行`verify-manifest`，无需先导入同一组定义、建立项目或启动服务。包内的`manifest.json`记录根精确版本、所供grant和完整图摘要；`composition.json`保存全部稳定实例、具名端口、依赖/汇合关系、祖先资源来源、完整静态提示、权限与预算；`assets/`带有全部精确引用的定义、Skill目录及上下文。重复引用只复制一份定义，实例状态仍按各自路径区分。

核验会从包内资源重建完整图并逐字核对身份，拒绝缺失、篡改、多余文件或未引用定义；它不依赖原始库位置或当前后端catalog。新准备仍检查当前定义准入，目录已存在时不覆盖。与单叶输入共用完整资产/容量检查和原子发布，超出10 MB或500文件的完整包明确拒绝。

需要使用其中的叶子时，准备UTF-8任务文件后直接从完整包生成输入：

```bash
ergora composition prepare-from-manifest ./kernel-delivery-manifest root/review/structure/review --task ./review-task.txt --directory ./prepared-review --max-prompt-bytes 30000
```

这一步会重新检查当前定义准入及整图身份；旧包能核验不代表现在还能调用。生成的输入沿后文`check-input`/`run-input`使用，不执行图前驱或端口，也不会创建State或依赖接收者的原始定义库。

这是完整**静态**材料，`execution_authorized`为false；它没有操作者任务正文、未来父结果、候选批准或运行会话。正式任务仍须经过创建、原owner批准和运行准入，当前支持形状见[正式审查组合](../../development/preparation.md#为正式任务冻结审查组合)。若希望State的完整备份同时保存该包，将输出目录放在自己的State数据目录下；否则单独保存/复制整个包，不能只留下`manifest.json`。`--material`会返回所有叶子的完整静态材料，省略该参数时只返回身份与清单。

### 固定当前预览到持久控制目录

在页面的“Agent 与组合库”中，先预览精确工作流及显式上限，再点击“保存当前预览为完整 manifest”。页面保存的是当前所选根，编辑缓冲和比较目标不包含在内。成功结果给出完整包绝对路径、`digest`及原`preview_sha256`；正式任务定义使用此`path`与`digest`。页面的“下载 composition-preview.json”仍只用于查看，不能代替完整目录。

CLI使用相同用例，必须明确提交已检查的预览摘要：

```bash
ergora composition preview kernel-delivery 1.0.0 --grant examples/composition/preview-grant.json
# 将上一步实际返回的 preview_sha256 填入，不使用示例占位符创建任务。
ergora composition freeze-manifest kernel-delivery 1.0.0 --grant examples/composition/preview-grant.json --preview-sha256 PREVIEW_SHA256
ergora composition show-manifest PREVIEW_SHA256 --material
```

完整包位于当前控制目录的`composition-manifests/PREVIEW_SHA256/`，沿原`--home`/`ERGORA_HOME`及平台默认持久目录；控制目录完整备份也会包含它。首次保存重新执行原准入并核预览摘要，上限或定义身份变化须重新审阅。相同摘要重试会核验原完整包，不覆盖已有目录；违反原完整核验的文件/定义/材料身份会明确拒绝。空目录正常复制保留，但沿原摘要合同不计入digest，稳定增删空目录不会改变身份。

保存回复丢失时，先保留原摘要并用“按当前摘要读取已保存包”或`show-manifest`查询；刷新后可重新预览同一精确版本及上限再读。读取不要求源库或当前后端可用，可独立执行`show-manifest`或`verify-manifest`，不能把历史可读等同当前可执行。HTTP对应`POST /api/composition/manifests`（原preview请求另加`preview_sha256`）、`GET /api/composition/manifests/PREVIEW_SHA256?material=true`；写入仍要求本地同源与原请求头。保存不创建项目、任务、批准或Agent调用。

## 在正式任务页面选择组合

先完成[项目登记](../../projects/registration.md)，再打开“正式任务”→“预览与创建”。原“项目角色”入口保持使用项目绑定，不自动套用定义库中的组合。

1. 载入已登记开发模板或兼容草稿，填写任务ID、工单和完整输入。选择“本任务 Agent 来源”：仅组合审查、组合执行与审查，或原生六阶段（Linux／WSL2）。训练优化仍使用独立入口。
2. 粘贴前文保存包返回的`manifest.preview_sha256`，点“读取完整 manifest”。此摘要不是manifest目录digest；页面从当前控制目录读取并核原完整包，再显示根身份和manifest digest。读取历史包不等于允许今天的正式调用。
3. 选择完整实例路径的审查子流程。执行与审查组合还要选执行子流程，点击“从当前输入载入工作单元”，逐个选择对应执行Agent。内置开发组合通常为`root/work`和`root/review`；单元ID对应同名work叶子。修改work子流程后重新载入分配；载入失败保留旧输入及分配，原任务预览会核全部unit和依赖。
4. 审查者可沿用精确定义的后端请求；覆盖时选择后端、配置模型等字段并写明理由。执行者须逐一显式覆盖；可写模式沿原后端合同要求可信Linux绑定，目前由Codex的“执行边界”选择“已信任的当前容器 / 用户”。页面不会从静态定义自动选择这一信任。认证仍由外部工具配置提供，不在此填写密钥。其他后端或不支持的模式会由服务端明确拒绝。
5. 默认优先不同执行/审查后端；同后端回退须填写策略说明。可明确要求不同后端或允许相同后端，仍沿原diversity合同。不同名称或不同模型选择本身不证明独立错误概率。
6. 原生六阶段可选择根图或嵌套六阶段调用，再选择盘点和计划 Agent，填写准备模式、仓库相对路径（每行一个）和总时间／预留清理时间／模型调用次数。准备成员也可逐实例覆盖后端。内置`refactoring`选择`root/development`、`root/development/preparation/inventory`和`root/development/preparation/plan`，执行／审查分别位于`root/development/work`和`root/development/review`；用[完整示例](../../../../examples/composition/refactoring/task.example.json)适配真实输入与工作单元。可在“本任务资料来源”追加[精确项目记忆和活动Skill](../../development/preparation.md#为正式任务选择项目记忆与活动-skill)：显式读取目录，填写新根版本并勾选；默认仅继承全部祖先资料，不自动召回。点“准备原生六阶段”，核完整输入后明确“确认授权准备（开始预算计时）”；`prepared`后才可预览。此时预算已开始，读取和预览均不续期；修改已授权输入须换新任务ID。授权前可“下载完整授权输入”，准备结果或未知结果也提供此下载。关闭或刷新页面会释放表单；按ID查询只读状态、不装载原表单，可用下载文件沿原CLI的`task preview --definition ... --revision ...`及双摘要`task create`继续。响应丢失先“读取原准备记录”，或重新打开“按ID读取准备记录”，不要自动重发授权。
7. 点“预览冻结合同”，审阅服务端完整冻结文件与全部准备／执行／审查成员、六阶段父链及原预算期限，再“确认创建冻结合同”。页面保留原准备和预览两个摘要；可选来源快照与六阶段组合可同时使用。创建只发布合同，不启动、批准或执行。后续按[正式操作顺序](../../development/tasks.md#正式任务的操作顺序与恢复)启动及批准原计划。旧仅审查／执行组合无需授权准备步骤。

字段变化使旧任务预览失效，迟到manifest或预览回复不能恢复旧选择。读取/预览失败保留输入；创建发出后锁定原合同。创建回复丢失时按页面保留的原任务ID只读查询原创建记录，再决定是否恢复，不能换ID重发。组合、后端覆盖和理由只属于本次冻结任务，不修改模板或项目默认绑定；各祖先资料、权限和candidate/批准仍由原所有者核验。当前表单随对话框关闭而释放，关闭前另存任务输入；定义库中的完整manifest仍持久保存。

## 可嵌套工作流定义

基础安装可使用`ergora composition`检查、导入、分享与预览版本化Agent/子工作流DAG。叶子预览包含全部祖先静态材料、权限链、具名端口和全局预算；示例、操作顺序及范围见[工作流组合手册](../../../definitions/workflows/compose.md)。静态预览不启动Agent；正式运行继续使用原六阶段与批准流程。

### 在页面浏览与预览定义

运行`ergora serve`后打开“Agent 与组合库”，无需先注册项目。这些库属于当前持久控制目录，项目切换不会更换它们。

1. 在“内置领域组合”明确导入所需组合；重复导入同一版本保持同一身份。可分别导入治理、大型开发和训练提案。
2. 从Agent或子工作流列表选择精确版本。详情展示标准定义、自身完整资源、包文件身份和默认后端请求；Skill附件的完整包可通过CLI的`export`分享。页面下载的“定义 JSON”只含定义正文，不能替代完整包。
3. 选中工作流后检查“静态预览上限 JSON”，再点“预览完整组合”。初始值来自根定义；修改只影响这次静态校验，不授予项目权限。错误会显示在页面，修改后的文本仍可继续编辑。
4. 在已发布嵌套关系图中选择实例，或用键盘操作下方实例表的按钮，查看完整祖先资源、来源、权限、端口、预算和装配提示。嵌套框/虚线依赖/蓝色具名数据分别表示三种关系；完整路径区分重复引用。“打开所选精确定义”及“打开结构父定义”回到对应编辑表单。可下载精确预览JSON，供检查与比较。
5. 审阅后点击“保存当前预览为完整 manifest”，保存当前根及全部定义和 Skill 附件到持久控制目录。成功结果的`path`和`digest`可填入正式任务定义；保存不会创建或启动任务。回复丢失时先“按当前摘要读取已保存包”，源库不可用时可用`ergora composition show-manifest PREVIEW_SHA256`独立核验；[完整步骤](../../../definitions/workflows/compose.md#freeze-the-current-preview-into-the-persistent-control-directory)。

导入不安装或认证后端，也不启动任务或服务。预览显示的后端字段是请求；实际调用仍要通过能力准入和认证。选择精确版本后，可在“编辑定义并派生新版本”中修改字段或 JSON/YAML，明确应用、检查并发布新修订；原附件和旧版本保持。完整步骤与浏览器缓冲边界见[Agent编辑](../../../definitions/agents.md#edit-a-specialist-agent-in-the-console)和[工作流修订](../../../definitions/workflows/revisions.md#revise-workflows-on-the-page)。图显示已发布版本，草稿不会自动进入图；可独立折叠子工作流、按职责/专长/后端查找并展开祖先定位，摘要线可回查完整原端点。布局/折叠/查找与合同分开，刷新重置，组件缺失时表格继续可用。操作见[关系图手册](../../../definitions/workflows/revisions.md#view-published-nested-relationships)。选择比较目标后，可用同一显式上限[比较两个已发布组合](../../../definitions/workflows/revisions.md#compare-two-published-compositions)，逐路径核对引用/权限/材料等差异并下载两份完整preview。完整manifest可在此页保存，再按[任务页面组合选择](../../../definitions/workflows/compose.md#select-a-composition-on-the-formal-task-page)读取原摘要、分配工作单元并设置逐实例后端；原生六阶段入口还可配置盘点／计划Agent与预算，显式授权准备后再预览、创建。原项目角色入口继续可用。

修改 instructions/context、完整Skill目录及普通附件可使用[CLI资源修订](../../../definitions/resources.md#revise-complete-resource-files)：固定原包，预览完整差异及建议摘要，明确接受同一候选，再检查和发布新版本。两类定义共用同一合同；二进制、文件执行位和空目录保持明确，历史文件可按字节窗口读取。页面也可在“资源与附件编辑”中完整读取/上传、暂存文件操作、预览差异并明确采用摘要，再检查和发布；详见[页面资源步骤](../../../definitions/resources.md#edit-resources-and-attachments-in-the-console)。正文、操作和接受身份共同进入历史，未应用字节独立保留；下载编辑缓冲不包含未编辑原包。

修改嵌套组合时，按[依赖链步骤](../../../definitions/workflows/revisions.md#publish-resource-revisions-through-the-complete-dependency-chain)先发布专家和子工作流，最后发布新根；从新根重新准备输入，旧快照继续保留旧材料。需要确认附件实际送达模型时，按[完整读取核验](../../../definitions/workflows/leaf-calls.md#verify-complete-attachment-reads)检查本次原生 list/read 证据。

## 导入领域专家组合

基础安装已带治理、大型开发和训练提案的专家/子工作流默认包。运行`ergora composition presets`查看实际使用范围，`ergora composition install-preset large-change`导入全部精确依赖。详情、节点关系、独立后端选择及分享见[内置领域组合](../../../definitions/workflows/compose.md#use-bundled-domain-compositions)。静态导入不选择可信容器、不启动服务或批准任务；正式开发继续走上文原任务流程。训练提案与[可信实验执行](../../../training/overview.md)分别使用。

修改父子权限时，按[联合修订步骤](../../../definitions/workflows/revisions.md#jointly-revise-parent-and-child-permissions)从内层到根逐版本发布，最后给出明确grant并检查实际调用能力。并行增加同一专家的多个实例时，使用不同节点ID和完整all-join；不同审查职责须另发子模板版本，见[重复实例与后端选择](../../../definitions/workflows/revisions.md#repeated-instances-responsibilities-and-backend-selection)。

### 在页面导入完整工作流目录

在“Agent 与组合库”点击“导入工作流目录”，填写控制台机器上包含 `workflow.json` 与全部自身资源的目录（可使用下节复盘候选的导出目录），核对显示的控制目录后明确提交。此库在同一控制目录共享，不依赖当前项目。回执包含原 ID／版本／digest、定义及文件资源身份；保留回执，关闭窗口并点击本页的“刷新定义库”，再选择回执中的精确版本。顶部全局“刷新”不重新读取定义列表。

相同内容和版本保持同一身份；同版本不同内容被拒绝，需选择新版本。导入仅发布此根包，子工作流和 Agent 依赖须预先导入；原导入与预览均核查完整引用、祖先资源与权限。选择新版本后按上文原上限预览，再明确保存新 manifest；回退可重新选原版本／manifest，旧任务保留原材料。导入不自动选中新版、预览、保存或执行。

请求异常可能已经执行。先刷新定义库，选择原 ID／版本核对 digest；也可用 `ergora composition show WORKFLOW_ID VERSION --material` 读取原包。不要通过删除原记录强制重试。关闭窗口或离开来源页面后，迟到回复不会操作后来窗口；重新打开后须重新核对原记录。HTTP 等价入口是 `POST /api/workflow-definitions/import`，正文 `{"directory":"/path/to/workflow-bundle"}`，沿用同源保护和 `X-Ergora-Request: 1`。
