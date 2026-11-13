# F8-H3b 显式原生续接交付

日期：2026-11-14。产品基线 `fde425164e45a15e255eb62e0e6f6fd959e00f6c`，文档检查点 `67966095814eec01f2e1e5d65d87e289320ad79f`。本片[计划](../plans/2026-11-14-harness-session-continuation.md)限定显式新 standalone task-MCP 源的一次续接。r3 实现、安装／实际调用、自身模板及最终新独立两轴本地出口通过，开放0／0；产品 `47443840b68693f63ee011dc6fbe29421a42223f` 已普通推送并核完整远端Ref，自己的 CI `43495562208` Success；原独立两轴终核通过。

## 实现与所有者

- `agent_runs.run_input --allow-one-continuation` 默认关闭；正式 supervised、自定义结果 schema、非 task-MCP 和不支持后端拒绝。新源成功前封存项目修订／repo 物理身份、完整输入／祖先资源／权限、有效 policy、schema、绑定和原预算；driver 封存固定 SDK／profile／patch／实际 prompt／cwd 与 home 物理身份。旧记录不回填授权。
- `continue_input` 消费原项目／源 run／完整 prepared input／稳定 intent／新预算。任务正文允许改变，原 composition、grant、叶及资源保持；一个来源使用一个确定 child ID，沿原 `agent_runs` document 保存名额和写前 `unknown`。整个操作持原 `file_lock`，FD 交给原 process owner 的直接子进程；相同请求仅返回原记录，冲突拒绝，中断不释放名额，child 不能再作 source。
- 沿 `agents.invoke → Invocation → AgentBackend.command → processes.run`，由 DeepSeek Adapter／独立 driver 执行固定 `0.2.2rc2` 的 `resume_session → Session.run`。复用原 home／ID／cwd，新调用有独立输入／MCP scope／audit／result。基础安装不 import SDK；归档的标准库读取与目录身份保护由原 driver 供 Adapter 共同使用，没有新会话服务、调度器或账本。
- `native_directories` 持有完整目录链，在发送前按原身份复核并在操作结束检查，覆盖 SDK 启动／发送／close 期间的同路径副本替换。SDK idle 不是持久化屏障；正常 close 后才核完整原前缀及本次 receipt／result。B1 在恢复后、额外 cwd RPC 与后缀准入前保存；原进程 owner 收尾后，无论成功／断连／取消／超时均沿原 Adapter 有界观察 B2 和可用区间。观察不是完成证明，无完整 receipt 保留 `unknown`，路径换权或读取失败明确保存 `observation_error`。
- 准备和 preflight 的时间从本次 wall budget 扣除；停止收尾另计，不承诺累计 token／费用或单次 HTTP。output 沿同项目 DB lineage 读取原档，分别返回本次 stdout、状态和 native 观察，原源记录／结果不覆盖。

