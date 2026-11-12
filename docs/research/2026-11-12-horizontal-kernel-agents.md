# X2：Kernel 到端到端优化的横向流程与接入边界

检索日期：2026-11-12。承接[分类说明](2026-11-12-optimization-taxonomy.md)和[R1 kernel](2026-11-12-optimization-kernel-agents.md)，复用[R2低精度](2026-11-12-optimization-quantization-agents.md)、[R3通信](2026-11-12-optimization-communication-agents.md)、[R5显存](2026-11-12-optimization-memory-agents.md)、[R6执行图](2026-11-12-optimization-execution-graph-agents.md)、[R9模型／框架](2026-11-12-optimization-model-recipe-agents.md)的固定原件。本报告只补跨域调用、内部模型会话和原生运行交接；未安装依赖、调用模型、运行 GPU／训练／服务，未复现作者成绩，未改变产品计划或接口。

**建议把 kernel 能力作为多种职责共同使用的能力面，并沿既有 Forge campaign 补最小真实消费者。** 精度、布局、融合、执行图、通信、内存和整模并非七个互斥 agent。一个 Forge 架构角色可以同时设计布局、融合和低精度计算；一个 GEAK host_runtime 角色可以同时改 wrapper、布局与图；同一通信问题又可能需要架构设计、实现、集成和独立评价四种职责。角色能力不授予权限，也不代表已经找到完整训练／服务的消费者。[forge-paper] [geak-lane]

可直接复用为单体定义的是有明确受限调用合同的设计／分析专家及 KDA 资料。**Forge、GEAK、Fuser、AKG AutoResearch 应保留为原生子流程候选**；即使 `TritonKernelAgent.generate_kernel()` 是一个 Python 方法，它仍包含测试生成、多 seed 和并行 refinement worker，不能因此伪装成一次单模型叶调用。[ka-agent] [ka-manager] 四个系统均未被本轮证据证明已经支持 Ergora 要求的“每个内部会话完整继承全部结构祖先材料，并受父权限上限约束”；具体缺口见下文。原生完成只产生候选，沿用原 task/run/candidate、可信评价和 owner 采用门禁。

**当前分类是“原生 candidate 工具／流程候选”，不是已准入的嵌套流程。** 本报告建议的首个 **kernel 方向消费者**是现有 Forge 旧 pin 的 candidate 通路；D1 总体执行消费者顺序由 D0 统一排定；只有先证明全会话材料／父权限准入，再补原状态与真实消费者证据，才可以发布为可执行子模板。

## 固定范围和版本

|对象|本轮使用的固定身份|研究位置与边界|
|---|---|---|
|ForgeKernel 原生双层优化|研究主线 `b2c8ae8510e02c28576808910a6b8827721ab7dc`；**现有 Ergora adapter 必须保持 `5030503d3ff71851aa34c14b9caf13ebfa9d9a78`**|R1 已核主线；本轮额外读旧 pin 的 launch、agent command／policy、loop、reference generation。两版本不是可互换兼容承诺；不得静默升级。|
|GEAK v4 整模＋kernel 层|`ec97e49ca886f8d02f8415192fdaac45d1005d2a`|补读 `e2e_workflow.js`、`kernel_lane.js`、Python interface 与独立 runtime。AMD 推理服务流程，不授予通用训练支持。|
|KernelAgent／Fuser|`e0647170da36ef9b059ac0bd3d60103aa4ed378b`|复用 R6 pipeline／composer，补提取、dispatch、KernelAgent／worker 调用面。公开重组目标是给定 shape 的 forward。|
|AKG-AGENT AutoResearch|`64b84b59541c134279f5d2ee0a5f35de0ec40022`，`br_agents`|复用 R1，补实际 task→workflow→AgentLoop、scaffolder、prompt、LLM adapter、tools。Ascend／其他 DSL 支持仍按 R1 的逐后端准入。|
|NVIDIA KDA|`acdd79343c5e9d0c7cb96289f26fd3f1051ce785`|复用固定 basic-flow／agent-flow，作为任务、实验和候选记录方法；它没有本轮可核的统一原生调度器。[kda-flow]|

前三个代码项目和 AKG 的根许可为 Apache-2.0，KDA 代码为 Apache-2.0、文档／prompt 为 CC-BY-4.0；具体模型、DSL、容器、资料与子模块仍按 R1 逐项处理。本轮不重排自报收益，不把不同 benchmark、baseline 或硬件的数字合并。

## 四条真实流程：交接到哪里，证据到哪里

### GEAK：服务目标驱动 kernel 层，返回服务验证

原生路径是 `handoff.json → interface/run_e2e.py → e2e_workflow.js`：环境与 GPU 产品／ISA 识别→同负载 warm-server baseline／profile→按关键路径和 headroom 分流→先调 flag/env/backend→重新 profile→提取真实 shape、调用点和不可改 oracle→kernel 层→可逆 overlay／binding→同口径 A/B、实际命中及 parity／质量→最终可加载 bundle。[geak-interface] [geak-e2e] 这是一条跨精度、库后端、layout、fusion、graph、host runtime 与整模的流程；它保留服务 TP／GPU 集不变，把单 GPU 优化池与服务资源区分，不能把本次 kernel 优化顺便变成 TP 搜索。

**精确入口须按源码区分。** README 把递归层概括为 unchanged `kernel_workflow`；本快照 `e2e_workflow.js` 的 `KERNEL_WF_SCRIPT` 实际指向 `kernel_workflow/kernel_lane.js`，通过 `workflow(..., laneArgs(...))` 递归。独立 `kernel_workflow.js` 另承担 dispatcher／backend bake-off，再调用 lane；不能把层名称当成逐字相同的 CLI 路径。应保留该固定版本的实际路由，不在 Ergora 重写 Director、TechLead、engineer、verify、integrator 或预算循环。[geak-e2e] [geak-dispatch] [geak-lane]

