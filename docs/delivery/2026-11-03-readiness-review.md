# F2.2 独立审查及结构、性能审计

日期：2026-11-03。审查者：Codex 独立代理 `f2_readiness_review`，使用 fresh context，未继承实现讨论。按项目 `AGENTS.md`、`docs/PLAN.md` 及 maintainable-project-delivery 的 independent-review 规则执行；仅检查源码、运行适度检查并写本报告，未修改源码、安装、提交或推送。

## 范围与身份

原始要求：持续执行 all-in-one 计划，完整节点审计结构与性能。F2.2 将有效绑定的版本、认证、连接、任务可用性分开显示，提供有界显式探测及修复指引，默认不调用模型；保留原结果和平台提示、冻结 283 文件。服务启停属于 F2.3，正式任务属于 F3。

基线 `a6bf1249772a16c5c660e77a4df1996457f76636`；初审开始时为全部未提交差异，随后相同实现提交为 `4622370f5cdb1b5fbdcbbcd3d75db2866f7e8bed`。已读取实际完整 Git 差异及初始 `review.diff`，包括原先未跟踪的新测试和交付记录。生产修正复核至 `1f78235ae6e155cc18c51d052817cdd5fa4f79d0`，包含 `9c858001f64a8b85d27bde66fac51f0759a837a4` 和 `6700ffc36b84bf5bf3cc780dc84f6939f528d0e1` 的修正；最终测试候选为 `ede2dc2e00c6ef00fbf8220505d89b0f22ecf315`，仅追加 Windows 夹具修正与记录，生产内容和 1f78235 完全一致。后续 F2.3 工作区不在本次审查范围。

检查文件：`src/ergora/{tools,cli,web,kernel}.py`、`src/ergora/data/console/tools.js`、`tests/test_readiness.py`、README、USAGE、AGENT_BACKENDS、PLAN、all-in-one 计划及本切片交付记录。邻近调用者包括 agents、processes、bindings、components/描述、projects、scheduling、console 的 app/state/api/ui，及已有配置、工具、Web、平台回归。

## 结论

- 需求符合性：通过。初审两项 P2 均已复核修正，最终包、完整 Linux 结果、真实浏览器、精确两 OS CI、归档和远端身份均已核对；`ede2dc2` 范围内无未解决阻塞 finding。
- 所有权与维护性：通过，本次范围内没有结构性阻塞。职责保留在现有所有者，实际复用成立，没有新增依赖、插件框架、数据库格式或抢入后续服务/任务职责。
- 性能：确认单次请求内相同绑定去重有效。已测数据只能支持本地安装检查成本的结论，不能外推模型、远程服务或整体任务速度。

## Findings 与修正复核

### P2-1：Temporal 探测必须保持实际绑定的目标地址语义

初审位置：`src/ergora/tools.py:127`（`4622370`）；邻近消费者 `src/ergora/scheduling.py:63` 等直接将原 `address` 交给 `Client.connect`。

可达场景：合法旧绑定 `http://127.0.0.1:34567` 通过现有 binding 校验，当前 Temporal SDK 的 `ConnectConfig._to_bridge_config()` 保留该 URL；初版 doctor 无条件前加 `//`，实际生成的 TCP 目标却是主机 `http`、端口 `7233`。独立复现拦截了 `processes.run`，没有发出网络请求。其后果是错误地把可用服务报告为不可确认，或检查另一目标。

最小修正：地址解析与实际 SDK 接受的形式一致，再从同一目标确定主机和端口，保持显式端口。

复核：`9c85800` 已按是否存在 scheme 解析；无 scheme、HTTP、HTTPS 三种带显式端口的真实 loopback TCP 合同回归均通过。`6700ffc` 又补齐 HTTP/HTTPS 省略端口的 80/443 回退及显式 0 的 invalid_endpoint。该版仍有同一 finding 的裸主机边界：现有 SDK 会先给 `127.0.0.1` 补 HTTP scheme，原生传输使用端口 80；doctor 却回退 7233。独立使用临时 libc connect 拦截器拒绝全部连接，`Client.connect("127.0.0.1")` 明确输出目标 `127.0.0.1:80` 和 `REVIEW_CONNECT_PORT=80`，没有建立网络连接。`1f78235` 已将裸主机与 HTTP 默认端口统一为 SDK 实际使用的 80，HTTPS 使用 443，保留显式端口，并拒绝显式 0 和不支持的 scheme；测试的裸地址预期同步纠正。最终源码 20 项诊断合同独立通过，此 finding 已关闭。

### P2-2：主动探测后工具卡片继续显示旧的分项状态

初审位置：`src/ergora/data/console/tools.js:73`（`4622370`）；卡片的版本/认证/连接来自 `data.tools.checks`。

