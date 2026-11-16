# a1／M6-V1 联合安装与发布验收

2026-11-16。准确源码合并提交 `f9b9d72d6d5f2102809a3cafaadb2226bba0966b`，基线 `0a5a0ffb32cd2a247eaef49a008cb5692ffad47a`。本片合并既有已审产品，不增加新的产品行为；源码／联合安装／发布与自己的CI分别记账。

## 依赖与保持的边界

- [a1只读设计材料](2026-11-16-design-packet-inspection.md)：`cb861ea7138627d6646e8de1c0867a3ed92ce474`，经 `3d632a7` 普通导入；需求／维护性独立approve／0。真实原生读取不需jsonschema，应用在两个公开入口统一validate；inspection-only，无批准／执行能力。
- [M6-V1表达片](2026-11-16-training-cycle-v2-expression.md)：`2acdcc44eb86659f3ab9d22d2f83bb0973388406`，普通导入本联合f9b9d72；独立两轴approve／0。新V2/v3完整表达，生产服务仍默认V1，所有schema3实际效果保持关闭，不认证M1c／四poller／真实两轮。

六个a1、五个M6源码／测试完整文件与各自固定产品同一，改动没有重叠产品文件。私有`merged-source-inputs.json`完整比较其中10文件，并另保存`test_training_submission.py`实际diff为空，合计11文件同一。保留原283参考、原锁、source25＋四measurement及原version缺省。

## 新联合安装与检查

新wheel SHA256 `ea1927be9ad5a51fdf28142af9a0e713beb5994aeb53c3efd32e647d88b53d71`，core／SDK各668完整产品与源、wheel的字节／执行位同一，三训练owner实际来自site-packages；283参考与依赖通过，core无SDK／SDK1.34.0。862构建／检查输入固定，原测试／示例179项另复制；root状态文档可更新，但源／测试／配置不允许在检查期间漂移。原件在私有`.ergora/checks/design-training-expression-integration/`。

新安装a1原57与V2/V3原25联合 **82 passed／39.06秒**，新安装原真实S/H定向 **8 passed／90.66秒**。两组完整argv/JUnit/raw及82项的实际ID均保存；前后产品／862输入／179副本保持，不使用单片通过代替。core直接导入训练owner、reference与纯task_design且无SDK、V2工厂明确缺optional；新安装同一Windows纯路径probe exit0，native路径接受、旧literal拒绝。这些是本地原生进程／受控SDK／模拟纯路径接缝，非真实服务、Windows主机或业务训练。

原 `scripts/ci/run.py --collect-only` 安装入口 **exit0／9.241秒**，实际2386节点。对上次准确2335原collector先作raw比较，52新增／1旧ID未同名；实际原因是原保留请求测试增加mode参数，旧ID映射到同一collect-round原分支。原diff和精确映射分别保留，映射后无删除、净新增51（plan23、runtime25、submission3），原六组／时限／保护未改。收集不是测试执行或Windows CI通过。

五条实际检查命令捕获269份自有进程身份记录，按PID／BOOT／start检查均absent，只证明捕获的命令后代，不称全系统零残留。最终源产品／构建输入／模式保持，清单SHA256 `7177f292c9d4377a8c616e4123dc88546d1ead487f7b708def67e53ca8388054`。原件为`final-freeze-resource-check.json`、两种collector比较和各命令记录，没有重跑无变化全suite／模型／业务训练。

## 独立集成终核与发布范围

[新的 fresh-context 集成评审](2026-11-16-design-training-expression-integration-review.md)需求符合性、结构／维护性两轴 **approve，开放 finding 0**，报告 SHA256 `afb0556c89bdcffa48650e6e4e4b557fd8644edf8cb52ca2f05cd170f4acaef6`。独立重核真实 native／应用调用、懒加载、25＋4 source pins、V1 缺省和所有 schema3 效果关闭；重算668项包、862项输入、179项副本、原283／127、collector映射及269份捕获身份，未要求源码修正。没有重跑已有测试或递归审查状态记账。

后继 [S1 拆片](../plans/2026-11-16-design-gates-registration-and-journal.md)已审原字节 SHA256 `a94b4a5a95a674330e09e84b0c7596635bc985521c3f8d221ed996dbb07965ae` 完整另存；公开链接仅将16个 `.py:行号` 改为 GitHub 支持的 `.py#L行号`，当前字节 SHA256 `bde47bee749ff973901beeebc6f148316b3ea2d2635e191ac5804942e142f984`。正文中的“待复核”保留该修订当时的状态，最终设计结论以[已完成的独立设计审](2026-11-16-design-gates-registration-and-journal-design-review.md)为准；没有调整已审政策或验收内容。链接变更原件及映射为私有 `approved-plan-r2-original.md`、`plan-link-formatting.json`。

## 公开候选与 CI

源码 f9b9d72 及上述已完成文档以 `eba86805e5d50824eefb5e69edd0faab099cbf42` 普通推送 `refactor/architecture-foundations`；`git ls-remote` 读得精确相同完整 OID。没有强推或合入 main。公开候选相对于已验源码仅改计划／交付文档，产品包身份保持。

05:05:11Z 官方 REST 发现返回 HTTP403，未认证额度 remaining=0、reset 为05:25:25Z；完整响应留存，不把它算作测试失败或 CI 成功。05:05:59Z 官方公开 Actions 列表的完整 commit 链接精确匹配 eba8680，发现本分支 push [43807888266](https://github.com/626619403/Ergora/actions/runs/43807888266)，创建05:04:37Z、状态 in_progress。HTML 原件 SHA256 `61ce683b666ef752f4033ffc90c901c1091dd728e762d1f02f526cff69c60d29`，只据其发现 run，不冒充 REST attempt／jobs 终态。原件在本片 `publication-r1/`，后续待原额度恢复再观察准确候选自己的最终八 job，不能借0a5a0ff八job成功替代。

后续 S1 和 M6-V2a 源码只在各自隔离 worktree，不在本包内。

05:26:53Z 官方 REST 已读得准确 `eba8680` 的 attempt1 最终 completed／failure，8 jobs 中7成功（含 Windows），Ubuntu group2 失败。完整 run／jobs 原响应和汇总保存在 `publication-r1/20261116T052653Z-*` 与 `current-summary.json`；05:31:26Z 原 annotations 指出唯一失败为 `test_schema3_intent_is_local_and_all_execution_entries_remain_closed`：期待 schema3 执行关闭，实际先被完整授权的 operation 版本校验拒绝。其 cold fixture 没有 snapshot／activity_context，仍按旧缺省构造 operation-v1，而真实 schema3 要求 operation-v2。生产拒绝仍生效，不能把该 CI 记为通过；后续在原 fixture 验证版本与关闭动作的最小修正，原失败保留。其他候选的绿色不替代本次失败。
