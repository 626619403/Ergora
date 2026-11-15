# Windows SDK boot clock 测试提前 skip 独立审查

日期：2026-11-16。审查者：fresh-context 独立 reviewer `windows_sdk_clock_skip_review`。本片与此前 submission 两 mark 审查分开；只写本报告。依据根／tests AGENTS、组件协议“脚本和检查”、maintainable-project-delivery 独立 brief 和 ergora-codebase-quality 的风格／测试接缝要求审查。

需求结论：**approve**。维护性结论：**approve**。本片开放 finding **0**，阻塞 finding **0**；允许协调者将本片两行变更固定并导入，固定身份和候选自身 CI 仍需分别核实。

## 身份和范围

交接基线／HEAD 为 `bc602a38c9658bab8f8f431ac48f4969c76ebf95`，即已审 submission 两 mark 之后普通合入消费者 `01ef69b71137df860e8fc433362d039ae241e744`。按本次只读授权没有运行 Git，因此不独立重认证 HEAD、完整工作树状态或所报基线对 01ef 的全路径空差异；这些属于协调者的身份门禁。

实际读取隔离候选 `tests/test_training_runtime.py`、`src/ergora/budget_clock.py`、worker 的时钟调用位置、r2 完整 patch、边界脚本、三份日志及 summary，并核对实施报告 r2。独立计算 patch SHA256 为 `25b2968d03bd0cc8308c75d6ac9de9bf179b273eafc0f75eb1e013fec79be2b3`。patch 只增加标准库 `import sys` 和函数级 skipif。将候选文件逐字移除这两行，与当前主项目该文件逐字相等；未发现参数、测试体或断言改动。

## 需求与维护性判断

`tests/test_training_runtime.py:302` 的 `skipif(sys.platform != 'linux', ...)` 覆盖原四个参数节点，在 fixture setup 前选择跳过。原测试第315行仍真实调用 `budget_clock.authorize(wall)`；`budget_clock.py:13` 的 `_clock()` 明确拒绝非 Linux，Linux 路径仍读取 boot ID 和 `CLOCK_BOOTTIME`。worker 的 `_CycleOperation` 同样调用该 clock，因此限定 Linux 是实际执行约束。保留原窗口起点、deadline、控制／工作／清理预算关系、attempt1／2、禁止父进程业务文件读取和 envelope 断言，未用模拟 clock 扩大平台声明。

函数级现有 pytest 能力就是正确 owner，不需要修改 fixture、产品、clock、CI 或增加测试文件。标准库导入位于现有导入区，局部两行变更没有引入新抽象、依赖或重复回归。Linux 四参数继续可收集且标记为 false，既有真实 BOOT 验证路径没有被跳过。

## 证据及限制

核过 r2 `check_boundary.py`：依赖先按宿主正常导入，仅在目标模块 reload 时暂设 win32，并由 finally 恢复 Linux，再调用真实 pytest；fixture setup 的 tryfirst sentinel 在 fixture 函数体执行前抛错。三份日志末尾 JSON 与 summary 各节逐项相等：

- 修前四节点没有 skipif，4 setup errors／0.30 秒；session `tmp_path_factory` sentinel 实际调用一次，失败被后继节点复用。没有执行原测试 call，也没有复现原 `_clock` 异常。
- 修后同四节点 skipif 均 true，4 skipped／0.02 秒，fixture setup 钩子调用为零。
- Linux collect-only 同四节点、skipif 均 false，4 collected／0.02 秒；不证明四场景已重新运行通过。

这验证真实 pytest 的选择与 setup 顺序，平台输入仅作局部模拟，不能称 Windows native 回归。新消费者风险是静态确认的非 Linux call 阶段 clock 拒绝，不是原863官方六个 setup 错误。本报告不重审原863／旧两 mark，不改写历史失败，也不对879或后继候选的 Windows／Linux 官方终态作结论。

没有重跑测试、安装、服务、训练或 Git；没有修改产品、fixture、clock、CI、PLAN 或他人文件。未新增阻塞项；后续按准确固定提交核两行导入及完整范围，再以该候选自身必要 CI 认证发布结果。
