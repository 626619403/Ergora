# Forge 调用约束与源码身份交付

日期：2026-11-14。按[本片计划](../plans/2026-11-14-forge-native-admission.md)推进，基线 `f4da08b9ff7c1dae92222677a43d8b56b87c78b0`。原件留在项目私有检查目录，公共文档不包含认证配置或机器路径。

## 当前状态

已核实际 Forge checkout 为既定 `5030503d3ff71851aa34c14b9caf13ebfa9d9a78`，初始无已跟踪或未跟踪修改。C2.0 只读接缝调查和 C2.1 源身份维护、隔离发行包、自身模板与新独立两轴已完成，开放 0／0，本地出口通过。普通发布／自己的 CI 另记；尚未实现完整 native 子模板。

一次真实 Claude 禁工具／禁 MCP 请求退出 0，5.275 秒，返回预定标记，原结果 `is_error=false`／`subtype=success`。stdout 1,697B，SHA256 `f8d0250d2051cecadcf780e05fbc1eba39c0c27bbb24ba28e68bf4579d4fdc51`；stderr 为空。它是配置状态检查后的实际推理补验，不证明 Forge 内部调用或角色隔离。

源码检查发现：原 `_call` 只检查 `src/forgekernel` 的 Git diff，实际 agent、超时和 policy hook 还执行 `scripts/` 文件。相同 HEAD 下修改脚本仍可能通过原门禁。C2.1 将在原 owner 修正此真实路径，并保留原 global_config 摘要合同。

独立源码设计调查另记[接缝报告](2026-11-14-forge-native-seam-design-review.md)；这是设计证据，不代替本片实现后的新独立审查。完整材料、权限交集、预算／停止和外部候选评价缺口保持开放。

## C2.1 实现与验证

原 `kernel.py` 内新增一个私有 Git 身份算法，由 `available` 与 `_call` 共用；检查包和 scripts 的 tracked 变动及非忽略未跟踪文件。doctor 对已修改源码显示 `version=unsupported`／`task_availability=blocked`，`installed` 仍仅反映可导入。原 driver、global_config 摘要、campaign／unknown／candidate 合同和依赖不改。

两项回归在独立基线源码上均实际失败：修改 tracked `scripts/timeout-run.py` 和新增包内未跟踪 Python 文件，旧 doctor 都错误显示 pinned。新源码五个 Forge CPU 用例通过，包含原 prepare／status、崩溃对账与配置漂移；不调用模型／GPU。测试使用独立 clone，不编辑日常 Forge 安装。

新 Python 3.11 noneditable wheel SHA256 `27b75368f2bae2def2371c8f1a129428c01a3be9a9dabf05902436a01fe5fdb2`，551 产品与源／安装逐字节相等，两 RECORD 及 283 冻结文件通过。安装版 agent／component／platform suites 23 通过、9 跳过，pytest 17.09 秒、监督 18.845 秒；跳过为 3 个未选 mini SDK 验收和 6 个 Windows 专属用例。没有重跑既有完整模型旅程或 GPU 实验，日常应用尚未升级到本片。

当前 Claude Code 2.1.312 可完成上述只读推理；本容器 bwrap 基本启动实际退出 1，错误为 `Failed to make / slave: Permission denied`。它说明本次沙箱探针未启动，不以此推断所有其他环境均不支持。原生策略的 `failIfUnavailable` 不被关闭；file-only MCP 会移除 teacher 原 shell／probe 工作流，未用它替代原算法。

## 自身模板与后续范围

原随包结构审查模板先选择与实现作者不同的 Claude backend；三份完整源码／测试／手册 50,239B 和三份继承资源均在实际 input／stdin 中。该次原 run `7383a3cae113413aa91a42ea6bc610ff` 在 240.495 秒超时，没有判词；不从早先简单标记成功推导结构化审查可用。

按用户明确授权，以同一候选文件的新输入回退到 Codex，run `251ab86208114773a7b0c2bb053c6861`，37.233 秒成功、`approve`，原 result SHA256 `237a6a09291bd6b49809f8eec90cf1f408819b6619eaccd89fb2e2c27d91e6ac`。三全文及全部继承资源在实际 input／stdin 中，input digest `e17b82b80776bc3063f5ea21d4b40db87fbdbbd502e12f7bde5d1f23154eda4f`。模型确认原 owner／共用算法和行为回归合理；它只做文本审查，没有独立运行测试或证明完整 native 能力。此成功回退不称异后端审查成功。

新 fresh-context 评审者已核原源码、测试、wheel／安装、模型与失败原件，[本片独立审查](2026-11-14-forge-native-admission-review.md)需求／可维护性通过，开放 0／0。最终七文件快照 manifest SHA256 `0bd91926c679334f5d16a91ce0c681ab136d565c8fca02304ffac6027fd8bca1`，产品／测试／手册与已验包及模型输入身份一致；后续状态记账不改变行为。

完整 C2 的工作会话／compact 继承、权限、绝对预算及真实停止仍开放；纯连接验证／标题元数据与工作子 Agent 按实际影响分开，不能只因存在辅助请求就预建通用代理。下一可独立推进 F8-H2 真实只读 Harness 调用；B3 等待实际 workload，旧原件与未验范围不改写。
