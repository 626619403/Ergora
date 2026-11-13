# F8-H3a 原生归档读取独立实现审查

日期：2026-11-14。审查者为新的独立实现审查上下文 `harness_archive_implementation_review`。先读原始要求、仓库约束和固定差异，再读交付叙述；未参与实现。应用仓库 `AGENTS.md`、maintainable-project-delivery 的独立审查要求和 codebase-design 的职责、Interface 深度原则，需求与维护性分别判定。

## 对象与当前判词

基线为 `322007f9c50223606d80f3d0fcdc157eac6db428`。初审覆盖 r1 的全部 13 文件：六个既有产品文件、两个既有测试文件、后端手册、H3a 计划／交付、会话接缝设计和总计划。终审覆盖 r3 的全部 18 个作者文件，另含 H2 发布／CI 的三份原记录补记及 S1 工程 Skill 计划／研究两份资料；后五份没有新增产品行为。本审查报告由审查者单独维护。

r3 manifest SHA256 为 `0243b8f5abb887f3fb386d0de03699f70aef9a6d29eb4f0754b7cf0657a08bbb`。全部 18 个冻结文件的大小／SHA 和终核时工作树逐字核准；其后只有 PLAN、H3a 计划／交付回填本次结论的三份状态变动，已经补核，其余十五文件保持原字节。精确路径、差异及审计由本片私有记录保存。

**最终 r3 需求符合性：通过，本地出口完成。** 初审三个 P2（SP1–SP3）均已修正并独立复核关闭，开放 0；初版失败和首轮模型 request-changes 保留。

**最终 r3 维护性：通过。** 无新增或开放的独立 finding。归档语义在原后端 owner，原输出 owner 先核项目归属，CLI／HTTP 共享原 Interface，网页共享原面板；没有新增会话账本、通用管理层或厂商分支。三项修正保持原职责与有限读取成本。

本片只评只读归档消费。H3b 的实际 SDK 恢复／新 prompt 续接、跨后端会话迁移、正式六阶段恢复均不作为本片缺功能，也不由本片关闭。

## 初审 finding 与修正复核

### SP1 · P2 · 已关闭：首次打开绝对路径会跟随中间祖先链接

位置：r1 `src/ergora/agent_backends.py:414`。

`directory(None, protocol.parent)` 一次打开绝对路径；`O_NOFOLLOW` 只约束最后一个路径组件。已解析并保存的 State 根或更上层目录之后若被移动并换成链接，`runs` 尾组件仍为普通目录，identity 的 home、header cwd 也仍可与保存字符串一致。独立 r1 安装版探针将生成的 State 根移走并用链接替代，实际返回 `available: true` 和原字节。它没有满足逐级非链接、原 canonical 路径的合同。

最小修正：在原后端内部从固定根沿每个路径组件用目录 fd／`O_NOFOLLOW` 打开，读取后核路径仍指向打开的目录。无需改变 State、上层消费者或新增路径管理模块。

r3 复核关闭：`src/ergora/agent_backends.py:423` 起沿每个路径组件打开并保留原路径 inode 复核。独立原场景在实际安装版由错误接受变为 `NotADirectoryError`，正常归档重建保持。

### SP2 · P2 · 已关闭：枚举后新增存储代次或另一会话未使读取失败

位置：r1 `src/ergora/agent_backends.py:428`、`src/ergora/agent_backends.py:465`。

三个目录只在读取前有限枚举，最后只比较目录 inode。读取开始后新增 `session.v4.1.jsonl`、第二 session 或第二 namespace，不改变既有目录 inode 和原文件 stat；响应仍把布局当成受支持的单会话原 v4。独立探针在首行读取后分别加入三种目录项，三次均被 r1 接受。

最小修正：保留原 2／2／3 项上限，在本次读取结束时重新核同三个实际枚举目录的布局。不要把全局祖先目录的时间变化变成无关拒绝条件；仅靠目录时间／size 在当前实测文件系统上也不足以发现同一秒内的小变更。

r3 复核关闭：本地 `listing` 保存三处实际布局，`src/ergora/agent_backends.py:479` 起按相同上限重枚举比较集合。独立在首行读取后新增 generation／第二 session／第二 namespace 的三例均拒绝；首修仅用目录 stat 的两例失败保留。

### SP3 · P2 · 已关闭：关窗后的迟到成功或错误没有完整忽略

