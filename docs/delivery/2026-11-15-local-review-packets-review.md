# Q1.1 精确本地审查材料包独立评审

日期：2026-11-15。评审者：fresh-context 独立代理 `local_review_packet_audit`。只读产品、测试和证据；唯一写入为本报告。依据仓库 `AGENTS.md`、[具体验收](../plans/2026-11-15-local-review-packets.md)、[原要求／Q 总计划](../plans/2026-11-15-domain-review-optimization-quality.md)，使用 `ergora-codebase-quality` 的 ownership／repository-style／test-seams references 和 `maintainable-project-delivery` 的 independent-review brief。

**当前结论：r2 最终本地需求符合性／可维护性两轴 approve，开放实质 finding 0／0，R1／R2 已关闭。** 精确提交／远端身份、当前候选自己的完整适用 CI 与 Windows 终态仍待核；不能据此宣布发布全部完成。下文保留 r1 的实证失败及其原身份。

## 身份与范围

固定基线／初审 HEAD：`eecd90aa70c9268144af1161ade9076790dabf92`；分支 `refactor/architecture-foundations`。初审对象为 `.ergora/checks/local-review-packets/review-scope-r1/scope.json` 的全部 16 个 tracked／untracked 文件；逐字快照位于同目录 `files/`，tracked diff SHA256 为 `63bc280ba595a8aebd95ab92a422e437b2eb6dbabb98af8bcfd7cb46f02b1822`。逐一独立核过 16 份快照的长度和 SHA256；初次核对时仅交付记录已有例行更新，产品／测试均与快照相同。

完整读取新增 Git reader、packet owner、Schema 和测试，核对实际 CLI 分派、正式 executor 的 preparation／review 材料调用、权限回调及原 execute 的异常／receipt 路径，并检查既有发布、相对路径、JSON、CI 分组和原完整材料 fixture。不是仅凭 diff 或作者报告作结论。

本片仅涵盖 state-free 本地 prepare／verify／read 和原读取复用。预训练／后训练专长、远端采集／发表、真实 B3／GPU、完整 Forge、多轮优化均不在此次实现验收范围。kernel 专家保留的用户补充已反映在 Q 计划；没有改旧优化模板。

## 初审结论

|轴|r1 结论|
|---|---|
|需求符合性|request-changes：R1 违反材料输入的有限资源边界；R2 允许同一提交的源表相互矛盾。其它已检查路径符合此次本地材料切片边界；最终候选、安装和适用 CI 尚待补核。|
|可维护性|request-changes：应在 packet owner 关闭 R1／R2。整体所有权和复用合理，未发现需要再造框架、第二任务／批准系统或拆分额外模块的证据。|

## Findings

### R1 — P2：需求／evidence 在总量检查前全部聚合

位置：r1 `src/ergora/review_packets.py:24`、`:168`、`:169`、`:173`。

`_document` 对每个文件允许读取 10 MB；`prepare` 的 evidence 列表推导先读完全部文件，之后才做 Schema 的 500 项检查和最终 10 MB JSON 检查。因此正常数量内的多份大原件也能先积累数 GB；超过 500 项的列表会先全部读取并构造巨大错误消息，可能在明确拒绝前耗尽内存。

独立小复现使用真实临时 Git、2 个提交和公开 `prepare` 入口，仅包装 `_document` 统计真实返回字节：501 份各 2,000B evidence 与 6B request，在数量拒绝前共读取 **502 份／1,002,006B**；destination 不存在。未进行大文件／OOM 压测。终端原输出如下，临时目录已自动删除，本报告是该独立复现的持久记录：

```text
documents read before rejection: 502 total bytes: 1002006 destination exists: False
```

最小修正：读取前限制 evidence 数量；需求和 evidence 共用累积字节预算，每份至多读取剩余预算＋1，超限立即停止；最终 JSON 上限保留用于序列化开销。用公开 prepare 入口观测实际读取量和失败不发布即可，不需为每个内部分支增加测试。

状态：r2 已关闭，修正与独立复验见后文；r1 失败记录保留。

### R2 — P2：同一提交身份可以对应不同文件表

位置：r1 `src/ergora/review_packets.py:59` 至 `:85`。

`_check` 核 source 各 label 的 commit 字符串与 repository 一致，但没有核共享 commit 的 label 是否有相同文件表。直接比较时 `base == diff_base`；只清空 `source.base.files`，保留 diff_base／head 与 blobs，离线 verify 仍通过。这是包内部可检测的矛盾，不需要认证 Git 来源或祖先关系。

