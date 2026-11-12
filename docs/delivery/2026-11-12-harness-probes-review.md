# F8-H1 有界探针与只读后端独立审查

审查者：fresh-context `f8_readonly_harness_review`；Spec 与 Standards 分别由新的独立上下文 `spec`、`standards` 复核。项目根为 Ergora；固定基线及本轮开始时 HEAD 均为 `a35123e4ea3f24b091774f1476c2e159804de560`，分支 `refactor/architecture-foundations`。本报告只覆盖 F8-H1；前片 H0 的终核记账不递归审查。

依据为原始需求、[本片计划](../plans/2026-11-12-harness-probes.md)、[交付记录](2026-11-12-harness-probes.md)、[父计划](../plans/2026-11-12-harness-admission.md)、[父研究](../research/2026-11-12-harness-admission.md)、`AGENTS.md` 与既有调用所有者。适用 `maintainable-project-delivery`、其 independent-review brief、`code-review` 两轴及 `codebase-design`；先读原件，再比对作者叙述。原始需求保留六阶段、精确候选和批准、未知回执恢复、完整祖先资料与父级权限上限；每大项实际自身模板及独立审查，不要求宿主提权，不对真实 SaaS 业务写。

## P1/P2 原始证据预核

本段是探针和适配要求预核，**不是产品实现或完整切片通过判词**。当前两个新增计划／交付文件仍未提交；产品最终变更、包与自身验收清单待作者提供后完整复核。

- 固定身份原件为 `.ergora/checks/f8-harness-admission/dsh-identity-r1.json`：Python 3.12.11，SDK 与 runtime-bin 均 `0.2.2rc2`，六份 SDK 源文件与固定源码 `e8f7b93a344964de3dca1ace9e72b6e4d6de87cb` 身份一致；原件明确没有证明 runtime 二进制由该提交完整重建。
- 直接读取 `probe-mcp-r3` 的 identity／scope／call-plan／十份请求索引和原 body／native-result／MCP 审计，以及离线审计脚本和产物。十份原请求 body 与其索引内容及 SHA256 一致；真实模型请求每次只含 `mcp__ergora_task__list/read`。九次计划工具调用与后续请求的 call/result 对应。
- 按原响应独立重建五件资料，共 72,162 字节；三页 list 依次 offset 0、2、4 到 null，六页 UTF-8 read 均连续到 null，正文及 SHA256 等于 scope，包括 71,019 字节资源的两页。scope SHA256 为 `85ba68880cdfff22fef09e9a9a35e91d9733eed21cfcc68eed645a8a49d0802f`；按既有树身份算法静态重算 13 件 input／11 件 manifest 与 prepared identity 相同，逐件源正文与 scope 一致。MCP 原审计为两次启动、一次成功 tools/list、九次成功 tools/call；服务记录无推理 token 环境变量。
- `denials-r1` 原件支持未授权 bash、未知 URI、65,537 字节超页三次 `isError=true`；原结果 schema 对 `decision=accept` 拒绝。环境标记结论只限本次 AGENTS／Skill 标记。
- `startup-r1` 原结果确为 5.39 秒、两次模型请求、无工具表、工具错误，native `completed`；私有验证器因错误假设存在 tools 字段而 KeyError，未生成 validated。`disconnect-r1` 为 7.08 秒、两请求、`Not connected`／`isError=true`，native 同样 `completed`。当前文档没有把二者称作 SDK 阻止模型或生产适配已经拒绝。
- timeout／普通 cancel／supervised cancel 原结果分别为 25.53／3.90／7.66 秒，原进程所有者分别给 `timed_out`／`cancelled`／`cancelled`、child=-9；各段两个受控 MCP 孙进程以及七个采样身份无存活，无 native 最终结果。脚本的孙进程为不 detach 的普通 Popen，检查明确要求同 pgrp／sid。正向、拒绝、启动、断连分别只支持五／五／四／五个采样身份的清理，不覆盖未采样短命进程。

## Spec

