# AC3c.3 / CR2a 独立审查

日期：2026-11-09。审查者：`composition_workers_review`，新的独立上下文，未继承实现会话。项目及文档所有者为本仓库与 `docs/`。读取 `AGENTS.md`、AIHERO 索引、maintainable-project-delivery 及其 independent-review brief、codebase-design，并独立检查实际源码、冻结原实现和相邻调用者。未修改实现或测试，未安装依赖、启动服务、运行重型测试或写远端。

最新本地结论：**R3 Standards / Spec 均通过**，ST1/SP1、SP2、ST2/SP3 全部关闭；R3-S4 经独立处置为非阻塞建议。真实自身模板两轮原始 `request-changes` 均保留，未改成模型批准。最终精确提交、必要双 OS CI 及即时远端终结仍待核。下方保留各轮身份、发现和复核过程，以最后的 R3 本地出口为准。

## 初审结论

- **Standards：request changes。** 一项 P2（ST1）：bootstrap 将控制环境的整个依赖目录带入原生环境的优先搜索路径，违反所选原生依赖的归属与隔离。
- **Spec：request changes。** 同一项 P2（SP1）：所选原生解释器不保证使用其自己的 Temporal SDK。其余本片队列、活动、文件合同与兼容要求在已检查范围内符合要求。

ST1/SP1 为同一缺陷的两轴归类，关闭前不能登记本片完成；不把它重复计为两个实现问题。公开 v2 start/status、正式提交/读取及可信 executor 仍属 CR2b/CR3，Supervisor 新 worker 完整栈属 CR4；这些明确后续事项不是本次 finding。

## 范围与身份

基线：`77f93302c53f2d619bf7f84ff9dd23905f754b41`。分支：`refactor/architecture-foundations`。原始十文件清单、SHA256、tracked diff 及新增文件内容由 `.ergora/checks/ac3c3-workers/review-initial-scope.json`、`review-initial.diff` 和 `review-new-files/` 固定。检查了其中全部文件：三份计划/架构/本片记录、下列四份生产代码及三份测试。初审时生产与测试均仍等于该清单；计划与本片记录随后仅追加回归状态，另外的 CR1 CI 终结不改变本片生产身份。

| 文件 | 初审 SHA256 |
| --- | --- |
| `src/ergora/reference.py` | `8dfc879092e34f7a21e541ee54c759cd582782643027777139d09ddd4602d6fd` |
| `src/ergora/reference_workflows.py` | `cd4ac7e7a9295e8b61647d3feecfad970e154271ccf04713d32962118bda2fb7` |
| `src/ergora/reference_worker.py` | `13ce7cac9e7b6293f0ec48d5d7c1214b9628ec86a878ff540c387760a668163c` |
| `src/ergora/services.py` | `9d7ffa3a06384acff2802f5934c03f1bb6469ff84bbe2ea609602e6f7522bdb9` |
| `tests/test_architecture_boundaries.py` | `bd37b635ecbf1f72120f710f36c8b74785e1a4ab3aba6778c30c089898476fa7` |
| `tests/test_composition_runtime.py` | `ec47bd4a832fdf859cbdcd301d9d8c56d1aefd9577185400f1c78ad5561f415f` |
| `tests/test_composition_workers.py` | `5c1b3bc0c2af4c7e8941fe519b5d07c922953532806ce0456a3a009380adc5cd` |

相邻检查包括原 `dev_platform` 的 worker、connection、Activities、FileAdapter、DevelopmentWorkflow、DevelopmentTransport，原 `agent_platform` 的 environment/service/Supervisor 生成配置，以及自有 task envelope、VerifiedSpecClient、公开任务状态与提交拒绝路径。父运行桥记录用于核对 CR2a 与后片的职责划分。

## Finding ST1 / SP1 — P2：整个控制依赖目录覆盖原生 SDK

