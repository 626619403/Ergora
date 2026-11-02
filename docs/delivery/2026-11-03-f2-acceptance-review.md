# F2.4 综合验收与 F2 阶段出口独立审查

日期：2026-11-03。审查者：fresh-context 独立 reviewer `f2_acceptance_review`，未参与实现。依照 `AGENTS.md`、maintainable-project-delivery 的独立审查要求及 review-pr 流程，先读原始要求、差异和验收脚本/产物，再读作者叙述与前序审查。

## 结论

- **需求符合性：通过。** F2.4 的组合旅程补齐当前安装、诊断和所选服务的 CLI/API 验收；F2 的交付范围、平台边界与未验维度清楚。最终候选的两 OS CI 已独立核实成功，可以按该范围关闭 F2 并进入 F3。尚未完成的真实服务协议、模型效果及正式任务入口不能由本结论推导。
- **结构、实际复用与维护性：通过。** 审阅范围内无已证实的阻塞 finding。F2.4 没有新增生产代码；F2 各切片继续使用组件描述、既有安装器、诊断所有者、统一注册与 Supervisor，没有第二套任务调度器、持久格式或只供验收使用的生产抽象。
- **性能证据：通过其有限主张。** 最终日志路径有实际测量且读取有界，诊断只主张请求内避免重复探测；没有证据支持模型、远端服务或整体任务吞吐提升，也没有作此完成声明。

上述结论绑定生产/测试候选 **`67d88eccb209ab77b31b13461ff6b237a8224e08`** 及最终 wheel SHA256 **`4d9f23118c434cbf368de33da037add286de44e342f340e78f214ef17e3526fe`**。审查期间作者开始准备后续 F3.1；后续工作区与提交均不纳入本次 F2 通过范围。

## 范围与原始证据

F2.4 审查起点及运行候选均为上述提交，起始未提交变更只有 `docs/PLAN.md`、`docs/plans/2026-11-01-all-in-one.md` 与新增 [F2.4 验收记录](2026-11-03-f2-acceptance.md)。阶段结构核查另查看 F1 最终 `4ffcfdd` 至该候选的 F2 生产差异，以及 [F2.1](2026-11-03-installation-profiles-review.md)、[F2.2](2026-11-03-readiness-review.md)、[F2.3](2026-11-03-services-review.md) 的独立审查与修正记录。

先检查的原始资料：

- `.ergora/checks/f2-acceptance/{linux-install-journey,services-journey,diagnostics-journey}.py`，对应 JSON、旅程日志、五份实际安装日志和 `installer-identity.json`。
- `.ergora/checks/f2-services/utf8-final-verify-package.py`、最终 wheel、包身份 JSON、`utf8-final-wheel-regression.log`、`utf8-final-targeted.log`、`performance.py`、`utf8-final-performance.log`。
- `.ergora/checks/f2-services/ci/` 中原始官方 run/job HTML、run selection、来源摘要与校验脚本，以及候选的 `.github/workflows/portability.yml`、`tests/windows-installation.ps1`。

检查实现与真实调用者包括 `components`/`data/components.json`、两平台安装器、`tools`、`services`、CLI/Web 入口、`registrations`/reference 边界、当前架构和公开手册。没有把前序报告的通过结论直接当成本切片的运行证据。

## 需求与证据对应

|需求|核实的证据与结果|边界|
|---|---|---|
|Linux 用户目录安装、重复升级、数据保持及离线失败|Python 3.12.3 实际 Bash 安装 5 次：control → development → research → research/旧参数叠加 → control；22 次 CLI，项目、绑定、修订及哨兵保持；空缓存明确失败且不生成入口|完整预备 wheel 缓存、禁用索引；降组合保留已有 SDK，与手册一致；没有模型或服务启动|
|Windows 用户目录安装、升级和入口保护|精确候选 Windows job 成功执行原生 PowerShell 5.1 验收：control → research → research/旧参数叠加；空格/Unicode 路径、SDK、重复安装、数据和外来入口保护|没有单独 Windows development 安装、降组合、离线缓存或本地 Supervisor 实测；不从 Linux 扩称这些组合已验|
|分项诊断、缺工具/认证/服务及修复指引|11 次 CLI 与同源主动 API；缺命令 blocked，ReMe TCP 可达但缺 token 仍 blocked，未监听 Temporal 端口 not_confirmed；默认无主动探测，项目保持|TCP、凭据存在和任务验收分开；2.946 秒含 CLI 开销，仅验证 5 秒主动预算条件|
|所选服务全流程及跨入口恢复|15 次 CLI、两次重新创建 TestClient 应用；统一注册/发布一致性、CLI/API 配置相同，所选进程 PID 保持；旧 revision/缺确认拒绝；停止、重复停止、重启、shutdown 均确认|真实 Supervisor 4.3.0 和冻结 launcher，但 `temporal` 是受控无模型进程，**不是实际 Temporal server**；两次应用重建不等于浏览器或真实 HTTP 服务进程重启|
|有界日志与游标|8192 字节默认中文窗口成功；API 返回游标交给新 CLI 读取追加中文/emoji；前序真实定向回归覆盖分片 UTF-8、overflow、截短轮转和 FIFO 拒绝|原始字节窗口有界；文本替换/JSON 转义后的响应可能增大，手册已有说明|
|不启动未选后台服务、不改权威配置|服务旅程检查其他程序保持 STOPPED，原 ini、项目和注册投影不变；测试 fixture 在 finally 中清理其临时 daemon|不把进程 RUNNING 当协议、worker、队列或模型就绪|

