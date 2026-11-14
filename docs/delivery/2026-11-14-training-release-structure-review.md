# F9c C2 精确 owner 批准／恢复：独立结构审查

日期：2026-11-14。审查者：fresh-context 独立 reviewer `training_release_structure_review`。先读取原始合同、AGENTS 与交付技能，再查看实际差异、未跟踪源码及相邻 owner；未继承实现对话。项目与文档根均为 Ergora。只写本报告，未改产品、安装依赖、重跑昂贵检查或操作远端。

基线：`c3c7c3e218e9d2efc89498e8c208bf5981b9a0d9`；分支 `refactor/architecture-foundations`；初审对象是该基线上尚未提交的工作树。

## 当前结论

- **需求符合性：本地实现与验收 approve，开放 0。** S1／S2 已修复，r2 最终安装49项、实际原生三run旅程、SDK-free／CLI／HTTP、原件与收尾及自身原模板原回复均直接核过。原问题、失败与修前范围保留，修后结论绑定下述精确 r2 身份。普通精确发布／完整Ref及自己的必要CI仍待，不据本地通过宣称整个交付已完成。
- **维护性：本地 approve，开放 0。** receipt 创建 checkpoint 已统一承担原字节／expiry身份冻结，复用原有 serializer；新模块持有完整、独立的 owner receipt 生命周期，沿用原 start／runtime／history／process owners。未发现新增重复权威、无真实消费者的通用抽象或无可达理由的 guard／测试。发布／CI阶段仍须原结构轴终核。

## S1 — P2：ready 前丢失原 receipt 会重新 mint 并刷新到期时间

初审位置：`src/ergora/reference_training_release.py:210–216`（初审 Git blob `7d32beb1fb3e40b73fa24e30ef80ed05e1103d6b`）。

可达顺序：原 `agent_platform.training.cli approve` 在 receipt writer 中成功发布私有 receipt，随后中断，尚未写出 `.receipt-ready.json`。本片已有 `after-owner` 服务场景明确构造了这一中断。若该原 receipt 在恢复前丢失，`write()` 只用 ready 是否存在判定是否发生过创建；此时 ready 不存在，于是再次调用 `original_write(path, value)`。原 CLI 每次调用都会以 `time.time() + 86400` 生成新的 `expires_at`（冻结原文件 `platform/local/agent_platform/training.py:267–270`），因而同一 operation ID 下会创建新的原 receipt 字节与新 expiry，随后可首次发送信号。

这违反原合同“原 receipt 已落盘而 attempt 未写时只复用原字节与原 expiry”“缺失时拒绝首次发送”，也让从本地中断恢复隐式变成一次新的 owner 决策。现有“receipt 已存在时原字节保持”与 expired／revoked 等测试没有覆盖原 receipt 在 ready 前消失的路径。

最小修复：在调用原 receipt writer **之前**持久化、绑定原 intent／receipt ID 的不可变创建尝试 checkpoint；创建尝试存在而 receipt 缺失时保持未知状态并交原 owner 对账，不再次调用原 writer。receipt 仍存在时继续读取、验证并复用其原字节与 expiry。该 checkpoint 只约束本地恢复顺序，不能成为批准权威。增加一个“after-owner → 删除 receipt → resume”反例，并保留 ready 前恢复原字节不变的已有正例。初审时实现方接受此项，后续复核如下。

源码复核：release blob `0764cd967bdf9f6ff3439f0cbf0c115bcfa84e48`、suite blob `b223cff4bc8cecdbca67d4ee96f2fa6bb4335e93`、fixture blob `0bc086a5334dba4679209ef0e2773e5ef5c1acad`。`reference_training_release.py:218–224` 在原 writer 前保存 `.receipt-attempt.json`；已有创建尝试而原件缺失时拒绝创建，未创建尝试却预有原件时也不接纳。`status:108–126` 按 result→signal attempt→ready→receipt creation attempt 的依赖逆序读取，验证 ready 必有创建尝试，使用 `owner_receipt_status: unknown` 区分创建不明与 signal 投递不明。新增测试 `test_training_release.py:146` 的 before-owner／after-owner 两个场景检查恢复后仍无新 receipt、无 signal、状态保持；原件仍在的字节／expiry恢复正例保留。只读核验 `source-r2/process/stdout.txt`，23项通过／205.16秒，包含此反例。S1 的缺失重建路径已关闭；这一结论未覆盖后续 S2 的原件漂移路径。附带移动的 RPCError 转换覆盖 dispatch 与 history reconcile；状态／prepare 的 SDK-free 早返回保持。