**P1/P2 范围内 no findings；产品和完整 F8-H1 判词待验收。** 两轴原件复核均未发现现有文档把 native 成功、合成响应或清理采样外推为正式准入、真实模型质量、Windows 或 OS 隔离。

正式适配接受结果时必须同时保留原 schema 校验、native completed、任一原生工具错误拒绝和原 task MCP readiness。`agent_runs._run_prepared` 已在原所有者核 readiness；无需在 backend 再造同一检查。完整资料交付与读取、父权限上限须通过实际产品路径复核，不能只借私有探针。

父研究第 218 行列过初始化／慢 MCP 窗口及“针对脱离组孙进程核兜底”。现原件只覆盖慢 LLM 与同组受控孙进程；当前交付准确限定范围。最终应明确其他窗口仍待后片，或补实际所选支持范围的证据，不能把 P2 状态泛化为完整生命周期验证。

## Standards

适用仓库标准还包括 [当前架构](../architecture/current.md) 的 AgentBackend 责任和局部映射要求。现计划沿用 AgentBackend／Invocation／agents.invoke／agent_runs／processes，独立可选 driver 隐藏 SDK 装配，未新增调度器、数据库、基础 SDK 依赖或 CI 工作流；该 seam 符合现有 Interface 与 Locality。未发现应为私有探针新增永久测试框架的依据。

**预检 ST1，P3，待最终候选复核：** `deepseek.py --check` 当前先输出 Python 版本，而 `tools._probe_check` 抽取首个三段数字版本；因此 doctor 可能把解释器版本展示为后端版本，且现正则不识别精确 `0.2.2rc2`。这影响计划要求的固定版本诊断。最小修正应让原诊断消费者可靠展示实际 SDK／runtime 版本，不增加独立诊断框架。此处是代码仍在实现中的早期检查，不替代最终完整 Standards 结论。

## 已执行的检查与未完成出口

审查仅使用文件／Git 读取和标准库对既有 JSON／body 作静态重建，没有运行 SDK、模型、测试、网络或原审计脚本，没有安装、提交或修改生产文件。原 SDK 探针的运行结果来自保留的原件；静态重建未把作者的 passed 字段当作结论。

仍待：最终完整 tracked／untracked 文件清单及精确身份、产品成功和失败路径、固定版本诊断、必要受影响检查、新非 editable 包／283 冻结身份、实际 CLI／用例调用及清理、完整资料和权限链、实际自身模板与原始回执，以及最终完整独立 Spec／Standards。提交、远端 Ref 和自身 CI 的验收另按真实后续证据记账。

## P3 源码与安装证据复核

同片继续复核，基线／HEAD 仍为 `a35123e4ea3f24b091774f1476c2e159804de560`。此段检查完整新增源码和手册，**仍不关闭整个 H1**；实际自身模板、补充生命周期及最终候选清单尚待交付。

检查的产品变更为 `src/ergora/agent_backends.py`、`src/ergora/data/components.json`、`src/ergora/tools.py` 与新 `src/ergora/data/drivers/deepseek.py`；测试为 `tests/test_components.py`、`tests/test_readiness.py` 与新 `tests/test_deepseek_backend.py`。同时读取 README、后端／组合手册、当前架构及本片计划／交付状态；追踪既有 `agents`、`agent_runs`、`task_mcp`、`components`、`processes` 等调用所有者。没有发现 agents.invoke／agent_runs／进程、调度、数据库、基础依赖或 CI 的产品改动。

### Spec 源范围结论

**无新增 finding。** Adapter 的模式合同仅 text-only／task-mcp，既有调用先核模式再建 protocol；原组合准入仍核完整输入及父链权限，write／shell／工具 network 请求拒绝。每次调用新 home／session、固定 profile／patch，不接受任意插件或 argv；完整 prompt、原事件、原终值归本次 protocol。原生完成状态和任一工具错误在 Adapter 拒绝，JSON／原 schema 在既有所有者校验，MCP readiness 仍由原 run owner 核对，无第二调度／状态账本。

