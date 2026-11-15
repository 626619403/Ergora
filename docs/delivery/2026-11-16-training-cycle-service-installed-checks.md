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

## 修后定向安装复验 r2

准确候选更新为 `eedba08c8c112683a7946726aab3f4fd590f26d6`，使用独立新 `package-r2/venv-r2-sdk`／`venv-r2-core`，wheel SHA-256 `747e221b584fa71518e2b64ce69fcace2eb4ef1340450cfd50e6f47e8729e017`。沿用本轮准备记录确认663产品文件、283参考文件及依赖检查通过；178份tests/examples在build前冻结。r1结果只适用于原候选，未把旧67项整体复跑或转记为修后通过。

新证据保存在同一验收父目录的 `installed-tests-r2/`，r1未覆盖。工作目录为 `$A/package-r2/test-inputs`，命令如下；先同一选择用 `--collect-only -q` 确认 **20/211项，191 deselected，1.55秒，退出0**，再运行：

```bash
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 "$A/package-r2/venv-r2-sdk/bin/python" -I -B -m pytest \
  tests/test_training_runtime.py tests/test_training_submission.py \
  -k 'cycle_sdk or cycle_service_closes or cycle_rejects_complete_aggregate_capacity' \
  -q --junitxml="$A/installed-tests-r2/junit.xml" --basetemp="$A/installed-tests-r2/basetemp"
```

结果 **20 passed、191 deselected，155.47秒，退出0**，无skip或失败，stderr为空。覆盖新R1–R4定向接缝：四种真实SDK关闭生命周期、父侧popen/cleanup/oversized-parent失败保留、request/stdout/frame容量失败收尾；以及原SDK来源认证、32候选66完整分支引用、重投、正常start、metadata容量和原aggregate容量。完整实际argv/cwd/env、collect、stdout/stderr、JUnit、basetemp及结果均在该独立目录保存。

r2 core实际导入worker且确认无 `temporalio`，对本轮 `test_cycle_sdk_start_hands_off0` 已通过且finally完成原budget stop的fixture执行原 `_CycleOperation(..., mode='inspect')`。使用已有authorization/ready，父异步loop期间禁止 `State._open`、`sqlite3.connect`、`training_cycles._load`／`_read_bytes`及 `protocol.read_raw`；真实S-H子进程完成inspect，返回 `inspected`／原submission `submitted`。9份原cycle文件逐字未变、业务数据库dump未变、原operation payload/window未变，子进程已退出；不查询SDK、不重开执行、不操作真实服务。

```bash
env -u PYTHONPATH "$A/package-r2/venv-r2-core/bin/python" -I -B "$A/installed-tests-r2/core-inspect.py"
```

最终core退出0，操作1.207秒（完整subprocess1.664秒）。详细返回保存在 `core-inspect-r2.json`，命令/结果/stdout/stderr及脚本同目录。首次私有检查脚本误将ready位置写成 `controller/ready.json`，在H启动前触发前置断言失败；已先报告主控，保存 `first-core-*` 完整脚本和日志。仅改私有验收脚本为真实cycle根 `ready.json` 后重跑通过，未修改产品、冻结测试或原业务记录。

本轮不重复r1 core离线service status／缺SDK启动拒绝，不重跑原67项总组、旧76+7或BR50。真实Temporal/Supervisor服务验收由另一独立任务记录；本轮没有操作其daemon、项目或7233。上述源码fixture与安装定向证据不能认证正式总Workflow、sandbox、接受后继、真实训练质量或准确发布CI。

## launch容量修正后的新安装 r3

产品候选为`97a0bbfae9687c15927f1437a374cd070baf0a94`，新wheel SHA256=`081aab4594f8afa18505c3ec8a8b78ff98690510303a7041e3074af5fcab38cf`。新core／SDK各663产品文件及执行位source＝wheel＝site，283参考核验和依赖检查通过；core无SDK，SDK1.34.0。相对478发布产品仅六个原owner变化；相对eedba08只有budget与worker的精确容量分类处理，无新产品模块。178个tests/examples在build前重冻；独立reviewer也逐文件核过两套r3实际安装，不仅采用作者summary。

`installed-tests-r3/`以原新包`-I -B`、unset PYTHONPATH运行冻结输入，选新launch容量、正常handoff、普通来源ValueError、丢offer、cleanup race与三旧容量接缝。collect实际**9/186**、177 deselected、1.26秒，运行**8 passed／1 failed／118.82秒**，完整命令、JUnit、stdout/stderr与basetemp保持。初败不改记通过：正常handoff测试期望observed但得到unknown；原7秒control window逐字同一，H已经真实submitted／唯一attempt，最后采样距截止约0.101秒，父侧仍须实际S退出、收齐帧及期限验证，过期unknown符合产品合同。

[独立复核](2026-11-16-training-cycle-service-final-review.md)未发现此处产品缺陷，同意只为该正常场景使用原fixture显式`control_timeout_seconds=30`，保持共用fixture默认7、故障预算及全部断言。该一行测试配置修订在`installed-tests-r3b/`重新冻结178输入，记录完整diff／源码身份，使用同一已核r3产品包仅复验受影响单项；初始8个通过项的产品／测试字节不变，不为配置修订重复整组。新单项与无SDK S-H读核结果待补，不与旧候选或不同输入混计总通过数。

r3b新冻结单项最终 **1 passed／21.58秒**，同一r3非editable SDK包、实际导入site-packages、unset PYTHONPATH、`-I -B`，新参数id及完整collect／命令／JUnit保留。其后在r3 core无SDK环境执行真实原`_CycleOperation(mode='inspect')`：H／S实际退出、返回inspected／原submitted，父loop禁用State／SQLite／业务reader，9份原cycle文件、DB dump和原window逐字保持。操作0.857秒、完整subprocess1.321秒，退出0。首次私有probe因pytest的`current`符号链接与实际目录同时匹配而在H启动前断言失败；完整`first-core-*`保留，只把私有取样条件改为排除symlink后通过，未改产品、配置或业务原件。

该一行测试修订已固定`af176cf6e79adb9c6ef6f32946672bc77cdb89de`；产品字节与97a0bbf／wheel081aab45完全相同，未重新构建无变化产品。初跑8通过／1失败与r3b一项通过分别保留其输入身份，不能描述为同一组一次9通过。SDK-free probe不查询SDK、未执行训练或创建服务；真实服务N2／N32在单独现场记录中验收。
