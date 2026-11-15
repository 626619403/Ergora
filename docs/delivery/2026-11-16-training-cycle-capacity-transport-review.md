# c1d M1c-T 独立证据范围审查

2026-11-16。Reviewer：fresh-context 独立 agent `cycle_transport_capacity_evidence_review`；未接收实现对话，仅按原需求、固定身份及原证据只读核验。采用 maintainable-project-delivery 的独审 brief 与 ergora-codebase-quality 的 test-seams，已读根／tests AGENTS、PLAN、组件协议、原 wire（特别是179–214、252、261行）、容量分期及其 D1 修订。

**需求符合性：approve；可维护性：approve。开放 finding／阻断均0。** 可以将 M1c-T 的现存旧 transport 定向安装验证及本次独立审查记为通过；不能将完整 M1c 或新 wire 记为完成。本结论不开放接受／collect／native 执行或 ordinal1。

## 身份与检查

检查主树 HEAD `23ad171bf8228bf80b070d6ad866f79d63986d56`、现有 tracked／untracked 文档状态；没有产品／测试工作树差异。本片对象为固定 M1b `67ab9b4e446527fd27a61eff1aa6acb8d24feb01` 对 `bd479050ddd2d9c6b6964f89fe44cfc895273d6b` 的九文件 patch，SHA256 `a15d116c62aa3bebb123823a0290479952e2bfee5fb8aced8ede0ce35fee334c`。M1b 自身源码、安装、模板及固定提交终核沿其[原报告](2026-11-16-training-cycle-v3-birth-source-review.md)复用，不在本片重新认证。

逐件读取 ignored `cycle-capacity-transport` 的 `transport-r1-command.json`、`transport-r1-result.json`、stdout、stderr及JUnit；六函数展开为九case，exit0，stdout **9 passed／150.23秒**，driver151.248秒，JUnit9项／0失败／0error／0skip（suite time150.178秒，计时口径不同）。argv确为同一 package-r1 SDK Python 的 `-I -B -m pytest`，无 PYTHONPATH，cwd是冻结 test-inputs；wheel SHA256 `1ed714c885686d134033ac610ac0367fe275288d2ce45b8e6c4f1058dc801292`。这是复用原已核安装，不是本片新安装／新模型成功。

读取 package-r1 的 frozen-inputs、product-inputs、merge-inputs-r1；本次独立逐项重算主树848输入与663产品文件的 bytes／SHA256／执行位，均与原清单一致；117份冻结 tests 副本也逐字及执行位一致。因而下面读取的主树 assertions 对应本次安装测试的冻结输入。仅沿清单读取，没有递归审查全部 checks。

## 主张与 assertions 对照

|交付主张|实际证据与可接受范围|
|---|---|
|完整 SDK metadata 计量|`tests/test_training_runtime.py:249` 用默认 DataConverter＋完整 Payloads.ByteSize，构造 JSON 合界而protobuf过界，断言非重试容量拒绝。它不是三个精确临界字节值的验收。|
|V1 signal/query/outcome|同文件867行以默认 sandbox 的真实 Workflow activation 实例运行；485行 fixture直接注入远端活动结果。错误shape、JSON恰32768但完整Payloads过界、外来identity后，合法stop仍保留第一完整reason并返回 needs_reconciliation。没有真实Temporal server。|
|request／stdout／frame三种容量失败|`tests/test_training_submission.py:3023` 实际 ActivityEnvironment 调用原活动，检查其余五个peer停止、returncode0与原ref。request参数仅断言writer构造容量拒绝且未spawn；stdout参数保留超界原stdout、没有ref；frame参数stdout自身合界，原SHA与ref一致。fixture在真实S/H进程中替换业务结果，保留原supervisor／process runner／reaper。|
|完整分支失败reason／peer|同文件2658行两参数：小reason逐字inline返回，大reason使最终完整活动结果非重试拒绝；两者均核原stop持久、另一分支原request存在。大reason的完整unsent-value日志由原 `_cycle_capacity`（worker1179行）持有；本测试未另对日志字节作断言，也不证明完整拒绝父request留存。|
|launch机会保持占用|同文件2909行通过真实注册大项目形成容量失败，固定原intent bytes／inode；重复start、attempt2、reconcile只走reconcile，无第二prepare、attempt、budget或业务start。业务服务为既有替身。|
|N32完整旧stop|同文件2633行明确66分支集合，加inspection逐个核完整stdout长度及SHA，最终默认Payloads整体≤32768。只有原全ref case；不覆盖新v3或所有inline unknown组合。|

[交付记录](2026-11-16-training-cycle-capacity-transport.md)已明确上述限制，没有把helper函数、绿色JUnit、服务替身或M1b历史证据冒称新功能成功。测试沿既有真实接缝，不增测试／CI／抽象、容量配额或第二owner；本片文档范围和维护成本适当。

## 保留的门禁

完整 M1c 仍开放：10,000,000B完整observation编码与M−1/M/M+1、多字节／LF、合法大于1MiB、合计超M、写入／fsync／deadline／reply loss；真实ref消费者和source／ROOT接线；V2实际输入／Memo、发送／接收／query／signal／outcome的完整转换边界；N32含inline unknown等新组合；新版本失败frame封套的二次完整计量。

尤其 `_CycleOperation.__init__` 在创建operation目录前拒绝超界raw（worker79行附近），原operation-request测试没有完整被拒payload留存证据。已审分期与交付均保留该未决项；必须另行完成有界监督设计及实际接线，不能以error文案、替代UUID或完整结果日志关闭。当前没有将其作为本限定片的已完成义务。

本次只读检查原文件、源码／assertions及清单，唯一写入本文；未跑测试／replay／安装／服务／网络／模型／训练，未修改他人文档或产品，未commit／push。结论仅覆盖本片所列证据，不认证真实训练、GPU或收益。