原始结果为 **22 + 15 + 11 = 48 次 CLI**，其中服务旅程两次拒绝场景按预期返回非零；不能把“48 次”理解为全部成功返回零。综合脚本没有模型调用。服务旅程首轮公开 definition 输入错误已保留在过程记录，修正的是验收输入，没有放宽产品 schema。

## 结构、复用与性能审计

安装配方由 `data/components.json` 集中，Bash/PowerShell 在 bootstrap 时直接读取；`tools.installation_profiles` 的两个真实生产消费者是 CLI 与 Web。没有要求启动前先安装 Ergora/Web，也没有把安装组合变成第二份持久项目配置。

分项诊断保留在 `tools.doctor`，CLI、dashboard 与主动 API 共用；同绑定在单请求内复用，跨请求重新检查。版本/凭据/TCP 子进程沿用 `processes` 的超时与清理；任意 command 不被主动执行。此前去重性能使用相同项目与合成 10ms 探测，调用数从 7 到 2；真实默认诊断的小样本时延有波动，因此只认可避免重复调用的结论。

`services.status/control/logs` 被 CLI 和 Web 两个不同生产文件直接调用。私有上下文、配置准备与原子写入归属于同一服务资源生命周期，单一调用并不构成抽取通用模块的理由。两个 Unix transport 类实现标准库框架 hook；覆盖 request 的目的在于防止变更 RPC 被默认重试。原 Supervisor 拥有进程状态，Ergora 只校验注册/修订/归属、生成关闭 autostart 的独立配置并观察确认；未复制持久调度或正式任务状态机。

最终 `services.logs` 通过 Supervisor 取得原生日志路径，以非阻塞 open、普通文件检查、seek 和一次 `read(limit)` 读取，再用标准库增量 UTF-8 解码器处理边界。没有整文件 materialization 或随日志总长度增长的扫描。实际最终测量条件为 Supervisor 4.3.0、冻结 launcher、受控无模型进程、64 MiB 稀疏 ASCII 日志：

- 40 次 4096 字节日志读取，中位 **2.478 ms**、最大 **3.625 ms**；客户端/daemon 峰值 RSS 增量 **792/172 KiB**。
- 20 次 status，中位 **2.520 ms**、最大 **2.926 ms**；启动 **0.184 s**，shutdown 确认 **0.164 s**。

这些数字来自已读取的实际脚本和最终日志，不是本 reviewer 重跑的数据。没有与旧路径作同条件统计比较，不能称为已证明的速度提升；它们支持该条件下的有界读成本。F2.4 自身只增加验收与状态文档，不新增性能热路径。中文窗口的正确性由独立旅程和前序定向检查支持，不把 ASCII 性能样本扩称中文/真实服务负载测量。

## Reviewer 实际检查

1. 独立读取候选 `git archive`，逐项重算候选中源码、脚本、测试、CI 与 pyproject 的 **375 个文件**；检查当时工作区与归档一致。候选源码、wheel、开发安装、基础安装和本轮实际 Bash 安装的 **338 文件完全相同**，最终 wheel SHA 与记录一致。
2. 独立重算全部 **283 份冻结参考文件**，均符合 manifest。两处 wheel 安装的 `direct_url.json` 指向最终 wheel 且无 editable 标记；其中 `archive_info` 未提供摘要，包身份结论来自前述独立内容哈希，不依赖缺失字段。
3. 实际运行 `PYTHONDONTWRITEBYTECODE=1 .venv-dev/bin/python -B -m pytest -q --tb=short -p no:cacheprovider tests/test_architecture_boundaries.py tests/test_components.py`：**15 passed，1.80 秒**。`git diff --check`、`bash -n scripts/install.sh` 通过。
4. 独立核对 CI 来源文件大小/SHA，解析原始官方 HTML：run **41514705189** 为 Success、commit 链接为完整候选；Windows **125515156473** 与 Ubuntu **125515156969** 的 job/平台对应，包构建安装、冻结身份及应用回归步骤均 success/已完成，Windows 另含 PowerShell 5.1 安装升级；各日志 URL 同时绑定完整候选 SHA 和精确 job，无 failure/cancelled/timed_out 步骤。此项为对已有官方缓存的独立核验，未宣称重新从网络获取页面。
5. 已读最终本地回归实际日志：**324 passed、19 skipped、36 subtests passed，164.58 秒**；最终定向日志为 **24 passed、1 skipped**。没有为文档切片重复完整套件、重新安装或重跑已验旅程。

## Findings 与剩余范围

上述需求、候选身份、实现边界、复用及证据范围内，**无已证实 finding，无需生产修正**。F2.1/F2.2 与 F2.3 已修正的前序 findings 保留在各自报告，不另立重复问题。

仍未验的维度包括上表列明的 Windows 组合、真实 Temporal/MLflow/worker/队列协议、真实 Agent 认证与模型任务效果、GPU、空白 Windows/winget 和本轮未运行的实际服务进程重启/浏览器恢复。它们需要各自环境与运行证据；当前 fixture、CI 和 TestClient 不能代替。F3/F4 的正式任务与界面旅程尚未由本报告验收；下一项是独立的 F3.1 只读任务入口。

本轮只写本审查报告，未改生产源码、安装软件、调用模型、操作用户服务、提交或推送。后续若修改 F2 生产代码、安装器、测试或打包配置，应按实际影响重新绑定证据并复审。