位置：r1 `src/ergora/data/console/agents.js:19`；既有 `src/ergora/data/console/ui.js:160`的 modal 关闭语义。

`dialog.close()` 不卸载内容，所以只关窗而未打开另一面板时，`view.isConnected` 仍为真，迟到成功仍写旧 DOM。更直接的可见问题是 HTTP 失败在成功路径的连接检查之前抛出；旧窗口已关闭或内容已替换时，统一事件 handler 仍弹出全局错误。独立受控 DOM 生命周期模型使用精确安装版的原 `agents/ui/api` 模块，验证了上述三种情况及活动窗口成功／错误对照。此复现不是实际浏览器验收；源码的关闭和错误传播路径亦直接支持结论。

最小修正：在本地历史面板同时核连接状态和所属 modal 的打开状态，成功及异常路径都忽略已关闭／替换的请求；活动窗口仍走原错误提示。补验仅关窗的迟到成功，以及关闭／替换后的迟到失败。无需改全局 modal 或引入通用生命周期层。

r3 复核关闭：`src/ergora/data/console/agents.js:12` 的本地 `displayed` 同核 connected 和最近 dialog.open，成功、catch、finally 共用该判断。原独立模型复现已转绿；实际安装 HTTP＋浏览器 closed／replaced／active × 成功／失败六组合逐项通过，只有活动成功更新正文，只有活动错误弹提示。

## 职责、控制流与测试审查

| 新增或扩展处 | 实际消费者与职责判断 |
| --- | --- |
| `AgentBackend.archived_history`／DeepSeek 实现 | 真实生产调用者为 `agent_runs.output`。它是既有可替换后端 Interface 的扩展；默认明确不支持，原生格式和普通文件／身份规则集中在对应 Adapter，没有上层厂商判别。 |
| 后端内 `directory`／`ordinary`／`stamp`／`listing` | 私有文件遍历、资源回收和物理观察算法，留在固定归档 owner 内有具体职责理由；不需要靠虚构跨文件调用证明复用。原 SP1／SP2 缺口已在同一 owner 内修正。 |
| `agent_runs.output` | 原 SELECT 先核 project/run 归属，再接收页参数；offset／limit／revision 检查属于该外部 Interface。原默认 stdout／stderr 分支保持，历史读取不调用运行、认证、SDK、结果解析或保存 owner。 |
| CLI 参数／HTTP `agent_output` | 仅把显式请求交给同一输出 Interface；没有第二套读取或调度路径。 |
| 网页 `archivedHistory`／`read`／`displayed` | `outputPanels` 由 Agent 调用结果与 overview 记录两个真实消费者使用。页状态留在面板，当前页替换、文本渲染、在途禁按钮合理；`displayed` 集中相同窗口生命周期判断，原 SP3 已关闭。 |
| 两个测试文件 | 字节重建、跨页变化、身份错配、未来代次／链接／FIFO、HTTP／CLI 同页与跨项目拒绝均保护可达的静默误读风险。复用了既有 suite，未新增纯粹镜像实现的测试框架。 |

其他 guard 有实际输入或生命周期原因：平台限制避免宣称未知平台可用；身份和首行各限 16 KiB；有界目录枚举拒绝歧义；普通文件与非阻塞打开避免 FIFO／设备行为；精确 home／ID／cwd 和整数版本保护原记录身份；严格 UTF-8 防止声称 replacement 解码仍逐字一致；revision 与前后文件 stat 防止跨观察拼页；缺非零页 revision 和越界 offset 在原输出 Interface 可达。未要求对旧格式／不支持后端创造空历史或启动 SDK 探测。没有发现需要删除的独立冗余 guard。

页面读取量随页限有界，身份、首行、目录枚举及原 stdout／stderr 也各有固定上限；没有为摘要遍历整个历史或材料树。revision 明确是物理文件观察标识，`writer_state` 为 unconfirmed；末尾和 `complete` 仅涉及本次观察字节，不改原 run 状态或声称 writer 已停止。

## 初审证据与限度

