# Q2.3a 精确来源审查输入：独立审查

日期：2026-11-15。评审者：fresh-context Codex，`source_bound_inputs_audit`；未继承实现会话。已读项目与源码／测试目录规则、组件变更协议，以及 `maintainable-project-delivery` 的 independent-review 和 `ergora-codebase-quality` 三项参考。

**本地需求符合性 approve；结构可维护性／测试价值 approve。开放实质 finding 0／0。** 结论限于本片精确来源到原完整单叶输入，不认证整图执行、报告功能或尚未发布候选的 CI。

## 精确范围与合同

基线为 `6f42cad6edcd2ef53f2f6326628d1df728a118bd`。直接读取了 `.ergora/checks/source-bound-review-inputs/review-scope-r1/` 的 `scope.json`、`author-diff.patch` 和全部十份 `files/` 原文；scope SHA256 为 `929a34d5f61b7f4485f338c7ef5449fe79b6eee07919bf3e952988a0a2966efb`，diff SHA256 为 `72f9311a1382a316b81f7e362c07cc6e742181c5e4006a9dcd61330494d1d3ec`。首次十份工作树文件与冻结原件的字节数／摘要逐项相同。

产品只有 [review_requests.py](../../src/ergora/review_requests.py) 新增和 [cli.py](../../src/ergora/cli.py) 分派；测试改动在原 `test_review_packets.py`／`test_review_associations.py`。其余为本片说明和交付记账；前片 `external-review-sources-review` 追加属于其自身发布／CI 终核。审查期间 PLAN 更新了实际已验状态，并追加前片交付终态及 [Q2.3b 后继计划](../plans/2026-11-15-source-review-reports.md)；已补读，均未改变本片产品／测试字节。最后复核四份产品／测试仍等于 r1。

按原要求检查了来源种类与独立 SHA、所选完整 manifest／digest、reviewer 实例及容量；材料不能截断，祖先 Skill／上下文和权限不能丢失或越级，未执行前驱不能跳过。领域／专长来自原组合，实例后端仍在原调用入口选择；不同后端优先和用户授权 Codex 回退保持。643 文件差异盘点确认所有 preset、原 runtime 与 kernel 专家路径均未改。

## 需求正确性

亲自沿 `review_packets.read`／`review_sources.read` → `review_requests` → `workflow_definitions.inspect_manifest`／`prepare_input_from_manifest`／`inspect_input` → `agent_runs`／原 backend 工厂与 `agents.invoke` 读取实际实现；同时核 `review_dags.require_root_task`、完整资源编译、`asset_trees.publish_directory` 及相邻调用／fixture。

- 新 owner 将原 reader 的完整规范化材料放进 task，原需求、三份源码表与全部 blob、显式上下文、祖先仓库规范、检查原文和外部观察均保留。源文件排版的 SHA 与规范化材料分别保留原有含义。
- reviewer／只读工具限制与包内所有实际源码路径的 read 上界在该来源边界检查；原编译器继续核全部结构祖先资料、资源身份和逐级权限。`require_root_task` 检查到根，能拒绝祖先未运行依赖；未新造图调度或自动执行。
- prepare 先核明确 manifest digest，再用原编译器生成完整输入并比较最终图；额外暂存使此检查发生在对外发布之前。原 no-replace 发布器处理已有／并发出现目录，来源／manifest 内部目的地会在建目录前拒绝；容量仍由原编译器拒绝，不发布部分成功输入。
- verify 重读明确来源及其 SHA，核完整 input digest、所选叶约束和完整 task 的身份。`manifest_digest` 是 task 中原选择声明；缺少原 manifest 时不认证其来源。手册、计划与实现对这一限制表述一致。
- CLI 在 State 构造前分派；新 owner 不接管 reader、输入格式、后端准入或 run，不调用平台、目标代码或模型，也不重发 failed／unknown。正式批准和整图 all-join 保持原边界。

## 结构与测试价值

