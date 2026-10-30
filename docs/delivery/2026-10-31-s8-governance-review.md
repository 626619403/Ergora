# S8 仓库治理方向独立审查

审查者：独立代理 `s8_governance_review`，2026-10-31，全新上下文。项目与文档根均为 Ergora；未继承实施对话。已阅读 `AGENTS.md`、`docs/PLAN.md`、S8 交付记录及 maintainable-project-delivery 的独立审查要求。基线与当前 HEAD 均为 `3b52365fe56d79c7b467a73e369b5a42c2b5afc9`，分支 `feat/evolution-console`；实现主要为未跟踪文件，审查依据实际文件内容，而非仅 Git diff。

原始要求：为三个模板研究真实 Agent，解耦模板与 Agent 实现，补充或替换合适实现，保持六阶段、候选绑定证据及默认 Codex 审查，最终由主任务提交推送。本报告只裁定仓库治理方向与其共用执行边界；不替代大型开发、训练优化或最终发行审查。

## 分别裁定

- **需求符合性：需要修改。** 角色提取、厂商选择、CLI/Web 共用服务、精确候选及冻结绑定的正常路径成立；以下两项 P2 阻止本方向关闭。真实模型质量对照仍待执行，文档已明确，未将协议夹具误称为模型质量验收。
- **可维护性：主体归属合理，需要修正执行边界。** `agents.py` 同时被独立调用和正式驱动消费；`reference_executor.py` 继承原有阶段算法，`stage_driver.py` 承担原监控内的适配进程入口，有实际所有权理由。没有要求另造工作流、插件平台或迁移冻结源码。主要缺口是 supervised 分支把后代清理交给未实现该行为的监控，以及未传递精确可执行文件。

## 发现

### S8-GOV-1 · P2 · 正式阶段返回成功后仍有同进程组子进程写入

位置：`src/ergora/processes.py:17`、`:22`、`:29`；调用边界 `src/ergora/stage_driver.py:37`、`src/ergora/reference_executor.py:79`。

正式驱动传入 `supervised=True`，既不创建独立进程组，也不在正常退出时清理后代，只在直接子进程仍存活时 kill 它。继承的 `agent_platform/process_job.py:124` 仅在命令返回后立即比较 checkout；正常完成路径没有清理尚存后代。因而“外层监控拥有整个进程组”不等于“成功返回前已结束该组所有工作”。

确定性复现：一个 `stage-json-v1` reviewer 用 `subprocess.Popen` 启动同组子进程，子进程等待两秒后写 `src/late-review.py`；父进程立即输出有效 approve JSON。经原 FileAdapter 与 Activities.poll 的六阶段运行全部成功，review 回执为 `SUCCEEDED`、independent-review 为 pass，随后文件实际出现。同步写 checkout 的 reviewer 则被正确拒绝。本发现涉及可控制的同组后代生命周期，不宣称提供或要求每 Agent 的 OS 隔离。

后果：只读变化检测及正式阶段的完成边界可以早于 Agent 的实际写入结束；同类 work 后代也可能与后续可信检查/提交重叠。独立调用已有的正常退出清理保证没有延伸到新正式桥接。

最小修正：在新增调用边界完成后代结束/清理，再将成功交还原监控进行 checkout 检测；同时保留外层取消、整体时限及未知结果不重复提交的语义。无需修改冻结参考文件。应增加正式桥接的“父进程成功退出、同组子进程延迟写入”回归，并检查正常调用、超时/取消不会因此失去进程控制。

可重放夹具：`build/s8-governance-review/probe_descendants.py`。当前运行返回 1，输出 `review_state=SUCCEEDED`、`late_review_write=true`；每次运行的回执和结果保留在该目录的 `runs/descendants-*/`。夹具属于忽略的本地审查产物，不是拟发行测试。

### S8-GOV-2 · P2 · 正式驱动忽略参考配置中的精确 Codex 可执行文件

位置：`src/ergora/stage_driver.py:33`；实际 argv 所有者 `src/ergora/agents.py:136`。

