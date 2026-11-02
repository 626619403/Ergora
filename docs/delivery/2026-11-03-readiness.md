# F2.2：分层诊断与修复指引

日期：2026-11-03。分支 `refactor/architecture-foundations`，基线 `a6bf1249772a16c5c660e77a4df1996457f76636`；开始时工作区干净。用户授权持续按计划实现、独立审计及提交推送。完整 F2 仍包含后续服务管理和综合验收。

## 合同与设计

现有 `tools.doctor` 被 CLI 和 Web dashboard 共用，仅检测安装，不能把安装等同认证、连接或任务就绪。沿用现有有效配置、组件描述、程序解析及进程树清理；保留旧 `project/checks/reference_runtime`、`installed` 和平台提示字段。新增版本、认证、连接、任务可用性和修复指引，包含配置来源及修订；未知保持未知。任务可用性指该绑定的声明操作前置条件，不替代真实任务验收，也不代表六阶段执行器已就绪。

默认保持本地安装检查，不主动连接外部服务，不执行用户 command 或模型。显式 `--probe` / 受保护 POST 探测原生 CLI 版本、Codex 凭据状态和外部绑定 TCP 可达性；总探测预算 1–30 秒，单个子进程复用现有跨平台清理。原始命令输出丢弃，版本只提取版本号，认证只使用退出状态，不输出账号或密钥。Codex 凭据存在不代表服务接受、额度充足或模型请求已成功；TCP 可达不代表服务协议、认证、worker 和任务已验收。未有稳定只读协议的工具仍明确 not_checked。

性能基线：当前一次 doctor 对继承角色进行 7 次 availability 调用、仅 2 种有效绑定；合成每次 10ms 的本地探测耗时 0.0813s。证据 `.ergora/checks/f2-readiness/baseline/performance.json`。拟仅在单次查询内复用相同绑定检查，下一请求重新检查，避免跨请求陈旧缓存；不是实际模型或远端速度结论。

所有行为保留在实际所有者 `tools.py`，CLI/API/工具页直接消费，不新增插件框架、依赖或数据库格式。冻结 283 文件保持；服务启停归 F2.3，正式任务归 F3。

## 验收计划

1. 缺程序/SDK、无效继承、平台不支持、凭据未知及缺凭据分别展示并有修复指引；默认绝不执行任意配置命令或访问网络。
2. 显式探测的版本解析、凭据输出隐藏、同请求复用/跨请求重查、TCP 可达与真实服务/任务未知分离、总预算和子进程超时清理有合同回归。
3. CLI/API 等价，工具页可主动探测并展示分项状态。非 editable wheel、全量适用回归、基础无可选依赖安装、冻结身份、真实浏览器和精确两 OS CI 按改动范围验收。
4. 新 fresh-context 审查者独立核结构、实际复用、性能证据和交付身份；修正后推送并继续 F2.3。

## 进度

完成调用盘点、官方接口核对和基线测量，开始实施；尚无新增功能通过结论。官方 Codex CLI reference 已获取，说明 `codex login status` 返回 0 仅表示凭据存在：https://developers.openai.com/codex/cli/reference/ 。官方搜索工具无返回，改为直接读取官方页；Claude 文档暂未取得，其认证不推断为可用。

## 实现及本地验收

已实现 CLI/API/工具页分项诊断，主动探测只执行固定版本/凭据状态命令及有界 TCP 子进程；自定义 argv 不执行。单请求复用相同绑定，下一请求重新检查。Forge 的本地 Git 版本检查也增加 5 秒上限。12 项新合同回归通过；最终非 editable wheel 全量 Linux 回归 300 passed、18 skipped、36 subtests passed（144.48s）。wheel SHA256 `3ae804ad5a607e84f463c8eece64ecdba60e71633181acafaf6ce67df0b9c7be`，源码/wheel/开发及新基础环境 337 文件一致，冻结 reference 283 文件 PASS。

新基础 Python 3.12.3 环境无 Web/Temporal/GEPA，真实 CLI 默认及主动诊断均通过；缺 Temporal SDK 保持 blocked，关闭端口保持 not_confirmed，不产生任务或模型调用。性能在同一基线项目/10ms 合成 availability 下由 7 次降到 2 次、0.0813s 到 0.0352s；本地 25 次默认诊断中位 0.00756s、最大 0.01063s，Python3.11.15。仅本地检查数据，非模型/远程性能结论。证据在 `.ergora/checks/f2-readiness/`。

浏览器旅程及精确两 OS CI、独立审计待完成；无这些维度的完成声明。下一项 F2.3 继续使用原 Supervisor，仅管理显式所选服务。

