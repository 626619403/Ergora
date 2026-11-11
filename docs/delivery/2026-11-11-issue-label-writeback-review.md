# F7c-C2a 独立源码与结构审查

日期：2026-11-11。评审者：`/root/f7c_label_writeback_review`，新鲜上下文；未继承实现会话，先读原要求、切片规格与实际差异，再读作者证据。依据仓库 `AGENTS.md`、AIHERO 索引、`maintainable-project-delivery` 的 independent-review brief 和 `codebase-design` 分开评估 Spec、Standards。本轮只写本文，未修改产品、测试或计划，未运行模型、测试套件、HTTP、安装或网络操作，未提交／推送。

## 精确范围

基线：`b5ee397e6571f95393b0f8d6e9ee7e6d947b0935`，分支 `refactor/architecture-foundations`。审查对象为忽略检查目录中的 `f7-label-writeback/review-code-r1/manifest.json`，SHA256：`531399071486c8fad56109f84badc2e7038522f08a3ca22eea1a1e0164a0f814`。逐一重算其 11 份 `files/` 原件，全部符合 manifest；初核时当前工作树的对应文件也全部相同。tracked diff 与新文件分别读取，未把 diff 当成包含新文件的完整候选。

|候选文件|本轮审查内容|
|---|---|
|[cli.py](../../src/ergora/cli.py)|标签准备与原 status／send／observe 的入口|
|[components.json](../../src/ergora/data/components.json)|GitHub 实际 operation 登记与 GitLab 未登记标签支持|
|[issue_backends.py](../../src/ergora/issue_backends.py)|传输、原生 ID 选择、GraphQL 请求／响应和 unsupported 合同|
|[issue_writebacks.py](../../src/ergora/issue_writebacks.py)|两个 action、共享持久生命周期、原 C1 codec 与恢复|
|[web.py](../../src/ergora/web.py)|DTO、受保护 HTTP 和共用用例|
|[test_issue_writebacks.py](../../tests/test_issue_writebacks.py)|原评论回归、抽取的夹具与原 v7 export→新 CLI 衔接|
|[test_issue_label_writebacks.py](../../tests/test_issue_label_writebacks.py)|标签协议、并发、未知恢复、入口、兼容反例|
|[issue-comment-v1.json](../../tests/fixtures/issue-comment-v1.json)|封存 C1 格式的合成 codec 记录及其明确限制|
|[切片计划](../plans/2026-11-11-issue-label-writeback.md)|C2a／C2b 范围和验收合同|
|[切片交付记录](2026-11-11-issue-label-writeback.md)|当前源码实现记录及尚待补齐的交付证据|
|[定向研究](../research/2026-11-11-issue-label-writeback.md)|原生合同、SDK 取舍及 REST 历史建议与 ID 后补的区别|

另外只读核查了 `docs/PLAN.md`、总计划相关约束，以及 `tasks`、`reference_task_export`、`issue_sources`、`issue_snapshots`、`State`、`backups`、`projects`、`task_envelopes.identity` 的真实相邻调用路径。工作树中其他 C1 终核／状态材料不属于本次 11 文件判定。

## Spec 判定

**本精确源码／规格候选通过；开放产品 finding 0。完整 C2a 交付尚未终核。** 未发现能由当前入口打开第二次标签 mutation，或用当前 membership 补造原 attempt receipt 的可达路径。