最有价值的交接是“immutable extracted task＋micro 证据→可加载 overlay＋真实服务证据”。源码把 `no_engagement`、签名不匹配、capture unsafe 等列为真实集成拒绝；修复指令要求找到实际 dispatcher seam，在 capture 前预编译实际 prefill/decode shape bucket，并证明 `engagement_check > 0`。`result.json` 另保留 server identity、measurement alignment、validated regimes、config、overlay 和未确认的中间 win。新 shape／并发／长度超出 validated regime 必须重验。greedy 字节 parity 及可选 accuracy 路径有各自覆盖，不能成为通用任务质量证明；FP8 等改变语义的候选仍需 R2 的独立质量门禁。[geak-e2e] [geak-interface]

### Fuser：可融合子图→候选 kernel→forward wrapper

`Fuser.pipeline` 调 `extract_subgraphs_to_json`：先让 Fuser 多 worker 改写原始 PyTorch problem，再由模型从获胜代码提取 `subgraphs.json` 和精确 shape signature；dispatcher 为每个子图构造任务、并行调用 `TritonKernelAgent`；composer 读取原 problem、子图和候选 kernel，输出 `composed_kernel.py`／`kernel_function(...)`，`--verify` 时运行生成的 forward 自测并可按错误再改。[fuser-pipeline] [fuser-extract] [fuser-dispatch] [fuser-compose]

这是从子图回到一个 wrapper 的真实代码链，但**还没有项目训练／服务消费者**。composer 要求保持 op order、stride、padding、dtype／layout，目标是“original model's forward pass for provided shapes”；没有证明 autograd 注册、backward/JVP、optimizer update、服务 dispatch 或整步收益。子图形状还经过 LLM 提取，必须用真实 trace／输入验证；重组会改变 kernel 边界和中间 layout，因此不能累乘各子图 micro speedup。`verify=False` 时 `success` 可在没有执行自测时为真；CLI 必须显式记录验证开关。[fuser-compose]

KernelAgent SDK 本身也不是一个无内部结构的专家：默认先用 LLM 生成 test，再生成多份 seed，`WorkerManager` 派生 worker 验证与 refinement。提供 `test_code` 默认是追加，并不关闭自动生成测试；冻结外部 oracle 时可使用真实参数 `generate_default_test=False`，同时保留外部可信评价。当前公开 `generate_kernel` 的 success 说明生成／测试流程通过，不自动证明候选更快。[ka-agent] [ka-manager] [ka-worker] 适合保留完整 Fuser 或 SDK 微流程后输出候选；不把 extractor／composer 的内部生成测试当独立审查。

### Forge：架构决策→实现→同 job 判断与机制测量

原生任务冻结 description、shape／输入组、reference、语言／硬件、目标和预算；judge 由 teacher 生成，经过静态检查、与 reference 校准后冻结容差；架构／teacher 通过里程碑交给 coding／student，后者实现并经真实 runner 验证、计时和 profile，停滞后回 teacher 诊断／修订。被确认的 kernel 可以成为后代 reference；独立 probe 认证的硬件机制进入知识库。[forge-launch] [forge-driver] [forge-paper] 应保留这个方向内循环，而不是在 Ergora 再建 teacher/student 调度。

这里的“架构”主要是 kernel 的工作划分、dataflow、layout 与 pipeline，不是已完成模型结构／并行 mesh 搜索。原生 `timing=device|e2e` 可区分设备时间和每次调用的 host 代价；**operator e2e 仍不等于训练 step 或服务 E2E**。已有 backward 任务只能证明那些算子任务，不等于自动接通 forward 的梯度消费者；JVP、checkpoint replay、graph capture、真实库 dispatch 和完整模型需要新的外部合同。[forge-launch] [forge-paper]

现有 [kernel.py](../../src/ergora/kernel.py)／[driver](../../src/ergora/data/drivers/forge.py) 已保留 fixed native campaign、global config 摘要、原 run record、候选摘要和 unknown 对账；只能 Linux＋local delivery，操作是 plan／prepare／run／status。它没有通用子模板入口、父材料参数、父权限交集或完整取消。kernel 方向的 D1 应首先为这条已存在的真实消费者补缺口；升级到 `b2c8ae8…` 必须另片核接口、语义和原件，不能借本报告更换旧 pin。

### AKG AutoResearch：可编辑 kernel 项目→有界实验与保留／回滚

实际入口为 `LangGraphTask(workflow="autoresearch")`／脚本→`AutoresearchWorkflow`：验证 reference／seed（必要时先 KernelGen）→组装 Skill／硬件／API 资料→scaffold task directory→`AgentLoop` 迭代 read/edit/quick_check/run_eval→`KernelVerifier` 和 worker 评价→保留或回滚→session／report。`max_rounds`、原生记录和恢复应由上游管理，不把其内部计划／编辑／诊断重新画成一组 Ergora 模型叶。[akg-task] [akg-ar] [akg-loop] [akg-tools]

它适合实际算子或多文件 kernel 项目，不自动把候选装进训练／服务；默认 task 的 Model forward 对比不能覆盖全部导数。`quick_check` 可能仅语法检查；通过它不等于 KernelVerifier 通过。上游有路径／editable-files／phase 等工具约束、session resume 与超时 salvage，须保留；这些是原生项目规则，尚不是 Ergora 全部祖先权限上限的证明。[akg-tools] [akg-loop] [akg-ar]

