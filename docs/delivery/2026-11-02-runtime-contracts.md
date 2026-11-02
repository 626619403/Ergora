# S11 / R5：运行契约与平台生命周期

日期：2026-11-02。分支 `refactor/architecture-foundations`，开始时工作区干净，HEAD `39e0c34f503d7cc607e8ae72a755a89b8b64b3e1`。该提交仅为R4状态收尾，实际生产代码/测试身份仍为 `f9a9b743be1b5bde352d212b75c47358d5d73e9a`。

## 范围与分步

用户授权按实施计划继续。按A1已确认范围，先核对现有运行摘要、产物引用、能力和生命周期所有者；只在有真实重复语义和消费者时提取共用原语。保持领域状态、旧run文档、原生ID、取消/未知及候选证据，不引入新的调度器、安全边界或通用运行基类。

|分步|产出|状态|
|---|---|---|
|R5.1 契约与责任核对|当前运行/产物/状态所有者、实际共用与须保留差异、明确能力/退出边界|已核对，形成契约说明；无源码迁移需求|
|R5.2 生命周期及可选SDK验证|Linux普通/受监督/抓取、Windows真实现有CI、Forge未知/查询失败与mini取消，记录版本与实际结果|最终43 passed / 5 skips；106本地链接 / 283冻结身份通过|
|R5 完整独立审查|fresh-context审查范围、契约、最小整理决定、实际证据和未验项；收口后进入R6|需求/可维护性通过，无findings|

## 已核实事实与待验证决定

- `processes.run`已被agents、evaluation、optimization、kernel直接使用，共用`status/returncode/output`进程结果及stdin/stdout/stderr文件。领域结果由各调用者扩展，不将退出0等同于评价/候选采用。
- `windows_job.Job`已由普通命令与research抓取共用。前者通过stdin gate，后者通过Event gate，在assign完成前不启动实际命令/网络操作；Job拥有终止及确认空进程集的责任。
- Linux普通命令依靠新进程组及finally清理；受监督stage_driver保留监控进程组、subreaper和信号取消标志；research使用spawn子进程、父死亡信号及总时间/字节预算。三者通信和死亡处理不同，不能因都使用进程而合并状态机。
- CLI/Web实际消费独立Agent、研究、评价、优化和Forge各域文档；F4/F5的统一任务/证据投影尚待实现。本节点不为未来页面增加没有消费者的结果类。
- 既有普通Linux命令没有SIGKILL控制器后的自动回收保证；网络抓取、正式监控和Windows Job各有不同保证。将用隔离、可清理的小探针核对该差异，不能将所有模式写成同一能力。

结论：已有共用结果和Windows Job存在真实消费者，其余通信/预算/生命周期不同。按原实现保留所有者，新增[运行契约矩阵](../architecture/2026-11-02-runtime-contracts.md)供调用者使用，不增加无复用依据的源码抽取。此决定及验收边界已通过独立审查。

## 计划验证与隔离

复用既有tests/test_processes.py、test_projects_tools.py、test_research.py、test_reference_executor.py、test_agents.py以及Windows测试；不复制其实现构造新测试框架。显式选择已安装固定ForgeKernel与mini SDK的独立Python，运行确定性CPU/本地命令fixture，不调用真实模型、GPU或改全局配置。测试及探针仅写忽略的`.ergora/checks/r5/`持久检查目录。

固定源码已读取：ForgeKernel `5030503d3ff71851aa34c14b9caf13ebfa9d9a78`，mini-swe-agent `04d809ceab9df28f9adaed044884180159172930`。执行前还将核对组件所声明提交、SDK导入及运行应用包身份。真实Windows结果必须对应相同生产源码；不以Linux模拟替代，也不从旧计数推导未执行的维度。

## 当前实际检查

执行前已核对源码、R4最终包清单与`.venv-dev`非editable安装的324个应用文件一致；两个SDK提交分别与声明匹配，真实导入通过。环境记录`.ergora/checks/r5/environment.json`，仅在本机忽略目录保存具体路径。