- 独立核准 r1 的 13 文件冻结快照，另核 noneditable 的 551 产品在构建源码／wheel／安装版逐字一致、两份 RECORD（559／564 行）及 283 冻结文件；未重装环境。
- 读取实际安装回归 stdout：四个 suite 收集 57 项并全部通过，pytest 31.27 秒。源码环境缺可选 Web 栈的 skip 没有被当作 HTTP 通过。
- 独立离线重建两个真实 H2 的全部原分页，10／6 页、151,777／97,424B 与当前原归档逐字一致，并用只读 SQLite 核保存状态。原运行脚本另在每次读取前后断言保存 run document 不变；本审查没有把当前状态比较冒充历史前后快照。
- 独立 r1 安装版小型探针核 4／5／7／4,093／65,536B 页限下多字节逐字重建，并复现 SP1／SP2；所有写入限于本片私有生成 fixture。
- 核已有真实安装版 HTTP＋浏览器分页、追加后 400／从头、文本渲染及当前页 DOM 的脚本与原件。其迟到成功测试关窗后立即新开面板，不能替代 SP3 的关闭／迟到失败补验。
- 只读核五个零 prompt 副本探针的原件审计及其限度；SDK 恢复仍会写种子，因此不能拿它作为 H3a 读取实现。原件未被本审查恢复或修改。

## r3 最终证据与范围

- 独立核完整 18 文件快照及所有修正。r3 noneditable wheel SHA256 `16118b3afb3aa44a2fa15d650ec9f71acfc50c1329f4a766ec373686ce2f6a62`；551 产品在构建源码／wheel／安装版逐字一致，两 RECORD 559／564 行及 283 冻结文件重新核准。九个源码／测试／手册 overlay 与最终快照一致。
- 原四 suite 的 r3 实际 stdout 为 60 项全过，pytest 31.45 秒；新增三个回归由实际 red 转绿。独立在已安装 r3 重跑 SP1／SP2 的四种原失败场景并核 4／5／7／4,093／65,536B UTF-8 重建；未为已通过的 suite 重复全量运行。
- 独立再次重建两个 H2 真实归档的 r3 全部分页，10／6 页及原完整 SHA 保持。归档不依赖 native-result 的本轮事件区间，保存 run 状态仍由原记录返回；无新增调用、批准或状态写入路径。
- 独立离线核 r1／r3 真实浏览器回复的全部初始页面、字节游标和摘要，以及当前 fixture 恰为原文加指定追加字节。r3 分页 2.928 秒、追加后 400／重读 2.397 秒、六生命周期组合 4.998 秒通过；脚本实际转发 HTTP200／400，没有伪造产品成功回复。早期 socket 路径及固定 pre 个数的驱动失败保留，不作为产品通过。
- 新自身原结构模板调用 65.875 秒返回 approve。独立核原 input digest、prompt＝实际 stdin、11 份完整文件共 215,436B、三份完整继承资源及原安装定义逐字一致，核结果原件与 SHA。最终全部产品／测试／手册与该调用所审文件一致；两份后补计划／交付只增加状态和原件记账，由本次完整终审覆盖。模型判词不冒充独立执行测试或理解程度证明。
- 独立核七个保存 PID／starttime 的当前终态、两个受控端口不在监听表、两张 r3 截图的大小／SHA。此结论只覆盖保存的观察身份，不扩大为全局进程隔离。
- H2 三份追加记录与原独立发布／CI 审计的精确候选、原件身份和范围一致；它们属于 H2 的完成记录，不是 H3a 自己的 CI。S1 两份资料明确是下一片设计，优先复用父资源继承和既有角色，尚未接入；没有借本片关闭 S1 或真实外部 workload 验收。

需求轴历史共 3 项 P2，全部关闭，最终开放 0；维护性轴新增／开放 0。本地出口通过。[交付记录](2026-11-14-harness-session-readback.md)、本片计划和总计划已回填本次状态；后续分别核 H3a 的普通 Git 发布与其自己的远端 CI，本报告不宣称两者已经完成。

本审查没有运行昂贵模型、SDK、安装、外部网络或业务项目操作。精确命令、模块 SHA、独立复现与原件审计保存在本片私有 `independent-review-r1`。归档观察不提供任意同大小原地改写的内容认证，不证明 writer 已停；六阶段、candidate／approval、unknown、预算、进程 owner 和 283 冻结参考的原归属保持。H3b 另片。

## 同片普通发布补核

2026-11-14，独立核准提交 `560bfdfab1b48486f71b0677a5f5113923d7ad30`，唯一父提交为 `322007f9c50223606d80f3d0fcdc157eac6db428`。直接读取 commit／blob 原对象并重算 Git 身份，19 条实际变更路径、字节数及 SHA 与发布清单一致；十八作者文件也与上述终核及三份状态补记一致。提交中的本报告 SHA256 为 `645b1a8b9d0b47737c2584d114423e918820623a328dbf1ba5fe5c940f596b12`；其后两处状态句校正和本附录只补记审查／发布进度，原判词和产品证据未变。