## 横向技术能力 × 职能矩阵

下表描述需要协作的职责；**每一格都是合同／证据要求，不是一名新 agent**。同一精确定义可承担多个技术域，完整原生系统也可同时包含多列。G=GEAK，F=Forge，K=KernelAgent/Fuser，A=AKG；这些字母只表示可核局部实现，不能授予整行覆盖。

|技术能力|设计／约束提出|搜索／实现|集成／交接|独立正确性与质量|性能与采用证据|
|---|---|---|---|---|---|
|精度／量化|R2 冻结训练／PTQ目标、scale、累加精度、误差和质量阈值；F可设计算子数值路径|F／A／G可写特定dtype kernel；ModelOpt／TE管理其原生格式，不能由kernel生成器替代|格式、packing、scale、checkpoint与runtime实际匹配；G量化backend是服务配置候选|独立边界输入、数值动态范围；R2开发集＋留出质量；训练另验梯度和更新|设备micro、完整wrapper、step／prefill／decode、达到同质量总成本分别报告|
|layout／stride／packing|真实shape、非连续stride、alias、storage offset、对齐、partition；F架构角色、G memory/host角色|F／A／K可改tile／layout；G可同时改wrapper|producer→consumer的layout、cast／transpose、pack／unpack成本；真实dispatch命中|输出与梯度、view／in-place／alias语义，尾块／不同shape；packing还核R6样本边界|把转换、workspace和新中间存活期计入wrapper及全step，不能只计内核|
|融合／子图|K分解／F里程碑／G算法角色共同判断可融合边界|保留K多worker及composer、F/A原生搜索|生成wrapper、参数绑定、Autograd实现、服务overlay／fallback|原图顺序、RNG／dropout、mutation、导数；生成自测后另验冻结oracle|launch数减少可能换来寄存器／shared memory增多，验真实shape分布与整步|
|执行图／host runtime|R6约束capture区、地址寿命、动态shape与bucket；G host角色|G可改dispatch／预编译；F可改operator host路径|compile／graph重建、warmup、replay、stream／event同步与实际backend|捕获与非捕获、重放多次、形状切换、fallback、内存复用，不能以编译成功代替|分别记录首次编译／capture、稳态、重编译与内存；完整服务／step含摊销|
|通信／重叠|R3／R4冻结rank、mesh、collective／MoE路由、拓扑和message分布|kernel专家可写计算／通信融合候选；R3原生库／搜索器负责其支持范围|多rank ABI、buffer ownership、stream／event顺序和dispatch消费者；G固定TP不是TP搜索|多rank值、梯度、同步、退出／死锁／恢复；单GPU通过不足|micro带宽与暴露通信、SM/HBM争用、全rank关键路径／step分别衡量|
|内存／重计算／卸载|R5容量、激活／参数／优化器状态、峰值与host预算|F/G/A优化局部存储；R5原生流程决定checkpoint／offload|saved tensor、recompute边界、pinned buffer、DMA和graph生命周期|RNG、重放语义、梯度、恢复后更新一致；不能只核shape/dtype|全rank峰值、临时workspace、host／PCIe／NVLink代价及吞吐；新峰值可能推翻micro win|
|整模／训练／服务|原所有者冻结模型／tokenizer／负载／质量／预算；G有服务系统层|按瓶颈调用一个或多个上述子流程，候选分支隔离|wrapper→真实注册／路由→实际step或服务请求；G有原生overlay链，F/K/A需外部消费者|R9数值与模型验证、冻结留出、收敛／稳定性；内部Director／judge不代替外部审查|同口径paired重复A/B、方差、失败／no_gain、端到端业务目标后才由owner采用|

例如“FP8＋融合＋CUDA Graph＋EP overlap”横跨六行；其设计者可以是同一专家，实现与评价可以由不同专家负责。工程上先隔离单项干预，再验选定组合；换layout会改变量化打包和graph地址，融合会改变HBM/SM与通信争用，recompute会改变kernel执行次数。旧trace的瓶颈占比、旧autotune胜者和micro排名可能失效，应重新profile并重测组合。R2／R3／R5／R6的固定一手来源已分别支持这些约束，不能直接相乘各方向的收益。

## 内部每个模型会话：完整材料与父权限核查

本节的“满足”要求：所有实际模型调用，包括 teacher、student、生成judge的会话、editor、diagnose、summarizer／compact及恢复后的会话，均收到全部结构祖先声明的 instructions、context、Skill 和附件正文／受支持的原始附件；固定材料无静默删减，实际完整读取可审计；工具权限是父链上限与上游角色限制的交集。**只在最外层传 manifest 路径、让角色自行选择文档或提供摘要不满足。** 下表判断的是已核默认流程，不从低层可扩展函数推导已实现接入。