位置：[reference.py:110](../../src/ergora/reference.py#L110)，由 [services.py:142](../../src/ergora/services.py#L142) 的正式 worker 命令消费。

非 editable 安装时，`Path(__file__).parent.parent` 是控制环境的整个 `site-packages`。bootstrap 把它永久插到 `sys.path[0]`，因此原生 Python 随后导入 `temporalio` 时先查控制环境。控制环境安装可选 Temporal SDK 是本项目支持的用法；两环境的 Python ABI、SDK 或依赖身份可以不同。此时 worker 会使用错误环境的 SDK/依赖，跨 Python 版本时还可能加载不到相应原生扩展而启动失败。

独立只读复现使用 R1 非 editable 包生成的 `worker_command` 和另一个已有原生安装的 Python；删除继承的 `PYTHONPATH`，不启动 main/服务，只运行命令中**原样的 sys.path bootstrap 前缀**后检查模块位置。原生解释器及 `sys.prefix` 始终相同：无前缀时 SDK 来自原生 `.venv/lib/python3.12/site-packages/temporalio`，加前缀后来自本片 `r1/wheel-venv/lib/python3.12/site-packages/temporalio`。当前两者恰均为 1.34.0，仍已直接证明依赖所有者被改变。

现有 R1 SDK 旅程把安装的 `.venv` 链接到同一 wheel 验证环境，因此无法区分两种来源；其 15.05 秒成功不覆盖上述配置。

最小修正：临时添加该路径以加载 `ergora` 包，随后立即移除该路径，再从已加载包的 `__path__` 导入 `reference_worker`。当前 `ergora.__init__` 无外部依赖；独立探针验证这种方式同时保留安装包 Ergora 来源和原生 Temporal 来源。也可使用只指定 `ergora` 包的等价加载方式。补一项命令级回归，明确使用不同的控制/原生依赖位置，验证 Ergora 来自安装包且 SDK 来自所选原生环境；无需复制全部 SDK 工作流旅程。

## 结构、性能与测试检查

版本选择集中在 `reference_workflows` 的局部映射和 `WorkflowInput` 共同构造/执行 interface；两个实际版本分别拥有类型、队列和请求根。上层 bootstrap 只遍历共同 Worker 构造，未添加版本或厂商分支、第二个调度器、DB 或依赖。`reference_worker` 单一生产调用者成立的理由是原生模块初始化及异步资源生命周期所有权；它不是为凑复用抽取的透传层。`worker_command` 属于 reference 子进程构造 interface。`CompositionAdapter` 的新增拒绝和 Activities 的 submit 重命名分别有真实协议差异及 SDK 注册需求，未发现多余公共框架。

v2 submit 在文件发布前核完整 admission 与 legacy 投影；缺失、legacy 和不同投影三条拒绝分支均有可达输入。随后复用原 Activities 的容量/请求摘要校验与原 FileAdapter 的不可变发布、回执、批准和 fence。两队列绑定各自 request root，因此 v2 fence 扫描其实际未终结请求；原 poll/authorize/fence 名称和算法保持。完整 admission 已计入 context 容量，六阶段、原 signals/owner gate、候选/作者隔离均来自原 scheduler。

初始连接由 60 秒 `asyncio.timeout` 覆盖整个重试，不仅覆盖 sleep；错误配置的原验证在连接前执行。检查 SDK async context 实现后，确认 `AsyncExitStack` 负责关闭所有已进入的 Worker，fatal worker 错误也会取消外层任务并触发清理。SIGTERM 在正常运行期唤醒退出；R1 真实进程证据 exit 0。没有把当前过程推广为 Supervisor 完整栈验收。

每版本短活动上限 16，v1 上限不变；这不能证明模型吞吐或全局模型并发增加。新增 admission 检查随完整文档大小线性处理，并沿原 payload 上限；未发现新无界调度或轮询。15.05 秒是该本地合成协议旅程耗时，不是模型性能结果。新五项参数化测试分别保护两版本请求/fence 语义和三种真实准入错误；复用原验证 fixture，约 2.63 秒，未发现应删的重复断言或为实现细节增加的额外测试层。缺少的命令环境回归见 ST1/SP1。

## 独立核验与限制

- 独立重算 R1 的 367 个源码、wheel、非 editable 安装文件 SHA256，三者无差异；wheel 为 `cd7faef097516045061be99e79abf1dc7052d3af08c5df1db255a14c4396a589`。逐个读取基线 Git 对象及当前文件核对 283 个冻结文件，无变化。
- 读取实际回归日志，R1 五套受影响测试最终为 **55 passed, 1 skipped，40.07 秒**；不是仍在途的状态。没有由审查者重复运行该套回归。
- 检查 `r1/sdk-workers.py`、JSON、原生 worker log、三份完整 histories 及实际请求/回执路径。两正常 history 各 95 events，v2 的全部活动在 `.composition-v2`；未终结 history 24 events，包含新版队列 `dev_fence` 和正确 pending job。三份 SHA256 分别为 `e3f345b8bab0da6fd40728ba6d81724729df8ec10884e1f1fca5ec6113549049`、`393a39e1698d30e23625b30328e51844601080754e48f8f8fad919e175eab733`、`90d5100660ff28efac19d97e2ce014d58d17067f5f397f70effa16d19075a0da`，与运行记录一致。
- 审查者使用 R1 安装代码与真实 SDK 的 Replayer，独立重放本片 legacy/composition/unresolved 三份和 CR1 R4 原始 legacy/composition 两份 history，**五份全部通过，0.35 秒**；无服务或端口。
- 独立运行前述两环境命令前缀探针，复现 ST1/SP1；同时验证临时包路径方案可保留正确的 Ergora/SDK 来源。探针未改源码或测试。

这些证据包含真实 native worker、FileAdapter/Activities 与批准验证，但外部产物、回执、owner 仍是明确的合成材料。本审查不证明实际 Agent、候选命令、正式 v2 提交、Supervisor 新 worker 完整栈、两 OS CI 或精确远端交付通过。自身模板审查在初审时另行进行中，未引用其预期结论。修正后的包/命令验证与同片复核仍待完成；保留本节初审身份及 finding，后续以追加复核记录关闭。

## 追加独立复现：本片自身模板的两项发现

自身模板实际调用随后完成：R1 109.69 秒 `request-changes`，原始材料为 `r1/hosted-review.json`、`r1/hosted-review/codex-review.md`。实现者转交两项具体疑点后，审查者在上述**原样 R1 安装代码**上独立复现；未沿用模板判定替代证据。它们使初次扫描对剩余合同的判断收紧，原始记录保留。

### SP2 — P1：完整 admission 未绑定外层 task/profile

位置：[reference_workflows.py:88](../../src/ergora/reference_workflows.py#L88)。提交只比较 admission 的 legacy spec 与 `context['spec']`，未比较外层 `task_id`、`profile_sha256`。原 Activities 已比较外层 `request_sha256`，无需再重复该 guard。

独立复现从真实 R1 文件请求读取有效 context，只把外层 `task_id` 改成另一个合法 ID，完整 admission、spec 和 job ID 不变。使用真实 `CompositionActivities.submit` / `CompositionAdapter` / `FileAdapter`，只将最终 `publish` 替换为内存路径捕获以避免写文件。调用成功到达 `requests-composition-v2/other-task/composed-review-468519c303ac175bf7c8fabb.json`，admission/spec 仍属于 `composed-review`。单独把外层 `profile_sha256` 改为 64 个零也成功到达发布。前者将请求归入错误任务目录；原任务随后 fence 按正确 task ID 扫描，会漏掉这个作业，破坏取消对账。后者允许同一上下文的合同身份互相矛盾。

最小修正：在 v2 admission 所有者处同时核外层 task ID 与 `selected.spec['request']['task_id']`、外层 profile SHA 与 `selected.spec['profile_sha256']`，不更改原 v1/FileAdapter 或重复原 request SHA 校验。各加一项独立变异、发布前永久拒绝的合同回归。

### ST2 / SP3 — P2：SIGTERM 未覆盖 Worker 生命周期两端

位置：[reference_worker.py:28](../../src/ergora/reference_worker.py#L28)、[reference_worker.py:37](../../src/ergora/reference_worker.py#L37)。信号处理器在全部 Worker 进入后安装，却在 `AsyncExitStack` 退出、Worker 实际 shutdown 前移除。因此已进入的 Worker 在后一实例进入期间收到 TERM，或退出清理期间再收到 TERM，都会直接终止进程并跳过后续 Worker 清理。

独立子进程探针不连接服务，注入两个异步 Worker context 并发送**真实 SIGTERM**：在第二实例进入时发送，进程 `-15` 退出，只有两条 enter，没有任何 exit；正常等待收到第一次 TERM 后，在第二实例的 `__aexit__` 发第二次 TERM，记录 `handler=False`，进程再次 `-15` 退出，第一实例未清理。当前 SDK `__aenter__` 本身无异步等待，因此前一个窗口较窄；真实 shutdown 含异步 drain/RPC，后一个窗口不能忽略。首次扫描核实的正常单 TERM / exit 0 路径仍成立，但不足以覆盖完整生命周期要求。

最小修正：停止事件及 TERM handler 覆盖初始连接、Worker 进入和整个 ExitStack 清理；停止时终结启动连接任务，检查 entry 之间的停止状态，保持 SDK Worker 进入当前根任务以保留其 fatal-error 取消语义。handler 在所有 Worker 关闭后移除。用有明确暂停点的轻量 lifecycle 回归核对真实信号下的清理顺序即可，无需为这些窗口再次启动整套模型/Temporal 流程。

追加检查后的 Standards 阻塞为 ST1、ST2；Spec 阻塞为 SP1、SP2、SP3。等待同片最小修正、相应红/绿证据、新包身份及复核。

## R2 同片复核：身份与生命周期关闭，sandbox 发现同项修正未完整

R1 的六项针对性回归在原安装包全部失败（`r1/review-red.log`，6 failed / 1.78 秒），明确覆盖命令依赖来源、外层 task/profile 和三个 lifecycle 时点。R2 源码六套为 65 passed / 1 skipped，34.80 秒；R2 非 editable 包同六套为 65 passed / 1 skipped，41.45 秒。审查者读取实际完成日志，没有重复运行整套测试。

R2 wheel：`7d4d40222081d78872be500aef00a6b876a87f6f8562af539a8e601055fa139a`。独立重算 367 个源码/wheel/安装文件均等于 `r2/package-identities.json`；283 冻结文件保持。相对 R1 的相关源码/测试新身份如下，其余已列生产/测试身份不变：

| 文件 | R2 SHA256 |
| --- | --- |
| `src/ergora/reference.py` | `65d8301c9e01433baeefef47dc0fd1427dfd38f80c501c56918c1086e40af6e6` |
| `src/ergora/reference_workflows.py` | `f83ae9b0855b310e73761dea900e6b4ee906fb54562d4b69a9524f70b293aaea` |
| `src/ergora/reference_worker.py` | `2d4c4ca3aa2dbba2d008e8cdc5b68b599842073daadd3ad4cb53cdc360100cd1` |
| `tests/test_reference.py` | `80d90443e5f061fb9d8a2d5a82e9136af21c62bcb88ccc41810922cda88628cb` |
| `tests/test_composition_workers.py` | `6c5f7c0d221b151a1b0531bf12289e043f948fd8336110e215c167f32de7c5be` |

**SP2 关闭。** guard 只增加外层 task/profile 与完整 admission 的对应检查，未复制已有 request SHA 校验，也未改变原算法。独立再次调用真实 R2 Activities/Adapter，仅拦截最后的 publish：两种原始变异均在零发布时得到永久 `ContractViolation`；未变异有效 context 仍到达发布。

**ST2/SP3 关闭。** handler 在连接任务之前安装，并在整个 `AsyncExitStack` 之后移除；启动连接与停止等待的两个 task 在所有分支均取消并 gather。停止与连接同时完成时以停止为先，正常连接异常经 `connecting.result()` 传播，未转为假就绪。Worker entry 仍在同一 `_serve` task，保留 SDK fatal-error 取消语义；entry 之间的停止检查有可达的部分启动场景。私有 `connected` 算法只拥有原重试与超时，不添加通用 lifecycle 框架。

审查者在隔离子进程中重跑真实 SIGTERM 探针：连接中 TERM 正常取消连接并 exit 0；第二 Worker 进入期 TERM、清理期间重复 TERM 均 exit 0，按 two → one 顺序退出，两个 exit 均记录 handler 仍存在。此处只注入 Worker/connection，无服务、端口或模型运行。三项新增生命周期回归直接验证行为，不复制 SDK 内部算法。

**ST1/SP1 仍待关闭。** R2 临时导入 Ergora 后移除整个控制根，独立原生解释器模块探针已确认 live 进程中 Ergora 来自 R2 安装包、Temporal 来自独立原生 `.venv`。但这尚不足以使 SDK sandbox 重新导入工作流：其独立模块表再次导入 `ergora.reference_workflows` 时无法定位顶层 `ergora`，实际 native worker 因 `ModuleNotFoundError: No module named 'ergora'` / `Failed validating workflow ErgoraCompositionWorkflowV2` 退出。证据为 `r2/sdk-workers/worker.log`，不能登记 R2 native SDK 验收通过。

同一 R2 SDK 旅程另有较早的 harness 路径判断错误：`.venv` 链接路径与 canonical 原生路径做词法比较而未 resolve。原脚本/日志/目录保存为 attempt1；修正 harness 后才暴露上面的真实 sandbox 问题，生产/wheel 未变。前者不计生产 finding，后者是 ST1/SP1 修正尚未覆盖的实际 SDK 路径，继续沿原项追踪。

当前最小候选方案是在专用 bootstrap 中安装只响应顶层 `fullname == 'ergora'` 的私有 `MetaPathFinder`，委托标准 `PathFinder.find_spec` 定位所选 Ergora 包；其余模块一律返回 None，依赖仍由原生环境负责。不建议把控制依赖目录放回全局优先路径，也不建议为了导入而关闭 workflow sandbox。该方案尚待实际代码、独立环境 SDK 结果与复核，本节没有提前登记通过。

## R3 本地出口：两轴通过，三项实现缺陷关闭

R3 最终 wheel 为 `40ba51dca24f3146a61463a4886379140a8f79f2d8778e386e0770612c530b9a`。相对 R2 只新增包定位的 import-framework 实现，`src/ergora/reference_worker.py` SHA256 为 **`8551f6dcd5202cc101a015cbdc19352847a55fe752870e95bde39bb832daab10`**；上表其余 R2 生产/测试身份保持。新增检查的 `tests/test_reference.py` 纳入本片实质范围，前片 CR1 review 的状态归档及本报告不改变生产身份。

独立再次重算最终 **367 个源码、wheel、非 editable 安装文件**，全部相等；逐项从基线 Git 对象读取 **283 个冻结文件**，与当前文件及原 manifest 全同。实际日志为源码六套 **65 passed / 1 skipped，34.96 秒**，最终包同六套 **65 passed / 1 skipped，40.47 秒**。跳过的是原有 Linux 下 unsupported-platform 案例；本轮没有重复重型矩阵。

**ST1/SP1 关闭。** `_ErgoraPackage` 只接受顶层 `ergora`，使用标准 `PathFinder` 在选中安装包父目录定位；每个其他模块返回 None。finder 在专用 `main` 生命周期注册并 finally 移除，没有把控制依赖目录留在 `sys.path`。单个私有类和 `find_spec` 是 Python 导入框架所需的具体实现，没有扩展成插件容器。

审查者以 R3 非 editable 包生成的真实命令前缀，在**独立原生 Python** 中做无服务探针：使用真实 SDK 默认 `SandboxedWorkflowRunner.prepare_workflow` 成功；workflow definition 的 `sandboxed=True`，`ergora` 和工作流模块均未加入 passthrough。记录 finder 实际只返回顶层 `ergora`，来源是 R3 安装包；Temporal Python 模块及 `temporal_sdk_bridge.abi3.so` 都来自原生环境。控制 `site-packages` 不在搜索路径，原生环境缺少的控制依赖 `jsonschema` 也不可见，未出现跨环境依赖回退。

R3 真实独立原生 worker 旅程为 **15.74 秒**：新旧各六份文件请求及原批准/回执验证，旧 worker 不能在新版 bootstrap 前消费 v2，新版未终结请求的 fence 得到正确 pending ID 与 `CANCEL_UNCONFIRMED`；两 owned 进程均 exit 0，端口关闭。独立解析三份原 history（95 / 95 / 24 events），活动队列/名称符合合同，文件摘要分别为 `1f178ae6c4f0eedb555552b0113f24a476025d739e0b51c1ea9958631f26eefe`、`1417afd49a42ab7a4f385593183ffcda39eddc1da2827c5e472cc898599c8b0a`、`0863214875617ef7835d0e74095b539c51b84d32a69db36777322a4aa05bc510`。审查者再用 R3 安装代码独立重放这三份及 CR1 R4 原两份 history，**五份全部通过，0.35 秒**。实际外部材料仍为合成协议证据。

| 审查项 | R3 处置 |
| --- | --- |
| ST1 / SP1：原生依赖及 sandbox 导入 | 关闭；包定位范围、默认 sandbox 和真实独立环境均已核 |
| SP2：外层 task/profile 绑定 | 关闭；R2 独立零发布拒绝证据及 R3 完整包回归保持 |
| ST2 / SP3：已取得资源的 TERM 生命周期 | 关闭；连接取消、Worker entry 与完整逆序关闭均受同一 handler 覆盖 |
| R3-S4：前置同步准备期也要求受控 exit 0 | 非阻塞；见下方独立处置，保留模型原判定 |

### R3-S4：不采纳额外前置 TERM handler 的理由

R3 真实自身模板在 **114.76 秒**结束，原始结果仍为 **request-changes**。它指出 `main` 的安装验证/environment 以及 `_serve` 的 imports/load_adapter 位于 TERM handler 安装之前，并建议将 handler 提前到 main。该运行 brief 使用了比原 W2“启动错误明确、退出清理所有Worker”更宽泛的“SIGTERM covers startup”；本审查按原始职责与实际后果独立处置。

已逐段追踪这些前置操作：安装验证只读 manifest 和文件摘要，environment 只读配置/凭据并构造进程环境，包 finder 和模块注册只改本进程导入状态，FileAdapter 初始化只检查路径与信任配置。它们全部早于首次 connect、Worker 构造及任何请求发布。此时 TERM 的默认结束路径没有遗留 Worker、已持有的外部连接、持久写入或后续派工。首次连接任务之前就已安装 handler，原 SP3 的已进入 Worker 清理缺陷修正有效。还核对实际 Supervisor `process.finish`：显式 stop 的 `killing` 分支无论退出码均从 STOPPING 进入 STOPPED，因此前置准备期的 TERM 不导致该 stop 被当作服务重启。

要求这些尚未取得外部资源的同步准备也返回 exit 0，是可单独选择的退出语义；当前没有据此要求新增状态传递、信号 latch 或主入口 guard 的工程后果。**R3-S4 作为非阻塞建议不采纳，未重开已关闭的 ST2/SP3，也未把模型的原始 request-changes 改写为 approve。** 若后续将资源获取移入这些准备步骤，应同时重审停止职责。

### 两轮真实自身审查材料的独立审计

除阅读结论，独立核对 R1/R3 SQLite `agent_runs` document 与实际 CLI stdout、run/input/prompt/result 身份；两份 13 文件输入及保存副本的 tree identity、11 文件 manifest、共有 10 文件内容均一致，原 definition libraries 已删除。完整附件中的正文逐项核 SHA256；对 baseline-relative changed hunks 从固定基线重建目标后再核，而非用当前源码替代旧轮输入。

- R1 run `cb4de4c9b2194e2cb6584aa9f0bb6d83`，109.69 秒，11 个保护文件，附件 **62,978 字节**，SHA256 `0138d582ccb7bdea47cb0bb69e38f27ea7ca00dcd5d4e51066c120cf17c2bb89`。实际原生 stdout 的 MCP completed read 为 `0 → 60000 → null`，两页 bytes 分别为 60,000 和 2,978，另有分段重读；全部返回切片与附件相同。
- R3 run **`7f4f9f5687a1453792d2b581a09d1cf2`**，114.76 秒，**12 个保护文件**与当前生产/测试仍一致。附件 **69,386 字节**，SHA256 **`0049457c0b3d9c48bfd0d4c819015001744ff996096619b7cdeec60c614af2c0`**。实际 MCP read 为一次 `0 → 64000`、一次相同重读，再 `64000 → null`（5,386 字节）；三次真实返回的 byte slices、整份摘要和完整覆盖均独立核对。

两轮均核实实际 native MCP receipt/scope 摘要；protocol prompt 与原输入/保存输入逐字节相同，protocol result JSON 与最终保存结果一致。R3 最终 result SHA256 为 `33c5c7141f12658bdf642151a171ac221383ed8352ab987065d35717bee0f99a`，与数据库及公开原始结果相同；未用模型声称“已读完”替代原生读取记录。

[公开最终身份](evidence/2026-11-09-cr2a-self-review-identity.json) 与原 R3 record 字节全同，[公开原始结果](evidence/2026-11-09-cr2a-self-review-result.json) 与实际最终 result 文件字节全同；[公开历史](evidence/2026-11-09-cr2a-self-review-history.json) 的 R1/R3 两条与原轮 JSON 全同，保留两次 request-changes 及精确输入身份。

**本地 Standards / Spec 通过，无未解决的阻塞 finding。** 这证明本片版本 worker 接线、保留的六阶段合同及已列本地协议/审查证据；正式 v2 start/status 仍拒绝。Agent、可信候选执行、CR2b/CR3、Supervisor 新 worker 完整栈及 CR4 继续独立验收。最终 scope/静态文档、普通精确提交推送、必要双 OS CI 和即时远端终结尚需同片记录；本节未提前登记远端完成。

## 不同后端实际尝试的补充归档

源码/测试保持 R3。本轮只核运行事实与归档，未重新审查生产或运行测试。只读 Claude 认证状态命令 exit 0，显示 `logged_in=true`、`auth_method=api_key` 及凭据引用存在；这项检查只证明认证配置存在。

随后通过已安装 Ergora 的 structure-review / task-MCP 实际尝试 `claude-code`：run **`9672ad4094d04f8f8c26a9db6ebc51ff`**，**8.45 秒 failed / exit 1**。其 12 个保护文件身份及 **69,386 字节**附件与 R3 Codex 审查相同；本次 input digest 为 `45460b64be20b0633d112a077aa4b7f69ccab9689b3518f10b63b20281d3500d`，prompt SHA256 为 `3488f13f79b6ecbccb071065054726630636fcae1ec96da9b1a5ab6af31c5681`，已核原输入、保存副本及 protocol prompt。

独立核 SQLite run document 与实际 `claude.stdout` 完全相同；原生返回为 HTTP 400 Bedrock `ValidationException: messages.1: system content must contain at least one block`。原生最终事件 `is_error=true`，input/output/cache tokens 均为 0，`modelUsage={}`；未生成最终审查结果文件，**无模型判定**。认证存在不能证明该网关调用可用，未登记 Claude 审查通过。

[公开历史](evidence/2026-11-09-cr2a-self-review-history.json) 的 `r3-claude` 条完整保留原 failed identity 全部字段，并另外标明零 token、HTTP 400、无模型判定和既有用户授权的 Codex/ChatGPT 回退。该条与私有原记录逐字段一致；原 Codex 结果及独立 S4 处置继续保留。没有修改外部网关或扩展本片源码，既有两轴本地通过结论保持。

## 精确候选与 ST3 — P2：原生文件旅程未限定 Linux/WSL2

首次已推送候选为 **`c36bcdc028def80429f674d250ee65838d2adc73`**，直接父提交为上述 `77f93302c53f2d619bf7f84ff9dd23905f754b41`，共 20 个文件。审查者从该提交的 Git archive 独立核定最终 scope 的逐文件身份；scope SHA256 为 `bb4722c19ffa5ba422facf1111c8c7a89a01ebdb0198553d975d57c7044cc12b`。其中 367 个包文件仍等于 R3 wheel/安装身份、283 个冻结文件等于基线、12 个自身审查保护文件等于 R3。候选静态检查覆盖 9 份 Markdown、358 个本地链接/锚点及 75 条 CLI parser 示例，缺失为零，`git diff --check` 通过。提交内本报告 SHA256 为 `4d8e117605ac773230ac6ab8043f5b60099dbf926b09b3296e56ec146bc06109`；后加 Claude 归档及当前 CR2b 工作区不得反向作为该提交的内容证据。

位置：[test_composition_workers.py:18](../../tests/test_composition_workers.py#L18)。新增 `test_each_version_publishes_and_fences_only_its_own_requests` 的两个 version 参数直接走冻结 FileAdapter 的安全文件读取；`read_json` 调用 `read_raw`，后者在冻结 `dev_platform/adapter.py:62` 使用 `os.O_NOFOLLOW`。该接口属于 Linux/WSL2 原生文件执行语义，Windows 没有这个标志；本测试未提前限定平台。其他命令、包身份、准入拒绝和注入的生命周期测试没有这一要求。

独立隔离探针先用 R3 实际安装适配器读取已保存请求成功，再仅在子进程中临时删除 `os.O_NOFOLLOW`，相同读取立即得到 `AttributeError: module 'os' has no attribute 'O_NOFOLLOW'`；随后恢复属性。未修改冻结实现、生产代码、测试或请求文件。原有 `tests/test_tasks.py` 的 Windows reader 替换只存在于其自己的子进程，不能覆盖这里的直接调用。

随后读取 [c36 的正式 Portability 运行](https://github.com/626619403/Ergora/actions/runs/42535845046)，没有用探针预测代替 CI。**2026-11-08 23:45:13 UTC** 新鲜 GET 的完整 job-groups 为 `totalCount=2`、`hasMore=false`；Windows/Python 3.12 job `128899838743` 已 completed/failure。官方公开 annotations 进一步明确两个参数 `[1]`、`[2]` 都在测试第 36 行经冻结 adapter 第 62 行触发同一 `O_NOFOLLOW` AttributeError，实际摘要为 **2 failed, 681 passed, 481 skipped, 16 subtests passed，335.94 秒**。该次 job 页面 SHA256 为 `c90a02190967800246f02d6a276a9cd05d7258edef0aabd1318bfc801cd5ba5a`。

| Windows 必要步骤 | c36 实际结论及完成时刻（UTC） |
| --- | --- |
| Build and install wheel | success，2026-11-08 23:35:39 |
| Packaged reference identity | success，2026-11-08 23:35:41 |
| Native application regression | **failure**，2026-11-08 23:41:18；[精确提交绑定日志](https://github.com/626619403/Ergora/commit/c36bcdc028def80429f674d250ee65838d2adc73/checks/128899838743/logs/6) |
| Windows PowerShell 5.1 installer and upgrade | success，2026-11-08 23:42:08 |

同一时点 Ubuntu/Python 3.11 job `128899838545` 仍 in_progress，前两步已成功，不能登记整次 CI 完成。**ST3 作为 Standards 的 P2 同片阻塞打开**；R3 本地两轴通过保留为历史，不能据此宣称精确双 OS 交付完成。最小修正是在这一参数化文件旅程执行昂贵 fixture 之前增加明确 Linux/WSL2 平台跳过，保留其余跨平台测试与冻结/生产语义。修正候选的精确范围、完整双 OS CI、即时远端 SHA 与最终 finding 关闭另行追加；当前没有提前通过。

### ST3 最小修正的独立复核

实施者以 c36 为基础隔离暂存该测试，未把当前 CR2b 工作区改动加入：新测试 blob SHA256 为 **`8a62bf811bac9c86dc390be1b2c49a3890b739cdc43f179c7f49c6b41660a180`**。审查者读取 `git show :tests/test_composition_workers.py`，确认差异仅为 `import sys` 和上述单个参数化函数前的 `@pytest.mark.skipif(sys.platform != 'linux', reason='Native FileAdapter file semantics require Linux/WSL2')`。移除这两项后，整份 AST 与 c36 完全相同；没有跳过整个模块，准入拒绝与生命周期等跨平台测试保留。

为核实 fixture 时序，审查者把暂存 blob 的**原样 decorator AST**交给真实 pytest 内存 collector，并用可观察的 `original_input` fixture：`win32` 项为 skipped，fixture 未获取；`linux` 项实际获取 fixture 并执行 body。实际为 **1 passed, 1 skipped，0.00 秒**，仅内存探针，无测试或生产文件写入。该修正避免未受支持文件语义进入 fixture，也保留 Linux 的实际旅程。**ST3 的实现修正复核通过**；生产包身份不变，沿用已核 R3 367 文件及本地协议证据，不重复构建/重型矩阵。精确修复提交及其完整 CI/远端出口仍待后续追加。

### 原 c36 CI 的真实终态

**2026-11-08 23:49:51 UTC** 再次新鲜读取完整官方运行、job-groups 和两 job：run `42535845046` 已 **Failure**，两 job 均 completed，非取消。Ubuntu/Python 3.11 `128899838545` 为 **success**，Build/install 与 packaged identity 均于 23:35:09 UTC 成功，Native application regression 于 **23:49:16 UTC** 成功；三步全部带有 c36 精确提交绑定的日志地址，[原生回归步骤](https://github.com/626619403/Ergora/commit/c36bcdc028def80429f674d250ee65838d2adc73/checks/128899838545/logs/6)。Windows 的真实失败与其余三步成功仍如上表。没有读取到 Ubuntu 完整测试摘要，未推算其测试计数。

该次运行页 SHA256 为 `9650988345178eef950a74d4c8d8d856173c49efed2cfe44f5cc6009705fe8b1`，完整 groups 页为 `43b7b729f573123791f388f144f4dde75ce016a9bb2a02cee1c9be7c180625a1`，Ubuntu job 页为 `89a973f6872d5ccece1f55cc2d4f2c5dfed9749172ddad24108d3f914ff59407`。本次未以“某平台通过”替代双 OS 出口，也未对失败候选登记远端通过；后续普通修复候选需拥有自己的完整成功运行。

## ST3 精确修复候选

普通修复提交为 **`25d83ec5659e1f189a1ccd50e66cfd18b8d2e2a8`**，直接父提交 c36。审查者独立读取 Git 对象与 archive，核定只改变 `docs/PLAN.md`、本报告、本片 worker 记录和 `tests/test_composition_workers.py` 四个文件，逐文件 SHA256 全部等于 `.ergora/checks/ac3c3-workers/ci-fix-scope.json`，该 scope SHA256 为 **`c3146a2e6a6673a1b84af20d91b19f0f27b4e45c3ce1ea4e210121209f6b94b5`**。测试为上述已独立核实的 early skip blob；生产 `src/ergora` 整树 Git OID 与 c36 完全相同：`9eef0e8bbf01e9000769d1833fc5cf0515a10089`，因此原 367 包文件/283 冻结文件及 R3 SDK 证据身份保留，当前 CR2b 未提交实现不属于该候选。

基线至该候选 `git diff --check` 通过。按候选 archive 检查同九份 Markdown，为 **360 个本地链接/锚点，零缺失**；其中 19 条既有 `.ergora` 私有证据链接按本地实际文件核实，未声称它们属于 Git archive。新增加的两个本地链接均有效。九份文档及 README 的全部 fenced 内容与 c36 完全相同，原已通过 parser 的 **75 条 CLI 示例**保持，未因纯平台调度修正重复重型回归。

修复提交内本报告 SHA256 为 `a123963d50943096e304b4e65f041f58a80f6926fd11f3022865e8984c730c15`，含 ST3 finding 与修正复核；原 c36 的最终 CI 状态节在提交后追加，仍是明确的状态归档。修复候选自己的 [Portability #112](https://github.com/626619403/Ergora/actions/runs/42537178771) 绑定上述完整 SHA，Ubuntu/Python 3.11 job `128903960310`、Windows/Python 3.12 job `128903960118`。当前两 OS 的 build/install 与 package identity 已成功，原生回归仍在途；最终双 OS 及即时远端结论继续等待，不提前关闭出口。


## 最终独立出口：Standards / Spec 通过，ST3 关闭

**2026-11-09 00:06:32.460153 UTC** 新鲜读取修复候选的[官方 Portability #112](https://github.com/626619403/Ergora/actions/runs/42537178771)、完整 job-groups 及两 job 页面：run **Success**，`totalCount=2`、`hasMore=false`，Ubuntu `128903960310` 与 Windows `128903960118` 均 **completed / success**。逐项核实下列全部 **7 个必要步骤**为 success、有实际完成时间，且每个 log URL 都绑定完整候选 `25d83ec5659e1f189a1ccd50e66cfd18b8d2e2a8`。两 job 全部步骤均无 failure、cancelled、timed_out 或 action_required；没有用某一步或单一 OS 的成功替代完整出口。

| 平台 | 必要步骤 | 结论 | 完成时刻（UTC） | 精确提交绑定日志 |
| --- | --- | --- | --- | --- |
| Ubuntu / Python 3.11 | Build and install wheel | success | 2026-11-08 23:51:54 | [步骤 4](https://github.com/626619403/Ergora/commit/25d83ec5659e1f189a1ccd50e66cfd18b8d2e2a8/checks/128903960310/logs/4) |
| Ubuntu / Python 3.11 | Packaged reference identity | success | 2026-11-08 23:51:54 | [步骤 5](https://github.com/626619403/Ergora/commit/25d83ec5659e1f189a1ccd50e66cfd18b8d2e2a8/checks/128903960310/logs/5) |
| Ubuntu / Python 3.11 | Native application regression | success | 2026-11-09 00:06:08 | [步骤 6](https://github.com/626619403/Ergora/commit/25d83ec5659e1f189a1ccd50e66cfd18b8d2e2a8/checks/128903960310/logs/6) |
| Windows / Python 3.12 | Build and install wheel | success | 2026-11-08 23:52:16 | [步骤 4](https://github.com/626619403/Ergora/commit/25d83ec5659e1f189a1ccd50e66cfd18b8d2e2a8/checks/128903960118/logs/4) |
| Windows / Python 3.12 | Packaged reference identity | success | 2026-11-08 23:52:17 | [步骤 5](https://github.com/626619403/Ergora/commit/25d83ec5659e1f189a1ccd50e66cfd18b8d2e2a8/checks/128903960118/logs/5) |
| Windows / Python 3.12 | Native application regression | success | 2026-11-08 23:56:33 | [步骤 6](https://github.com/626619403/Ergora/commit/25d83ec5659e1f189a1ccd50e66cfd18b8d2e2a8/checks/128903960118/logs/6) |
| Windows / Python 3.12 | Windows PowerShell 5.1 installer and upgrade | success | 2026-11-08 23:57:17 | [步骤 7](https://github.com/626619403/Ergora/commit/25d83ec5659e1f189a1ccd50e66cfd18b8d2e2a8/checks/128903960118/logs/7) |

该次官方页面 SHA256：run `126e142e13403b3c5a0b5096ecaac7e5b8b1f5cffea713099945667a156074db`；完整 groups `94433402f7ac1f0c2cfc7871b982288e97264fef0fcc764a104b3703d829dbb1`；Ubuntu job `ac47d973d2e1e8d7e64c5b206005d3afe599983320660823225d2246258ddbbb`；Windows job `55784e10171184a7df72201de4a7d16aedbc16aef679f750befe803578ebb9e3`。成功步骤的完整 pytest 摘要未由此次可读页面提供，因此不推算测试计数；原 c36 的真实失败计数仍按前节保留。

完成上述官方核验后，审查者于 **2026-11-09 00:06:32.469133 UTC** 立即执行只读 SSH `git ls-remote`，于 **00:06:37.360137 UTC** 得到 exit 0：`refs/heads/refactor/architecture-foundations` 精确等于 **`25d83ec5659e1f189a1ccd50e66cfd18b8d2e2a8`**。该读操作不修改远端，未把先前推送回执或较早远端状态当作 CI 成功后的即时证明。

**ST3 正式关闭；当前 Standards / Spec 均通过，无未解决的阻塞 finding。** 本片身份为 c36 的 20 文件实现加直接子提交 25d83ec 的四文件平台修正，生产代码仍是已独立核实的 R3 包/SDK 身份。ST1/SP1、SP2、ST2/SP3 保持关闭；S4 非阻塞且不采纳的独立理由、两轮模型原始 request-changes 与 Claude 实际失败无判定均原样保留。正式 v2 提交/reader、可信执行、Supervisor 全栈及 CR2b/CR3/CR4 继续按原范围另验。

本节及原 c36 CI 最终状态是精确候选之后的审查状态归档，不改变上述已验 Git 对象；没有将当前 CR2b 工作区或本次追加文档反向纳入 25d83ec 的 CI 身份。
