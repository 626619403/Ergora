# AC4.1：嵌套只读审查分支的必需并行汇合

日期：2026-11-09。基线 `4538f4e44a3c301aedde570e130a342bc1c55714`。状态：本地实现、实际协议旅程、最终包及真实自身模板通过，[独立两轴及文档终核](2026-11-09-parallel-reviews-review.md)通过；已精确普通交付 `f9f4fc01546aa065f2fe32294a28c31387b2cf56`，自己的双 OS CI 七必要步骤及独立实时 HTTPS 远端终结通过。前片 CR5 已精确交付，自己的双 OS CI 42559480219 七必要步骤及独立 04:14:59.894943 UTC HTTPS 远端终结通过；不改原 a4cc 失败。

## 本片范围

消费既有 `parallel-review` 示例：结构、正确性、测试价值三个嵌套子模板，各自保留固定 Agent/后端/Skill/祖先上下文/有效权限，独立检查同一候选及原 verify/plan 原件；所有成员在本片都是必需审查。只支持 root task 逐层直映、只读且无 shell/network 的审查叶，最终显式 all-join 覆盖全部成员。任一缺失、失败、request-changes、超时或重复作者/审查会话均不通过。每个成员独立 job/worktree/monitor/receipt，命名为 `review:<稳定实例路径>`；复用原 per-job 去重/取消/fence 与账本。

保留 v1、现有 v2 单叶的六阶段活动顺序、stage 身份与结果。新分支由不可变完整 admission 内多个成员决定；此前多成员提交已在副作用前拒绝，不存在已支持的同形运行需改写历史。没有增加第二调度器、工作流全程递归或另一套作业账本。Temporal 只在原 review 阶段内以确定性路径顺序启动分支，遵守既有祖先/项目并发 scope 和配置的上限；单叶仍调用原 review stage。

汇合由可信 workflow 生成显式版本化 `composition-review-aggregate`，只引用各成员原回执的完整 SHA/job/路径，不冒充模型/人类 actor，也不另发一个假的 review 通过回执。原 outcome 的 evidence_sha256 继续绑定 verification 与 review 结果；证据索引和离线 handoff 共用原件引用规则。非必需建议、前驱输出、通用串行依赖、写执行者分配和三大领域模板默认组合留到后片，不能由此宣称 AC4 全部完成。

## 所有者与验收

- `task_envelopes` 继续拥有无 SDK 的运行形状与 outcome 原回执引用；准入/摘要/执行器消费同一选择规则，不在各层复制图规则。
- `reference_workflows` 在原 review 内协调分支；共享祖先并发 scope，过滤 review 子阶段，避免将先完成的审查误认为实现作者。原失败/取消仍交原 stop/fence，未确认外部作业保持可对账。
- `reference_executor` 按稳定 stage 选择唯一 member，复用完整 manifest/当前权限准入、调用快照/原监控/真实后端/MCP和回执；不新建模型路由或执行账本。
- `reference_task_reconciliation` 与 `handoff` 读同一原件引用，核多个成员各自的候选/回执/产物，旧单回执不隐式迁移。

先做必要的形状/隔离/汇合/并发/失败与引用回归；再构建非 editable 包核 source/wheel/install 与 283 冻结，实际公开 CLI + Temporal + 原 executor 跑三审查同候选、拒绝、取消/恢复，并核完整 history/replay/证据/handoff。确定性模型 fixture 只证明协议；大项还需真实用 Ergora 自身审查模板检查本片，另起 fresh-context 独立者审结构/性能/冗余与需求。各项只在实际执行后记通过，Linux 真实执行及 Windows 静态/原生检查范围分开。

## 当前实现与检查

新运行形状归原 `task_envelopes.review_members`：保留单叶直接输入，多个叶要求显式 all-join 的输出覆盖全部成员；输入端口仍必须沿完整结构父链直映原 task，前驱输出不被伪造。运行摘要、提交准入与执行器共用此规则。原 `reference_workflows` 仅在多成员 review 内用祖先 scope 的共享 semaphore 和原 stage 调用，汇合后查审查会话互不复用；authors 排除 review 子阶段。执行器按完整稳定 stage 绑定唯一成员，继续核完整已发布创建/manifest/当前后端策略和原模型证据。证据索引与离线 handoff 共用原回执 SHA 引用规则，旧 receipt 形状保持。

首轮定向探针 4 failed / 25 passed，是测试替换了 workflow.call 却仍期望其被替换前才完成的 dev_submit 名称转换；测试信号已改为实际被拦截的 dev_submit。修后源码定向 75 passed / 17.93 秒。未据此改调度生产代码。

