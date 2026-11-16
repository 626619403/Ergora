# 父请求原字节留存：独立源码审查

2026-11-16。审查者 `/root/cycle_parent_retention_source_review`，fresh context；未参与实现。此报告只审本片，不继承相邻片批准。授权为只读源码及必要证据、仅写本报告；未改产品、测试、计划或交付记录。

**当前最终结论：固定产品 `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3` 需求符合性 approve、可维护性 approve，R1已关闭，开放 finding／验收阻断0／0，可以普通导入该准确产品。** 新非editable安装、原模板及冻结／进程证据已独立终核，详见末节。旧r2 request-changes与各轮失败保留为历史；正式V2／v3、ordinal1、完整M1c及真实训练仍不在批准范围。

## 对象与结论

原始合同为[已接纳计划](../plans/2026-11-16-training-cycle-parent-request-retention.md)及[设计复审](2026-11-16-training-cycle-parent-request-retention-design-review.md)。进入时该两份文件 SHA256 分别为 `bf35924d01b665470fe5ba216f9e9e450162390498cff44dcdd5eb5ddb39bafe`、`18f89b6d07bcd92e57f97388f07b4ba3a64cf4a7ffe653a6c437b0f07be70e06`。根明确的内部 producer 边界为实际 `_CycleOperation` constructor／同次编码／run；正式 SDK v3 creator、V2 注册、ordinal1 执行仍属后片，不能以本片测试冒称已开放。

隔离树 `.ergora/worktrees/training-cycle-parent-retention`，基线 `68ba793a2d2ff02e4cffe50a03cfcec38d67256a`。完整差异仅 `src/ergora/reference_training_worker.py`、`tests/test_training_submission.py`、`tests/fixtures/training_cycle_operations.py`。

|冻结|完整 patch SHA256|worker SHA256|审查用途|
|---|---|---|---|
|r1|`709e9ba2172546a8654bbbc0d66eba0b3112f45d25a35f69863213c319b469fb`|`8b8295717a90cd6f176795d8680f9791e96de5ec94122222c546435ee02fd787`|原实现及已知 ordinal 类型缺口；不是最终通过候选|
|r2|`b376d5470617b777bd11ab0c981b1eddf73ca0f2130f2570b69ce92d17cd823d`|`c794f265f7420c599b7e112a40c781631accb0ada47f73a755ac743409896537`|ordinal strict-int 最小修正；首审对象（历史）|

独立重算 r2 `git diff <baseline> -- src tests` 的 patch SHA，并对 frozen-r2.json 全部781份输入重算SHA：0差异。r1与当前仅上述三文件不同，未把其运行成绩迁到r2。

**首审r2需求符合性：request changes；可维护性：approve（无另立维护性 finding）。** 当时开放阻断 R1 一项：确认边界的完整身份类型校验尚未覆盖 `parent.pid`。安装、自身原模板、最终冻结证据与终核仍 pending；本结论不是整片验收。

## R1（P2）：确认中的浮点 parent.pid 可冒充原整数身份

位置：隔离候选 `src/ergora/reference_training_worker.py:247` 的最终确认判断。r1 已知 `ordinal=False` 与原 `ordinal=0` 字典等值；作者在r2补了 ordinal strict-int。此修正保留另一处同型错误：把确认 `identity.parent.pid` 从原整数改成数值相同的 JSON 浮点，`confirmation['identity'] == self.identity` 仍为真，ordinal检查也通过。N／SHA正确、S真实wait0、全部pipe结束与原clock有效时，父端仍会记录 `durable_confirmed`。

该路径不授予业务执行，业务仍是 `capacity_exceeded`；但违反最终确认必须绑定原完整、有效 process identity 的合同，把无效外部确认报告为已确认留存。既有 `training_execution_protocol._process`（第369行）明确要求 `type(pid) is int`，S入站也已复用它，父确认不能只依赖Python宽松等值。