- `issue_writebacks.py:251–269` 仍通过原 `tasks.creation / show / export_status` 读取 published v7 task、来源 snapshot 和原 creation／run／candidate／export；`send:369–380` 再核绑定、这些原事实、actor 与 operand。`configuration_sha256` 是准备事实，没有用它阻断无关 Agent 配置的新修订；操作者仍须传当前 expected revision。
- `_scope:170–173` 不含标签名、准备时间或 snapshot 摘要；`_prepare:293–315` 的唯一 scope 及 operand 比较冻结首次准备的一个标签。已有 attempt 的 `send:362–364` 直接返回原记录；再次准备、换名称或换绑定配置不能获得同一来源／creation／run／export 候选的新槽。
- `GitHubBackend.label_selection:275–297` 读取原 issue、repository 和已存在 label，核 native issue ID、名称／namespace／受控 URL，并冻结服务返回的不透明 GraphQL ID。`label_operation:299–303` 只追加一个原 label ID，完整请求随 intent 返回；没有标签创建／替换／移除或按写失败后的名称重新定位。GitLab 继承 `IssueBackend:200–212` 的显式 unsupported，原评论实现保留。
- `send:382–409` 在短事务中核当前 revision、保存唯一 attempt并提交，随后才作一次写；结果事务重核 revision 和原 attempt。网络请求不持有共享 SQLite 写事务。错误、进程退出或结果保存失败保留已提交 attempt，不能重发。
- `_request:69–95` 复用原无 redirect／无自动重试／1 MiB 完整响应门槛；评论继续预期 201，GraphQL 具体操作声明 200。`_graphql:305–314`、`_label_page:316–337` 和 `_CandidateLabel.match:140–149` 联合要求完整原响应、无 GraphQL errors、非空有效 payload、原 echo／Issue／repo、有限页内原 label ID 和精确名称。目标页未见、nullable、partial、错误目标或 echo 均不能产生 result。目标已在原响应内时不要求读取其他页。
- `observe:412–430` 和 `observe_label:349–359` 只 query 原 Issue 的当前一页，cursor 作为不透明变量传递。命中、空页、未见目标或人工移除均不改 result，`proves_original_attempt` 始终为 false。`clientMutationId` 只核回显，代码未将它当作幂等键或可查询的操作记录。
- C1 的 `_TEXT / _SHA / _POSITIVE / _INTENT` 声明及 `_scope / _body / _matched_response / _candidate / _source / _revision / _target / _load / status / _save_observation / validate_storage` 均与基线作 AST 比较，未变。评论 action 保持原 attempt 字段、正文和匹配规则；result 保存格式未变。State／旧 snapshot 所有者没有本片差异，backup 继续调用同一 `_load` 校验。合成旧 fixture 只证明 codec 范围，没有把它称为原 snapshot／task 集成。

没有把 REST 预检或 `/user` 成功当作写权限证明，也没有把 label membership 当作“本次首次新增”。GHES 检查只确认从 `/api/v3` 推导 `/api/graphql`，不证明跨版本部署；真实平台权限、通知／自动化和服务端并发行为仍为未验范围。

## Standards 判定

**本精确源码／规格候选通过；开放结构／维护性 finding 0。** 未发现须为可证实问题删除的新抽象、重复 guard 或测试。

|Module／新增 Interface|实际调用与保留理由|
|---|---|
|`prepare_label`|`cli.py:638`、`web.py:460` 两个生产文件调用；与原评论入口一起进入 `_prepare`，没有入口复制持久状态机。|
|`_WritebackAction`、两种 adapter 与 `_ACTIONS`|comment 和 label 是实际差异；validate／select／attempt／write／match／observe 的区别留在各 action。`_record`、prepare、send、observe 通过同一 Interface，registry 在本域，未增加远程副作用框架。|
|backend 的 label Interface|生产消费者在 `issue_writebacks.py`；GitHub 拥有协议、endpoint 与映射，GitLab 在相同 Interface 上明确 unsupported。上层没有按 provider、具体类型或 capability 另开执行路径。方法的必要性来自本族所有权，并未以测试或多个同文件调用冒充跨文件生产复用。|
|`_graphql_url / _graphql / _label_page`|GitHub 内部的私有算法，集中实际 add／observe 的 endpoint、传输映射及页合同；拆回调用者会重复这些知识。无需另立公共 Module 或通用 GraphQL client。|
|测试 helpers 与旧 fixture|`configure_labels` 同时供标签文件和原 v7 export 衔接使用；这是测试复用。旧 fixture 检查发布 codec，故障测试检验持久 attempt 与原响应因果关系，均有独立的静默错误风险。|

输入格式检查归 backend，持久 intent／attempt／result 完整性归 `_record / _load`，冻结 operand 对比归 send。页字段在 runtime 映射和离线 result 读取中都检查，分别保护外部输入与保存记录，存在实际不同的读取路径。两处 prepare operand 检查分别覆盖已存在记录和并发准备的 unique-scope 冲突，不能据表面相似删掉其中一处。

现有 `IssueBackend._request`、`tasks`、State 和 backup 已得到复用。研究具体说明 PyGithub 2.10.0 高层标签方法会转名称且丢弃原结果，python-gitlab 8.6.0 也不补齐本片 ID／receipt／重试合同；没有证据表明换用这些高层方法能满足本片约束。本轮没有新增 SDK、依赖或另一份正式账本／调度器，也未发现应以现成库替换的重复实现。

## 已核证据与限制

以下是读取作者原件并核其身份，不是评审者重新运行：

