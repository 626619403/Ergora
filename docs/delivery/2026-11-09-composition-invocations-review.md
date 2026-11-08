# AC3b.2b 受限单叶调用独立审查

日期：2026-11-09（Asia/Shanghai）。轮次：R1。审查者：`composition_invocations_review`；另由全新上下文 `standards`、`spec` 分别检查两轴，未继承实现会话。依据为 [AGENTS](../../AGENTS.md)、maintainable-project-delivery 及其 independent-review brief、code-review、codebase-design。审查授权仅含只读检查、隔离小探针和本报告写入；未修改生产代码、测试或计划，未安装、提交、推送。

R1结论：**需求符合性需要修正两项 P2；维护性需要处置一项 P2 启发式发现。** 两轴原始结论和补充调用路径检查分别保留，不能用其中一轴的无发现覆盖另一检查的可复现问题。R1源码检查已结束；修正后须做同片复核。

## 身份与范围

基线及审查时 HEAD 均为 `eee09efcba093839dba5407c474a7a5b46a3a2a0`，分支 `refactor/architecture-foundations`。本片是未提交工作区；`git log baseline..HEAD` 为空，未把空三点差异作为本片差异。

冻结记录 `.ergora/checks/ac3b2-invocations/review-r1-scope.json` 的 SHA256 为 `9d971e05d02a52523dd911bd8be7967b462c743503b45be040d168a77cf60c4a`；其中十项文件SHA在检查结束前全部吻合。冻结 tracked diff 为同目录 `review-r1-tracked.diff`，SHA256 `b3357af42c0b7bb537259b77c0b4d668a1720371c10646b82a5ceb08db66714a`，同样核对一致。新交付记录、新测试均全文阅读。

|范围|文件|
|---|---|
|实现|`src/ergora/agent_backends.py`、`src/ergora/agent_runs.py`、`src/ergora/agents.py`、`src/ergora/cli.py`|
|新增测试|`tests/test_composition_invocations.py`|
|合同、手册、进度|`docs/delivery/2026-11-09-composition-invocations.md`、`docs/WORKFLOW_DEFINITIONS.md`、`docs/AGENT_BACKENDS.md`、`docs/PLAN.md`、`docs/plans/2026-11-08-agent-composition.md`|

前片 `composition-inputs-review`、`definition-admission-review` 的纯归档修改排除。相邻只读检查包括输入核验/定义准入、进程与 Windows gate、State 实际 `agent_runs` 表、Web dashboard、前端记录展示、现有 Agent/Windows 测试、当前架构和 ADR0004/0005。相邻 `processes.py` 当时未修改，SHA256 为 `53cef03e7925e9d88051ca191e75e6a360d71d73b5ec8ce49568fe11ab63128d`。

先读原任务合同：完整祖先及自身指令/上下文和操作者任务进入显式单叶调用，保存精确副本/实际 prompt、argv、结果；text-only 拒绝写、shell、工具网络请求，附件不提供文件执行权；原生专用配置关闭 ambient 能力，推理配置不能覆盖模式权限；原定义及实际 binding 当前重新准入，坏输入不启动模型；失败、超时和结构错误可见且持久，CLI 非成功非零。原普通调用/六阶段保持，任务 MCP、正式批准和 Temporal 嵌套属于后片。随后才读作者实现说明和验证叙述。

## Standards 轴原始结果及事实更正

此轴报告硬标准违规 **0**、启发式发现 **1**。新增行为归现有所有者，真实调用沿原 ABC/局部注册；未发现应删除的单用转发模块或无可达失败的守卫。

**S1，P2 启发式：运行列表提前加载完整资源正文。** [agent_runs.py](../../src/ergora/agent_runs.py):104 将完整 `leaf["resources"]`（包括 `text`）写入运行 document；同文件:130–134 每次解码最近100条，[web.py](../../src/ergora/web.py):272–277 每次 dashboard 刷新完整返回。页面初始只显示8行，正文到点击记录时才展示。