五段产品原件已直接复核：State 用只读 SQLite 读取与 run.json 完全相同；重新计算原 input／保存 input 树身份；原 prompt、附加 schema 后 native prompt、binding、scope 身份和全部资源源文件、请求索引／原 body 均吻合。正向十请求、五件 72,162 字节，六页 UTF-8 连续到 null；工具错误和断连 native completed 仍由 Adapter 拒绝，未发布结构结果。启动注入段为原用例函数入口，exit0 但 run.failed；它已经归档 schema-valid result，随后被原 readiness 拒绝，不能把有结果文件当作接受。慢模型段原 15 秒 native budget，含 preflight／清理端到端 17.36 秒 timed_out。原采样与端口清理结论保持其 6／6／5／6／6 个身份范围。

### Standards 源范围结论

**无开放 documented-standard 或 heuristic smell finding；ST1 关闭。** 真实 `diagnostic-red.stdout/json` 保留旧投影 3.12.11；driver 现在先发发行版本，原共用 regex 支持 a／b／rc，`doctor-h1-r1.json` 的实际 reviewer 为 0.2.2rc2、installed=true，认证与 task_availability 仍 not_checked。

Locality 保持在既有后端族：配置和平台声明由组件描述拥有，SDK 装配隔离在独立环境 driver；上层没有新增厂商分支。新增 URL、平台、精确版本和原生结果检查分别保护实际外部输入／支持矩阵／兼容性／已观察工具失败，未重复原 schema 或 MCP readiness。唯一新增 driver 文件具有隔离可选 SDK 环境的真实职责；其 main／版本检查／通知保存均局部使用，不把测试或再导出声称为生产复用。没有发现应删除的推测扩展接口。

七个新参数化用例通过原 agents.invoke Interface 核 native 与 stdout 的独立接受条件及不支持模式的早期拒绝；原组件测试按旧工具身份保护字段，新 binding 与缺 SDK 场景沿原矩阵扩展。readiness 只扩展已存在参数，未增加真实模型、SDK 或永久探针 CI，成本与变化相称。

### 包身份与验证范围

直接按 wheel 和安装 RECORD 逐行重算摘要／字节数，r1／r2 均为 457 个 wheel 条目、452 件产品、462 行安装 RECORD，无差异；两份安装产品均与当前源码逐字一致，283 件原 reference 冻结身份相同，安装 direct_url 指向 wheel 而非 editable。两 wheel 的差异仅 METADATA／RECORD，与 r2 README 元数据变化相符。r2 wheel SHA256 为 `8da7a263f4c2dbd8b826796bdf09d8664d8dc773328906992c1c7d16912674b9`。

读取的实际安装日志为 189 passed／7 skipped、170.60 秒；setup 原件支持离线安装和退出0，原 reference verify 为283／PASS。以上未重跑，未外推为全仓库、Python 3.11／Windows 或真实模型通过。本轮审查仍只读文件与标准库静态核对，没有运行 SDK、模型、测试、网络、原审计脚本或安装命令。完整 H1 判词等待后续原件。

## 补充生命周期与 provider 错误原件

继续直接核脚本、原 result／validated／owner stdout、受控后代身份及原请求；validated 保留字段与原 result、owner stdout 一致。Spec 轴独立复核范围内无新增 finding。

|原件|实际触发与观察|可支持范围|
|---|---|---|
|`probe-supervised-detached-cancel-r1`|6.650636 秒 cancelled；向原 supervised owner 发 SIGTERM；wrapper 的两次 `start_new_session=True` 孙进程均记录独立 pgrp／sid，且等于各自 PID；七个采样身份与两受控身份已停止|原 subreaper 对这两件脱离原组／会话的受控后代清理|
|`probe-supervised-initializing-cancel-r1`|0.502634 秒 cancelled、0请求；脚本见三个进程身份且尚无 MCP wrapper 后代记录后向原 owner 发 SIGTERM；三个采样均停止|MCP 前早期启动取消；不能据此定位某个 SDK wire handshake 边界|
|`probe-supervised-slow-mcp-cancel-r1`|1.502812 秒 cancelled、0请求；wrapper 记下一件同组孙进程后、execv 原 MCP 前 sleep；SIGTERM 给原 supervised owner；五个采样与受控身份停止|MCP 启动／协议探测挂起窗口，不是进行中的 tools/call|
|`probe-group-slow-mcp-timeout-r1`|10.512157 秒 timed_out、0请求；同样在 wrapper 的 execv 前挂起；原非 supervised owner 的10秒预算；五个采样与一受控身份停止|原普通进程组对挂起 MCP 启动的超时清理|