入口、参数及恢复限度已写入 [后端手册](../AGENT_BACKENDS.md#显式续接一次只读会话)、README 与[当前架构](../architecture/current.md)。正式六阶段恢复、任意多轮、跨后端／版本迁移、workspace、完整 C2／真实 B3 不在本片。

## 设计和原始失败

[两种 Interface 调查](../architecture/2026-11-14-harness-continuation-options.md)选择原 Invocation 携带已准入来源，未增加第二条调用链。[先行机制探针](2026-11-14-harness-continuation-probe.md)只验证固定 SDK 的两次合成 prompt、新 scope／上下文及刷盘，不能替代产品验收。

恢复时既有三 suite 首轮 76 通过／2 失败：迁移后的归档测试仍引用旧模块 codec 注入点，已随所有者迁移修正。首次新行为运行 89 通过／86.78 秒，其后继续补扣时及故障检查，旧成绩没有作为最终候选结果。

r1 noneditable wheel SHA `cc2d78a85fdb1d5545e81de56e9bf77fea95776740fcfe5e2e711b0edc7df17a`：561 产品／两 RECORD／283 通过；七 suite 130 通过／12 跳过，118.37 秒 pytest／120.563 秒受控进程。其实际产品／SDK 合成 source＋followup 成功，31.309 秒、12 HTTP，85,042B 父附件两轮完整读取、新 scope、原记录／结果及原档前缀保持，重复 intent 无新请求。r1 断连／取消各 7 HTTP、`failed`／`cancelled` 且 `unknown`，各采样 11 个 PID／starttime 均无存活。短预算例在首个续接 HTTP 前超时，原夹具要求“已接收一个 HTTP”因而失败；它证明前置时限，不作为发送后超时成功。更早夹具目录/frontmatter不一致在 SDK 前失败，原件保留。

## 独立问题与修复

[Spec 审查](2026-11-14-harness-continuation-spec-review.md)复现两项 P2：原 home 未封存物理身份，完整副本能接管；恢复／发送失败缺少 B2 及新增区间记账。[结构审查](2026-11-14-harness-continuation-structure-review.md)进一步复现 close 后、B2 前替换副本仍可完成，以及总 PLAN 恢复入口过期的 P3。

r3 通过共享目录上下文、发送前和结束身份检查修复副本时窗，并把 B1 保存提前及 B2 观察移至原进程 owner 收尾后。两独立审查者分别按原场景复核：发送前换 home 未发新 prompt；close 后换 home 为失败／unknown；恢复 cwd RPC 断连保存 B1=B2 的恢复种子区间，发送断连保存已知 B1/B2，无 `completed`，相同 intent 不重发。原失败与初修窗口未删除；最终安装与实际证据已由两方向补核，发布／CI终验见末节。

## r3 候选与验收

r3 noneditable wheel SHA `587c345fae69a70fdf0d436433bebe7a3df81ce801eca6003c2909c2a5c392a4`；561 产品文件在构建源码、wheel 和安装逐字一致，wheel／安装两 RECORD 及 283 冻结参考文件重算通过。源 DeepSeek suite 35 通过／37.54 秒；r3安装版七个受影响suite **133通过／12跳过**，125.12秒pytest／127.014秒受控进程；跳过项保留原可选依赖／平台条件，不算已运行。实际固定 SDK 四场景与新真实模型结果如下。

实际自身结构审查模板及新独立最终两轴已通过；终版公开文件静态核验、普通提交／推送及自己的CI已完成，精确身份见末节。证据只保存在被忽略的本片持久检查目录，不把凭据、内部服务或业务源码放入公开文档。


|r3实际调用|观察结果|
|---|---|
|合成成功|28.841秒、12HTTP；85,042B父附件逐轮连续完整读取；原home/ID/cwd、原记录／结果、原档完整前缀保持，新scope和独立结果；同intent零重发。|
|合成发送后断连|28.716秒、7HTTP，child failed／unknown；原前缀和B1/B2物理观察保留，无completed；重复零重发。|
|合成发送后超时|34.863秒总夹具时间（含新source），child新授权12秒；7HTTP，timed_out／unknown；原前缀和已知区间保持，重复零重发。|
|合成Ctrl+C|28.773秒、7HTTP，cancelled／unknown；保留物理增量，重复零重发。四例各采样11个PID/starttime均无存活，loopback监听已关闭；范围限采样进程。|
|真实模型原模板|原`refactoring-quality`结构审查叶，显式授权DeepSeek／Responses绑定；source63.193秒、followup36.864秒均成功。新输入不含两个随机记忆标记，实际回复完整带回前轮用户与助手标记；三份父Skill附件4,084B在两轮各完整读取，新scope，源结果和原档前缀保持，重复无新调用。10个采样进程均无存活。|

真实模型这两次为每次240秒的显式wall授权，不证明提供方HTTP次数、累计账单或模型错误独立性；两轮使用同一原会话及绑定。自身审查使用用户授权的Codex回退并另存原回复，不冒称Claude或异后端审查已经通过。


## 自身模板与本地出口

原安装版 `ergora-structure-review/root/review` 已实际运行，Codex回退73.433秒、`approve`，无可执行finding。完整九文件220,205B实际进入原输入／stdin，原全部内联资源也已核；这次文本审查不独立重跑运行证据，不替代两名fresh-context reviewer。原回复SHA `acdb060f5c6570769fcff414e06f7a5115380373c145d4a60618dcfccdcdc9fb`，原输入摘要 `a88990d77af65c22536fa04ee7d64ce36311a867d3e1a7f94876f8ec09f27792`。

[可公开验收摘要](evidence/2026-11-14-harness-session-continuation.json)保留包、五案例、结果／输入摘要及scope统计；凭据、服务地址与原始私有缓存未发布。两名独立审查者已分别补核最终包、实际调用、自身模板与公开文档，本地出口通过、开放0／0。终版17文件、225个本地链接、机器标识和diff检查通过；扫描首次把README原有通用loopback安装链接误归私有地址，核固定基线相同字节后排除，原失败保留。普通发布与自己的CI已收口，详见末节。

## 精确发布与自己的 CI 终验

产品提交 `47443840b68693f63ee011dc6fbe29421a42223f`，17 文件与发布冻结字节及 Git blobs 相等；普通推送当前开发分支，完整远端 Ref 一致。自己的 [Portability CI 43495562208](https://github.com/626619403/Ergora/actions/runs/43495562208) 最终为 Success，8 个 job／30 个必要步骤通过。原独立两轴分别重核最终官方页、原 HTTP 大小／SHA、完整候选绑定、各步骤成功与完成时间；开放0／0。此为本片状态记账，不继承给后续 F9a。
