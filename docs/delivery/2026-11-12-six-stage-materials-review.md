# B1 完整材料输入：独立两轴评审

日期：2026-11-12。范围为[B1](../plans/2026-11-12-six-stage-materials.md)，原始接受条件见[D1设计的B1](../plans/2026-11-12-six-stage-native-consumer.md)。协调者及 Spec、Standards 两个评审者均使用 fresh context，未参与实现；两个子评审以 `fork_turns: none` 并行启动，先读原始要求、实际变化及相邻所有者，再读作者叙述。采用 AIHERO `code-review`、`maintainable-project-delivery` 的 independent-review brief 和 `codebase-design`；两轴分别判词，不合并排序。独立上下文不代表不同模型后端或统计独立。

## 候选身份与检查范围

固定基线及评审时 HEAD 为 `210f58d46c3332f4d192ee8cb13e8c149dd2173f`，产品基线为 `5ab6d350024de8515487d0bedb3b950be60ac867`，分支为 `refactor/architecture-foundations`。提交区间为空，因此审查明确使用 `git diff 210f58d46c3332f4d192ee8cb13e8c149dd2173f` 加完整新文件，没有用空的 three-dot HEAD 差异代替。

本轮判词绑定持久私有检查目录 `six-stage-materials` 中 `review-candidate-r1/` 的34份完整文件：

- 逐文件尺寸／SHA 清单 `review-files-r1.json`：SHA256 `a6a1b9854eadecfd4457af7cb558eb558a6dd34cc9784bc5375bca3e184d649a`。
- 1420行 tracked 差异 `review-tracked-r1.diff`：SHA256 `22a2fe44fec9c5705413d64d62fcb8c92d2d2fccecd486b8f4698698f22b17e4`。
- Spec 原报告 `spec-review-r1.md`：SHA256 `b1fd4923cf3f9d74a34abd494e5554654ad1446bb692ca63e8660f4ef0bf0126`。
- Standards 原报告 `standards-review-r1.md`：SHA256 `d7de4743384a081f5f983ed813d3c91f45e75634a73747ae3d3f61c2c6acc21d`。

协调者与两评审者均核过冻结副本与逐文件清单；初读时34份原路径也逐字相同。两个子轴均读完整差异、全部新增文件及必要相邻调用者。协调者随后完成36文件范围的同片补核：原34文件加本报告与公开自身审查投影；产品、测试、示例及手册保持原件，变化仅为四份计划／状态文档和两个新增报告文件。原两个子轴判词仍绑定其34份冻结候选，最终文档与实际证据由本独立协调者追加核验，没有冒称模型审过冻结后的文档。评审者未编辑产品、测试或公开手册，未重跑测试、安装、模型、GPU或网络检查。

收到的 `review-files-final-r1.json` 为36路径清单，SHA256 `1129e3501739e7cd00e4e41da310c25f3288d1992239f83c310b3aa6946adade`，收到时逐项匹配。随后D1文档澄清两处设计基线文字，本报告也更新状态，因此该清单不是后续最终字节身份。D1补核版本SHA256为 `1bb3498fce1697ebe7d3bcaaf757e6b2fcc7822f041046f794b90c3c5012d60b`；精确交付另以最终ready清单及Git对象核对，本报告状态更新不递归审查。

## Standards

**文档标准符合性：通过；可维护性：通过，仅限所查候选。硬违规0；判断性 baseline smell finding 0。**

已读 AGENTS、PLAN持续规则、B1两计划、当前架构、合同身份表、reference边界、ADR0001／0002／0004／0005及相关Skill；未见自有 CONTRIBUTING 或 CODING_STANDARDS。仓库规则优先于 smell baseline，工具已强制的格式项不重复报告。

- `tasks.py:68` 的 member 冻结供三类叶本地复用；`review_dags.py:12` 的根 task 校验及 `reference_executor.py:208` 的批量 Git读取复用现有所有者；`reference_inputs.py:263` 共用 v7/v8 准入。新增注册类满足既有 Interface，无新通用框架或厂商分派。
- `reference_executor.py:432` 的 producer 请求／收据／claim／调用身份门禁保护持久输入；不因形状相似建议删除。`task_mcp.py:251` 的连续覆盖校验归资源所有者，正式接受点调用它。
- 新测试针对遗漏叶、长尾截断、分页缺口与产物变动等静默失败风险，复用原生夹具；未新增 CI。Git读取保持批量、有界且整份拒绝。

未确认需要修复的文档标准违例或具有具体维护代价的 baseline smell。`git diff --check`通过。协调者最终补核未发现新增Standards finding：四份状态文档区分历史设计、当前实现与待完成的交付；公开投影保留原件身份和证据限制，没有将advisory权限、采样清理或模型读取夸为更强保证。产品与测试没有修改，不需重跑产品检查或另起新两轴。

