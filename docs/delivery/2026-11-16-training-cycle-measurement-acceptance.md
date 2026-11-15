# c1d M2a＋M3a：内部测量接受与轮次发布

2026-11-16。状态：具体[计划](../plans/2026-11-16-training-cycle-measurement-acceptance.md)及R1修订已由[fresh独立设计审查](2026-11-16-training-cycle-measurement-acceptance-design-review.md)接纳，需求与维护性两轴approve、开放0。根任务接纳B分片：现有operation-v2内部collect／reconcile用例，M2四事实和M3索引／完整观察由同片闭合实际consumer；M5仅必要只读binding格式提前，SDK v3注册／正式V2及执行开放不提前。

已审计划SHA256 `2ecfa840f5c52b53cf9dbd3782a9a7b330b5421b19623eac9c70484ac3fa0bff`，独立设计报告SHA256 `6feca847785ed8bc7a7ceb496d8be52b5c3282d60cb842c0ad02e63caa94eb48`。原首审R1 request-changes保留：reader完整返回在prefix前失败可能丢失；修订要求实际H逐份写／flush原 `helper/stderr.txt`，不把reason／原chain说成完整RPC detail，不增加文件／ledger／授权，也不冒称flush durable。

实施基线 `23ad171bf8228bf80b070d6ad866f79d63986d56` 已含M1a与已验M1b固定产品，新的持久隔离分支为 `feat/training-cycle-measurement`。实现、源码检查、真实S/H与服务替身、安装、自身原模板、fresh源码审查、固定提交／发布分别待验；设计批准不代记实现通过。旧schema1／2、operation-v1与c1c命令、25来源、原ready／预算／stop／一次机会、六阶段保持。

超界父请求exact raw有界留存的[另案设计](../plans/2026-11-16-training-cycle-parent-request-retention.md)仍在审，不在未接纳时偷偷实现。全M1c、M5最后native／前驱gate、M6正式V2／v3及实际两轮仍开放，schema3执行拒绝和ordinal1门不解除；此片不认证训练／GPU质量或收益。