原审查者第一次写到“没有正文消费者”“UI仅显示四字段”。协调审查者发现 [overview.js](../../src/ergora/data/console/overview.js):156 的通用 `pre(item)` 后，原审查者复读并明确撤回这两句绝对表述：详情确实可显示 document 内的正文。**原发现收窄为列表每次提前加载100条大正文，P2启发式优先级保持**；不能以“绝对无消费者”作为删除依据。

只读内存探针执行生产 `document` 赋值 AST，900,000字节ASCII资源正文使单条JSON为901,334字节；去 `text` 后为1,322字节。100条列表额外携带90,001,200字节，三次 `_store` 额外序列化2,700,036字节。这是给定合法容量范围内的序列化字节量核算，**未测耗时、HTTP传输或SQLite物理写入**。

最小目标为运行列表保留资源身份/来源，完整材料按需查看。可以从已核输入副本读取正文；不要求增加API或另一份持久材料。作者选择本片新记录的 `context.resources` 去 `text`，保留其他资源身份/来源，完整材料继续由快照和现有 `verify-input --material` 提供；此处记录待复核的处置，不登记已修。

此轴全文读新增测试/交付记录，核邻接消费者及冻结身份；未启动模型、修改文件或重复整套测试。

## Spec 轴原始结果

此轴独立结论：冻结10项 scope 与当时内容一致，基线/HEAD 如上。已读原合同、两份 ADR、计划、完整新增测试及作者报告，追到输入核验、后端、进程与持久化实现。

1. **缺失/部分：** 未确认代码层面的合同缺失。报告时IV3仍未完成：合同要求“真实已配置模型的一次单叶调用与可读持久记录”，`hosted-review.json` 的Claude90秒、Codex240秒均 `timed_out`、CLI1，无有效结构化审查；应保留失败，取得合格调用后再关闭IV3，无需扩大实现范围。
2. **Scope creep：** 未发现。复用原 AgentBackend、`agents.invoke`、运行表和State备份路径，没有提前引入调度器、正式批准manifest、任务MCP或嵌套执行。
3. **似实现但错误：** 此轴检查未确认finding。副本核验先于启动；原定义和实际binding重新准入；权限拒绝、显式覆盖、完整prompt/argv、失败持久化和非零退出有对应路径。

此轴实际新增检查：

- 既有 wheel venv 中执行 `python -m pytest tests/test_composition_invocations.py -q`：**11 passed**。
- `PYTHONPATH=src` 下以临时目录/本地内存 Responses 服务调用实际Codex的 `agents.invoke(..., text_only=True)`：succeeded、1次请求。临时Git祖先 `.codex/config.toml` 指令与 `.agents/skills` 标记未进入请求，ambient MCP哨兵未产生，工具仅 `request_user_input`。
- 重算冻结身份：10项未变。

未执行托管模型、Windows原生调用、整套回归或精确候选CI；不替代其他审查轴。其“IV3待验”是该轴报告时的事实，后到证据单独记在下文；其未发现代码问题不覆盖补充检查的两项可复现缺陷。

## 补充调用路径检查

### C1，P2：Windows 文本 stdin 改变精确 prompt 字节

位置：[agents.py](../../src/ergora/agents.py):58、65 → [processes.py](../../src/ergora/processes.py):162–163。新入口在Windows可达，最终gate以 `input=request["stdin"], text=True, encoding="utf-8"` 调 `subprocess.run`。CPython在文本stdin上写默认换行模式，Windows将每个LF变CRLF，已有CRLF会变成CRCRLF；归档 `prompt.txt`/`stdin.txt` 则显式 `newline="\n"` 保持原字节。因此普通多行prompt就与声明的完整prompt SHA不一致。

合同依据：“保留精确副本、actual prompt/argv/results”，输入预算及身份按完整user prompt的UTF-8字节定义。此为新入口复用相邻路径后产生的可达合同问题，不要求引入OS隔离或扩大后片能力。

证据为源码路径与隔离换行机制探针；**未称作原生Windows端到端实跑**。探针以 `io.TextIOWrapper(io.BytesIO(), encoding="utf-8", newline="\r\n")` 写入 `ancestor\n任务\r\n`，原16字节变18字节，SHA不同；同时核CPython `_stdin_write` 直接调用 `self.stdin.write(input)`。

