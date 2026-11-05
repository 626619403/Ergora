# G0.1 独立审查：全新安装、登记与无模型旅程

日期：2026-11-05。审查者：`/root/g0_onboarding_review`，本片新建的 fresh-context 独立审查者；先读取原始范围、实际补丁和两份新增文档，再核作者记录与原证据。适用项目规则为根 `AGENTS.md`，并按 maintainable-project-delivery 的独立审查流程执行。本轮只写本报告，没有修改生产、测试、CI、依赖或其他文档，没有安装、启动服务、运行模型、提交或推送。

## 审查身份与范围

基线与审查时 HEAD 均为 `cd0b5a0a7d5301e30ba5febe45e4e73ba7e218a4`，分支 `refactor/architecture-foundations`。逐项重算 `.ergora/checks/g0-onboarding/review-scope.json` 的 11 份文档 SHA256，全部相符；实际 tracked diff 逐字等于 `review-tracked.diff`，没有生产、测试、依赖或 CI 变更。

完整文件范围如下，两份新增文档均已阅读全文：

- `README.md`、`docs/USAGE.md`、`docs/AGENT_BACKENDS.md`。
- `docs/PLAN.md`、`docs/architecture/current.md`。
- `docs/delivery/2026-11-05-f5-completion-review.md`、`docs/delivery/2026-11-05-f5-completion.md`。
- `docs/plans/2026-11-01-all-in-one.md`、`docs/plans/2026-11-05-evidence-handoff.md`。
- 新增 [G0.1 交付记录](2026-11-05-new-user-onboarding.md)、[G0 分片计划](../plans/2026-11-05-new-user-acceptance.md)。

必要源码检查覆盖冻结参考的 `agent_platform.cli.task_action`、`doctor.report`，以及现有统一 CLI、`reference` 安装身份校验、正式提交和服务管理所有者。私有脚本、原命令与日志、现存持久数据和截图是验收证据，不作为新增生产接口；下一片尚未执行的辅助文件不在本片范围内。

## 需求符合性结论

**G0.1 本地验收与文档符合约定范围，通过；范围内 no findings。精确文档交付尚未完成，完整 G0 仍未完成。**

公开 Bash 安装器确实以 development 组合在先前不存在的持久 app/bin 路径完成非 editable 安装，实际 exit0、58.78 秒。另建基础接收者与原生依赖 venv；后者按原 lock 及 require-hashes 同步，实际 exit0、54.62 秒。这些时间只描述已有工具、缓存和认证条件下的原命令，不代表空 OS 安装性能。

独立从现存 app、接收者、工作树资源及原 wheel 重算：各 352 个包资源完全相同，283 个冻结资源相符；新 runtime 的 53 个受校验 Python 文件、lock 和固定二进制也相符，原生 venv 不是旧环境软链接。app 的 direct_url 是源码目录的非 editable 构建，安装日志的新 wheel SHA 为 `40064f8b1c186caffd2dbced6a18722e5c238c86b68383b108ddc85e8ef56c11`；只有接收者使用原 `f644858498143dc077bf77114235f9896d01f5da6b008dd984684b5a2c521166` 归档，未混称同一 wheel 字节。接收者实际没有 Temporal SDK。

两个新业务 Git 根各有一次完整 register 和一次公开角色修订，当前均为 revision2；新控制库只有两项目行，其他业务表为空。9 项可信基线检查的实际命令、成功输出及操作者目录中的合同均已核对。两模板 preview/create、相同意图重复创建、旧 revision 拒绝、离线合同和创建记录的证据一致。首次缺服务 start 实际 exit2；没有 attempt/result/run，原 submission 保持 prepared。重复 start 返回原记录并 exit1，现有 CLI 源码明确只对 submitted 返回0；没有重新派发。

首轮辅助脚本误期待上述重复 start 为 exit0，整条命令的真实 exit1 及原脚本均保留。后续脚本只读回首轮22项成功记录，补做其余命令并 exit0。独立重算为53个实际子命令：40次 Ergora CLI、9次可信检查、4次 Git；归一旅程52项与额外一次正确 exit1 的重复 start 分开记账，没有把首轮失败抹去。

新 HTTP／浏览器交互原记录是14次 API GET、零 POST、零 pageerror；readiness 和初载请求另计。两个恢复窗口的 submission SHA 与原 CLI 一致，390px 页面与弹窗宽度核验无水平溢出；视觉检查了 prepared 手机图及 large-change 桌面／手机错误页三张代表截图。两次 status400 的真实响应是 Temporal connection refused，输入 `unsubmitted-g0-read-probe` 明确只是测试 opaque 值；未冒称原生 run 或真实运行观察，也没有点击恢复按钮。

现存两新任务文件语义等于各自 creation intent，新文件摘要等于最终基线；两个业务 repo 保持干净及原 HEAD，submission 仍只有原 intent。requests/receipts/artifacts/approvals/fences 为空，新 Temporal／claim 库及托管 Supervisor socket 不存在，新 control 库保留。独立重核旧139文件、两旧 repo 的文件／HEAD／refs／worktrees、3条 claim／0 active lease，均未改变。

正式退出证据包含浏览器 close 实际 exit0、HTTP owned 身份检查及 SIGTERM、有序 shutdown 日志和真实 shell143，而不是将信号退出改写为0。审查时两 owned PID 均不存在，四执行端口及 HTTP 端口全部关闭，请求临时目录为空，原 Supervisor ini 摘要保持。

## 可维护性、结构与成本结论

