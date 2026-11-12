# B2：一次授权、全程共用的六阶段预算

产品基线`f394945db894740ad23a81c62b4ad87c85a84511`。承接[D1的B2合同](2026-11-12-six-stage-native-consumer.md)及[B1完整材料](2026-11-12-six-stage-materials.md)。本文件是下一片的设计与实施计划，预算产品尚未实现，独立设计复核开放0／0；[交付记录](../delivery/2026-11-12-six-stage-budget.md)逐节点保存实际证据，恢复时先核[PLAN](../PLAN.md)、本文件、Git和所属交付。B1自己的CI另按原候选记录，不作为B2验收。

## 行为与范围

一次六阶段实例只有一个预算身份、首次授权起点和总截止时间。材料准备、编译、排队、重试、owner批准等待、模型／可信命令、结果收集和进程清理都消耗这段时间。重试、重启、观察原ID或恢复丢失回执不能重领预算。另限制这个支持形状内已知的模型调用slot；一次CLI启动不等于一次provider请求。

总额内显式预留清理时间：工作截止到达后停止新增工作，沿原fence确认；总截止时清理或结果仍未确认，保存原unknown／未确认及实际超时事实，不能报额内成功。后续只读观察和安全收尾继续使用原身份，不授权新业务，也不把新观察timeout加回预算。

保留原tasks／创建与提交意图、Temporal、Executor、候选、批准、attempt-before-send和monitor原件。不建第二调度器或正式账本，不改283冻结参考文件。本片不开放任意图、多个native、跨主机执行、provider费用／token／内部API请求数的严格预算。跨task项目级累计额度／并发没有实际共享消费者，不能从单份composition的`project` scope推导已实现。

## 源码事实与设计决定

已由实现者及一位fresh-context只读调查者分别核对实际调用路径；调查不是独立设计判词，也未运行预算测试。

|现有所有者|已核事实|本片决定|
|---|---|---|
|`tasks._definition`／原creation|现有preview在父进程读manifest／冻结材料，再进固定30秒的临时编译子进程。create重编并精确比较整个record，preview本身不写真实任务。|新增显式prepare写入，先落起点；安装遍历、`_definition`、材料及编译全部进入可停止的prepare worker，由同一绝对deadline监督。新preview读取原prepare，不能先无限读取材料再只给编译child计时。|
|`_Creation`的task lock／intent／七份合同|已有原ID冲突、不可变发布和恢复。|prepare原件仍属于task-creations，引用原定义、项目修订／注册及执行身份；creation/input绑定其摘要，丢回执读同一份。|
|`WorkflowInput`／VerifiedSpecClient／submission|完整input已进入原SHA、memo、history和原ID核对；attempt保存后只lookup。|新definition／input及独立queue／request-root；复用原提交链。到期不能使unknown允许重发。|
|原Temporal call／stage／approval|activity、stage、owner等待分别重新计时，review还有独立poll循环。|同一deadline限制排队、重试、全部等待；原workflow负责到期与fence，不另包父调度。|
|Executor／Git／Sandbox／monitor|构造／Git锁／部分Git命令在模型前；monitor有额外等待、快照、TERM／KILL及收集。ThreadPool的Future取消不能停止其线程。|先验证单job独立进程的接缝；让既有进程所有者监督整个job，不能只缩短模型timeout或在线程里改全局Git函数。|
|`processes`／stage_driver|supervised调用依赖外层TERM；普通killpg不能覆盖另建session的monitor，现有回收循环也没有总截止。|在原进程所有者集中绝对期限、停止／回收和未确认结果；旧原件保持，复用实际生命周期算法，避免平行复制整个执行器。|

采用“原creation先持久prepare”。让外部caller自行传deadline虽然改动少，尚不能证明首次授权及丢回执只发一份预算；只从submission或workflow开始计时又会漏掉材料准备。两种方案均不作为本片总预算实现。

```mermaid
flowchart LR
  Policy[定义中的稳定预算policy] --> Prepare[原creation持久prepare原件]
  Prepare --> Materials[完整材料准备与编译]
  Materials --> Preview[原实例的确定性preview]
  Preview --> Create[精确确认并发布原creation]
  Create --> Submit[原提交意图与attempt]
  Submit --> Workflow[原Temporal共用deadline]
  Workflow --> Job[原Executor及进程所有者]
  Job --> Collect[原结果收集与回执]
  Workflow --> Fence[原fence与未确认对账]
  Prepare -.同一身份与截止.-> Job
```

这是待实现的调用关系，不是当前已经可运行的新版本。

## 预算与调用合同