## S2 — P2：ready 前会把漂移后的 receipt 字节与 expiry 接纳为原件

位置：`src/ergora/reference_training_release.py:83–85`、`:200–212`、`:218–227`（复核 Git blob `0764cd967bdf9f6ff3439f0cbf0c115bcfa84e48`）。

来源与核验：本片自身原模板 r1 返回实际 `request-changes`，原回复位于 `.ergora/checks/training-release/self-review-r1-codex/original-result.json`；本 reviewer 已读取原回复并独立沿源码确认。独立需求轴另行内存复现由实现方上报，本 reviewer 未另跑该复现。

可达顺序：沿现有 after-owner 场景发布原 receipt，停在 ready 之前。创建 marker 此时仅保存 intent／receipt ID，未保存原字节摘要与 expiry。把仍存在的私有 receipt 的 expiry 改成另一个未来时间，或只调整原 JSON 的格式，再 resume。`check_owner()` 的 expected expiry 取自当前文件本身（`:205`），只检查其仍未过期；格式差异也不影响规范 JSON 身份比较。由于 ready 尚不存在，`:210–212` 无旧摘要可比，于是漂移后的原字节与 expiry 会被写成新的 ready 并继续发送。

这仍违反“只复用原字节与原 expiry，不续期，漂移时拒绝首次发送”的合同。S1 创建顺序修复保护了“原件缺失”，尚未保护“原件仍在但已漂移”，因此先前的无开放源码阻断判断需要由本项更新。

最小修复：在原 writer 之前，从原 CLI 传给 writer 的 `value`，使用原 writer 的现有序列化约定冻结预期原字节 SHA 与原 expiry 到不可变创建 marker；ready 必须匹配该 marker，恢复读取原 receipt 也必须匹配该 marker，不能把当前文件的摘要／expiry当作新的身份。保留 S1 的缺失拒绝，不复制原 adapter 授权逻辑。扩展 after-owner 反例覆盖“仍有效的新未来 expiry”和“只改格式的原字节”，检查不发信号、不覆盖原 receipt、不落 signal attempt，并保留原字节／expiry正常恢复正例。实现方接受此项；初次记录时保留 r1 产品，待其安装检查结束后才修复与重新打包，后续复核如下。

修后源码复核：release blob `aeca15d7e7ee8d592b15b3a2dbb501e85ef553ca`、suite blob `59aa7a4bb0a13bbbe50507d5a76fead344e27c9d`，fixture仍为 `0bc086a5334dba4679209ef0e2773e5ef5c1acad`。`reference_training_release.py:223–225` 在调用原 writer 前，用现有 `reference_training_context._native_bytes` 冻结原 CLI 传入 value 的字节 SHA 与 expiry。该 helper 的 UTF-8、ensure_ascii=False、indent=2、allow_nan=False 与末尾换行均与原 `core.write` 一致，未新建重复 serializer。`owner_attempt:84–85` 复用 ready 的受限形状；`check_owner:210–214` 与 `status:113–115` 直接匹配创建 marker 的原 SHA／expiry，不能接纳同语义但不同格式的字节。S1 已有创建尝试且原件缺失的拒绝仍在。

`test_training_release.py:165–188` 加入 `future-expiry` 与 `raw-bytes` 两个 after-owner 参数，分别延长仍有效 expiry 与追加有效 JSON空白，检查拒绝恢复、原件原字节保持、零signal、无signal attempt；原字节／expiry 正常恢复与 S1 两中断反例保留。最终 `install-r2/regression-r1/process/stdout.txt` 明确记录两个新反例实际 PASSED，整组49项通过；S1／S2 均关闭，不依赖修前测试结论。

## 已核结构与真实调用路径

