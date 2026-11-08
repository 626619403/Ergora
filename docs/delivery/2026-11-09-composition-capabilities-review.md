# AC3b.4 能力矩阵与准入出口独立审查

日期：2026-11-09。审查者：fresh-context reviewer `/root/composition_capabilities_review`，未继承实现会话。以原始需求、精确切片和实际代码为依据；仅写本报告及个人 `.ergora/checks/ac3b4-capabilities/reviewer-r1/` 证据，未修改生产或测试、安装依赖、调用模型、提交或推送。

## 范围与身份

基线和 R1 审查时 HEAD 均为 `ce4fc4b26c783431ba1c9aa7f8a0875b2ff88954`，分支 `refactor/architecture-foundations`。原始十文件及 SHA256 见 [R1 scope](../../.ergora/checks/ac3b4-capabilities/review-r1-scope.json)，已读固定 [R1 diff](../../.ergora/checks/ac3b4-capabilities/review-r1-tracked.diff) 及新增[交付记录](2026-11-09-composition-capabilities.md)全文。diff SHA256 为 `ee251fbc5f74f7a6ac1af82ba817981b5198d02d00535a7ecb86892877ff04ac`。十文件为 README、AGENT_BACKENDS、PLAN、WORKFLOW_DEFINITIONS、交付记录、agent_backends、agent_runs、cli 及两份调用／MCP测试。前片 task-mcp 两份状态追加排除；本片不接 AC3c 正式 manifest／批准或 AC4 嵌套调度。

已读 AGENTS、PLAN 最新检查点、用户指定的 AIHERO 索引，以及 code-review、maintainable-project-delivery／independent-review、codebase-design。另用两个 fresh 只读子上下文分别核 Standards／Spec，因可用槽位限制先后运行；主审查者另行追踪完整调用链并执行机制探针。没有将实现者通过日志或自身模型决定当作独立结论。

R2 修改开始后，个人[身份记录](../../.ergora/checks/ac3b4-capabilities/reviewer-r1/scope-checked.json)明确记录已变化的工作树文件；R1 动态探针使用单独冻结的 **362 文件原安装包**，其中三份变更生产文件逐字匹配 R1 scope，避免混用后续工作树。其对应 wheel 为 `7a8c3dfea4f926d18ca39bc1315955502e6d8999b79988a93e28d9c2cda678d0`。该冻结是原包证据副本，没有另行安装。

## Standards

**R1 结论：范围内无硬规则违规或可证维护性 finding。**

- `agent_runs._admit_input` 留在既有用例所有者内，由 `check_input`／`run_input` 两个真实生产用例消费。完整输入、祖先权限和材料仍由 `workflow_definitions.inspect_input`／原编译器拥有，未另建权限模型或调度器。
- `composition_policy` 是既有 `AgentBackend` seam 的实际扩展；Codex／Claude 各自说明 sandbox、认证和原生伴随工具差异，局部 `_restricted_policy` 仅共享两个真实实现的同形字段。只声明模式、没有能力合同的新后端明确失败。CLI 只从原 catalog 取得注册名，角色／模式／配置资格仍归准入，未增加上层厂商分派。
- 新分支分别对应调用模式、外部权限请求、缺失 SDK、后端不支持模式及完整父链。父链来自已重编译并核一致的结构结果；无需再添加猜测环或重复权限检查。原 `agents.invoke` 的二次校验继续保护直接调用者。
- 未新增依赖、基础模块反向导入或公共模块。新增链展示为一次实例 map 和结构深度遍历；完整输入重验仍是既有有界 I/O 的主要成本，未发现有证据支持的性能必改项。未进行峰值内存／吞吐测量，也不把字节和文件上限当作性能保证。

## Spec

**R1 结论：原限定合同范围内无新增 finding；已采纳的推理配置前移调整待同片复核，本片暂不终结。**

已核 `check_input` 在创建 run／scope／原生进程前调用同一准入所有者；`run_input` 从该准入文档增加运行身份与终态并保存同结构 policy。报告含请求／实际 binding、覆盖理由、supplied-grant → root → parent → leaf 完整权限链和所有继承资源来源，资源正文不进入运行列表。

报告分开完整内联、固定附件和实时 workspace；read 路径只是许可上限。固定附件仅 task-mcp 支持，write、shell、工具 origin 网络、外部 MCP、实时 workspace 和宿主隔离均明确不支持；必要 write／shell／network 请求在模型前拒绝。Codex 的 read-only 是 advisory 请求，不能由定义 sandbox 扩权；Claude 没有冒称 OS sandbox。报告明确未探测 CLI／认证／模型容量，仍保留推理 HTTP、stdio、日志／State 写入及 `formal_execution_authorized: false`。普通 native、默认 text-only、原 MCP／取消／结果处理没有被本片重写。