可达场景：已安装 Codex 的默认卡片显示 `not_checked`，主动探测返回版本和凭据状态后，初版回调只替换详情 JSON，没有更新 `data.tools` 或重绘卡片。于是分项展示与成功探测后的详情不一致；切换标签再回来还会丢失该探测结果。原浏览器断言只检查正文存在 requested/remediation/字段名，不能证明卡片值更新。

最小修正：在当前项目/当前快照仍有效时回写同一诊断快照并重绘，使卡片、详情和标签切换消费一致数据。

复核：`9c85800` 的 `tools.js:74`–`76` 已检查 `app.data` 对象和当前项目身份，回写 `data.tools` 并调用现有 `render`；`app.js` 的实际调用者已提供该回调。最终 `browser-final.log` 在真实 Codex 0.166.0 / credentials_present 情况下检查卡片与详情、切标签保留及 390px 无横向溢出；`browser-delayed.log` 通过延迟版本 999.0.0 的响应证明刷新后不被旧结果覆盖。跨项目的身份保护已按调用路径检查，未另做浏览器用例。此 finding 的源码及代表性浏览器验证均已关闭。

## Windows 夹具修正复核

旧精确 CI [41507301574](https://github.com/626619403/Ergora/actions/runs/41507301574) 绑定 `1f78235`：Ubuntu job 125489765558 成功，Windows job 125489765343 的 Native application regression 单项失败，页面注解为 `test_whole_active_budget_includes_child_timeout` 得到 not_confirmed 而非 timed_out。本审查独立读取对应官方页面证据，未把该失败 run 当作通过证据。

原因与源码相符：测试无差别 mock `resolve_program`，Windows `_run_windows` 也需用它解析被测试子进程的真实 Python，因而未启动预期的超时进程。`ede2dc2` 保存原 resolver，仅对程序名 codex 返回测试值，其余路径委派真实 resolver；原超时、认证未知、剩余预算、调用次数及墙钟上界断言保持。本审查认为这是修复夹具与真实平台所有者之间的边界，没有降低测试合同或修改生产代码。精确归档提取的 20 项测试在最终非 editable 安装上独立通过（1.81 秒）；新精确候选 CI 41508379597 已在真实 Windows runner 通过原生回归和 PowerShell 安装/升级步骤，最终核对见下文。

## 所有权、复用和必要分支审计

`tools.doctor` 的真实生产消费者是 CLI 和 Web 两个文件；Web dashboard 继续只取默认诊断，新增 POST 明确申请主动探测，页面仅消费该结果。新 `_local_check`、`_probe_check` 各只有 doctor 一个生产调用者，但都是同一所有者内部的完整私有算法，区分本地安装检查与显式探测，未包装成虚假的共享服务。`DoctorPayload` 由真实 POST 请求边界使用，严格验证公开预算参数有明确接口职责。

有效配置及其校验复用 projects/bindings/components；程序解析和主动子进程复用 processes。单请求以完整有效绑定为键，结果按层复制；下一请求重新探测，没有跨项目或跨请求缓存。新增的无效配置跳过、缺程序/平台拒绝、解析失败、预算耗尽、进程错误及版本不兼容分支均有可达外部条件。临时私有目录、有限版本读取和仅返回状态保护原始凭据输出，未重复引入业务状态机。前端修正的身份判断保护跨项目/刷新期间的异步响应。地址解析修正及 SDK 证据见 P2-1。

未修改冻结 reference、六阶段门禁、正式结果/批准身份、服务启动或后台探索。未知认证、TCP 可达和任务前置条件仍分别表示；安装或端口存活没有被提升为模型或正式任务验收。默认本地检查仍可能执行既有 mini/Forge 的安装检查；手册明确主动预算不包括本地安装检查和清理，不能把主动 1–30 秒预算解释为整个 doctor 的硬时限。

## 实际检查与性能边界

- 初审独立运行 `tests/test_readiness.py tests/test_project_configuration.py tests/test_projects_tools.py tests/test_web.py`：36 passed；`9c85800` 相同集合：39 passed。以上两轮均使用非 editable 开发安装、禁写 bytecode 和 pytest cache。`6700ffc` 显式 `PYTHONPATH=src` 的诊断合同为 19 passed；默认端口的 SDK 语义问题不被该轮测试的 7233 预期覆盖。曾在最终包尚未重装时误用旧 wheel 运行新增回归，产生 3 项失败；已确认属于候选身份不匹配并从源码重跑，不将该轮作为最终包的回归结果。最终 `1f78235` 同样通过 `PYTHONPATH=src` 独立运行诊断合同：20 passed，1.88 秒。仅出现既有 FastAPI/httpx 弃用警告。
- 已审阅作者初版 wheel 完整 Linux 日志：300 passed、18 skipped、36 subtests passed，144.48 秒；最终 `sdk-final-wheel-regression.log` 为 308 passed、18 skipped、36 subtests passed，147.74 秒。本审查没有重复整个测试套件，初版和最终结果分别记账。
- 独立只读核对初版 wheel SHA256 `3ae804ad5a607e84f463c8eece64ecdba60e71633181acafaf6ce67df0b9c7be`，337 文件的源码、wheel、开发及基础安装均与记录一致。最终又将 `ede2dc2` 的 Git archive 在内存中独立展开，337 文件逐一匹配最终 wheel、身份记录和两个安装；生产内容与 `1f78235` 无差异。最终 wheel SHA256 `bddd0b9b017d93bf6f845303796d016e2c0f2607c5d33b01eeb62e41bb6a6a11`，冻结清单 283 文件也在 wheel 内逐一核对通过。
- 独立从源码执行 `reference.verify()`：PASS，283 文件；基线至当前的冻结目录无差异。检查过 `git diff --check`。
- 作者基础 CLI 的两份真实报告区分缺 Temporal SDK、默认未探测与关闭端口；自定义命令未执行。本审查未重复浏览器，已阅读最终脚本及成功结果，按 P2-2 所列实际范围接受最终浏览器证据；原版较弱断言保留为历史证据。

性能记录的合成条件是每次 availability 固定延迟 10ms、同一基线项目：作者测量调用数 7→2，单次耗时 81.3→35.2ms。本审查另从精确基线 Git 内容加载旧 doctor，以只读 SQLite 项目快照分别运行五次相同合成条件：旧版每次 7 调用，中位 71.37ms；候选每次 2 调用，中位 20.90ms。该独立复测不包含作者 `State` 初始化等成本，绝对数值不能直接拼接，但确认消除了五次重复安装检查。

作者初版 25 次真实默认诊断中位 7.56ms、最大 10.63ms；最终 performance.json 的同条件合成结果仍是 2 次调用、31.84ms，25 次真实默认中位 10.59ms、最大 12.45ms，均为本机 Python 3.11.15 的本地测量。波动符合结论仅针对重复探测次数的界限；没有相应的旧版真实分布，不能作为整体真实速度提升的比较。版本/凭据/TCP 子进程共用单调时钟预算，DNS 在子进程内并复用现有进程树清理；超时回归覆盖进程超时与剩余预算。外部协议、namespace/worker、账号额度、真实模型任务和 GPU 效果未验，本切片没有对此作通过承诺。

## 最终 CI、归档和远端核对

2026-11-02 19:26 UTC，本审查独立核验 [CI 41508379597](https://github.com/626619403/Ergora/actions/runs/41508379597)。保存的官方 HTML 与 `ci-html-status.json` 记录的长度/SHA256 一致；另从官方 run 页面及两个 job 页面重新读取，三个请求均 HTTP 200。独立解析确认 run 的完整提交链接为 `ede2dc2e00c6ef00fbf8220505d89b0f22ecf315`、状态为 Success，两个 job 的必需步骤已完成且日志 URL 均绑定该完整提交及对应 job ID：

- [Ubuntu / Python 3.11，125493456323](https://github.com/626619403/Ergora/actions/runs/41508379597/job/125493456323)：Build and install wheel、Packaged reference identity、Native application regression 均成功。
- [Windows / Python 3.12，125493457063](https://github.com/626619403/Ergora/actions/runs/41508379597/job/125493457063)：以上三项及 Windows PowerShell 5.1 installer and upgrade 均成功。

没有用初版或旧失败 CI 替代最终候选。再次从 `ede2dc2` 的 Git archive 读取生产内容，337 文件逐一匹配最终 `bddd0b9b017d93bf6f845303796d016e2c0f2607c5d33b01eeb62e41bb6a6a11` wheel；该候选测试文件 SHA256 为 `ca7dc4e793e6b406acd6b65af5aee0ea9d90865cf3269283a94c2b9dc17c3a66`。此次核验未读取工作区 F2.3 源码来代替已验收归档。

2026-11-02 19:25:17 UTC，独立核对 origin 等价指向授权的 626619403/Ergora 仓库，`git ls-remote` 返回 `refs/heads/refactor/architecture-foundations` 精确为 `ede2dc2e00c6ef00fbf8220505d89b0f22ecf315`，与最终 CI 一致。

F2.2 独立审查完成，无未解决阻塞项。交付所有者据此更新计划及交付状态；当前未提交的 services、CLI/Web、pyproject 等 F2.3 增量不在本次通过范围，须独立审查。完整 F2 仍含 F2.3/F2.4，F3 保持后续职责。