四段均没有 native 最终结果，原记录端口／服务线程已关闭；审查时再读 `/proc`，没有仍匹配原 PID／starttime 且非 zombie 的采样或受控身份。早期提出的三个遗漏窗口已得到上述具名补证；仍不扩大为任意插件、未采样短命进程、进行中的 tools/call 或 Windows 的完整矩阵。

`product-provider-error-r1` 通过原 r2 安装 driver 的真实 CLI，11.631754 秒、exit1／run.failed；脚本确定返回 HTTP500，原请求 body 与索引完全相同且只有一次请求。原 native finish_reason 为 error，Adapter 拒绝，未写结构结果。只读 State 与 run 原件相同，原六个采样身份无存活／端口线程关闭。此段支持该合成 provider 错误无隐式重试，仍不代表实际网关或模型兼容。

## 完整十九文件与本地出口终核

**Spec 通过，开放 finding 0；Standards 通过，开放 documented-standard／heuristic finding 均为 0；ST1 已关闭；F8-H1 本地出口通过。** 两条独立上下文对同片最终清单再次复核，结论一致。本节取代前文“完整判词待验收”的阶段状态；精确提交、推送、远端身份和本提交自己的必要 CI 仍由后续真实原件验收。

固定基线及本次终核 HEAD 仍为 `a35123e4ea3f24b091774f1476c2e159804de560`。完整 tracked／untracked 范围与私有 `candidate-files-h1.json`、实际 Git 状态一致，共十九件：

```text
README.md
docs/AGENT_BACKENDS.md
docs/PLAN.md
docs/WORKFLOW_DEFINITIONS.md
docs/architecture/current.md
docs/delivery/2026-11-12-harness-admission-review.md
docs/delivery/2026-11-12-harness-admission.md
docs/delivery/2026-11-12-harness-probes-review.md
docs/delivery/2026-11-12-harness-probes.md
docs/plans/2026-11-01-all-in-one.md
docs/plans/2026-11-12-harness-admission.md
docs/plans/2026-11-12-harness-probes.md
src/ergora/agent_backends.py
src/ergora/data/components.json
src/ergora/data/drivers/deepseek.py
src/ergora/tools.py
tests/test_components.py
tests/test_deepseek_backend.py
tests/test_readiness.py
```

初版静态十九件摘要已逐件核对。随后 `PLAN`、总计划、父计划和本片计划／交付五件状态更新已另读原文，准确区分初轮探针、已实现只读适配、实际自身模板与尚待精确交付；父计划早期陈旧状态已消除。源码、测试、README 和后端手册没有在已核 r2／模型冻结后更改。H0 收口及本报告的审查记账没有增加实现范围，不递归开启前片或审查自身。

### 实际自身模板的原件重建

直接读取 `self-review-h1.py`、审计源码、冻结清单和二十六份原附件、manifest／prepared／实际输入、原 prompt、scope、Codex JSONL、MCP 回执、原结果及只读 State；没有执行这些脚本。实际运行是 r2 非 editable 安装的随包结构审查模板修订 `1.0.120`，run ID `3b069eeb748d4495aa4a14467f18ee44`，授权 Codex 回退、`gpt-6.1-sol/high`，159.932476 秒、CLI exit0、succeeded／approve。模板与原随包正文相同，定义变化仅修订、叶引用、新证据 Skill 和材料限额；原 definitions 目录移开后仍由冻结材料完成调用，workflow ports 未执行。

用标准库独立重算原树算法：十三件 prepared／实际 input 完全一致，十一件 manifest 与记录摘要一致；祖先／叶正文、两件 Skill 和附件逐件等于 scope 所声明来源，原 parent／grant 的 write、shell、network 上限保持空／false。原 composition、task 与完整 prompt 可重建，prompt 同 stdin 和 protocol 原件；admission 的 binding／policy 与最终 run 相同。只读 SQLite 中原 run document 与 CLI stdout 完全一致。

