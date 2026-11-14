# F9c C2：精确 owner 批准与投递恢复

日期：2026-11-14；实现基线 `c3c7c3e218e9d2efc89498e8c208bf5981b9a0d9`。承接[原证据读取](2026-11-14-training-evidence.md)，本片自己的发布／CI单独验收。

## 行为与职责

在已发布的 training-optimization 项目内，以项目 revision、原已提交完整 run ID 和完整 evidence SHA 确认一次 owner 决策。一个实验只有一个本入口批准意图，不提供更换 request ID 绕过 unknown；超期、撤销或被原 owner 拒绝后的新决策留给明确的原 owner 对账流程，本片不自动续期或重新批准。读取本地意图不需要 SDK／服务；Linux／WSL2 才能写入或发信号。

保留原 `agent_platform.training.cli approve` 的 AWAITING_RELEASE／binding／evidence 检查、私有 owner receipt 和原 `perf_temporal.client release`。应用只冻结输入和投递检查点，原 adapter 仍是授权／baseline／gate／fence与集成票据的唯一权威。先记录原 receipt，再保存 attempt，才发送信号。成功 ack 仅表示投递；票据、真实集成复验、采用分别观察，不能统称批准成功。

意图冻结 control home／项目／注册／revision、原 start 意图摘要、完整原 run、evidence、actor、稳定 operation UUID 与原证据文件摘要。短 DB revision 预约只覆盖本地冻结，不跨 RPC；原 process monitor 限制整组运行时间，逐实验非阻塞文件锁防并发。第一次发送前核原 C1 证据、当前 baseline／fence和完整 spec；每次连接用原 runtime lookup 核完整起始 spec／固定 run／start memo。发送后的恢复只读固定 run 的完整 release 信号历史；原 manifest／runner／baseline／evidence 后续漂移或删除不能成为重发理由，也不能阻断历史对账。

原批准 CLI 同步执行；在现有有界子进程中调用，避免在已有 event loop 内嵌套 asyncio.run。只暂换该模块的变量并 finally 恢复：固定 uuid 对象、受限 receipt writer、原 release 子调用；不改共享 uuid／subprocess／time 模块。原 phase／release 连接均固定原 run。原 receipt 若已落盘而 attempt 未写，恢复只复用相同 actor／binding／evidence 的原字节与原 expiry；不覆盖、续期或 mint 另一 receipt。receipt-ready 仅记录 ID／原字节 SHA／到期时间以支持状态读取，不代替原授权。缺失、撤销、过期、非私有或漂移一律留原件并拒绝首次发送。

## 接口与结构

- `ergora training approve PROJECT EXPERIMENT --revision N --run-id RUN --evidence-sha256 SHA --confirm`
- `ergora training approval PROJECT EXPERIMENT`：仅本地事实。
- `ergora training resume-approve PROJECT EXPERIMENT --revision N --intent-sha256 SHA --confirm`：attempt 前继续原决策；attempt 后仅历史对账。
- HTTP：GET 原实验 `/approval`，POST `/approve` 与 `/resume-approve`，mutation 均要求 `confirm: true`，复用原 loopback／CSRF guard。

`reference_training_release` 持有完整批准 checkpoint／原 CLI 桥接算法，唯一生产消费者是 `reference` 训练子进程入口；并回 submission 会混合起始与 owner release 两种生命周期。`training` 持有应用 revision 预约，CLI／HTTP共用；复用 `_Submission`／`_TrainingProject`、C1 evidence、runtime lookup、原 history matcher、原 immutable writer与file_lock。不建通用批准服务、第二实验账本或调度器，不修改283冻结参考文件。页面 C3 另立片。

## 验收与进度

1. 原 SDK 编解码的离线服务合同：同意图幂等、精确 run／input／memo／phase／evidence、来源漂移、baseline／fence、原 receipt 私有／expiry／revocation、落盘后中断、attempt-before-send、投递丢回复／history缺失／不同 receipt、attempt后删来源仍只读对账；零重复发送。
2. 最终 noneditable 包／两 RECORD／283；相关安装测试，实际 CLI／loopback HTTP／SDK-free 状态，原件与进程收尾。条件允许时本地 Temporal 合成 native archive 的 release 旅程；合成结果不表示真实训练／质量／性能。
3. Ergora 自身原结构审查模板、新 fresh-context 需求／结构两轴；普通精确发布、完整 Ref、自己的 Windows／Linux 必要 CI和原结构轴终核。

立片时合同已立、尚未实现或验收，以下按轮记录进展。每个步骤更新[交付](../delivery/2026-11-14-training-release.md)与[主计划](../PLAN.md)。C1自己的CI继续独立跟踪；真实 F9d／B3、C3页面和F10／G1仍开放。

第一版产品／CLI／HTTP及SDK编解码服务合同测试已写，复用原approve／release，未修改283参考。源码相关suite正在运行，新的独立结构轴正在检查；最终安装与实际入口／自身模板尚待，不提前主张验收。

