# F9b3：训练取消请求、未知投递恢复与停止事实

日期：2026-11-14。基线 `0d9c0a7a2e0c7d107f3a832fa9492a452df71f34`，承接[F9b2](2026-11-14-training-submission.md)与[F9总计划](2026-11-14-training-workbench.md)。F9b2已精确发布，自己的CI `43511152711` 八job／30必要步骤与原独立两轴终核通过。本片B3.1–B3.5已实现，功能／安装分段及真实CPU／页面、自身模板已验，新的独立两轴最终本地补核通过、开放0／0；普通发布与自己的CI尚待完成。baseline／runner／prepare控制面归F9b4，精确evidence批准归F9c，真实GPU归F9d／B3。

## 原问题与既有 owner

原 `perf_temporal.client.main` 已通过 `request_cancel`／`CancelRequest` 发送精确binding和reason。`ExperimentWorkflow.cancel_and_confirm` 已拥有取消／有界等待，原 `LocalTrainingAdapter` 拥有job／fence／取消和poll；executor拥有最终结果。F9b2实证：控制Outcome可为CANCEL_UNCONFIRMED，后来本地executor结果为CANCELLED；已结束控制工作流再发原cancel会失败。这些是不同事实，不能由UI重写或用monitor退出代替。

新增控制面只负责取消操作意图、发送前attempt、回执和原history对账。原start意图／回执必须已恢复，固定同一个run；不为legacy外部run伪造控制面归属。不新增实验／调度／批准表，不直接kill训练或接管原fence／executor，不自动重复信号，不扩大模板权限。

## 可验收节点

|节点|实施与复用|验收|
|---|---|---|
|B3.1 原run与操作身份|原提交owner读取原意图／receipt，核home／registration／execution／完整spec；取消绑定原intent SHA、固定run、稳定request ID、reason和操作人。相同request ID不得改原因／归属|不接受未确认start、错误run、旧revision或跨项目；本地取消读取不依赖当前baseline／runner／spec或SDK。真正孤儿checkpoint仍拒绝，并保持并发合法读序|
|B3.2 单次原生取消|原client继续决定cancel的query/binding检查和signal方法；局部包装固定经核完整输入／memo的run，发送前保存attempt。使用原CancelRequest字段，加独立操作摘要供原history认领；reason不混入标记|首次精确发一次；原已结束run返回not_sent／already_closed，不能称已取消；RPC／中断留下prepared或unknown，未确认不自动重发|
|B3.3 原history恢复|已有attempt时仅沿固定run分页读原signal事件，核完整binding／reason／操作摘要，再补history回执|真实扣住ACK后能恢复，缺事件／NOT_FOUND／外部同原因或不同标记保持unknown／报错；signal已投递不代表外部停止|
|B3.4 显式停止观察|原runtime lookup/query/result与原ClusterAdapter的lookup_job／poll_job读取固定实验。原fence／job／executor是各自owner的事实，展示完整原状态和不一致／缺失，不制造新的停止结果|CANCEL_UNCONFIRMED与本地CANCELLED可并存；QUEUED／RUNNING／缺job或fence不冒称外部已停止；不发cancel、执行runner、写fence或重算批准|
|B3.5 共享入口与页面|training应用Interface给CLI／HTTP；本地cancel记录默认只读，显式run／request ID／reason确认，原意图SHA恢复。停止观察按按钮触发，独立于当前detail；复用既有页面生命周期|双击一次，旧project／detail／操作回复不覆盖新选择，错误保留；CLI未确认非零，查询命令的成功读取与停止状态分开|

## 架构与实施顺序

1. 先收拢原signal history匹配算法的所有权，再增加取消行为，避免把训练依赖到Task语义。现有Task approval／cancellation实际共用的完整payload分页匹配可移到专用reference history Module，保持算法不变；逐项核真实调用者、原输入和原测试，不另建通用事件框架。提交记录沿原core.write／safe_file／read_raw／file_lock，训练start的身份／receipt由原 `_Submission` 复用；不将Task creation套给Experiment。
2. 取消owner只保存小型操作记录，引用原start意图摘要，不再复制多MiB原manifest。验证不变量在持久化／外部发送owner进行；控制数据库短预留只覆盖本地prepare，不跨RPC。
3. 原client装载冻结原spec用于取消，当前文件缺失不应阻断已有run的控制；不能默默恢复或修改当前实验文件。固定run的原输入、memo和binding在外部发送前核验。SDK离线编码探针已证明带独立标记的原CancelRequest仍可解码为原binding／reason、history字典保留标记；这仅是可行性，必须再验真实服务／worker，不冒称已送达。
4. stop-status复用原runtime与选定原ClusterAdapter观察Interface。Windows原生先保留SDK独立本地取消记录读取；实际取消／原local executor观察沿Linux／WSL2，不把fcntl的原owner冒称Windows可执行。
5. 页面在已确认原run上提供小型取消区，不新增调度、全局状态树或第二套表单框架。文档使用者能按稳定request ID找回原操作；按钮默认不发信号／runtime查询。

## 验证和出口

- 用真实SDK的有界Service替身验证ACK丢失／timeout、完整signal marker、固定run／原输入／memo冲突、外部同原因、NOT_FOUND和重复请求；复用已有测试装载基础，新场景只保护真实静默错误。原Task history消费者做受影响回归，不无理由再跑全仓。
- noneditable最终包的源码／两RECORD／283身份；实际CPU原prepare→原start→取消→原history恢复／原executor观察。测试helper可扣住真实已接收ACK，但不得伪造接收或改写负Outcome。原控制CANCEL_UNCONFIRMED和原job最终状态分开保存。
- 真实浏览器确认、迟到回复、错误输入／双击、三视口、原件保持与所有验收进程收尾；原模板自身审查及新的fresh-context独立需求／结构两轴。保留原失败，修后同片补核。
- 普通提交／推送开发分支，核精确Git对象／Ref和本片自己的CI；不自动合main、不采用训练候选。每节点更新本计划、交付与总PLAN。

## 本地实施进度

|节点|实际状态|
|---|---|
|B3.1|原start／run／memo与操作身份已实现；错误目标／旧修订／原因漂移检查、最终r3实际无SDK本地读通过。|
|B3.2|真实服务／原worker接收带操作SHA的CancelRequest；四run各一signal，原closed返回not_sent。|
|B3.3|真实接收后扣住ACK，在当前spec缺失时由页面恢复同一原history；未发意图显式继续；缺事件／外部同原因／错误marker保持unknown。|
|B3.4|原control／adapter／fence分别观察；两CANCEL_UNCONFIRMED与后来本地四CANCELLED分开保留；原件25份保持、无started／训练命令0。|
|B3.5|CLI／HTTP与页面共用；错误SHA／run零POST、双击一次、三迟到路径、最终三视口通过。原390溢出保留并局部修复。|

源码52项通过。安装九suite原155项在600秒停界，89项逐项PASSED；仅将未完成66项在r2包补测，66通过／278.86秒。不同轮次范围不合称全新单次通过。r3只移除r2一个EOF空行，568／两RECORD／283及当前源码逐字、AST不变和SDK-free读已核；没有因纯格式改动重复全部回归。自身两轮原模板approve、最终独立两轴与发布进度见[交付](../delivery/2026-11-14-training-cancellation.md)及[公开证据](../delivery/evidence/2026-11-14-training-cancellation.json)。