## Spec

**所检 B1 范围无 finding。** 规格缺失／部分实现：未确认产品缺项；未要求行为／scope creep：未发现；看似实现但错误：未确认。

已按原始接受条件核 definition4／input8、准备叶根输入与全覆盖、冻结创建／恢复、完整祖先正文／Skill、精确 Git对象、原 inventory 全成果、容量整份拒绝和附件连续读取门禁。关键位置为 `review_dags.py:28`、`task_envelopes.py:333`、`reference_executor.py:262`／`:432`／`:734` 及 `task_mcp.py:171`／`:251`；跟踪了 stage_driver、agent_runs、workflow_definitions、agent_backends及冻结原 Executor／workflow 的相邻调用。

完整结构祖先资源、父权限上限、实际后端选择、原六阶段／owner批准／候选／unknown的既有所有者保持。B2总预算、C原生单实例与D完整真实旅程明确排除，不将它们待做列为B1产品缺陷，也不借本轮评审关闭它们。

协调者最终补核未发现新增Spec finding：实际模板仅审原34份冻结候选，来源／配置／输入／结果与公开读取投影一致；四份状态文档准确承接295／58项检查、453产品／两RECORD／283身份及实际模板结果。D1开头和版本注册表已明确为设计时基线，不把旧缺口当作当前状态；B2／C／D继续待做。

## 已核证据及仍待闭合项

协调者及子评审离线读取最终原日志和命令回执，未自行复跑：受影响源码9个suite为295 passed／338.10秒，命令回执exit0；Python3.12非editable安装的B1／task-MCP／架构3个suite为58 passed／200.58秒，回执exit0。旧129／70项及新13项结果保留原候选范围，不借作最终候选通过依据。

协调者直接只读复核了283份冻结文件的实际SHA，均与参考manifest相同；453份源码与r1隔离安装的453份产品文件，路径集合及字节完全相同。wheel SHA256为 `dffc1232c60a4a0a883420f4f0bc4f01bf15fb6ac9e940d13443029f4f246c21`，wheel RECORD458行及installed RECORD463行的有效hash／size逐项匹配。Spec评审也独立比较了453份源码／安装文件。

组件旅程覆盖原preview／create、Executor子进程、stage_driver、确定性native CLI协议及真实MCP分页，证明该实际进程链与字节交付；不证明真实模型理解、真实Temporal服务或完整任务CLI生命周期。trusted current-container writer的advisory权限也没有成为OS隔离。

## 最终文档与实际模板补核

协调者直接读取原始 `native.stdout`、实际input／scope、原生MCP调用stream、结果和进程采样记录，使用隔离安装的只读inspect接口及独立重建代码核对，未只采信作者的passed字段。随包结构模板保持原正文／权限，仅增加证据Skill、版本1.0.121及材料限额；manifest、prepared与实际input、prompt、准入、scope及原结果身份相同，活动定义库已退役，调用读取冻结包。

|实际尝试|观察结果|已核范围|
|---|---|---|
|Claude Code|8.01秒failed，退出1；原API400为system content校验，无审查结果|原失败stream及8个采样所属进程无存活；不列为审查意见或双后端通过|
|Codex，gpt-6.1-sol／high|377.86秒succeeded／approve，退出0|5份scope连续UTF-8读取至`next_offset:null`；原结果及4个采样所属进程无存活|

Codex原stream中42个UTF-8响应含重复、19次base64重试；重建时只用实际UTF-8正文填连续范围，五份内容逐字等于固定scope。629,091字节候选附件SHA256为 `f6550a2e32f75fcb967d308e671eb0cb78ab6461e2dc7a71ae58c67821fb025f`，其中34份完整文件逐件回核冻结副本；失败tool call为0。原结果SHA256为 `5cc1dd956c151094a217d967debcf28ceed892340010d39e8061d4a349536131`，原stream SHA256为 `9bdb87109a61a6cff65c4a2be8ee008bfe88c6fc63ea77cda869e6b6a398263a`。当前再次只读观察，同一采样PID／starttime也均未存活；该结论限于已采样身份。

公开[自身审查身份与读取投影](evidence/2026-11-12-six-stage-materials-self-review.json)SHA256为 `db4c218875622a5907735aa12487de481d52217aa4ecb9a25e4fc0e592bb182c`；其evidence字段、五scope身份、原文件清单及用量逐项匹配实际原件。原生本轮计数为input 3,083,925、其中cached input 2,858,880，output 8,847、reasoning output 4,071；缓存和reasoning不再次相加，不据此推导账单或错误独立性。该模型在冻结时收到的是检查叙述，没有自行复跑测试或读取后续最终状态文档。

