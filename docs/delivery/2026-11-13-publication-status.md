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