最小修正：Windows gate把UTF-8编码后的字节交给binary stdin，保留现有Job/进程生命周期。加入一个使用真实子进程读原始stdin、比较混合LF/CRLF/Unicode字节的跨平台回归，由Windows CI实际覆盖gate；不需要新增运行器。

### C2，P2：TOML 日期值使坏配置留下永久 running

位置：[agent_backends.py](../../src/ergora/agent_backends.py):88、93–114，[agent_runs.py](../../src/ergora/agent_runs.py):117–126。TOML允许日期类型；`model=2026-11-09` 被allowlist保留，`json.dumps(value)`抛 `TypeError`。该异常绕过运行层的 `OSError/ValueError` 和CLI异常处理，调用直接抛出，SQLite已写入的记录停在 `running`，没有 `finished` 或可读error。

合同依据：“坏输入不能运行”“失败……均可见和持久，CLI非成功非零”。没有模型被启动仍不能把未完成记录留作运行中。

隔离复现使用新增测试的既有 `prepared.__wrapped__` 夹具，仅在临时目录创建合法输入；写上述单行TOML，经真实 `cli.main([... composition run-input ... --codex-config FILE])`，给 `processes.run` 安装禁止调用的spy。结果：

```json
{"raised":"TypeError","error":"Object of type date is not JSON serializable","native_calls":0,"runs":[{"status":"running","finished":null,"error":null}]}
```

最小修正在Codex配置所有者处，将不能编码/不合法的推理配置转成可读 `ValueError`（或采用准确字段类型校验），沿现有运行失败持久化路径处理。增加日期配置反例，核模型未启动、记录failed且有finished/error、CLI1；不需要上层吞掉所有异常。

## 结构、复用、守卫和验证判断

新行为仍由 `agent_runs` 拥有独立调用及记录、`agents.invoke` 拥有协议/进程、后端实现拥有专用原生命令；没有新增调度框架或厂商上层分派。`_store` 留在原记录所有者，复用两条已有/新增调用路径的保存操作；不把同文件多次调用当作跨生产文件复用配额。模式检查同时服务显式入口的运行创建前拒绝与可直接调用的共享 `invoke`，有不同调用责任，不能仅按重复次数删除。

输入完整核验、当前定义/实际binding准入、模式权限拒绝、运行目录不置于输入内、复制后重核身份分别保护外部输入/持久副本/直接调用责任。未发现要删除的无可达失败守卫。源目录和副本两次完整核验属于不同生命周期点，未建议仅为节省IO去掉。复制期间目录仍须稳定，现有文档没有把一致性核验称作同用户进程隔离。

新增测试主要覆盖对外合同，保留与既有普通Agent/结构结果测试的职责区别；没有建议为测试数量删除反例或新增通用测试框架。C1、C2暴露的是现有覆盖未检查的实际字节/异常边界。S1的量化仅支持列表材料成本，不能推导整体延迟或数据库吞吐结论。

## 实际证据与边界

作者已报源码首轮44 passed/6可选skip/1夹具签名失败，夹具修后新增9例通过，再补2个边界；不把初轮夹具失败归为生产缺陷。已只读核有效 `iv3-after-install-wheel-tests.log` 为47 passed/6 Forge/mini可选环境skip，未采用安装未结束误启的 `iv3-wheel-tests.log`。

`package-identities.json` 记录360源/wheel/安装文件和283冻结身份通过，wheel SHA256 `c548b64ad446f64085a1b5aaccee393a00c9b65ba76176cbdb4aff19bbcaddd1`。原生Codex0.166.0/Claude2.1.312本机合成协议四例的摘要已核：完整prompt、ambient标记缺失、工具仅响应/交互、伪造exec_command/Bash未执行；不称真实认证、托管模型质量或OS隔离。

