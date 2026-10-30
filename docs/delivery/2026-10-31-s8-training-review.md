# S8 训练优化方向独立审查

日期：2026-10-31。审查者：Codex，独立 reviewer `s8_training_review`，使用全新上下文；未继承实现讨论。项目根为 Ergora，文档归属 `docs/`。

**最新复审结论：训练方向需求符合性通过，可维护性通过；F1–F3 已关闭。** 具体修复身份、独立检查及限制见文末“同切片复审”。以下保留初审记录。

**初审需求符合性：需要修改。** 分方向选型、角色与实现解耦、CLI / Web 共用消费者和可信训练门禁分离均已有真实实现；但 F1、F2 破坏结果不明恢复和冻结输入语义，F3 丢失受支持 CUDA 候选的身份。

**初审可维护性：需要修改。** 模块归属及复用方向合理，无需新增框架或复制原生执行引擎。修复应留在现有 campaign 状态与驱动边界，明确持久状态及有效配置身份；当时边界对原生默认配置和恢复状态的假设不完整。

## 审查身份与范围

- 基线与当前 HEAD 均为 `3b52365`，分支 `feat/evolution-console`。工作区大部分实现尚未跟踪，因此读取原始文件，未把 `git diff` 当作完整变更范围。
- 直接审查的生产文件：`src/ergora/kernel.py`、`src/ergora/data/drivers/forge.py`、`src/ergora/data/training-agents.json`、`scripts/install-agent.sh`、`src/ergora/agents.py`、`src/ergora/tools.py`、`src/ergora/projects.py`、`src/ergora/reference.py`、`src/ergora/processes.py`、`src/ergora/cli.py`、`src/ergora/web.py`、`src/ergora/state.py`、`src/ergora/data/console/app.js`。按相对路径排序，以 `路径 UTF-8 + NUL + 文件字节 + NUL` 拼接的 SHA-256 为 `5ec0c5c0fca8667b23a7af5e476aa14c45251b5c500b1fdd9c55f9e393d1d20d`。其中包内文件与本次运行的非 editable `.venv-dev` 安装逐字节一致。
- 检查邻近测试：`tests/test_agents.py`、`tests/test_projects_tools.py`、`tests/test_reference.py`、`tests/test_web.py`；文档：`AGENTS.md`、`docs/PLAN.md`、S8 交付记录、`docs/AGENT_BACKENDS.md`、`docs/TRAINING.md`、`docs/USAGE.md`、`docs/INTEGRATIONS.md`、README、第三方声明、选型报告及其来源 JSON；安装 / 打包配置：`.gitignore`、`pyproject.toml`。
- ForgeKernel 固定源码 `5030503d3ff71851aa34c14b9caf13ebfa9d9a78`，核对其 `launch.py`、`runs.py`、`task.py`、`taskcard.py`、`localenv.py`、`paths.py`、README 和安装元数据。原生运行时来自忽略的 `build/upstreams/ForgeKernel` 与 `build/forge-env`，并非本次新增或打包的业务源码。

初审对应以上文件指纹。初审收尾时检测到作者正并行修改 `kernel.py` 与 `data/drivers/forge.py`；当时未将初审测试结果用于这些修正。修正的独立检查见文末复审。

## 发现

### F1 · 高：失败的 status 会擦除崩溃遗留运行的对账要求