- `training.approve/resume_approve` 与 CLI／HTTP共用确认、精确 revision 预约；DB 写预约只包住本地 prepare，dispatch／resume RPC 在退出预约后执行。HTTP复用现有 loopback／Origin／请求头 guard，严格 `confirm` 进入相同应用接口。
- 新 `reference_training_release` 唯一生产消费者是 `reference._training_process` 的训练子进程入口。`_Release` 组合现有 `_Submission/_TrainingProject`，复用其注册身份、start intent、run receipt、规范 JSON摘要、受限路径读取；C1 `inspect`、runtime `lookup`、`find_signal_event`、原 immutable writer、`file_lock` 与 process monitor 均沿原 owner 使用。没有新增调度器、授权判断或实验账本。
- 本地冻结与 owner release 分属不同生命周期。把 `_Release` 并回 start 或抽成供 start／cancel／approve 使用的通用基类会扩大共同接口；目前的私有记录／检查方法集中在本模块，真实调用者足以解释其所有权。与 cancellation 相似的少量状态读取代码尚不足以构成新增抽象的维护收益。
- 原同步 `owner.cli(['approve', …])` 在有界训练子进程内运行；dispatch 本身同步，原 phase 与 release 阶段分别创建 event loop，未在活动 loop 内嵌套 `asyncio.run`。对 `owner.uuid/write/subprocess` 仅替换模块引用，未改共享 `uuid/subprocess/time` 对象，`finally` 还原连接、原模块变量和 argv。
- 原 phase 与原 release 两次连接都经过 `runtime.lookup`：固定完整 run ID、校验完整起始 Experiment，再核原 start memo，然后返回只用固定 handle 的接口。原 CLI仍负责 AWAITING_RELEASE／binding／evidence 检查；原 release 客户端仍构造实际信号。发送前再核 C1 原源文件摘要、baseline／fence／完整 spec、原 receipt，且先落 signal attempt 再调用实际 handle.signal。
- 发送后的恢复分支只读取已冻结 start/spec 与固定 run 的完整信号历史，不调用 C1 preflight，也不重读当前 manifest／runner／baseline／archive。状态把 signal delivery、authorization、integration verification 与 execution success 分开；ack 没有变成采用或训练成功主张。
- receipt 身份、私有权限／uid、expiry／revocation、ready 摘要与 persisted intent／attempt/result 的依赖检查分别对应真实输入或恢复故障；S1／S2分别指出创建顺序与完整原件身份冻结的缺口。未发现应删除的重复授权实现或无可达理由的 guard。
- 新测试在公共应用接口及原 SDK编解码服务 seam 上覆盖静默误投递风险，复用已有 start、archive 与服务 fixture。run／input／memo、phase／evidence、receipt、来源漂移、unknown历史对账与零重发断言有合同依据；未发现仅锁死默认值或重演实现细节、应阻断交付的测试。

## 检查对象与证据限制

产品与测试初审文件：`src/ergora/reference_training_release.py`（新）、`training.py`、`reference.py`、`cli.py`、`web.py`、`tests/test_training_release.py`（新）、`tests/fixtures/training_release_client.py`（新）、`tests/test_architecture_boundaries.py` 与 `scripts/ci/linux-groups.json`。其余相对基线的 C1／前片发布和CI文档变化保持归原片所有，不拿来证明本片。

相邻只读检查：原 `agent_platform.training` approve／LocalTrainingAdapter、`perf_temporal.client`／adapter；`reference_training_submission`／context／runtime／cancellation／evidence／history；应用 project/revision 选择、web guard、`state.file_lock` 与 `processes.run`。冻结参考目录相对基线无差异。架构名单仅新增该原边界模块，Linux group5 纳入新 suite。

初审 Git blob（按上述产品／测试顺序）：新 release `7d32beb1fb3e40b73fa24e30ef80ed05e1103d6b`；training `e955d5302def562f6687fddfba90b436b5ee1f24`；reference `d025440940bdb0c758c7a4b6c8d1c39193ef7043`；cli `4b2b52d6f463e375274c1f73662324a8789df7fb`；web `ce4e6a314ae32abbc967a64140a9b7e0e7138497`；新 suite `e2fec112e23bd59ed9fe77b0b028e47e2522c5bf`；新 fixture `6fe4b7ec2bb06bbdd40d458e1fc420816dd76cc6`；architecture `42a7532a29c81539501bf459560586c3b81fa1a7`；Linux groups `eaf6283bf75691f81b2739bd197c1dfb633dfbfb`。

