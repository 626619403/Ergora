# Q4.2a1：只读训练启动检查独立评审

日期：2026-11-15。评审者：Codex fresh-context 独立 reviewer，任务 `training_start_admission_audit`。先读取原合同与实际差异，再核实现、邻接调用和原始验证材料；未接收作者实现会话或预定 verdict。只写本报告。

|评审轴|结论|适用范围|
|---|---|---|
|需求符合性|approve|下述固定快照的只读启动检查、本地安装与验收记录。|
|可维护性|approve|行为归原 submission owner，应用层守项目身份，CLI 解析和映射退出码；没有新增运行状态权威或复制准入实现。|

**实证 finding：0；阻塞 0；开放 0／0。** 未发现需要代码修正的可达缺陷或冗余检查。本结论限于 Q4.2a1；固定发布、完整远端 Ref、自己的适用 CI 及发布后补核仍待完成，不能据本报告把整个 A4 或后续自动循环标为交付闭合。

**固定身份与范围。** Git 基线及本片读取时 HEAD 均为 `5a3e3b2a96c92632a65e60e87bcfc8713eff41e9`，分支 `refactor/architecture-foundations`。精确待审材料为 `.ergora/checks/training-start-admission/review-scope-r2/` 下的 `scope.json`、`author-diff.patch` 和 `files/`；清单 SHA-256 为 `a94f3ffa51c56956ddd6124073bfb3474fca8fed548bbc9579a008a70022577b`，diff SHA-256 为 `544c3c43b074716f6f5b7d43e61e1ed304cad6a2b861e7e3a3cdd927f22dd96d`。13 个完整文件的字节数／SHA、16 份列入证据的字节数／SHA 全部直接匹配；核对时当前 13 路径与快照一致，当前这些路径的 tracked diff 也逐字同原 patch。

|产品／测试文件|字节数|SHA-256|
|---|---|---|
|`src/ergora/cli.py`|93,667|`a33bbb070f90abe363069bde7f70c39ff15b9409fcf89c76110d9951dd0cf376`|
|`src/ergora/reference_training_submission.py`|17,960|`99a758f6235183632f909dfe15fe34fc2527980f5801dc39395375f5a4b4d7a8`|
|`src/ergora/training.py`|17,996|`017560f26589e307416eb6be0f487c11cae38569f13502f58ae448e32496bed7`|
|`tests/test_training_submission.py`|17,040|`131bfdf0b717244b39b31f0a83dcd1f9e659459cc4197a22d5fdb701596c7142`|

其余九文档为 `docs/PLAN.md`、`docs/TRAINING.md`，`docs/plans/` 下的 `2026-11-15-training-start-admission.md`、`2026-11-15-bounded-training-cycles.md`、`2026-11-15-domain-review-optimization-quality.md`，以及 `docs/delivery/` 下的 `2026-11-15-training-start-admission.md`、`2026-11-15-bounded-training-cycles.md`、`2026-11-15-bounded-training-cycles-plan-review.md`、`2026-11-15-complete-review-reports.md`。完整身份见上述清单，包含未跟踪文档的完整字节。

审查期间另出现的 `docs/plans/2026-11-15-training-cycle-selection.md` 以及前片原 reviewer 对其报告的追加均排除。本片只核前片引用的归属和措辞，不代认证其 CI，也不把纯 Q4.2 计划评审作为本实现证据。

收尾时 `docs/PLAN.md` 和前片 `2026-11-15-complete-review-reports.md` 又同步了前片 CI 终态；已逐项与冻结快照比较，变化限于前片完成状态及其原终核引用，其余11路径仍同快照。本报告不重新认证这些后补 CI 事实，评审身份仍为上述冻结13路径。

**合同与实际调用。** 以[本片合同](../plans/2026-11-15-training-start-admission.md)为准，核对结果如下。源码行号相对上述固定快照。

