# Windows SDK fixture skip 独立审查

日期：2026-11-16。Reviewer：fresh-context 独立代理 `windows_sdk_skip_review`。按根／tests AGENTS、组件协议“脚本和检查”、maintainable-project-delivery independent-review brief 及 ergora-codebase-quality 的 test-seams／repository-style 审查。仅只读检查源码与原件并写本报告，未运行测试、安装、服务或修改 Git。

需求合规：**approve，开放 finding 0**。维护性：**approve，开放 finding 0**。结论限于本片两个提前平台标记；不认证新候选全平台 CI 已通过。

## 精确范围

隔离树 `windows-sdk-skip` 的 HEAD 为 `3a176c75f4afdc73f9fbe96ffd37a7fb26854f4a`。完整实际 diff 仅为 `tests/test_training_submission.py:2806`、`:2866` 各新增一个既有邻居同款 `skipif(sys.platform != 'linux', ...)`，分别覆盖父失败三参数及容量失败三参数。未改产品、fixture、参数、断言、预算、CI 或测试数量。

基线文件 SHA256 `cdfeb4be11d583d3c9675cf224adfd3f64cbb81195c33b81139689bc49779915`；候选文件 `dd8cfb287145ebd6881b74b87bbbcbc1f64112d36d4a666ce85e786009167599`；实际 `git diff` SHA256 `a609ff40a466f7d42d053cbdfb8387c86c2c4a6268e10a60860b551024ced6f3`，与保存的 `change.patch` 字节同一。核实基线与官方 `86356927cd88750717bb910502e3f7bd66aa41ba` 在 src／tests／scripts／.github 无差异。

## 真实失败与修正边界

直接读取 `ci-training-shards/publication-r1` 的 run-r5-response、jobs-final-response、windows-final-response、windows-annotations-response 原件。官方 run 43747795571，push／attempt1、准确 head 86356927，终态 completed／failure；六 Linux job success，Windows 回归 failure，PowerShell 5.1 安装升级 success。原 annotations 明确列出本片六节点的 Linux-only submission ValueError，汇总为 1190 passed／976 skipped／6 errors、16 subtests passed、1459.85 秒。原失败没有被局部结果覆盖。

实际依赖 `cycle_sdk_activity → controller_dispatch → controller_admission`；授权／prepare 与 SDK fixture 的真实 supervised operation 在函数体前执行。`src/ergora/reference.py:503` 的 submission owner 对非 status、非 Linux 明确抛错。仅在函数体内处理无法阻止 setup 失败，函数级 skip 是恰当的 pytest 边界；邻近 SDK 测试已采用同一方式。新增条件在 Linux 为 false，全部六节点、参数和原测试体保留，Linux 执行覆盖没有削减。

## 验证证据及限度

直接读取 ignored 检查目录 `windows-sdk-fixture-skip` 的 `check_boundary.py`、三个原始日志、verification-summary 及 patch，并交叉核对输出。脚本先在 Linux 导入依赖，仅 reload 目标模块时临时设 win32，finally 恢复 Linux；随后真正调用 pytest，以 fixture setup sentinel 阻止任何 fixture 函数体执行。修前六 setup errors 是 sentinel 的错误，首次钩子 tmp_path_factory，不能称作 Windows 原生 ValueError 复现。修后六 setup skips、fixture 钩子零调用，证明标记确实在 fixture 前生效。Linux collect 六节点条件全 false，节点身份一致。

上述局部导入平台模拟是针对装饰器求值及 pytest setup 顺序的适当轻量检查，交付记录已准确标注；不是原生 Windows SDK 行为认证。原生错误证据来自官方 annotations。两行机械标记不需要另增重复测试、CI 或重新认证无变化的训练／模型；未提出无依据全 suite 要求。

后续验收依赖：主线导入／提交／发布后，新候选仍需以自己的官方 Windows／Linux CI 记账。旧候选六 Linux 成功只属于旧候选；本报告不提前宣称全平台完成。无阻塞代码 finding。