后到的真实小任务证据为同目录 `hosted-small-call.json`：原安装包的structure-review、Codex、3,630字节prompt、28.78秒、succeeded/CLI0、合格approve，run `dbc5cc4347534f188843770ef0640387`。协调审查者额外以SQLite只读连接核对：CLI JSON与DB原样一致；原输入、核验副本、protocol prompt、process stdin四份字节相同；输入digest、prompt SHA和结构化result/SHA均匹配。该证据满足“有一次真实配置的单叶调用和可读持久记录”的窄范围检查。**它仅审了supplied tiny candidate，不是本仓库完整审查，也不使两次87,840字节大输入超时变成通过。**

R1未重装、未启动新的托管模型、未跑昂贵整套/原生Windows/候选精确CI；作者所报7文档230链接、65 parser/diff静态检查未冒称本审查者全量重做。协调审查者另跑 `git diff --check`、冻结身份核对和上述隔离探针。

## 处置与复核出口

作者已接受C1、C2和S1的收窄处置。R1登记状态仍为待修/待复核；允许下一轮明确扩到 `processes.py` 及相应真实stdio字节测试，Codex配置异常在原所有者处理，资源索引去正文且保留精确快照。须更新R2范围/身份，跑受影响回归，记录同片复核；旧包/合成协议证据保持其原源码身份，修正版不能继承为新包验收。

原交付记录的“在途”状态应按两个大输入超时及小任务成功同步。后续普通推送、精确CI、前片eee自身远端/CI均分别记账，不在本R1中提前宣布通过。

轴统计：Standards硬违规0、P2启发式1（最重为列表提前加载正文）；Spec原始代码finding0、当时IV3待验1项（后到小任务窄范围证据已补）；补充调用路径P2共2项（Windows字节身份、坏TOML配置失败生命周期）。

## R2 同片复核

日期：2026-11-09（Asia/Shanghai）。同一独立审查者复核原发现及其最小修正，保留上方R1两轴原始结果，不以R2改写历史。**R2需求符合性和维护性在本次检查范围内通过：C1、C2、S1均关闭，无新增finding。** 原生Windows执行及本片精确候选CI、自托管完整材料模型任务的最终结果继续分别待验，本结论不提前关闭整个交付节点。

R2基线/HEAD仍为 `eee09efcba093839dba5407c474a7a5b46a3a2a0`。明确扩展的冻结范围为原十项加 `src/ergora/processes.py`，未把前片三个归档文档混入本片。`review-r2-scope.json` SHA256为 `f817ec5ab64ee1441b2fe780e360193e5c1f069943e5273ecf5e1976cc684349`，`review-r2-tracked.diff` SHA256为 `65c3720365a02ef668e38b40b6cffb20a3a355654bd3a7d58d1a4696e661f847`；检查开始与结束均重算11项及差异身份并吻合。全文重读新增测试、交付记录及R2实际修改，核相关调用路径；未改源码、测试、计划或安装包。

### 原发现处置

- **C1关闭。** [processes.py](../../src/ergora/processes.py):162–163 的最终gate明确发送 `request["stdin"].encode("utf-8")`，去掉文本管道转换；原Job、环境、输出、超时/取消路径保持。新增真实子进程回归直接对比保存stdin与接收字节SHA，涵盖中文、LF、CRLF和裸CR。独立在已安装R2包运行真实Linux子进程，保存/接收SHA一致；另抽取并执行该包实际Windows gate的 `subprocess.run` 调用AST，使用真实子进程核binary stdin字节一致。后者在Linux执行，仅证明实际gate表达式，不冒充Windows Job端到端运行；原生Windows仍由本片候选CI验证。
- **C2关闭。** [agent_backends.py](../../src/ergora/agent_backends.py):114 的配置序列化仅捕获该操作可达的 `TypeError` 并转为带字段名的 `ValueError`，由原运行层失败持久化处理，没有增加CLI/运行层通用异常兜底。独立用已安装包经真实CLI分别提交 `model` 日期、`service_tier` 时间、provider `env_http_headers.X-Test` 日期时间三种TOML值，均CLI1、`failed`、有 `finished` 和可读字段错误，DB与CLI记录一致；禁止进程调用的spy均未触发。
- **S1关闭（Standards启发式的收窄目标）。** [agent_runs.py](../../src/ergora/agent_runs.py):104 的本片新索引仅投影去掉资源 `text`，其他字段保持。独立正例逐一比较所有非正文资源字段及来源，检查源输入/核验副本/实际protocol prompt和digest不变，确认三个失败记录及一个成功记录的列表均不含资源正文。执行生产 `context` 表达式，将同一资源的text从1字节增至900,000字节，索引JSON均653字节；这证明正文不再随每条列表记录增长，未测HTTP延迟或数据库物理写入。完整材料继续由已有输入快照/`verify-input --material`提供，无新增API、迁移或第二份材料所有者。