桥接将参考配置的 `codex_bin` 放入 request，但驱动只把其父目录加入 PATH，最终仍执行字面量 `codex`。原执行器的 `model_protocol` 直接使用配置路径。配置为已有的版本化文件或包装器（如 `pinned-codex`）时，新桥接会调用另一个 `codex`，或在配置文件本身可执行的情况下报找不到命令。

确定性复现：同一隔离目录放置两个不同名称的协议夹具，配置 `codex_bin` 为 `pinned-codex`。驱动成功，但结果 summary 显示实际执行的是兄弟文件 `codex`。两者均为本地夹具，没有调用模型。

后果：切换到正式桥接后，已配置的 CLI 版本或包装逻辑被替换，无法保证原配置身份，或使本可运行的配置失败。

最小修正：将显式配置的可执行路径传至原生 argv 构造处并作为 argv[0]；普通独立调用仍可使用默认 PATH 查找。回归需让配置文件 basename 与 `codex` 不同，并用另一个可辨识的 `codex` 证明不会回退。

可重放夹具：`build/s8-governance-review/probe_driver.py`。当前返回 1，输出 `configured_binary=pinned-codex`、`observed_binary=codex`；结果保留在 `runs/driver-*/`。

## 已核对的行为与证据

1. 治理 `agent_contract` 从原 profile/roles 提取 inspector、planner、implementer、reviewer，排除执行器负责的 behavior-baseline/test-results，保留 integrate/verify 的可信所有权。新增合同没有厂商或机器路径；冻结模板仍为原发行资料。
2. 原有六阶段执行、精确计划 SHA 审批、范围和回归检查、精确候选 SHA、作者身份/会话排除仍由原所有者消费。首次接入保存项目修订与四角色绑定；正向夹具在 inventory 后修改 implementer 为不存在命令，原任务仍成功，证明后续阶段使用冻结选择。
3. 新项目所有角色默认 Codex，mini 仅能绑定实现角色；缺少 stage-json 能力、结构输出错误、命令失败、工具缺失有可见失败。CLI/Web 使用同一绑定/运行服务；页面选择来源于同一 catalog，并明确普通调用不等于正式验收。
4. 治理调研区分 Agent 与代码工具：Aider 的 repo map/自动提交策略、Serena 的组件许可证及 MCP 角色、OpenHands SDK 的 Python 3.12 要求、Claude 的商业许可均与固定来源一致；候选没有被写成已接入。Codex/Claude 的质量与认证缺口明确保留。

审查者执行：

```bash
.venv-dev/bin/python -m pytest -q tests/test_reference_executor.py tests/test_reference.py tests/test_projects_tools.py tests/test_web.py tests/test_agents.py -k 'not forge and not real_mini'
.venv-dev/bin/python build/s8-governance-review/probe_driver.py
.venv-dev/bin/python build/s8-governance-review/probe_descendants.py
```

- **29 passed、3 deselected**，一项既有 TestClient/httpx 弃用提示；包括两个开发模板 × command/Codex 协议夹具的四次完整六阶段。此处调用真实 FileAdapter 与 Activities.poll，未启动 Temporal 服务、未调用真实模型。
- 另以隔离夹具执行同步 reviewer 改动负例，review 失败；原监控给出只读阶段改动检测。该检查与延迟后代复现一起区分了有效的同步保护和缺失的生命周期边界。
- 上述 12 个 S8 应用文件与 `.venv-dev` 中非 editable 安装的文件逐字节相同；原参考 283 文件身份测试通过。
- 对治理相关六个上游的 27 份已取得文件重算 SHA，与来源 JSON 一致。补查已安装 Codex 0.165.0 help 和固定提交的 `codex-rs/cli/src/main.rs`、`codex-rs/exec/src/lib.rs`：exec 使用 InProcessAppServerClient；不将缺少 `--no-daemon` 误报为共享 daemon 问题。

限制：本轮未重复作者报告的全量 103 项 + 36 子测试、真实隔离 Temporal 服务、mini SDK、Forge CPU 或 Chromium 验收；这些仍属 S8 交付记录中的作者证据。未执行 Codex/Claude 认证或模型质量比较、GPU、SSH delivery 或远程取消。仅写本报告及忽略的隔离审查夹具，未更改源文件、冻结参考、依赖、服务、浏览器、提交或远端。

