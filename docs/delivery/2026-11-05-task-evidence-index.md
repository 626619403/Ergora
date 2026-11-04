# F5.1：原任务证据引用索引

日期：2026-11-05。状态：完成；源码/最终包/三原run只读验收、新独立审查、精确`2c0ddbccd25dda66d971eadd6770b61877c83bb7`普通推送/实时远端及双OS CI41911536059均已通过。[同片独立终结](2026-11-05-task-evidence-index-review.md#精确-ci-与同片最终终结)无未解决finding。源码基线`da80e777f9ccb1caf6de54f66d245669d953b8d2`；历史逐步状态保留各自范围。总体边界见[F5计划](../plans/2026-11-05-evidence-handoff.md)。

## 入口与事实

增加`ergora task evidence PROJECT TASK --run-id RUN_ID [--timeout 20]`及GET `/api/projects/{project_id}/tasks/{task_id}/evidence`。必须固定原提交的run，只接受已闭合且无后继的原运行。沿`tasks → reference → reference_task_reconciliation._Inspection`复用原spec/memo、连续完整history和原请求/回执/产物验证；不逐job重复查询history，不复制材料正文或执行账本。此前`task external-status`及显式对账返回格式、未知语义和副作用保持。

返回schema_version=1的只读投影：项目/原run、创建/提交摘要、冻结spec及Agent绑定快照、原outcome及摘要；每个原job的调度event ID、原context摘要、stage、请求/回执状态和摘要、已核回执（actor、candidate、checks和材料name/path/SHA）。材料仍按原可信根的相对引用读取；不加入认证配置、环境变量或任意本地路径入口。

发布回执的字节验证与原outcome引用分开。只对outcome实际包含的verification/review回执报告摘要是否匹配；其余无显式引用的阶段保持未知，不能因SUCCEEDED或文件存在声明workflow采用。取消/异常原结果原样保留；缺失/损坏请求或材料使当前材料核验不完整，不能改写原结果为通过。外部清理fence状态独立展示，正常任务没有fence不等于材料无效。正式任务未记录的评价集/Skill/记忆/来源采用决定明确`not_recorded`，不读取当前配置补造过去快照。

引用索引限1 MiB响应、1–60秒查询墙钟和外层进程超时；完整history与FileAdapter所有产物仍会被读/核，逐产物16 MiB不是总IO上限。超时/超大/归属失败明确报错，不返回看似完整的部分成功。预算/用量字段、可搬运交接格式与网页消费者分别留在F5.2/3/4，本片不增加依赖、schema迁移或新生产模块。

## 所有权与实施节点

1. 在原`_Inspection.jobs`保留调度event引用，重复同context合并其event列表，冲突context仍拒绝；原context/job摘要及外部对账checkpoint不改变。文件观察的完整回执仅在索引模式返回，旧external-status及对账不增加响应字段。
2. `_Submission`保留本次已经校验的创建快照供索引使用，避免重读原创建意图；它不是缓存或第二份持久数据。索引扩展原`_Inspection`的读取入口，独立处理只读错误，不提供resume/reconcile指引。
3. tasks/reference/CLI/HTTP各在现有所有者接线。新入口无confirm/revision写参数；API与CLI转发同一原ID及墙钟。无旧run接管、模型、信号、ref、fence或lease变更。

## 验收与审查

- 用真实SDK history/codec及本地FileAdapter的轻量材料覆盖正常/取消、重复调度、完整原身份、原outcome引用匹配与冲突、缺失/坏摘要/安全路径及冻结绑定，不复制新增通用测试框架。
- CLI/HTTP等价转发、必要输入先拒绝、只读超时/RPC错误和响应上限；原external-status/reconciliation的输出与checkpoint保持。
- 独立非editable包350资源/两安装及283冻结核对；先代表回归，再由精确双OS CI承担完整矩阵，不重复F5.0的过宽本地运行。
- 最终包对既有两正常原run及取消原run进行明确的只读CLI/API验收，逐job回执/材料摘要/原outcome与持久证据对照，核原文件/完整history/refs/worktrees/leases不变。必要时只开本次专用Temporal，worker/executor保持停止；结束后正式shutdown，持久数据保留。
- 新的fresh-context审查检查正确性、状态声明、所有权/复用、必要守卫/测试及完整核验成本；提交推送、精确CI及同片终结分别记账。本片实际验证见下节，前片精确CI终结前不推下一生产候选。

## 实施与验证进度

六个现有生产文件已接通只读索引，未增加生产模块、依赖、schema迁移或执行账本。首轮43项之前的42项实测41通过、1失败，仅为新测试预期错误文案与现有错误不一致；保留原日志并修正预期。增加1 MiB响应反例后，同源定向43 passed/1上游TestClient弃用warning（pytest2.97秒、外层4.21秒）。覆盖真实SDK消息、完整原history及FileAdapter材料、重复调度/冲突、取消原结果、缺失/篡改/符号链接、CLI/API等价转发、无写超时/RPC和架构。原运行数据与服务尚未使用，本片不借前片结果宣称发行或真实旅程通过。

私有命令及日志位于忽略的`.ergora/checks/f5-task-evidence-index/`；`index-contracts`保留首轮失败，`index-contracts-fixed`为修后43项。下一构建独立noneditable包、代表旧external-status/对账回归与三个原run只读核对；最终新fresh-context审查及精确CI/推送分别登记。

## 最终包与原运行只读验收

独立wheel SHA256 `9e3caeb50dc327109d06025933cdd83fff629681ea9c91f7476c8b5d3eabcf74`；350资源在源码/wheel/两套noneditable安装中逐项相同，283冻结reference与F4相同，基础Web安装无Temporal SDK。包内新增23项全部通过（pytest7.85秒、外层10.81秒），原external-status/显式对账两模板代表4项通过（pytest36.50秒、外层37.46秒）。源码43项及这两组按各自包/范围记录，不合为一次全量回归。

仅正式启动原专用Temporal，worker/executor等保持STOPPED，无新任务/模型。最终包完成三CLI和五个ASGI GET：三成功索引逐项与SDK完整原history、原创建/提交/Agent绑定、请求/回执及产物字节核对，错误run和跨项目各400；ASGI TestClient在进程内调用，端点实际执行登记原生子进程与Temporal RPC，未进行外部HTTP socket或浏览器测试。

|原运行|原history|job|产物/字节|原结果与清理观察|
|---|---|---|---|---|
|repository-governance正常|329事件|7|23 / 105296|REVIEW_READY；原verify/review引用各matches；无fence，external_confirmed=false|
|large-change正常|348事件|6|19 / 156248|REVIEW_READY；原verify/review引用各matches；无fence，external_confirmed=false|
|repository-governance取消|112事件|1|1 / 59|原CANCEL_UNCONFIRMED保持；后续已对账fence使external_confirmed=true|

三次CLI约1.76–2.37秒、对应API约1.47–1.58秒，CLI输出15347–32101字节。此为当前小规模、持久本地Temporal的整体观察，包含进程启动和原合同预检；不据此推断大规模history吞吐/并发或通用性能提升。1 MiB只是返回上限，完整history和各产物读取成本已在公开手册披露，无缓存/新执行账本。

前后139原证据文件、三完整history/outcome、两repo的文件/HEAD/refs/worktrees及三claim/零active lease逐项完全相同。私有证据为`native-before.json`/`native-after-verified.json`、`original-index-verified.json`、逐runCLI/API和真实`*-command.json/.log`；数据不提交公开仓库。正式shutdown已confirmed，两个本片专用进程已退出、服务端口关闭、三个持久数据库保留；最终离线重算139文件/租约保持，四服务端口关闭且未启动外部HTTP；新独立审查、精确提交推送/双OS CI待分别收口。

独立本地终结：新的fresh-context审查已核源码所有权/必要守卫/测试、350资源/两安装/冻结283、三原run材料与前后不变及正式shutdown，需求和可维护性均通过，无未解决finding。下一精确提交、Git archive同包核验、正常RSA推送、精确双OS CI与同片最终续核；完整F5仍待后续切片。

精确候选`2c0ddbccd25dda66d971eadd6770b61877c83bb7`已提交并普通快进RSA推送，实时远端一致；Git archive350资源逐项等于9e3cae包。提交前10份文档331本地链接/锚点及README28命令通过。默认nc代理407只发生于只读预检，未发推送；复用已有CONNECT脚本后成功，认证值未进入argv/公开文件。精确双OS CI与同片提交/CI终结待核；本片数据服务已退出。

完整F5.1收口：精确CI41911536059的Ubuntu126860081709及Windows126860081963全部必要步骤成功；同片独立审查已核原官方HTML/完整commit及log URL、未改的全量workflow接线和实时RSA远端，无未解决finding或本片剩余验收。F5.1完成，F5.2–5及G0仍分别推进。
