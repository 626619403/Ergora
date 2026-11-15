# 训练回归 CI 分组独立审查

日期：2026-11-16。Reviewer：fresh-context 独立 agent `training_ci_shard_review`。使用 `ergora-codebase-quality` 与 `maintainable-project-delivery`，先读适用规则、[原始计划](../plans/2026-11-16-training-ci-shards.md)与实际 tracked／untracked 变更，再读[作者交付](2026-11-16-training-ci-shards.md)及[成本调查](2026-11-16-ci-training-shard-duration-analysis.md)。没有继承实施对话。

## 身份与结论

审查产品／测试树为隔离分支 `fix/training-ci-shards`，HEAD／比较基线均为 `97a0bbfae9687c15927f1437a374cd070baf0a94`；本次检查其三个未提交文件。主项目 docs 为本报告 owner。

|文件|检查时 SHA256|
|---|---|
|`tests/test_training_submission.py`|`31ad45584fa959e9b792a2b20c1e9598b580ac2e4f70f98d49109a4a649e0681`|
|新 `tests/test_training_cycle_controller.py`|`c59e8e5d178fa252d639f99ad40630293169a05714102320232679c83e1cd2f3`|
|`scripts/ci/linux-groups.json`|`298e4160010d20840f2152fb647e5f58eddfc43948fa92fa1c55d190164ec0e0`|

**需求轴：C1／C2 源码与静态覆盖 approve；C3 安装行为／成本及 C5 远程预算 pending。维护性轴：本次迁移 approve，未发现需修订的源码问题。** 开放源码 finding 0；这不是此片完整验收通过，也不认证20分钟问题已经解决。

## 独立核对

- 直接读取 HEAD 原文件、新文件及实际 diff，以 AST 仅定位函数，再比较包含装饰器的完整原文。37个测试及唯一 helper `admission_process` 全部逐字相同，余下92个原顶层函数也未变；合计仍130个函数，没有重复定义／删除测试。原模块非函数顶层语句也相同。因此原参数、故障预算、恢复／生命周期断言及函数内 skip 均保留。
- 新模块的显式导入不含测试函数；依赖方向为新模块→原 submission→既有 training／runtime／registration fixtures，没有反向依赖。`prepared → experiments → registration → installation`、`controller_admission → cycle_selection`、`cycle_candidate`／`controller_dispatch`的真实闭包均沿原 owner 复用，未复制 fixture。新文件对应 controller 同意／停止／恢复及 candidate root 生命周期的完整接缝，满足独立模块必要性；不是新通用测试框架。原模块其余 preparation／SDK／stop 测试仍使用这些 fixture，保留其原 owner 合理。
- 对新模块及嵌套闭包做 symbol-table global 解析，无缺失符号。原 helper 的 `__file__` 仍指向同一个 tests 父目录，admission 子进程 fixture 路径不变；复用 helper／fixture 的函数全局仍归原定义模块。没有依赖测试模块名字的 monkeypatch／动态全局查找。新模块除 docstring、import、定义之外无顶层执行语句。
- 读取原 collect 编排、私有观察插件、实际五轮 request／result、snapshot 与 phase JSON 原件，独立重算前后 Counter，未运行作者会写 verification.json 的脚本。Linux2227节点、Linux上Windows选集2172节点，仅归一新模块路径后逐节点一致，Counter每项为1；两边的 snapshot 与原 plugin coverage nodeid 同一。所有节点 fixture 定义来源／源码摘要／scope／依赖参数与闭包顺序一致；受影响模块全部 markers 一致。原 plugin 两轮 identity SHA256均为 `a4737ae2314c3a6ce67c88470488363b2ddd9ee27757f896a189b628a640b2d9`，与实际源码相同；各收集 result均0，phase无 collection失败事件。
- 原 plugin 的真实 selected 节点为 group2 386→461、group5迁后539；迁前614来自原coverage按固定原group5核算。JSON仍六组，文件数12／13／14／15／12／20，86个路径唯一且存在，应用 test模块无漏项。只新增一个现有group2条目，runner／workflow／plugin未改，无增job、删节点、缩预算或延长超时。
- 37个迁移测试均保留 `sys.platform != 'linux'` 的 test级 skipif。依赖的 fixture函数体不会在import时启动安装／服务；pytest skipif语义仍在fixture setup前生效。此次Windows选集实际仍在Linux收集，无法据此认证原生Windows执行或提前skip成本。

## 安装边界与尚缺的验收

`tests/test_training_runtime.py:16` 的 `installation` 仍为 module scope；普通分支复制 reference，managed分支调用 `reference.prepare_training`并创建无pip venv。新模块显式暴露原 fixture后，请求模块改变；fixture源码／scope一致不能证明构造次数和成本相同。managed的5个execution-boundary节点及其参数、普通节点的安装选择均原样保留。新增模块可能额外触发普通及managed构造，参数调度也可能改变重建顺序；这属于已明确记录、待实际测量的成本，不是可由AST或collect证明的无成本变更。

C3仍需同一新非editable安装产品下完整跑group2／5，保留准确产品／测试身份、request、JUnit、phase、退出及原进程收尾；检查安装setup／teardown错误、真实停止／恢复故障和所有节点终态。若安装观测只能得到test phase级setup时间，应明确它不能单独分离每次fixture构造，而不能声称已经量出准确构造次数。出现失败应读原故障证据后做最小修订，再按精确差异复核。相邻SDK happy-path的control_timeout显式配置调整不在本次三文件身份内，若合入需另核原文差异及受影响运行证据。

C5需要最终候选自己的官方Linux group2／5在原整个job20分钟限制内完成；本地成功不替代它，历史其他候选或单项时长不可相加认证。真实Windows未运行，远程478完整逐项日志未取得，不能确定当时超时所处的节点／phase或宣称根因已完全证明。

本review仅做必要只读源检查与无资源 `python -B` JSON／AST／symbol-table探针、`git diff --check`（通过）；没有运行suite、安装、服务或网络，没有修改产品／测试、commit或push。唯一写入为本报告。下一步由主控补C3原件，再在相同／明确更新身份上终核；本报告不要求无依据扩大其它组运行。
