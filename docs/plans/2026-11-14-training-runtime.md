# F9b1：原生训练实时查询

原请求：复用已有训练执行和实验账本，让同一项目入口可以观察真实状态；发送后未知必须按原ID对账，不能由本地started/result推断远端事实。实施基线 `8182499fa46c61adecea2f6defd2c777a433eed5`。该片只接实时读取；prepare/start/cancel及原evidence批准分别随后立片，不隐含执行、信号、批准或恢复。

## 接缝与行为

- training.status为CLI、HTTP的两个实际消费者提供统一准入；先沿training.inspect核项目登记、训练模板、原manifest/spec与repo见证，再显式查询。
- reference.training_runtime_status沿原进程隔离模式调用小的reference_training_runtime模块；读取所选原参考安装的固定perf_temporal models/connection/workflow，不引入任务调度器、会话或实验表。必须核新使用的training upstream源码身份；现有validate_installation只覆盖local与upstream/platform。
- 使用原workflow_id perf-experiment/EXPERIMENT。describe一次取得实际run_id，再固定该run读取第一历史事件的完整原Experiment JSON，用既有canonical_sha区分int/float/bool，完整材料不同即拒绝。不能仅靠binding一致认领另一个运行。
- RUNNING返回原Status；COMPLETED读取固定run的原Outcome、follow_runs=False，CANCEL_UNCONFIRMED/GATE_FAILED等领域结果原样显示。失败/终止/超时等Temporal结束为NEEDS_RECONCILIATION，不能宣称停止外部作业或领域成功。返回原binding/workflow/run与查询事实，不修改registry/started/result/fence。
- 只有describe的明确NOT_FOUND表示不存在。网络错误、缺失历史、原输入/返回binding不符、SDK缺失和有界超时都报错，不退回离线猜测、不自动重发/启动。
- 原页面默认继续离线查询；用户按显式查询按钮后才调用runtime GET，结果与离线证据分别呈现，沿DOM/project/home/detail序号抑制迟到响应。不增加自动轮询或新服务。
- 运行依赖为可选ergora[temporal]；真实端点和连接环境沿当前参考owner。CPU测试与真GPU分别记录。

## 验收

复用现有原生contract fixture、SDK层只读client替身及原status测试模式；针对完整输入数值类型碰撞、run固定、真实领域负结果、NOT_FOUND与UNAVAILABLE区分、超时/单次查询、两项目环境与原件不变、CLI/HTTP同语义做必要覆盖。只登记原Linux组，Windows沿原workflow执行实际支持范围。新noneditable包/两RECORD/283、实际受控本地Temporal旅程（环境可用时）、浏览器显式/迟到状态及停止、原模板自身审查和新fresh-context两轴；普通发布精确Ref及自己的CI，不能借F9a。

F9a已普通发布并核精确Ref，自己的CI终验单独推进、不被本片取消；产品已实现于工作树，首轮验证发现夹具缺新必需家族与边界清单未登记；按原合同补完整夹具／登记真实边界，第三轮47通过，旧已加载架构清单的1失败保留；仅补验新清单，然后最终安装／实际旅程／审查，未降低准入。后续F9b2提交需发送前意图/attempt与原run对账，再接取消与恢复，禁止复制task submission为第二训练调度器。

## 当前检查点

源码与最终noneditable r1已实现并验：564逐字／两RECORD／283，安装48通过。原生CPU控制实际排队、取消／fence／executor取消收集后，同一SQLite／原run恢复读到CANCEL_UNCONFIRMED，保留本地CANCELLED；原42事件／完整输入及新查询与SDKOutcome相等。私有驱动的导入／路径／过强取消断言失败均保留，未变更产品迎合预设或重发原start/cancel。页面默认不查询、手动完整状态、三晚到排列／三视口及45GET／21原件保持／自有服务停止均已验。自身14完整文件approve；新的独立需求／结构两轴均已补核全部最终本地原件、本地出口通过，开放0／0。普通发布／精确Ref／自己的CI待收口，详见交付；下一片为[F9b2显式提交](2026-11-14-training-submission.md)。