最小修复：在现有父确认边界对确认的 `identity.parent` 复用 `protocol._process`，保留ordinal strict-int及原完整等值、N／SHA／EOF／wait／clock检查；无需新validator、类型矩阵或协议。验证沿现有真实S确认fault增加一个pid浮点参数：先保留r2原产品红例，再对新冻结候选确认unknown／无ref且原raw、真实wait和业务容量拒绝保持。已向根和实现owner报告；后续r3修复及复核见末节。

## 合同与维护性检查

- `_CycleOperation.__init__` 先验证原payload并只编码一次，v2超界保留原UUID／raw／output；旧v1仍立即raise。诊断分支不进入普通H、root、SDK registration或执行入口，不返还机会。
- 发送沿原async owner，用原bytes的memoryview分块≤65,536B、逐块SHA、drain并显式yield；实际send、stdout／stderr、wait都由原handle收束。取消后shield持有任务；诊断S可直接kill并wait，未冒用普通H的stopped资格。
- 同一buffered stdin读封套和N raw；S只写exclusive原request.json，核N／EOF、原fd fsync、目录链同步及同dev／inode／N／SHA流式重读；一个最终有界确认，不另建receipt、ledger、ready或重试队列。父保留有界确认并继续排空，超长／额外帧不能静默截成有效确认。
- S内watchdog与主线程共用本地remaining算法，实际调用原budget_clock.remaining，检查原BOOT、bootstrap、原clock及parent完整身份；只对collect-round／reconcile-round这两个现存work mode开放，cleanup reserve与原预算不变。文件I/O阻塞时watchdog独立存在，无子进程或可取消future伪装停止。
- 大raw ref仅在request_retention内；result_ref仍属原小helper/stdout.txt。诊断unknown保留实际wait状态，业务supervisor_returncode=None／operation_stopped=False，没有把诊断回收称作H-stopped。
- 三个新增函数留在现有worker：小监督投影、共用时钟算法、实际诊断进程入口。entry有一个生产spawn调用，隐藏async loop无法承担的受管storage与blocked-I/O生命周期；不是抽象复用wrapper，无需新module／ABC。身份、文件、clock和取消guard分别保护实际外部确认、持久原件、不可续预算与资源收尾。
- 新测试留在既有fixture／submission接缝，保留真实S、watchdog、管道、磁盘及wait，仅注入相关故障。普通v1／history旧检查保持。CPU合成source及内部constructor边界不能认证真实服务、训练质量、正式producer或完整M1c。

除R1外，在此源码与调用链范围内未发现独立正确性或维护性问题。并发祖先目录替换、不可中断I/O、任意N成功保证不在已接纳合同内；没有扩大这些威胁模型，也没有把unknown叫成功。

## 已独立读取的运行证据与限制

证据根为ignored私有 `.ergora/checks/cycle-parent-request-retention/`。逐项读取argv、完整patch身份、JUnit／result、相关失败输出；没有重跑昂贵tests。成绩按其自身候选保留：

|原件|实际结果|候选与范围|
|---|---|---|
|run-01|1 failed，JUnit7.174秒|早期patch；测试编码oracle缺陷，不能记通过|
|run-02|1 passed，JUnit6.012秒|早期patch；同次196,331B多字节raw真实留存；不是r1全输入认证|
|run-03|15 passed，JUnit62.134秒|早期patch；诊断边界／真实stream／故障、取消peer与独立clock drift|
|run-04|5 passed，JUnit19.901秒|r1；真parent SIGKILL、spawn/send/loop取消、chunk公平|
|run-05|46 passed，JUnit334.913秒|r1；全部round_，包含原26及新增20|
|run-06|17 passed，JUnit196.567秒|r1；受影响旧v1、取消、cold、blocked stop、容量兼容|
|run-07|5 passed，JUnit2.459秒|r1；SDK取消／history-bound／eviction接缝|
|run-08|3份replay各returncode0，约1.30秒|r1；78／45／46 events旧原件，默认Replayer及eviction完成；不是新history|
|run-09|1 failed，JUnit6.276秒|r1产品＋新ordinal fault；真实S原124,337B raw／wait0后，父误报durable；保留原红|
|run-10|21 passed，JUnit83.047秒|r2；全部21诊断，不能消除其尚未覆盖的pid类型缺口|
|run-11|8 passed，JUnit101.087秒|r2；必要旧v1|
|run-12|1 failed，JUnit6.266秒|r2产品＋新pid-float fault，完整124,337B、wait0后误durable；patch `f437d36afed29a46b25d07bafefacf77525cc2db9fd753634fc9de5b0e3b62a8`|

