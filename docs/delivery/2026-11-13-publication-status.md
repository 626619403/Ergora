# 2026-11-13 普通发布与跨平台 CI 状态

分支`refactor/architecture-foundations`已普通推送到`00922d302daa371ab980093889a8468694c10a94`，退出0／6.793秒；随后正常SSH `ls-remote`返回同一完整SHA，退出0／1.324秒。使用已有RSA及已有代理连接方式，没有强推、凭据或SSH配置更改。原407／握手与官方HTTPS超时是早期失败样本，不代表此次推送失败。

该精确提交自己的[Portability 43373597757](https://github.com/626619403/Ergora/actions/runs/43373597757)在两次官方REST样本中为in_progress；第三次REST为403限流。随后一次官方run／两job HTML读取取得终态：

|执行环境|必要步骤|最终范围|
|---|---|---|
|Linux／Python3.11|wheel构建安装、reference身份成功；Native application regression取消|job页面明确`The job has exceeded the maximum execution time of 20m0s`；没有取得全量日志，不推断特定测试失败或死锁|
|Windows／Python3.12|wheel构建安装、reference身份、native regression、PowerShell5.1安装升级全部成功|四必要步骤completed／success|

整体run为Cancelled，`required_steps_passed=false`，不能关闭跨平台出口；也不能借这个后续候选的CI关闭早前B2／C精确提交。没有触发重跑、取消或更改远端CI。

原始公开响应的身份：run body SHA256 `394d0305ac29563f9bf35a1a1ad2d939d57150d213e00bcee5ba1da39b808353`；Linux job body `c3c6d27ca5b311c0374ee4ba309297baebfd130d59abcf427c201b7047fbc631`；Windows job body `359a31f7cefdc88f59cd7366f2c8173ee63ea153db71c32ae82be1c50d113ec1`。命令、push／Ref回执、原HTML／HTTP回执及离线必要步骤投影保存在本仓库私有验收目录`publication-2026-11-13-r1`，运行数据不进Git。

下一步先获取可读的末段日志或在已核非editable安装中按相同Linux suite有界记录逐测试进度／durations，区分累计必要检查与卡住的具体路径，再决定修正实现、等待方式或CI分组／预算。不会仅以放宽期限或删掉故障／生命周期检查宣布问题已解决。B1只读资料和A2真实模型旅程的本地验收各自继续记录。

## 后续本地有界采样

已用原A1非editable产品和`00922d3`精确tests子树运行相同Linux suite选择：92份tracked测试／fixture等文件逐字相等，其中71份`test_*.py`，不是92个测试模块；本地Python3.12，远端为3.11。共collect 1,696项，在30分钟外部截止后沿原进程owner停止，最终为cancelled／-9；已写终态891 passed、26 skipped、0 reported failed，进度54%，没有完整suite通过或最终durations。

最后一条在途为`test_backup_failure_prevents_any_migration`，只有最后位置不足以证明它卡死。没有据此把耗时归因为stdin、Temporal或某项迁移测试。原stdout SHA256为`c672440d4f9fd57f3a1b2e506e8ece67c6bb470c4d410258de8151186b77f7bd`；92文件身份清单SHA为`e0ab7d0f4defccb5ac1c0ed6c63e061403d160e609f64798aa6db2bcfd0075f5`。采样驱动、watchdog、request、原stdout、终态和summary均保存在原publication checks的`linux-profile-r1/`。

该采样是不同机器／解释器上的旧精确候选数据，不能替新修正包或远端CI授予通过。已开始独立只读test／CI成本审计；下一测量须保存每项实际耗时和未完成路径，再决定最小CI调整及完整覆盖验证，保留必要停止／恢复检查。

## 独立成本调查与首个分阶段探针

[独立只读报告](2026-11-13-linux-ci-profile-review.md)已完成：Linux原回归1182秒后触及整个job上限；Windows原回归816秒。可证重复的reference身份检查只有秒级成本，不能据此删除生命周期／失败恢复测试或宣称超限已解决。

按报告建议，在原A1非editable安装和原测试源码运行最后未完成的单case，逐阶段立即保存事件：setup 0.169秒、call 0.021秒、teardown 0.00015秒，pytest为1 passed／0.70秒，探针整体1.173秒完成。原case及产品身份与原采样相同，本地仍是Python3.12。该结果只排除独立条件下必现的该迁移慢路径，不能排除前序污染或解释完整suite累计成本；没有修改产品或CI。原件保存在同publication checks的`linux-migration-probe-r2/`。下一测量应保留原suite逐项phase与完整退出结果，再据实选择CI分组或预算。

已在独立Python3.11环境安装原A1 wheel，逐文件核源码／wheel／安装相等和283 reference身份后启动同一原Linux suite；92 tracked／71测试模块与00922逐字保持，依赖清单单独保存。`linux-profile-r3/`实时写每项setup／call／teardown及完整collection nodeids，不依赖终态durations才留数据。控制器使用已核process owner与明确4500秒stop callback，达到边界则沿原收集／reap退出；75分钟仅是本次调查的外部边界。该采样仍在途，不能用它关闭新候选安装、完整CI或远端出口。

### 采样驱动的spawn入口问题

该采样中已有九个`test_research.py`用例报告失败，首个原State记为`Source fetch process ended without a result`；不能继续将本次采样描述为零失败。独立命令行`python -I -m pytest`重跑首case为1 passed／1.40秒。随后把原计时驱动仅缩至同一case得到稳定red：1 failed／0.89秒，原stderr显示spawn重新执行未保护的驱动，在`phases.jsonl`的独占创建处抛出`FileExistsError`。仅给同一驱动增加`if __name__ == "__main__"`入口保护，同case为1 passed／1.46秒。产品、测试、解释器和安装均未修改，原失败与日志保留于`research-probe-r6/`至`research-probe-r8/`及同前缀stdout文件。

这确定了首case的采样驱动故障，不是产品修复，也尚未逐项关闭其余八个失败。原完整计时继续收集实际phase，终态应保留这些失败；随后以正确入口补测受影响模块并检查相同原trace，再分别判断覆盖、成本和CI调整。新CI应通过独立pytest子进程加载观测plugin，避免让自定义顶层驱动成为spawn的主模块。旧远端超限原因仍须完整成本数据支持，不能借此把原Cancelled改为通过。

后续仅修正入口的`research-probe-r9`已跑完整原research模块：11 passed、1 skipped／11.39秒，全部phase及退出0落盘。原九个失败nodeid都在这次模块范围中通过；原完整采样的失败trace仍待终态输出核对，不能覆盖或删除原失败，也不能据模块补测声称整个原suite已通过。

### 固定边界与未完成项续测

`linux-profile-r3`在预定4500秒边界沿原owner停止，实际4500.222秒、cancelled／-9，未放宽该边界。原pytest未写最终footer／完整失败trace；原九个research失败保留，首case的驱动red／green与全模块补测只能分别授予相应范围，不能补造九份原trace或单次全suite通过。

已按原collection nodeid顺序减去所有完成teardown的项，仅对未完成项启动`linux-profile-r4-tail`；原92份tests身份再次逐字核准，沿同一旧产品／Python3.11／依赖，使用独立`python -m pytest`和已实测的观测plugin，不再以自定义顶层驱动作为spawn主模块。续测明确1800秒停止边界，不重跑已完成项。模块／进程隔离与原连续运行不同，最终只合并为覆盖和成本记录，不宣称原连续suite成功。观测plugin另以全research模块11通过／1跳过、受控失败完整判词和实际中断前phase落盘探针通过；CI代码尚未改变。

### 分段成本已齐与新CI候选

原233项tail已退出0：227 passed、6 skipped、36 subtests passed，pytest391.72秒／控制器393.593秒。原1463完成项与tail233的并集恰为原1696、交集0。原采样仍为cancelled且九失败保持；没有将分段补测称连续suite通过。pytest9.2在父call报告前发出子报告，因此成本使用每node／phase最终父报告，不重复累加36子报告；剔除r3未完成node的1.104574秒setup。去重后阶段成本4875.574秒／75文件，详见[公开成本投影](evidence/2026-11-13-linux-ci-costs.json)，原两份phase日志保留。

[CI分组计划](../plans/2026-11-13-linux-ci-shards.md)现采用六个显式整文件组，原job20分钟上限保持，每组本地估算812.58–812.63秒。正式pytest plugin保持独立入口并记录report类型／完整失败；workflow从同一JSON生成matrix且尝试上传已落盘观测。新候选Python3.11非editable安装521产品／两RECORD／283身份相等；全量1708collection与六组254／250／342／312／251／299并集相等、交集0。代表research／process／installation／submission-lock检查31通过／5跳过57.86秒，仅授予此范围。正式负向／失败／中断探针已通过；独立审查发现提前skip起点缺失及最慢文件文字两P3，已改外围wrapper并修正文案。r2四模块31通过／5跳过58.00秒、103phase起点齐全；修正后原结构模板48.881秒approve，完整12文件与原件的新独立两轴通过、开放0／0，见[交付与审查](2026-11-13-linux-ci-shards.md)。普通推送／新候选自己的CI尚待完成；原Windows通过不继承。