|可观察要求|直接证据与判断|
|---|---|
|选择完整 manifest SHA，拒绝项目修订混读|`training.py:113–122` 在应用入口核完整小写 SHA-256，冻结所读 project，经原进程检查后重新读取 revision；发生实际 revision 变化则拒绝。原 owner 第238–240行比较所选 SHA 与原观察／原 intent 的绑定。|
|无原投递意图时复用完整原准入，返回完整观察及 true|`reference_training_submission.py:234–245` 先 `load()`，无意图直接调用已有 `preflight()`。第51–78行仍拥有当前注册、baseline、runner／walltime、已有 job／fence／negative result、Git 根／完整 commit、comparator 等检查；返回整个原观察，没有另写筛选器。|
|已有 prepared／unknown／submitted／rejected 时只读原事实及 false|同一分支存在 intent 时不调用 preflight，SHA 取自 intent，再调用原 `status(intent)`；`observation=null`、`ready_for_new_start=false`。原注册身份核验及 checkpoint 一致性校验保持，没有以当前 runner 或 baseline 重新授予启动许可。|
|无需 SDK、服务、密钥、模型或训练|`reference.py:382–387` 仅 dispatch／resume 需要 SDK；第412–436行复用原受控子进程。submission 主入口第292–293行仅 dispatch／resume 读取运行连接环境。check 在建立锁／创建 intent 的第248行前返回，没有到达 dispatch／reconcile。实际无 SDK 安装和 CLI 证据亦与此一致。|
|退出码和平台范围|`cli.py:619–628,1196–1197,1226–1228` 保留薄解析、JSON 输出和 readiness 的 0／1 映射；错误沿原统一处理退出2。`reference.py` 相对基线未改，check 沿原非 status 操作的 Linux／WSL2 gate，Windows 历史 status 的原路径保持。|
|原 start／恢复义务不变|实际 diff 未改原 prepare／dispatch／resume 逻辑。第182–186行保留两次最终 preflight 和 attempt-before-send；第214–227、278–282行仍在已有 attempt 后按原 history／memo 对账。没有新增重发、批准、候选生成或自动轮询。|

结果中的 `read_only=true`、`execution_authorized=false` 和 `runtime_status=not_queried` 与真实路径一致。检查仍是顺序观察；并发参与者可在读取之后发布 intent 或改变原文件，因此 true 不表示预留或服务上没有旧 run，后续 start 必须沿原检查。[手册](../TRAINING.md)和合同明确保留了这一边界。项目注册／执行位置漂移后的旧运行恢复能力也仍属后继节点。

Kernel 专家保留可直接核对 `data/presets/workflows/ergora-training-proposal-v3/workflow.json:81`、原 bottleneck skill 的第14行及 preset catalog 的 `training-optimization-v3`；本片未改变这些产品字节。

**结构、性能和测试价值。** 新增的唯一生产函数 `training.check_start` 的当前生产调用者是 CLI；它是应用用例入口，集中持有项目读取、完整 SHA 输入和 revision 漂移约束，不需要为满足复用数量而另造模块或 ABC。计划中的有限选择不是已经存在的调用者。真正的准入、intent／checkpoint 身份及状态聚合继续由原 `_Submission` 隐藏，CLI 不复制它们。

新增 guard 分别保护明确的外部身份输入和实际并发修订变化；无 intent／有 intent 分支对应真实生命周期，已有意图还复用原持久一致性检查。没有新增 speculative fallback、重复 runner 校验器或另一套状态机。`run()` 与 preflight 中的注册核验沿原结构保留。

每次 check 只进入一次原有子进程入口，成本来自原完整参考安装／注册／记录身份核验及 Git 读取；没有新增服务请求或循环。完整观察会随合法原材料大小增长，后续 a2 的总容量／存储义务仍单列。这里没有加速、吞吐或 GPU 性能主张；测试耗时不能当作准入延迟基准。