|系统／实际模型入口|源码已提供的能力|未满足的具体接口与边界|
|---|---|---|
|Forge 旧pin：`RealBackend.run_agent` 的teacher/student；launch的judge生成也以teacher进入；可选`goal_ref.generate`另有`/goal`会话|普通turn通过stdin接收上游拼好的完整prompt，`AgentPolicy.install(role, workspace)`每turn设置并添加notice；student离线／reference隔离、role写范围等原生限制真实存在。`goal_ref`另安装自身policy。[forge-runtime] [forge-policy] [forge-goal]|Ergora request只传task/campaign/global config等，没有祖先材料或父上限；`task.toml [agent]`只选backend/provider/model/effort/timeout。`RealBackend`和独立goal路径都没有消费父材料的接口。上游teacher可写repo／联网不代表父层允许；必须补交集入口，保留其更严role限制。不能改description或复制目录便声称每个turn和judge已读全资料。|
|GEAK standalone：所有`agent()`→`backend.runAgent({prompt,label,cwd,env,model,timeoutMs})`，嵌套workflow共享该runtime|是真实统一拦截点，独立backend扩展可包装每次调用；已有role／schema／agent timeline。原生Claude路径另有SDK／CLI，不能只适配standalone后称两条均支持。[geak-runtime] [geak-backend] [geak-run]|默认prompt仅组合角色资料与业务inputs，无Ergora祖先材料合同或读取回执；`task`是steer字符串，不是该合同。registry的Claude默认`--dangerously-skip-permissions`，Codex默认`--dangerously-bypass-approvals-and-sandbox`；原生SDK为`permission_mode="bypassPermissions"`。JS realm限制不是agent shell权限隔离，须在可信容器内强制父上限。修改backend是可行适配点，**目前未适配**。[geak-registry]|
|Fuser／KernelAgent：Fuser worker、shape extractor、主agent测试／seed、每个refinement worker、composer各自的provider／EventAdapter调用|SDK可传problem与test，生成／修订prompt可留档；部分OrchestratorConfig有isolated/deny_network旋钮。[fuser-extract] [ka-agent] [ka-worker] [fuser-compose]|`run_pipeline`与`generate_kernel`无统一祖先instructions／Skill／附件入口。只在problem_description附材料不能覆盖shape extractor／composer等全部独立路径；worker自行新建provider。Fuser extractor固定构造`isolated=False, deny_network=False`，composer验证同样如此，SDK worker直接subprocess跑测试；外层存在权限对象不产生内部执行限制。需所有provider路径覆盖和可信runner上限，现状不满足。|
|AKG：初始KernelGen；AutoResearch主loop、diagnose／compact及fast client；自然语言`--desc`还可另调模型生成reference|`scaffold_task_dir(program_md, context_files, extra_files)`是真实内容入口；program/context进入system，extra_files供read_file；AgentLoop注入LLM adapter，knowledge prompt传给内部turn。不是完全没有材料扩展点。[akg-ar] [akg-scaffold] [akg-loop]|默认逐context文件截15,000字符、总量40,000、fundamentals 20,000；`program.md`也经过该逻辑，超总额直接break、缺失／读取异常可能跳过；其余Skill按需，初始skill block默认8,000字符／top5，激活时注入上限6,000。提高参数可解决特定有限材料容量，不能证明全部会话／附件／读取已覆盖。main system与fast/compact的prompt不是一份通用父合同；初始KernelGen、`--desc`生成reference另走LLMClient。工具的editable/phase规则未消费父权限交集。须补强制材料通道、全会话覆盖和明确拒绝，不能把`context`元数据当全文继承。[akg-prompt] [akg-config] [akg-task]|
|KDA外部coding agent|basic-flow／agent-flow可作为宿主的完整资料；现有Ergora只读设计叶本来就能带祖先全文材料|KDA未提供一个接管其内部会话的runtime，所以只能声称宿主已验证的那次调用。若宿主再派内部agent，仍须逐次审计，不由KDA文档获得递归继承或权限保证。[kda-flow]|

“无模型的确定性 judge／benchmark”不需要虚构模型会话，但仍必须冻结其输入、执行权限和证据；由teacher生成judge的会话必须计入。所有临时editor／integration修复与重试都不能绕开上述入口。若父层完整材料包含上游 blackbox/student 原生禁止读取的reference，准入应暴露冲突并拒绝该组合，等待显式材料／权限修订；不能削弱原生隔离，也不能静默省略材料。

### 最少需要触及的真实接口

下表是应验证的接缝，不是建议修改上游调度；不能用一个“父材料已传”的外层参数替代各行的真实消费者。

|接入对象|最少的 provider／prompt／tool 接缝|准入前必须证明的事|
|---|---|---|
|Ergora→Forge旧pin|本地 `kernel._call` 的request与`data/drivers/forge.main`须传冻结父材料／权限身份，并有实际消费。上游普通turn在`loop/cli.RealBackend.run_agent`、`AgentPolicy.install`；独立reference turn在`loop/goal_ref.generate`。`scripts/agent-claude.sh`及`claude-goal.py`均读取`FK_CLAUDE_BIN`，提供一个**已存在、尚未适配**的CLI接缝。[forge-agent-script] [forge-goal-cli]|可先研究adapter自有CLI wrapper与可信容器上限：普通stdin及goal的`--append-system-prompt-file`都完整组合原native prompt和父材料，teacher/student身份可与原policy记录核对，临时文件不可被agent篡改。wrapper只覆盖CLI进程边界；CLI同进程内部再派subagent时，原policy的deny继承不证明全文继承，仍须可观测／可注入，否则拒绝未覆盖能力。不假定一次prefix已覆盖长会话／附件／恢复；不能修改旧pin源码后绕过dirty-source门禁，接缝不足就保留缺口。|
|GEAK standalone／native|standalone的`createRuntime.agent → backend.runAgent → backends/generic.buildInvocation/spawnAgent`；父材料可在统一backend调用前拼入，权限在可信容器与命令构造处强制。原生路线另有`run_e2e._invoke_via_sdk/_invoke_via_cli`与Workflow内部agent，必须单独准入。[geak-runtime] [geak-backend] [geak-run]|所有label、原生重试和递归lane都受同一父上限；container／job边界限制编译、server、shell后代；不能只覆盖外层SDK会话，或把JS执行realm当OS隔离。最小适配可先只支持standalone的一条后端。|
|Fuser／KernelAgent|`Fuser.worker`的provider／EventAdapter、`subgraph_extractor`的provider／EventAdapter、`TritonKernelAgent._call_llm`、`Worker._call_llm`及`compose_end_to_end.compose`都要覆盖；`OrchestratorConfig`／`runner.run_candidate`及SDK worker的测试subprocess是执行边界。[fuser-worker] [fuser-events] [fuser-extract] [ka-agent] [ka-worker] [fuser-compose]|多进程重建provider后仍带完整父材料和role身份；所有测试／重组命令受父上限，未verify和native fallback如实输出。只替换主agent的preferred_provider不能覆盖worker自行创建的provider，更不能覆盖完整Fuser。|
|AKG AutoResearch|`scaffold_task_dir`与`prompt_builder.build_system_prompt`解决强制材料；`AkgLLMAdapter.call`是主loop／diagnose／compact共同LLM接缝，但初始`KernelGen`的`AgentBase.run_llm`、`--desc`的直接`LLMClient.generate`另需覆盖；`check_connection`也直接调用fast client的generate，实调清单不能漏记。`agent/tools.build_tool_handlers`、`TurnExecutor`及原Verifier／worker的真实执行端共同限制工具。[akg-scaffold] [akg-prompt] [akg-llm] [akg-base] [akg-turn]|强制祖先材料不能进入可截断／top-k／按需分支；`compress._call_llm_text`使用独立summary prompt，也必须带父材料，prompt-too-long不能削掉强制材料。diagnose虽复用knowledge prompt，仍须验证完整而非截断。提高配置值只可解决容量，父权限仍须在tool／worker端实施，不能靠prompt。[akg-subagents] [akg-compress]|