独立结构轴发现P2：原receipt写入后、receipt-ready前中断，随后receipt丢失时会重建同ID并刷新expiry。接受finding；将保存receipt创建attempt-before-write，创建结果不明或缺失时拒绝mint，补针对性反例；首轮源码仍在原时间界限内运行，待其结束后修改，保留原范围。

首轮源码原180秒monitor在20个已通过测试后停止（cancelled／-9），没有完整suite成功结论。现已按finding在原receipt写前保存创建attempt，ready前中断后缺失不重建；读状态区分receipt创建unknown与signal投递unknown。新增写前／写后中断且receipt缺失的反例，RPC错误转换覆盖history恢复。修后源码仅本片suite按600秒界限验，最终安装再执行相关整组。

修后源码本片23项全部通过／205.16秒（monitor205.884秒）。最终r1 wheel `9db0b643eddfdcd20e8e088ebe57b7c4b3c2c21f378fe150112a695d629f66e6`，574产品、两RECORD582／587与283冻结通过，九路径产品／测试／CI当前树与包测试快照逐字一致；安装六suite80项仍在途。

实际本地Temporal／原worker上三个原合成archive已完成：CLI直接确认／重复读取、真实server收信号后丢ack并从原history恢复、原receipt落盘中断后经HTTP恢复；每run仅一个release信号，原adapter均创建automatic_merge:false的集成复验票据。beta恢复期间原spec／baseline／runner／archive缺席，原receipt字节及expiry保持。六真实loopback HTTP、实际-P -S SDK-free状态、24准备原件／105读取原件字节保持、Git clean与无runner／executor-start／fence通过。首个私有验收脚本误读扁平ticket字段而KeyError，API实际正确返回integration_ticket.record；原失败／三进程收尾保留。续验只读取同三个run／archive／receipt／attempt／结果，无重建、重发或新ID；其最终原history与本地原票据均核。合成CPU不代表真实GPU／训练／质量／性能／集成复验或采用。

自身原模板r1审14完整文件／268,992B，62.870秒request-changes；独立需求轴亦实证第二P2：创建marker未绑定原expiry／字节时，ready前仍有效延期或格式漂移会被接受。已修为原writer前按原serializer冻结receipt字节SHA和expiry，恢复／ready均核创建checkpoint；新增future-expiry／raw-bytes反例。r1包及80项继续其已冻结旧范围；r2重包与修后验收不继承其成功。原模型意见／初审finding保持，手册旧C1待接批准声明已更新。

r1安装六suite80项／445.97秒（monitor447.761秒）通过，其身份仍为S2修前；r2仅重跑受到S2与C1换行预期修正影响的release／evidence／architecture，旧HTTP／start／cancel不借r2身份重称已重跑。原native-r1私有扁平票据预期失败已由同ID续验核完整原history，r2会在最终新包重新完整跑原流程。

最终r2包`173be7d224743fa85cf8992820e86ab181dab6e1e6680a5cb803a49230ff6617`，574产品／两RECORD582／587／283及当前九路径逐字一致。原writer前现已固定原receipt字节SHA／expiry，正常恢复保持原件，未来expiry／格式漂移拒绝；自身原模板r2实际审15完整文件／281,510B、53.813秒approve，原结果SHA`e632aa609e13a028e707fedf2106fd902121b47b2a5de55338a3473feed1008c`，原request-changes保持。

最终r2真实CLI／本地Temporal与原worker三run、三原合成archive完整旅程70.482秒通过：各唯一release与INTEGRATION_TASK_CREATED、原本地票据、receipt创建／ready／attempt与原字节／expiry、丢ack历史恢复、receipt落盘中断HTTP恢复、SDK-free状态、六HTTP、24／105原件保持及三进程／端口收尾。未执行runner／训练／GPU／真实质量或性能测量，不表示真正集成复验／采用。新独立两轴已补核这些原件，安装49项尚待终态。

最终安装三suite（release／evidence／architecture）49项全部通过／248.18秒，原monitor250.292秒；两个S2新反例实际通过，C1原文本预期修正同组通过。修前80项／445.97秒与修后49项范围分别保留，不将80项冒称修后全套。最终r2实际完整旅程、自身approve与两个独立轴的原件补核均齐，新的独立两轴最终本地结论收尾中；精确普通发布／完整Ref与共同候选自己的CI尚待。

新独立需求轴已最终本地approve、开放0；结构轴正在收最终原件。公开[证据摘要](../delivery/evidence/2026-11-14-training-release.json)列原失败及最终验收。原CI插件仅collection：group5选414／总1867，1453 deselected、4.39秒，新suite25项唯一归5；不称414项执行。

最终新的独立需求／结构两轴已直接核90原引用、修后49项／两新增反例、最终574包／两RECORD／283、完整真实三run／CLI／HTTP／SDK-free／原件与收尾、自身实际完整stdin和原回复：最终本地通过，S1／S2均关闭、开放0／0。精确普通发布、完整远端Ref、原两轴固定身份补核及共同候选自己的CI仍待；不称原C1失败CI成功。