使用 uv build 后的非 editable 包（首次 `python -m build` 因所选旧开发环境缺少 build 入口而失败，原日志保留）核 **369 源/wheel/安装文件一致、283 冻结保持**，wheel SHA `3664fe70244d707cc8673bd1db54b2eeff7531dbde60a5bcb816863f8f5e0340`。包上五组相关套件（parallel reviews、composition tasks/runtime/workers、handoff）**124 passed / 81.36 秒**；包括祖先并发1/2、作者过滤、失败/重复会话/取消、缺分支汇合和前驱输出拒绝、创建未知提交恢复与多回执 handoff 绑定。此处没有实际 Temporal 执行证明，实际旅程另记。

实际旅程首探针保留了旧验收根名称，`mkdir` 遇已存在目录立即拒绝；没有触碰旧数据或启动服务。R2 换新持久验收根后开始三任务公开 CLI/Supervisor/Temporal/scanner 验收。活动进程/耗时/history 与新独立审查、自身模板、最终交付尚未登记通过。

恢复时核实 R2 已在首次公开 start 因验收 venv 缺少 `a2a-sdk` 元数据而拒绝；该包只有应用与本片定向测试依赖，尚未装完整 reference 锁定依赖。原 stderr、未派送状态与 finally 的服务 shutdown 原件保持；不能据此记实际 Temporal 通过，也没有据此改生产准入。下一探针先按既有 reference requirements.lock 补齐同一隔离 venv，在新的持久验收根运行，重新核包身份与进程清理。

## 独立发现与修正

- **AC4-1／P2：合法透传输出的支持判定。** WorkflowDefinition允许输出直接绑定自身输入，运行桥此前无条件索引`node/output`导致KeyError。根/嵌套两种合法静态包在旧安装包均红；现在明确ValueError，历史摘要返回不支持，不能把未执行输入算成审查结果。
- **AC4-2／P2：聚合引用未完整绑定。** 旧包可接受与原收据矛盾的member stage/job ID/job SHA，仅receipt SHA正确即称matches；旧包三红一绿。共享规则改为`outcome_reference_state`，线上索引与离线handoff共同核四项原件身份，冲突标differs，缺失仍保留not_recorded/unavailable。
- **AC4-3／P2：祖先配额被窄子树等待者占用。** 原顺序先取项目/根再等子配额，会阻塞独立兄弟。合法嵌套窄子树/兄弟的旧包信号回归为红；改为在固定祖先树中由窄到广取得配额，原根上限1/2及兄弟可并发合同保持，不增加调度器。
- **AC4-4／P1：共享all-join依赖的指数遍历。** 24个join/29实例的合法图在旧包触发364,181次本模块调用；它远低支持节点上限。现在仅缓存已完成`(path,port)`覆盖，保留活动链环检测及透传拒绝。回归核有界访问量而非墙钟阈值，避免将机器启动速度作为语义。

前三修正源码61项通过。另一源码组合5失败/114通过暴露既有测试装配问题：unsupported用例创建只有解释器symlink的假venv，后续模块级installation复用它而丢失venv的SDK；同一测试改为复用完整`sys.prefix`目录，与既有提交fixture一致，没有改生产SDK检查。R4非editable包在此修正后五组相关套件 **130 passed /149.08秒**；AC4-4为其后发现，不能据此记最终缓存修正包通过。最终包与复审另记。

R3实际运行已取得三个并行review活动、worker停止期间收据完成、重启原run到达REVIEW_READY及只调用原三Agent；后续探针误读终态`status`而非`outcome`导致KeyError。原成功副作用和失败日志保持，附加观察34个原进程均退出。R4从相同原任务/状态目录继续：新候选重读第一条原run并重放完整history、收集证据与离线handoff，不重复成功调用；其余两条已创建的原任务继续验拒绝、取消及fence/对账。首条原执行仍属于R3原包，不能把新读取/重放当作新包重新生成原收据；两种身份分别保留。

## 最终本地证据

[R4实际继续旅程](evidence/2026-11-09-ac4-parallel-journey.json) **228.31秒通过**：首个原run到达REVIEW_READY；第二条同候选必需审查请求修改，原收据FAILED、结果BLOCKED；第三条真实活动审查经公开cancel停止，原收据CANCELLED、原结果CANCEL_UNCONFIRMED。后两条外部证据均确认无未决/意外作业，取消后等待10.3秒无迟写，再显式reconcile释放原claim并保持原outcome。每条8个原job、三个独立审查会话；成功聚合逐成员引用均matches，未汇合任务均not_recorded。三份完整history为183/189/178事件，完整输入、队列、候选与重放通过；三份交接包离线核验通过。只读独立者重核全部24原收据/116产物。正式shutdown并观察49个原PID/starttime及递归后代，0存活；采样不宣称捕获全部短命进程。