对二进制附件，以上以字符串为主的入口未证明通用多模态传递；必须为实际后端验证原始附件与完整读取／理解接口，不支持即拒绝该组合。任何wrapper／provider适配的验收必须保存每个实际请求、完整资源映射和上限拒绝回执；本轮没有实现或运行这些适配。

## 原生生命周期要保留的实际范围

|流程|可复用的原生run／预算／恢复|不能据此承诺的操作|
|---|---|---|
|Forge|原campaign目录／`run.json`、step记录、`forge run`恢复、`status`；task预算与原loop停止原因；可选reference生成另有预算和绝对deadline。当前Ergora保留native record／unknown，对账后才续跑。[forge-launch] [forge-runtime] [forge-goal]|Ergora `operate`只允run/status，无cancel。杀外层driver不证明agent／GPU后代已停；不能把现有timeout标成完整native取消，也不能让恢复获得一份新预算。|
|GEAK|eval_dir、versioned handoff/result、phase/state续入、磁盘checkpoint恢复；`--timeout-s`／env取真实上限，SIGTERM可flush，原生workflow另有任务／时间预算。保留上游accepted/no_gain/timeout/error和provisional信息。[geak-run] [geak-interface]|独立runtime `spawnAgent` timeout只`child.kill(SIGKILL)`，不是所有后代／server取消证明；不能从SIGTERM salvage推导Ergora已支持取消。无kernel-task预算的tuning loop仍受外层时限，不能把budget=6解释成所有候选／LLM调用只花六次。|
|Fuser／KernelAgent|`.fuse/<run_id>`、subgraphs／kernels summary／composition、worker日志；迭代、LLM／test timeout；Fuser orchestrator有signal→cancel event→worker terminate/kill。[fuser-pipeline] [fuser-orch] [ka-manager]|这是局部worker清理，不是已核全pipeline持久恢复／status／cancel API。composer自测timeout固定2400秒，不由pipeline的每项timeout自动约束；每worker/max-rounds也不是全流程GPU-hour／token预算。|
|AKG|task_dir、session store、best／round记录、KEEP或回滚，AgentLoop `resume`，workflow timeout／取消后的salvage。[akg-loop] [akg-ar]|`AutoresearchWorkflow`会把workflow_timeout提高到至少`max_rounds × (eval_timeout+60)+300`，故调用者较小配置不构成父硬上限；脚本／高层workflow未证明把所有resume与远端worker取消接成统一外部API。需按具体入口验证原ID、剩余预算及worker状态。|

上游的账本、session、timeline和counter保留为其原生证据，Ergora只保存原ID及关联回执／摘要，不重新统计为第二权威账本。进程退出0、原生`PASS`、`success`、`ok`分别解释：例如GEAK退出0还可能`no_gain`或`timeout`，Fuser可未verify，AKG脚本可打印失败而正常退出。外层必须解析原生结构和实际artifact，unknown先按原ID对账，禁止超时后盲目新建。

## 一手论文补足的方法与泛化边界

- **ForgeKernel v1 §3–4、§6、附录A–C**支持“架构计划与编码分离、停滞反思、reference逐代封存、独立probe认证知识”。其主要NVIDIA实验是H100/B200、27算子／29配置，正确后在冷L2条件测device time，选择每配置最佳run；这不是整模吞吐实验，也没有统一等预算完整训练比较。judge按算子来源使用不同容差：梯度、GDN/KDA state等采用相应相对／尺度／cosine约束及相关key／长记忆输入，说明固定allclose阈值并不普适。论文明确仍可能局部最优，跨硬件知识必须再验证。[forge-paper]
- **GEAK 2025 v1 §3–4及Evaluation Scope**采用Generator→Evaluator→Reflector／Optimizer、hardware knowledge和可执行错误反馈；修复了“缺失测试调用／比较空stdout”等错误，将其改为真实tensor输出及一致seed。这是为何必须保留真实调用和冻结oracle的直接证据。论文明确窄TritonBench-revised测试可能高估正确性；execution accuracy是在成功compile的样本中计算，speedup只在通过的kernel上算。**该论文早于本次v4系统层，不能用其结果证明v4整模、内部权限或恢复。**[geak-paper]
- **robust-kbench v1 §3–5、附录C**用多初始化／多输入与forward/backward任务，先用LLM verifier软筛选再硬件测试、profile、进化搜索；编译／内存／数值verifier在各30个样本上的accuracy约0.82/0.80/0.73，不能作正确性裁决器。论文实测发现部分任务在未见shape上性能下降，backward优化更难；公开交付是benchmark／evaluator／数据／kernel，不把论文完整搜索系统当可调用SDK。这支持外部shape留出、真实梯度验证及同质量比较，不提供通用JVP保证。[robust-paper]

