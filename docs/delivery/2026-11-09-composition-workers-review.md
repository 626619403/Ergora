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