审查者没有重跑测试、安装或操作远端；最终补核只读取原始材料、比对源码／包、重算摘要与解码已存原历史。初审与修后静读的精确对象如上；新增的 `tests/test_training_evidence.py` 修正仅把预期文本读取改成 `read_bytes().decode('utf-8')`，与产品保留原 CRLF 字节的合同一致，没有更改 C1 产品行为。README／训练手册／当前架构的补充与实际 CLI／HTTP及后续 C3 页面分工一致。

## 最终本地终核：r2

[公开证据](evidence/2026-11-14-training-release.json)当前90份原引用（含后补的3份 group5 collection材料），本 reviewer 逐份核字节数与 SHA-256，全部匹配。对应私有根为项目内 `.ergora/checks/training-release/`；原始报告、脚本和失败均按原范围保留。

- **精确身份。** 独立重算 wheel `173be7d224743fa85cf8992820e86ab181dab6e1e6680a5cb803a49230ff6617`；574产品在当前树、冻结安装快照、wheel 与 noneditable 安装间逐字一致。逐行重算 wheel RECORD582行与 installed RECORD587行的原 hash／size，核283参考manifest，均无差异。C2九件产品／测试／CI映射独立重算为 `9485aaaec5042b912fe1847d15b3babcb6b78610a364736583827d4bb5b3b150`，当前树／快照匹配。最终 release／suite／fixture Git blob仍为 S2 修后记录，未新增产品变化。
- **安装检查。** `install-r2/regression-r1/result.json` 为 succeeded／0；实际 argv 是安装解释器 `-I -m pytest`，执行 release／evidence／architecture 三suite，49项全部通过／248.18秒，monitor250.292秒。两个 S2 参数反例原日志明确 PASSED。r1六suite80项／445.97秒只属于 S2 修前身份，未冒称修后重跑 start／cancel／web 全组。
- **原生完整旅程。** 直接检查 `native-r2.py`、result、三份原 history、固定 runs、原 ticket 与检查点，实际本地 Temporal／原 worker 旅程70.482秒通过。alpha直接确认与重复读取；beta在真实server接收后主动丢ack，原 spec／baseline／runner／archive缺席时按固定原history恢复；gamma原receipt发布后中断，再由HTTP显式恢复，原字节／expiry保持。每个run均核完整起始 spec与start memo、恰好一个完整release信号、对应 receipt／evidence／binding、本地原票据及 `INTEGRATION_TASK_CREATED`；三票据均 `automatic_merge: false`。独立比对三receipt的原字节 SHA／expiry = creation marker = ready。
- **实际入口与原件。** 六条CLI命令均使用最终安装解释器且退出0；六个真实loopback HTTP请求含拒绝未确认／错误intent、正常恢复／重复读取与票据观察。已核 `-P -S` SDK-free原stdout等于gamma本地结果。24准备原件与105读取原件的当前摘要逐份匹配保存值；原脚本确认Git clean，无runner、executor-start或fence。三个受监视进程均收尾到终态，原cleanup记录Temporal与Web端口关闭。
- **自身原模板。** 原 `ergora-structure-review` 经用户已授权的Codex回退，r2原reply为 approve，原结果 SHA `e632aa609e13a028e707fedf2106fd902121b47b2a5de55338a3473feed1008c`。独立核实际stdin = prepared prompt，prompt SHA匹配，15完整文件／281,510B的内嵌原字节逐份匹配packet摘要；原脚本还核全部继承资源实际进入stdin。53.813秒结果仅给出源码结构意见，明确其调用时r2运行证据尚待；本 reviewer 另以上述最终原件补核运行结果。r1原request-changes与S2原回复保留。
- **CI接线。** 新suite仅在Linux group5登记；原插件实际collection为414／1867项（1453 deselected）／4.39秒、returncode0。这只是收集证据，未执行CI测试，也不代表新候选Windows／Linux必要job通过。

首轮源码 source-r1 的20点／cancelled／-9与未完成范围、S1修后23项旧身份、旧安装80项、native-r1私有脚本误取扁平ticket字段的失败与同原run续验均保留，没有因r2成功改写为成功。当前本地源码／验收无开放需求或维护性finding；下一步是普通精确发布、完整Ref与自己候选的必要Windows／Linux CI，再由原结构轴核固定候选。

本结论仅覆盖精确 r2 本地合同与合成archive上的真实原生控制／receipt／history／票据旅程。未进行真实训练、GPU、质量／性能测量、真实集成复验或采用；F9d／B3、C3与F10／G1仍各自开放。
