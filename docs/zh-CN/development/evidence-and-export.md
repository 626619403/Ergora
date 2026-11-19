# 读取闭合运行的证据索引

简体中文 · [English](../../development/evidence-and-export.md) · [文档目录](../../README.zh-CN.md)

统一创建并保存原提交回执的任务，在原run闭合且没有后继运行后可集中读取证据引用：

```bash
ergora task evidence my-project TASK_ID --run-id RUN_ID --timeout 20
```

API：`GET /api/projects/PROJECT_ID/tasks/TASK_ID/evidence?run_id=RUN_ID&timeout=20`。使用登记Linux/WSL2完整运行时；查询预算1–60秒，父进程另留5秒，本地合同预检另计。超时、超大响应或错误归属会明确失败，不返回部分完整索引。

`contract`固定原创建/提交摘要、spec及Agent绑定快照；`original_outcome`和其摘要保留原结果。`jobs`列出原调度事件ID、context摘要、请求/回执状态和完整已核回执；回执中包含actor、候选、checks和材料的name/path/SHA，不返回材料正文。需要正文时，从所列调度事件使用[原job读取入口](run-and-recover.md#读取原job回执与文本证据)。

`published_evidence: verified`只表示本次检查的全部原请求/已发布回执及产物字节完整匹配。它不代表检查通过、独立审查通过或任务可合入；`execution_success`保持null。只有原outcome显式保存的verification/review回执会与对应job逐项比较，`outcome_reference_state`显示`matches/differs/unavailable`；其他阶段显示`not_recorded`，不能从文件存在推断已采用。缺失或坏回执/产物使`published_evidence`为`incomplete`，错误请求、fence、根或history则明确拒绝。外部清理由独立的`external_confirmed/fence/unresolved_jobs`说明；正常任务没有fence也可拥有完整材料，取消任务仍保留原CANCEL_UNCONFIRMED。

索引限1 MiB响应，但仍扫描完整原history，并通过FileAdapter读取和核对每份产物（每份最多16 MiB）；它不限制总IO或总内存到1 MiB。结果是当前材料观察，后续读取仍须重新核验。`context_snapshots`中的评价集、Skill、记忆及来源采用快照若未被原任务记录，均为`not_recorded`，不会用当前配置补写历史。查询不启动服务、不执行模型、不写fence、不释放租约或修改Git ref。

`budget`字段仍投影同一冻结profile的`limits`、阶段等待、人工批准等待和轮询间隔，附原profile SHA及`workflow_admission_and_waiting`范围。`max_parallel_units`约束work单元调度，不是所有外部进程的全局并发上限。stage期限从原dev_submit返回后建立，并在空回执poll后检查；它不保证外部进程硬截止，也不是任务总时长或费用上限。历史执行器的独立walltime不能从当前配置补造。 v9的统一授权另在`contract.original_input.budget`，运行观察在`original_outcome.budget`；不要把旧profile投影当作这份持久授权或实际模型调用计费。

`usage`列出完整原history的事件数、activity调度、实际记录的activity-start、signal、dev_submit事件数和不同job数，并给出冻结request的work单元数。SDK会合并部分重试历史，因此这些计数不能推导全部重试、模型调用或计费。`workflow_span`按原首/终事件的Timestamp计算秒数并附event引用，包含排队、人工等待、并发和服务停止时间；它不是模型运行时长或job时长之和。缺时间戳为`not_recorded`，反向为`invalid_timestamps`且值null，真实零跨度才为0。`model_calls/tokens/cost`没有按原job验证的结构化用量来源时均为`not_recorded/value: null`，费用币种和来源亦null；不从材料文本或当前价格表自动推估。

## 收集与离线核对交接包

原run闭合且上述索引的材料完整时，可显式收集到新的本地文件。使用登记Linux/WSL2完整运行时，不启动worker或重新运行agent：

```bash
ergora task handoff my-project TASK_ID --run-id RUN_ID --output ./task-handoff.zip --timeout 20
```

收集只读取原索引和回执引用的产物，不扫描环境、凭据、任意用户目录或整个仓库。缺失/坏材料或额外job会拒绝收集；原业务失败、取消不妨碍交接完整材料，不会被改写成成功。文件以同目录临时文件完成后仅创建发布，目标已存在时拒绝覆盖；需要支持硬链接的本地文件系统。正常异常会清理临时文件，进程被强制中止时须先检查目标及同目录`.ergora-handoff-*`残留，确认没有仍在运行的收集进程后再处理。查询预算1–60秒、父进程另5秒；超时不保证文件尚未发布，先核已有目标，不能盲目覆盖。

接收者只需基础`ergora`安装，可在Windows原生或Linux上运行，无控制库、SDK或在线服务：

```bash
ergora handoff verify ./task-handoff.zip
ergora handoff verify ./task-handoff.zip --sha256 EXPECTED_PACKET_SHA256
```

`--sha256`可选，接受独立取得的整包64位小写hex摘要；匹配时`external_sha256: matches`，未提供时`not_recorded`。成功输出`status: verified`、包/manifest摘要、项目/原run/候选引用及原outcome。`verification_scope: packet_bytes_and_declared_internal_identities`仅证明包内字节、摘要和声明的spec/request/profile/绑定、job/回执/材料关系相符；`origin_authenticated: false`和`execution_success: null`保持。包未携完整创建/提交意图、服务history、context或Git对象，其SHA只是引用；不能离线认证原执行者、验证history计数、审查独立性、重演执行或复验候选代码。外部SHA也不自行构成签名或来源认证。

v1使用标准ZIP_STORED、UTF-8 JSON、SHA256及公开[版本化schema](../../../src/ergora/data/schemas/task-handoff-v1.json)，只含`manifest.json`与按摘要去重的`blobs/SHA256`。Manifest 限制遵循已核验的原始输入合同；参见[当前按范围划分的限制（英文）](../../architecture/contracts/formats.md#supported-task-routes-and-material-limits)。逐 blob、总 payload、成员和完整包限制仍各自独立。每blob16 MiB、去重材料总64 MiB、4096成员/整包72 MiB；重复、多余、缺失、非规范路径、链接、加密或压缩成员明确拒绝。验证直接读取成员，不提取或执行。限额不把ZIP库峰值内存或原索引的完整history/逐材料读取成本限制到1 MiB。交接包用于材料复查，不替代原执行目录、Git及租约库的联合备份；本地路径输出和传输另由操作者选择。

HTTP客户端可显式`POST /api/projects/PROJECT_ID/tasks/TASK_ID/handoff`，JSON正文为`{"run_id":"RUN_ID","timeout":20}`；沿用同源及`X-Ergora-Request: 1`，不接受服务器源/输出路径等额外字段。成功返回`application/zip`和固定attachment名称`ergora-handoff.zip`，`X-Ergora-Handoff-SHA256`为本次响应字节的整包摘要。服务端在私有临时目录调用同一收集用例，受限读回并核SHA后先清理临时目录，再发送响应；普通失败也清理，不启动服务或更改原任务。下载位置由客户端选择，客户端须避免覆盖需保留的本地文件。该入口缓冲最多72 MiB包字节，有额外内存成本，不是流式下载；强制进程终止的残留按运维方式处理。响应摘要便于比对本次下载，不是签名；需要独立期望SHA时须从另外的可信渠道取得。

## 网页证据、预算与交接

正式任务中先“读取原运行”，在已闭合的原run点击“证据、预算与交接”。打开窗口不请求索引或材料；“读取证据索引”集中核原材料并展示原结果、完整性、外部协议确认与租约事实。预算和用量区保留原来源与单位，未记录的模型调用、token、费用显示未知，真实0保持；冻结等待限制不能当作进程或费用上限。上下文关联未记录时不使用当前配置补写。

原job目录每页20项，点击“原job回执与材料”复用原回执窗口，再选择并明确读取文本。索引、完整合同与材料内容都按文本显示。重新读取失败保留先前观察并标明失败；关闭重开从空状态开始，不自动轮询、重试或预取正文。

“收集并下载交接包”无需先读取索引。页面调用上述POST接口，核实际响应字节与摘要头后交给浏览器保存；成功提示不证明文件已落盘，请检查浏览器下载列表及保存位置。页面显示整包SHA、字节数和`ergora handoff verify`命令，仍需独立核来源、原结果和候选。服务端与浏览器均缓冲包字节，下载不是流式传输。失败不触发本次下载，旧下载信息如有仅代表先前操作。

关闭、替换窗口，编辑run或切任务/项目后，迟到索引不回写，迟到包不触发下载；这不会撤销服务器已经发出的只读收集。同一窗口忙时禁止并行读取/下载，不自动启动服务、worker或模型，也不发布fence、释放租约、批准候选或改写原取消结果。

## 核对闭合运行的外部作业证据

统一创建并保存原提交回执的任务，可用固定的原run读取完整历史、原作业请求、可信终态回执和已有fence：

```bash
ergora task external-status my-project TASK_ID --run-id RUN_ID --timeout 20
```

API：`GET /api/projects/PROJECT_ID/tasks/TASK_ID/external-status?run_id=RUN_ID&timeout=20`。原run必须已闭合，且仍是该workflow ID的最新run；不支持continued-as-new或其他后续run。使用登记Linux/WSL2完整运行时，预算1–60秒，父进程另留5秒，本地合同预检另计。

`original_outcome`保留原工作流结果；失败、取消、终止或超时的Temporal run没有结果时为null。`jobs`逐项列出原历史job、请求与回执状态及摘要；`unresolved_jobs`包含缺少请求、缺少或损坏回执以及额外请求/孤立回执。错误根、冲突请求、错误fence或不完整历史会明确拒绝。只支持登记执行状态目录下的requests/receipts/artifacts/approvals/fences布局。

仅在完整历史对应的全部请求和可信终态回执均匹配、没有额外作业且已有正确fence时，`external_confirmed`为true。requests和receipts两类job目录均参与检查；无法绑定原history的孤立回执不支持确认。FAILED/CANCELLED回执也是外部作业终止证据，不能据此推断开发成功。这是可信文件协议的当前快照，依赖执行器按原协议发布回执和遵守fence，不代替操作系统进程检查。缺目录不会把已知历史job变成零作业通过。

查询不保存本工具运行记录、不发布fence或释放租约，`lease_released_by_operation: false`、`execution_success: null`。CLI返回0只表示查询成功，务必检查external_confirmed和未决项。未确认时保留原任务、运行目录及租约，先沿原ID补齐证据。

## 导出精确候选与恢复回执

仅适用于统一创建且已保存提交回执的任务。先用`task status --run-id RUN_ID`核对原运行已完成且outcome为`REVIEW_READY`，审阅其确切candidate与可信检查/独立审查证据，然后明确指定本地目标分支：

```bash
ergora task export my-project TASK_ID --revision 1 --run-id RUN_ID --candidate-sha CANDIDATE_SHA --branch agent/TASK_ID --confirm --timeout 20
ergora task export-status my-project TASK_ID
# 中断后先查export-status，以原intent_sha256和当前项目修订恢复：
ergora task resume-export my-project TASK_ID --revision 1 --intent-sha256 EXPORT_SHA --confirm --timeout 20
```

一个任务保存一个不可变导出目标。重复export只返回原记录，不能更换run、candidate或branch。`prepared`表示尚无写前检查点，可明确resume继续；`unknown`表示已保存原结果摘要，恢复只核对原run/outcome及实际分支，不能重新fetch或创建。分支不存在时返回`unknown/branch_not_found`，避免复活人工删除的分支；保持原记录并人工对账。已有分支指向不同commit、原结果变化或记录冲突均明确拒绝。

Git只抓取对象，不写FETCH_HEAD，不checkout、merge或推送。目标分支通过Git条件事务创建；已有正确candidate可接受，其他已有分支和符号引用保持。确认分支后沿原规则释放适用工单租约，写原格式`tasks/TASK_ID/export.json`及本工具回执。`exported`表示已保存该导出事实，`checked_out: false`、`merged: false`，后续仍须按项目策略审查合入。重复终态读取不会实时核查之后的人工分支修改。

`export-status`只读本地记录，不连接Temporal或释放租约。意图、写前检查点和回执位于执行状态目录`ergora/task-exports/TASK_ID.{intent,attempt,result}.json`，须与原创建、提交、任务、工作区及租约记录一起备份；不能只备份控制库。准备时严格核当前revision/confirm并非阻塞取原任务锁，网络/Git阶段已释放控制库写锁。每阶段1–60秒预算，父进程另留5秒，预检另计；超时后先读记录，实际是否写入仍以原分支和检查点对账。Linux/WSL2使用登记的完整运行时，旧入口导出不隐式接管。

API：GET/POST `.../tasks/TASK_ID/export`，POST正文为`revision/run_id/candidate_sha/branch/confirm/timeout`；POST同路径`/resume`使用`revision/intent_sha256/confirm/timeout`。写请求沿用同源保护及`X-Ergora-Request: 1`，confirm必须为true。CLI变更只在exported时返回0，HTTP成功也须检查status。