两项新增测试保护真实接缝：无 SDK 准入与 CLI／原文件／DB 保持，及进程观察后的实际 revision 更新和原 runner 准入失败。四种原投递状态的断言加在已有服务替身／恢复测试中，原调用计数仍保护不重发；没有新建重复测试文件或 CI job，原显式 CI 分组已包含该文件。未发现只为固定默认值、文案或实现细节增加的测试矩阵。

**直接核对的验收原件。** 下列检查均读取实际文件或执行最小本地接缝，没有用汇总中的成功布尔值代替原件。

- r2 wheel SHA 为 `cbe1c14efbb577810585db94d696a03f14f0c2f6e3c30ebcae135b85203ca495`。独立读取 wheel zip、源码和两个实际 site-packages，643 产品文件的路径／完整字节全部相同；与 Git 基线相比只改三个产品模块，无新增／删除。两安装的 `direct_url.json` 均指向这个 wheel，无 editable 标记；两解释器实际隔离导入各自 site-packages。core 实际 `find_spec('temporalio') is None`，SDK 安装版本为1.34.0。两套各283参考文件均逐一匹配原 manifest 摘要。
- 原源码 r1 XML 确为2项、1通过／1失败，失败源于测试对不存在的 SQL revision 列写入；r2 已改为更新 project JSON 内 revision，原 r2 XML 为2通过，stdout 为1.63秒。未把原测试注入失败描述为产品修复。
- 安装 XML 的四类分别为 training 13、submission 15、runtime 15、cancellation 11，共54项，failure／error／skip均0，XML209.514秒；原 stdout 为54通过／210.12秒，stderr为空。其服务行为来自真实 SDK 协议的本地替身，未升级为真实 Temporal 服务验收。本 reviewer 没有重跑该210秒套件。
- 原实际旅程驱动确实调用 registration、baseline、runner、preview／prepare 的原 owner，runner 命令设置为一旦误执行就失败。三条 CLI 原 stdout／stderr 摘要与清单相同：两次正确 SHA exit0，完整6164B JSON逐字相同，SHA均为 `040b446d0c571e173e96de23589aee6c661bd812537a5d82d0d6343f8218204f`；错 SHA exit2。before／after文件逐字相同，SHA均为 `a3ce907637fd7ccf2ec07c6773b0cee51719c2388576e62d092d0accc8ef1478`。又将当前42原文件及只读打开的完整88行 DB dump 与原 before 比较，仍一致。模型／workflow／runner 为0的主张与驱动调用路径及原始记录相符；这是合成 CPU 合同的本地准入。
- 自身原结构模板的17份完整文件共354,253B，逐一核字节／SHA及 task 中的完整文件块；3份祖先资源均完整进入 prompt。`inspect_input` 实际验证 digest 为 `7410a4ffb74719935172a7a8838ef28986a4d41820a7ac69f426819c735cc615`。冻结 prompt、真实 stdin 和 protocol prompt逐字相同；原模板／Agent定义及资源与当前安装的原 preset 对应。run `343bb89a50284f6eb6be2b1cdd51fd8b` 的 DB 行与原 native stdout 相同，实际 Codex事件流含完整原回复；protocol回复与归一 result 的 JSON 值相同，归一 result逐字同 original-result，SHA为 `b288266e1697ae3360c4fcc8792a6e142c2c055b9493f13b36f44d2626a9163b`。驱动记录43.254秒／approve；实际 binding是授权的Codex回退，未冒称Claude成功。该模型明确仅审所给材料，未认证私有运行或 CI。
- 自身模型输入的产品、测试、手册与本次最终快照一致；后补计划／交付是实际验证状态。总体循环计划另有一句“无法确认停止时报告未确认”的措辞精化。计划 reviewer 的历史 SHA 与结论保持原归属；当前九文档没有把计划 approval扩为本实现或自动循环验收。九文档的211个本地文件链接缺失0，行尾空白0，`git diff --check`通过。

**Reviewer 自行执行的最小复核。** 用最终 SDK 安装解释器，以 `-I -B -m pytest -q -p no:cacheprovider` 运行原文件中两项新增测试，结果2通过／1.29秒。无安装或新增测试文件。

