# c1b2a：独立 cycle 服务与普通／停止配额

日期：2026-11-15。状态：具体方案准备，产品未实施，尚未独立设计审查。承接[原控制器合同第4节](2026-11-15-training-cycle-controller-contracts.md#4-workflow活动和阻塞通路)与[c1总计划](2026-11-15-training-cycle-workflow.md)。前置c1b1的新安装包SHA256为`565aefd026e01f83470af5e49a74d1743c3919779a4b4a217fc2dc56755eb29b`，其最终精准补验／独立终核及固定提交尚待；实施基线须在前置固定后填写，不把当前WIP当已验基线。kernel专家继续保留v3。

## 交付目标与范围

提供可由原Supervisor启动的独立`training-cycle-worker`进程，与原`training-budget-worker`使用不同PID／event loop。在cycle进程的非阻塞loop中分别注册普通和停止Worker，各自保留活动并发配额。普通活动只消费已冻结授权及真实SDK controller身份，经原H读取／核对资料，再复用c1b1的start或只对账消费者；停止活动复用原独立writer／逐owner通知／drain／实际执行链观察。

本小片先交付服务边界与inspect／start／reconcile／stop的真实消费者。总`TrainingCycleWorkflow`、显式execution消费者、测量collect／接受／rounds、第二候选和公开自动运行按钮分别后接，不注册会假成功的空实现。没有总Workflow时，此服务单独启动不会发起实验。服务boundary验证中的最小Workflow夹具只能证明SDK路由与进程隔离，不能称正式总Workflow或训练旅程。

## 已核源码事实

|实际owner／接缝|现状与本片复用点|
|---|---|
|`reference_training_worker._serve`／`main`|只注册原ExperimentWorkflow与Activities，8活动配额；保留此入口和其原loop。新入口在同一已pin的owner，不往原loop塞第二Worker|
|`_CycleOperation`／`_CycleCandidate`|已分别持有原S-H与独立Popen预算根；业务文件、State、锁、native注册装载及SDK调用在H／根。继续调用同一算法，不另建process-host|
|`stop_live_controller`|先经冷inspect得到原完整snapshot，再独立启动writer／drain／各候选notify与observe；一个分支阻塞不串行挡住另一分支。各观察不等价于durable stop|
|`training_execution_protocol`／`CycleAdmission`|严格operation封套、原compute∩control一次窗口、父共享准入／可见stop、原intent／attempt／receipt及完整controller身份已有owner。新活动来源核对放在这个边界及H，不放CLI／页面|
|`reference.training_budget_worker_command`／`services._prepare`|前者用应用解释器与所选native安装，后者从原training-worker配置生成独立服务命令／日志；服务目录与管理身份已有归属，不修改283参考配置|
|Temporal SDK 1.34.0|已在实际安装只读核`activity.Info`有workflow_id／workflow_run_id／workflow_type／workflow_namespace／task_queue／attempt；Worker有各实例独立max_concurrent_activities与graceful_shutdown_timeout。这里只核API，不等于真实服务注册通过|

## 输入、身份与恢复合同

活动业务输入沿原六字段workflow_input：protocol、control_home、project、cycle_id、input_sha256、authorization_sha256；候选动作只再携原ordinal，不接受另外一份候选／baseline／command列表。服务从真实`activity.info()`取调用Workflow ID／run／type／namespace，不信任业务输入自述身份。普通活动的来源与ordinal在H中和原完整授权、controller intent、attempt、receipt及有序位置重新核对。

首次活动可能早于客户端receipt保存。缺receipt时只沿c1a2原同一attempt／memo对账，匹配实际SDK run才继续；NOT_FOUND／不同run／reset／旧receipt／不完整started input均保持unknown或明确拒绝，不补新attempt、不发第二次start。原case不能以“活动已启动”直接自授预算owner或SDK投递权。

具体typed活动请求、H mode／封套字段及结果，在实施前以现有strict转换器固定；优先复用原字段与内存对象，不另建数据库表或可变current-round。SDK身份的采集在activity adapter，完整记录认证在H／原protocol。只读inspect与start的最后执行gate必须分开，前一次认证不能替代真实SDK动作前的父许可、完整owner及同一窗口。

普通活动先取得一个有界冷观察；后续start只使用c1b1自己的compute∩control一次窗口，prepare／Popen／传送／confirm／dispatch共用，不因活动轮询刷新。已存在intent时不再授offer；已有attempt只能调用原reconcile路径。SDK producer的副作用活动maximum_attempts=1在c1c实现；本片服务也不能把unknown或重投的activity请求改成新的执行机会。

停止输入含同一原身份及非空reason，由独立stop queue消费原total剩余，不占普通槽。取消普通activity仍按c1b1区分交接前／后；取消停止activity或服务关闭时，必须继续持有已创建的原S/H／Popen并完成原退出观察，不能以Future取消冒充回收。不能给已接受历史轮统一发送Temporal cancel。server terminate与实际本地停止分别记录。

## 服务、配额与结果边界

新服务使用原应用解释器及可选`ergora[temporal]`；core未安装SDK时，普通离线读取／inspect仍可用，启动该服务可见拒绝。服务启动期沿原native环境装载；运行中的SDK loop不读业务State、JSON、日志，不执行fsync／flock或同步等待。不得把这些操作放入线程伪装成非阻塞；OS-only Popen创建继续沿c1b1的明确例外及生命周期合同。

普通queue沿原`ergora-training-cycle-v1`，独立stop queue的完整名称在设计终核时固定。两Worker各自至少一活动槽，不能从同一普通槽或同一同步helper借配额。首版不新增无实际用户的调优配置；真实并发参数若暴露，定义有效范围且验收跟随传入配置，不锁默认值。原budget worker的queue／进程／活动注册不改。

活动input／result仍≤32KiB。完整大内容保留原operation文件，返回完整typed事实及准确原件引用；不得切掉候选、身份、异常或分支后称完整成功。现有snapshot或停止聚合无法容纳时，明确容量拒绝并保留已经发生的原事实，不假定32候选一定能运行。需要聚合引用时必须确认原文件实际存在并绑定原operation，而非加第二份停止账本。SDK编码、业务成功、durable stop和子树回收分别验证。

## 实施节点与客观验收

|节点|最小变更与原owner|验收证据／禁止越界|
|---|---|---|
|b2a.0 具体身份与设计|固定前置提交；沿原protocol／H明确SDK来源认证、首活动receipt竞态及typed封套，明确独立queue与关闭顺序|新的fresh-context设计两轴通过后才改产品；不是仅凭本文批准实现|
|b2a.1 服务入口|原worker内新增独立入口与普通／stop活动注册；reference提供真实命令，services管理新服务／日志／SDK可用性|实际Supervisor两个worker PID／loop不同；core无SDK拒绝新服务但原读取保持；不改旧Worker与283|
|b2a.2 有界普通活动|适配inspect、原start与只对账reconcile；真实SDK身份由H认证，不新增候选调度|同run正常消费者到达原H；错input／run／ordinal不Popen／不start；receipt未落盘只恢复同一attempt，NOT_FOUND不重发|
|b2a.3 独立stop与关闭|直接消费原stop_live_controller，独立Worker槽；普通H持真实锁／fsync阻塞|真实SDK路由下stop仍被领取，writer／逐owner异步通知，原reaper／实际wait完成；各durability结果不互相替代|
|b2a.4 安装与交付|新非editable core／SDK、原适用service／submission／架构接缝；自身模板、新独立产品两轴|完整包／资源／283保持；真实服务与fixture范围分列，所有进程／端口收尾，更新手册及精确发布状态|

测试优先扩展`test_services.py`、`test_training_runtime.py`及`test_training_submission.py`已有真实注册／S-H接缝；只有独立风险确需新测试文件时才动CI分组。SDK服务替身用于协议反例，真实Temporal／两个OS服务用于queue与loop隔离，不拿前者代后者。此片没有实际训练／GPU／质量或测量收益验收。

实施前还要用具体调用者解决两点：首个receipt认证的H mode应共用原reconcile算法且绑定实际SDK run；多分支stop结果的完整32KiB表示应引用原件而不隐藏分支。方案不足时先缩小片或修订接口，不增加无caller的通用活动总线。

每步写本片交付；前置产品固定后再新建交付记录和设计审查，随后b2a接线。之后的execution／collect、标准sandbox总Workflow与c1d完整接受／后继门槛仍沿[c1原计划](2026-11-15-training-cycle-workflow.md)，不提前称自动循环可用。
