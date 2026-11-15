# Windows schema3 fixture 前置跳过：独立审查

2026-11-16。Reviewer：fresh-context 独立 reviewer agent `windows_schema3_fixture_review`。项目／文档归属为 Ergora；按根与 tests 的 AGENTS、当前 PLAN、脚本和检查协议、maintainable-project-delivery independent-review brief 及 ergora-codebase-quality test-seams 审查。只读源码和指定原件，唯一写入本报告；没有执行测试 body、安装、服务、提交或推送。

需求符合性：**approve，开放 finding 0**。维护性：**approve，开放 finding 0**。结论仅覆盖下述四行机械修改及相应证据，不表示新候选 Windows CI 已成功。

## 精确范围与身份

基线与隔离树 HEAD 均为 `833966d4ba21fa7bcb6670e9908d05f058cf8fdd`，实施分支 `fix/windows-schema3-fixtures`。隔离树完整 tracked diff／status 只有 `tests/test_training_cycle_controller.py`，新增4行、删除0行。四个新 mark 位于修后1463、1523、1593、1664行，均为已有同模块惯例：`skipif(sys.platform != 'linux', reason='Controller consent requires Linux/WSL2 clocks and flock')`，作用于原四函数及其原有五个参数化节点。

独立从 Git 基线和隔离树字节重新计算：基线测试 SHA256 `3db640cd63890dd8370b8a7447b2602ee253327baa94ccb2083fdec0dd4ced35`；修后 `c58f14558427fba3b4dff38e1cece97ad9f46bad177d1ee5033442607a4f8de3`；完整 diff `c390efec69da51acbc973aba25d525fa38c5a12438b99b9277e48dced7ad1305`。完整 diff 与留存 `implementation.diff` 相同。仅移除目标函数前新增的四行，逐字节恢复基线；`git diff --check` 返回0。因此 fixture、body、参数、断言、产品及 CI 没有被改动。根工作树其他在途文档不属于本次源码候选。

## 真实失败与 fixture 闭包

独立阅读原 `cycle-v3-birth/publication-r1/windows-failure/request.json`、`annotations.json`：绑定准确833966d；官方 annotations 明确五个 ERROR 与 `1214 passed / 995 skipped / 5 errors / 16 subtests passed / 877.59s`。native callback 节点报 native source preparation requires Linux，其余四节点报 native submission requires Linux。原件是 annotations，不是完整 traceback／job 日志。

源码依赖链解释了这些可达失败。四个函数均依赖 `controller_admission` → `cycle_selection` → `prepared` → `experiments` → `registration` → `installation`（以及 pytest tmp_path／request）。`controller_admission` 在 setup 调用 `training_cycles.create`；它经 `training.check_start` 到 `reference.training_submission(..., 'check', ...)`，后者对非 Linux 直接拒绝，尚未进入测试 body。original-type 的两个 program_version 都走该链。intent 用例另需 `service`，但 service 自身的平台／SDK skip 无法抢在上述 controller fixture 的 Linux 调用之前保护测试。

native callback 还对 `installation=['managed']` 做原有间接参数化：模块级 `test_training_runtime.installation` 首先调用 `reference.prepare_training`，该函数先拒绝非 Linux；body 后续才动态取得 `historical_execution` → `prepared`，并使用原 `.venv/bin/python` native reader。故只在 body 或依赖 fixture 的末端 skip 不足；函数级 pytest mark 在 fixture setup 前覆盖两条入口，且不扩大至整个模块。Linux／WSL2 的 `sys.platform == 'linux'` 保持原执行边界。

## 验证证据与维护性

已阅读 `.ergora/checks/windows-schema3-fixtures/` 的 helper、commands-before／after、summary、前后 JSON／日志和原 patch，并用只读 Python 逐项核对节点、条件、报告及字节身份。helper 先在 host 解析依赖，仅 reload 本测试模块时设 `sys.platform='win32'` 使 decorator 求值，随后恢复 Linux，再调用真实 pytest；它不是原生 Windows 运行。

修前五个独立进程各收集1个准确节点、无 skipif、fixture hook一次、预期 sentinel setup error一次、退出码1。sentinel 截断的第一项是 `tmp_path_factory`，因此这组检查证明“原先会开始 fixture setup”，不独立复现具体 native 报错；具体报错由官方 annotations 和上述源码闭包支持。修后原四目标合跑记录5 skipped／0.05秒，五个 setup 均 skipped、无 call 报告、fixture hook零次、退出码0。Linux 前后同序同名五节点，修后五项 skipif 全 false，原两参数保持；after collect 为5 tests collected／0.04秒。没有把收集通过称为 Linux body 回归通过。

首次修前合跑日志保留第一个 sentinel 与后续 pytest9 fixture finalizer 内部 AssertionError；这是 helper 在共享 fixture 异常路径的限制。后续逐节点日志均只有预期单个 sentinel／1 error，无该内部 AssertionError。交付已区分两轮，没有将 helper 异常称为产品故障。

四行直接沿用 pytest 原生边界和现有模块写法，不增加包装、重复测试文件或 CI 矩阵；保留原 Linux 测试全部断言。对本次可达风险，这是最小且易维护的修正。没有证据支持另改 fixture 或产品平台约束。

## 限制与后续

未运行原生 Windows、昂贵 Linux body／全量回归、新包安装或新候选 CI；本 reviewer 也未重跑作者 pytest，只审查实际原件及静态身份。旧833966d官方失败保留，原 plan／六 Linux success 不自动认证后继候选。交付与当前 PLAN 均将本片新 CI 留作后续。

本次精确源码切片无阻塞 finding。后续按既有授权固定并普通导入／推送候选，绑定其准确 head 的官方 run，观察 Windows 五节点跳过及适用 jobs 的实际终态；只有该证据才能关闭“恢复 Windows CI”的运行验收。