`review_requests` 的唯一生产调用者是 CLI，两项公共用例承担完整来源到只读叶的组合义务。若删除该 owner，来源读取、task 身份、叶约束和发布前校验会回流 CLI；因此该模块具有具体职责，不是单次转发。三个私有函数分别拥有来源选择、完整 task 编码和来源专属叶约束；没有为重复利用数量增加接口。local／external 分支解释两种已有输入，不是新后端分派；没有新增 ABC、schema 文件、State 或持久账本。

新增 guards 对应明确外部选择、来源读取权限、未执行依赖、manifest 两次读取与不可覆盖发布风险；通用资源、SHA 格式、容量和输入结构继续由原 owner 校验。新增测试落在已有 Git／平台来源 fixture 内，覆盖错来源任务、完整祖先资料、有效但不适用的权限、切换 manifest、祖先依赖、容量失败不发布，以及无凭据／无 Git 的外部来源离线输入。容量测试同时检查临时目录清理，外部测试检查无新平台读取和无 State，未只测错误措辞。

原四 suite 同时包含源码／来源、组合编译与调用接缝，能覆盖实际组合关系。未新增测试文件或 CI job；现有显式 Linux group 0／3 已分别收录两个被改 suite，Windows `all` 仍选全套。没有要求删除或扩大测试的实证理由。

## 原件核验

以下为直接读取原件并重算所得，未用作者报告或模型判定代替：

1. 解析 `source-tests-r2.xml`：216 passed，0 failure／error／skip，四 suite 为 29／64／25／98，XML suite time 为 67.137 秒。解析独立安装 XML／stdout：同样 216 passed，stdout 记 77.35 秒，仅原 Starlette warning。没有重复跑这两套测试。
2. 重算 `package-r1.json` 全部 643 项，并读取原 wheel 与独立 `venv-r1`：源码＝wheel＝实际 site-packages 逐字一致；`direct_url.json` 指向该非 editable wheel。wheel SHA256 为 `0608ada9d10cf2a39c972cdf276f7fbaddaf8a9b0bdb8d72f5ff2829f7d6e979`。对固定基线只新增 `review_requests.py`、只改 `cli.py`；283 份 reference 与固定基线逐字相同。
3. 重算 native 17 条原命令 stdout／stderr 摘要及预期 exit code：两次已有目录拒绝为 exit 2，其余为 0。对预训练、后训练、GitHub、GitLab 四份完整 input 重新调用原 inspect／read／verify，均匹配原回执；另直接核原 manifest digest 和 input composition 相等、task.material 与原 reader 全文相等、每叶四份完整资源在 prompt 中。`source-manifests.json` 的五份目录、153 文件全部保持。
4. 真实领域 run `efd0fc2581d24d45a42e20d34b475c97`：直接核 sealed input、原 `input_request`、prompt、实际 stdin、原生 command／turn.completed／结构化回复、result 与只读 SQLite 原记录；该 State 恰有一条相同 run。input digest 为 `93a04ede6e9cbd92ab58242fc4b6cb2ccc09d3f3f8611607513aee9f4d19c714`，result SHA256 为 `13456e90b1fec938fa53742df1430dff67e6d6ca4f6b4180b10256116e7814e9`；保留 CPU 标量缺陷的 request-changes，未改成通过。
5. 自身原结构模板 run `9606ae65ca07424a9d364153ab5b0eac` 也按上述原链核同；20 份 338,145B 完整供给文件逐项核摘要并存在实际 task，三份资源和完整 task 在实际 stdin 中，原生结果为 approve。input digest 为 `c310bbb028e339c6bca6d6e44956b106a798c567f805570461d9361d98b7cee8`，result SHA256 为 `1c311cf88c853020e19396447194c7a47208b872d588d7e5a889bc956953e869`；该模型文本没有被当作本次独立结论。

私有旅程原 stderr 的收尾字段错误发生在成功原模型调用之后。已读 driver／`finalize-native-r1.py` 和同一原 run；恢复脚本只读同一 run 并整理验收产物，没有模型分派。原 stderr、原命令回执和原回复仍在，因此不将此记录错误归为产品调用失败，也不凭汇总 JSON 宣称已恢复。