### 已采纳的准入范围调整：推理文件晚拒绝

自身真实模板审查另提出 P2：R1 `check_input` 不接收 `codex_config`；坏 TOML／provider 文件会在 `run_input` 已保存 run／输入副本、task-mcp 已预检后，才由 `CodexBackend.command` 拒绝。个人[机制探针](../../.ergora/checks/ac3b4-capabilities/reviewer-r1/probe-r1.py)在冻结 R1 包复现该时序：`freeze → launch 配置 → stub 预检 → launch 配置 → failed/finished`，尚未进入模型执行。没有启动实际 MCP server 或模型。

R1 CP1 明确不接受推理配置参数，公开手册也明示不检查推理文件；因此两个独立轴均将其作为原设计公开边界，而非因 R2 改动倒推原合同违规。实施方现采纳扩大准入范围：`check-input` 接受可选 `--codex-config`，由 Codex 原所有者共用无副作用解析／编码，在建立运行或服务前拒绝本地坏配置。这是明确、最小的接口调整；不能扩写成 provider 健康／模型可用性验证。修正及其实际身份待后续追加。

## 已执行检查与局限

个人 [R1 结果](../../.ergora/checks/ac3b4-capabilities/reviewer-r1/probe-r1-results.json)共九例：四后端／模式组合在阻断模型、进程解析／运行、scope 冻结、MCP launch／probe 和 socket 连接后均成功展示完整报告；前后个人 State／输入文件逐字不变，无运行行或目录。另核仅声明模式但无 policy 合同拒绝、覆盖后端也不能绕过当前定义准入（check／run 各一）、缺顶层 SDK 拒绝，以及上述推理文件晚拒绝红例。

实现者记录的首轮源码／非 editable 包各五套 **141 passed／6 skipped**、后续 CLI catalog 定向 **12 passed／37 deselected** 及十二次实际 CLI 已读；清单不同，没有相加或冒称本审查重跑全部测试。R1 的四组合报告、注册但不合格后端和权限拒绝日志与代码路径相符。父片 CI 不属于本片验收。

本次独立动态检查仅在 Linux／Python 3.12 对冻结 R1 包运行；未调用真实模型、原生 CLI、认证或外部服务，没有重跑已归前片的完整 MCP 生命周期。原生 Windows 的 task-mcp 仍明确拒绝并引导 WSL2。本片精确 Git 候选、自身必要 CI、远端终结，以及采纳调整后的最终包与真实自审尚待对应证据，不登记完整交付。

## R2／R3 同片独立复核

保留上述 R1 原结论与公开边界。本节在相同基线继续复核修正，没有重新定义原验收或使用后片 manifest 工作树代替本片候选。两个只读轴分别核过增量；最终生产／测试对应 [R3 scope](../../.ergora/checks/ac3b4-capabilities/review-r3-scope.json) 的十文件，固定 diff SHA256 为 `af0c7bd23b74ea339b9b947bfa2cae2360748204d57b61ac9d591bfe07f30431`。

R2 scope 的配置前移版本，diff 为 `9e7bab85a54052ba7f9e2fb1afaeda136dfa947bd6a737ed94aef81bb890bcb5`，对应 r3 构建 wheel `eb9333920e648523fb1f5747994ab5016b8da5fd9a23e060732b92be0ddfce6a`。个人冻结该包后，以基线 Git 对象加三份精确变更源码重建预期文件集，与该 wheel／安装副本的 **362 文件**逐字一致，参考文件未变；后续工作树变化另列，没有借用新源码验证旧包。结果见 [R2 identity](../../.ergora/checks/ac3b4-capabilities/reviewer-r1/r2-identity.json)。

最终 R3 scope 对应 r4 构建 wheel `efe09b026a4ebe471aeb6d11e7901f6355c771d2dedbbe20443e9dcadccf2f26`。2026-11-08 21:02:31 UTC，个人核十文件与 scope、固定 diff、源码／wheel／非 editable 安装的 **362 文件**及基线加精确变更的预期集全部一致，**283 冻结身份**保持。最终包另行冻结保存，详见 [R3 identity](../../.ergora/checks/ac3b4-capabilities/reviewer-r1/r3-identity.json)。之后的公开证据和状态追加不改变该生产身份；后片 `composition-manifests` 准备文档排除。

### Standards

**最终本地结论：通过，无未解决 finding。**

`CodexBackend._options` 有 `composition_policy:119` 和 `command:178` 两个真实消费者，文件解析、受限字段选择与编码仍归后端原所有者。`agent_runs:90` 只沿原工厂传配置，不增加厂商分派；CLI 两入口转交同参数。只读轴 AST 核对确认，抽出的原算法除 `request.mode`／`request.task_mcp` 参数替换外与基线一致，native 命令余部未改；最终严格编码仍在原字段所有者转换错误，没有再添解析器或备用路径。