## 精确审查身份

主实现文件及 SHA256：

|文件|SHA256|
|---|---|
|`src/ergora/agents.py`|`6ab86427c5a097ef831c4b8a7f414b12d94fa22ac59d354c9465ae731354ed9f`|
|`src/ergora/reference_executor.py`|`d87c1ec1d466913a8e72daf67438b4228a5d06c3288bbdfabbc8ed7f48cea5ae`|
|`src/ergora/stage_driver.py`|`4948198d0c504a8e7b021ac1957d77895f6ccc0dcfb27a0c15b9110e0ff6cfeb`|
|`src/ergora/reference.py`|`97c38b28280eee0afe0d00a84528868f50fb85022bc46ee79f61c318b5154ffb`|
|`src/ergora/tools.py`|`a45860e7f9e711dd24903d8924c4edfd246f8ab1506b24fdd477d4d3168699bf`|
|`src/ergora/projects.py`|`9976114db0284312e7c6c9de6a21d08ac61c6ffcc651d4db160d76851a63cab1`|
|`src/ergora/processes.py`|`de2141524d555a1ea43648eee8014afef2464dcb362c8fd9f1818df5c35f8f58`|
|`src/ergora/cli.py`|`72ecbc4c5c6dca6054a785e821aeb73624179986c5a32b02c068940b59a7e632`|
|`src/ergora/web.py`|`c3b3c5809d4f3d593eaaa2324f9bf93d88b355359920582dc0b017dd3080dd0b`|
|`src/ergora/data/console/app.js`|`bfe67419c7c6907d9691f3ed11919dfd0981655052f4b23af75c1aae8eef19c9`|
|`src/ergora/data/drivers/mini.py`|`4f47393b3bb46a20bb24b38889e132bbc6f470953c1518e698877aa5904e55ed`|
|`src/ergora/data/training-agents.json`|`e7a3db67ca0d02934aec8ce82974c2bd77181a3f10ae9f734ea2612c60ff7018`|

同时检查的入口、文档、测试与必要邻居：`src/ergora/state.py`；`tests/test_agents.py`、`test_reference_executor.py`、`test_reference.py`、`test_projects_tools.py`、`test_web.py`；`tests/fixtures/stage_agent.py`、`reference_acceptance.py`、`mini_acceptance.py`；`README.md`、`pyproject.toml`、`AGENTS.md`、`docs/PLAN.md`、`docs/delivery/2026-10-31-s8-agents.md`、`docs/AGENT_BACKENDS.md`、`docs/USAGE.md`、`docs/INTEGRATIONS.md`、`docs/research/2026-10-31-template-agents.md` 及其 `sources/2026-10-31-template-agents.json`。

冻结邻居按执行与合同边界阅读：`src/ergora/data/reference/platform/local/agent_platform/` 下的 `core.py`、`executor.py`、`sandbox.py`、`process_job.py`；`platform/upstream/platform/dev_platform/` 下的 `activities.py`、`adapter.py`、`workflow.py`；治理 `profile.json` 及 `platform/templates/repository-governance/` 的七个文件（LOCAL-GUIDE、evidence、input、input.schema、instructions、output.schema、roles）。其中模板数据包括哈希和关键字段检查，不声称逐字段重新审查完整冻结 JSON Schema。

上述枚举共 46 文件的快照身份：`e31a5b85317c39d62d2b2aea0d494717402d2abe12f8f52851abac731f092fe6`。计算方法：按完整仓库相对路径排序生成 `{路径: 文件SHA256}`，用 `json.dumps(..., sort_keys=True, separators=(',', ':'))` 编码后再次计算 SHA256；不包含本报告与本地审查产物。

关闭条件：修复 S8-GOV-1 / S8-GOV-2，运行针对两者的回归与受影响正常/取消检查，并由本审查者复审。后续模型/GPU效果及 S9 提交推送继续由各自交付阶段记录。

## 修复复审 1（2026-10-31）

