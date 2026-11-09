# CR3b：正式单叶审查执行桥

日期：2026-11-09。基线`d8668a43abf5adcbabdf12d0ee5b1f570114262b`。状态：内部实现、最终发行/边界及真实自身审查通过，独立终核通过；普通提交推送及本候选CI/远端待完成。公开v2 start/status仍关闭。前片CR3a只迁入可信verify，本片完成E1/E3的内部执行支持，E4公开入口和真实Temporal旅程另片收口。

## 范围与复用

- 原Executor构造写project/claim之前，用已发布完整task文档、专用编译子进程的published核验和原编译/冻结bindings核同一创建。绝不在多线程executor构造会全局patch read的_Creation。
- 从信封完整manifest字节恢复私有包，沿inspect_manifest/preview做当前准入；只支持一个纯只读reviewer叶，其输入沿祖先直接到根task，结构祖先不执行端口。缺失上下文、同legacy不同manifest、多成员/依赖输入、权限不满足均明确拒绝。
- 动态任务包含完整stage context、已冻结原模板指令、经过摘要验证的全部依赖artifact、明确任务/叶子共同读取范围的同候选Git源码及diff。不能截断、跳过链接/子模块/非UTF8或超容量后声称完整。动态任务与静态祖先资料一起保留输入/候选/作业身份。
- 原进程monitor拥有取消/超时/未知和一次调用；现有Agent输入/限制/MCP所有者负责原生调用与材料。不另建正式调度、批准、候选或receipt。底层输入保留operator-supplied/非正式授权语义，外层正式调用快照单独绑定已核作业；不能谎称所有图端口已执行。
- 原v1流程和五阶段继续复用；CR3a的verify所有者不再复制。新增接口只为实际正式消费者，审查结构/冗余与恢复开销。

## 验收节点

- [x] R1：副作用前的发布创建/编译/固定选择准入；缺失/漂移/不同上下文/不支持的图拒绝，旧v1保持。
- [x] R2：动态候选输入完整可核、权限/容量拒绝、删原库后可执行；原monitor和受限后端实际协议/MCP结果保留。
- [x] R3：内部两开发模板六阶段、原人工批准/候选/checks/receipt保持；审查拒绝/超时/取消/恢复按实测分别记账。
- [x] R4本地：最终非editable发行/冻结身份、相关合同回归、新fresh-context两轴独立审查及自身模板实际调用；普通提交推送和精确CI/远端另核。

原verify-wrapper seam夹具属于CR3a历史，不能用于绕过新的正式准入；本片新增真正已发布v2创建与每阶段完整admission夹具替代其正式执行覆盖。真实模型效果不从合成原生协议推导。完整Supervisor栈及恢复出口归CR4；多成员/有界嵌套调度归AC4。

## 实施与在途证据

创建专用进程入口从reference搬到标准库reference_creation_process，由原应用入口直接别名和executor两个实际生产调用者复用，避免reference→executor→reference的静态环；专用实现仍在reference_task_creation，published复用原完整准入。初次源码创建/架构37 passed/17.99秒；Agent输入/架构33 passed/2.49秒。当前非editable R1包正在运行正式单叶六阶段/边界，未预记通过；初次no-isolation build缺setuptools，保留失败后改原隔离build成功，未改依赖声明。

reference_executor拥有正式候选资料、外层调用快照及继承阶段；读取Git原始对象避免工作树/CRLF转换，保留两完整任务范围树和差异、全部依赖字节与模板指令，限额不截断。agent_runs.run_input新增实际正式消费者所需的完整binding、结果schema及受监督调用选项，仍保存底层独立run；stage_driver只在已选组合请求中复用它，原生调用保持原路径，原monitor统一控制生命周期。正式输入授权来自外层已核创建/job，底层不改成自行授权。

新增现有原生fixture分支以真正published v2创建替代旧verify-wrapper人工封装seam，准备调用后删除原manifest和活动Agent/Workflow库，保留完整wrapper、祖先/Skill和同候选原件。两模板与六个副作用前拒绝、五个动态资料拒绝、真实协议review拒绝/超时/取消及一次调用恢复在R1包验证中。协议可执行程序是合成Agent，不能证明实际模型实现或审查质量；后续自身模板另实调。

