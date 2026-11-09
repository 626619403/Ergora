# AC3c.4：组合任务的联合离线备份与同路径恢复

日期：2026-11-09。固定基线`cee213a581895d491c1cd41b5fe79b23bfd09b59`；状态：R2联合离线备份/恢复与R4在线继续通过，联合恢复实际出口和自身模板修正复审通过，新独立本地两轴通过，精确交付在途。前片CR4已精确交付，自己的双OS CI42551052990七必要步骤与独立即时远端终结通过，原件见前片记录。

## 范围与验收出口

复用原`state backup / verify-backup / restore --offline`，不另建备份框架或调度/租约账本。增加通用联合恢复操作手册；本片无需修改生产源码、测试、依赖、CI或283冻结文件。

在CR4已停止的专用持久验收根，对控制home用原备份接口；离线归档登记CONFIG/STATE、业务Git库及此栈所需的本地执行文件。控制备份和外部归档保存在源目录以外的新持久目录，普通文件/模式/目录/链接身份与数据库完整性分别核对，秘密配置仅留本地受限备份，不发布内容。外部解释器/工具二进制作为明确依赖重新核身份，不声称已打包其所有外部环境。

保留所有原目录后，在原绝对路径、同平台恢复。目标原存在时原接口必须拒绝；不能重写JSON绝对路径、重建原ledger或自动重新提交。恢复后先离线核完整任务信封、创建/提交/取消/对账意图与回执、24 receipt/87 artifact、四原owner-plan、四claim/三active、一条显式释放，以及所有业务repo/mirror/worktree的候选、引用和工作区状态。

然后仅由公开services入口重新启动本次owned栈，四原run查询保持原outcome/候选；v2和v1完整首输入/队列、完整history与原SDK replay分别核。服务重启允许增加原历史中的查询无关系统事实，不能因此宣称history字节永远不变；比较任务相关事实和旧历史前缀。重复`task start`不得派生新run，检查没有新请求/回执、租约或意外作业。原CANCEL_UNCONFIRMED保持，不能用服务恢复改写为成功或释放其余claim。最后显式shutdown并核owned服务停止，持久原件保留。

实际命令/耗时/身份、失败及未验范围分别登记；新fresh-context独立者核原件与手册，按大项要求用Ergora自身审查模板真实审查本片材料。原业务Agent仍是确定性协议fixture，非模型质量或生产灾难恢复承诺。Windows控制home原接口已属既有支持，此片的真实整栈恢复仅Linux；不声称跨平台、跨路径、在线多库原子快照或远端服务迁移。

## 记录

原始验收程序与缓存存项目忽略的`.ergora/checks/ac3c4-recovery/`，运行/备份根在home下持久目录。本片的联合备份/恢复实际原件见下，不用CR4的单次重启旅程替代。

首轮R1已完成原控制备份/拒绝覆盖/同路径恢复和外部tar提取，但探针把Linux符号链接模式位也纳入必须相等，因三条链接从0775变为0777而在上线前退出。全部普通文件/目录/链接目标相同，GNU tar compare成功；Linux链接模式不提供访问授权，不据此修改产品。保留R1全部日志、归档及原目录；R2仅把链接身份比较改为链接目标（普通文件/目录仍核模式），先与R1最初完整清单/五库逻辑/32 Git快照对照后再做完整新备份旅程。R1不能预记上线恢复成功。

R2原控制恢复、外部全树/普通模式/链接目标、五SQLite逻辑与integrity、32 Git离线原件全部通过，真实服务已启动，原resumed-v2 status及重复start保持；随后探针错误地要求每条任务external_confirmed=true而退出，finally正式shutdown。原Inspection语义要求存在fence且无未决项，正常REVIEW_READY无fence即返回false，六receipt成功且unresolved/ unexpected均空；该事实不应被修改。保留R2原脚本/归档/日志，R3继续已恢复现场的在线检查，先重核protected全树/原四控制与作业账本/Git，按原fence核external_confirmed；不创建fence、不reconcile其余claim，也不机械重复已通过离线备份。

R3在线继续已核四原run/status、重复start、完整history/replay与原fence语义；最终探针将离线全树清点用于在线过滤前，遇原Supervisor socket而拒绝，finally仍正式shutdown，5个已观察原进程均退出。该special-file拒绝属于正确离线保护，不放宽产品或离线清点；保留原四history及全部失败原件。R4仅将在线核对改为直接清点受保护请求/证据/任务/工作区子树，避开本来未纳入稳定比较的服务socket，继续同一已恢复现场完成核对。

