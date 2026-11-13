# 2026-11-13 Linux CI 耗时与测试结构只读调查

结论：`00922d302daa371ab980093889a8468694c10a94` 自己的 Linux CI 超过 job 预算已证实，具体根因仍未确定。原本地采样也没有完成，不能以最后显示的迁移测试、后续 stdin／轮询修正、测试数量或某个 timeout 参数替代根因证据。当前没有证据支持删除一批测试来关闭出口。

本调查仅新增本文；没有修改产品、测试、CI 或计划，没有运行测试、模型、服务或完整 suite，没有远端写入，也没有接触当前 A2 的进程或端口。按 maintainable-project-delivery、codebase-design 与 diagnosing-bugs 区分原始观察、静态成本、推断和建议。没有已经运行且能重现此次 CI 超限的紧凑 red loop，因而本片不进入“已定位／已修复根因”状态。

## 身份与证据范围

- 远端候选是 `00922d302daa371ab980093889a8468694c10a94`；[Portability 43373597757](https://github.com/626619403/Ergora/actions/runs/43373597757) 和[发布记录](2026-11-13-publication-status.md)仍是跨平台状态入口。
- 只读源码以该提交及原冻结 source 为准。核对 `git diff 3122487fe57d43188cd5c5a42a787d506a29d5a7 00922d302daa371ab980093889a8468694c10a94 -- src tests .github pyproject.toml` 无差异。原安装是 A1 的非 editable wheel；上述两提交的产品、测试和 CI 内容相等。当前工作树另有后续修改，不能混作原 CI 身份。
- 原 `test-identity.json` 的 92 项与 `git ls-tree -r --name-only 00922d302daa371ab980093889a8468694c10a94 tests` 一一对应；逐项 `git show <SHA>:<path>`、SHA256 和冻结 source 字节均相等。92 项是整个 `tests/` 子树的 tracked 文件，其中 71 项是 `test_*.py`，其余包含 fixture、JSON、SQL 和 PowerShell 文件。
- 本地原件位置是私有验收目录 `publication-2026-11-13-r1`：控制器 `profile-linux-r1.py`、`profile-watchdog.py`，以及 `linux-profile-r1/{request.json,test-identity.json,process/stdout.txt,result.json,summary.json,watchdog.json}`。远端使用 `ci-terminal-html-r1.json` 的步骤投影；没有新发起网络读取。
- `test-identity.json` SHA256 为 `e0ab7d0f4defccb5ac1c0ed6c63e061403d160e609f64798aa6db2bcfd0075f5`；原 stdout SHA256 为 `c672440d4f9fd57f3a1b2e506e8ece67c6bb470c4d410258de8151186b77f7bd`。本文没有复制原 HTTP headers、运行时绝对路径或环境变量值。

以下源码位置均指 [00922d3 固定提交](https://github.com/626619403/Ergora/tree/00922d302daa371ab980093889a8468694c10a94)，不是对后续修改的审查。

## 事实：CI 实际执行内容

`.github/workflows/portability.yml:17–70` 只有一个 `native` job 的双 OS matrix：Ubuntu／Python 3.11、Windows／Python 3.12，`fail-fast: false`。`timeout-minutes: 20` 位于 job 层，覆盖 checkout、Python setup、wheel 构建安装、reference 身份和回归；它不是给 pytest 单独的 20 分钟。

安装命令包含 `dev,web,gepa,temporal,task-mcp`；回归只有一次串行 pytest 调用，没有 xdist、文件分片或 pytest 级单 case timeout：

```text
python -u -m pytest -v --tb=short --durations=20 <suites>
```

|选择|Ubuntu／Python 3.11|Windows／Python 3.12|
|---|---|---|
|`tests/`|全部选择，平台 skip 仍由各测试决定|全部选择，平台 skip 仍由各测试决定|
|冻结 reference `tests/test_contracts.py`|选择|选择|
|冻结 reference `tests/test_portable.py`|选择|未选择|
|冻结 reference `tests/test_workflow.py::AdapterTests`|只选该类|未选择|
|冻结 reference `tests/test_runtime.py`|选择|未选择|
|`tests/windows-installation.ps1`|未选择|回归后的独立步骤|

reference 路径共同前缀为 `src/ergora/data/reference/platform/upstream/platform/`。静态定义分别是 contracts 21、portable 27、AdapterTests 20、runtime 8 个 unittest 测试方法。Linux 比 Windows 额外选择 55 个方法。没有选 `test_workflow.py::IntegrationTests` 的 8 个方法，也没有选择冻结 reference 下其余所有测试文件。`AdapterTests` 使用临时文件和 synthetic adapter；`test_runtime.py:28–34` 使用 AsyncMock。不能把导入 `WorkflowEnvironment` 等同于启动真实 Temporal。

`tests/test_budget_workflow.py:31–35` 的 7 个真实本地 Temporal 场景在测试函数内检查 `ERGORA_TEST_TEMPORAL_BIN`。workflow 没有配置该变量；原本地控制器还显式移除了它。这证明原本地没有运行这些场景，不能据此补造远端 skip 数量。函数内 skip 发生在 fixture 解析之后，仍可能支付 `budget_creation`／`full_graph` 的 setup 成本。

原 CI 的 HTML 步骤投影：

|步骤|Linux|Windows|
|---|---|---|
|Build and install wheel|success，15 秒|success，35 秒|
|Packaged reference identity|success，起止同秒|success，2 秒|
|Native application regression|cancelled，1182 秒|success，816 秒|
|PowerShell 5.1 installer and upgrade|不适用|success，55 秒|

这些秒数来自步骤起止时间相减，不是完整日志中的 case durations。Linux job 页面明确报告 `The job has exceeded the maximum execution time of 20m0s`。整体 Cancelled；Windows 四必要步骤成功不关闭 Linux 出口。未取得 Linux 全量日志，所以不知道远端最后执行到哪个 case。

## 事实：原本地 30 分钟采样的上限

控制器实际选择与 Linux CI 相同的五个 suite 路径，通过 `-I -u -c` 调用已安装 Python，并在程序内把冻结 reference 路径加入 `sys.path`；pytest 另加 `--basetemp` 和 `--durations=30`。环境是 Linux／Python **3.12.11**／pytest 9.2.0，和远端 Python **3.11** 不同。

原 stdout 收集到 1696 items。终态行重新计数为 891 PASSED、26 SKIPPED、0 个已报告 FAILED；最后未完成行是：

```text
tests/test_state_migrations.py::test_backup_failure_prevents_any_migration
```

最终进度约 54%；还没有任何以 reference suite 路径开头的执行进度行。stdout 没有 durations footer、完整 pytest 终态摘要或逐 case 时间戳。`result.json` 是 1799.910 秒、`status=cancelled`、`returncode=-9`；watchdog 记录了 30 分钟边界向精确旧控制器发 SIGINT，进入其原有 finally／reap 路径。

固定提交的 `src/ergora/processes.py:128–136` supervised 分支按 0.2 秒 `communicate` 轮询，但这里没有比较 `timeout` 截止时间；原采样依赖外部 watchdog 才在指定边界停止。这是**采样控制器的限制**。CI 的回归步骤直接使用 `subprocess.Popen`，没有通过这个 supervised 分支包裹整个 pytest；不能把两者混作同一超时机制。

最后显示的 case 源码在 `tests/test_state_migrations.py:237–254`：函数级 `old_home` fixture 建立旧 SQLite 状态，测试在备份连接处注入错误，再检查 schema、原记录和不完整备份清理。它本身没有显式 sleep 或启动子进程；实际调用进入 `State(root)` 的 schema lock 和 SQLite 备份路径（`src/ergora/state.py:144–186`）。这些源码事实不证明它快，也不证明它卡住。没有该 case 的 setup／call／teardown 起止及栈，最后一行不能用于归因。

## 事实：已经存在的累计成本与生命周期检查

对原冻结 `tests/**/*.py` 仅作 AST 统计：660 个 `test_` 定义、68 个函数级 fixture、3 个 module 级 fixture；有 108 处 `subprocess.run`、12 处 `Popen`、25 处 `shutil.copytree`、45 处 `time.sleep` 和 15 处 `asyncio.sleep` 调用。计数包含 fixture/helper，排除字符串里被子进程执行的 Python，也不是运行调用次数或耗时排名。参数展开和函数内循环会放大运行次数。

|实际调用／位置|已经证明的工作|必须保留的行为；尚未测量的部分|
|---|---|---|
|`tests/test_services.py:33–100` 的 `stack`；12 个测试直接请求它|每次复制 reference 两个目录、生成 Supervisor config、创建受控服务脚本、执行 Git init／空提交、创建 State／注册；finally 在自己 socket 存在时请求 shutdown，并以 0.1 秒间隔观察消失，最多 10 秒|独立 ownership 和真实 shutdown 不能省略。10 秒是上界，不是每次固定支付；setup、start、stop、teardown 的分量未知|
|`tests/test_services.py:202–221`、`src/ergora/services.py:179–235`|受控进程忽略 TERM，测试把 stopwaitsecs 设为 3 秒；先以 1 秒得到 unconfirmed／STOPPING，再确认真正停止且只发送一次 stopProcess。产品按 0.1 秒观察实际状态|不能把停止请求当停止完成；不能为省时间删除第二次观察、清理或仅检查返回码|
|`tests/test_composition_executor.py:14–81`|22 个参数化 case 各启动一次 `reference_acceptance.py`；不同 case 进入成功、构造前拒绝、输入／review 失败或恢复路径|共同 setup 重复是事实；这些 mode 的验证点不同。45／90 秒 subprocess timeout 是上限，不能相加作为实际耗时|
|`tests/test_full_stage_materials.py:103–115`、`tests/test_work_agents.py:150–165`、`tests/test_review_dag_runtime.py:248–279`|分别有 6、11、9 个 case 再经同一个 reference fixture 进入材料、work、DAG／旧版本路径；fixture 在 `tests/fixtures/reference_acceptance.py:21–92` 复制 reference、建 config／repo／State／checks，成功路径再执行实际产品 owner|启动解释器、复制和持久化可能累计；不同 fixture mode 不是同一测试的无条件重复。没有各 mode 的时间分解|
|`tests/fixtures/reference_acceptance.py:575–582`；`tests/fixtures/stage_agent.py:69–73`|成功路径固定观察 1.2 秒，检查 review 派生的 1 秒后写入是否被清理；取消路径另有 2.2 秒观察（reference fixture:245–262）|这类等待是观察“后来没有写”的窗口，不可直接替换成“现在文件不存在”。可评估用精确进程身份／退出确认缩短，但要保留“实际启动、清理完成、无迟到副作用”的证据|
|`tests/test_processes.py:49–66`|normal／timeout 两个 case 都先确认真实 descendant 启动，再固定等待 4.2 秒，检查 4 秒后迟到写未发生|至少存在两个 4.2 秒观察窗，外加产品运行耗时；正常完成和超时使用不同清理路径。不能将二者合并为只测成功返回|
|`tests/test_budget_jobs.py:230–249`、`:322–396`|最终 fsync 注入 5 秒延迟；重启容量场景固定观察 3 秒，覆盖一个以上 admission tick|防止过期 success、重启后重复占槽／提前放行，不能以更短的 sleep 冒称等价。可以测量各场景实际成本后再改可观测同步方式|
|`tests/test_budget_submission.py:21–40,65–79`；`tests/test_task_budget.py:138–197`|有真实原 budget 到期等待、慢材料和 detached descendant 注入；提交恢复只能 lookup，不能再 start 或续预算|`sleep(60)` 等出现在被预期终止的受控 worker，不能当成测试会完整等待 60 秒。等待与收集／回收必须分别计时|
|`tests/test_state_migrations.py:95–133,152–254`|8 组 schema×journal 升级、旧 writer fence、失败回滚、进程骤停和备份失败|数据、旧 writer、恢复、非完整备份清理是不同不变量。不能因同一 `State` 构造多次就删掉失败／恢复检查|

现有可复用例子是 `tests/test_registrations.py:16–21` 的 module 级只读 installation，以及 `tests/test_architecture_boundaries.py:14–36` 的 module 级 AST 图；不是所有 fixture 都每 case 重建。跨文件导入的 module 级 fixture 也不等于整个 session 只复制一次。共享可变 State／repo／runtime 会改变隔离和失败恢复的语义。

## 冗余审计的证据边界

**可证明的重复工作**：CI 的 `python -m ergora reference verify` 经 `src/ergora/cli.py:594` 调用 `reference.verify()`；`tests/test_reference.py:12–13` 再调用同一函数，读取并核对同一 manifest 的 283 文件（`src/ergora/reference.py:35–43`）。后者还固定检查文件数。该重叠真实存在，但身份步骤只占远端起止同秒／2 秒，没有证据表明删掉这一调用会解决 1182 秒／1800 秒问题；283 冻结合同和独立安装步骤仍须保留。

**未证明可以删的断言**：静态扫描发现相同表达式重复出现，但抽查均有中间操作，例如：

- `tests/test_agent_definitions.py:61–69` 在幂等导入之后、失败修订之后分别检查原 index；不是同一时点的重复。
- `tests/test_task_approval.py:60–69` 在重复操作之后、项目 revision 改变后的恢复之后分别检查 signal 只发生一次。
- `tests/test_review_dag_runtime.py:182–198` 在前驱尚未完成时、取消到达结果交付之后分别检查后继未被启动。
- `tests/fixtures/work_delivery_acceptance.py:227–281` 在不同 stage 的材料上检查 root task、issue source 和原 artifacts；删除一处会放弃对应交接接缝的校验。

目前没有证实“高成本而不增加行为覆盖”的可删除 case，也没有证实可删除的昂贵断言。断言文本相同、共享 fixture、参数矩阵大或普通路径会报错，都不足以证明冗余。按 codebase-design 的 Interface／Seam 看，这些测试分别跨 CLI、HTTP、持久恢复和进程生命周期；仅在同一实现行相遇，不代表测试相同 Interface。先归并纯重复 setup／等待的测量，再考虑缩小测试表面，不能反向把故障检查删掉以制造 green。

## 推断：现有事实能支持到哪里

1. Linux 在 `tests/` 内已有多种 Windows 会跳过的实际 owner／subprocess／Supervisor 路径，差异不限于最后追加的 55 个 reference 方法。原本地在执行到 reference 之前已经达到 30 分钟；仅把追加 reference 方法拆出不能作为已经足够的修复。
2. 重复解释器启动、reference 校验／复制、Git／SQLite 初始化和固定负向观察窗是合理的**待测成本项目**；静态计数不能对它们排序，更不能说明哪一项主导。
3. 仍无法在“多数测试累计超预算”“少量长 case／setup／teardown”“一次顺序依赖或锁等待”之间选择。没有 per-phase 时间，甚至不能确认最后一条停在 fixture 还是 test call；没有栈则不能宣称死锁。
4. 不能按 54% 把 1800 秒线性外推为总耗时；后半段并非等价工作。Python 版本、runner、依赖解析和本地采样控制器不同，也不能把本地 1800 秒直接当作远端所需预算。
5. 后续 stdin／poll compact 修正的受影响检查结果只证明各自范围，本调查不审查它们，也不把它们用作“全部 CI 根因已解决”的证据。

## 建议：下一次紧凑测量

先只运行原来最后未完成的 **一个** case，使用原冻结 source／非 editable A1 Python，记录 setup／call／teardown 的即时事件，并在 15 秒仍未完成时输出栈。目的只是检查是否存在可独立重现的迁移慢路径，避免被最后一行锚定；不启动服务或模型。以下命令是下一片可执行探针，**本片没有执行**：

```bash
profile_python=.ergora/checks/refactoring-preset/install-r1/wheel-venv/bin/python
profile_source=.ergora/checks/refactoring-preset/install-r1/source
profile_output=.ergora/checks/publication-2026-11-13-r1/linux-migration-probe-r2
timeout --signal=INT --kill-after=10s 60s "$profile_python" -I -B -u - \
  "$profile_source" "$profile_output" <<'PY'
import hashlib, json, os, sys, time
from pathlib import Path

source, output = (Path(value).resolve() for value in sys.argv[1:])
output.mkdir()  # Fresh directory; do not overwrite the original sample.
os.chdir(source)
sys.path.insert(0, str(source / 'src/ergora/data/reference/platform/upstream/platform'))
import ergora, pytest

if 'site-packages' not in Path(ergora.__file__).parts:
    raise SystemExit('Expected the recorded non-editable installation')
target = 'tests/test_state_migrations.py::test_backup_failure_prevents_any_migration'
started = time.monotonic()
stream = (output / 'phases.jsonl').open('x', encoding='utf-8', buffering=1)

def emit(**event):
    stream.write(json.dumps({'elapsed': time.monotonic() - started, **event}) + '\n')

emit(event='identity', python=sys.version, product=ergora.__file__, target=target,
     test_sha256=hashlib.sha256((source / 'tests/test_state_migrations.py').read_bytes()).hexdigest())

class Phases:
    def pytest_collection_finish(self, session):
        emit(event='collected', nodeids=[item.nodeid for item in session.items])
    def pytest_runtest_logstart(self, nodeid, location):
        emit(event='start', nodeid=nodeid)
    def pytest_runtest_logreport(self, report):
        emit(event='phase', nodeid=report.nodeid, when=report.when,
             outcome=report.outcome, seconds=report.duration)
    def pytest_sessionfinish(self, session, exitstatus):
        emit(event='finish', exitstatus=int(exitstatus))

with (output / 'stdout.txt').open('x', encoding='utf-8', buffering=1) as stdout:
    saved_stdout, saved_stderr = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = stdout
    try:
        code = pytest.main(['-v', '--tb=short', '--durations=0', '--durations-min=0',
            '-o', 'faulthandler_timeout=15', '--basetemp=' + str(output / 'cases'),
            '--junitxml=' + str(output / 'junit.xml'), target], plugins=[Phases()])
    finally:
        sys.stdout, sys.stderr = saved_stdout, saved_stderr
        stream.close()
raise SystemExit(code)
PY
```

60 秒是本次单 case 测量的外部保护边界，不是建议给产品或 CI 新增 60 秒 timeout。运行前要确认这两个原路径仍保持原身份；该 Python 若不再可用，先用原 wheel／相同依赖重建并记录身份，不能悄悄换成当前源码或 editable 包。shell 返回 124／被信号中断、缺少 `finish` 或缺少 teardown 都应记为 incomplete。

探针快速通过，只能排除这一个 case 在独立条件下必现慢／挂，不能排除前序污染。若停住，先依据栈区分 schema lock、SQLite backup、注入或清理，再用最小前序复现；不能立即修改 migration。若独立通过，再把同一种逐阶段事件记录用于**同提交、Linux 3.11、同 wheel extras、隔离 runner 的原 suite**，保留所有 nodeid、环境／依赖和原退出状态；必要时按文件测量以确定最慢文件，明确文件隔离会改变原串行顺序。每条事件须立即落盘，不能再次只依赖结束时的 `--durations`。

## 建议：最小可验收 CI 方案

现在可以确定观测与覆盖要求，尚不能有依据地确定 shard 数量或新的分钟预算。

1. **先补可中断保留的测量。** 回归记录逐 case 的 setup／call／teardown、正在运行的 nodeid、轮询或清理中的栈；保留构建／安装与测试的独立时长。无论成功或失败都上传已落盘记录，给 job 的硬截止前留出明确的收集／清理窗口；硬终止仍可能阻断上传，不能保证 `always()` 能救回未写出的数据。JUnit 和最终 durations 可同时保留，但不能作为唯一来源。
2. **保持原覆盖和安装接缝。** Windows 四必要步骤、Linux wheel／283 身份／原 suite 均保持。下一候选的原 collection nodeid 集合应成为分组清单；如果分片，所有 required shard 的并集必须等于原集合、交集为空，并记录原本的平台／可选 skip，不能靠新增 skip 或取消变 green。需要这项清单校验是因为分片会产生可达的静默漏测风险。
3. **只在完整计时后按成本分组。** 若是多个独立文件的累计成本，优先显式文件清单的独立 Linux jobs，使 runner／runtime／临时资源相互隔离；按测到的 setup＋call＋teardown 平衡，不按字母／方法数量平均。保留有意的跨进程争用测试在原测试内部。当前没有 xdist 依赖和可并行性证据，不为这次问题先引入 xdist。若单个文件本身占满预算，先定位该文件的长阶段，增加 shard 不解决它。
4. **复用与等待改动另验。** 若 setup 主导，可参考现有 module 级 installation，只共享经核实不被测试写入的材料，保留每 case 独立 State／repo／runtime。若固定观察窗主导，可在原进程 owner 接缝观察精确 PID／start identity、退出／reap 和迟到副作用，保留真实 descendant 启动门槛。不能只缩短 sleep、去掉 finally、把 receipt 发布当作 cleanup 完成，或用 mock 代替所有生命周期旅程。
5. **预算来自测量。** 每个 job 需要覆盖冷安装、该组完整测试和 teardown、产物收集；以同 OS／Python 的实测完整耗时和观察到的抖动确定余量，并记录样本数。现有原件只给出一次超限和一次不等环境的中断，不能据此宣称 25／30／40 分钟或固定 N shards 足够，也不能把所有 subprocess timeout 相加作为预算。若完整计时显示主要是必要工作，适度调整预算可以成立；如果显示单点阻塞，则先修复可重现路径。

验收应落在新精确候选自己的 CI：全部 required jobs 完成、原 nodeid 覆盖守恒、安装产品身份正确、失败与 cleanup 的含义保持、实际耗时和剩余预算可检查。原 `43373597757` 仍是 Cancelled，原 30 分钟采样仍是 incomplete；本文没有把它们改写成通过。

## 本片校验与交接

已做只读 Git／SHA／stdout 计数、原 CI 步骤投影与固定源码调用核对。静态脚本没有导入产品模块或执行测试。本文内的下一测量代码只作语法核对，不宣称已运行。

下一 owner 先执行上述单 case 探针，再决定是否需要原前序重放或匹配 Linux 3.11 的 suite 计时；测量完成后由主执行者更新 [PLAN](../PLAN.md) 和[发布记录](2026-11-13-publication-status.md)。测试／CI 的实质改动仍需自己的验收与独立审查，本只读报告不代替这些门槛。
