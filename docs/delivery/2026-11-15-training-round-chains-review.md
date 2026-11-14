# Q4.1 多轮证据索引独立审查

日期：2026-11-15。评审者：fresh-context 独立会话 `training_round_chains_audit`。先读原始要求、`AGENTS.md`、[活动计划](../plans/2026-11-15-training-round-chains.md)及实际变更，再沿调用者与私有原件核对[交付记录](2026-11-15-training-round-chains.md)。应用 `ergora-codebase-quality` 的 repository-style／module-design／test-seams 及独立维护性审查规范。本评审只写本报告和 ignored 证据；没有改实现、其他文档或业务仓库，没有安装、调用模型、启动服务或写 Git。

|审查轴|最终本地结论|范围|
|---|---|---|
|需求正确性|**approve，开放实质 finding 0**|显式人工选原实验、不可变新目录、固定前缀扩展、离线 SHA／内部链接核对。失败和 unknown 不升级；初始锚点、实际比较、候选／前驱、注释、原结果／报告索引和批准事实分开保存。|
|结构可维护性|**approve，开放实质 finding 0**|CLI 保持传输职责；新 owner 隐藏索引格式与采集组合，复用原实验、统计、归档和批准 owner，没有新增调度、数据库或批准权威。|

本地已检范围没有需要修正的可达问题。普通发布、固定发布身份与本片自己的适用 CI 仍待完成；此结论不预批这些后续事实。

## 固定审查范围

基线及当前 HEAD 均为 `eadabc0441991a02acc06e17efd8d6c16b7d9d27`，待交付内容尚未提交。已检查最初 r1 全文与最终 r2：**11 个作者文件／304,343B**，完整文件值、长度、SHA256 和 tracked diff 均与工作树逐项相同。最终 `scope.json` SHA256 为 `4466dd3efd713b03c845796fe06c79114ed5c386115543668f258ca238762614`；`tracked.diff` SHA256 为 `ebba391fbad56b140e00a8e9d542bba4f074d6de4ad40b17655798f6ef994977`。本报告不在该作者清单内。

|文件|检查内容|
|---|---|
|`src/ergora/cli.py`|两入口及分派、严格 JSON 输入、离线读不构造 State|
|`src/ergora/training_rounds.py`|原观察组合、身份／链接、容量、前缀保留与发布|
|`src/ergora/data/schemas/training-rounds-v1.json`|请求、索引、原观察字段和边界|
|`tests/test_training_evidence.py`|三项新增接缝及原 fixture／调用链|
|`docs/TRAINING.md`|实际 CLI 用法、比较语义、容量和覆盖范围|
|`docs/PLAN.md`|当前检查点及验收归属|
|`docs/plans/2026-11-15-domain-review-optimization-quality.md`|Q4.1 与其他片边界|
|`docs/plans/2026-11-15-training-round-chains.md`|本片合同及完成条件|
|`docs/delivery/2026-11-15-training-round-chains.md`|结果、原件、旧失败及未完成项|
|`docs/delivery/2026-11-15-training-bottleneck-path.md`|原 Q3.3 发布／CI 的追加记账|
|`docs/delivery/2026-11-15-training-bottleneck-path-review.md`|原 reviewer 追加终态与旧报告前缀|

r1→r2 仅六份计划／交付文档补记实际 74 项、原文本审查的历史范围和 Q3.3 终态；产品、测试和用户手册逐字保持。原 Q3.3 报告 12,288B／SHA256 `483653cf934d301f42395259a5f73c3ec9882f1a35b635e7fea79e762f0fa4f4` 的前缀保持。本评审读取其原终核记录，未用本片 640 文件或本片测试认证旧 638 产品，也不重新扩大旧审查结论。

## 所有权与合同核对

已实际跟踪 [CLI](../../src/ergora/cli.py) → [索引 owner](../../src/ergora/training_rounds.py) → [training](../../src/ergora/training.py) 的 inspect／evidence／submission／approval，再到 `reference._training_records`、`reference_training_evidence`、`reference_training_submission`、`reference_training_release` 及原读取／归档／投递路径。

原 inspect 负责原 manifest／spec／runner／request／result／gate／negative result 的准入和文件身份；原 evidence 负责 accepted archive 的原内容地址、manifest／baseline／comparator 和 artifact 索引。索引完整保留这些返回 JSON 值，没有复制统计判定器或将 `artifact_content_status=not_read` 改成已读。baseline 当前不匹配及失败结果可以保留，不能因此获得批准。

