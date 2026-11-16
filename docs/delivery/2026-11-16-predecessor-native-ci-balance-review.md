# M5／native 最终 CI 分组独立审查

2026-11-16。Reviewer：fresh-context 独立 agent `predecessor_native_ci_balance_review`。先读原始要求、Git diff、最终 collector／selector 与实际 fixture，再读作者交付；应用 maintainable-project-delivery independent-review brief 和 ergora-codebase-quality test-seams。

需求符合性：**approve**。可维护性：**approve**。本配置审查范围内无 finding，开放阻塞项0。这不是最终候选测试正文或远端时限认证。

## 准确身份与范围

- 实施基线及当前主树 HEAD：`3a57987dcca17395d7fd993843c28255013e2970`。
- 唯一被审产品配置：`scripts/ci/linux-groups.json`，未提交 raw SHA256 `8ffe961f3e4578485186d864430b9f93becf5eed81bea37338a6aa0015e685ab`；基线 raw SHA256 `5995dfe1bd13235475fbbfd79b2ff51dc2065f302924e465e4fa1474456241df`。
- 收集产品：`bc58be6781d35e7e4fbd54ad997df8a4743428a8`；安装冻结清单指向同一完整 OID、空源码 diff。最终证据根为 ignored `.ergora/checks/predecessor-gates-ci-balance/final-native-r5-four-files/`。
- 根 AGENTS、scripts/AGENTS、组件脚本检查协议、PLAN、原 runner／PhaseLog、原 workflow 均已检查。其他并行产品和文档修改不在本配置审查范围，不递归审查作者报告。

## 独立核验

直接读取 Git 原始 diff，重算配置：仅 `test_training_preparation.py`、`test_task_budget.py`、`test_training_runner.py`、`test_training_runtime.py` 四完整文件从5→1；其余文件归属完全相同。六组文件数13／20／12／18／13／10，总86个唯一文件，基线与新配置文件集合相同。

直接解析原 `all/phases.jsonl`：2335个唯一节点，无未分配文件；六组重算354／444／410／453／315／359。与前一单文件配置的最终同产品 collection 比较，node multiset 相同。原 selector 日志组1／5分别444／359，与重新按文件归属计算的完整集合相同。四文件当前节点分别15／12／7／55，共89，全部进入组1。

直接比较父留存原 `.ergora/checks/parent-retention-ci-balance/all/phases.jsonl` 的2317节点：四个已有节点改名的旧／新ID实际存在，映射后无删除；净增集合恰为 comparison.json 的18节点。不能将原始ID差异称为字面集合不变。

对 collector-root 中855个非缓存文件逐一核 frozen-inputs.json 的字节摘要／执行位，仅指定JSON不同，无其他输入差异。目录另有一个生成的 `pytest_phases.cpython-312.pyc`，不属于冻结源码输入。原 collector 内层返回0／6.778秒，外层记录0／6.874秒；未将二者混为同一计时。未重跑collector或测试正文。

fixture核对使用准确复制输入：registration 在 tmp_path 下建立repo／control／config／runtime；experiments、runner_project、preparation_input 和 task_budget 的 full_creation→work_creation／work_graph 沿原 function fixture 构造。installation 为 module fixture，通过 tmp_path_factory 建立独立目录，managed／managed-v2按参数选择原临时venv。模块间直接导入fixture并不要求来源模块的测试正文同组选中。runtime_client及SDK替换沿 monkeypatch；检查所见未发现依赖组5其他正文先运行或共享持久目录的新增耦合。此为静态隔离检查，不能替代新组正文执行。

原 `.github/workflows/portability.yml` 与基线字节相同：六Linux、Windows all、Linux20／Windows30分钟、原安装／上传流程保持。Windows all 在 runner 中不传 `--ci-group`，因此本JSON搬组不改变其选择。

## 成本结论与未验范围

旧公开组5的17分31秒和组1的7分07秒提供分散成本的合理方向；旧JUnit为三个保持正文文件提供历史成本，runtime已有55节点，不能沿用其旧26节点成本作为新总耗时。选择四个完整既有文件利用目标组余量，保留原selector和fixture，未引入新调度或拆分规则。不能把旧文件秒数相加作为远端节省，也不能仅凭节点数证明均衡；作者当前交付明确保留这些限制，没有预记最终时限通过。

本次只做配置、原始证据和相关fixture的短只读检查，唯一写入为本报告；未安装、网络、启动服务、运行测试正文、修改产品或提交。新联合准确候选仍须自己的官方六Linux／Windows结果认证正文、跨文件运行和20／30分钟时限；当前审查可接受配置进入普通整合／发布步骤，不转授历史候选CI成功。