另做四份 Python AST 解析、实际生产消费者搜索、tracked `git diff --check` 及五份新增文件的空白／末尾换行检查，均通过。含当前公开记账、后继计划及本报告的 18 份 Markdown／309 个本地链接与 fragment 零错误；未验证外部网页。未安装、重跑模型／全套测试、训练、启动服务、发平台请求、提交或推送；本次仅写本报告。

## 剩余验收

本地没有阻塞修正。普通发布后仍须核本片自己的固定源码／完整远端 Ref、适用 CI 终态与同一 reviewer 补核；前片固定 6f42 的 CI 不能认证此片。Q2.3b 的精确原 run 读取、跨分支完整覆盖与本地报告明确未实现，后继计划仅是合同。四路 all-join、真实平台完整成功采集、训练／GPU／分布式／质量／性能及完整 Forge 均不在本次验收内；stdin 字节交付也不证明模型理解或任意 provider 上下文容量。

## 固定普通发布补核（2026-11-15）

同一 reviewer 直接读取固定提交 `f1fc4501b8f15060eee7502caf6531c8f44a1b5f`：唯一 parent 为 `6f42cad6edcd2ef53f2f6326628d1df728a118bd`，tree 为 `037b4d810155232894ed7838b8975057a027c700`。**固定发布需求符合性 approve；结构可维护性／测试价值 approve；开放实质 finding 0／0。** 本节不提前认证尚在运行的 CI。

固定差异恰为 14 文件／305,445B，各项 blob ID、字节数及 SHA256 与 `publication-r1.json` 逐一相同；回执 SHA256 为 `124753eafeeb5ca1c5e6155f3b4299688835d8714d87f25f298b0b8c15894f73`。保存的完整 `remote-r1.txt` 为上述提交及 `refs/heads/refactor/architecture-foundations`，摘要 `aa5a9c6d8be8b1c734366b6f2596e200112958928ca724595b3399181256d002` 匹配发布回执；未把 push 前的 pending 字段误当终态。这里核保存的远端原件，未额外执行 Git 网络写入。

固定产品／测试与 r1 已审原文逐字相同；其余差异限于本片审查记账、前片 CI 终态同步及明确未实现的 Q2.3b 计划。固定提交中的本报告即原 8,754B／SHA256 `f453e1364301776ee3d9528a777f4ab6bc884e5b0691e2391e45a2cb5c932ae7`，本次追加保持该前缀。只从固定 Git 读取的 643 份产品＝原 package 清单＝原 wheel＝原独立安装逐字同，283 reference 对固定 parent 保持；没有用后继工作树认证此候选。

完整 baseline→固定提交 `git diff --check` 通过，覆盖新增文件。固定 Git 的 18 份 Markdown 共 313 个本地引用：312 个目标／fragment 在固定 Git 内解析通过；前片报告另有一条明确指向私有 CI 审计原件的链接，其本地 104,860B 和声明摘要已直接核同，不将该 ignored 原件声称为公开 Git 内容。

