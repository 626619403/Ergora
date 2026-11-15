# c1b2a：已安装包定向检查 r1

日期：2026-11-16。产品候选为 `feat/training-cycle-service` 的 `fef7d98e30d5625e5ce37dc45e14904f76447775`，产品比较基线 `6725e62511aa4a5b68baf684ec3cbc1f0470d3e6`。本次只运行冻结输入对非 editable 安装包的定向检查；没有修改产品或测试，没有提交、推送或启动准备项目的服务。

使用 package-r1 的新 SDK/core 环境及同一178份冻结输入。wheel SHA-256 为 `b7e282af7a9e154a6b61525ca36cbc9d834ef0d2c92fb701dae5bea69685fcfd`；来源身份检查记录663个产品文件 source/wheel/installed 相等，SDK环境 Temporal SDK 1.34.0。包身份核对沿用本轮准备原件，不冒称此处重新构建。

私有证据位于项目 ignored `.ergora/checks/training-cycle-service-acceptance/installed-tests-r1/`；包和冻结输入位于同父目录 `package-r1/`。以下以 `$A` 表示此验收父目录的绝对路径；实际完整 argv、cwd 和环境分别保存于 `collect.command.json`、`tests.command.json`、`core.command.json`，结果及耗时保存于对应 `*.result.json`，stdout/stderr各自完整保存。运行脚本 `run.py` 和 `core-check.py` 也保留。

工作目录为 `$A/package-r1/test-inputs`，清除 `PYTHONPATH`，设置 `PYTHONDONTWRITEBYTECODE=1`，先 collect：

```bash
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 "$A/package-r1/venv-r1-sdk/bin/python" -I -B -m pytest \
  tests/test_services.py tests/test_architecture_boundaries.py \
  tests/test_training_runtime.py::test_cycle_sdk_capacity_counts_metadata_and_rejects_without_truncation \
  tests/test_training_submission.py \
  -k 'test_services or test_architecture or cycle_sdk or cycle_candidate or cycle_operation_cancellation or cycle_cold_inspection or cycle_stop_notifies or cycle_stop_exhausted' \
  --collect-only -q
```

确认68/216项，148 deselected，collect退出0、1.86秒。随后同一选择移除 `--collect-only` 并追加以下参数运行：

```bash
-q --junitxml="$A/installed-tests-r1/junit.xml" --basetemp="$A/installed-tests-r1/basetemp"
```

结果 **67 passed、1 skipped、148 deselected，531.82秒，退出0**。JUnit、pytest basetemp、完整 stdout/stderr 均保留；stderr为空。分布为 services全文件20项（19通过、1 skip）、architecture boundaries全文件16通过、runtime capacity1通过、submission指定组31通过。唯一skip为 `test_native_windows_reports_wsl_requirement`，原因为 `Native unsupported-platform check`；本轮Linux不能认证原生Windows行为。运行中正常等待约9分钟，没有按时限杀进程。

core环境另执行私有独立脚本：

```bash
env -u PYTHONPATH "$A/package-r1/venv-r1-core/bin/python" -I -B "$A/installed-tests-r1/core-check.py"
```

脚本从 `preparation-r1/paths.json` 读取准备项目 control路径，真实读取唯一项目 `cycle-service-acceptance` 的 `services.status`，结果daemon=`not_running`；确认 `temporalio` 不存在，再真实调用 `services.control(state, project_id, 'start', ['training-cycle-worker'], revision)`，得到明确 `ValueError: The selected training worker requires ergora[temporal] in this application environment`。再次status与首次完全相同，退出0；没有实际启动服务。完整前后status和拒绝文本保留在 `core.stdout`，stderr为空。

本轮不重跑历史76+7或BR50整组，不认证全库、准确CI、发布、真实Temporal双queue/独立进程容量、真实Supervisor准备栈生命周期、信号/fatal收尾、正式总Workflow、sandbox、接受后继或真实训练质量。服务测试使用受控服务fixture；其结果不等同准备栈真实长期服务验收。