首轮命令为`.venv-dev/bin/python -m pytest -q -rs --tb=short -p no:cacheprovider --basetemp .ergora/checks/r5/lifecycle-tests tests/test_processes.py tests/test_projects_tools.py tests/test_research.py tests/test_reference_executor.py tests/test_agents.py`，移除`PYTHONPATH`、设`PYTHONDONTWRITEBYTECODE=1`并显式选择上述SDK的独立Python/checkout。结果 **42 passed、5 skipped、1 failed，140.06s**；失败为mini `complete`进程在15秒内未返回，stderr为空，不能据此定位根因。日志`.ergora/checks/r5/lifecycle-sdk-regression.log`。

未改驱动、SDK或测试超时，单独复跑mini三项（正常/超时取消/空提交）为 **3 passed，15.56s**，日志`.ergora/checks/r5/mini-repeat.log`。随后按同一SDK配置复跑整组，增加`--durations=8`、改用独立`--basetemp .ergora/checks/r5/lifecycle-final`，结果 **43 passed、5 skipped，122.14s**，日志`.ergora/checks/r5/lifecycle-final.log`。5项跳过为4项Windows-only和1项未选隔离Temporal，Forge三项、mini三项均实际运行。不隐藏首轮失败或将重试通过等同于已解释其原因。

一次性Linux探针`.ergora/checks/r5/posix-controller-probe.py`：对隔离controller下两个受信进程分别发SIGINT和SIGKILL。SIGINT返回`cancelled`且两后代停止；SIGKILL时controller无结果、两后代仍运行，确认普通命令没有父硬退出自动清理保证。探针作为subreaper主动杀进程组并waitpid回收，两个场景均`cleanup_confirmed=true`；原始结果`.ergora/checks/r5/posix-controller-probe.json`。不增加断言孤儿应存活的产品回归，不改当前用户服务。

Windows证据复用[R4精确候选CI41380351919](https://github.com/626619403/Ergora/actions/runs/41380351919)，Windows job125069579809 / Ubuntu job125069579994均成功，已由[R4独立审查](2026-11-02-application-use-cases-review.md)核对官方页面。`git diff f9a9b74 -- src tests README.md pyproject.toml .github/workflows`为空，故这是同一源码/测试身份的历史真实平台结果，并非本轮新Windows运行；不据此新增逐项计数或未观察的能力。

静态收尾：四份当前Markdown的106个本地文件链接存在、无行末空白、`git diff --check`通过；非editable包`reference verify`为 **PASS / 283 files**，源码/测试/CI与上述精确身份无差异。记录`.ergora/checks/r5/static-checks.json`。未改冻结源码、旧HTML、配置格式、状态文档或运行服务。

## 未验范围及后续动作

未调用模型/GPU、未跑真实Forge模型campaign的取消竞态、未再启动Temporal端到端旅程、未测Linux正式monitor被SIGKILL的即时整树停止。本轮固定SDK fixture及源码检查不证明这些维度。mini首轮超时原因尚未定位；保留失败及后续通过记录，不为通过而放宽阈值。

## 独立审查与交接

新的fresh-context reviewer已完成[独立审查](2026-11-02-runtime-contracts-review.md)：需求符合性、可维护性均通过，无findings或范围内的阻断性验收缺口。独立核对源码/安装包身份、106链接、历史CI原页及本轮日志；未将其只读复核写成重跑测试。保留mini首轮超时和全部未验维度。

R5实现/验证/独立审查已收口，本轮文档提交后按授权推送并在后续检查点记录精确提交。下一项为R6：优先收拢Web直接读取模板的边界，复验编译/原执行链及冻结绑定；无依据时保留已有reference/Executor适配。F3/F4持久任务/恢复及D3隔离仍属各自节点。

交接确认：`d685bb9867ef2cdc35d3c5b785dba2bb147dbeac`已推送`origin/refactor/architecture-foundations`，再次读取远端SHA一致，工作区干净后进入[R6](2026-11-02-reference-boundary.md)。生产/测试身份仍为上述`f9a9b74`。