已用匿名、有界、无重定向的官方 API GET 按完整 SHA 发现唯一 Portability run [43636049607](https://github.com/626619403/Ergora/actions/runs/43636049607)，attempt 1。随后直接保存该 run、完整 job 分页与八个原 job 页面十份响应；2026-11-14T20:14:24.596665Z 解析时仍为 In progress、24／30 必要步骤成功，不能据此关闭门禁。发现响应、各次请求回执及原页面分存本片 `.ergora/checks/source-bound-review-inputs/ci/`，没有借前片 CI。剩余验收为此固定提交自己的完整 CI 终态及同片补核；不重跑模型／测试或推送。

## 固定 f1fc450 自己的 CI 终态补核（2026-11-15）

同一 reviewer 已直接取得并重解析上述 Portability run `43636049607`／attempt 1 的官方 API 和原页面终态。完整 SHA 仍为 `f1fc4501b8f15060eee7502caf6531c8f44a1b5f`，parent／tree 由固定 Git 再次核同。**需求符合性 approve；结构可维护性／测试价值 approve；开放实质 finding 0／0，Q2.3a 片内剩余验收 0。** 本节关闭前文待固定发布／本片自有 CI 的事项，不认证任何后继工作树或后继提交。

官方 API 于 **2026-11-14T20:33:48.248785Z** 返回 run completed／success、八个 job completed／success、30／30 必要步骤 success。随后独立取得的终轮原页面窗口为 **20:34:06.636823Z–20:34:10.066255Z**；run 显示 Success，完整分页 `totalCount=8`／`hasMore=false`，八个唯一 job 无漏项或重复，分页和各自原页终态一致：

|固定 job|ID|必要步骤成功数|
|---|---|---:|
|plan|`132572973523`|1/1|
|Ubuntu／Python 3.11／group 0|`132573018819`|4/4|
|Ubuntu／Python 3.11／group 1|`132573018825`|4/4|
|Ubuntu／Python 3.11／group 2|`132573018902`|4/4|
|Ubuntu／Python 3.11／group 3|`132573018813`|4/4|
|Ubuntu／Python 3.11／group 4|`132573018842`|4/4|
|Ubuntu／Python 3.11／group 5|`132573018826`|4/4|
|Windows／Python 3.12／group all|`132573018794`|5/5|

必要步骤由固定 workflow／六组配置及 runner 确认：plan 的 `Read explicit test groups`，七个 native 的 `Run actions/setup-python@v5`、`Build and install wheel`、`Packaged reference identity`、`Native application regression`，加 Windows 的 `Windows PowerShell 5.1 installer and upgrade`，合计 30 项。逐项核完整终态属性、非空起止时间、步骤次序与 plan 先于 native；原 log URL 精确绑定本完整 SHA／本 job ID／步骤号。终轮 API 与 HTML 的 30 项名称、编号、状态及起止时间全部相同。Windows 回归于 **20:32:40Z** 成功，PS5.1 安装升级于 **20:33:39Z** 成功。

本轮共保存 **55 个匿名 GET**：一次完整 SHA 发现、17 轮 run／attempt-1 jobs API 观察，以及两轮 run／完整分页／八 job 原页。每请求 timeout 20 秒、响应上限 2 MiB，拒绝重定向，不带凭据，无自动重试或平台写入。24／27／28／29 项成功的在途观察原样保留；终态没有借其他 SHA、重新分派 CI 或模型来替代。

已直接读取 **94 份审计输入** 并建立字节数／摘要清单，其中 55 份 HTTP 原响应逐项匹配请求回执，均为预期 URL 的 HTTP 200；另核 API／页面身份、完整分页和固定配置。独立审计结果为本片 `ci/reviewer-ci-terminal-r1.json`，49,976B／SHA256 `4250af640da0947fd71fd55e549ef49a89233b789fc4c484b0c1903e5e057da7`，保存全部原件清单、两轮完整 job／步骤及 17 轮 API 状态。关键原件如下，八个 job 原页的逐项身份见该结果：

|本片 CI 原件|字节数|SHA256|
|---|---:|---|
|`api-run-reviewer-r17.json`|11984|`51d0777a55f94c7bf3d44818d1b2312526cbd037467e259bf87435ad0c5b2874`|
|`api-jobs-reviewer-r17.json`|21121|`444d81408a7bc62031e2198503ca158619188a0ab9cb2d5e0483c1caf417f3ff`|
|`run-reviewer-r2.html`|213348|`b4626291c7871801b5b5c5de79445c467370825bac801a53a152f4944e67265f`|
|`job-groups-reviewer-r2.json`|2736|`57ebc70b5a27c9c9f832a95ef75c533acc99afd3fcc087bb8720cf67b7269940`|
|`receipts-reviewer-r2.json`|7626|`35028f51bc4e760e3940b8034ddec6587302990497f73155add93e60b1e3f6fe`|

原 8,754B 报告及固定发布补核后的 11,166B 前缀均保持。没有下载逐测试日志／JUnit，也不编造 Windows passed／skipped 数；本次未安装、重跑测试／模型、训练、推送或修改其他产品／文档。Q2.3b 的报告／覆盖、真实平台完整采集、四路 all-join、训练／GPU／分布式／质量／性能与完整 Forge 的原未验范围保持，不因本片 CI 成功关闭。