主审另对七种有限值 native／text-only／task-mcp 命令构造逐字比较，R1、配置前移版和最终包完全相同，见 [command compatibility](../../.ergora/checks/ac3b4-capabilities/reviewer-r1/command-compatibility-results.json)。该比较只构造命令，没有执行原生 CLI，不扩大为原生运行或 OS 保证。

### Spec：采纳改进与已证实问题

**配置前移调整已落实。** 个人 [R2 probes](../../.ergora/checks/ac3b4-capabilities/reviewer-r1/probe-r2-results.json) 共二十五例，其中缺文件、无效 TOML、provider 非表和日期不能编码四种配置 × 两模式 × check／run 共十六次，均在阻断全部 scope／模型／进程／服务入口时可读拒绝，State／输入逐字不变且无 run 行或目录。四组合有效检查无副作用；Claude 保持忽略 Codex 专用选项；四次以本地进程／预检 stub 执行的调用与检查 policy／binding 一致。后四例是受控机制测试，不是原生协议或模型验收。

**SP-1 · P2 · 扩展配置准入遗漏 TOML 非有限数，最终已关闭。** R2 `agent_backends.py:169` 使用默认 `json.dumps`，`nan`／`inf`／`-inf` 可编码为 `NaN`／`Infinity`／`-Infinity`，不满足新扩展的本地 JSON 兼容准入保证。自身第二次真实审查指出后，主审使用固定 R2 包独立复现六种值／模式组合：检查成功且命令构造保留这些非标准字面量，未启动运行、服务或模型，见 [R2 red](../../.ergora/checks/ac3b4-capabilities/reviewer-r1/nonfinite-r2-results.json)。实际原生 CLI 将如何处理这些字面量未由该探针执行；本地兼容检查漏拒绝本身已有证据。

最小修正在同一编码点增加 `allow_nan=False`，既有字段错误转换同时接 `ValueError`。个人用最终冻结包重跑三值 × 两模式 × check／run **十二次**，均在任何运行／scope／服务／模型入口前拒绝，State／输入不变，见 [final green](../../.ergora/checks/ac3b4-capabilities/reviewer-r1/nonfinite-r3-results.json)。该项属于 R2 扩大合同后的真实缺口，不倒推 R1 CP1 违规；最终没有未解决 Spec finding。

实现者修后 r3 包五套 **188 passed／7 skipped**、最终严格编码源码及包各 **11 passed／30 deselected**，以及 r3 的十六次实际 CLI 证据已核其记录和范围。最终单行修正后没有冒称重跑全部五套或十六次 CLI；原包非有限数红例的实际记录是 **6 failed／4 passed**，没有改写成十项全失败。个人身份辅助脚本曾误计生成的 pycache、误判原始 JSON 字段形状，已修正并重新核验；这些辅助错误未计产品失败或验收通过。

### 最终真实自审原始回执

主审没有重复调用模型，只读核了已有 r4 自审运行 `cc5c5236a81c4b129edbd276e4c7ffa0`：实际 Codex／`gpt-6.1-sol`／本次 `high` 推理配置，110.34 秒、CLI 0／`succeeded`，结构决定 `approve`。绑定记录保留用户授权的 Codex／ChatGPT 回退原因，没有将其写成异后端实测。证据见 [independent hosted verification](../../.ergora/checks/ac3b4-capabilities/reviewer-r1/hosted-r4-verified.json)。

五份受保护源码／测试的精确 SHA 与最终 scope 相符；按实际全文及指定上下文 diff 重建的附件 **52,413 字节**，SHA256 `af043a783def152edbab4f987141a1f2315b908b437aebe3a557e0b855646f27`，与固定 scope 和原生返回逐字一致。实际有七次附件 read，其中 0、12,000、24,000、36,000、48,000 五页连续覆盖全文，末页 4,413 字节且 `next_offset=null`，另有两次完整读取；连同 Skill／list 共九次 MCP 调用。

原输入和运行快照重验、完整 prompt／实际 stdin、CLI JSON／只读 SQLite、检查／运行 policy、scope／native receipt 及结果文件摘要逐项一致。原生 argv 确为 read-only，关闭 shell，任务工具恰为 list／read；预检与 native 两个已记录服务 PID 在审查时均已退出。原报告明确仅审供应源码，CLI 与 task-mcp 测试为上下文 diff，未执行测试，也没有检查未供应的旧实现；其 approve 不替代本独立调用链审查或本片 CI。