还读了static-identities.json：25个GATE_SOURCES键、reference manifest及283份verify保持的原记录；这是作者实际运行原件，非本审重做verify。r2未继承r1完整组或历史重放；进一步修复须另冻身份并补其适用证据。

检查还包括根／源码／tests AGENTS、PLAN、组件协议、maintainable-project-delivery（含independent-review brief）与ergora-codebase-quality的module-design／test-seams／repository-style；完整原始diff及邻近protocol、budget_clock、process、SDK注册与原caller。`git diff --check <baseline>`无空白诊断。未执行安装、模型、自身模板、网络、服务、训练、commit、merge或push；源码检查与安装／最终验收分开。

证据记录边界另已告根：旧私有command.json包含完整继承环境，后续只读取非敏感投影；根负责私有权限和runner允许列表改进。报告不复制环境值或敏感原件。此项不作为产品源finding。


## r3 同片复核：两轴 approve，R1 关闭

原r2结论与R1保持为历史。准确r3三文件patch SHA256 `f5b46155f6b135257bcbf4a00ab05c2afc096e52c4bae0659af13ef005d60c76`，worker SHA256 `be12b4de17c448e7e07217aacf60a097e080333f169e99cccaa91981e66bd926`。本审独立重算完整patch及frozen-r3.json全部781输入：均匹配。相对r2产品唯一新增是父确认第245行 `protocol._process(confirmation['identity']['parent'])`；ordinal strict-int、原完整identity/N/SHA、全部pipes/wait、原clock/stop保持。复用既有边界正确，没有引入新抽象、执行或新状态。

本审已独立读取run-12的真实红例、manifest和完整patch，确认worker仍是r2，pid-float故障在真实S输出处注入，父误记durable。r3从源码上消除了R1的剩余类型缺口。本审随后独立读取准确r3的manifest、完整patch、result／JUnit和testcase清单：

- run-13 **22 passed／88.092秒**（runner总88.677秒），包含bool ordinal与float parent.pid的真实S确认反例、完整原raw成功、容量分流／N±1／EOF、存储与回复故障、watchdog原clock拒绝及真parent SIGKILL、取消及公平分块。
- run-14 **8 passed／102.512秒**（runner总103.076秒），包括旧v1 cold结果读取、spawn／helper／loop取消、blocked stop-peer及原request／stdout／frame三种容量失败。完整patch与r3同一。

**R1关闭；r3需求符合性approve、可维护性approve、开放finding0。** 此结论只限准确r3源级实现与其实际定向证据。r1完整26／17与SDK/history兼容仍保留原身份，未重称r3全量结果。安装／自身模板／最终资源证据由根单独完成；本审不提前认证正式SDK creator、v3注册、ordinal1、真实训练或完整M1c。

还独立对run-02／09的原request.json作字节投影核验：分别196,331B／124,337B，无尾LF，原ordinal和parent.pid均为int，output只有request.json；未打印正文。报告本地链接目标存在。

最终静态记录：报告本地链接目标存在，报告 `git diff --no-index --check /dev/null <report>` 无空白诊断（新文件差异状态1）；源码 `git diff --check <baseline>` 无诊断。


## 固定产品最终证据终核：允许普通导入

2026-11-16，同一独立审查者完成本片最终证据终核，未参与构建、安装、模板运行或产品提交。固定提交 `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3`，唯一父 `68ba793a2d2ff02e4cffe50a03cfcec38d67256a`，隔离树clean。独立重读Git对象及完整47,112B diff，恰原三文件710+/12-，SHA256仍为 `f5b46155f6b135257bcbf4a00ab05c2afc096e52c4bae0659af13ef005d60c76`，与冻结及package-r3/implementation-r3.patch逐字相同，原R1修复未漂移。

