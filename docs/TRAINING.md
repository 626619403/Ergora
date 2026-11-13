# 训练优化与持续改进

训练模板负责固定 workload、实验输入、正确性要求、基线和候选证据。实际训练、kernel 生成及设备访问由所选工具和项目环境完成。Ergora 的项目记忆、Skill 候选和资料观察可以先独立使用，不代表模型训练或性能已经得到改善。

专家组合的安装、只读叶准备、后端选择和开发交接可沿[三模板入门旅程](TEMPLATE_WALKTHROUGHS.md)操作；真实实验继续使用下文的可信runner及精确证据批准。

训练领域组合仍提供只读proposal叶，由操作者提供workload和前驱资料；开发任务的`work-units-v2`不会自动调度训练实验或批准候选。全部祖先Skill/上下文仍须完整交付，真实设备运行和结果采用继续按本手册的runner/gate处理。

Windows 原生可设计训练模板、普通调用提案角色并管理记忆 / Skill；带完整Skill附件的组合单叶使用Linux task-MCP，须在WSL2/Linux运行。ForgeKernel、mini 驱动及完整参考实验执行同样使用WSL2/Linux，可信参考执行器还要求Linux容器。原生安装不会配置CUDA、GPU或这些参考服务，详见[Windows手册](WINDOWS.md)。

## 准备工作

```bash
ergora templates copy training-optimization ./training-task
ergora project add my-project --repo "$HOME/projects/my-project"
```

也可在控制台“工作流设计”中选择“训练优化实验”，预览和下载文件。模板包括 `workload-contract.md`、`baseline.json`、`experiment.json`、runner 示例、hypothesis、result、evidence、attestation 和负结果记录。先将其中的占位内容替换为真实配置，再批准合同与精确实验。

固定模型 / 代码版本、数据身份、随机种子、数值精度、并行布局、设备、计时区间、重复次数及正确性阈值。训练环境与数据由项目准备；安装控制台不会安装 CUDA、PyTorch 或申请 GPU。性能候选同时满足项目正确性和质量约束后才有比较意义。

## 参考实验执行

完整参考发行提供 `agentflow training`、可信 runner 与 perfctl 门禁。按 [完整训练优化参考手册](../src/ergora/data/reference/platform/docs/TRAINING.md) 的参数执行：

```text
init / runner-add → prepare → worker-start → start
→ 选定精确实验并以 manifest SHA 执行 run-local
→ 可信证据与统计复验 → 人工批准 evidence SHA
→ 该项目的集成 / 复验任务
```

`run-local` 逐实验显式执行；没有常驻训练队列消费者。审批、结果、取消和恢复沿用原实验身份。未知结果需要对账，不直接用新 ID 重跑。候选模型或 Agent 的报告不能替代可信 runner 的验证；实验失败和负结果也要保存。

### 预览与初始化基线

先登记选择 `training-optimization` 的真实Git项目和参考安装，填写模板的 `baseline.json`。`commit` 必须是该仓库内已存在的完整提交，配置与workload摘要须真实；登记不证明这些测量或质量已通过。

```bash
ergora training baseline-preview my-project --baseline ./training-task/baseline.json
# 核对返回的完整 baseline、project_revision 和 baseline_sha256
ergora training init-baseline my-project --baseline ./training-task/baseline.json \
  --revision REVISION --baseline-sha256 PREVIEW_BASELINE_CONTENT_SHA256
ergora training list my-project
```

控制台“训练实验”→“当前基线”→“预览与初始化基线”支持同一流程：粘贴完整JSON、预览、核对完整资料与项目修订，再粘贴预览的内容SHA并确认。修改JSON或切项目会使旧预览失效。CLI／页面／`POST /api/projects/{project}/training/baseline-preview`（`baseline`对象）和`POST .../init-baseline`（再加`revision / baseline_sha256`）共用应用入口。

内容SHA由完整对象的canonical JSON计算，保留额外说明字段、忽略键顺序与排版；使用预览返回值，不能拿文件的 `sha256sum` 代替。回执的 `current_baseline_file_sha256` 则是原文件字节SHA。CLI原始输入文件和原生序列化文件各最多1MiB；HTTP沿控制台既有4MB请求上限，解析后的baseline还须满足原生1MiB容量。预览和初始化无需Temporal SDK、服务或GPU；实际原子初始化使用原perfctl锁，只支持Linux／WSL2，Windows原生可预览。

预览的`not_initialized`表示尚无原基线，`already_initialized`表示已有完整同内容，`conflict`表示不同内容。初始化成功返回`initialized`或`already_initialized`，CLI退出0；错误／冲突退出非零。若初始化请求失联，先重新读取列表，再预览相同JSON并显式重试；已发布的同内容文件保持原字节，不另建基线，不覆盖不同内容。已有不同基线须走经过审阅的迁移流程，此入口不提供替换。

### 预览与登记可信 runner

在 Linux／WSL2 的控制环境安装 `ergora[temporal]`，填写训练模板中的 `runner-template.example.json`。预览与登记不需要 Temporal 服务或 GPU。runner 是可信操作者授权的逐实验命令，登记会保存 argv，但不会运行它；其 `{manifest}`／`{output}` 占位符由后续原生 `run-local` 执行时替换。