独立小复现先公开 prepare 一个直接比较包，再只清空 base 表，verify 的终端原输出：

```text
same commit label with empty base file table: {'base': 0, 'diff_base': 1, 'head': 1}
```

最小修正：共享 commit ID 的 source label 必须共享相同文件映射；一条通过公开离线入口暴露矛盾的回归足够。

状态：r2 已关闭，修正与独立复验见后文；r1 失败记录保留。

## 结构与测试价值

`git_materials` 有两个不同生产文件中的真实消费者：`reference_executor` 与 `review_packets`。它集中有界二进制进程读取、版本／环境限制和完整 blob batch；formal owner 仍提供叶权限回调，packet owner 持有采集身份、选择范围、离线一致性与发布。CLI 在 State 构造前分派，沿既有 `publish_directory` 原子不覆盖发布；未增加依赖或与模型／远端平台耦合的层。

新接口是完整材料边界，单个 CLI 生产调用者不构成多余抽象。私有 instructions／changes／check／summary 分别隐藏本 owner 的算法和合同，没有为凑复用率增加包装。输入、身份、内容引用、容量和发布检查都有可达的外部输入或持久资料失败情形。原正式候选、批准、恢复和取消 owner 未迁移；原异常处理也捕获 reader 的 ValueError。

真实 Git 测试覆盖分叉时 base／diff_base 区别、完整删除／改名源、CRLF／Unicode、工作区隔离、显式上下文／祖先规范、移走仓库后的读取、缺对象不 fetch、Git 配置可执行路径隔离、SHA256 仓库、可变字节预算和关键篡改。它们保护静默丢源／错误身份／越权发布等真实风险。沿原 suite／CI group 增补合理；R1／R2 应由最小公开入口回归补齐。

## 已核证据与保证边界

- `source-r1.json`：源码导入下 32 passed／3.97s；这是作者运行记录，范围不扩大为安装或 Windows。
- 独立核 r1 wheel SHA256 为 `23ea59fd386d7d08dc70e21ebb83c63a483ab8cf36f125628bc3234c7615cbaa`，wheel 的 614 个产品条目及摘要与 `package-r1.json` 相同，五个本片产品文件与冻结源码逐字相同。`runtime-r1.stdout` 确认为非 editable 安装位置、Python 3.12.3；venv 使用 system-site-packages，不是 clean 环境验收。
- `reference-r1.stdout`：283 份冻结参考 PASS；没有把新控制面模块算作冻结参考变更。
- 初次核安装回归时仍在途；后直接读取 `installed-r1.stdout` 的终态为四 suite **70 passed／234.20s**，原 request 使用安装 venv、`-I`、未设 PYTHONPATH。它属于 r1，不能提前认证后续修正候选。
- 独立复现及源码核对确认：Git 只读对象路径禁用 replacement／hook／external diff／textconv／lazy fetch，不 checkout；blob 字节原样解码编码保留 CRLF。线程分别有界排空 stdout／stderr，超限或 60 秒 process wait 失败经 finally kill／wait 清理。未独立执行 Windows 或真实超时故障注入，不宣称全平台生命周期动态验收。
- 离线可核 source 引用、blob 的 Git ID／SHA256、changes 与选定前后表、文档摘要；独立整包摘要可以绑定收到的全部字节。r1 将 diff 改成任意字符串时，未传原整包摘要的 verify 仍通过；传原摘要则拒绝。这不证明 diff 派生、commit 到文件表的真实 Git 树关联、来源／祖先、依赖完备性或检查可信性。实现者拟增加本地 diff 摘要／字节限制并明确这个边界；此处不要求自造 diff 重放器。
- 之后才读取原自身模板的 r1 结果：`self-review-r1-codex.json`／`self-review-r1-codex/review.md`，真实 100.280s、request-changes，同样指出资源聚合与同提交源表矛盾；它没有替代本独立审查。

## 初审时待终核

R1／R2 修后重新冻结完整 scope，核源码／最小回归与最终非 editable wheel；受影响安装检查、自身模板、实际文档声明，以及最终普通提交／推送的完整远端身份和候选自己的适用 CI 终态。当前不作最终通过或发布批准；真实 B3／完整 Forge 等原开放条件保持。

## r2 修正与最终本地复核