### R2验证与限制

独立包边界检查打开最终wheel，并重算记录中的360份源码、wheel成员和site-packages安装文件SHA，逐份一致；最终wheel SHA256为 `98d838a54ee7353868cf0ac827a3ee744d0514a7c835107fa9c5f249e189bd9f`。另实际运行安装包 `reference.verify()`：283文件、v2.2、PASS，原zip摘要 `8018be5094623ca0646d28d3671daaf7ac60774280eefc1c5c023bc19dc5c760`，`runtime_started: false`。上述独立探针确认导入site-packages，未以源码覆盖安装包。

只读核 `r2-source-tests.log` 与 `r2-wheel-tests.log` 同六套各49 passed/12 skipped，跳过分为6个Forge/mini可选环境及6个在Linux跳过的原生Windows用例。新增回归保护真实字节和外部配置失败，不是新增抽象的实现镜像；原正例同时保护精确材料和精简索引。结构修正全部留在原所有者，没有增加运行器、依赖、泛化接口或重复守卫。独立另跑 `git diff --check` 通过；未重复49项整套、重装或启动托管模型。

R1原生协议四例、两次大输入超时和tiny真实成功继续绑定R1原身份。R2不改有效配置的原生命令投影或Linuxstdin路径，但这些历史记录仍不改称R2重跑。作者的R2完整材料模型审查仍在途，未登记approve；本次复核也未将前片eee的CI/远端终结计作本片验证。下一步按实际模型结果同步状态，再普通交付及核本片精确CI/远端；状态文字应同步顶端旧47项摘要及历史“当前在途”措辞，避免恢复入口与最新结果矛盾。

## R3 新增证据与独立重现

R2自托管真实Codex任务随后返回 **request-changes**。原始材料 `.ergora/checks/ac3b2-invocations/r2-hosted-review/codex-review.md` 的SHA256为 `55c85e0def83809d7018fe411d53d5df214a85b48667541ef2030d566adca0a3`。它对所给源码做静态审查，明确没有运行命令/测试；未提供的快照/准入helper和未变六阶段不在其核实范围。它的两轴原发现分别为：

- **Standards：P2 blocking，Persist argv after Windows executable resolution。** `agents.py:64` 先保存command.json，`processes.py:31` 随后将argv[0]替换为解析后的exe，实际Windows启动argv与记录不同。建议在进程所有者完成解析后、启动前保存。
- **Spec：P2 blocking，Make excessive JSON nesting a durable result failure。** 成功退出的后端若返回超过解码递归限制的JSON，`RecursionError`不在 `agents.py:73` 和运行层既有异常处理中，跳过最终保存，DB留下running且无finished。建议只在结构化结果错误处理内加入此异常。

协调审查者随后独立确认两项，均属于本片原合同；上方R1/R2仍保留当时范围内的结果，新增证据使本片在修正复核前继续处于request-changes，不能凭此前局部通过提前交付。

### C3，P2：Windows记录尚未解析的argv

以仍匹配R2冻结SHA的site-packages实现，沿真实 `run_input → agents.invoke → _run_windows` 检查，只有Windows Job、Popen及exe解析使用隔离spy。CLI0/记录succeeded时，protocol command.json的argv[0]为 `codex`，交给gate的原生argv[0]为 `C:\\Runtime\\codex.exe`，其他参数一致。此为实际R2路径加生命周期spy，**未执行原生Windows Job/进程**；源码也明确有该替换，因此无需把平台未实跑误当不可达。