**本地终结：Standards 通过，Spec 通过；SP-1／P2 已关闭，采纳的配置前移调整已落实，无未解决阻塞 finding。** 本片精确 Git 候选、自身必要 CI 和即时远端终结仍须后续独立核验；原生 Windows 新模式、认证／provider 容量、OS 隔离、正式批准和完整嵌套执行均未扩大为已验。下一动作是本片最终 scope／静态与普通精确交付，不等待尚未创建的 CI 才给本地结论。

## 精确候选 Git 对象核验

2026-11-08 21:10:00 UTC，独立核固定候选 `582b16a4fba75a7e52f5d2f8287499de21ad9cf4`，唯一父提交为原基线 `ce4fc4b26c783431ba1c9aa7f8a0875b2ff88954`。实际差异正好十五文件，全部 Git blob SHA256 与 [final scope](../../.ergora/checks/ac3b4-capabilities/review-final-scope.json) 一致。保存的 tracked diff 覆盖原十一份跟踪文件，另四份当时未跟踪的新文档／公开 JSON 均已从候选读取全文 blob 核对；没有把十一文件 diff 当成完整十五文件。独立完整候选 diff SHA256 为 `7730dc5cbff999c7cbfac4c89283eaa57d9fe575b3090fa1a255264004656746`。

直接从该固定 Git 对象读取全部 **362 生产文件**，与最终 `efe09b026a4ebe471aeb6d11e7901f6355c771d2dedbbe20443e9dcadccf2f26` wheel 和个人冻结安装副本逐字一致。按候选 `reference-manifest.json` 逐项核 **283 冻结文件**，均符合 manifest 且与父提交字节一致。候选公开自审身份／结果 JSON 与已核 r4 原始回执一致。后片 `composition-manifests` 准备文档确实不在候选树内。

可核结果见 [candidate verification](../../.ergora/checks/ac3b4-capabilities/reviewer-r1/candidate-582b16a.json)。该检查不使用后续工作树作为候选证据，也未提交或推送。Standards／Spec 本地结论保持通过；候选自身 CI 和即时远端终结尚待对应 run／远端回执。本追加属于原片审查状态归档，不属于上述已创建候选的 Git 树。

## 候选自身 CI 与即时远端独立终结

2026-11-08 21:21:05 UTC，独立重新抓取官方 [run 42523659092](https://github.com/626619403/Ergora/actions/runs/42523659092)、精确两个 job 页面，并从该 run 的 `jobGroupsFetchUrl` 取得完整批次（`batch=0&size=200`）。run 整体状态为 `Success`，提交链接绑定完整候选 `582b16a4fba75a7e52f5d2f8287499de21ad9cf4`，workflow 为 `portability.yml`。完整批次 `totalCount=2`、`hasMore=false`，实际 job ID 正好为下表两项，没有遗漏后续批次；使用的是独立直接抓取，未用父代理先前下载的页面替代。

| 官方作业 | 必要步骤的独立结果 |
| --- | --- |
| [Windows／Python 3.12，128862379653](https://github.com/626619403/Ergora/actions/runs/42523659092/job/128862379653) | `Build and install wheel`、`Packaged reference identity`、`Native application regression`、`Windows PowerShell 5.1 installer and upgrade` 全部成功 |
| [Ubuntu／Python 3.11，128862379855](https://github.com/626619403/Ergora/actions/runs/42523659092/job/128862379855) | 上述构建、参考身份和应用回归三项全部成功 |

各必要 `check-step` 均为 `data-conclusion=success` 且有 `data-job-completed`，`data-log-url` 精确绑定该完整候选与对应 job ID；两页没有失败、取消或超时步骤。原始官方页面、完整批次及各自 SHA256 随个人证据保存，结构结果见 [CI final](../../.ergora/checks/ac3b4-capabilities/reviewer-r1/ci-42523659092/final.json)。此前进行中回执分别保留，没有把步骤先成功当作整体 CI 已完成。

紧接上述成功核验，使用既有逐命令 SSH 传输执行只读 `git ls-remote`；**2026-11-08 21:21:05.510377 UTC** 返回 `refs/heads/refactor/architecture-foundations` 精确指向完整候选 `582b16a4fba75a7e52f5d2f8287499de21ad9cf4`。本次没有修改 Git 配置、提交或推送，SSH 命令及凭据未打印或另存，也未使用后片已变化的 `workflow_definitions`／CLI／schema／测试工作树推断该候选源码身份。

**最终结论：Standards 通过，Spec 通过；全部已知 finding 关闭，固定候选自身双 OS 必要 CI 与即时远端终结核验完成，本片可收口。** 双 OS CI 覆盖候选的应用回归和安装路径；本片 task-mcp 运行验收仍限 Linux，原生 Windows 仍明确拒绝并引导 WSL2，认证／容量、OS 隔离、正式批准及完整嵌套调度没有扩大为已验。本追加是执行后的原片审查归档，不属于上述已执行候选的 Git 树。
