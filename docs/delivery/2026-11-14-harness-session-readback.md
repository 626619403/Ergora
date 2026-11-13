# F8-H3a 历史与恢复交付记录

日期：2026-11-14。按[本片计划](../plans/2026-11-14-harness-session-readback.md)从已推送 `322007f` 推进；隔离探针已审计，归档读取正在实现，尚无产品会话续接实现。

固定源码的 SDK `resume_session` 会恢复原生会话，不提交新 prompt；它不是无写历史读取。原 server 调用模型选择，只有路由变化才追加选择事件；原 agent-loop 会补种子标记并修复中断末轮。完整原生历史、原 `native-result` 的本轮事件和 Ergora 调用结果分别核查，不能用归档的旧完成结果当新响应。

两份真实原生文件的只读初查、五副本原件链和[接缝设计](../architecture/2026-11-14-harness-session-seam.md)已完成。原模型回执保持，副本探针只用显式 loopback 和假凭据。产品实现、验证及新独立审查均未提前关闭。

## 副本探针初验

固定 SDK／runtime 的五个零 prompt 场景已结束：两个真实成功会话副本各自恢复原 ID；缺失 ID 拒绝、原副本字节未变；并发第二个 runtime 的恢复被原锁拒绝；传入不同 cwd 仍恢复成功并返回原历史 cwd。最后一点说明应用需要核自己冻结的目录，而不能把 SDK 成功当目录合同通过。

四个成功恢复的副本均只追加 68B `session/end-seed`，原完整字节前缀保持；同一模型路由没有追加 `model/selection`，五个通知列表均空。没有通知不表示没有写入。五例总模型 HTTP 为零，只有显式假凭据和 loopback 路由，无 MCP 插件；这不同于生产绑定的正式续接。原两份 home 在各例前后逐字保持；按 PID／starttime 观察的 11 个进程均无存活。前两例分别 5.431／3.978 秒，缺失 1.069 秒、不同 cwd 5.078 秒、占用 9.649 秒。私有 `audit-r1.json` 核原件链通过，未关闭 H3。

## 归档读取实现中

六个既有产品文件扩展原后端／output／CLI／HTTP及两处网页消费者；没有新增 schema、数据表或会话模块。归档只读 canonical 未压缩 `session.v4.jsonl`，identity 和首行各限 16 KiB，页面 4–65,536B，逐页保留 UTF-8 边界。revision 绑定原调用、identity 和文件 stat，是本地观察标记，不是全文内容 SHA，也不证明 writer 已停止。文件改变、身份不符、路径替换、符号链接或未来代次明确拒绝；其他后端显示不支持。

网页仅用户点击才读取，页面替换而不累积整历史 DOM；保留原 stdout／stderr 行为。

## 回归与实际消费者

- 源码定向检查：17 通过／1 个可选 Web 模块跳过，系统解释器未装该可选栈；下面独立安装版另验真实 CLI／HTTP 路径。JavaScript 语法与 `git diff --check` 通过。
- 新 Python 3.11 noneditable wheel：SHA `a5d58b1710c7bebfbe6686dcf558bb74f8aaa463c437672fb07a606fbbf3b11a`。551 产品的构建源码／wheel／安装逐字一致，wheel 559／安装 564 行 RECORD 与 283 冻结文件通过。SDK 不是读取前置依赖。
- 安装版四个既有 suite 共 57 通过，31.27 秒 pytest／32.982 秒受控进程。新增可达风险覆盖多字节分页重建、append／同字节 replacement 后旧 revision 拒绝、身份／cwd 不符和未来代次／symlink／FIFO 拒绝；原 Web fixture 增 CLI／HTTP 同页、跨项目隔离、缺 revision 拒绝及不改保存 run。原默认输出和不支持后端亦核。
- 同一安装版读取 H2 的两个原始真实 run：151,777B／10 页及 97,424B／6 页逐字重建；SHA 分别 `b7926eb7e0197bb4740f538235bae0de61c2708c1baf939b66bd844de779fd23`、`f56d0a32cdd3d6b80b57c87c1508a4badb3985b4adebcab54a9909eee9133d12`。原归档与数据库中的保存 run 文档保持，没有 SDK／新 prompt／模型请求／resume。
- 实际安装版网页通过私有已保存历史夹具验分页至尾、从头读取、UTF-8 原文／HTML 文本展示、仅当前页 DOM；实际归档追加后下一页 HTTP400，旧游标失效且可从零读；在途按钮禁用、关窗后迟到旧页不污染新面板、其他后端明确不支持。两段 Playwright 分别 5.194／2.655 秒通过；原件与最终审计待收口。首次 wrapper 执行权限／npm 解析停滞、默认 Chrome 不存在及完整 Chromium 缺 libcups 的失败分别保留；改用既有离线 CLI 和已缓存 headless-shell，未修改系统包。

私有原件统一在本片检查目录，含 `install-r1`、`real-readback-r1` 与 `browser-r1`。自身模板、独立实现审查和精确发布／自己的 CI 仍待完成。

## 审查发现与修正

首次自身原结构模板 run `22d060dba30245a899f8b77b0da5f50b`，69.933 秒成功返回 `request-changes`；十一全文 210,175B 与三份继承资源均在实际 input／stdin。input digest `5f701bd609b5d8d4cb2dc0ce771ca7f8cfdb949559434f8799e4b0dbb63e6900`、prompt SHA `475ced4aed4a47a9ef9bf29d46c290d9385272cebef6a36ad6165cf25e0c70af`、result SHA `39f2b24103a4d29f814aa8fdc92f669520a8c76c82d881de950e47961d64eff2`；沿原授权 Codex 回退，不复用旧判词。

