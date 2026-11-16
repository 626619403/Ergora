# 父请求留存 CI 再平衡独立审查

2026-11-16。Reviewer：fresh-context 独立 reviewer `parent_retention_ci_balance_review`。只读检查产品、调用者及既有原件；唯一写入为本报告。遵循根／scripts AGENTS、组件“脚本和检查”协议，以及 maintainable-project-delivery 独审 brief、ergora-codebase-quality test-seams。

## 结论

需求符合性 **approve**；维护性 **approve**；本片 findings **0**，阻塞代码 finding **0**。结论仅覆盖配置再分配及已记录收集／映射证据，不认证新组合测试正文、运行时长或发布。新候选自己的原时限官方 CI 仍待验。

## 精确范围与核验

基线／检查时 HEAD 为 `c4c0946060ba781eb8b2cb2e7e9d3ad2798dcd5a`。完整非 docs 产品 diff 只有 `scripts/ci/linux-groups.json`；其他在途 docs 状态／设计不属于本片，未修改。配置只把完整 `tests/test_composition_tasks.py`、`tests/test_services.py` 从 group5 移到 group1，保持原排序和现有接口，无新增抽象、配置维度或检查框架。

独立从 git baseline、当前 JSON 和 `.ergora/checks/parent-retention-ci-balance/` 原件读取计算：

- 原 SHA256 `9923dbdb2ab8282e9840a98f1b22828189d441e8ea7758b9b188f8e9ecdf4608`；新 `5995dfe1bd13235475fbbfd79b2ff51dc2065f302924e465e4fa1474456241df`。baseline／candidate 原件分别与 git／当前文件逐字相等。
- 六组、86 唯一文件，前后集合相同；新文件数13／16／12／18／13／14，恰两文件5→1。
- 读取前后完整 phase 原集，以 Counter 独立核2295→2317，无删除；新增恰22，与固定 r3 installed-retention-r3.xml 逐 node 相等。原70节点仅随上述两文件移动；按当前 JSON 计算各组349／355／409／453／315／436。
- 保存的 selection-1／5 collected node 序列分别与从完整2317节点计算的选集逐项相同。检查 verify.py 确实调用原 PhaseLog，使用模拟 item 仅回放路径选择；这不是执行测试。完整收集 phase 仅 identity／coverage／collected／finish，无测试 phase。既有 result 退出0、4.622秒；本审查未重跑 collector 或该写原件的 driver。

阅读 `scripts/ci/run.py`、`pytest_phases.py` 和 `.github/workflows/portability.yml`：矩阵依六组生成原六 Linux job，加原 Windows all；runner／job及 Linux20分钟、Windows30分钟未变。runner 一个 pytest 子进程；插件按完整文件路径筛选并验证重复、缺失、未登记路径。Windows all 不传 ci-group，插件在读取 Linux JSON 前返回。本片没有删测试、改测试正文或绕过保护。

## 闭包与成本依据

直接检查 composition_tasks 显式导入及 fixture 定义：composed_creation→creation_project→registration→installation，前三者 function scope，installation module scope并用 tmp_path_factory 独立复制参考安装；runtime_client／native_client／cancellation_client 为 function scope monkeypatch，指向显式 fixture 文件。未见必须同 group5 测试共同执行才初始化的共享对象；导入 fixture 不要求收集其源模块正文。services 自有 function stack，独立临时目录／配置／state／supervisor，finally shutdown并等待 socket 消失。移动完整模块没有拆散其模块 fixture。

独立核两文件与旧 b6538cf 正文逐字相同；旧完整 JUnit 分别50节点／79.714秒、20节点／52.196秒。当前 product 依赖与远端环境不能因此视作旧状态。

读取旧准确 a0d533d 的 `20261116T005631Z-summary.json`：官方43780806957、push／attempt1、准确 head、completed success，八 job success；group5 1123秒、group1 238秒。预算调查保留较早005135Z Windows在途快照是历史事实，不能覆盖后来的终态。新增22安装选集116.27秒只说明额外串行成本方向；旧两文件131.910秒与远端 job／安装选集不可线性相加减。本片把现存工作移向较空组有证据依据，没有证据保证新候选20分钟内通过。

## 未验边界

本审查只执行 git／文本读取和只读 Python JSON、phase、JUnit、哈希核算；未执行 tests、collector、安装、网络、提交。未认证新组合正文、fixture实际跨模块交互、Windows运行或远端时长。已有旧 CI 成功不转授父留存及新 JSON；后续应保存准确新公开候选自己的原六 Linux／Windows 官方 CI 终态，实际失败再沿对应节点定位。