已读static-r2／r3原回执：均为36文件、6个已加载秘密值、issue0，JSON与空白检查通过；两份快照分别有216／217个本地链接目标，范围不含锚点、渲染或外部URL。该轮补核时，r3逐文件快照与工作树比较仅本报告的状态更新不同，四份当时最新状态／计划文档也已读取；本报告相对文件链接均可解析。后续static-r4与最终ready身份已按下节核验，后续状态记账不借旧清单宣称新字节已经核过。

**B1精确交付终结：实现、对应行为／安装身份、实际自身模板、完整候选独立补核、普通提交／推送、精确Git／作者Ref原件及本提交自己的必要CI均已核准，两轴开放finding均为0。** 独立直接Ref的403保持；B2总预算、C原生单实例与D完整真实旅程继续开放。

## 精确Git与远端原件终核

产品提交为 `f394945db894740ad23a81c62b4ad87c85a84511`，唯一父提交为固定基线 `210f58d46c3332f4d192ee8cb13e8c149dd2173f`。协调者直接读取Git tree／blob，核变更路径恰为36份；每件Git内容、尺寸、SHA及文件模式均等于 `closure/ready-r1/files/` 原件。ready manifest SHA256为 `27dcd5a53417ccf2d3ab5440f8d735c33984731ca498e1c5e5b31e6d2b73fce3`，其中提交时的本报告SHA256为 `f38799e33d0fd65149b5f01d3ad61a22b8aa42045a1e66573106b2306e765d82`。static-r4的36文件身份也逐项等于ready，218个本地目标／6个已加载秘密值issue0。

已直接核作者commit、push、Ref三组命令、stdout／stderr及JSON回执：退出均为0，push没有force，原stdout显示基线至上述提交的普通更新；SSH `ls-remote` 原stdout将 `refs/heads/refactor/architecture-foundations` 指向同一完整SHA。这是对作者远端原件的独立核验。

协调者于2026-11-12 11:47:19 UTC仅一次直接GET官方GitHub Ref接口，返回HTTP403，原body明确为API限流；280字节body的SHA256为 `cab107d310af6137d3ca21f7de123c972a91cb1cbd91e2f58f61fe192ba31735`，GitHub Request-ID为 `C786:1BD399:1D40F49:2D1CBAE:6AF5A746`。保留该失败，不声称评审者独立远端读取成功，也未重试。

本产品提交自己的必要CI已按下节读取实际原件终核，没有借历史候选CI。上述追加为同片评审状态记账，不改变已核36份产品提交身份，不要求递归产品审查。

## 本提交自己的CI终核

协调者离线直接读取[run43211896925](https://github.com/626619403/Ergora/actions/runs/43211896925)及两个job的官方原HTML和获取回执。run页面的commit链接为完整 `f394945db894740ad23a81c62b4ad87c85a84511`，可见Status为 `Success`；三份回执均HTTP200，URL、实际body字节数与SHA逐项相符。

Ubuntu／Python3.11的job为 `131161352417`，Windows／Python3.12的job为 `131161352527`，原 `check-steps` 均为 `data-job-status="completed"`。按该提交内 `.github/workflows/portability.yml` 核七个必要步骤：

|必要步骤|Ubuntu／3.11|Windows／3.12|
|---|---|---|
|Build and install wheel|success／completed|success／completed|
|Packaged reference identity|success／completed|success／completed|
|Native application regression|success／completed|success／completed|
|Windows PowerShell 5.1 installer and upgrade|workflow条件跳过，非Linux必要步骤|success／completed|

七个实际必要步骤均有开始／完成时间、`data-job-completed`及完整绑定本提交SHA和所属job的 `data-log-url`；未把Linux按条件skipped的Windows步骤算作成功。Ubuntu回归于12:03:02 UTC完成，Windows安装／升级于11:59:34 UTC完成。`ci-terminal-r4.json` 的run、job和逐步骤汇总与这些原HTML一致。

原件body SHA256分别为：run `1b7b96ffcbd76f42dc3cddaa1fc62390e88a671234c415041deefaa1593eb747`；Ubuntu job `cf72c10a3e2c74b1710f4d98f34c74090029cc8ff2884616067cef70fb8b6293`；Windows job `7266f2928e6641d959440fe92d896639e826bbd8a70de30f23c85de10e8df6f4`。私有原件位于所属closure的 `ci-run-html-r3/`、两份 `ci-job-…-html-r1/`。

原REST403、前两份run HTML的In progress、首次取得run Success时两job尚未核验的记录，以及matrix／navigation两份404均保留原范围。终态证据来自官方HTML原件，经独立评审者离线核验；不称REST终态读取成功、评审者直接网络成功或完整日志下载。本次没有重跑产品、模型或安装检查。

两轴汇总：Standards 0项，轴内无最严重finding；Spec 0项，轴内无最严重finding。