|证据|原件结果与本轮核查|
|---|---|
|`source-r1/result.json / inputs.json / pytest.stdout / pytest.stderr`|显式 PYTHONPATH 使用本候选源码；67 passed／155.35 秒，driver 158.94 秒，exit 0；8 项源码／测试输入 hash 与 manifest 匹配，stdout SHA256 `e7fee68c542c322d9a70fd37f64d3de06281acd06c32d019d356656c60184e8d` 重算一致，stderr 空。|
|`r1/installed-validation.json / installed-tests.stdout / installed-tests.stderr`|六个 affected suites，117 passed、1 skipped／95.80 秒，driver 97.99 秒，exit 0；stdout SHA256 `edb7b4438faf9e435b3744e83b88142797121205c26fbce8090099fbfbc0b92c` 重算一致，stderr 空。该输出没有单独列 skip 原因，不将 skip 计作通过。|
|`r1/reference-verify.stdout` 与同 validation 记录|exit 0，PASS／283，`runtime_started:false`；stdout SHA256 `290fccab50430e86df60d77e79b493eb8758894418558353e598478613799456` 重算一致。|
|`r1/package-identity.json` 与现存 wheel|记录非 editable、446 包文件、451 wheel 文件／456 installed RECORD 行、两 RECORD／283 身份。wheel SHA256 `981028c61542244bd7795ac6b3c1c8eb7620fdcbbae4b663d47d6d7f487c00a2` 已独立重算；wheel 内五个 affected 产品文件与本次归档逐字相等。本轮未独立重算完整两 RECORD 或全体 installed 文件，不能把作者的完整包核验改称本轮独立安装验收。|

原 v7 集成测试实际走原任务发布／start／Git export／claim 释放和 fresh CLI 评论、标签；Temporal SDK／结果受控，未运行六阶段真实模型推理。其他候选故障夹具控制 task ports，使用真实 State 与 loopback HTTP；本轮只审读这些测试和作者结果，没有自己发送 HTTP。静态结构检查没有产生性能实测结论。

## 本片后续终核

本轮没有阻断产品 finding。源码／规格判定不提前关闭 C2a：还需作者补齐实际自身审查模板原件、完整公开说明及当前计划／交付状态，冻结最终全部文件，再交同片独立终核。最终精确 Git／remote 与本提交自己的必要 CI 仍需对应原件；C1 的 CI 或历史模型判词不能替代。GitLab C2b 仍须另核完整返回 schema、部署／授权及 scoped rename 约束，不借本次 GitHub 通过关闭。

## 同片续核：实际自身模板原件

本节是后续只读原件核验，补齐上文首轮尚待的模型证据；评审者没有重新启动模型或 MCP。实际 run `18c4b04c030b40a2bb800a7f3e8a32bf` 使用 Codex／`gpt-6.1-sol`／high，CLI exit 0、succeeded，driver 256.521786 秒，原 decision 为 `approve`。

逐项读取 `self-review-r1/` 下冻结 manifest、prepared input、actual input、admission、scope、native stream、protocol／run result、原始 result、review 和进程采样。按 `asset_trees.inventory_tree` 的实际文件摘要＋执行位完整树算法独立重算：manifest digest 为 `ec9c1f6169f8208ec6b41f8b078cdbff4e829cb59563e6bcd9131564791819c2`，prepared／actual input digest 同为 `36b3c7b4da07c120eb1ef073c3bc27f6ee013fb479796fc20ffacceb837a0f83`。两份 input 的 composition、request、task、prompt 逐字一致，composition 与 frozen manifest 相同；admission／native 绑定相同 request、原资源和 input digest。

prompt 原字节 SHA256 `524e3f3cbba8f4bd22901a6eb55ca4c4eb2c036e2fca00ef3d9a96b8108994d9` 与 request／admission／native 相符，actual prompt、stdin 和 protocol prompt 逐字相同。完整祖先内联提示及 operator task 均在 prompt 中。scope 的 run／input／list-read 工具集合和实际 native command 中的 scope hash 相符；五份 scope 字节逐一等于 frozen、prepared 和 actual assets。

原生 stream SHA256 `2192ef17b12bde25a85dd2d318de88ae28cf32a0597775677b5f933d3be3bd26` 已重算。独立解析到 **22 次成功 MCP 调用：1 list、21 read，0 失败**。list 一次列出全部五份资源并以 null 结束。四份指令／Skill 各一份 UTF-8 页完整读到 null；候选附件有 14 个独立连续 UTF-8 页，从 offset 0 接至 311806／null，每页内容、offset、size、SHA 和 next_offset 均与 scope 原字节相符。另有 offset 0、25000 的两次重复页，以及 offset 279000 的一份 22000B base64 页；后者在相同 offset 缩小窗口后取得 UTF-8，再连续读完，没有把 base64 或重复页当成已补足的连续文本。