r2 完整范围为 `.ergora/checks/local-review-packets/review-scope-r2/` 的 17 文件（包含本报告当时的快照），固定基线不变。独立逐一核长度／SHA256；`scope.json` SHA256 为 `55957062fe925449d03205a40c36de9ea3e5ab186f3075f0c3d81f5f9f4c51c3`，tracked diff SHA256 为 `7e87f3d0b59a960d09588166068ab5876ffb7211e2f0b624dffce62b32907a6a`。冻结后 PLAN／交付仅追加真实状态，本报告为同片复核记录；未观察到产品／测试漂移。

- **R1 关闭。** r2 `review_packets.py:175` 先按 Schema 的 evidence 数量上限拒绝超数，再以需求和 evidence 共用剩余字节预算读取（`:24`、`:177`）。每次最多读取剩余＋1，最终 JSON 容量门禁保留。作者原公开回归 `document-budget-red.stdout` 明确观察到旧源码读取 12,000,035B；修后 green 与新安装包已通过。独立再用 501 份不存在的 evidence 和不存在的需求调用公开 prepare，得到数量错误，**document read 为 0、destination 不存在**，证明确实先拒绝再读取。
- **R2 关闭。** r2 `review_packets.py:59` 在原 validator 内按 commit ID 比较完整文件映射，保留来源／祖先不认证边界。作者 `consistency-red.stdout` 在旧源码观察到同提交矛盾和 diff 篡改两条实红；相应公开离线入口回归在修后安装件通过。
- 本地 source 增加 `diff_sha256`，并核 diff 原始 UTF-8 字节不超过声明的 source 预算；原正式 executor 的 diff 字符串形状未改。更新后的使用说明明确：摘要发现未同步摘要的字节变更，不能离线证明 diff 由该 Git 树派生；恶意者可重制正文和摘要，需独立整包摘要绑定原材料。这一限制表述与实现一致，没有增加 diff 重放器或第二认证系统。

独立以最终非 editable 安装 Python 的 `-I -m pytest` 定向复验公开入口的聚合预算、同提交矛盾、diff 篡改与 diff 超限四条，结果 **4 passed／0.97s**；仅使用临时测试目录，没有改产品或测试。作者源码新包／导入边界记录 `source-r2.stdout` 为 37 passed／3.68s。测试保护的是旧实现实际漏过的风险，资源回归观测实际文件读取量；不要求再为明显数量报错增加重复测试。

独立重算 r2 wheel SHA256 为 `6a9f36c230955f67649f82d9eb1b7b5b92f2c2c633dc86cae5a993d98b94b48c`，614 产品条目与 `package-r2.json` 全部一致，并逐个核当前安装文件为同一字节。五个本片产品文件与 r2 冻结快照逐字相同；相对 r1 仅 `review_packets.py`／Schema 两个产品条目变化，共有 reader 和正式 executor 保持 r1 字节。原 283 参考 PASS；安装环境仍使用原 system-site-packages venv，不宣称 clean 安装。

安装终态已直接核 `installed-r2-request.json`、`installed-r2-result.json`、stdout 和 XML：**38 passed／36.01s，exit 0**；XML 实际为包测试 **22**、架构测试 **15**、原完整材料 full 旅程 **1**，0 failed／error／skipped。这次运行认证 r2 新逻辑和原 full 材料边界；未改变的其它原正式路径仍保留 r1 的 70 项记录，不冒称 r2 重跑了四套完整回归。

原自身结构模板 r2：run `9564e184230a41b8abe619657ee64fd6`，56.430s，succeeded／approve，23 份完整文件／608,241B。独立核原结果 SHA256 `f8f9a380d1703ed5525eb28b1879cfb6e6702b9143b9554b8bac996a53f7e6df`、prepared prompt 与实际 stdin 逐字相同、原 task 全文在 stdin、三个声明父／叶资源全文在 stdin；所供本片产品／测试与 r2 冻结身份相同。所供文字通过不扩展为模型观察了运行或 CI。

|轴|r2 最终本地结论|
|---|---|
|需求符合性|approve；R1／R2 关闭，开放实质 finding 0。此次本地材料与原读取复用符合具体切片，保证范围和未实施能力有明确说明。|
|可维护性|approve；开放实质 finding 0。修正在 packet owner 内关闭输入和持久资料不变量，沿原库／reader／发布／CI 入口，没有新增不必要抽象或重复验证系统。|

待后续精确提交／普通推送完整身份核对、暂存全部新增文件检查，以及该候选自己的完整适用 CI／Windows 终态。此处是最终本地复核，不提前认证远端或 Windows；真实 B3／完整 Forge 等开放条件继续保持。