同一独立审查者继续复核本切片；基线/HEAD 与分支未变。重新阅读更新后的 PLAN/S8 交付记录、`agents.py`、`stage_driver.py`、`processes.py`，检查强化后的两份六阶段夹具及原监控的取消路径。12 份应用文件再次与非 editable 安装逐字节一致；冻结 monitor 未修改。

- **S8-GOV-2 已修复并复验。** 原生 argv[0] 直接消费传入的 `codex_bin`，驱动传递参考配置路径；原始 `probe_driver.py` 返回 0，`observed_binary=pinned-codex`、`configured_binary_honored=true`。四次六阶段夹具也使用会失败的兄弟 `codex`，均通过。
- **S8-GOV-1 正常完成路径已修复。** supervised 仅有独立单任务 stage_driver 消费；Linux subreaper 接管孤儿后代，直接子进程退出后反复 kill/wait adopted children，再返回监控进行 checkout 检查。该所有权没有扩展到 Web 多线程进程。原始 `probe_descendants.py` 返回 0，review 为 `SUCCEEDED`，`late_review_write=false`。
- **同一生命周期问题的取消分支仍需修正（P2）。** 当普通同组 child 设置 SIGTERM handler 为忽略时，fence 的组 SIGTERM 先终止 stage_driver，跳过它的 finally/reap；GNU timeout 随直接命令退出，原 monitor 的 stop 看到 supervisor 已退出便不再发 SIGKILL。实测回执 `CANCELLED`，同组 child 随后仍写入。其 PGID 与原 monitor 记录的 timeout PID 相同，没有 setsid、脱组或远端作业。位置仍为 `stage_driver.py:12` / `processes.py:51` 的终止边界，原监控 `process_job.py:62` 为触发条件，冻结源码不应因此改写。

新增可重放夹具 `build/s8-governance-review/probe_monitor_cancel.py`：先确认 Agent 子进程确已运行，再触发 fence，或等待正式阶段时限。运行 `fence` 得 `CANCELLED/late_write=false`，运行 `timeout` 得 `FAILED/late_write=false`，运行 `ignore-term` 得 `CANCELLED/late_write=true` 并返回 1。运行资料位于 `runs/cancel-*/`。取消处理应让专用驱动在终止前走完可控后代清理，或可见地保留未决状态；不能仅因 supervisor 退出就确认后代已终止。

重跑初审相同 pytest 命令：**30 passed、6 deselected**，包括四次六阶段、独立 SIGINT/超时、冻结身份与 API 退化处理；仅既有弃用提示。新增取消 probe 仍使用真实原 FileAdapter / Activities.poll 与进程监控，不启动 Temporal 服务、不调用模型。作者报告的全量 107 项 + 36 子测试和其他方向原生工具/浏览器证据没有在本复审中重复执行。

本次修复身份：

|文件|SHA256|
|---|---|
|`src/ergora/agents.py`|`e2b35edaaecc0517894edf86208bba33c7153640dc3df69839295a47c684ee9a`|
|`src/ergora/processes.py`|`4684542f406a88c31265a5b075784f511aa5259908a634e665e103f78643b85f`|
|`src/ergora/stage_driver.py`|`79742381e30f81152a7dd76fcd24ef0259772d658b916634d90fd3ea009ce421`|
|`tests/fixtures/reference_acceptance.py`|`ebe01896396d643f37c3f0f7a348a22b098e0709e7d4626f119873040273297b`|
|`tests/fixtures/stage_agent.py`|`c6e38414c22a2220ad0c83a8a2e0ec56b1ee5e383af3d36b2007437244f0e33a`|

复审裁定：需求符合性与可维护性均暂不关闭，等待上述同组取消反例修正并复验；原两项正常完成/可执行路径反例已通过。模型/GPU效果、异常机器死亡和强隔离仍不在已验证范围内。

## 修复复审 2（2026-10-31）

专用 stage_driver 现在将首个 TERM 转为 KeyboardInterrupt，并在 handler 内先忽略重复 TERM；Popen 创建被移入 finally 覆盖范围。以下均由同一审查者独立重跑：

