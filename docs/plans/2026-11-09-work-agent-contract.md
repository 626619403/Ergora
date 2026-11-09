# AC4.3c.1：专长执行者与原工作单元的组合合同

实施前设计草稿；已通过新独立Spec/Standards设计门禁，尚未注册格式或改变运行支持。基线`0fd881e4f21d2814eaf7ce0db47a7fd3c28c4144`为已精确交付的AC4.3b，其CI42584734023与独立明确HTTPS远端核验通过；本设计不继承它的运行验收。后续按独立纵切片接通，不一次替换原六阶段或为每个Agent运行一遍完整六阶段。

## 目标与真实所有者

将原正式任务的每个work unit交给明确冻结的专长Agent实例；保留inventory → plan → owner批准 → work units → integrate → trusted verify → review的原顺序。用户能组合多个实现、测试等专长，并在review继续采用当前只读串并行模板。结构祖先提供完整材料和权限上限；数据前驱只交付原产物，不成为父类。当前设计只将work与review映射到定义；inventory/planner等原绑定保留，其后按真实消费者另行版本化，不能宣称已支持任意职能拓扑。

|合同|继续使用的所有者|
|---|---|
|资源、端口、结构、父子权限、稳定实例路径|原WorkflowDefinition编译与完整manifest|
|unit ID、paths、依赖、任务/项目范围、原批准|原task spec/profile与创建/批准链|
|work调度和候选演进|原DevelopmentWorkflow.units和stage；必要的版本化差异留在其已有继承层|
|独立checkout、原claim、进程、检查、commit|原Executor.prepare/execute、monitor、唯一ledger|
|后端选择、完整输入、实际调用回执|原reference_executor/stage_driver与backend共有Interface|
|integrate/verify、审查聚合、取消/未知恢复、交接|原运行与证据所有者|

新功能不创建第二份可独立修改的工作DAG、候选账本、执行器服务或工单仓库。纯数据算法只在真实共用后提取；定义不保存活的Agent进程/可变会话。

## 显式选择与旧版本

拟在用户task-definition-v2的composition内增加可选execution对象，包含protocol、所选work子树、unit→instance分配及新模式。protocol暂定work-units-v1；该选择同时要求明确的review_protocol=dag-v1。存在execution才选择正式信封v5和自己的queue/request-root/活动/Workflow；没有字段仍逐字保持v1-v4。公共schema、创建、Input、实际调用及证据/恢复消费者全部接通前不允许发布可start的v5。

composition.members仍只保存reviewer；execution保存写成员和分配，避免旧review聚合意外把writer当审查者。v5的backend_overrides可选择两组实际成员，旧版本仍只接受review路径。所选binding、模式、实际能力政策、多样性决定、完整manifest与原unit分配共同进入原创建意图/信封身份；活动定义或项目绑定变化不改变旧任务。

下面给出拟定选择，字段是本设计的实现目标；生产消费者要求调整时先记录合同修订，不能无声改变旧格式。旧运行器在发布/发送前拒绝未知版本，不能从相同legacy投影取得新任务归属。SDK-free读取继续不导入Temporal装饰器，保持已修RD-1的控制端/worker可选依赖布局。

示例选择（摘要和路径由实际manifest生成，不复制占位值运行）：

```json
{
  "composition": {
    "manifest": "./delivery-manifest",
    "manifest_digest": "<完整manifest SHA256>",
    "review_protocol": "dag-v1",
    "review_instance": "root/review",
    "mode": "task-mcp",
    "execution": {
      "protocol": "work-units-v1",
      "instance": "root/work",
      "assignments": {
        "implementation": "root/work/kernel",
        "tests": "root/work/validation"
      },
      "mode": "workspace-task-mcp"
    },
    "diversity": {"policy": "prefer-distinct", "reason": "<仅实际同后端回退时填写>"}
  }
}
```

assignments的键来自原`input.work_units[].id`，值是manifest中的精确Agent实例路径；不按名称、提示词相似度或活动Skill库自动猜测。backend_overrides仍以精确路径为键，各值为binding与非空reason。新的execution只增加一份被原spec与完整manifest约束的固定分配，不再保存第二份unit路径或依赖。信封内把本选择扩展为经过准入的成员binding、政策、实际权限范围和原unit→实例映射，不把本机manifest路径作为未来运行所需外部文件。