```bash
ergora training runner-preview my-project --runner ./training-task/runner-template.example.json
# 核对完整规范化 runner、project_revision 和 runner_sha256
ergora training register-runner my-project --runner ./training-task/runner-template.example.json \
  --revision REVISION --runner-sha256 PREVIEW_RUNNER_CONTENT_SHA256
```

`project` 必须是当前已登记项目，`repo` 必须指向其 Git 根；回执显示 resolve 后的规范路径。字段／argv／超时由原 `agentflow training runner-add` 的登记逻辑验证；`schema_version`须为整数1，超时为1–82800秒。预览只在隔离子进程的临时配置目录运行原登记器，不修改真实配置；确认后仍由原登记器不可变写入真实 `training-runners/RUNNER_ID.json`。共享配置目录中的ID全局唯一，建议使用带项目名称和版本的ID。

控制台“训练实验”→“可信 runner”→“预览与登记 runner”提供同一流程。HTTP为`POST /api/projects/{project}/training/runner-preview`（`runner`对象）及`POST .../register-runner`（再加`revision / runner_sha256`）。编辑或切项目使旧预览失效，确认内容SHA与原文件字节SHA分列；CLI原文件和原生序列化文件各最多1MiB，HTTP沿既有4MB封套。

预览状态为`not_registered / already_registered / conflict`；确认成功返回`registered / already_registered`。同内容重试保留原文件字节；同ID不同内容拒绝，更新命令需要新的已审阅ID。ID属于其他项目时拒绝且不展示其命令。回执丢失后先重新预览相同JSON，读取当前原件，再显式确认重试。实验 `prepare` 暂沿原生流程；登记不提交实验或批准训练合同。

## 在控制台查看原实验

先按[项目登记说明](USAGE.md)用 `project register` 登记已有 Git 项目，选择 `training-optimization`，并指定原生参考安装、配置和执行状态目录。已有原实验保留原目录与身份，无需导入另一份实验数据库。基础安装的列表／详情不要求启动 Temporal、MLflow 或 GPU；显式实时查询和完整训练执行分别按下文及上一节配置。

```bash
ergora training list my-project --limit 20
ergora training list my-project --limit 20 --after CURSOR_FROM_PREVIOUS_PAGE
ergora training show my-project EXPERIMENT_ID
```

打开控制台“训练实验”，可查看当前 baseline、分页原实验、完整 manifest／spec、当前 runner 与已冻结 job 请求、执行结果、门禁报告摘要、取消围栏、负结果及已有 MLflow run ID。完整原件附文件 SHA；当前基线不匹配会明确显示。页面同时列出本项目已有 Forge 候选记录，原生候选操作仍在工作流设计的训练模板中。

CLI、页面和 `GET /api/projects/{project}/training[/{experiment_id}]` 共用同一只读查询。列表的 `limit` 为每页实际检查的条目数，坏条目单列错误并继续推进游标，不会把后续实验藏起来。每个 JSON 文件最多读取 1 MiB；不接受越界路径或 symlink。文件正在发布时可能暂时缺失或不一致，重新读取即可核对；查询不修写原件。

原作业请求中的冻结 runner 或当前 runner 至少保留一份，用于核对项目和 Git 根；两者均缺失时明确报告归属无法核实。配置目录与状态目录可以共用同一文件夹，仍分别标记两种资料来源。

上述离线列表／详情保留 `runtime_status: not_queried`。开始文件存在不能证明作业仍在运行，未读到结果也不能判为失败；`recorded_result_state: SUCCEEDED` 只描述原执行结果，门禁仍可能失败。门禁摘要核对原 result 引用的 report SHA 与 manifest／job binding，但不会重新执行统计、正确性或质量评价。取消需在下述独立面板中明确确认，精确 evidence SHA 批准仍沿原 `agentflow training` 流程。

### 显式查询原运行状态

在运行 Ergora 的环境安装 `temporal` extra（从仓库安装时使用 `python -m pip install ".[web,temporal]"`），并按完整参考手册启动同一原生 Temporal 服务与训练控制 worker。已有实验无需重新提交；连接环境沿已登记的参考安装。

```bash
ergora training status my-project EXPERIMENT_ID --timeout 20
ergora training status my-project EXPERIMENT_ID --run-id ORIGINAL_RUN_ID
```

页面先选择实验，再点击“查询原运行状态”；`GET /api/projects/{project}/training/{experiment_id}/status` 使用相同语义，支持可选 `run_id` 与1–60秒 `timeout`。没有自动轮询。查询先核原manifest／spec及仓库归属，再核原工作流第一历史事件中的完整Experiment输入，固定实际run ID读取原Status或Outcome；SDK和新增使用的原生源码均须匹配受支持版本。

`runtime_status: queried`只证明本次取得绑定的原运行时事实，`not_found`仅来自原运行时明确的不存在答复。缺历史、输入或binding不一致、网络错误和超时会直接报错，不会回退为本地“运行成功”或自动重提。`GATE_FAILED`、`CANCEL_UNCONFIRMED`等原结果保留；控制工作流结束不等于外部作业已停止，集成票据也不表示自动合并。列表／详情的已保存证据仍单独显示，实时查询不会重算门禁、批准或修改训练原件。

### 提交已准备实验与原 ID 对账

先用原`init / runner-add / prepare`冻结真实实验，并启动同一原生Temporal／训练控制worker。`ergora training show`返回当前`project_revision`及`experiment.binding.manifest_sha`；确认完整原manifest与可信runner后，提交它们的精确身份：