本轮未定位并核到能直接对应当前Fuser或AKG AutoResearch版本、同时说明其全部集成／权限合同的专属原始论文，因此相关接口结论以固定源码为准。KDA的既有方法文档不是原生执行能力证明；不以相关论文标题或厂商排名填补缺口。

## 最小输入、输出与证据合同

下列是接入原有定义、manifest与候选的字段要求，不是新DSL或第二调度协议。一次方向子流程可以由原所有者分配多个受限调用，但同一个candidate始终绑定同一冻结实验身份。

|合同面|最小输入|必须保留的输出／证据|
|---|---|---|
|身份／目标|父task/run/candidate与精确定义链；native版本／配置；模型／权重／tokenizer／dataset／reference身份；优化目标和质量阈值|native campaign/eval_dir/session/job/rank及操作回执；输入hash、源码patch／kernel／wrapper、导出／overlay／配置与哈希；无收益、失败、unknown不丢失|
|可执行语义|真实operator／子图signature、全部参数、shape分布／stride／layout／alias、dtype／scale／accumulation、mask／RNG；训练明确forward/backward/JVP谁消费|独立oracle输出、边界／随机／未见shape测试，所需导数／更新值、容差及误差分布；缺backward/JVP明确unsupported，不能以forward代替|
|环境／资源|GPU产品／ISA／数量／拓扑、driver/compiler/DSL/framework版本；mesh、stream／graph、workspace和host预算|实际探测身份、工具可用性／fallback、编译／加载／rank日志、峰值显存／host／临时磁盘；未执行项直接标记|
|完整材料／权限|全部结构祖先instructions/context/Skill／附件的冻结原件和来源顺序；父链permissions/limits与上游role policy交集|每个内部模型会话的role／parent／backend、完整请求或完整读取连续证据、材料清单与字节数／hash；实际执行边界／拒绝。摘要和路径清单不能替代正文或实际附件。超模型／附件能力明确拒绝|
|预算／生命周期|全流程wall、GPU/CPU时间、候选／迭代／并发、LLM调用／token、单步timeout和清理余量；原ID恢复约束|上游实际已用／剩余预算、各层原状态、操作所属进程／job、取消确认或unsupported、恢复一致性；外层unknown与原native终态分开|
|micro→wrapper|冻结的算子／子图baseline（含当前库／compiled路径）、真实调用与计时窗口|先测isolated，再测含layout转换、packing、allocation、launch、sync的wrapper；候选实际被调用的trace／counter／dispatch证据，禁止fallback伪赢|
|wrapper→step／服务|真实训练batch／tokens、optimizer／accumulation／mesh，或服务ISL/OSL／并发／请求分布／warmup、latency／throughput规则|完整step关键路径、所有rank峰值和失败；服务prefill/decode、TTFT／tail与吞吐、相同token工作量；paired重复、方差／噪声阈值及cold／warm口径|
|独立评价／采用|冻结开发集与最终留出、质量／收敛标准、独立reviewer与可信runner权限|原生judge及外部正确性／质量／性能证据分别保存，完整组合回归；原owner审批与候选身份。搜索方不得改oracle、阈值或采用结论|

实际命中至少形成一条链：`原调用点／dispatch条件 → 候选wrapper → 编译产物／kernel → 实际workload的调用证据 → 同一运行的完整step／服务指标`。只证明文件存在、import成功、wrapper微测更快或开关被接受，都不足以声明实际目标已优化。恢复后该链的版本／配置变化也要重新核定。

## 可组合方向子流程举例

1. **NVIDIA训练：FP8布局与融合候选。** 原所有者先冻结R2的TE／Bridge可用配方、loss／梯度／更新和全step baseline；R6／R7定位实际热点。设计专家把dtype／scale／layout／forward及其backward调用、graph／recompute条件交给保持旧pin的Forge原生campaign。上游保留其teacher/student循环，返回kernel和证据；原训练消费者补注册／wrapper／导数和命中检查，再分别验单项和选定的低精度＋融合＋graph／overlap组合，复测完整step和质量。没有backward/JVP或consumer时只能保留局部候选，不能发布为训练优化完成。
2. **AMD服务：量化／backend调优＋热kernel＋overlay。** 原所有者冻结模型与相同服务负载／质量标准，GEAK原生系统层先config再profile／提取，按固定源码调用kernel lane，返回可逆overlay／launch bundle；保持其内部验证和no_gain。外部可信runner独立重放实际dispatch、prefill/decode shape bucket、warm-server A/B和任务质量；多卡TP保持声明值。validated regime外的新长度／并发重新评价，owner决定采用，不由GEAK内部Director直接改变项目正式候选。
3. **Ascend算子：layout／内存候选再接通信或训练。** 有真实worker／DSL兼容环境时，以冻结forward和需要的导数reference交给AKG AutoResearch；原生quick_check→Verifier→KEEP/rollback保留。返回的多文件kernel项目交原框架wrapper与多rank消费者验证，再与R3通信后端／R5重计算分别和组合测量。AKG成功不意味着已经具备collective、autograd或完整训练流程；若需要子图拆分，Fuser只能在其实际CUDA/XPU支持范围作为另一可选生成流程，不能凭Triton名字移到Ascend。