另在自动清理的临时目录复用原 `registration`、`experiments`、`prepared` fixture，原 prepare 创建本地 intent，原 checkpoint 构造器生成四种本地状态。随后移除当前 runner 并改变 baseline，用真正无 SDK 的 core 安装执行8次实际 `check-start`：四种状态正确 SHA 均 exit1、完整 submission 与原 status 相同、observation为null；各自错 SHA 均 exit2。每次读取前后原 config／runtime／repo 文件及完整 DB dump保持。该隔离复核验证已有意图不重新准入和 CLI退出码；synthetic checkpoint不作为远端提交或真实恢复证明。

已读根／源码／测试 AGENTS、[组件协议](../architecture/component-change-protocols.md)，以及 maintainable-project-delivery 的 independent-review、ergora-codebase-quality 的 repository-style／module-design／test-seams 参考。按项目现有 pyproject 和显式 CI 分组选择检查，没有套用外部框架的格式或测试规则。

本次实际环境为 Linux；未实际验证 WSL2 或 Windows，也未跑全套回归、模型、训练、GPU、profiler、真实服务、安装、提交或推送。未认证前片的发布／CI；未验收后继有限选择、提交前 fence、全生命周期停止、跨恢复预算或自动循环。上述边界不改变本片固定快照的本地两轴结论，后续发布和每个实现片分别提供自己的证据。

## 固定发布与本片自己的 CI 终核

日期：2026-11-15；由本片原 fresh-context reviewer 延续固定发布核对。原12,584B报告前缀及 SHA-256 `61daea268894558530ecc013a6b53937c742960ec5361c94d85d0531862039a2` 保持，原件另存本片 ignored 检查目录的 `ci/reviewer-fixed-r1/original-review.md`。以下只认证固定 Git 对象，不以正在推进 a2 的工作树替代本候选。

已独立核固定提交 `d3c90e751ee9257df36b74e57e8956d38bbde848`，parent 为 `5a3e3b2a96c92632a65e60e87bcfc8713eff41e9`，tree 为 `66828b6a6e47e949ff025980fe04d71e10ac2f1b`。与 parent 的15路径恰为原13路径、本报告和前片原报告的终核追加；全部 Git blob、字节数和 SHA 与实际发布清单相符。产品／测试／训练手册与本片冻结快照逐字相同；四份后补计划／交付差异只记录已验证的本地审查和前片终态，未扩大本片行为。a2 设计不在该提交。

又直接从此固定 Git 读取全部643产品 blob，与原 r2 wheel及两个实际非editable安装逐字比较，三者相同；283参考文件逐一匹配原 manifest。wheel SHA仍为 `cbe1c14efbb577810585db94d696a03f14f0c2f6e3c30ebcae135b85203ca495`。原发布／push日志与远端记录保持；独立匿名 GitHub commit API 和完整 branch-ref API 均HTTP200，parent／tree及 `refs/heads/refactor/architecture-foundations` 的完整SHA与本固定候选一致。未重跑安装、模型或全套测试。

