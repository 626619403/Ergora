# F4.3a：原运行待批计划的有界读取

日期：2026-11-04。状态：首轮CLI/API与专用只读实现已写，源码/发行身份/两真实run只读验收已通过，[新的独立本地审查](2026-11-04-task-plan-inspection-review.md)已归档且无finding；已提交推送`14100cd8d9efca270e0a93d9a6c1b77fde9ed66c`且实时远端一致，精确两OS CI及同片独立终结复核通过，本片完成。前置为[F4.2c真实组合旅程](2026-11-04-task-console-journeys.md)，已独立收口并推送581144c。本片只提供后续页面需要的只读材料，不发批准信号。

## 已核现状与目标

当前status只返回原run的phase/plan SHA，完整计划文本仍位于可信executor产物。原生workflow用整个plan receipt的canonical SHA作为待批plan SHA；它并非execution-plan文本的文件摘要。现有approve已经要求原提交run/spec/memo、当前待批phase与精确plan SHA，不能用页面重算的文本摘要代替。

本片增加同源`task plan` CLI和GET任务plan API，要求明确run ID、plan SHA和1–60秒预算。沿已有统一创建/提交所有者和原生运行连接核原run/spec/memo，再查询实际AWAITING_PLAN_APPROVAL及所选摘要；流式读取原history前缀，定位plan的dev_submit context及job ID。用原请求envelope、原plan receipt的canonical SHA和当前待批摘要核身份，只读取该receipt中被冻结profile声明为plan材料的文本；不把其他日志带入页面。

## 范围与所有权

- 在既有任务用例、CLI/Web和reference边界接入口；计划审阅归已有`reference_task_approval.py`，复用`_Submission.submitted/lookup_run`、`_Creation`安全路径/有界JSON、原SDK分页及converter，不新增第二套receipt校验器、状态机、通用资产服务或依赖。
- 每份计划文本最多256 KiB，使用已有no-follow/常规文件/有界read原语；摘要与实际UTF-8文本一致才返回，总响应最多1 MiB。超限、缺材料、损坏、错误run/plan、网络失败明确拒绝，不以部分文本或空字符串装作完整审阅材料。后续F5负责通用证据索引，F4.4负责日志/观察分页。
- 所有读取不保留SQLite写锁、不创建decision/owner receipt、不调用authorize/approve/cancel、不变更原运行或产物。返回只是读取时的身份快照；后续批准仍由既有服务端再次核当前计划。
- 同步更新公开使用说明及架构。F4.3b再把材料与批准/原decision恢复接到页面，F4.3c接取消/外部清理，F4.3d接精确候选导出；本片不提前声明这些页面行为完成。

## 验收清单

1. 先按原合同覆盖history前缀/分页、严格receipt/job/spec身份、文本摘要/UTF-8/大小与安全路径、实际错误phase和网络失败；纯输入/内容分支使用轻量fixture，必要进程和CLI/API再用现有真实原生边界，避免每个轻量反例重复完整安装。
2. 原审批/运行合同及架构边界定向回归；新非editable包逐项核源码/wheel/两安装及283冻结reference。不为纯复用代码机械增加镜像断言。
3. 对F4.2c两条真实等待run只读核CLI/API材料等于已保存原artifact及待批SHA，保护该片54文件与零signal；在新独立目录或受控传输中验证错误/缺失/超限，不篡改这两任务来制造反例。
4. 完成最小完整实现/本地验证并记账后，新的fresh-context审查者检查正确性、所有权、复用、必要守卫及有界成本。修正后再提交推送、核精确两OS CI和远端，最后更新完成状态。

私有运行材料使用本片独立checks目录；前置组合旅程保留自己的脚本、快照和独立结论。完整F4仍待F4.3剩余操作及F4.4综合出口。

## 实施检查点

恢复后核对基线`581144c3d6205bb400577a79b694f53a8638cf15`与实时远端一致。已修改tasks/reference/专用approval边界/CLI/Web五个生产文件，在既有模块内实现只读材料算法；新增轻量`tests/test_task_plan.py`，实际SDK分页和codec只替换不可控传输与提交预检，文件安全读取与规范JSON摘要保留真实实现。主入口在环境加载前确定操作身份，保证环境超时也返回正确只读错误。公开使用说明已同步；测试结果见下方，发行身份、两原run只读验收、独立审查及提交CI仍未完成。

首轮32项以内轻量检查的历史失败已保留：第一轮26通过/2失败，真实SDK按类型提示忽略额外payload的情况已在解码前核单payload；目录读取依现有原语拒绝，测试接受其实际OSError。第二轮29通过/3失败仅因主入口测试未加入local包路径，已修夹具路径。当前运行计划/批准/运行/架构联合定向；不把失败轮记通过。README、使用手册和当前架构已同步读取顺序、回执摘要与读取界限。

## 已执行验证

- 源码联合定向：`env PYTHONPATH=src .venv-dev/bin/python -m pytest -q tests/test_task_plan.py tests/test_task_approval.py tests/test_task_runtime.py tests/test_architecture_boundaries.py --tb=short`实际exit0，90 passed/1既有依赖弃用warning，266.68秒。新读取32项为轻量文件/真实SDK消息与分页检查；共享审批/原运行合同沿用原集成夹具。只证明本片定向范围，不代替当前完整回归或精确CI。
- 文档初核：7文件303本地链接/锚点、27条README命令parser通过；后续记录更新后会重核。
- 正在构建非editable wheel并离线安装到开发及无Temporal SDK的基础Web环境；原生SDK仍由登记的Linux运行时提供。真实两run只读CLI/HTTP验收待该包完成。新的独立审查已启动，报告与终结结论待补；不提前记通过。