AC4-4修正后的[R5最终包身份](evidence/2026-11-09-ac4-parallel-package-identity.json)：wheel `e69663a6b0d9b682201943f00241208fced85e969214cfd09b6819857657c214`，**369源/wheel/安装文件一致、283冻结保持**。最终包行为回归62项通过；同轮原架构门禁8通过/1失败，因为handoff的新共享纯wire-contract依赖尚未登记。独立者核`task_envelopes`无应用/SDK导入后，在原架构检查中明确把它限制为stdlib-only基础模块，handoff只增加对该基础模块的许可，未放开任意应用依赖、未改生产包；**最终10项架构检查通过/0.19秒**。原失败日志保留，不能当作最初门禁已绿。

新独立者在R5实际安装包复做四类反例/正例：透传输出明确不支持、共享join有界遍历（52次coverage，旧242,786次，同一指标）、窄子树不阻塞独立兄弟、四项作业引用矛盾均拒绝，四项finding关闭。该调用计数不同于回归所用全部模块调用数，不混为同一指标，也不作通用速度承诺。

[R5实际只读复核](evidence/2026-11-09-ac4-parallel-reinspection.json) **15.01秒通过**：仅启动Temporal，worker/executor保持停止；三份原完整输入/history及SDK重放、证据索引和离线交接包均通过。194份原合同/请求/收据/产物/批准文件SHA及原Agent记录前后保持，未重复模型调用，结束后三端口关闭。R5仅给出这些实际读取/重放及缓存回归证据，不把R3/R4原执行归给新包，不宣称完整活动进程崩溃恢复或Windows原生正式执行。

自身结构模板真实调用 **135.07秒approve**，Codex `gpt-6.1-sol` / high / task-MCP，run `064340c46a714076b647842064462494`：[精确输入身份](evidence/2026-11-09-ac4-parallel-self-review-identity.json)和[原模型结果](evidence/2026-11-09-ac4-parallel-self-review-result.json)。附件231,383字节，包含16份完整源/测试/原所有者及继续旅程脚本。Claude不可用时按用户授权使用Codex/ChatGPT回退，不声称模型错误独立；该调用不宣称自己运行测试或核未提供依赖。

模型一项非阻塞建议指出架构测试只限制第一方依赖，未实际禁止第三方SDK，与“stdlib-only”表述不符。已在同一既有断言额外核`task_envelopes`的import roots属于`sys.stdlib_module_names`；**10项/0.19秒再通过**。只改测试门禁，生产包身份保持；原模型输入仍绑定建议前的测试文件，没有回写原回执或重复付费审查。新独立者已核该处置，并从实际stdout重组Skill读取及candidate连续8页至null，完整231,383字节、scope/prompt/native审计/结果和16份原源码身份保持。

本地静态核13份Markdown、340个本地链接/锚点及75条README/定义与后端手册CLI parser，无缺失；新独立者纳入报告新增两证据链接后核342链接/锚点及新增USAGE两命令，同样通过。`git diff --check`及最终源码/wheel/安装逐项身份保持。完整29文件scope本地两轴与文档终核通过；新增的本报告导航链接及精确提交/自己的双OS CI/远端身份在stage时继续分别核实。

## 精确交付终结

普通提交 `f9f4fc01546aa065f2fe32294a28c31387b2cf56` 的29份提交对象已由独立者逐份核对固定 scope，父提交为原基线，283冻结无 diff。该提交自己的 [Portability 42563729227](https://github.com/626619403/Ergora/actions/runs/42563729227) 于2026-11-09 05:02:56.122194 UTC独立读取为 Success：Ubuntu三必要步骤与Windows四必要步骤均成功，每条原日志链接绑定该完整提交，job完成属性齐全。随后同一脚本05:02:58.894557 UTC以明确HTTPS、禁用全局/系统URL重写读取远端，分支指向同完整SHA，exit0且stderr空。API首次403限流与官方HTML默认只取首批的中间限制保留在[独立报告](2026-11-09-parallel-reviews-review.md)，最终已按官方batch参数取齐两job；没有把分页遗漏当作Windows未调度。

本片必需嵌套并行审查精确交付完成；下一片为[AC4.2a版本化审查职责](2026-11-09-review-requirements.md)，建议运行、通用串行及写分配仍未据此登记完成。