```bash
ergora training submission my-project EXPERIMENT_ID
ergora training start my-project EXPERIMENT_ID --revision REVISION --manifest-sha256 EXACT_MANIFEST_SHA256
ergora training submission my-project EXPERIMENT_ID
# 已有意图：使用上一步返回的完整 intent_sha256
ergora training resume-start my-project EXPERIMENT_ID --revision REVISION --intent-sha256 ORIGINAL_INTENT_SHA256
```

控制台在实验详情只读取本地提交记录。首次提交需粘贴完整manifest SHA，继续／对账需粘贴原intent SHA；项目revision变化时重新读取。HTTP沿相同应用入口：`GET .../training/{experiment}/submission`、`POST .../start`（`revision / manifest_sha256 / timeout`）及`POST .../resume-start`（`revision / intent_sha256 / timeout`），实时操作timeout为1–60秒。默认导航没有start、自动轮询或自动重试。

CLI的`start`／`resume-start`仅在返回`submitted`时退出0；`prepared`／`unknown`／`rejected`退出1并打印原JSON，不能据此继续执行训练。`submission`是只读观察，成功读取退出0；它的退出码不表示提交成功。`submitted`也仅表示原控制工作流已确认接收，不代表训练已运行或通过。

提交预检要求已准备的合同、当前匹配baseline、同仓库的可信runner、存在的原Git提交和原比较器，拒绝已有job／执行／fence记录。意图保存原合同、baseline／runner及文件摘要，位于已登记原执行state的`ergora/training-submissions/`；它只是操作checkpoint，实验、job、统计、批准与调度仍属于原owner。不要删除这些记录来绕过未知状态。

|本地提交状态|含义与后续|
|---|---|
|`not_recorded`|尚无控制面意图；只能在确认精确manifest后提交。已有原生运行不会被认领。|
|`prepared`|意图已保存，尚无发送attempt；可显式`resume-start`继续一次原提交，发送前重核原来源。|
|`unknown`|已落盘attempt但未取得回执；`resume-start`仅按原workflow ID查找，固定实际run并核完整输入及意图memo。明确NOT_FOUND也不会清attempt或重发。|
|`submitted`|原start返回run ID，或已核原历史／memo补回原run回执；不代表训练已执行、门禁通过或已经采用。|
|`rejected`|存在无本意图的运行，或同ID竞争被原客户端拒绝；保留冲突记录，不认领、不重发。|

丢失回复、超时或进程停止后，先读取`submission`，不要改实验ID、重新`prepare`或直接调用原start以绕过记录。attempt后对账沿意图中的原spec；后来的baseline／runner变化不把它重解释为新发送许可。输入或memo冲突、缺历史、RPC错误会保留unknown并明确报错。旧注册／执行目录变化须恢复原登记后处理原意图，不能把旧记录搬到新home认领。

提交只排队原控制工作流；实际runner仍须按原`agentflow training run-local EXPERIMENT_ID --confirm-manifest-sha ...`逐实验执行。原evidence SHA批准和集成票据继续使用原训练协议；`ergora task`只管理开发Task。

### 取消原运行与分别观察停止事实

先确认 `training submission` 返回 `submitted` 和完整原 `run_id`；未知 start 必须先按上一节恢复。实际取消与原执行器观察要求 Linux／WSL2、`temporal` extra 和同一原服务／训练控制 worker。取消请求使用稳定 ID；保留这个 ID，失败后继续查询或恢复同一请求。

```bash
ergora training cancellation my-project EXPERIMENT_ID stop-one
ergora training cancel my-project EXPERIMENT_ID stop-one --revision REVISION --run-id ORIGINAL_RUN_ID --reason '停止本次实验'
ergora training cancellation my-project EXPERIMENT_ID stop-one
# 使用取消记录中的原 intent_sha256；不要使用 start 的意图 SHA
ergora training resume-cancel my-project EXPERIMENT_ID stop-one --revision REVISION --intent-sha256 ORIGINAL_CANCEL_INTENT_SHA256
ergora training stop-status my-project EXPERIMENT_ID --timeout 20
```

页面先读取原提交回执，再填写请求 ID 并点击“读取本地取消记录”。首次取消需粘贴完整原运行 ID 并填写原因；已有意图需粘贴原取消 SHA。取消和“读取停止事实”都是显式操作，没有自动轮询。当前 manifest／baseline／runner／spec 缺失时，已有原提交与取消仍按冻结的原输入恢复；详情读失败不会隐藏这些操作。

|取消记录状态|含义与后续|
|---|---|
|`not_recorded`|该请求 ID 尚无意图；确认原运行和原因后创建。|
|`prepared`|意图已保存但尚无发送记录；`resume-cancel` 可显式继续一次原请求。|
|`unknown`|发送前 attempt 已保存，投递未确认；恢复只查固定原 run 的完整信号历史，不重发。缺事件、NOT_FOUND或RPC错误不清除原 attempt。|
|`requested`|原信号已取得发送回执，或历史中匹配了完整 binding／reason／独立操作 SHA；它只证明投递。|
|`already_closed`|原控制工作流已结束，记录 `signal_delivery: not_sent`；没有发送取消，不能称已停止。|