合同要求保存“实际argv”，普通Windows原生命令名即可触发；实际被选择的exe路径不能从当前PATH可靠追溯。最小目标是在进程所有者完成Windows解析后，保存与送入gate相同的argv；避免记录后再重复解析，也不需要新增命令执行框架。独立证据保存在 `.ergora/checks/ac3b2-invocations/reviewer-r3-windows-argv.json`。

### C4，P2：过深JSON结果逃逸并遗留running

固定R2安装包 `agents.py` SHA后，以临时真实Codex命令夹具写入10,000层、20,001字节的JSON数组并退出0。实际进程返回succeeded/0；CLI返回2并输出解码递归错误，DB记录仍为running，finished/error均为空。没有调用托管模型；夹具是外部结果解析的真实进程输入。

这违反“invalid structured result均可见和持久”的原合同，且无需大体积输入即可到达。最小修正是在现有结构化结果读取/验证的异常处理加入 `RecursionError`，沿既有failed/finished/CLI1路径持久化；不提高递归限制，也不增加运行层吞全部异常的兜底。独立证据保存在 `.ergora/checks/ac3b2-invocations/reviewer-r3-recursion.json`。

该轮重现固定R2安装文件而非正在修改的工作区。修正版scope、实际验证及同片复核待作者提供；本节仅确认新增发现与最小目标，未宣称修复完成。

### R3 生产修正预检，最终回归待收口

随后收到的 `review-r3-scope.json` SHA256为 `84ec991d49ccb47ab73c65c6150a77771cf212157d6ff05d82bb6bc369ba5cac`，冻结diff SHA256为 `b22afe81ad145ee61d020f4f95b7473d6a8a251f0044c1490b335b0e077b2271`。五个生产文件、测试及 `processes.py` 与该清单一致；PLAN/交付记录因包测试真实失败后的状态纠正已变化，最终文档/测试身份待另行冻结。核心修正身份为 `agents.py` SHA256 `2703e318c46765f061bbeb55b1a31c432c9e9f58d3265cf275c8242a872670fa`，`processes.py` SHA256 `8b71a48351a8823bf712ad0735b369e829d3a259010ce8aebec6792b42269eb2`。

生产修正的定点检查已通过：C3由 `processes.run` 接受有实际消费者的可选 `command_record`，在Windows解析一次后、送gate前记录argv，`_run_windows` 不再第二次解析；`agents`转交记录路径。此接口归进程启动事实所有者，未新增转发模块，也没有多写一份命令。独立执行实际 `run` 函数代码，仅替换平台名、exe解析及Windows gate为隔离spy：解析恰一次、记录先于gate且逐项相同、调用方原argv未变；未运行原生Windows。

C4只在既有结构化结果错误处理中加入 `RecursionError`。独立真实临时Codex夹具返回同一10,000层/20,001字节JSON且退出0，源码路径现CLI1、failed/finished、递归错误可读、CLI与DB一致。又在真正导入site-packages的Python3.12包复核同一路径，结果一致；没有通过修改递归上限获得结果。证据分别为 `reviewer-r3-fixed-windows-argv.json`、`reviewer-r3-fixed-recursion.json`、`reviewer-r3-package.json`。

本次还独立逐份重算360个源码/wheel/安装文件身份、最终wheel SHA256 `ea7f45f3818e23f08b1da86b40420bdf6f9f0ee88b8f5d9d4dce9d3932eef961`，一致；安装包实际 `reference.verify()` 为283/PASS、runtime_started false。未重装或重复整套回归。

最终回归尚不关闭：作者当前Python3.11源码六套47 passed/16 skipped；Python3.12包46 passed/1 failed/16 skipped。已读失败日志：2,000层JSON在3.12尚可解码，生产已按无效结构返回failed/finished，失败在回归额外要求错误含recursion，不能归为生产失败，也不能把该反例当作已覆盖递归分支。此前两次不存在测试文件的收集前失败另行保留，未计测试通过。计划只加深反例到跨当前版本确实超阈值的10,000层后复核；同片最终scope/实际结果及R3模型任务结果仍待更新。