- 原 `probe_driver.py`、`probe_descendants.py` 均返回 0，精确可执行文件仍被使用，正常 review 成功且无延迟写入。
- 原 `probe_monitor_cancel.py` 的 `fence`、`timeout`、`ignore-term` 三模式全部返回 0，均实际启动子进程，分别得到 CANCELLED、FAILED、CANCELLED，均无延迟写入。
- `tests/test_reference_executor.py tests/test_projects_tools.py`：**14 passed，31.42 秒**，包括新增可分发的忽略 SIGTERM 子进程真实 fence 回归。

首个 TERM 在正常执行中的问题已修复，重复 TERM 先设置 IGN 的顺序也正确。Popen 创建中断的隔离调度检查通过：尚未赋给 `process` 的真实子进程仍由 finally/subreaper 回收，没有延迟写入。

**S8-GOV-1 仍有一个较窄的 P2 时序窗口。** 如果首个 TERM 在正常完成已经进入 finally 后到达，`stage_driver.py:17` 的 KeyboardInterrupt 会中断该 finally 本身，跳过 `processes.py:70` 的剩余 reaping。当前保护只针对已发生过一次 TERM 后的重复信号，尚未覆盖“第一次信号恰好在清理中到达”。同组子进程忽略 TERM 时仍可存活。

新夹具 `build/s8-governance-review/probe_signal_windows.py` 使用真实子进程、实际 `_cancel` handler 与 `processes.run(supervised=True)`；只在 reaper 首次调用现有 os.kill 前插入调度 barrier，使外部父进程可确定地发送首个 TERM，未修改应用源码。结果：`creation/late_write=false`，`cleanup/late_write=true`，返回 1。该时序夹具直接检查专用驱动的处理边界；上面的三次完整原监控取消 probe 均通过，两类证据不混称。

最小剩余修正：清理必须同样抵抗第一次 TERM，例如在退出清理期间屏蔽/延后该异常，或保证异常中断后继续完成 reaping；保留真实 fence/timeout 的终态。此要求不扩展到机器故障、SIGKILL、远端作业或强 OS 隔离，不需要修改冻结监控。

本轮身份（与非 editable wheel 一致）：`processes.py` 为 `cf6394b12a52ff2812e7f3aa734e5dc908e25871d0e244777af9b5d14bbc651b`，`stage_driver.py` 为 `e4e2912a2178022bf20bb2987d62868437095c6d6189cc67c7ae66de15d2ca2f`；`agents.py` 与上一轮相同。新增回归文件 `tests/test_reference_executor.py` 为 `a1630f9ed7f7dad2c5452ac9185e2b401d9f56d54b7ea75cd21c6b69f71bfae8`，两份 fixture 分别为 `3dedf3c132f5d911761632b664f482cd1237294de309a24c35d2ffc09f9d0590`（reference_acceptance）和 `f3ad4a9bd081b4e9f3a53f25a75004ab06b7d0eb5b5412496ece31897b464cad`（stage_agent）。

本轮裁定：S8-GOV-2 继续关闭；S8-GOV-1 仅剩上述 first-TERM-in-cleanup 反例，需求与可维护性裁定暂不关闭。除报告/忽略夹具外未写入其他项目文件，也未调用模型/GPU或触碰服务/浏览器/远端。

## 最终复审裁定（2026-10-31）

本节为本报告最新裁定；前述初审和两轮复审保留其各自检查点的事实。基线/HEAD 仍为 `3b52365fe56d79c7b467a73e369b5a42c2b5afc9`，实现未提交，分支未变。

- **需求符合性：仓库治理方向本切片通过。** S8-GOV-1 的正常完成、运行中取消、忽略 TERM 后代和首次 TERM 清理窗口均已修正并独立复验；S8-GOV-2 继续关闭。当前检查范围内没有未解决发现。
- **可维护性：仓库治理方向通过。** TERM handler 只设置取消标志，不再抛异常；supervised 通信以 0.2 秒间隔观察标志，创建前/返回后及 finally 中的取消均保留回收所有权。首次与重复 TERM 都不会中断 reaping。模块级标志仅由独立、单任务 stage_driver 使用，实际生产调用没有跨 Web 请求或多个任务复用该状态；其余 kernel/evaluation/optimization/普通 Agent 调用维持非 supervised 路径。冻结监控和六阶段算法未改动。

