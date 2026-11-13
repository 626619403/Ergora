# F9b4：原训练准备入口

日期：2026-11-14；首片基线 `fad53478c9261157b3016563b410b9d4b4d85b9d`。承接[工作台总计划](2026-11-14-training-workbench.md)及[取消交付](../delivery/2026-11-14-training-cancellation.md)。F9b3已普通推送并核完整Ref；自己的CI `43516776101`8job／30必要步骤Success、原独立两轴发布／CI终核通过，不借前片结果。每片完成实现、实际验收、新的独立审查及精确发布后更新本页。

## 原 owner 与分片

原 `agent_platform.training.cli(init)` 已对已有基线作内容比较，首次创建委托原 `perfctl.main(init)` 的锁、验证和原子文件发布。原 `register_runner` 使用 `core.write` 默认不可变写入；不同内容不会覆盖同ID。原 `prepare` 按全局manifest→项目manifest→spec逐件发布，`core.write`也是不可变的，但进程中断或冲突可留下部分文件。之前仅凭函数正文推测runner会覆盖不成立，以实际 `core.write` 为准。

|片|范围|验收出口|
|---|---|---|
|F9b4a 基线初始化|CLI／HTTP／页面预览完整baseline、确认项目revision和内容SHA；直接复用原init。当前基线同内容可重试，不同内容拒绝，未获回复后重新读取原文件。不新增实验表或基线迁移协议|原验证器、真实Git身份、registration／路径绑定、原文件保持；实际非editable安装、页面迟到／双击／三视口、原模板自身审查与新的独立两轴；自己的发布／CI|
|F9b4b 可信runner登记|固定项目／repo、完整argv／timeout和稳定ID，显式确认后调用原register_runner；沿原不可变写入，重复相同输入可读取，不把登记当执行授权|原runner完整内容与SHA、跨项目共享ID冲突、输入／回执丢失恢复、无命令执行；先立本片验收细则|
|F9b4c 精确prepare|明确原多文件发布／恢复语义后，冻结完整draft、原baseline与runner，按稳定实验ID调用原prepare；中断只恢复原操作，不修改冲突件或换ID绕过|真实中断点、部分发布及冲突保持、三原文件／原binding对账、无start／runner；先立本片验收细则|

真实GPU、原逐实验run-local、精确evidence批准和集成／复验仍归F9c／F9d及原owner。本片不启动服务、申请资源、运行训练、采用候选或改业务试用仓库。

## F9b4a 合同与实现位置

- `training.py` 是CLI和Web共用应用入口；预览只读，初始化要求当前published训练项目及正整数revision、预览返回的canonical SHA256。原始JSON格式不参与内容SHA；原文件字节SHA另列，不混称。CLI原始文件和原生序列化文件各受1MiB界限约束，HTTP既有4MB请求上限另保留，不截断。
- reference子进程继续隔离各项目的config／state环境，使用原process monitor有界执行与收尾。原reader已用的baseline验证机械提为同一函数供reader／setup实际复用，仍调用原perfctl的ident／commit／sha原语；实际发布直接交还原training init使用的 `perfctl.main(init)`，保留其锁、重复检查及原子发布，不复制发布算法。仅首次原子单文件初始化，无需另建操作账本；失联后重读原文件、相同内容显式重试。
- baseline.commit须为该注册Git根内存在的完整commit，但不要求等于开发项目的base_sha；两个基线各有用途。原init不证明基线测量／质量或性能收益。
- registration、执行目录规范路径及有界JSON读已在原提交owner使用；若抽取共同上下文，限于实际setup／submission两个消费者的机械共享，不将训练初始化依赖Task／start语义。保持283冻结文件。
- 预览与初始化均不依赖Temporal SDK、不查询服务。源码核对后选择直接进入原perfctl发布owner，避开原training模块的无关SDK导入；实际初始化仍因原fcntl锁只支持Linux／WSL2。Windows原生预览沿现有no-follow reader；未实际测试的OS明确保留。
- 页面在当前基线旁展示JSON预览和完整SHA确认。编辑输入或切项目使旧预览／回复失效；双击只发一次，错误不冒称已初始化。成功后重读原baseline。已有不同基线不提供覆盖按钮。

## 验证与状态

复用现有registration／training／runtime夹具和显式CI分组；新增检查只保护错项目、漂移、无回复重试、路径越界、旧预览或错误SHA等可能静默损坏。不得为可见普通错误／文案堆测试，不无理由重跑全部仓库。安装包核源码／两RECORD／283；实际CLI和HTTP同合同，浏览器生命周期与原件保持；用原结构审查模板检查本仓库，再以新的fresh-context reviewer做需求／结构两轴。

当前：F9b4a实现及本地实际验收完成。首轮独立两个P2（CLI原文件限读／Windows预览Git路径）最小修复后，r2包570／两RECORD／283、受影响20安装测试／11.39秒、实际SDK-free和完整页面／27原件／收尾、自身聚焦approve均核过；r1五suite57通过／232.41秒保留其旧包范围。r1页面脚本重复选择导致timeout原件保留，r2仅修验收同步并完整重验。新的独立两轴最终本地原件补核通过、开放0／0；精确发布／自己的CI尚待。后续记录见[交付](../delivery/2026-11-14-training-baseline.md)及[公开证据](../delivery/evidence/2026-11-14-training-baseline.json)。

接续：F9b4a `fe26796a…`普通发布、27个Git blob／完整Ref及原两轴固定发布身份补核已通过，自己的CI `43520929146`第四份原run／8job／30必要步骤Success，原结构轴CI终核通过。F9b4b已按[单独计划](2026-11-14-training-runner.md)完成r1包／安装40项／真实CLI与页面／原件及收尾／自身审查，新独立两轴最终原件补核通过0／0，未借本片CI关闭runner自己的发布要求。F9b4c下一片细化原多件恢复语义。