附件 311806B、SHA256 `7c89b8a2a2c85fff359d4a98693680a0b6bbaded9284d80b922567c10c5ebc03` 与 index 和各 asset 一致。对 13 个 complete FILE 区段按声明字节边界逐项重算，全部符合 `raw-evidence-index.json`。其中八份产品／测试与首轮 11 文件候选完全相同；额外 `projects.py / tasks.py` 提供 owner 上下文，计划／交付是当时冻结的较早版本。原结构模板的指令与原 Skill 逐字保持；只有定义版本、所选新引用、候选证据资源和材料预算作本次适配。

原 result SHA256 `1a4555922b3f7344b54f61edcda6e47f95bf706d7d87f6da7a1fa3aa5650b4a5` 已重算，run 保存结果与 original-result 逐字相等；protocol 结果及 native 最后结构化消息解析后相同，`review.md` 等于原 response。原结果明确分别给出 Spec／Standards 无待改 finding，并保留未附 owner、真实服务和后补公开文档的范围限制。`self-review-r1.json` 与 `-read-audit.json` 的相关身份和读取结论已由本轮原件核验支持。

原采样记录四个所属 CLI／后代 PID＋starttime，保存的 live 列表为空；本轮再只读 `/proc` 核查这四个原进程身份，均无匹配存活。不扩写为全部短命进程证明。native turn 记录 input 1301769、cached input 1171328、output 5687、reasoning output 3511；cached 属于 input，不另行相加，不推算计费。Codex 是已授权回退，不称成功的不同后端独立证明；固定 MCP 资料授权和 native read-only 请求不称 OS 隔离。

## 完整 26 文件候选与本地出口

最终公开／产品／测试候选为 `full-review-r1/manifest.json`，SHA256 **`bb44bec7fae1b845e65013d9478cec72cdd0256c372300d627a9efe4d5d27959`**，基线仍为 `b5ee397e6571f95393b0f8d6e9ee7e6d947b0935`。独立重算 26 份 `files/` 原件，大小／SHA 全部相符；源码、测试、旧 codec fixture 和原研究与首轮精确候选不变，沿用首轮逐路径审查。其他文件按基线 diff 和相关上下文核读，新增 JSON 读取完整内容。

完整文件集合为：

- `README.md`；`docs/AGENT_BACKENDS.md`、`docs/PLAN.md`、`docs/USAGE.md`。
- `docs/architecture/contracts-and-identities.md`、`docs/architecture/current.md`。
- `docs/delivery/2026-11-11-issue-label-writeback-review.md`、`2026-11-11-issue-label-writeback.md`、`2026-11-11-issue-writeback-review.md`、`2026-11-11-issue-writeback.md`。
- `docs/delivery/evidence/2026-11-11-issue-label-writeback-acceptance.json`、`2026-11-11-issue-label-writeback-self-review.json`、`2026-11-11-issue-writeback-acceptance.json`。
- `docs/plans/2026-11-01-all-in-one.md`、`2026-11-11-issue-label-writeback.md`、`2026-11-11-issue-writeback.md`、`2026-11-11-project-trackers.md`。
- `docs/research/2026-11-11-issue-label-writeback.md`。
- `src/ergora/cli.py`、`data/components.json`、`issue_backends.py`、`issue_writebacks.py`、`web.py`。
- `tests/fixtures/issue-comment-v1.json`、`tests/test_issue_label_writebacks.py`、`tests/test_issue_writebacks.py`。

后续 C2b 的 `docs/research/2026-11-11-gitlab-label-ids.md` 明确不在本片集合；26 件中均无指向它的文字或新增公开链接。本报告的追加与下述三件状态修正是同片评审／记账，不把其新字节冒称原 manifest 中的旧 blob。

### 最终 r2 发行身份

独立只读重算 r2 wheel SHA256 **`13ace2b7aebaac9bf171fcb335e84bea2b6c53bc7758206c55840b70d062d600`**，并逐一验证全部 **451 条 wheel RECORD、456 条 installed RECORD** 的实际 hash／size；只有各 RECORD 自身按规范留空。源码、r1 wheel、r2 wheel 和 r2 installed 的 **446 个包文件集合及原字节完全相同**；原 reference manifest 所列 **283 件**在源码／r2 wheel／r2 installed 中各自符合冻结摘要。

