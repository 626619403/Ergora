# ADR 0002：静态依赖保护与 R8 出口

日期：2026-11-02。状态：采纳。适用范围为当前自有单包，不重写冻结参考项目。前置决策见 [0001](0001-refactoring-foundations.md)，当前所有者、A1结案及兼容退出条件见 [架构图](../current.md)，实际验收见 [R8记录](../../delivery/2026-11-02-refactoring-exit.md)。

## 问题与选择

R1–R7 已集中组件/schema/DDL、拆开资产/采用与调用用例、划定 reference 边界并拆分前端。需要在后续功能加入时及时发现反向导入和新环，不通过每个文件的全部 import 白名单锁死结构。

|方案|能力与代价|结论|
|---|---|---|
|[Import Linter](https://import-linter.readthedocs.io/)|成熟声明式 layers/forbidden/independence 合同，Grimp 构图；本次 PyPI 2.15（Python >=3.10）需 Click、Grimp、Rich、typing-extensions，新增开发依赖/配置及命令|后续出现多包/外部SDK层级合同、复杂间接依赖规则时重评；本轮不安装|
|既有 pytest + `ast` / `graphlib`|对当前27个顶层文件及函数内 import 做少量规则，无新依赖/命令；只覆盖语法显式导入|采用，放 `tests/test_architecture_boundaries.py`，随现有 Linux/Windows 回归运行|
|全库 Ruff/Pyright 严格化或新通用插件/图分析器|解决不同问题，会扩大到历史风格、类型及第三方代码，不能替代实际运行验收|不纳入本轮，不格式化冻结/第三方文件|

标准库检查只有测试消费者，不引入生产“架构框架”或通用解析命令；两个 pytest fixture 负责读取实际安装包和派生局部导入边，无持久图索引。现有动态兼容/运行测试继续使用，不再复制一份旧 API 行为实现。

## 约束与失败场景

1. 自有顶层 import 图无环。包括函数内 import，防止评价重新导入采用用例或调用层反向依赖 facade；`graphlib` 报告实际环。
2. `components / contracts / state / windows_job` 不导入应用模块；`processes` 只允许消费 `windows_job`。这些是当前底层职责边界，新增项目/评分/HTTP行为应留在上层，不搬到基础模块。
3. 除入口自身，其他自有模块不得导入 `cli / web / __main__`。CLI 可延迟加载 Web，业务不能要求传输栈或从入口取共享规则。
4. `agent_platform / dev_platform` 以及随包 `ergora.data.reference` 下模块的显式导入只在 `reference / reference_executor`。检查普通 `import`、绝对/相对 `from` 和函数内导入；冻结目录可作为 namespace package 导入，不能只检查原顶层包名。其他调用者使用现有资源/编译接口或既有用例，避免 HTTP/资产代码直接操作原全局/ledger。

这些规则允许上层自由组合既有域模块，没有全库逐文件白名单。变更底层职责时先更新 ADR 和实际消费者，再按行为验收，不把新增白名单当成解决耦合的方法。没有新增子包；若后续拆包，必须同步包发现/资源验收，并将本检查范围升级到相应包图，不能让新源码静默落在保护之外。

## 检查与限制

```bash
python -m pytest -q tests/test_architecture_boundaries.py
```

测试从 `ergora.__file__` 定位被测包；CI 先非 editable 安装 wheel，因此同时约束实际安装的代码。直接源码开发应显式选择对应解释器或 `PYTHONPATH=src`，避免误验旧安装。

静态检查不解析字符串中的 Python、`importlib` 动态模块名、JS、子进程命令、隐式属性访问或运行时配置，不证明权限/取消/恢复/模型效果。`reference` 的专用编译/动态执行桥、SDK driver、前端 ES modules、包资源身份及平台生命周期分别由现有测试和真实探针验证。R8 使用隔离安装副本注入反向导入和环，记录检查确实拒绝的结果；不在产品或 CI 中添加自我镜像测试框架。

R8 不改变运行代码、默认值、证据摘要或 SQLite schema，不引入数据迁移或新增同步双写器。现有两个项目配置入口仍明确可见，单向有效配置属于 F1；正式任务/页面属于 F3/F4。回退本节点只撤销文档/测试提交，不能用它降级 R3 已迁移的数据。