本地 `cancellation` 读取不需要 SDK 或运行中的服务，成功读取退出0。`cancel`／`resume-cancel` 仅在 `requested`／`already_closed` 时退出0，其他记录状态退出1；该退出码不能作为外部停止证明。实际信号由原客户端检查 binding 后发送，记录固定原 start 意图、原 run、原因和操作人；同一请求不得改变原因或冒用操作人。意图、发送 attempt 和回执保存在原执行 state 的 `ergora/training-cancellations/EXPERIMENT/REQUEST_ID.*.json`，须与 `ergora/training-submissions/`、原 job／fence 和 Temporal history 一起保存。不要换 ID 或删除 checkpoint 绕过未知投递。

`stop-status` 是一次只读观察，分别返回 `control`（原 Status／Outcome）、`executor_observation`（原 adapter 的作业观察）和 `fence_recorded`；读取成功退出0。原 `CANCEL_UNCONFIRMED` 与后来本地 `CANCELLED` 可以同时存在，页面会分别保留。`QUEUED`／`RUNNING`、缺作业、未读到 fence 或控制工作流结束都不能合成为“已经停止”。此查询不发信号、不写 fence、不执行 runner，也不重新评价或批准候选；仍需操作者核对真实设备／远端作业。

HTTP 使用相同入口：`GET .../training/{experiment}/cancellations/{request_id}`；`POST .../cancel`（`revision / request_id / run_id / reason / timeout`）；`POST .../resume-cancel`（`revision / request_id / intent_sha256 / timeout`）；`GET .../stop-status?timeout=20`。实际操作的 timeout 为1–60秒。Windows 原生仅提供本地取消记录读取，实际取消和 executor 观察使用登记的 Linux／WSL2 环境。

## 从专家提案填写原实验合同