从该精确 Git 提交读取全部 551 个产品 blob，完整集合和原字节与已测 r3 构建源、wheel、安装版一致；wheel SHA、两 RECORD 559／564 行及 283 冻结文件重新核准。没有取后续 S1 工作树作为本片源码，没有重新安装或运行模型／测试。

作者普通 push 原回执退出 0／5.679 秒，目标为现开发分支，无 force；其后 SSH `ls-remote` 原回执退出 0／1.301 秒，将完整 `refs/heads/refactor/architecture-foundations` 解析为同一 `560bfdfab1b48486f71b0677a5f5113923d7ad30`。本审查仅核保存的原件，没有自行发网络请求。

私有 `independent-review-r1/publication-audit.json` 保存精确 Git、包与原回执核查，SHA256 为 `90f4421ab206bfcba3904a1debee613a226cfb42a629142296e673387c1014bb`。普通发布补核通过，新增发现 0，需求／维护性开放 0／0；H3a 自己的 CI 仍待终态原件，不借 H2 或其他候选关闭。实际续接 H3b、完整 C2 与真实 B3 的范围保持。

## 同片自己的 CI 终态补核

2026-11-14，独立从官方原 HTML 核准本片精确提交 `560bfdfab1b48486f71b0677a5f5113923d7ad30` 的 [CI `43481386288`](https://github.com/626619403/Ergora/actions/runs/43481386288)：第五份 run HTML 为 Success，八个 job 均 completed 且原页标为 succeeded。workflow 和六个 Linux 分组直接读取该提交的 Git 对象，导出必要步骤数为 1＋6×4＋5＝30，未使用后续 S1 工作树源码。

| 原 job 范围 | job 数 | 必要步骤及终态 | 原步骤耗时 |
| --- | --- | --- | --- |
| plan | 1 | 读取显式测试分组，1 项 success | 1 秒 |
| Linux Python 3.11，group 0–5 | 6 | 每组构建安装、包内参考身份、应用回归、上传观察，24 项 success | 应用回归 165–256 秒 |
| Windows Python 3.12，group all | 1 | 同四项及 PowerShell 5.1 安装升级，5 项 success | 应用回归 899 秒；安装升级 56 秒 |

独立 HTMLParser 逐项核全部 30 个必要步骤的 success、job-completed 标记和 UTC 起止时间；每项原日志路径非空且唯一，均含完整候选 SHA、对应 job ID 和 step 编号。上述耗时由原起止时间计算；Windows 回归为 UTC 18:19:51–18:34:50，PowerShell 为 18:34:50–18:35:46。独立提取结果与作者最终观察投影逐字一致；本结论没有声称读取全部日志正文或下载上传产物。

离线核准 20 份原 HTTP 资料：19 份 HTML（九份最终页面、十份历史页面）和一份原生 job-batch JSON，逐件重算正文大小／SHA、回执 SHA 并核 URL、最终 URL 与 HTTP200。run 原页中的实际 batch 地址、八个原生 job 的 ID／名称／链接、总数和无后续批次标记与原 metadata 一致。该早期 batch 仍是 plan 完成、其余七个 job 在途；首四份 run、首四份 Windows 及 Linux group 0／1 的初次在途页面也保持原状态，未被回写为成功。

再次从精确 Git 对象核 19 条变更身份、551 个产品与已测 r3 构建源／wheel／安装版逐字一致，两 RECORD 559／564 行与 283 冻结文件保持。私有 `independent-review-r1/ci-terminal-audit.json` 保存完整独立核验，SHA256 为 `6b08fef05572bd3f57ebd306ab8a088478524f09ba84a1e1bbbc77fd235aeffd`。本次仅审计保存的原件和 Git／包字节，没有网络请求、完整日志／产物归档下载、模型／SDK 调用、安装或测试重跑。

本片自己的 CI 终态补核通过，新增发现 0，需求／维护性开放 0／0；连同本地出口和普通发布补核，H3a 只读归档消费的精确交付完成。实际会话续接 H3b、完整原生准入 C2 和真实工作负载 B3 继续开放。