模型发现初始绝对路径仅最后一级受 O_NOFOLLOW 保护，以及枚举后新增未来代次／第二会话不会改变原目录 inode。三个实际安装版回归 red 已保留。新的独立评审分别复现，并补充关闭窗口但 DOM 未卸载时迟到成功仍更新、迟到 HTTP 错误仍弹全局提示的 SP3／P2；其余两项记 SP1／SP2。全部接受。

最小修正留在原后端和面板：逐级 descriptor 打开全部路径；对三个原枚举目录在结束时按原 2／2／3 上限重读列表，不依赖全局祖先时间；面板成功、异常及 finally 都按是否仍在打开的原 dialog 中处理。初次目录 stat 修正因目录时间粒度而仍有两例失败，原 r2 源码结果／构建包保留；改有界重枚举后源码 20 项通过。没有关闭原生 failIfUnavailable 或增加会话状态表。

修正后的 r3 noneditable wheel SHA `16118b3afb3aa44a2fa15d650ec9f71acfc50c1329f4a766ec373686ce2f6a62`，551／两 RECORD 559＋564／283 与构建源码逐字通过；原四 suite 增至 60 项全过，31.45 秒 pytest／33.050 秒进程。r3 安装版对原 H2 两历史再次 10／6 页逐字重建通过，原归档和保存 run 未变。完整网页复验、自身修正复核与独立终审在做。

r3 实际网页六场景生命周期验收 4.998 秒通过：closed／replaced／active 分别交叉真实 HTTP200／400；仅活动成功更新正文，仅活动错误弹提示。页面通过新安装版原 HTTP，测试只延迟转发及在错误对照中选用无效旧 revision，没有伪造生产成功。分页至尾／从头读复验 2.928 秒通过；追加后的变化与重读复验继续进行。首个 r3 浏览器 socket 路径过长、一次脚本固定 pre 个数的错误均保留；使用较短的用户缓存 socket 目录、改核实际新面板未被污染后复验，不改产品迁就脚本。

## 修正后的验收出口

r3 追加后实际 HTTP400／从头读取／不支持后端复验 2.397 秒通过。离线核 r1／r3 页面正文的 UTF-8 字节游标、完整重建、追加前摘要／追加后原件和新旧 revision；六生命周期结果逐项对应原真实回复，`browser-audit-r3.json` 通过。两份 r3 页面截图保存在私有验收资料，截图本身不替代响应正文和原件链。

新的自身原结构模板 run `050b1413e81a49fc89556cb82b43a66f`，65.875 秒 approve；十一全文 215,436B 与三份继承资源实际在 input／stdin，input digest `39f02ebbd2f00767ea100f1c63395230904ad8fb27d15985fd0db817e325c0bd`、prompt SHA `38c3d3b8a40274590efda58e77efac988d6671daac4cd68979b5d1ce79cff2f0`、result SHA `b696ca9dc97db8b4f5fcf2a31c7767789a98fb404355aae0ec430e4b2af31475`。原首轮 request-changes 与真实 red 不变；没有将模型阅读材料冒称独立运行测试。

[新独立评审](2026-11-14-harness-session-readback-review.md)已对 r1 的三项问题分别复现，并在 r3 安装版核关闭条件、五副本／两真实原历史／包及 60 项回归。当前待完整最终公开快照和清理／自审原件补核，再标本地出口完成；普通发布及自己的 CI 另验。H3a 只解决归档读取，H3b 的实际续接、完整 C2 和真实 B3 不由本片关闭。

浏览器／HTTP 所属七个 PID／starttime 观察身份终态无存活，两次隔离 HTTP 端口均已关闭，`cleanup-r3.json` 通过；只证明本组受控采样，不宣称全局隔离。最终静态和完整公开候选交同片独立终核。

## 独立终核与发布出口

同片新独立评审已逐件核准最终十八文件快照（manifest SHA `0243b8f5abb887f3fb386d0de03699f70aef9a6d29eb4f0754b7cf0657a08bbb`）、r3 包／原件、修正后的自身实际输入与结果、全部网页场景和清理记录。SP1–SP3 关闭，无新增实质发现；需求和维护性两轴通过，H3a 本地出口完成。模型只读的十一文件与完整独立十八文件审查范围分别保存，不把后补状态文档计入模型已读内容。

下一步普通提交／推送当前开发分支，核精确 Git、测试包、远端完整 Ref，再验本提交自己的 CI。本片不合入 main，不关闭实际续接、原生嵌套流程和真实训练验收。

普通发布候选 `560bfdfab1b48486f71b0677a5f5113923d7ad30`、父 `322007f`，十九 Git 对象和 551 产品与 r3 测试包一致；普通 push 5.679 秒退出 0，完整 SSH Ref 1.301 秒退出 0、同一 SHA，获原独立发布补核。提交收录的独立报告 SHA 为 `645b1a8b…`，其后仅补充三份作者状态已核的两句记账和发布附录，原判词／产品证据未变。

自己的 CI `43481386288` 第五官方 run HTML 为 Success；八 job／30 必要步骤 success／completed，完整提交 SHA 的 step log 路径均核准。Linux 回归 165–256 秒，Windows 回归 899 秒、PowerShell 5.1 安装升级 56 秒；首四在途 HTML 和原收据保持。原独立已重算二十份 HTTP／HTML 原件及精确候选，终核通过，新增／开放 0／0；H3a 精确交付完成，未借其他候选的 CI。H3b、完整 C2 和真实 B3 继续开放。