### R3 最终本地结论

最终本地复核通过。**C1、C2、S1、C3、C4全部关闭；需求符合性和维护性在已列检查范围内均通过，无新增finding。** 此结论承接上方修前重现、生产/安装包探针及最终证据核对，不删除原R1/R2/R3失败记录或两轴原始判断。原生Windows端到端、普通候选提交后的精确CI和远端身份仍留待后验；本报告不把本地通过写成整个交付已完成。

最终11项身份使用 `review-r3-final-scope.json`，SHA256 `47d80158fccf956e7ead3404bf46151b2cc0ce7d3bd7ca4d0dcf9d678f040186`；冻结 `review-r3-final-tracked.diff` SHA256 `1300e1f0ea2b74d3d1a31a524d0622a65344cf8ef7152fddeaeaad3c433ff334`。逐项重算吻合，HEAD仍为基线eee09ef。相对于前一R3身份，只变更PLAN/AC计划/本片交付状态和测试反例深度；生产源码与已核R3 wheel及真实自审所供身份一致。两份下一片未跟踪文档 `docs/research/2026-11-09-task-mcp.md`、`docs/delivery/2026-11-09-task-mcp.md` 明确排除本片，前片归档也继续单列。

只读核 `r3-depth-source.log`、`r3-depth-wheel.log`：将JSON反例加深后的单例分别1 passed。Python3.12原先46通过/1失败及16跳过保持原日志，加深反例后只有这一例重验；未冒称最终源码/包又各跑了一次完整47项。Python3.11的原47通过和加深反例后的单例通过分别记账。当前47项每项都有对应通过证据；与R2的49项套件清单不同，不把两套计数混加。

真实R3自托管回执为 `r3-hosted-review.json` 及 `r3-hosted-review/codex-review.md`：run `6b43bb67fb4442e59b3686478f42157d`，239.98秒、succeeded/CLI0、decision approve。模型原始两轴分别为“Standards: No blocking findings”“Spec: No blocking violation found in the supplied paths”；明确这是只读所供源码的静态检查，未运行命令/测试，未提供的输入/准入验证器、完整六阶段和windows_job不能由它证明。保留这些限制，不将approve解释为正式批准或全仓执行验收。

协调审查者以SQLite只读连接和原始文件独立核实：

- 原输入、核验运行副本、protocol prompt与进程stdin四份58,029字节内容相同，prompt SHA256为 `ea2e007377acf381bea8941db1ee5e56c6e96319739de6e41cb8e37596c66a13`；输入digest为 `d94c1e110e2e99eae7fef1e23780408ac8f19e543f36ac9667d645669fcd57b7`。
- CLI打印的完整运行JSON与DB document相同，结构化result符合既有reviewer schema，result SHA256为 `c7bb8e22e3d1c39535d21ba97481a1a95d8227f2f0846c522e83fd79064914b7`；原review.md与 `artifacts.response` 正文完全一致，输入与运行的正式执行授权仍false。
- 从原任务正文提取五份完整文件，逐份SHA与该轮所给身份相同；CLI另提供变更上下文及完整文件身份。最终所有生产SHA与审查时相同。最终测试与模型收到的旧测试严格只差同一行两处 `2000 → 10000`，没有偷偷继承未审查的生产改动。

上述最终回执核验证据另存 `reviewer-r3-final-receipt.json`。R3包360/283身份、真实进程递归失败持久化和Windows argv分界已在前段独立核过，最终生产未变，不重复启动模型或重跑整套。下一按新候选实际提交身份核双OS必要CI、Windows真实字节/argv回归和远端一致性，再按原计划进入最小任务MCP。

## 候选Git对象与推送身份核验

普通候选为 `8208efa36cb9c76344d10d6789702e5bcc654ade`，已独立核唯一父提交为 `eee09efcba093839dba5407c474a7a5b46a3a2a0`，与 `candidate.json` 所列15项变更集合完全一致。集合为R3冻结11项、本报告和前片3项状态归档，没有隐含的后片实现。

