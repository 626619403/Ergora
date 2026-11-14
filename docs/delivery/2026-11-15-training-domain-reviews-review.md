# Q2.1／Q2.2 独立审查

日期：2026-11-15。审查者：fresh-context Codex agent `training_domain_reviews_audit`。先读原始要求与实际差异，再读实施叙述；遵循仓库 AGENTS、maintainable-project-delivery 的 independent-review brief，以及 ergora-codebase-quality 的 style／module／test-seam references。源码只读，仅写本报告。

|审查轴|结论|
|---|---|
|需求符合性|**approve：本地实现与所供验收证据符合 Q2.1／Q2.2 范围。** 精确发布与本片自己的 CI 尚未验收。|
|可维护性|**approve。** 未发现实质源码／合同／测试价值问题；一项交付记录矛盾已修并复核关闭。|

## 精确范围

固定基线 `a38dd21891ac200c575e8520c49cc82f97c9d478`，分支 `refactor/architecture-foundations`。完整 tracked／untracked 24 文件取自私有证据目录 `.ergora/checks/training-domain-reviews/review-scope-r1/` 的 `scope.json`、`tracked.diff` 和 `files/`；逐项核过快照字节数及 SHA256。原 tracked diff SHA256 为 `52c9f1aed1ab06f3f3c10c1b61f9fb04160498e0e3028c7b044d92b23d9c53e8`。

范围包括两位领域 Agent 的六个文件、四份 workflow 的八个文件、原 preset catalog、`tests/test_presets.py`、CPU 样例及七份 README／文档。另沿 `workflow_definitions`、`definition_bundles`、`review_dags`、`task_envelopes`、`reference_inputs`、`reference_executor`、原通用三路定义与现有测试检查真实安装、冻结、输入及正式准入路径。快照后仅三份状态文档更新，已读其增量；产品、测试、样例保持快照身份。随后新增的 `training-flow-maps` 两份准备文档不属于本次 Q2 范围。

## 需求与所有权核对

- 两个 reviewer 各有独立版本、专长与完整自包含 Skill；后端仍由原绑定选择。预训练与后训练指导分别覆盖各自数学、数据、状态、恢复边界，并要求按实际算法／配置判断。固定 Bridge／slime 来源及适用限制随 Skill 发行；未引入 BBuf 正文、训练器或新依赖。
- 两个根均嵌套原 `ergora-delivery-review` 与领域叶，四个 reviewer 都是 required，终端为覆盖全体的显式 all-join。原 28 项 catalog 内容及 192 个历史 preset 文件逐字保持；安装、资源祖先、权限上限、调度及批准继续由原 owner 承担。
- 安装重试、冻结后移走活动库、完整结构祖先资源、只读 grant 及正式提交准入有现有接缝上的行为保护。新增测试不锁提示词措辞；样例的 Git／算术／采集流程集中在一个用途清楚的示例脚本，没有增加平行执行器或推测性接口。
- 使用手册命令与实际 CLI／API 合同一致，并明确独立 `run-input` 只调用所选叶。静态根和正式准入通过没有被写成四路实际运行或平台批准；Q2.3 统一运行／报告仍开放。

## 核过的证据与检查

私有原件均在仓库的 `.ergora/checks/training-domain-reviews/`，不随发行：

|证据|实际核对结果|
|---|---|
|`installed-r1.stdout/xml`|原安装 suite 61 passed／76.43 秒，零失败／跳过；读取原输出及 XML，未重跑整套。|
|`definition-console-r2.stdout/xml`|原页面 suite 21 passed／24.92 秒。r1 缺可选 Web 依赖的 skip／exit 5 保留，未算通过。|
|`package-r2.json` 与两份 wheel|独立重算 r2 wheel SHA256 `3d7c5e71d4b7b17ece885ce7bf72321d336d351411d4142c9504e433a9b03e60`；628 产品文件的源码、r1 wheel、r2 wheel、非 editable 安装逐字相同。安装解释器来自不继承 system-site-packages 的 venv。|
|四份完整 CPU packet 与 `domain-journey-r1/` 原件|用已安装 reader 核包；验证 task 与完整读取一致，所有声明父／叶资源在 stdin，prompt＝stdin，input／prompt／result 摘要及原 response 一致；两个冻结根各能构造四成员 ReviewDAG。|
|`self-review-r1-codex/` 原件|原结构模板 run `abecaacd1ac440588153f69506683085`，24.281 秒、approve；独立核 29 份完整文件／365,465B、三份父／叶资源、实际 task／prompt／stdin 及结果身份。该模型 verdict 仅为所供源码文本审查。|

独立以精确提交的源码／配置和 `Fraction` 算术复核：预训练 baseline／有效重分组为 `15/2`，回归为 `16/3`；后训练 baseline／有效 masked 变体为 `3`，回归为 `103/2`。四次原 Codex 叶分别对两回归 request-changes、两有效变体 approve，回应准确保留未执行检查及 all-join 未运行的边界。检查原件已公开期望值，此例证明具体合同和资料交付，不是盲测或总体检出率。

本审查还用同一安装解释器运行：

```bash
python -B -I -m pytest -q -p no:cacheprovider tests/test_presets.py \
  -k '(domain_reviews_keep_general_identities_and_frozen_ancestor_material or bundled_review_can_be_selected_without_its_delivery_parent) and (pretraining or posttraining)'
python -B -I -m ergora reference verify
```

结果为 **4 passed／33 deselected／10.27 秒**；参考 **PASS／283 文件**，`runtime_started: false`。原 source-only 环境失败与安装替换窗口中的早期检查失败保持原记录，不追认为通过。

## Finding 与剩余验收

**C1，低，已关闭：** 交付记录原第 9／12／20／35 行仍把已完成的样例、四次调用和自身模板描述为当前待办，与同页成功原件相矛盾。最小修正是更新当前状态／下一步，或明确标为历史。实施者已更新这些语句并说明 Q1 CI 的历史时点；本审查重新读取确认一致，无产品变化。开放实质 finding **0**，开放记录 finding **0**。

本报告通过本地 Q2 实现审查，不认证尚未发生的提交／远端 Ref／本片 CI。Q1 修正及其 CI 保持独立身份。未运行新的训练、GPU、多卡、长程质量／性能、Claude 或整根四路端到端旅程；这些不由四个 CPU 叶结果替代。Q2.3、后续 kernel 专家评估、真实 B3／完整 Forge 等原开放范围保持。