先完成下文的[专家提案及手动交接](#可选的实验专家提案)，保存完整manifest、所选叶input、原result及实际后端记录。原result的自由文本供人审阅，不能直接当作`experiment.json`。以下步骤适用于各优化方向；真实文件仍使用`ergora templates copy training-optimization`给出的原模板，执行命令沿[完整参考手册](../src/ergora/data/reference/platform/docs/TRAINING.md)。

1. 明确真实项目、优化目标和允许改变的语义，分别选定基线负责人、候选作者、受信runner、独立评价者及采用负责人。design／profile完整原结果先交kernel；measurement接收全部相关原结果和实际实验材料。三叶方向没有kernel时直接交接两份分析。
2. 按下表填写合同。每个值记录真实来源和人工决定；缺少实际commit、配置、数据、初态或验收方法时先补齐，保留未验状态。提案中的示例数值、搜索成本估算或自生成PASS不进入真实测量。
3. 人工审阅范围、检查、质量和资源预算后，才设置`contract_approved: true`；登记真实baseline与runner，再运行`prepare`。它检查canonical提交与别名、仓库commit、当前基线和比较器，补充执行字段并冻结原字节。后续确认它返回的`manifest_sha256`，不要用提案、draft或重新排版JSON的SHA代替。
4. 原runner以精确manifest执行，生成可信证据、独立检查／审查／质量与配对比较。measurement可解释这些原材料并提出缺项；其`approve`不代替实验门禁或人工采用。最后按原`evidence SHA`批准，再交该项目的开发集成／复验任务。

|目标文件／字段|来源及决定|
|---|---|
|`workload-contract.md`的目标、硬件、数据、更新、计量、停止／恢复、资源授权|真实项目说明与原配置／报告；profile指出缺口，design给有限建议，操作者确认有效源样本、rank范围与实际optimizer更新语义。Markdown不会自动变成workload指纹。|
|`baseline.json`的`baseline_id / commit / config_sha256 / workload_fingerprint / evidence_uri / quality_scope`|基线负责人确认的精确commit、最终有效配置、工作负载身份、原证据位置和质量适用范围。`baseline_ok`核前四项与experiment匹配；证据URI和质量文字仍须人工核查。|
|`experiment.json`的`schema_version / experiment_id / baseline_id`|沿原schema 1和唯一实验身份登记，关联同一baseline。结果不明先按原ID对账；改变已绑定内容须按原流程创建可追溯修订。|
|`track / allowed_changes`|按实际变化选择E／N／A并列精确边界。kernel、packing或低精度的方向名称不能自动决定分类；提案建议不授予修改oracle、阈值或受信runner的权限。|
|`owner / author / contract_approved`|实际负责人／候选作者和人工合同决定。它们不是模型后端名称；独立review的`reviewer_id`须区别于作者，身份真实性由受信流程负责。|
|`baseline_commit / candidate_commit`|真实runner仓库中的完整Git提交；`prepare`补同值`baseline_sha / candidate_sha`，已有别名冲突会拒绝。设计公式、生成代码片段和原result摘要都不是候选commit。|
|`workload_fingerprint / environment_fingerprint`|项目固定的工作负载与真实环境身份，包括有效batch／token、precision、软件／硬件／mesh等实际条件；保留用于计算指纹的原记录。内容和归一化规则由项目定义，平台不自动探测或证明其真实性。|
|`dataset_manifest_sha256 / initial_checkpoint_sha256`|真实数据manifest及初态产物摘要，保存可复现来源与内容范围；不能填示例、文件名的SHA或未实际使用的checkpoint。|
|`base_config_sha256 / candidate_config_sha256`|两臂实际最终有效配置摘要，包含所选版本中真正生效的开关；配置能解析和提案写了参数不证明执行时使用过。|
|`validation_contract_sha256 / checks_required`|项目独立oracle、容差、shape／stride／梯度／RNG／全rank／恢复等所需覆盖及其固定合同。检查列表非空且唯一；模板中的JVP等仅为示例，按真实任务选择充分检查，不能为迁就PASS删掉必要项。|
|`quality_required`|显式布尔值；N／A要求true。E是否需要任务质量证据也由项目合同决定；短loss、单算子误差或一次forward不自动替代训练／服务质量。|
|`comparison_tool_sha256 / performance_policy`|核实际固定`compare_runs.py`原字节SHA；批准实际归一化单位、配对重复／统计／阈值。原gate重算并核两臂代码、配置、环境、数据和初态；局部kernel speedup或Amdahl估算不能充当整体配对测量。|
|runner的`schema_version / runner_template_id / project / repo / command / timeout_seconds`|原runner schema 1、真实项目Git根和受信argv；`{manifest} / {output} / {baseline_repo} / {candidate_repo}`由原执行器提供。使用已验证环境与资源权限，保留唯一作业／rank／取消所有者。|
|`prepare --max-run-seconds`及其补充字段|该值是排队加执行窗口，至少覆盖runner执行walltime，二者分别核预算；prepare还补`runner_template_id / max_run_seconds / local_project`。总搜索、模型调用和原生重试成本另向原所有者核账，不能凭单个walltime声称全预算已受控。|
|`notes`及人工追溯表|可写提案manifest／input／result身份、完整前驱结果摘要、决定与缺项的说明位置。若在notes记录追溯表SHA，可人工核表与原件；现有validator不自动校验这条关联，表不是新执行或批准凭据。|

在项目的持久资料目录保存一份普通Markdown追溯表即可；其格式由项目维护，不需要再建数据库或转换服务。记录以下对应关系，后续有真实manifest再补其位置／SHA：

```text
原组合根 id / version / digest；完整manifest digest
所选实例path；input digest；原run ID／实际backend／model／回退原因
各完整原result的位置／SHA，以及kernel和measurement收到的原前驱
原合同字段 → 真实来源／SHA → 人工决定／负责人 → 未验项
prepare返回的实验ID／manifest SHA → 原runner／job → evidence SHA／原批准
```

这些身份各有作用：组合manifest固定模板和资料，叶input固定本次任务，result固定模型原产物，实验manifest绑定真实候选和实验合同，evidence SHA绑定执行证据。它们不能互换，也不会因为记录在一张表中就自动获得执行权。

失败、`no_gain`、噪声、缺项与`unknown`保留原身份和预算；只有受信执行、独立正确性／质量与统计都满足合同后才进入原采用流程。原生工具结束、生成器自报PASS或measurement建议通过均不关闭这一步。具体证据字段见[原证据格式](../src/ergora/data/reference/platform/upstream/docs/evidence-format.md)。

## 将实验候选交给开发任务

训练证据已按原evidence SHA获准后，在同一业务项目使用repository-governance或large-change创建集成/复验任务；先通过`project register`登记相应开发模板、路径和可信检查。按[正式任务旅程](../README.md#首个开发任务)预览、创建、提交、批准精确计划，再用原run结果核对verification/review与candidate并导出本地分支。训练批准、开发计划批准和业务合入分别保留原证据，不能互相替代。

开发集成/复验任务闭合后，可按[交接包说明](USAGE.md#收集与离线核对交接包)收集它的冻结索引及回执指定材料，供无服务环境离线核字节。该包不自动收集独立训练实验的数据、checkpoint或完整统计来源；训练证据、原批准SHA及复现实验仍按本手册保存。

`ergora task cancel/reconcile`仅处理统一创建/提交的开发任务。训练实验、Forge campaign及远端作业仍使用各自原生ID、取消和恢复协议；开发task的外部已确认不证明GPU/远端实验已停止。正式开发与训练若共享执行state，停止worker/执行栈之前先核对其全部在途作业；只关闭控制台不表示外部作业已取消。

## 记忆、Skill 与资料

- 将已核对的项目约定保存为带来源和修订的记忆；`ergora agent run --recall QUERY` 将所选项目记忆作为可核对的观察传入。
- 用标准 Skill 目录保存操作知识。手动或 GEPA 产生候选后，用固定 train / validation / holdout 评价，核对正确性、报告成本和泛化限制，再明确采用。它优化文本资产，不更新模型权重。
- 对明确的官方文档和论文来源配置有界 URL 观察；资料变化生成待审提案。Temporal Schedule 可持久触发，默认暂停，每次有独立预算。

具体 JSON 输入 / 输出、CLI、ReMe 与 GEPA 接入见 [INTEGRATIONS.md](INTEGRATIONS.md)。基础安装、控制台和备份见 [USAGE.md](USAGE.md)。

## 专用 Agent 的接入方向

模板以 `agent-contract.json` 声明 experiment-planner、performance-analyst 和 kernel-tuner 的能力与产物；具体 Agent 由项目角色绑定选择。参数搜索可由项目 runner 接 Optuna 等现成工具，可信实验执行和数值/质量/性能复验不交给生成器。

[OpenBMB/ForgeKernel](https://github.com/OpenBMB/ForgeKernel) 提供可选固定版本的原生 campaign 适配。先安装独立工具环境、配置本地任务与设备，再通过 `ergora kernel plan/prepare/status/run` 或训练页面操作。固定版本仅支持 Claude backend；计划检查与创建 campaign 不调用模型/GPU。完整配置、继续执行和结果不明时的对账步骤见 [Agent 手册](AGENT_BACKENDS.md#forgekernel-原生候选)。

生成器原生报告只作为候选材料，仍需提交候选代码、冻结实验 manifest，并运行上述可信证据门禁。KDA、ForgeKernel、mini-swe-agent 等的比较和许可证见 [三模板选型](research/2026-10-31-template-agents.md)；CPU 接口验证不能证明 GPU 性能提升。


## 可选的实验专家提案

`ergora composition install-preset training-optimization`导入实验设计、性能分析、kernel设计和测量复现审查的独立专家及子模板。根为`ergora-training-proposal`，当前版本1.0.0；[完整使用范围](WORKFLOW_DEFINITIONS.md#使用内置领域组合)说明可独立调用的只读叶子及输入准备。它们的提案和审查意见供操作者据此填写原workload/baseline/experiment，保持本手册的可信runner、独立测量和原证据摘要人工批准流程。静态图没有自动运行训练实验，模型生成代码或Forge原生完成也不构成实验采用。

显式选择新版跨域专家时安装`training-optimization-v2`，根仍为`ergora-training-proposal`、版本为`2.0.0`。四个Agent和analysis／measurement／proposal子模板均固定v2；原v1和原任务保持，可在同一库并存。根不默认挂载全部方向的工具库，各叶读取本项目短Skill及随包离线证据合同；其中的来源链接是研究出处，不表示工具已安装或模型实际联网读取过资料。

|叶路径|主要职责与所需资料|结果边界|
|---|---|---|
|`root/analysis/design`|固定workload／baseline、目标单位与质量门禁，按瓶颈选择有限动作；列组合干预、预算、停止及回退|给原runner的实验提案，不分配资源或执行搜索|
|`root/analysis/profile`|分析提供的trace／memory／rank／拓扑和数据路径，区分采集条件、关键路径与不确定性|已有报告分析与可证伪假设，不虚构新profile|
|`root/kernel`|冻结shape／stride／precision／alias／RNG／导数及真实wrapper，结合fusion／graph／memory／communication|文本或设计是candidate，未编译／未独立验证不称可用kernel|
|`root/measurement/review`|核精确候选、独立正确性／质量、配对窗口／rank／方差和总成本；区分kernel／wrapper／step或服务|有范围的审查意见，缺失／失败／no_gain／noise／unknown不改为收益，也不批准采用|

先为该精确根生成grant和完整manifest，再按[单叶调用](WORKFLOW_DEFINITIONS.md#调用一个准备好的叶子)准备一个叶输入。带Skill附件时选Linux／WSL2的`task-mcp`模式并确保实际读取完整固定资源。单次`run-input`不会执行其图前驱：操作者把design／profile的完整原产物和摘要明确交给kernel，再把全部相关输入与真实实验材料交给measurement；缺少的报告、硬件或实验数据须保持未验，不用占位数字充当实测。后端覆盖按实际叶路径保存原因，measurement优先异于执行后端；不可用时显式记录已授权的同后端回退。

跨域专家可复用于多个方向子模板，单份kernel设计也可覆盖精度、布局、融合和通信等关系。方向知识与原生执行能力分别接入；安装v2提案不等于已接入Forge／KDA内部全流程或任意外部MCP。实际实验继续使用本手册前述原manifest、可信runner、独立评价和精确evidence SHA批准。

## 通用性能诊断

```bash
ergora composition install-preset optimization-performance-diagnosis
```

根为 `ergora-opt-performance-diagnosis-proposal`、版本 1.0.0，复用 v2 的 design／profile／measurement 三叶。父模板提供标准 [`ergora-performance-diagnosis`](../src/ergora/data/presets/workflows/ergora-opt-performance-diagnosis-proposal/skills/ergora-performance-diagnosis/SKILL.md)：先固定同症状反馈命令，再按实际格式、版本、phase 和硬件选择已有报告 reader。没有可比证据或 trace 来自不同场景时保留 unknown，向原 runner 提出有限补测请求。

沿[单叶输入与调用](WORKFLOW_DEFINITIONS.md#准备完整的单叶输入)为该精确根准备 grant／manifest，显式选 `root/analysis/design` 或 `root/analysis/profile`；之后把两份完整原结果交给 `root/measurement/review`。资料通过父链累加，权限仍为只读、无 shell／网络；安装不执行整图、采集器、parser 或实验。工具路线是选择依据，具体工具的安装、可用性和授权分别核实。真实收益仍按本手册的原 runner／evidence gate 验收。

若仅需要项目级 Skill，可在本仓库 checkout 根、已登记实际项目后执行：

```bash
ergora skill import my-project \
  src/ergora/data/presets/workflows/ergora-opt-performance-diagnosis-proposal/skills/ergora-performance-diagnosis
```

首次 import 是初始 baseline；后续候选不自动采用。独立 `agent run --skill ergora-performance-diagnosis` 不修改模板固定资料，完整选择区别见[重构手册](USAGE.md#使用重构配方)。

## 独立的优化方向子模板

按任务选择下列配方，不必让每个专家加载全部方向资料。每个根的版本为1.0.0，组合共享的analysis／measurement v2及designer／analyst／measurement reviewer；基础三叶路径为`root/analysis/design`、`root/analysis/profile`和`root/measurement/review`；low-precision与kernel方向另含`root/kernel`。每叶继承本方向完整context、自身Skill与全部结构祖先资料。

|安装用preset|根ID|准备的方向资料与输出|
|---|---|---|
|`optimization-memory-tuning`|`ergora-opt-memory-tuning-proposal`|最热rank与阶段的状态／激活／workspace／allocator容量分解，估算缺项、碎片假设和有限对照|
|`optimization-activation-recompute`|`ergora-opt-activation-recompute-proposal`|实际版本的selective／full层边界、RNG／数值／梯度／通信重放、图与卸载兼容性|
|`optimization-cpu-offloading`|`ergora-opt-cpu-offloading-proposal`|层级激活、细粒度激活、优化器三个机制分开；host／pinned／NUMA／传输／CPU计算和总成本|
|`optimization-cuda-graphs`|`ergora-opt-cuda-graphs-proposal`|host关键路径、实际capture／replay／optimizer范围、地址／RNG／pool寿命和setup摊销|
|`optimization-sequence-packing`|`ergora-opt-sequence-packing-proposal`|offline／in-batch／worker buffer／global-batch四路径，样本边界／MTP／loss权重／有效token与恢复|
|`optimization-parallelism`|`ergora-opt-parallelism-proposal`|dense／expert两mesh的合法性、rank／stage与拓扑、有限布局及独立训练／恢复证据|
|`optimization-megatron-fsdp`|`ergora-opt-megatron-fsdp-proposal`|状态容量／通信权衡、实际DDP flag、checkpoint格式、权重reshard与完整续训分开|
|`optimization-hierarchical-cp`|`ergora-opt-hierarchical-cp-proposal`|HCP选择依据、内外组／MPU／TE路径、真实attention／梯度和端到端收益证据|
|`optimization-tp-dp-overlap`|`ergora-opt-tp-dp-overlap-proposal`|TP／DP／PP实际生效路径、bucket／精度／launch归属、关键路径与争用|
|`optimization-moe-dispatcher`|`ergora-opt-moe-dispatcher-proposal`|实际dispatcher／backend初始化、ABI／拓扑、自然路由与独立全rank正确性|
|`optimization-moe-overlap`|`ergora-opt-moe-overlap-proposal`|普通EP overlap与delayed wgrad分开，版本／graph／重计算约束及独立测量|
|`optimization-profiling`|`ergora-opt-profiling-proposal`|原trace／稳态窗口／rank覆盖，区间并集、依赖归因和有限关键路径机会|
|`optimization-memory-snapshot`|`ergora-opt-memory-snapshot-proposal`|受信报告、allocator／历史口径、step对齐和快照差异；缺失峰值或设备总量保持未知|
|`optimization-recipe-model`|`ergora-opt-recipe-model-proposal`|模型／任务／配方身份、收敛语义与执行映射、真实builder／mapping／模态缺项；适配交原开发流程|
|`optimization-model-verification`|`ergora-opt-model-verification-proposal`|十二核心项、完整权重／forward／训练／resume／质量证据；exit0和schema-valid卡不替代实际结果|
|`optimization-cluster-resiliency`|`ergora-opt-cluster-resiliency-proposal`|唯一rank生成者、原experiment／job／cycle和unknown、日志归因、checkpoint持久化与下一update恢复证据；只读提案|
|`optimization-low-precision`|`ergora-opt-low-precision-proposal`|PTQ／QAT-QAD／TE训练的格式、融合／导出／runtime、质量及成本方案；复用四位v2专家|
|`optimization-kernel`|`ergora-opt-kernel-proposal`|真实算子／wrapper、独立oracle、当前编译基线及kernel／整体测量；复用四位v2专家，原生工具另行准入|

例如选择容量诊断，先准备项目、后端、根grant及真实UTF-8任务正文，再使用原命令：

```bash
ergora composition install-preset optimization-memory-tuning
ergora composition show ergora-opt-memory-tuning-proposal 1.0.0
ergora composition prepare-manifest ergora-opt-memory-tuning-proposal 1.0.0 --grant ./grant.json --directory ./memory-manifest
ergora composition prepare-from-manifest ./memory-manifest root/analysis/design --task ./memory-task.txt --directory ./memory-design --max-prompt-bytes 100000
ergora composition check-input PROJECT_ID ./memory-design --mode task-mcp --backend codex --backend-reason "Explicit design backend"
ergora composition run-input PROJECT_ID ./memory-design --mode task-mcp --backend codex --backend-reason "Explicit design backend" --timeout 600
```

grant的`permissions`／`limits`从该精确根读取，按[完整manifest准备](WORKFLOW_DEFINITIONS.md#保存和分享完整组合)设置；若需要新增权限，先修订所有相关父级上限再修订子模板，不能用task正文越权。正文提供实际code／config／依赖版本、模型与token／batch、精度／optimizer／PEFT、mesh／rank、失败阶段与原trace／snapshot／峰值、目标与独立数值／质量门禁、允许改动、资源／时间预算及恢复要求；缺项标为未知，不填写虚构测量。

单次调用只运行所选叶。独立准备profile输入后，把design和profile的完整原产物、来源摘要及真实实验材料一起放入measurement的新任务正文。measurement默认优先异于执行后端，覆盖及回退须显式记录原因。配置能解析、估算低于容量、未OOM或有限短loss都不等于端到端性能／质量通过；资料中引用的Bridge／Core版本是知识来源，不表示这些依赖已安装，也不证明该组合适合当前运行版本。多个方向可作为普通精确引用子模板组合，但静态图不会获得自动训练执行权。

集群／恢复提案还需实际入口／初始化、nodes与每节点进程、原提交回执与作业身份、所有rank日志及共享路径、checkpoint提交／分片与恢复后的下一update证据。用srun直接生成训练进程或每节点一个launcher，按真实入口选定一个rank生成者；lost acknowledgement先按原身份对账，空日志的RESTART建议与异步保存入队均保留未验。`optimization-cluster-resiliency`不运行Slurm、NVRx或恢复动作；确定性归因工具、带内部模型的Restart Agent和实际集群执行分别准入，完整步骤及来源见其已声明context。

低精度提案需源权重／精度、模块与模态覆盖、tokenizer／chat template、校准／开发／独立留出数据、每任务质量门槛、格式／算法／scale／packing及目标runtime／硬件身份。该方向额外保留`root/kernel`：先手动提供design／profile完整原产物，再把三份完整原结果和实际实验材料交给measurement。PTQ、QAT／QAD与TE训练分别核；effective_bits、低perplexity、短loss或搜索返回best均不替代任务质量与真实性能。原生ModelOpt／AutoRound／TE未随提案安装或执行，原runner与评价／采用门禁保持。

Kernel提案需真实operation／调用者、shape分布／stride／layout、数值／alias／RNG和所需梯度、硬件／compiler／DSL及当前编译基线。与低精度方向相同，先把两份完整分析交给`root/kernel`，再将三份完整原结果与真实实验资料交给measurement。候选自生成PASS、原生judge或exit0分别保留其范围；完整wrapper命中、独立oracle、梯度及实际step／服务测量单独核准，局部speedup不直接变成整体收益。其完整context给出KDA、Forge、KernelAgent/Fuser、GEAK、AKG及robust-kbench的固定来源与接入条件；提案包本身不安装／执行这些工具，不改变Forge pin／后端协议或原campaign、runner与评价／采用所有者。

Graph提案需提供实际trace／shape分布／地址和RNG生命周期、当前编译及capture范围；capture成功与实际replay、冷启动和稳态收益分别核对。Packing提案还需数据／tokenizer身份、真实样本边界／mask／loss分母、原生路径和resume状态；按所选版本区分runtime THD与offline／in-batch限制，配置token容量不能当有效源token吞吐。缺项保留未验，由原runner和owner决定实验／采用。

并行方向还需实际dense／expert mesh、局部head／expert／layer划分、rank顺序和节点链路。普通mesh的两组整除下界不替代原生validator或自定义layout／GTP支持。FSDP需区分实际实现与配置版本：引用快照使用`ddp.use_megatron_fsdp`，旧`dist`字段已移除；保存／加载前核`fsdp_dtensor`，并分别验证权重重分片及optimizer／RNG／数据顺序的完整恢复。HCP仅显式选择，需核hierarchical groups真实传入attention和独立数值证据；TE最低版本、建组或短loss均不能单独证明组合正确。库和solver仍是原生工具，不因出现于context就成为已安装Agent或获得执行权限。

通信方向先固定真实mesh／rank↔GPU↔NIC、原baseline和精确框架／库版本。TP请求可能被原实现禁用；DP配置需对应真实DDP／optimizer消费者，bucket按参数数量计，不能把FSDP当同一个开关。MoE先证明所选flex后端已在目标环境初始化，不把缺包失败当性能结果；固定Bridge源码识别deepep／hybridep／ncclep，显式None选择alltoall，不支持的最终后端不会静默替换。MoE overlap与delayed wgrad须分别对照，harness一次同时开启两项不能用于单项归因。强制负载均衡改变路由语义；自然路由、全rank数值／梯度／恢复和未profile的配对step测量仍须独立通过。方向资源详列固定实现的必要条件，不能代替实际版本的完整validator或训练质量门禁。

Profiling方向先提供可信原报告的身份、工具／schema、稳态step、所有已采集rank与PP stage、时钟及丢事件情况；由原工具所有者准备完整文本／JSON分析结果。这些叶不能执行SQL／采集或安装依赖，`nsys query`等操作还可能生成缓存或自动安装包，须单独核操作与资源权限。预算按裁剪区间并集计算；暴露的通信／copy只有真实producer依赖支持时才可归因于阻塞，缺计数器保持未知。profile中的机会范围不能当实际speedup，实际变化仍须独立未profile配对测量与质量验证。

Memory-snapshot方向优先提供原parser产生的完整可信文本／JSON及原snapshot摘要。不要把任意pickle交给只读Agent执行：反序列化、来源信任及RAM／事件／时间预算由已授权parser所有者负责。说明真实recording起点、selected device／rank、history丢失、step markers、graph／allocator和对齐方式；dump时的allocated／active／awaiting-free／inactive与重建历史peak、设备总占用分别报告。等待释放的块尚不可复用；缺原alloc／step或其他rank不能推出全局headroom、泄漏、性能或采用结论。固定来源的Plotly绘图依赖CDN，不因生成HTML就称完全离线。两方向均可单独选preset并沿上述三叶手动交接，不会安装Nsight／snapshot parser或隐式获得新权限。