**可维护性通过，范围内 no findings。** 新计划与交付记录位于项目自己的 docs，稳定说明留在已有 README／手册，状态与下一片边界有明确入口。F5 终结追加只记录原片事实：原 `cd0b5a0` 的唯一父提交、12文档、原包身份、普通 push 原命令／exit0／前后远端及最终静态记录均与追加内容相符，没有混入 G0 新安装或重建新的生产验收身份。

冻结 `task_action(start)` 在连接前调用原 doctor，`ready_for_real_tasks` 明确要求 Temporal 和本地 A2A 监听；MLflow 监听不在该布尔准入中。原生 lock 已包含其库依赖。README／USAGE／Agent 手册补全显式 `temporal worker executor a2a` 因而有源码依据；服务管理没有因此隐式补依赖，冻结准入保持，版本化适配边界的解耦仅列为后续 F7。

本片没有新生产抽象、函数、异常分支、断言、测试框架或 CI 作业，未引入单调用包装或机器路径耦合到通用代码。私有安装／验收脚本中的路径与断言用于本次持久环境身份、外部文件、原意图检查点及 owned 进程生命周期，属于具体可达的验收失败条件。可信检查继续放在候选允许路径之外，复用公开 CLI、模板、现有 hash／Git／SQLite／浏览器工具，没有新造引擎或修改评分器。重复创建和 prepared 读取验证幂等边界，未变成冗余的常规 CI；纯文档没有重复重型全量或多 OS 矩阵。

没有生产性能优化结论。安装耗时和请求数绑定实际环境及统计窗口；模型 `gpt-6.1-sol`／medium、600秒／并行2和手工 HTTP provider 选项仅属已记录元数据，未被用作模型效果、认证成功或费用证据。OS 工具／缓存／认证复用与全新应用／数据分开，未将宿主系统包预检失败改写为空 OS 一键通过。

## 检查、限制与剩余交付

除上述只读身份、原命令、源码、SQLite、Git、端口和截图核验外，独立用已核安装的实际 parser 重核11文档的368个本地链接／锚点及 README 的30条命令，全部通过；`git diff --check` 通过。未执行这些业务示例、重新安装、重开浏览器、启动栈或重跑模型／全量回归。原验证命令 `verify-onboarding` 的实际 exit0 与最终数据相符；独立检查没有覆盖或重写作者原结果。

没有阻塞 finding。加入本报告与审查状态后，实施者仍须刷新包含报告的完整 scope／静态清单，形成精确纯文档提交，保留普通 push 的真实命令及 stdout/stderr／exit，并提供提交前后远端 SHA。由同一审查者再从 Git 对象核唯一父、完整文件及摘要、包资源身份，并只读实时确认远端，才能关闭 G0.1；本轮结论不提前代替这些步骤。

随后 G0.2 才恢复 `governance-g0-normal-r1`、`large-g0-normal-r1` 的原 prepared 意图并验真实六阶段、计划批准、取消／重开及证据导出。空 OS、完整宿主包安装、本机 Windows／WSL2 浏览器、真实模型可用性与费用、GPU 和远程 tracker 均未在本片验收；Windows 只保留原精确 CI 支持子集，G0.3 另作综合收口。

## 精确提交与同片最终终结

2026-11-05，同一独立审查者从 Git 对象核候选 `18ed62eb4eb0dba6a27d0535919a394330fa1e45`，唯一父提交为原基线 `cd0b5a0a7d5301e30ba5febe45e4e73ba7e218a4`。`diff-tree` 恰为12份 Markdown，完整文件集合及各提交 blob 的 SHA256 逐项等于 `final-review-scope.json`，原 tracked 部分逐字等于 `final-review-tracked.diff`。初审后仅补审查／交付状态和本报告，未引入新行为；候选中的原审查报告字节保持。终结写入前工作树干净。

独立在内存读取该精确候选的 Git archive，352个包资源逐项等于本片已核安装的完整身份表；生产、冻结参考、测试、依赖和 CI 均无变化。新 app 的源码构建归档与基础接收者的原 f644858 wheel 仍分别记账，没有将资源一致推断为两归档字节相同，也没有将旧精确 CI 当作 G0.1 新运行。

最终静态原命令实际 exit0。审查者另从精确候选读取全部12份文档及引用目标，重核371个本地链接／锚点，并用已核安装的实际 parser 解析候选 README 的30条命令，全部通过；文档摘要、计数及命令列表与最终 `static-documents.json` 相符。没有使用后续工作树内容或执行这些业务示例。

真实 commit、push 外层命令及实际 Git push 的原记录均为 exit0。普通 push 没有强制选项或强制 refspec，原 stdout/stderr 记录正常更新 `cd0b5a0..18ed62e`，前后 `ls-remote` 原输出分别等于唯一父提交与候选。审查者复用同一已授权的每命令传输配置，于 **2026-11-05 00:04:59 UTC** 另行只读实时查询，实际 exit0，远端 `refactor/architecture-foundations` 完整 SHA 为 `18ed62eb4eb0dba6a27d0535919a394330fa1e45`。私有传输配置未写入本报告，其使用不改变普通 ref 更新语义。

结合初审的全新安装、单次登记、无模型 CLI／浏览器、新旧数据保持、正式退出及结构／成本核验，**G0.1 需求符合性、可维护性和精确交付全部通过，无未解决 finding，可登记本片完成。** 本轮只追加本报告，没有安装、启停服务、运行模型、提交或推送，也未重复已通过的运行矩阵。G0.2 的同一 prepared 意图实际恢复、真实六阶段与异常旅程，以及 G0.3 综合收口仍须单独验收；完整 G0 和前述未验平台／效果维度没有因此完成。