最终初包SHA256为`4160cfdd64a69e0dbb713bda584a57c2cfad939eb1895c28d055836a62c90037`，348源码/wheel/两非editable安装逐文件一致、冻结283保持；基础Web环境无Temporal SDK、独立reference verify为PASS。安装包的新读取合同32项通过（1.93秒，1依赖warning）。真实验收脚本的首轮端口占用，以及第二轮误用POST专属路径作GET就绪探针的405，均已保留脚本与原日志；前者未启动服务，后者在finally显式停止并等待本次HTTP退出，两轮均未批准/取消或操作任务文件。脚本已改为空闲端口及既有GET bootstrap路由，第三轮实际材料验收进行中，尚未计通过。

真实验收追加历史：第三轮在旧`task status`的无SDK调用者明确拒绝（exit2），未调用plan；已保留该轮并用有SDK开发安装查询status，新plan与HTTP仍从无SDK基础安装调用。第四轮治理模板CLI/API及三材料字节/摘要已实际相同，错误run也已被正确拒绝，但脚本误期望exit1，实际CLI异常合同为exit2而退出；脚本/响应/日志已保留，不将该轮计完整通过。未为验收更改生产接口或旧退出码。第五轮按实际契约执行两模板与终核；完整通过结果在下方单独登记。

## 最终本地验收

最终wheel为上述4160cfdd…，没有为验收脚本失败修改生产或旧CLI契约。`native-acceptance-v5`实际exit0，16.69秒。原始材料位于本片独立私有checks目录，不覆盖前片证据。

|检查|实际结果与范围|
|---|---|
|源码联合定向|90 passed/1依赖warning，266.68秒；新读取、原批准/运行及架构边界|
|最终wheel合同|32 passed/1依赖warning，1.93秒；非editable安装加载|
|包与冻结身份|348源码/wheel/两安装逐文件一致，283冻结资源不变；基础Web无SDK，reference verify PASS|
|治理模板只读|CLI/API完全相同，三材料6849字节与原artifact相同；响应9412字节|
|大型开发只读|CLI/API完全相同，三材料7889字节与原artifact相同；响应10403字节|
|错误身份|两模板wrong-run均CLI exit2，wrong-plan均HTTP400；明确拒绝，不写decision|
|原证据|54选定原文件前后相同且等于F4.2c归档；两原history各112连续事件、零signal，plan context均event56|
|HTTP与保留栈|本片测试HTTP已请求SIGTERM、wait返回-15，PID消失/端口关闭；原Supervisor及五服务RUNNING、training-worker STOPPED，留供紧接页面验收|

本机两次CLI为1.70/1.39秒，HTTP为1.169/1.173秒，仅说明本次112事件小任务的读取观察；不据此声称规模化性能。生产实现流式读取history前缀，找到plan便停止；文本和总响应均有明确上限。未物化完整history或引入缓存/新索引。

新的fresh-context审查者已独立跑32项轻量检查、重算包348/冻结283身份，并直接只读连接两原run核原spec/memo、当前待批phase/plan、history及零signal；同时核作者CLI/API原响应和54文件快照。需求与可维护性本地范围无finding，[正式报告](2026-11-04-task-plan-inspection-review.md)已归档；提交身份、精确CI和实时远端仍待后续核对。当前未批准、取消、执行后四阶段或实现网页批准，不标完整F4完成。

提交前静态终核通过：本片八份Markdown、315个本地链接/锚点及27条README CLI parser命令；未改CI或原测试。后续只待本片提交、推送、精确两OS CI及同一审查者的最终身份复核，当前本地实现完整可审。

## 提交与精确CI检查点

实现/测试/文档14文件已提交推送`14100cd8d9efca270e0a93d9a6c1b77fde9ed66c`，实时远端完整SHA一致；工作区当时干净。本片精确[CI41781897332](https://github.com/626619403/Ergora/actions/runs/41781897332)已从官方完整提交行及run页面定位，初读为In progress，不能继承前片成功。之后同一审查者核精确提交、必要步骤与实时远端，才关闭本片。下一[B页面设计](2026-11-04-task-approval-console.md)已记录，尚未实现。

## 最终交付

`14100cd8d9efca270e0a93d9a6c1b77fde9ed66c`精确CI41781897332两OS必要步骤全部成功；Windows126415114987含PowerShell安装升级，Ubuntu126415115241含build/identity/native回归。同一独立审查者逐份核官方原HTML、完整提交与selectedJobId、全部必要步骤精确日志URL，并自行实时核远端仍为原完整SHA；[终结报告](2026-11-04-task-plan-inspection-review.md)已归档，无未解决findings，F4.3a完成。后续B本地页面与README改动不参与A的348/4160cfdd发行身份；A原wheel及两非editable安装保留。当前状态记账随下一片归档，不为纯记账重复重型CI；完整F4仍待后续页面与综合出口。
