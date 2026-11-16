# 测量检查前的 Linux CI 有限再平衡

日期：2026-11-16。实施基线 `610f111f0755edcfd8b4c582a7644ff79621c8ce`，隔离分支 `fix/measurement-ci-balance`。依据[有限预算调查](2026-11-16-measurement-ci-budget-analysis.md)，仅在原 `scripts/ci/linux-groups.json` 将完整 `tests/test_training_cancellation.py`、`tests/test_work_agents.py` 从 group5 移至 group3。配置保留六组、86个唯一文件；文件数从13／14／12／16／13／18变为13／14／12／18／13／16。没有修改测试、产品、runner、plugin、workflow、job数量或时限。共享 PLAN 未改；尚未提交、合并或推送。

冻结配置 diff SHA256：`b751bf77b0bb07de3b5bb3b1e17cf769a1ee7c34a2642a16309fc4fe6fd73b24`。旧 JSON SHA256 `186e719860ad0cde5ce01d88bfbe1013320395d860acb5434954b1f9b3360c92`，新 JSON SHA256 `9923dbdb2ab8282e9840a98f1b22828189d441e8ea7758b9b188f8e9ecdf4608`。

## 实际检查

复用既有非editable完整SDK环境的Python3.12；实际 `ergora` 导入来自该环境的 `site-packages`。未安装依赖、执行测试正文、启动服务或训练。调用现有 `scripts/ci/run.py --group all --collect-only --output …` 两次；runner依原合同将 PYTHONPATH 限为现有CI脚本及reference目录。完整实际argv、cwd、输入摘要、结果及原phase日志均保存在根 ignored `.ergora/checks/measurement-ci-balance/`，包括 `manifest.json`、`before-linux-groups.json`、`config.patch`、`before-all/`、`after-all/`、`validation-request.json`、`verify.py`、`comparison-result.json`。

|检查|实际结果|
|---|---|
|原配置 all collect-only|exit0；2269节点；11.032秒|
|新配置 all collect-only|exit0；2269节点；2.975秒|
|前后完整节点多重集|完全相同；各2269唯一节点，无新增、遗漏或重复|
|原／新配置 group3|415 → 453节点|
|原／新配置 group5|496 → 458节点|
|唯一归属变更|cancellation全13节点、work_agents全25节点，均5→3|
|配置覆盖及完整性|六组、86唯一存在文件；全部收集文件有归属；原插件拒绝条件未触发|
|机械差异|`git diff --check`通过；隔离树仅一个JSON变更|

组3／5选择检查消费真实all collector的完整覆盖，向未修改的 `pytest_phases.PhaseLog.pytest_collection_modifyitems` 传递每个节点的 `nodeid`／`path` 适配对象，对原／新配置各回放两组，保留四份原插件phase日志和配置副本；逐项核其精确选集与仅38节点整文件搬组。此为现有分组选择接缝检查，不是四次pytest组执行，也没有重复六遍完整收集。before／after all日志确认没有setup／call／teardown事件。原runner／plugin不变：Windows all不传 `--ci-group`，插件在读取Linux配置前返回，故该配置不改变Windows all选择；本次未执行Windows。

## 剩余门禁与 CI 边界

本片待新的fresh-context reviewer独立核需求／维护性两轴，不能将预算调查视为审查通过。上述公共源码基线没有活动M2新增测量case；最终M2候选的节点／组合仍须另核，既有r2环境只作为收集依赖，不认证后续r3实现或安装验收。

本次没有本机新组合测试正文及成本结果，也没有发起或观察本配置候选自己的远端CI。原六Linux各20分钟、Windows all及原时限保留；搬组只分散已有串行工作，不保证远端留足测量余量。后续准确候选须以自己的head／event／attempt及原phase／JUnit核六Linux与Windows结果，不能移记历史成功。本记录不宣称新CI或最终测量验收通过。

## 独立审查与固定导入

[fresh独立审查](2026-11-16-measurement-ci-balance-review.md)分别判需求／维护性approve、开放0，核原JSON差异、2269真实收集节点、原selector回放、fixture闭包及原runner／plugin／workflow保持；结论仅限分组映射。

隔离固定提交`16e28bd27730581454c0561e5f49a2c5d11c4c15`已普通cherry-pick至开发分支`a01570a5ad2fb46d36e1578f2687e9d4e71c70bb`，仅原JSON4行增／4行删；未推送，等最终测量片联合核收集和发布。不借基线collector／旧JUnit认证最终测量节点、Windows body或远端时限。

M2固定产品68ba793普通导入c6cfafb后，新联合实际collector2295＝原2269＋新measurement26，无旧节点删除；纯mapping选择回放原38节点仍恰两文件5→3，组3=453／组5=484。原JSON与runner／plugin不变，Windows四mark单独沿已审交付。新收集原件在cycle-measurement-collect/final-union-r2，首次协调命令venv路径错误的r1失败另保留；未运行全组body，不把原2269或这次collector当新联合CI成功。