## 工作单元和模板图一致

第一协议采用一对一分配：每个原unit恰好对应一份冻结implementer叶子，每个所选work叶子恰好执行一次。相同Agent定义可在不同稳定路径重复引用；不同实例有独立job、checkout、session和结果。一个叶子不能绑定多个unit而留下含糊的result端口，未知/缺失/重复映射在准入拒绝。

work子树以单task输入承接根任务，具有一个显式非空all-join终结输出，覆盖所有工作叶子。支持静态有界的嵌套、串行、并行、具名端口。将静态实例依赖投影为工作叶子的传递先后关系，与原work_units依赖的传递先后关系逐项相等；冗余直接边不改变语义，但遗漏或新增执行顺序均拒绝。端口来源也必须为相应已完成前驱。实际执行顺序仍由原units拥有，不再执行一份独立的模板work图。

权限有效写范围是project/task/unit与整条祖先请求的交集。unit路径必须完整位于叶子可写范围；缩窄后无法完成已批准unit时明确拒绝，不能只做可写子集后宣称unit完成。原路径规范、protected paths、无序重叠拒绝、依赖commit合并及批准检查保持。单checkout只有原job的一个写所有者；候选Git操作、确定性检查和commit仍由可信Executor执行，Agent不拥有正式批准或评分权。

所有叶子同时服从原max_parallel_units、全局executor容量及完整结构祖先限额。候选实现应扩展现有调度方法，不建立另一个持久running表；精确嵌套限额和独立就绪分支推进须由实际旅程/调度检查证明，不能凭静态图推断。

## 完整材料与实际写调用

旧text-only/task-mcp的read-only合同保持。新正式workspace模式需要backend自己的构造与能力合同，不解除旧composition.run-input的write/shell/network拒绝，也不新增任意可写的公开叶子入口。内部调用由原stage context、完整admission与owner已批准plan授权；已有material input快照仍保留execution_authorized=false，不把一个静态manifest或operator输入当写权限票据。

调用前恢复精确冻结树，完整装载root→leaf所有instructions/context与Skill正文/附件，记录资源与全部来源。沿原task MCP可提供固定结构资源的list/read；动态工作依赖的全部原产物先以内联进入实际输入，计入同一预算。当前资源schema没有外部server声明；不能因模式名称宣称支持任意外部MCP。声明的当前能力必须真实消费，无法装载的必需资料或MCP能力在调用前拒绝。

原workspace checkout由Executor提供，不能接受模型给出的任意cwd。实际提示包含原阶段模板、批准计划、unit与有效路径、完整祖先和依赖原件；新路径不能沿旧实现[:60000]截断依赖正文。超预算明确停止，不省略祖先、Skill或产物。实际binding、输入/提示SHA、资源/权限来源、原job/context/claim/session和模型结构化结果都保存原调用证据。

后端通过共有Interface选择；原生工具、配置和结果差异归本adapter，不在调度器按厂商分派。新模式仅显式开启需要的workspace工具和固定任务MCP，关闭ambient规则、Skill/插件、hook、未选MCP和隐式子Agent。必须用安装CLI的实际help/受控协议验证组合，不能把只读restricted选项盲目套到可写Claude。

第一版`workspace-task-mcp`与当前参考执行器一致，以Linux/WSL2为运行范围；固定资源服务依赖现有Linux no-follow文件描述符，原进程与checkout所有者也使用Linux机制。Windows已有安装、CLI、定义、预览及兼容读取能力保持；Windows包CI不等于此新写路径原生运行验收。后续原生Windows支持须提供相应进程/固定资源机制的实际实现与旅程，不能只去掉平台拒绝。

能力报告区分请求/有效上限与enforced/advisory/unsupported。可信容器或用户进程边界不等于OS隔离；原Git范围gate能拒绝越界最终候选，不能证明过程中没有临时读取/写入或网络访问。绑定显式current-container表示操作者选择该可信进程范围；公共默认不悄悄降级为它。所需强制路径/网络能力在实际sandbox不可支持时拒绝，不能把提示词当隔离。CLI模式可用和实际模型推理可用分开；Claude上游400仍允许已授权Codex回退，但每次回退保持实际binding和原因。

## work→review只运行原六阶段