以上都是未来真实消费者的组合示例，当前训练模板仍为只读proposal；没有一条被本次只读研究执行。

## 采用决策及 D1 优先的真实接口

|决策|具体对象与理由|D1最小可验收出口|
|---|---|---|
|**采用**|KDA任务／实验合同、R1独立oracle与robust-kbench防过拟合方法；沿用已有多roles／specialties、完整材料和权限编译|先用现有只读kernel设计专家输出可复核任务合同；资料可引用、不冒称已跑native流程。|
|**优先适配**|旧pin Forge campaign已有真实消费者、native ID和unknown；无需再造内部调度|在现有kernel操作及原owner中接一个可引用方向调用；覆盖judge生成、teacher/student、可选goal等所有实际会话的全文材料与父权限交集。先明确能力／不支持项，再提供原ID prepare/run/status/reconcile/resume；取消须有真实后代／GPU job终止证据，否则保持unsupported／unknown。|
|**条件适配**|GEAK完整服务层最能检验“提取→kernel→实际服务命中”；保留runtime与内部预算|只选一条实际后端路径，统一覆盖每个agent调用与递归lane的父材料／容器权限；保存原eval_dir／state、warm A/B／engagement／quality和恢复，不额外重建Director／TechLead。AMD服务资源未就绪不作运行承诺。|
|**条件适配**|Fuser／KernelAgent SDK用于真实CUDA/XPU子图候选生成；AKG用于具名Ascend／其他已核DSL|先逐入口完整材料／权限适配和外部冻结oracle，再返回可调用wrapper／项目；保留多worker／搜索／回滚。未经每个provider／worker／fast/compact路径审计，不发布完整继承；没有外部消费者时只标局部candidate。|
|**借鉴**|Forge机制probe、GEAK Amdahl＋engagement、AKG文件／session与保留回滚、Fuser具名子图产物|复用其原件和原生输出供原owner审查，避免复制成第二ledger；在已有candidate中分别记录micro／wrapper／全step／质量证据。|
|**暂缓**|通用任意kernel系统插件框架、把所有技术格各建agent、用静态图替代native执行、无公开实现的论文流程、跨硬件／训练支持推定|先完成一个真实consumer的材料、权限、原状态与证据闭环后再扩大；不以“父manifest已传”或“全部模型用同backend”提前关闭缺口。|

D1至少按依赖依次补三件事：**①所有内部会话的材料和权限准入；②原生运行与原所有者的操作交接；③实际消费者的候选证据回收。** 第①项应冻结完整祖先资源，保留来源／内容／附件类型与读取证据，超限拒绝；每个入口包含恢复和临时editor，原生更严角色限制保持。第②项只映射上游已支持的操作、预算和状态，补真实取消或明确unsupported，不二次分配native内部工作。第③项绑定patch／wrapper／native证据与真实训练／服务命中，可信runner重新评价后回原候选门禁。

当前 [run-input](../../src/ergora/agent_runs.py) 是受限单叶调用，不执行workflow前驱／端口；[StageDAG／WorkDelivery](../../src/ergora/review_dags.py)只为原六阶段的implementer／reviewer派生数据，原Temporal／Executor仍拥有运行；[WorkflowDefinition](../../src/ergora/workflow_definitions.py)描述静态结构与绑定，不能自动调用上述native系统。D1应为选中的真实流程补接口并复用原所有者，而不建立第二调度、账本或运行DSL，也不替换既有六阶段和candidate/owner合同。

## 原件与研究边界

私有原件／逐次获取receipt／UTC时间／SHA256／404失败回执保存在 `.ergora/checks/specialist-template-refresh/research/horizontal-kernel/`；`source-index.json`区分本轮新增、R1/R6等复用原件与本地产品源码，复用时重新计算内容hash但不冒称新网络获取。已有GitHub REST403／搜索连接器限制沿用R1记录，本轮只用公开raw／HTML固定源码，没有尝试凭据。探测错误路径的404只说明该URL不可得，不能证明项目没有某能力。

结论为源码与论文层面的选型／接口研究。没有验证目标机器兼容、原生取消成功、所有模型真实读完整附件、GPU正确性／收益、服务命中或完整训练；这些是D1／后续独立验收的出口。纵向报告的支持矩阵及原失败样本继续保持其范围。