|身份|独立重算 SHA256|
|---|---|
|实际／prepared input|`2c10d06703f9d9505d9bc88878c4ce3b944079f1017f85829e29befcdaf6ae01`|
|manifest|`57e4423ffe58a5e7d5c7acd66a3aed7aeb6b59ccefb558b96ac4b3f2bc7c47cb`|
|完整 prompt|`e9280c5c7928bbbff51af866cf717bfceec8f8727ed0e81b841900d06293b252`|
|scope|`572e0190e43499070c659356b442b723a718885a181e35f2e11d6b2d39e6eef4`|
|192,448 字节附件|`087eab242e19fd8d8ce9fb5f2098ae713449730712066c1b3bb80762264a2363`|
|原 native stream|`59eb7894ac4be4da9e6db28b4ae3b7a272edbf0cc5933e039b1807455a8608db`|
|原结构结果|`a97d1cfa3c8cfdfad58d0d2f114adea234b0316c14183bf8dbdaef5053508977`|

从原 Codex stream 而非模型自述独立重建全部工具结果：一次 list 完整列出五件 scope；四份指令／Skill 各一页，candidate.txt 九页连续 UTF-8 至 `next_offset:null`，八页各24,000字节、末页448字节，另有两页重复局部复读。全部正文／大小／SHA 与 scope 和原文件吻合，无 base64 未重读或中间遗漏；原 MCP 回执与十六次成功工具调用对应，没有失败工具项。二十六份冻结文件的完整正文、顺序、字节／SHA 与附件逐字一致；其中本片计划／交付在模型冻结后只有已另核的晚期状态更新。

原结构结果与 protocol／归档副本相同，decision 为 approve，正文等于 `review.md`；四个采样身份与审计记录一致，审查时再读 `/proc` 没有仍匹配原 PID／starttime 的存活身份。清理结论只限这些采样，不包含未采样短命进程。

模型判词只覆盖所给二十六份完整冻结材料，其文本明确没有独立重跑作者审计，未收到全部 HTTP／SDK 历史、探针脚本和包原件。此前本报告的包、产品及生命周期独立原件复核承担该部分；不能把模型 approve 外推为完整十九公开文件、后来的审查记账或精确 Git／CI 已获模型批准。本轮完整十九件的结论来自本次独立 Spec／Standards。

### 最终两轴与验证边界

Spec 没有发现范围内可达缺陷：可选只读叶保持完整祖先资料和父权限上限；unsupported native／workspace 在建 protocol 前拒绝；原 schema、MCP readiness、生命周期、调用记录、批准及未知恢复各留在既有所有者。正向与具名失败、受控生命周期证据符合文档收窄后的范围，未借 native completed、结构结果文件或合成 loopback 宣称正式候选成功。

Standards 没有开放违反或具体 smell：局部注册、独立 SDK driver 与组件能力声明属于既有后端边界，上层没有新增厂商分支或第二状态账本；必要测试沿原 Interface，未增加永久探针框架或 CI。ST1 的 red、共享 prerelease 解析修正和实际 doctor 版本三者闭合。两轴独立复核均确认源码／测试与已核安装产品身份未变。

独立静态复核重现357个本地目标、六个已加载秘密值、JSON／私有路径 issue0，当前 `git diff --check` 退出0；边界仍不含远端链接、锚点和浏览器渲染。报告写完后的最后静态及精确十九件提交身份由作者冻结，不把初版摘要误称最终提交摘要。本次仅写本授权报告；没有运行 SDK、模型、测试、网络、安装、原审计脚本或提交命令。

当前本地出口没有未满足的 H1 实现／评审项。后续仍需普通提交／推送、精确远端身份及自己的必要 CI；H2 真实网关／同模板正式候选、H3 持久会话／续接、Windows 新 SDK、OS 隔离和完整六阶段均未关闭，也没有真实 SaaS 业务写或双后端成功结论。