R1非editable包新增原生执行 **17 passed / 106.98秒**；原d866包运行“缺完整admission”反例实际1 failed/2.98秒，明确显示旧构造接受并产生原副作用。原子restore初版源码/输入/架构46 passed/3.98秒，后续test setup合并进同fixture；最终R2另验，不移记身份。

独立者指出两项可达问题：实际selected backend覆盖的当前mode/policy应在原构造之前检查，依赖receipt允许100项×16MiB，不能收集完再按1MiB拒绝。当前已提前核实际binding/平台/mode/policy及MCP package存在，并在读取每项依赖前应用累计剩余额度；最终完整JSON/prompt限额仍沿原input所有者。另自检将Git blob逐项子进程改为batch-check先核总大小、batch读原字节及内容寻址表；两棵完整树引用同表，不重复未改文件正文。原子manifest恢复归workflow_definitions，复用原不可替换发布和inspect，无第二套资产发布合同。

当前R2新包及19项正式执行/容量/实际policy回归在途；正式task-mcp与真实自身结构模板将分开实测：前者证明实际组合协议和原生MCP回执，后者审本片实际源码，不从合成Agent推断模型质量。

R2非editable包369源码/包/安装与283冻结一致；合同111 passed/155.45秒、executor合成43 passed/403.64秒。它们仍用原fixture简化依赖，不能作为真实原scheduler的完整验收。新独立者CR3b-SP2/P1发现冻结workflow实际review依赖是verification+plan，plan保留starting候选；初版把所有依赖要求当前候选，真实流程会拒绝。已将fixture各阶段改为冻结scheduler真实形状，并在R2实际取得1 failed/11.99秒红例，detail=Review dependency belongs to another candidate。修正保留两条原依赖，只核verification当前候选、plan完整receipt等于批准者所批plan及摘要，全部正文共用预算，没有平行增加另一套plan装配。

R2真实正式task-MCP调用本身成功且MCP就绪，实际Codex返回request-changes，外层正确FAILED/independent-review=fail；原测试探针错误期待SUCCEEDED而报错原件保留。模型正确指出默认governance验收的边界reproducer/仓库map没有被合成syntax-only命令证明，不把这次模型拒绝记成功开发。随后探针显式区分协议完成与验收拒绝；后续R3须按真正原依赖再调用，不沿用该旧形状证明。

真实自身structure-review/MCP/Codex `gpt-6.1-sol` 201.41秒request-changes，完整222,714字节附件连续8页读至null，[输入身份](evidence/2026-11-09-cr3b-r2-self-review-identity.json)和[原结果](evidence/2026-11-09-cr3b-r2-self-review-result.json)保留。CR3b-SP3/P2指出成功monitor恢复时若invocation.json缺失，旧exists条件会跳过实际身份；已改code0组合必须有原invocation，并核成功状态/结果摘要。新增缺凭证恢复用例。模型非阻塞建议也已落实：Git stdout/stderr经selectors有界读取，超限/timeout立即kill并wait，不再将完整输出先写磁盘；批量metadata stdin用有界临时文件避免读写pipe死锁。正式receipt另外保存实际materials/prompt和MCP scope/audit原件并核摘要，沿原artifact所有者发布，离线材料不会只剩外部路径。

R3新包及最终回归/真实MCP/自身审查待验；R2的所有结果只属于其各自原件身份。独立者已复核上述源码修正和真实进程超限回收。Claude不可用的依据沿前片已记录的实际上游失败，用户明确授权ChatGPT/Codex回退；未重新探测已知受限服务，不声称执行/审查模型错误独立。整体正式Temporal/Supervisor入口仍归CR3c/CR4。