本轮全部包/源码身份从固定Git blob读取，未使用已经开始AC3b.3实现的工作区。与R3最终清单比较，9项内容逐字相同；PLAN及本片交付记录的原SHA都能匹配候选文件的严格前缀，新增后缀仅追加本地独立结论和下一交付步骤。最终测试和生产源码保持复核身份。两份MCP后片文档在候选树内不存在。

独立以 `git cat-file --batch` 读取360个候选包文件，逐份与保存的R3 wheel及身份清单比SHA，一致；wheel仍为 `ea7f45f3818e23f08b1da86b40420bdf6f9f0ee88b8f5d9d4dce9d3932eef961`。再读取候选自身reference-manifest，283份冻结内容在候选Git对象与wheel中均符合原SHA。证据为 `reviewer-candidate-object-check.json`。

作者普通推送回执 `push-remote-identity.json` 记19:38:33 UTC远端一致。审查者随后独立以origin原生HTTPS进行只读 `git ls-remote`，**2026-11-08 19:42:05.550867 UTC** 实际分支 `refs/heads/refactor/architecture-foundations` 仍指向完整 `8208efa36cb9c76344d10d6789702e5bcc654ade`。此前默认SSH查询退出128、SSH443连接超时；HTTPS查询成功，不把失败尝试算作身份通过。独立回执保存为 `reviewer-candidate-remote-check.json`。

本轮候选范围/包/即时远端核验通过，无新增finding。精确候选双OS CI及原生Windows终结尚待实际结果，未登记IV4或本片最终交付完成；不继承前片eee的CI结论。

## 精确候选CI与独立终结

审查者独立抓取[官方run 42516045882](https://github.com/626619403/Ergora/actions/runs/42516045882)及两个作业页面，run状态为Success，完整提交链接为 `8208efa36cb9c76344d10d6789702e5bcc654ade`。逐页核对selectedJobId、矩阵名称、完成状态，以及必要步骤日志URL内的完整候选SHA和job ID。再从run页面提供的job_groups_batch接口以 `attempt=1&batch=0&size=200` 独立读取全部作业：totalCount为2、hasMore为false，两项均completed/success。

- [Windows / Python3.12，job 128839172613](https://github.com/626619403/Ergora/actions/runs/42516045882/job/128839172613)：Build and install wheel、Packaged reference identity、Native application regression、Windows PowerShell 5.1 installer and upgrade四项均success。
- [Ubuntu / Python3.11，job 128839172876](https://github.com/626619403/Ergora/actions/runs/42516045882/job/128839172876)：前三项均success；Windows专用安装步骤按条件skipped。

固定候选Git对象中的 `.github/workflows/portability.yml` 确实运行完整tests目录，候选 `tests/test_composition_invocations.py` 中真实原生进程的混合换行UTF-8 stdin字节测试、选中可执行文件与command.json argv一致性测试均无跳过标记，10,000层JSON失败持久化反例也在该套件中。该次原生Windows成功补齐此前平台回归缺口；证据范围为这些应用回归和安装升级，Windows真实托管Codex/Claude任务仍不在本次验证内。独立汇总、原始HTML/完整作业列表及哈希保存在 `.ergora/checks/ac3b2-invocations/reviewer-final-ci-verified.json` 及其所列来源；R3保存wheel SHA256再次核实一致。

完成上述CI核验后，审查者于 **2026-11-08 20:04:45.210152 UTC** 再次以origin原生HTTPS执行只读 `git ls-remote`，分支 `refs/heads/refactor/architecture-foundations` 即时指向完整 `8208efa36cb9c76344d10d6789702e5bcc654ade`，退出0且精确匹配。最终回执为 `reviewer-final-closeout-remote-check.json`。

**AC3b.2b独立最终复核通过：C1、C2、S1、C3、C4全部关闭，已检查范围内无未解决finding。** 此结论绑定上述候选Git对象、本地R3证据、该候选双OS成功CI及最终即时远端身份；原R1/R2/R3失败、静态模型审查限制和检查边界全部保留。正在推进的MCP后片工作区实现与文档继续排除本片。