[kda-flow]: https://github.com/NVlabs/kda/blob/acdd79343c5e9d0c7cb96289f26fd3f1051ce785/docs/agent-flow.md
[forge-launch]: https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/launch.py
[forge-driver]: https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/loop/driver.py
[forge-runtime]: https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/loop/cli.py
[forge-policy]: https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/loop/agent_policy.py
[forge-goal]: https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/loop/goal_ref.py
[forge-agent-script]: https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/scripts/agent-claude.sh
[forge-goal-cli]: https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/scripts/claude-goal.py
[forge-paper]: https://arxiv.org/html/2611.04998v1
[geak-interface]: https://github.com/AMD-AGI/GEAK/blob/ec97e49ca886f8d02f8415192fdaac45d1005d2a/interface/run_e2e.md
[geak-run]: https://github.com/AMD-AGI/GEAK/blob/ec97e49ca886f8d02f8415192fdaac45d1005d2a/interface/run_e2e.py
[geak-e2e]: https://github.com/AMD-AGI/GEAK/blob/ec97e49ca886f8d02f8415192fdaac45d1005d2a/e2e_workflow/e2e_workflow.js
[geak-dispatch]: https://github.com/AMD-AGI/GEAK/blob/ec97e49ca886f8d02f8415192fdaac45d1005d2a/kernel_workflow/kernel_workflow.js
[geak-lane]: https://github.com/AMD-AGI/GEAK/blob/ec97e49ca886f8d02f8415192fdaac45d1005d2a/kernel_workflow/kernel_lane.js
[geak-runtime]: https://github.com/AMD-AGI/GEAK/blob/ec97e49ca886f8d02f8415192fdaac45d1005d2a/interface/runtime/engine/run_workflow.mjs
[geak-backend]: https://github.com/AMD-AGI/GEAK/blob/ec97e49ca886f8d02f8415192fdaac45d1005d2a/interface/runtime/engine/backends/generic.mjs
[geak-registry]: https://github.com/AMD-AGI/GEAK/blob/ec97e49ca886f8d02f8415192fdaac45d1005d2a/interface/runtime/engine/registry.json
[geak-paper]: https://arxiv.org/html/2507.23194v1
[fuser-pipeline]: https://github.com/meta-pytorch/KernelAgent/blob/e0647170da36ef9b059ac0bd3d60103aa4ed378b/Fuser/pipeline.py
[fuser-extract]: https://github.com/meta-pytorch/KernelAgent/blob/e0647170da36ef9b059ac0bd3d60103aa4ed378b/Fuser/subgraph_extractor.py
[fuser-dispatch]: https://github.com/meta-pytorch/KernelAgent/blob/e0647170da36ef9b059ac0bd3d60103aa4ed378b/Fuser/dispatch_kernel_agent.py
[fuser-compose]: https://github.com/meta-pytorch/KernelAgent/blob/e0647170da36ef9b059ac0bd3d60103aa4ed378b/Fuser/compose_end_to_end.py
[fuser-orch]: https://github.com/meta-pytorch/KernelAgent/blob/e0647170da36ef9b059ac0bd3d60103aa4ed378b/Fuser/orchestrator.py
[fuser-worker]: https://github.com/meta-pytorch/KernelAgent/blob/e0647170da36ef9b059ac0bd3d60103aa4ed378b/Fuser/worker.py
[fuser-events]: https://github.com/meta-pytorch/KernelAgent/blob/e0647170da36ef9b059ac0bd3d60103aa4ed378b/Fuser/event_adapter.py
[ka-agent]: https://github.com/meta-pytorch/KernelAgent/blob/e0647170da36ef9b059ac0bd3d60103aa4ed378b/triton_kernel_agent/agent.py
[ka-manager]: https://github.com/meta-pytorch/KernelAgent/blob/e0647170da36ef9b059ac0bd3d60103aa4ed378b/triton_kernel_agent/manager.py
[ka-worker]: https://github.com/meta-pytorch/KernelAgent/blob/e0647170da36ef9b059ac0bd3d60103aa4ed378b/triton_kernel_agent/worker.py
[akg-task]: https://github.com/mindspore-ai/akg/blob/64b84b59541c134279f5d2ee0a5f35de0ec40022/akg_agents/python/akg_agents/op/langgraph_op/task.py
[akg-ar]: https://github.com/mindspore-ai/akg/blob/64b84b59541c134279f5d2ee0a5f35de0ec40022/akg_agents/python/akg_agents/op/workflows/autoresearch_workflow.py
[akg-loop]: https://github.com/mindspore-ai/akg/blob/64b84b59541c134279f5d2ee0a5f35de0ec40022/akg_agents/python/akg_agents/op/autoresearch/agent/loop.py
[akg-scaffold]: https://github.com/mindspore-ai/akg/blob/64b84b59541c134279f5d2ee0a5f35de0ec40022/akg_agents/python/akg_agents/op/autoresearch/adapters/task_scaffolder.py
[akg-prompt]: https://github.com/mindspore-ai/akg/blob/64b84b59541c134279f5d2ee0a5f35de0ec40022/akg_agents/python/akg_agents/op/autoresearch/agent/prompt_builder.py
[akg-config]: https://github.com/mindspore-ai/akg/blob/64b84b59541c134279f5d2ee0a5f35de0ec40022/akg_agents/python/akg_agents/op/autoresearch/framework/config.py
[akg-tools]: https://github.com/mindspore-ai/akg/blob/64b84b59541c134279f5d2ee0a5f35de0ec40022/akg_agents/python/akg_agents/op/autoresearch/agent/tools.py
[akg-llm]: https://github.com/mindspore-ai/akg/blob/64b84b59541c134279f5d2ee0a5f35de0ec40022/akg_agents/python/akg_agents/op/autoresearch/adapters/llm_adapter.py
[akg-base]: https://github.com/mindspore-ai/akg/blob/64b84b59541c134279f5d2ee0a5f35de0ec40022/akg_agents/python/akg_agents/core_v2/agents/base.py
[akg-turn]: https://github.com/mindspore-ai/akg/blob/64b84b59541c134279f5d2ee0a5f35de0ec40022/akg_agents/python/akg_agents/op/autoresearch/agent/turn.py
[akg-subagents]: https://github.com/mindspore-ai/akg/blob/64b84b59541c134279f5d2ee0a5f35de0ec40022/akg_agents/python/akg_agents/op/autoresearch/agent/subagents.py
[akg-compress]: https://github.com/mindspore-ai/akg/blob/64b84b59541c134279f5d2ee0a5f35de0ec40022/akg_agents/python/akg_agents/op/autoresearch/agent/compress.py
[robust-paper]: https://arxiv.org/html/2509.14279v1