R3发行369文件/283冻结一致；真实原依赖shape的20项 **20 passed /224.60秒**，受影响legacy/verify **9 passed /90.42秒**，架构9项/0.13秒。正式task-MCP真实模型再次调用完成，MCP ready/candidate-bound，实际decision仍为request-changes，外层FAILED且没有通过检查；独立者核全部11份receipt产物、完整verification+已批准plan正文、prompt/input/material和MCP原件摘要。轻量1000文件/1015独立blob、89260原字节的材料准备三次0.214/0.168/0.680秒，仅该算法范围，不代表整栈提速。

R3自身真实模板 **301.20秒request-changes**，[身份](evidence/2026-11-09-cr3b-r3-self-review-identity.json)和[结果](evidence/2026-11-09-cr3b-r3-self-review-result.json)保留。完整276858字节附件5个唯一连续分页至null（第一页重复一次）已独立核原件。新增CR3b-SP4/P1：原monitor从候选checkout执行`python -m ergora.stage_driver`，候选同名包/标准库影子可在受限后端前执行；SP5/P2：审查Git读取未禁replace refs，与可信scope gate原始对象不一致。当前统一驱动改`-I -m`，Git帮助器统一`--no-replace-objects`，不改原monitor/冻结文件。新增真实安装旧R3红例 **2 failed /20.80秒**：候选影子实际执行；被删的base-only blob正文实际被替换。R4新包、22项完整原生回归、相关legacy及真实自身模板在途，未预记最终通过。此前R3通过不覆盖这两项修正。


## 最终R4本地收口

发行 **369源码/wheel/非editable安装文件一致，283冻结保持**，wheel SHA `5f44d0dfec32cfbc12c3070ffcf3210bd2d16c13780171871c5e3247136d7b4d`；最终executor SHA `7afa9d3cd16ddc0f95743e50a33d38647529a3d28d896459388c4047cde71b33`。安装包原生 **22 passed /250.68秒**，覆盖两模板六阶段、全部准入/材料拒绝、超时/取消/中断恢复、影子导入与被删base对象replace。原两模板×两后端四组合/五verify边界9 passed/87.13秒；四统一/导入注册路径与同五边界9 passed/94.66秒（五边界重复运行，不能合计为18个独立场景）。未变化的111合同及manifest/输入所有者保留R2各自原身份，不机械重跑未改范围。

R4真实正式task-MCP通过已隔离驱动，仍按真实模型request-changes保存外层FAILED/independent-review=fail，lower成功、native ready、全部11产物已独立重核；它证明协议与证据保持，不证明默认治理任务实现成功。真实自身结构模板 **205.12秒approve**，run `dee75f24f3e5419c90a93e3ae45c1847`；[身份](evidence/2026-11-09-cr3b-r4-self-review-identity.json)和[结果](evidence/2026-11-09-cr3b-r4-self-review-result.json)保留，5唯一页完整279029字节/首读重复一次均独立逐字节重算。原独立者逐项关闭SP1–5/M1、核20源身份及完整15份生产/冻结邻居原文与R4wheel一致，无剩余blocking finding。该审查没有运行测试或证明公开v2/Supervisor可用。

[独立两轴报告](2026-11-09-composition-review-execution-review.md)核本片实际范围；后续[CR3c公开运行入口](2026-11-09-composition-public-runtime.md)接双根扫描/start/status和真实Temporal旅程。当前不将手工六阶段或真实模型正确拒绝扩大为整栈成功。普通提交、自己的必要双OS CI和即时远端身份仍需分别记录。

提交前对新文件的staged whitespace检查发现creation-process模块多一个尾空行，已仅移除该LF；R4实测/自审原件保持原身份。R4-final重新发行369文件/283冻结一致，wheel SHA `bd72d38bde47930c82e7d0acaa37fb7aab1f3efc3d8ae778f3e85a180584c3ca`，与R4包唯一源码差异为该LF，Python AST（含位置）完全相同，最终helper SHA `8e6122720bed4c53b009a828d8039f7abfd322d29b106a6d6107e684be3f0914`。独立者确认该机械差异，不重跑未变化行为的模型/fixture，也不改写原自审身份。最终静态文档9份/62链接及75条CLI parser通过。