## 实际恢复出口

[R2离线与R4在线汇总](evidence/2026-11-09-ac3c4-recovery.json)：原控制备份71文件，manifest SHA `912ce5282e4f47d59acaa8e3337193ca6eff17d762778f8e4ea07932fa05512b`；原控制home存在时restore明确拒绝。外部tar **11,489,280字节**，SHA `3a52f9276228f4806a9d6fdd6b2df4569e979375654fab2ef0acc88dd278f8de`。保留九个原目录后在原位置恢复；**1,992项（1,400文件/589目录/3链接）、五SQLite integrity/全表逻辑及32 Git状态**与最初原件相符，文件/目录模式和链接目标保持。三个外部依赖链接的目标可用并核身份，但其venv/二进制目标未归档，不能据此宣称新机器环境重建完成。

R4只继续R2已恢复现场的在线验收，**44.47秒/exit0**，不将此时间称整片备份总耗时。真实公开Supervisor/Temporal/双worker/A2A/scanner重开，四原run的完整status/候选与原提交逐JSON相同，重复start保持同run。四完整history **161/167/162/161事件**，原事件前缀/完整首输入/版本队列与SDK replay通过。两个正常REVIEW_READY原fence未记录/`external_confirmed:false`保持；拒绝与取消原fence匹配/true，全部无unexpected/unresolved。取消原CANCEL_UNCONFIRMED保持，未为过探针新建fence或调用其余reconcile。

scanner观察12秒后原保护树1,145项、控制/leases/A2A/executor四库逻辑和32 Git状态保持，无新请求/回执/作业或租约。原24receipt/87artifact/四owner-plan及四claim（三active/一released）[重核原件](evidence/2026-11-09-ac3c4-evidence-check.json)分别保存。正式shutdown后五个已观察owned Supervisor/后代原PID/starttime均退出，三端口关闭/managed socket不存在，数据库与保留目录仍在；采样不保证捕获所有短命进程。

实际使用的非editable安装包仍为CR4发行aaa55f0；本片未改生产/测试/依赖/CI。R2开始与R4结束全**369源码/wheel/安装文件一致、283冻结保持**。通用[备份恢复手册](../BACKUP_RECOVERY.md)复用原接口与GNU tar，并明确闭合run方可外部查询、同平台原路径、外部依赖/服务及tar非事务限制。[新独立报告](2026-11-09-composition-recovery-review.md)已直接重算归档/清单/库/Git与history和最终清理；自身模板两轮结果见下，最终本地两轴及精确交付分别登记。

自身结构模板R4真实调用166.23秒返回request-changes（原结果保留）：手册恢复后services start未显式原CONTROL，默认home可能找不到或选择其他同名项目；project/task查询也需同home，且重复start应明确task start。独立者确认AR-2/P2成立；仅修正文档的home限定、原task重复提交与Temporal先于worker，不重跑未变备份旅程。R5已用自身模板复查更正后的完整手册及实际home/服务/提交所有者，R2/R4原验收仍保持其实际范围。

自身模板[首次身份](evidence/2026-11-09-ac3c4-r4-self-review-identity.json)/[原request-changes](evidence/2026-11-09-ac3c4-r4-self-review-result.json)和[复审身份](evidence/2026-11-09-ac3c4-r5-self-review-identity.json)/[原approve](evidence/2026-11-09-ac3c4-r5-self-review-result.json)分别保留。R4为真实Codex `gpt-6.1-sol`/high/task-MCP、107106字节九份完整资料、166.23秒；独立者已完整重组连续分页并核身份。R5只复查更正后的完整手册及三个原home/服务/提交所有者，**46348字节、96.92秒、approve/exit0**，run `80e4cb76640c47d8ac73564fbbd64569`，不借此扩大到未附依赖或宣称模型执行测试。R5原生完整分页和最终16文件文档scope已由同片独立者核；没有重跑不变恢复旅程。

新独立本地终核通过，AR-1/AR-2关闭，R1–R3探针范围及两轮自身审查均保留。最终静态10份Markdown、208本地链接/锚点、79条公开CLI parser与diff检查通过；完整16文件（仅文档/公开证据/前片交付记账）普通提交、自己的CI及即时远端另行登记。
