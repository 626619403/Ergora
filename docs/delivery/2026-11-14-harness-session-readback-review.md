# F8-H3a 原生归档读取独立实现审查

日期：2026-11-14。审查者为新的独立实现审查上下文 `harness_archive_implementation_review`。先读原始要求、仓库约束和固定差异，再读交付叙述；未参与实现。应用仓库 `AGENTS.md`、maintainable-project-delivery 的独立审查要求和 codebase-design 的职责、Interface 深度原则，需求与维护性分别判定。

## 对象与当前判词

基线为 `322007f9c50223606d80f3d0fcdc157eac6db428`。初审覆盖 r1 的全部 13 文件：六个既有产品文件、两个既有测试文件、后端手册、H3a 计划／交付、会话接缝设计和总计划。终审覆盖 r3 的全部 18 个作者文件，另含 H2 发布／CI 的三份原记录补记及 S1 工程 Skill 计划／研究两份资料；后五份没有新增产品行为。本审查报告由审查者单独维护。

r3 manifest SHA256 为 `0243b8f5abb887f3fb386d0de03699f70aef9a6d29eb4f0754b7cf0657a08bbb`。全部 18 个冻结文件的大小／SHA 和当前工作树逐字核准；精确路径、差异及审计由本片私有记录保存。

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

需求轴历史共 3 项 P2，全部关闭，最终开放 0；维护性轴新增／开放 0。本地出口通过。后续仅需在[交付记录](2026-11-14-harness-session-readback.md)和总计划回填本次状态，再分别核 H3a 的普通 Git 发布与其自己的远端 CI；本报告不宣称两者已经完成。

本审查没有运行昂贵模型、SDK、安装、外部网络或业务项目操作。精确命令、模块 SHA、独立复现与原件审计保存在本片私有 `independent-review-r1`。归档观察不提供任意同大小原地改写的内容认证，不证明 writer 已停；六阶段、candidate／approval、unknown、预算、进程 owner 和 283 冻结参考的原归属保持。H3b 另片。