本候选自己的 [Portability run 43644626885](https://github.com/626619403/Ergora/actions/runs/43644626885) 为 push／attempt1，head SHA精确绑定上述 `d3c90e7`，workflow为固定提交的 `.github/workflows/portability.yml`。2026-11-14 21:49:37 UTC 首次独立观察仍为 `in_progress`／conclusion=null：plan已成功，六个Linux分组及Windows任务仍在运行，共8 job。该观察及HTTP200官方run页面完整保存在 `ci/reviewer-initial-r1/`；它没有借用前片的run或结论。

固定发布复核保持需求／维护性两轴approve，新增finding 0。此时尚有一个交付开放项：本候选自己的CI终态及实际必要步骤，当前不称本片精确交付闭合。后续有界观察和终态另追加，保留本次在途原件。

2026-11-14 21:55:34 UTC 的独立API观察中，plan及六个Linux分组全部成功，Windows仍在回归阶段；按固定workflow列出的30个必要步骤已有28个成功，剩余Windows回归及PowerShell5.1安装升级。22:03:19 UTC 的HTTP200官方Windows job页仍显示同一回归运行中，安装升级未开始，没有失败结论。后续先观察该官方job页，结束后再核整次run／全部job；本轮观察最晚至22:18 UTC，覆盖固定workflow中Windows job的30分钟时限，若届时仍无可核终态则保持开放项。API／官方页的各次完整响应和请求时间分别保留在本片 `ci/reviewer-observe-r2` 至 `r6`、`ci/reviewer-windows-*`，没有触发重跑或改变远端状态。

**终态补核：需求符合性 approve／可维护性 approve，新增 finding 0，开放0／0。** 2026-11-14 22:14:02 UTC 的独立匿名API与官方run页均已核本候选自己的 `43644626885 / attempt1` 为 `completed / success`；head SHA、push事件、branch及workflow均与固定候选相同。最终完整远端 `refs/heads/refactor/architecture-foundations` 仍为 `d3c90e751ee9257df36b74e57e8956d38bbde848`。该结论关闭的是本片固定发布／自己的CI开放项，不转授后继 a2。

|本候选实际 job|原 job ID|终态|适用必要步骤|
|---|---|---|---|
|plan|132599526918|success|1／1|
|Linux 3.11 group 0|132599561826|success|4／4|
|Linux 3.11 group 1|132599561813|success|4／4|
|Linux 3.11 group 2|132599561814|success|4／4|
|Linux 3.11 group 3|132599561819|success|4／4|
|Linux 3.11 group 4|132599561837|success|4／4|
|Linux 3.11 group 5|132599561822|success|4／4|
|Windows 3.12 group all|132599561848|success|5／5|

30个适用必要步骤为：1次 `Read explicit test groups`，七个native job各自的 `Run actions/setup-python@v5`、`Build and install wheel`、`Packaged reference identity`、`Native application regression` 共28次，以及Windows的 `Windows PowerShell 5.1 installer and upgrade` 1次。逐项核API中的名称、状态和结论，并对照八份HTTP200官方job页的实际 `check-step` 名称、序号、成功结论及完成时间，30项全部一致。八job身份与attempt全部对应本run，没有缺job或用此前run替代。Linux的Windows专用步骤按原条件跳过，未计入适用30项；适用必要步骤无失败、取消或跳过。

Windows原生回归于22:11:36 UTC成功，PowerShell5.1安装升级于22:12:34 UTC成功。22:12:04 UTC曾保留29／30、run仍在途的观察；最后一项和整次run确认成功后才关闭门槛。该Windows回归结论保持原历史读取支持范围，未把新的check-start宣称为Windows原生准入。

终核原件在本片ignored目录的 `ci/reviewer-terminal-r1/`，含run／jobs API、官方run页、八job页及最终远端ref；每次请求均保留完整响应、HTTP状态、请求时间、字节数和SHA。全部有界观察合计50次匿名只读GET，均HTTP200，原始响应身份逐项核过；未认证前片CI，未重新安装或运行模型／训练／本地全套。原检查清单收录150件／6,050,561B，含固定Git核验、观察原文及采集器。

完整独立终核记录为 `ci/reviewer-ci-terminal-r1.json`，67,280B，SHA-256 `380cfa8a4aa9cae0515c2552a1226a5e04f587b6638f11df8846e0c59905787e`；其150件清单不包含该汇总自身。记录绑定固定commit／parent／tree、15blob与r2包身份、原报告前缀、30适用必要步骤、八官方job页及50次原始GET，无身份或状态冲突。原12,584B报告前缀及最初在途记录保持。Q4.2a1本固定候选的精确交付门槛已闭合；a2及后继预算／停止／自动循环继续按各自范围独立验收。