submission／approval 均调用原 status 路径；没有进入 dispatch／resume、runtime 查询或信号发送。unknown／prepared／未提交不会读取批准；已提交才读取原 run 的本地决定。`requested` 是原投递事实，coverage 始终保留 execution_success=null、authorization_status=not_evaluated 和 promotion_approved=false。初始锚点和实际比较从原 manifest 分别保存；每轮 parent SHA 表示操作者所选链的前驱，不替代 Git 祖先关系或候选采用。变化／下一瓶颈保留为注释，不参与原门禁。

格式校验及各 guard 有实际边界：外部请求／重复键、配对的旧目录与整份 SHA、同注册项目／repo、重复原实验、32 轮／10MB、项目 revision 漂移、同轮项目／binding／gate／共享文件 SHA 冲突、轮内内容／前驱及旧前缀。读取只接受单个普通 `rounds.json` 并有界读取；发布复用原 `publish_directory` 原子不覆盖语义。没有发现需要下放到 CLI、基础 State 或冻结参考的职责，也没有为将来消费者创建通用插件层。私有编码／SHA／比较／校验函数是索引 owner 的局部算法，不以测试调用冒称跨生产模块复用。

schema 对自身索引结构严格，对保留的原观察允许原扩展字段，并约束本层实际解引用的字段；原格式解释仍归原 owner。离线读取不构造 State 或调用原训练观察，不认证来源、实时状态或当前授权。多个采集观察不等于原子实时快照。首版同初始 baseline／workload 的限制和后续 baseline 迁移／自动循环的边界，代码、schema 与手册一致。

## 直接验证与测试价值

- 独立从固定 Git 对象重算 638 基线文件，再核 **640 源码＝wheel＝非 editable 安装＝记录清单**。仅 `cli.py` 改变，新增 module／schema 两文件；283 参考逐字保持。r1 wheel SHA256 为 `368f534a0497a12d00c89ad5f2e835343ed4e773c88048ab457a2b6f381bb558`。没有算法、模型、数据、质量门禁、state schema 或原 kernel 提案路径变化。
- 直接核原 CPU executor 的两份结果及 poll：不同候选、同原 baseline，刻意 exit7／exit9 均为 FAILED。18 条原命令的 stdout／stderr SHA 全部核同；旧轮完整值保持，重启读响应逐字相同，错 SHA 和已有目标明确拒绝。**121 份**原 config／runtime 的 before／after／当前字节一致。
- 直接读原 C3 三份提交 receipt、保存索引及其原文件，run ID 与对应原 receipt 一致。beta 的 accepted archive 仍是旧合成材料，原 approval 为 **requested**；alpha／gamma 为 **not_recorded**。五个保存轮共 50 个原文件索引引用的 SHA 及原 JSON 字段均核同；原 C3 **96 份** control／config／runtime 的 before／after／当前字节一致。没有把旧 C3 视为本片新执行或新批准。
- 直接解析作者安装 JUnit：原四 suite **60 passed／23.900s**，后续扩大 submission／lost-ack 为 **74 passed／128.821s**，均零失败／错误／跳过。交付摘要的 128.84 秒与 JUnit 原计时字段分开保留；没有以早期 pending 记录冒称当时已完成。
- 独立使用原 venv 的实际 site-packages 运行现有三项 round 接缝，**3 passed／12.10s**。它们分别覆盖失败／pending 与离线 CLI、旧 accepted 前缀及后继失败／baseline drift、丢 start 回复后保留 unknown 且不 RPC／批准；沿用原 fixture 和服务替身，没有新增模型测试、独立 CI job 或镜像实现的断言矩阵。未重跑无变化的全量回归。
- 自身原结构模板的原结果为 approve／exit0／29.538761 秒；独立重核 **16 完整文件／326,102B** 均在原 task 与实际 stdin，三个祖先 resource 完整，sealed input 与 stdin 对应，原 result SHA 为 `08ca4204535b0be2a766f0a9c6f12847867696b152eaa3f7334fa6752e6eb852`。该调用只审冻结文本，其扩大测试仍 pending 的语句保留历史身份；不把它当安装、原件或 CI 证明。