可声明一个总delivery图：work子树输出接review子树输入。该跨阶段边只在v5可准入；review不能先于work，不能在verify后再运行writer，任意混合阶段回边、循环或未映射外部来源明确拒绝。完整总图的所选节点集合与阶段映射必须可核，不能无声忽略模板节点。

work/join输出只是原工作receipt与产物的具名投影，没有额外模型或正式job。原units完成后，仍由原integrate和trusted verify生成最终候选与验证证据，才进入review。即使声明输入投影work输出，review始终收到强制的最终candidate、批准plan和原verify材料；不能凭一个writer的文本绕过这些门禁。

所选work与review子树必须互不重叠，完整manifest的Agent叶子恰为两子树的并集；其它可达Agent或未映射成员拒绝。结构祖先和虚拟join可以保留，但其依赖必须能投影到原work→integrate→verify→review顺序，不允许外部未执行前驱。review根的task端口可继续投影原根task，或显式投影所选work的具名终结输出；其控制前驱最多为该已映射work调用。review内部沿当前DAG规则，不得读未完成审查或未映射外部结果。

跨阶段来源不经review-opinion parser伪装成审查意见。由真实work原件拥有者核原request/context/admission、unit映射、原SUCCEEDED receipt、实际backend/session、claim与所有产物字节，以及原工作commit确为可信integrate/verify最终candidate祖先的关系。候选、产物或已批准plan不符时在下游调用前失败。稳定port地址、共享join表与预算可复用已验证的纯算法，但原review v4输入/来源语义不能被新版本隐式改变。

后端多样性比较每个reviewer与所有实际被分配writer的后端，而非只看项目原implementer默认binding。prefer-distinct同后端需显式原因，require-distinct拒绝相交；实际会话和author来源检查继续独立存在，不用不同CLI推导模型错误独立。

## 失败、取消与恢复

复用原request/context/job、attempt-before-send、claim与不可变产物/回执；完成或允许恢复的原调用不能因活动定义、worker重启或项目绑定变化重跑写副作用。未知发送、未知清理保留原状态并由原ID对账，不把一个新run当旧run恢复。审批仍只由owner提供，自动复审不产生owner批准。

任一必需work失败/超时/候选或范围错误都停止后继并走原StopWork/fence；取消信号与结果同到时仍保持取消，不再发下游。模型写完但未完成原commit/回执的活动进程崩溃场景要实测既有恢复能力，不声称只重启worker就覆盖了该窗口；不支持的窗口明确保留人工对账。

## 可验收纵切片

|节点|范围|出口|
|---|---|---|
|C1设计|本合同、调用/依赖与新旧版本；梳理当前只读与原写入口|新fresh-context Spec/Standards审查；记录未决语义；只文档交付，不注册新模式|
|C2工作调用|先补真实backend workspace模式与完整材料构造，保留旧入口；不提前给正式任务虚假支持|受控真实CLI工具/Skill/MCP与拒绝证据、清晰能力矩阵；结构与性能审查|
|C3正式分配|一对一分配、图/units一致、新v5/原调度及可信写执行纵切片一起接通|两互补writer、串行原units及独立并行分支、完整祖先，原范围/检查/commit/verify保持；旧格式/history不变|
|C4跨阶段与恢复|真实work端口到review，所有writer后端多样性，取消/unknown与原ID恢复|原产物完整入实际prompt，独立会话；不漏任何requiredreview；原请求/调用不重复|
|C5交付|安装包/283冻结、实际CLI/Supervisor/Temporal/evidence/handoff、新旧history、自身模板与新独立审查|普通提交推送，核该精确候选自己的必要CI与明确HTTPS远端SHA|

如果C2需要新增不可独立调用的公共格式，则与C3合为一个可运行纵切片；可以先在私有调用构造中验证，但不能把未接通的模式保存为可用配置。若审查发现范围仍过大，在本表记录新的可验收子片及依赖，不把已实现项回写成未实现，也不把后片验证归给前片。

完成后再推进三领域默认组合、同一语义的低代码页面和新用户全旅程。训练组合仍交原可信runner/gate，CPU/GPU证据分别验收；不通过修改模板自改评分、权限、凭据或执行框架。


本设计已由[新独立两轴评审](../delivery/2026-11-09-work-agent-contract-review.md)通过，0finding；后续C2–C5仍须各自实现与验收。普通文档交付及本片最终静态状态见[交付记录](../delivery/2026-11-09-work-agent-contract.md)。
