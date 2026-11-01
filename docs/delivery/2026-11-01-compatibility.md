# S11 / A2：兼容保护与边界决定

日期：2026-11-01。开始基线 `cab3a724e421d0a7d9ff6f03dfcbd3225361e2f1`，从已推送 main 创建 `refactor/architecture-foundations`。生产树与 A1 相同；没有改生产实现、运行依赖、数据或 283 冻结文件。

## 本切片与产物

- [兼容与操作基线](../architecture/2026-11-01-compatibility.md)：实际命令、边界检查映射、旧格式、操作步骤与测量限制。
- [ADR 0001](../architecture/decisions/0001-refactoring-foundations.md)：内置 JSON 组件描述、R2 JSON Schema/jsonschema 依赖选择及替代方案、状态权威、R3 旧二进制问题、reference/生命周期/训练人工入口。决策不冒充运行实现；A2 没有安装或新增 jsonschema。
- [7 项固定兼容测试](../../tests/test_compatibility_baseline.py)与 [身份](../../tests/fixtures/compatibility-v0_2_0/identities.json)、[旧 schema](../../tests/fixtures/compatibility-v0_2_0/schema.sql)、[合成旧状态/资产](../../tests/fixtures/compatibility-v0_2_0/state.json)。schema 捕获旧版 16 表；旧数据只证明读取、修订与未知状态保留，不声称历史 evaluator/Forge 可执行。
- [CI](../../.github/workflows/portability.yml)：增加 refactor/** push 入口，Linux 复用 frozen AdapterTests/RuntimeTests；保留真实 Windows / Linux wheel 和原安装/合同检查。没有启动完整 Temporal WorkflowTests 或服务。

没有新生产函数/抽象。测试 fixture 是旧格式的独立构造者，不调用当前 State 初始化来生成“旧库”；固定期望从重构前捕获，不能随未来实现一起变更。所有样例为合成，无私有凭据、机器 home 或真实运行数据。

## 实际验证

使用既有 `.venv-dev`：Python 3.11.15，Ergora 0.2.0，pytest 9.2.0，PyYAML 6.0.3，FastAPI 0.162.0，Pydantic 2.14.2，Temporal 1.34.0，GEPA 0.1.4。jsonschema 没有安装于该环境。

1. 变更前原组合（tests + frozen contracts/portable）：109 passed、17 skipped、36 subtests passed、1 warning，81.53 s。
2. 新复用的 frozen AdapterTests + RuntimeTests：28 passed，1.89 s；不启动 Temporal server。
3. 新兼容测试：7 passed，1.05 s；POSIX 和普通 Skill 向量、compiled SHA、旧库重开/新进程/冲突通过。
4. 安装后的无模型 command 旅程：7 个计数操作、1.18 s、succeeded、revision=2，完整输出可读；不含安装/输入/认证/正式执行。
5. 首次最终 Linux 组合在 collection 失败：显式选择 frozen AdapterTests 时不能依赖其他测试的导入副作用，缺少 dev_platform 路径。已在 CI 的该 Linux 测试子进程明确设置冻结 platform PYTHONPATH；不修改运行时环境或冻结代码。随后直接执行修改后的 CI Python step：**144 passed、17 skipped、36 subtests passed、1 warning，78.64 s**。
6. 静态检查：65 本地文档链接/围栏、fixture JSON、CI refactor 触发和 Python step 语法通过；git diff --check 通过；运行/脚本/依赖/旧 HTML 与基线零差异；reference.verify PASS 283。两 OS wheel / CI 结果待实际运行，不预先标通过。

17 个原基线跳过包含原生 Windows、未显式选择的 SDK 和隔离 Temporal 服务；不从历史 115 项计数推导本轮未跑的可选检查。FastAPI 的 httpx 弃用提示可见，本切片没有为消除 warning 顺带升级依赖。

独立审查：待新 fresh-context reviewer；当前实现已整理，最终验证未收口。公开推送用于实际两 OS CI，审查和节点完成状态另记。

## 迁移/回退与下一步

本节点没有生产迁移；测试和 CI 入口可正常 revert。固定历史夹具保留为后续保护，不重写旧摘要。R2 新依赖在其节点接入并验 wheel；R3 必须解决旧 0.2.0 不识别 user_version 的实际限制，不能只新增元数据就宣称拒写。

完成本节点检查/独立审查、提交推送并核对后，R1 集中静态描述和真实消费者，保留现有绑定语义、独立运行及可选 SDK 边界。每个节点继续更新 PLAN、详细登记及交付记录；重构出口验收前不宣称 all-in-one 功能闭环已实现。