## 独立审计修正

初审指出 Temporal 带 scheme 的兼容地址被错误解析，以及主动诊断后卡片/标签切换仍保留旧分项。两项已修正：地址按实际是否含 scheme 解析；前端把主动结果保存到当前项目的同一服务器快照并重绘，过期项目/刷新响应不回写。新增裸地址/http/https 的真实 TCP 回归，修正后 15 项定向通过。初候选 `4622370f5cdb1b5fbdcbbcd3d75db2866f7e8bed` 已推送；其 CI 41505762773 仅是初候选，不用来证明修正后候选。正在重新安装修正 wheel、回归、浏览器、精确两 OS CI，最终身份另记。

地址 finding 复核又覆盖缺省端口和显式零端口：HTTP/HTTPS 无端口分别使用 80/443，裸 Temporal 地址默认 7233，显式 0 拒绝且不回退到其他目标。新增四项合同回归，当前 19 项定向通过。完整回归、wheel 与 CI 均以最终候选重新记录，不沿用前候选通过结果。

审查者用原生 SDK 1.34.0 及拦截 connect 的探针核实：不带端口的裸 Temporal 主机也经 SDK 的 http:// 默认连接 80，并非本地开发服务惯用的 7233。已据此修正该回退及测试；显式配置 127.0.0.1:7233 不受影响。非 HTTP/HTTPS scheme 明确拒绝，不猜测其他目标。前一段的裸 7233 是被此证据修正的中间实现，不是最终合同。独立性能复测五次也确认 7→2 次调用，仅据此主张请求内去重。

## 最终候选验收

最终源码/测试 `1f78235ae6e155cc18c51d052817cdd5fa4f79d0`，最终 wheel SHA256 `bddd0b9b017d93bf6f845303796d016e2c0f2607c5d33b01eeb62e41bb6a6a11`（sdk-final-dist）。337文件在源码、wheel、开发/新基础安装一致；最终基础环境两次真实CLI和缺SDK/缺服务诊断通过。独立源码复审20项通过，两P2关闭。

实际浏览器使用最终安装包：主动Codex只读检查返回版本0.166.0、credentials_present，task_availability仍not_checked。卡片/详情一致，切标签保留结果；390px无溢出；用受控延迟响应证明刷新后旧诊断不覆盖新快照。证据 browser-final.log/browser-delayed.log 及 output/playwright/f2-readiness-final-mobile.png。没有执行模型。最初默认浏览器revision缺失，改用已有headless shell配置成功，未安装新依赖。

最终性能重测同一项目10ms合成探测2次、0.03184s；真实默认25次中位0.01059s、最大0.01245s（Python3.11.15）。与初测条件相同，主张仅为请求内避免重复检查；波动及源码独立复测见审查报告，不外推模型吞吐。最终完整Linux回归、精确CI41507301574、最终审查和远端身份仍在收口。

最终生产包完整 Linux 回归 308 passed、18 skipped、36 subtests passed（147.74s），源码/资源身份保持。但 CI41507301574 的 Ubuntu 成功、Windows 一项超时夹具失败：测试将整个 processes.resolve_program 替换为 codex，连 Windows gate 内真实 Python 的解析也被替换，造成 not_confirmed 而非 timed_out。已把替换限定为 codex 程序，保留原 Python 解析、原超时与清理断言；这是测试夹具修复，生产包不变。后续精确测试候选重新跑两 OS CI，不使用此前失败 run 充当完成证据。

## 完成交付

F2.2完成。[独立最终复核](2026-11-03-readiness-review.md)通过，两P2均关闭，无未解决阻塞。生产源码1f78235、最终测试候选`ede2dc2e00c6ef00fbf8220505d89b0f22ecf315`（仅Windows测试夹具修正）已推送并核对远端。最终bddd…6a11 wheel与337文件×两安装/归档保持一致，283冻结文件通过；Linux最终308 passed/18 skipped/36子测试，测试夹具修正后20项定向通过。

[精确CI41508379597](https://github.com/626619403/Ergora/actions/runs/41508379597)全部成功：Ubuntu125493456323的包/冻结/完整适用回归、Windows125493457063相同检查及真实PowerShell5.1安装升级均通过，官方HTML完整SHA/日志绑定和证据摘要已独立核实。先前41507301574的Windows夹具失败保留且不充当通过证据。

当前继续[F2.3](2026-11-03-services.md)的服务生命周期；停止后再启动必须获得实际停止确认。完整F2还需F2.4，不从doctor版本/凭据/TCP检查推导真实任务验收或效果。