原 install-r1 的 externally-managed 拒绝和 approved-observation-r1 的错误 approved 预期均仍在原件；后者实际保存的是 requested。修的是私有 driver，没有产品重建或删除失败。仓库没有为本片配置新的 formatter／linter；沿原 pytest／架构边界和包身份合同检查，未施加外部项目风格。

沿原链接检查器独立复核含本报告的 **8 份 Markdown／194 个本地链接及 fragment，零错误**；外网未验证。全范围 `git diff --check` 通过。作者较早七份文档／189 条的记录保留其当时身份。

独立证据在本片 ignored `reviewer-r1/`：`identity-audit-r1.json`、`native-links-audit-r1.json`、`self-review-audit-r1.json`、`final-scope-audit-r2.json` 及 `installed-round-tests-r1.xml`。完整作者 r1／r2 冻结清单与原件保留在原目录；公开产品不依赖这些机器路径。

## 限制与后续验收

本次没有运行真实训练、GPU、profiler、数值／梯度／分布式或长期质量／收益验证；CPU 刻意失败和旧合成 archive 只证明相应控制与持久合同。没有验证自动优化、跨 baseline 迁移、累计收益、自动采用、跨轮预算或完整 Forge；这些仍按原条件另片。kernel 专家在原 v3 提案路径保持，允许无需 kernel 修改。

剩余验收是本片普通提交／推送后的精确发布核对，以及该完整候选自己的适用 CI 终态。前片 CI 成功不认证本片。当前本地两轴 approve／开放 0／0，不代表远端或未来运行已经完成。

## 固定普通发布补核（2026-11-15）

同一独立评审者已直接核对普通发布 `750dd68ff2b1e41f6fe390d6a52e651bf41d5642`，唯一父为原基线 `eadabc0441991a02acc06e17efd8d6c16b7d9d27`，tree 为 `ffd7e16a8c0861c1043c182e214a68c2e741b938`。本节覆盖上文待普通发布／远端身份状态：**固定发布需求符合性 approve／可维护性 approve，新增实质 finding 0／0；本片自己的 CI 仍 pending，不认证成功。**

从固定 Git 对象得到的变化集合恰为 **12 个文件**，逐项 blob ID、字节数和 SHA256 全部匹配原 `staged-r1.json` 与 `publication-r1.json`，没有额外或缺失文件。相对已审 scope-r2，产品、schema、测试和用户手册逐字相同；仅四份计划／交付文档补记实际本地独立通过，并加入本报告原 **9,708B／SHA256 `8a0eb09b4e676bb1c92200a748cd32f3b81d82b3277b3e3e1b32994edd96bf62`** 的版本。追加前该报告及本节前缀一致，原本地审查结论和证据没有改写。

|发布原件|独立重算 SHA256|
|---|---|
|`staged-r1.json`|`578738175adcb0cae5e22e826d330551e504ef1f0c28a09a2ff74cb547d377f7`|
|`publication-r1.json`|`7397035646388d6cbb6e90aa6151b61832fdf9a7006920d930b5d008fbfb33fc`|
|`remote-r1.txt`|`4820653449bf449253d3ae51c81dba9778fb7f061b5a538016a9b9e349d46425`|

独立执行只读 `git ls-remote --refs origin refs/heads/refactor/architecture-foundations`，实时 Ref 与保存原件均为上述完整发布 SHA。固定提交的 **640 产品 Git blob＝原记录清单＝r1 wheel＝原非 editable 安装**；wheel SHA256 仍为 `368f534a0497a12d00c89ad5f2e835343ed4e773c88048ab457a2b6f381bb558`，**283 参考**与原基线逐字相同。这里从固定 Git 对象读取产品，没有使用后继工作树认证本片。

同样只读固定 Git 对象，复核发布的 **8 份 Markdown／195 个本地链接及 fragment，零错误**；新增的一条是交付记录中的本报告入口，上文 194 条保留原检查身份。基线→固定发布的 `git diff --check` 通过。私有补核原件为本片 `reviewer-r1/publication-r1.json`、`publication-live-remote-r1.txt`、`publication-docs-r1.json` 与原报告前缀快照。

本次没有重跑测试／模型／训练、安装或平台写入，没有提交或推送。原三接缝、两条原合同旅程及文本审查继续保留原身份；此补核没有扩大为训练质量、性能、自动循环或采用。剩余项为该完整候选自己的适用 CI 终态及同片补核，不以任何前片或后继结果替代。