实际检查了最终 `processes.py`、`stage_driver.py`、`agents.invoke`、`reference_executor.model` 及所有 `processes.run` 调用者；检查新增 `tests/fixtures/signal_windows.py` 和参数化测试。可分发夹具使用真实 TERM、真实 handler/子进程，只在创建返回前和首次 adopted-child kill 前安排信号，并包括清理中的重复 TERM，没有把进程回收实现替换成测试结果。

审查者独立重跑结果：

|检查|结果|
|---|---|
|原 `probe_signal_windows.py`，creation / cleanup|均 `cancelled`、`late_write=false`，返回 0|
|原 `probe_driver.py`|实际为 `pinned-codex`，配置路径被使用，返回 0|
|原 `probe_descendants.py`|review `SUCCEEDED`、independent-review pass、`late_review_write=false`，返回 0|
|原 `probe_monitor_cancel.py`，fence / timeout / ignore-term|均确认 Agent 已启动；分别 CANCELLED / FAILED / CANCELLED；均无延迟写入，返回 0|
|定向 pytest|**22 passed、6 deselected，38.47 秒**|
|安装与冻结身份|12 个应用文件与已重建非 editable wheel 一致；283 个冻结文件身份全部通过|

定向命令：`.venv-dev/bin/python -m pytest -q tests/test_reference_executor.py tests/test_projects_tools.py tests/test_agents.py -k 'not forge and not real_mini'`。本轮包含四次完整六阶段、真实 fence、两种信号窗口、普通调用的 SIGINT/超时/后代清理及原生结构协议回归；未选择的 6 项为其他方向原生工具相关检查，不作为本审查者已运行的证据。

最终实现/回归身份：

|文件|SHA256|
|---|---|
|`src/ergora/processes.py`|`9956fef8a5588f226fe697edb0dde13b3564c95f1d783e564b45794cfb612141`|
|`src/ergora/stage_driver.py`|`f3bc6519a010dbfcc62ee1fbf6df9198f9807d71d4c7af1cfd525a05d2d894ed`|
|`src/ergora/agents.py`|`e2b35edaaecc0517894edf86208bba33c7153640dc3df69839295a47c684ee9a`|
|`src/ergora/reference_executor.py`|`d87c1ec1d466913a8e72daf67438b4228a5d06c3288bbdfabbc8ed7f48cea5ae`|
|`tests/test_reference_executor.py`|`3b1840eb3a667e879aea67db1a1ca29a8396c4810b0fc9c87ec8110c74f87c15`|
|`tests/fixtures/signal_windows.py`|`43833c39a4b9c41c72b9ffa5685616ce6ed872231f88467a7fe2b2fd2e044ba1`|
|`tests/fixtures/reference_acceptance.py`|`3dedf3c132f5d911761632b664f482cd1237294de309a24c35d2ffc09f9d0590`|
|`tests/fixtures/stage_agent.py`|`f3ad4a9bd081b4e9f3a53f25a75004ab06b7d0eb5b5412496ece31897b464cad`|

本通过只覆盖上述治理合同与本地受控执行边界，不扩大为真实 Codex/Claude 模型质量、GPU效果、远端取消、机器故障恢复或每 Agent 强隔离验收。本轮未重复全量 Temporal/原生工具/浏览器验收；最新全量结果由主任务在 S8 交付记录补充，历史 108 项结果不替代新检查点。发行核对及最终提交推送仍由 S7/S9 完成。复审仅追加本报告并使用忽略的隔离夹具，没有修改实现、依赖、冻结源码、服务、浏览器或远端。

交付补记（作者通报，非本审查者重复执行）：最新全量为 **110 passed、36 subtests passed，84.60 秒**，启用真实隔离 Temporal 与完整 mini/Forge 原生环境，只有既有 httpx 弃用提示。上述复审后，作者仅清理 `processes.py`、`state.py`、`tools.py` 的末尾多余空行及一处 S5 文档行尾空格，并重新构建安装；本表继续保留实际受测时的精确身份。此机械清理不改变本报告检查的治理合同、进程生命周期或裁定：本方向需求与可维护性通过，模型/GPU效果及其他已列范围限制保持有效。