位置：[kernel.py:86](../../src/ergora/kernel.py#L86)、[kernel.py:97](../../src/ergora/kernel.py#L97)、[kernel.py:113](../../src/ergora/kernel.py#L113)。

可达场景：`run` 已将文档保存为 `running`，尚未保存结果时父进程和驱动终止；缓存的 `native_record` 仍可能是 prepare 时的 `created`，而原生 `run.json` 已是 `running`。之后的 `status` 因临时机器配置错误、导入失败或超时未能读出原生状态。失败分支把文档写成 `failed`，却只对 `run` / `prepare` 设置 `requires_reconciliation`。于是下次 `run` 的三个判断全部为假，未提供对账依据也会调用原生驱动。

独立 CPU 探针：真实 prepare 后构造上述持久检查点，将 `FK_DELIVERY` 临时设为非法值使真实 status 驱动失败，再恢复环境；用调用拦截器阻止下一次进程创建。结果为 `after_failed_status=failed`、`requires_reconciliation=null`、缓存原生状态 `created`、`unreconciled_run_dispatched=true`。补上显式 uncertainty 标记的对照组会正确拒绝调用。没有执行原生 run、模型或 GPU。

影响：服务崩溃后的检查失败会绕过已承诺的人工对账步骤；固定上游具有脱离父进程存活的 GPU runner，不能据此确认旧作业已停止。该问题不直接生成 perfctl PASS，但会丢失资源生命周期控制。

最小修正：在开始有副作用的原生操作时先持久保存不确定性，直到成功取得明确结果才清除；或在恢复 `running` 检查点时建立此标记。失败 / 超时的观察操作必须保留原先的不确定性。增加“崩溃检查点 → status 失败 → 无依据 run 被拒绝”的 CPU 回归，覆盖 CLI / Web 共用的业务函数即可。

### F2 · 高：原生快照没有冻结实际生效的全局默认配置

位置：[forge.py:28](../../src/ergora/data/drivers/forge.py#L28)、[forge.py:32](../../src/ergora/data/drivers/forge.py#L32)、[forge.py:43](../../src/ergora/data/drivers/forge.py#L43)、[kernel.py:82](../../src/ergora/kernel.py#L82)。相关声明：[控制台预算说明](../../src/ergora/data/console/app.js#L1950)、[Agent 手册](../AGENT_BACKENDS.md#forgekernel-原生候选)。

固定上游的 [load_task](https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/task.py#L252) 每次都将当前 `global_config/models.toml` 和 `loop.toml` 合并到任务中；[new_run](https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/runs.py#L116) 仅复制任务目录。适配器保存的任务 SHA 不包含这些默认文件，运行前也只检查 `src/forgekernel` 的 Git 差异。因此修改共享默认配置后，同一 campaign 的模型、目标或继承预算可以改变，项目绑定与任务快照 SHA 仍完全相同。任务省略默认项是官方支持、示例已使用的正常输入。

独立 CPU 探针使用原生 loader 和 run 快照，仅将默认配置读取位置指向隔离副本：模型由 `claude-opus-5-5` 变为另一 ID，target 从 `1.2` 变为 `9.0`；另一份未覆盖 budget 的任务从 `4` 小时变为 `40` 小时。两次均保持快照 SHA 不变，原生 `open_run` 接受。未修改固定上游安装，也未执行 campaign。

影响：页面所称“预算来自冻结的原生任务”不成立；维护者为其他任务修改默认模型 / 预算，会改变已有 campaign 的支出和停止条件，其记录无法单凭当前快照身份复现。独立 perfctl 仍能拒绝未验证候选，但不能补回原生生成过程的输入身份。

最小修正：在 prepare 时保存有效合并配置或其全部默认来源身份，并在每次 run / resume 前核对；发现漂移时显式拒绝，不自动采用新默认值。也可在创建快照前将有效配置物化为自包含任务，再交给原生 `new_run`。不应修改冻结参考树或另写原生搜索流程。增加“prepare 后改默认模型 / 预算，同一 campaign 仍用原配置或明确拒绝”的 CPU 回归。

### F3 · 中：CUDA 候选 `best/kernel.cu` 未进入产物身份记录

位置：[forge.py:47](../../src/ergora/data/drivers/forge.py#L47)。

适配器接受 Forge 的有效原生任务，但产物采集仅枚举 `report.md`、`best/kernel.py`。固定上游 [taskcard.py](https://github.com/OpenBMB/ForgeKernel/blob/5030503d3ff71851aa34c14b9caf13ebfa9d9a78/src/forgekernel/taskcard.py#L35) 同时支持 CuTe DSL 和 CUDA，后者由 `write_report` 写出 `best/kernel.cu`。

独立 CPU 探针真实创建 `language=cuda` 的 campaign，加入明确标注为夹具、从未编译执行的 `best/kernel.cu` 和报告，然后执行真实 status。结果 `observed`，`artifacts` 只有 `report.md`，CUDA 候选文件存在但没有路径 / SHA 记录。

影响：已接受任务语言生成的主要候选产物缺失身份，无法从 Ergora 的操作证据确定具体 CUDA 文件；这也使手册的候选身份声明仅对示例 CuTe 任务成立。

最小修正：从冻结任务语言及上游 `kernel_file(task)` 获取候选文件名，采集实际最佳产物的路径和 SHA；或至少明确覆盖两种受支持文件名。增加 CPU 文件夹具，核对两种语言的候选都被记录。无需 GPU 性能测试即可验证此修正。

## 已核实的满足项

- `agents.py` 由独立调用和正式阶段驱动消费；`kernel.py` 由 CLI / HTTP 共用；模板元数据由 `reference.py` 交给复制、预览和结构输出消费者。新增边界有实际生产调用，未发现为假设消费者新增整套插件平台的问题。
- 训练合同只声明实验规划、性能分析、kernel 提案、产物及可信操作，不导入具体厂商。项目角色可切换 Codex / Claude Code / 自定义结构协议；mini 明确限于实现角色。原生 Forge 位于单独 kernel 层，不冒充通用提案角色或 Codex 原生后端。
- campaign 保存项目 ID、修订和具体绑定；改变当前绑定后仍访问原 campaign，跨项目 ID 查询拒绝。现有 CPU 测试实际覆盖这两项和任务文件篡改拒绝。
- 固定版本、Python 要求、Claude-only、local-only 和 GPU / 模型尚未验收的声明与检查的上游实现一致。ForgeTrain 尚未发布自治 Harness、KDA 为工作流及知识资产、Optuna 为搜索组件、Agent Lightning 为训练框架的区分合理。未发现用上游性能数字冒充本项目实测排名。
- `native_finished` / `native_failed` 只写原生候选记录；没有调用可信评价或把 Forge judge / `target_met` 转成 PASS 的路径。现有训练手册仍要求候选提交、冻结 manifest、可信 runner、正确性 / 质量及配对性能复验和 evidence SHA 人工放行。
- 安装器使用固定源码和独立 venv，不暗中安装 CUDA / PyTorch 或调用模型。GUI 有角色表、kernel 层绑定、计划 / 创建 / 状态 / 同 campaign 继续及对账依据字段；界面共享服务端状态。

## 实际检查与限制

审查环境为非 editable `.venv-dev`，Python `3.11.15`。本次独立执行：

1. 显式设置固定 Forge checkout / Python 后，`python -m pytest -q tests/test_agents.py -k forge`：**1 passed，8 deselected**。只有 CPU plan / prepare / status。
2. `python -m pytest -q tests/test_agents.py tests/test_projects_tools.py tests/test_reference.py tests/test_web.py -k 'not mini and not forge'`：**25 passed，3 deselected**；仅既有 TestClient/httpx 弃用提示。
3. 上述三类 CPU 探针与继承预算探针均复现发现。隔离运行数据在忽略的 `build/s8-training-review-fixtures/cpu-probe/`，它们是临时检查点 / 候选文件夹具，不是发行源码、可复用测试套件或用户运行环境。未编辑业务源码、依赖、冻结参考文件，未使用作者的浏览器或运行服务。
4. 直接核对源码树全部 **283** 个冻结文件，全部匹配 manifest；原始 ZIP SHA 为 `8018be5094623ca0646d28d3671daaf7ac60774280eefc1c5c023bc19dc5c760`。
5. 对照选型来源 JSON 校验已下载官方文件的字节数及 SHA：ForgeKernel **13** 文件、ForgeTrain **3**、KDA **2**、Optuna **3**、Agent Lightning **3**，全部匹配固定版本；检查相关 README、许可及接口声明。未重新联网查询上游最新状态。

作者交付记录的全量 `103 passed + 36 subtests passed`、Chromium 和其他安装验收是本次阅读的既有证据，未在本审查中重跑。没有运行付费模型、Claude 认证、GPU 性能、SSH delivery 或原生 GPU 作业取消；不据此作质量 / 性能优劣判断。冻结参考文件身份和门禁入口的检查也不等于重新进行了真实训练数值实验。

初审结论：F1、F2 阻塞训练方向验收，F3 也应在完成 S8 前处理。保持模型 / GPU 效果为未验证状态是正确边界，不额外要求本轮扩展到这些运行。修复后需对相同故障场景和现有 CPU 路径复验，并记录复审结果。

## 同切片复审

日期：2026-10-31。由同一独立审查者对作者完成的 F1–F3 修正复核；原始发现及检查结果保留为历史记录。

**需求符合性：通过，限本报告的训练方向范围。可维护性：通过。** F1、F2、F3 均已关闭，复核范围内没有新的阻塞发现。修正保留现有状态所有者、真实原生 API 和候选 / 可信验收边界，不需要另建配置框架或执行引擎。其他审查者负责的 mini 协议、监控回收、Codex 路径和页面异步归属修正不由此结论代为批准。

### 修复后的文件身份

HEAD 仍为 `3b52365fe56d79c7b467a73e369b5a42c2b5afc9`，分支和未提交交付方式不变。重新阅读 `docs/PLAN.md`、S8 修复记录、下列文件及相关原生调用；两个生产文件与本次测试使用的非 editable `.venv-dev` 安装逐字节一致。

|文件|SHA-256|
|---|---|
|`src/ergora/kernel.py`|`85981649cf75c4e252e5e28f1c991f553457b6b808d508c1237d1bd9cf681a3b`|
|`src/ergora/data/drivers/forge.py`|`bdbc4f9a1ab1f4bbf72cec2f4ca127169fe0791015148be214ab419a9c0db13b`|
|`tests/test_agents.py`|`783b182f11c7e13de22d917629313d58d75a4d9cd87d2212bf1ac8f56aa303e2`|
|`docs/AGENT_BACKENDS.md`|`9a2bf28e2824a3f3e0c8e6fad88d18d7a53390a4067e88437ace312e3a6cd2ed`|

原生 Forge 仍固定 `5030503d3ff71851aa34c14b9caf13ebfa9d9a78`；复审采用安装脚本产生的完整独立工具环境，其 Python 为 `3.12.3`，应用测试解释器为 `.venv-dev` 的 `3.11.15`。该外部安装环境没有作为仓库文件或测试夹具提交。

### 逐项处置与独立反例复验

- **F1 关闭。** [kernel.py:78](../../src/ergora/kernel.py#L78) 在观察操作改写状态前，将恢复的 running / unknown / 原生 running 转换为对账标记，并随操作持久保存。独立探针复建了原始崩溃检查点和原生 running 记录；真实 status 因非法机器配置失败后，新 `State` 仍读到 `requires_reconciliation=true`；恢复配置后即使 status 成功，标记也保留，无依据 run 被拒绝。提供明确依据的对照组能够到达调用边界并归档依据；该调用在创建进程前被拦截。
- **F2 关闭。** [kernel.py:144](../../src/ergora/kernel.py#L144) 保存 `models.toml`、`loop.toml`、`backends.toml` 的字节身份，[forge.py:21](../../src/ergora/data/drivers/forge.py#L21) 在原生操作前核对。独立探针使用完整固定源码的隔离克隆及真实 prepare / status，分别改变默认模型、默认预算和 backend 文件；三者都使 status 显式拒绝，恢复对应文件后都能再次观察原 campaign。另直接加载实际驱动、仅拦截 `drive`，核对三个漂移对 run 同样在进入原生执行前拒绝；恢复后的 run 对照组能够到达拦截点。没有执行搜索、模型或 GPU。手册同步说明配置身份、恢复原配置、备份及运行期间不修改共享默认配置的约定；当前是操作入口身份检查，不宣称强隔离或复制了完整运行环境。
- **F3 关闭。** [forge.py:52](../../src/ergora/data/drivers/forge.py#L52) 使用快照任务及原生 `taskcard.kernel_file` 选择实际候选文件。独立探针分别真实 prepare CuTe DSL / CUDA 任务，加入未编译、未执行的候选夹具，再执行真实 status；`best/kernel.py`、`best/kernel.cu` 均保存了与实际字节一致的 SHA。手册也已覆盖两种文件名。

### 复审检查结果与范围

1. 完整固定原生安装上的 `python -m pytest -q tests/test_agents.py -k forge`：**3 passed，9 deselected，2.85 秒**。涵盖原有计划 / 创建 / 状态 / 项目归属 / 篡改拒绝及新增恢复 / 漂移 / CUDA 身份回归。
2. 上述独立探针全部通过；摘要保存于忽略的 `build/s8-training-review-fixtures/recheck-result.json`，运行文件夹为同目录下的 `cpu-recheck-6a6252eb/`。这是隔离检查数据，未作为业务运行安装或发行测试套件。
3. 再次直接核对全部 **283** 个冻结参考文件，全部匹配原 manifest。
4. 首次复审选择旧 `build/upstreams/ForgeKernel` 研究缓存时得到 **2 passed、1 fixture setup failed**：隔离 `git clone --shared` 因该缓存缺少部分 Git blob 而无法检出，尚未进入漂移测试。确认具体错误后改用完整固定安装，得到上述 3 项通过；没有修改研究缓存或产品源码，也未将夹具失败隐记为通过。

作者更新记录中的 **36 项定向、107 项全量 + 36 子测试**及浏览器验证仍是作者证据，本轮没有重跑整套测试或作者服务。本次只修改此审查报告并生成隔离夹具；不安装依赖、不更改生产源码、不提交或推送，也不调用模型、GPU、SSH delivery。模型质量、GPU 性能和原生 GPU 作业取消的未验证边界保持不变，不影响本次明确限定的 CPU 接口及身份合同验收。