- 稳定policy表达总wall、总额内的清理保留量及已知模型调用上限；不接受没有真实消费者的严格维度后静默忽略。具体字段／编号随实现冻结，预留task-definition5／input9，实施前再次核注册表。
- 首次授权prepare在昂贵安装身份遍历、manifest读取、编译／probe之前，取得原task lock并原子保存起点、policy和原定义／项目身份。尚无原件前不启动这些准备副作用；原件发布后失败或丢回执都不能新发起点。
- 从原件发布至材料／编译结果收集和临时目录清理，由同一可停止的prepare进程所有者负责；新preview/create的材料重核也走此消费者。父进程仅作短的身份定位及受限结果发布，不在监督之外执行`tasks._definition`／完整安装遍历。prepare worker和整个job监督复用既有进程原语；所需清理未确认时不继续发布可执行合同。
- preview的完整record只含原实例，不含动态remaining／expired／当前时刻。状态投影单独计算剩余时间。create绑定原prepare摘要和原preview摘要；resume-create读原intent，不重编或重领。过期尚未发布的合同不能继续发布可执行输入。
- 跨workflow／进程使用固定UTC截止；Linux执行同时以同boot的单调起点约束，取更保守剩余时间。进程内不得反复`monotonic()+原额度`。首片不承诺跨boot／跨主机或异常时钟恢复；该形状先明确拒绝，待有实际消费者再扩。
- 从原图冻结有限slot：inventory、plan、每个work unit、每个review成员（含建议审查）。已知上界为`2 + work unit数 + reviewer数`；integrate／verify没有模型调用。超policy上限在执行前拒绝。
- slot绑定预算身份和原确定性job／process身份，实际启动须匹配。原started-before-launch及unknown不退款、不重发；提交重试、poll、claim、读原terminal不重复扣减。区分预留、启动attempt和实际可核原生命令，不将预留数称实发次数。
- 预算约束不等于资源在某一绝对时刻已被内核回收。清理无法确认时保守报告超期／unknown，保留安全收尾；不以Temporal直接timeout或Future取消代替停止证据。
- 新版本child仅产出待验证结果，不得直接复用现有`process()`末尾的正式receipt发布及ledger更新。原job生命周期finalizer在整个拥有树退出、结果／hash收集验证和预算核对后，唯一调用原`verify_receipt`／`publish`并更新原jobs状态。这个门禁适用于SUCCEEDED、FAILED和CANCELLED全部正式终态；cleanup未知时只保留原attempt与错误／待核证据，不发布任何terminal receipt。原FileAdapter.fence会把任意有效终态当作停止已确认，不能用先发FAILED再清理的顺序。

## 可验收实施节点

|节点|交付与主要所有者|必要证据|状态|
|---|---|---|---|
|B2.0 实际执行接缝|小型独立进程探针，验证绝对截止覆盖准备延迟、阻塞锁和另建session的后代；只用既有进程监督原语，探针不进入产品或CI。|真实PID／starttime、原返回与清理结果；失败保持，不能用算术对象测试替代。探针只验证监督原语，真实prepare材料与正式receipt门禁仍须各片验收。|三种实际进程探针及原件独立补核通过，观察者未代清理；设计SP1／DS1两P2已关闭、开放0／0|
|B2a 持久预算与准备合同|`tasks`／CLI／HTTP共用prepare；原`reference_task_creation`保存一次原件，新schema及WorkflowInput读完整实例；完整材料遍历／编译／收集及清理由prepare worker受同一deadline监督，preview/create/resume保持精确身份。|首次prepare丢回执／重复／并发返回同实例；时钟前进preview不变；慢manifest／编译在实际入口停止且不漏清理；冲突／到期不发布；旧合同保持。新输入的start显式unsupported，不能注册一个可绕过预算的worker。|待实现|
|B2b 原workflow消费者|原submission／WorkflowInput／Temporal共用deadline与slot，涵盖队列、owner、semaphore、poll、重试及原fence。|真实workflow调度的过期排队／owner等待、并发准入；丢start回执后到期仍只lookup，wrong memo／完整input保持。不能拿手工stage序列冒充Temporal生命周期。|依赖B2a；仍不开放新执行|
|B2c 实际进程与收集闭合|原Executor／进程所有者适配整个job的构造、Git／锁、可信命令、MCP／模型、快照、读取／hash及清理；child返回待核结果，原finalizer清理确认后唯一发布全部正式终态及ledger更新，最后才开放新start。|慢Git／被占锁／慢preflight或收集、TERM抵抗及脱离组孙进程；child结果已返回而后代仍存活时原poll／fence仍unresolved，不因FAILED／CANCELLED误确认；真实spawn数不超过slot；原ID恢复、旧进程原件和283身份。|依赖B2.0／a／b|
|B2d 独立出口与发布|受影响行为检查、非editable安装、实际自身审查模板、新fresh-context两轴及普通提交／推送和自己的必要CI。|每片实际命令、失败／未验范围、finding修正复核及精确身份。最终真实六阶段旅程归D，不因本片受控进程通过提前关闭。|各可独立交付片分别执行|

B2a／b可分片交付准备合同及控制消费者，但新运行始终阻断至B2c验收；若过渡版本产生无实际价值的空Interface，则保留为同一未发布片的实施节点，在真实消费者闭合后一起发布。每次公开版本的既有语义保持，后续扩展不能偷偷改变已发布的严格合同。

## 实现位置与审查要求

预算计算若需要共享，使用一个小的stdlib模块，真实调用者为原creation／submission、WorkflowInput／workflow和Executor／monitor。模块只拥有实例身份、截止计算及有限slot，不引入BudgetStore、万能插件或计费服务。若只有本地一个消费者的方法就留在其原所有者；版本构造／执行沿现有共同Interface，不在上层按厂商／具体类型分派。

进程迁移先围绕同一request／started／PID／terminal与unknown Interface组织，保持原任务调度；收集完成及拥有进程停止确认后才发布任意正式终态回执。新finalizer恢复时只收集核对原attempt／待核结果，不能重新执行child body；正式receipt已发布而ledger更新中断时只恢复原状态更新。不会仅以模型返回、future.done或Temporal关闭释放仍未确认的资源。预算与原安装级active上限、单task祖先并发分别记录；多task项目全局上限不在本片无实现承诺中。

复用现有creation／submission／transport／composition／work／processes行为夹具；新增检查只覆盖实际的静默失败风险和生命周期，不复制预算减数、默认值断言或重复CI。每个完整片更新本计划与交付记录，启动新的fresh-context独立评审；产品大项同时使用Ergora自身模板，核实际材料／范围和成本。设计／探针结论与产品执行判词分别保存。