新wheel SHA256 `0426af971d2d573b952873d89be327cd8e7de115547f05d1391ad31c7507faeb`。本审直接重算853份源输入、663产品文件、core／SDK各663份真实site-packages、wheel内对应产品的字节与执行位：全部匹配；179份冻结测试／示例副本字节全部匹配。package元数据表明仅worker产品字节改变，无新增／删除产品文件；core无Temporal，SDK1.34.0，所有列明owner实际导入site-packages。参考283文件PASS及两套依赖check exit0原件已读取，没有冒称本审重跑。

安装两组的argv、driver、stdout／空stderr、result和JUnit逐项核对：新SDK Python3.12，`-I -B`，移除PYTHONPATH，在冻结测试副本目录运行。诊断组实际 **22 passed**（JUnit116.263秒，pytest文本116.27秒，driver117.429秒），旧v1定向组实际 **8 passed**（JUnit119.146秒，pytest文本119.15秒，driver120.278秒），均绑定上述wheel。source22＋8与installed22＋8各自保留身份，不借旧轮覆盖新安装。run-15准确r3的三份原history重放记录亦已读取：原SHA／82,086、44,640、48,561B／78、45、46events保持，均returncode0、空stderr、实际replay与eviction完成，约1.30秒各；不是新正式Workflow运行。

Ergora自身 `ergora-structure-review@1.0.0` 原结构模板的composition、check-input／run-input命令、summary、review和原result已读取。实际Codex61.542秒、exit0／succeeded／approve。对13份scope快照逐份重算，共607,088B，均完整进入task；完整47,112B diff和完整baseline worker也在task中。实际802,880B stdin包含完整task及全部3份祖先／本级资源，SHA256重算为 `2b1be0f9ec1b5cdd9294b405ddf6d220f99696db62e69440a5e8783df9d5356a`；原result重算为 `6cc016d4ca0db063b90c4ee2567d5fc71d79c5155fc45e55a41b44ad328dd600`。模型回复明确只审所供文字、没有工作区或自行跑测试；本审未据其approve替代独立判断。

根post-check的安装55份完整captured marker身份，其原marker SHA逐项匹配、记录状态全部absent，本审当前再查对应`/proc/<pid>`全部不存在。source另161份原身份记录亦全部absent，当前对应`/proc`无一存在。两个集合分别保留其捕获范围，不拼造未捕获进程身份，不把发信号或仅僵尸拒绝称为完整回收。源码／installed tests内真实wait与parent-SIGKILL的实际reap／absent断言继续按原场景成立。

已读根追加交付末节和PLAN当前checkpoint：准确产品、安装／模板结果、旧红例、内部constructor producer边界及正式runtime待办均明确。`final-inputs-r3.json`的head为提交前baseline，记录同一完整patch；后续candidate-r3.json与本审Git对象核验将它绑定到固定提交，不把这个历史字段误称新提交。根仍需在实际导入后更新其状态，公开推送及候选自己的CI另验；这不构成本片本地产品导入阻断。

**最终两轴：需求符合性approve；可维护性approve。R1关闭，新增finding0，开放finding／本片验收阻断0／0。允许普通导入准确产品 `1f57ca46e3e10115e8dd8cd9537f0011f6f505e3`。** 接受的是已接纳内部v2边界上有界诊断S的原raw留存及truthful unknown合同；不认证正式SDK producer／V2或v3注册、ordinal1、完整M1c、M5／M6效果、真实服务／GPU或训练质量。有限window、磁盘故障、D-state及并发祖先替换的既定限制保持。

本次只静态读取原件、重算字节／执行位／Git身份及查询已捕获PID存在性，未重跑昂贵测试、安装、模型、服务或训练；未修改产品、测试或其他文档，未commit／merge／push。只追加本报告及更新其当前结论。历史含完整环境的私有证据未再次输出，仅读取允许的安全投影。
