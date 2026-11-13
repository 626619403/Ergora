# 测试维护

在仓库根目录使用 Python 3.11 或更新版本。日常检查可安装 `.[dev,web,gepa,temporal,task-mcp]` 后执行 `python -m pytest tests`。真实 Temporal 检查需用 `ERGORA_TEMPORAL_TEST_ADDRESS` 指定隔离服务；未提供服务或可选能力时，原测试的 skip 保留。

CI 验证安装后的 wheel。要在独立虚拟环境重现此接缝，先安装 `build`，执行 `python -m build --wheel`，再安装 `dist/` 中生成的 wheel 及 `dev,web,gepa,temporal,task-mcp` extras；不要使用 editable 安装，也不要将 `src/` 添加到 `PYTHONPATH`。随后执行：

```bash
python -m ergora reference verify
python scripts/ci/run.py --collect-only --output .ergora/checks/collect-all
python scripts/ci/run.py --group 0 --collect-only --output .ergora/checks/collect-group-0
python scripts/ci/run.py --group 0 --output .ergora/checks/run-group-0
```

每次使用新的结果目录；命令拒绝复用目录，防止把旧日志当作本次结果。省略 `--group` 或指定 `all` 会选择本平台的完整范围。Windows 使用 `all`；原生 Windows 的 PowerShell 5.1 安装／升级检查仍由 CI 单独运行。Linux 的范围为 `tests`、冻结参考的 contracts、portable、workflow 的 `AdapterTests` 和 runtime；Windows 为 `tests` 与 contracts。CI 脚本只将观测 plugin 和 Linux 参考导入路径加入 `PYTHONPATH`，应用仍从当前解释器安装的 wheel 导入。

Linux 按[文件清单](../scripts/ci/linux-groups.json)分组，每个测试文件只登记一次。新增文件时将其加入一组；移动文件时同步改该处。plugin 先收集完整范围，再选择当前组，拒绝漏登记、重复分配、缺失文件、无效组及空选择。整文件执行保持文件内 fixture 和用例顺序，组间使用独立 runner。对各组执行 `--collect-only` 后，核对其 `collected.nodeids` 并集等于全量 collection、交集为空；仅检查分组数量不足以证明完整覆盖。

组数从同一 JSON 生成 GitHub Actions matrix；每组仍构建／安装 wheel 并核参考身份，job 上限为 20 分钟。调整分组前，使用实际阶段耗时评估最慢整文件和安装／上传余量；不要用删除故障／恢复检查掩盖超时。最初的分组依据见[分段成本记录](delivery/evidence/2026-11-13-linux-ci-costs.json)，它是历史测量，不能代替新候选实际运行。

结果目录保存 `request.json`、完整 `stdout.txt`、`phases.jsonl`、JUnit 和正常收尾时的 `result.json`。JSONL 即时记录全量／实际选中 nodeid、阶段起点、setup／call／teardown 的结果、耗时与失败正文、collection 跳过／失败和 session 终态。子测试的 `report_type` 与父用例不同；子报告耗时已包含在父阶段内，不应再次累加。正常的 pytest exit 0 才表示该次选择通过；`--collect-only` 只证明收集／选择，不能作为测试通过。

中断可能缺少 session 的 `finish`、JUnit 或 runner 结果；最后阶段起点只能定位在途范围，不能证明死锁。CI 尝试用 `always()` 上传已落盘文件，但 job 硬截止或 runner 丢失后不保证上传成功。缺失原件、取消和未完成结果均保留其实际范围。观测入口保持 `python -m pytest`，不要在自定义脚本顶层调用 `pytest.main()`，以免 spawn 重新执行驱动。