r1→r2 完整 archive entry 集合相同，逐项比较只有 `ergora-0.2.0.dist-info/METADATA` 和 `RECORD` 两项内容变化。r2 METADATA 与安装后的内容一致，末尾逐字等于完整候选的 README。故 r1 的 117 passed／1 skipped 保持其原运行身份，同时确证 r2 产品字节相同；不需要为了这次元数据变化重复相同产品检查，也不声称 117 项在 r2 重新运行。

r2 `installed-validation.json` 的两项原 stdout 已重算并全文读取：标签准备 CLI help exit 0／1.017081 秒、reference verify exit 0／0.316086 秒；后者为 PASS／283、`runtime_started:false`，两份 stderr 均空。它们是作者已有运行原件，本轮没有再次调用安装解释器执行命令。

### 公开材料与证据投影

README、使用手册和架构说明与实际 Interface／调用路径一致：GitHub ID 单标签、GitLab unsupported、原 C1 合同、一个语义槽、attempt-before-send、有限页的正向 receipt／unknown、query 观察、实际请求数量和 socket I/O 时间限制均有对应实现；没有把 actor 预检写成写权限／mutation actor 收据，也没有宣称 CAS、静默通知、GHES 跨版本或真实账号验收。

两份 C2a 公开 JSON 的身份、结果、读取审计和原 response 已逐字段对原件。删去公开投影中的私有路径字段后，自身 metadata 与原件相等，read audit 和原 response 完整相等；acceptance 的 r2 包、r1→r2 delta、命令 exit／时长／stdout hash、源码与安装 stdout hash 均与原件相同。C1 后补只登记它自己的 b5ee397／CI43015595781 结案，与原 C1 独立终核报告范围相符，保留 SSH407、两份 In progress、非成功 REST／非全日志的限制；本轮未重新请求 C1 远端或 CI。

独立提取完整候选的 **388 个本地 Markdown 目标，缺失 0**；JSON 解析及尾空白检查通过，三件状态修正后仍为相同 388 个目标。作者 `static-r1/result.json` 另外记录 6 个已载入秘密值的扫描通过；本轮未另取环境凭据，因此不把该 6 值检查称作本轮独立秘密扫描。未执行外链请求、浏览器／Mermaid 渲染或全体历史 anchor 检查。

### ST1：P3 当前状态表述落后，已关闭

位置：`docs/plans/2026-11-11-issue-label-writeback.md:26`、`docs/delivery/2026-11-11-issue-label-writeback.md:17`、`docs/plans/2026-11-01-all-in-one.md:475`。完整候选中 L1／L2 仍写“待回归／安装／审查”“检查进行中”，交付段和总计划交接点也保留安装尚在运行的当前表述；同一候选已记录 67 项源码、117 项安装与实际自身 approve。恢复者从当前矩阵／交接点进入时会误读尚待范围，可能重复已经完成的检查。最小修正是将活动状态同步为已验事实，并将旧安装进行中语句明确标为当时历史状态，不改变历史原件。

作者只修正上述三份文档。本轮相对 full-review-r1 逐 diff 复核：只同步已通过的源码／安装／自身状态，完整独立及精确交付仍待；其余 23 份候选文件，尤其产品／测试，仍逐字相同。修正后三件 SHA256 分别为：

|文件|修正后 SHA256|
|---|---|
|C2a 计划|`bda9a3a1480d5fcf6d77d7ba4fc8b2e414258ae61e956054ceb8601077e30c52`|
|C2a 交付|`a7023b711f9061ad2a9e4679efcf387f686ac7b26db220bf5144a010f49c2123`|
|总计划|`05a09183ca21cc02ea0ec0049000486cc3fb66b2543eef0495d925fbab68c958`|

ST1 关闭；这是纯状态修正，无需重跑产品。

**完整本地出口通过：Spec 开放 0，Standards 开放 0，ST1（P3）已关闭。** 该结论覆盖上述 26 文件、三件已核状态修正、最终 r2 全包／两 RECORD／283、实际自身原件及公开投影；本报告追加按同片记账处理。C2a 精确 ready／Git 对象、普通提交／推送、同 SHA remote 和本提交自己的必要双 OS CI 继续待核，当前不称 C2a 精确交付或整个 F7 完成。
