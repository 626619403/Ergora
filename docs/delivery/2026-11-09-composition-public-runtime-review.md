# CR3c / E4 公开单叶组合入口：独立两轴审查

日期：2026-11-09。审查者：Codex fresh-context 独立审查者，未继承实现对话；依据原始要求、固定基线 `6826047031aebddb7eb6c5fcf43cfe91ebb45ada` 和实际工作树独立检查。应用 [AGENTS.md](../../AGENTS.md)、maintainable-project-delivery 的 independent-review 及 codebase-design。此报告只覆盖 CR3c：公开单只读 reviewer 叶子的 start/status 和原常驻 Executor 的双请求根扫描。

## 当前结论

|审查轴|本地结论|
|---|---|
|要求符合性|通过；有限单叶入口、完整身份及原恢复/证据合同符合本片范围|
|可维护性|通过；所有权、实际复用、必要控制流、测试/CI 和性能检查无剩余阻塞 finding|

最终安装包六文件 **134 passed / 424.33 秒 / exit 0**，当前文档与证据已完成本地复核。此结论覆盖所审工作树的本地验收；普通提交、本候选自己的必要 CI 和即时远端身份仍需另行完成，不能继承 CR3b 的通过。

## 检查范围与身份

已独立读取固定基线至工作树的完整 tracked diff。生产改动恰为 `task_envelopes.py`、`reference_inputs.py`、`reference_executor.py`、`reference_task_runtime.py`、`tasks.py`；测试改动为 `test_composition_tasks.py` 与 `fixtures/task_runtime_client.py`、`fixtures/task_submission_client.py`。同时读取 `reference_task_submission.py`、`reference_task_creation.py`、`reference_creation_process.py`、`reference_workflows.py`、`reference_worker.py`、`reference.py`、静态图编译、原 FileAdapter/Transport/Executor、相关测试及现有 CI 的必要调用者。

文档范围为 `README.md`、`docs/PLAN.md`、`docs/USAGE.md`、`docs/WORKFLOW_DEFINITIONS.md`、`docs/architecture/current.md`、`docs/plans/2026-11-08-agent-composition.md` 及 `docs/delivery/` 下的本片记录、`2026-11-09-composition-runtime.md`、`2026-11-09-composition-review-execution.md` 和其 `-review.md`。前片这两份记录的追加是固定 6826047 的交付记账，不算本片新生产行为。开始检查时没有 untracked 文件；随后新增的三份 `2026-11-09-cr3c-*.json` 公开证据已读正文并与私有原件逐项核对。本地终核 scope 为 18 个 tracked 改动和三份新证据，另加本报告；本报告是审查者唯一写入文件。

独立重算完整 **369 个源码文件 = wheel 文件 = 非 editable 安装文件 = R1 身份清单**。wheel SHA256 为 `306677fdd8df02fbac1b862e5dec4ac6d572bd52a3d88e5ce96af8ff18e03d3a`。用 `git --no-replace-objects` 读取固定基线的全部 **283 个冻结 blob**，集合及 SHA256 均等于当前发行 manifest；冻结目录与基线无差异。[旅程源身份](evidence/2026-11-09-cr3c-public-journey.json)五文件及[自身模板源身份](evidence/2026-11-09-cr3c-self-review-identity.json)十四文件均与所审工作树相同。

## 要求符合性

- `task_envelopes.review_member` 是有限运行形状的单一所有者。`CompositionInput.require_submission`、实际 Executor 在原构造副作用前的准入、`summary.runtime_supported` 共用它。它检查单成员、纯只读 reviewer、叶子及全部结构祖先的直接根 task 输入和空依赖；历史可读性与运行支持分开。`_Submission.prepare` 在 workflow SDK 导入及 submission intent 写入前调用它，原 dispatch、attempt-before-send、memo 和未知派发后只查询原 run 的恢复没有另开路径。
- `tasks.status` 交付完整保存信封；`_status` 只用 `selected.spec` 计算原 workflow ID 并 poll，把 `selected.document` 交给 `VerifiedSpecClient` 核原始单 payload 的完整 JSON 身份。相同 legacy 投影不能代替不同 admission；原 not_found、传输错误与未知语义不合并。
- `reference_inputs` 的局部版本注册映射拥有 `request_roots`。常驻 Executor 仅扩大原扫描集合，继续使用同一 active 集合、线程池、并发预算、receipt、rejected 文件和原 claim/ledger；无第二套调度或账本。创建重验仍经独立 `task_creation` 子进程，不在 Executor 线程构造 `_Creation`。旧冻结 Executor 仍只扫描旧根。
- 原六阶段、可信验证、候选绑定、owner 批准和 monitor 保留。`runtime_supported` 的公开说明明确只代表静态形状，不代表认证、模型、SDK、服务就绪或完整图执行。多成员、运行态父输出、完整 Supervisor 生命周期及备份恢复出口继续属于后片。

## 结构、必要控制流、测试与性能

共用形状模块具有实际生产复用；删除它会使同一规则重新散落到提交、执行及摘要。私有 `_manifest_graph` 只集中同模块的 JSON 解码及嵌套上限错误，不引入新通用框架。`request_roots` 虽只有 scanner 一个直接调用者，其作用是已有版本接口的注册投影；把版本判断放回 scanner 会损害 Locality，无需再抽一层。

多成员、权限、依赖和根输入检查分别保护真实未支持的调用形状；visited 检查避免被修改的持久图形成无限祖先遍历。它不替代后端可用性、完整 manifest 重验或执行时的可信创建检查。历史、提交、执行各自的完整身份核验保护不同外部或持久输入，不能仅因看似重复删除。

新增公开 start/丢响应恢复和 status 测试跨过真实应用接口，验证了完整信封、正确入口/队列、memo、单次 start 和只读历史碰撞拒绝；与低层版本/Transport 测试保护的接线层次不同。复用既有 SDK fixture，没有为本片新建测试框架或重复 CI 矩阵。既有 Linux/Windows 条件保留，不把跳过的 Linux 原生场景声称为 Windows 执行通过。

审查者用 `python -B -S` 的只读标准库探针：受支持单叶通过，多成员、write、shell、network、依赖、节点输出、错误根输入和循环祖先均明确拒绝，进程未导入 Temporal；两请求根正确。对一份 9,819 字节实际静态图，1,000 次摘要共 0.052856 秒，仅说明该样本的额外图解码开销，没有据此声称普遍性能提升或完成压力测试。scanner 保留原两秒周期；未发现本片引入的实证性能退化，也无证据支持删减合同检查。

## 实际证据与限制

首轮源码日志确为 **132 passed / 2 failed / 428.93 秒**，两失败均停在新测试重复建立模块共享 `.venv`，未到生产提交执行；修正后单独两条非 editable 安装包 start/丢响应恢复日志为 **2 passed / 14.11 秒**。首轮未保存完整 shell 命令头，不能把恢复出的六文件范围写成原始精确 flags，也不能把两轮拼成同一轮 134 通过。

R4 最终使用同一非 editable 安装的解释器，以 `-I -m pytest -q` 运行 `test_composition_tasks.py`、`test_composition_runtime.py`、`test_composition_workers.py`、`test_composition_transport.py`、`test_task_submission.py`、`test_task_runtime.py`，完整 argv 含显式持久 basetemp。原日志 **134 passed / 424.33 秒**，保存 validation 的 exit code 为 **0**，日志 SHA256 为 `d6ce2899529e1d5996483185b8757f30f420896d02654e4b71a71d44194d8032`。独立重算最终 R4 清单与当前完整 369 源文件、R1 wheel/安装一致，283 冻结不变；修正后的三个测试文件也仍匹配自身模板审查的原身份。没有重新打包或沿用不同生产候选的测试。

[真实公开旅程](evidence/2026-11-09-cr3c-public-journey.json) **304.469 秒**，治理 v2、大型变更 v2、治理 v1 均 `REVIEW_READY`。审查者直接解析三份保存 history：每份 161 个事件，原输入与保存文档一致；v2 类型/队列为 `ErgoraCompositionWorkflowV2` / `development-tasks.composition-v2`，v1 为原类型/队列；各六个原 submit context 和六份 `SUCCEEDED` receipt 对应，全部 **65 个 artifact** 摘要吻合，审批为原 `owner` / `human` 合同并绑定原 plan receipt，verify/review/outcome 指向同一 candidate。程序以实际 SDK 重放三份 history 通过，审查者核程序及原件，没有另跑 Temporal。

该旅程在非 editable 安装下实际启动 Temporal、双版本 worker、A2A 和常驻 scanner，经公开 CLI 与原 prerequisite/owner 批准机制运行；先移除源 manifest 和活动定义库。Agent 使用确定性 native/command 协议，批准是探针 test-operator 经原 owner 合同完成，不等于真实模型质量或业务 owner 人工验收。R1 漏 `--definition` 和 R2 目录 0755 导致原 doctor 拒绝的日志仍保留；R3 仅修测试装配，没有修改生产门禁。

[自身结构模板原结果](evidence/2026-11-09-cr3c-self-review-result.json)为 Codex `gpt-6.1-sol` / high / task-MCP，**119.662 秒 / approve**。独立核 stdout 的六个成功 read 页，offset 为 0、30000、60000、90000、116000、141000，至 `next_offset: null`；逐页重组恰为 **157273 字节**，SHA256 `17ba8be96029c731c43435b51ca4801f9e9cfad03aeeb2bdd29b8b36c5237596`，与声明附件及保存结果摘要一致。模型报告如实限制在提供源码，未宣称测试/旅程通过。本片使用已授权的 Codex/ChatGPT 回退，不把同后端 fresh-context 或该实调称为模型错误独立。

文档观察已关闭：`docs/architecture/current.md`、总/AC 计划及运行桥的当前导航原先仍表示全部 v2 拒绝，`README.md:161` 还把正式批准统称为待接入；这会让用户误判已验入口，也妨碍按当前检查点恢复。最小修正已收窄到有限单叶入口及原 owner 批准，历史描述保留其原范围；审查者复核当前正文及 diff 后关闭。新增 README 锚点错误的首轮静态结果及修正后的通过分别保留。最终静态原件为 **11 份 Markdown / 206 个本地链接及锚点 / 75 条 CLI parser 通过**，普通 diff whitespace 检查通过；本报告自己的五个链接亦已核有效。

审查者没有改源码、依赖、测试或提交，没有运行 pytest、安装、真实模型或服务。本地要求/结构两轴和已记录验收无剩余阻塞 finding；精确提交、自己的必要 CI 与即时远端终核待实际结果另记。完整 Supervisor 生命周期、故障/取消/恢复及备份出口仍属 CR4/AC3c.4，未完成范围不由此结论代替。


## 提交后终核追加（2026-11-09 02:14 UTC）

本追加将上文的本地两轴结论推进到本候选自身的提交、必要 CI 和即时远端身份终核；上文首轮失败、后续修正及执行限制仍按原记录保留。

用 `git --no-replace-objects` 独立确认候选 `8948335ee2b2737bd8cc53e5c33f1fdd2f35ea94` 的唯一父提交是固定基线 `6826047031aebddb7eb6c5fcf43cfe91ebb45ada`。两者间恰为 **22 个文件**，每个原始 Git blob 的 SHA256 均与 R4 `review-scope.json` 相同。候选完整 `src/ergora` 树的 **369 个文件**与 R4、原 wheel 及非 editable 安装身份一致，**283 个冻结文件**逐个等于固定基线；wheel SHA256 仍为 `306677fdd8df02fbac1b862e5dec4ac6d572bd52a3d88e5ce96af8ff18e03d3a`。候选 diff whitespace 检查通过。

固定候选文档与 R4 `static-documents.json` 的逐文件摘要相同，最终静态范围为 **11 份 Markdown / 207 个本地链接及锚点 / 75 条 CLI parser**，全部通过；此处 **207** 更新上文较早的 **206**。本地安装包 **134 passed / 424.33 秒 / exit 0** 仍属于此前已核的同一生产候选，无需以当前后片工作树重跑或代替其身份。

在 **2026-11-09 02:14:12.695604 UTC** 独立重读 GitHub 官方 [portability run 42548357813](https://github.com/626619403/Ergora/actions/runs/42548357813)，整体为 **Success**，绑定完整候选 SHA 和 `portability.yml`。两个 job 均结束；以下七个适用必要步骤的 `data-conclusion` 均为 `success`，日志 URL 均包含本候选完整 SHA 及各自 job ID。

|Job|必要步骤|完成时间（2026-11-09 UTC）|
|---|---|---|
|[Ubuntu / Python 3.11](https://github.com/626619403/Ergora/actions/runs/42548357813/job/128938177503)|Build and install wheel|01:58:54|
|Ubuntu / Python 3.11|Packaged reference identity|01:58:55|
|Ubuntu / Python 3.11|Native application regression|02:08:16|
|[Windows / Python 3.12](https://github.com/626619403/Ergora/actions/runs/42548357813/job/128938177477)|Build and install wheel|01:59:41|
|Windows / Python 3.12|Packaged reference identity|01:59:43|
|Windows / Python 3.12|Native application regression|02:05:55|
|Windows / Python 3.12|Windows PowerShell 5.1 installer and upgrade|02:06:51|

该次读取的 HTML SHA256：run `ff4bbf5e24c36a6f36e767f1e42aba5bb6d494715cc0e04b75d04c2362f5a014`；Ubuntu job `5d7a94509ed3fdfd191bb5d7775053b0eb4d2992c1e928e0372a9baaadafc3c9`；Windows job `cdd3873149683ee2b79020f06be02dd31915710f880beb8794431c49ad744780`。未通过已遇限流的匿名 API 轮询，也未修改或执行会写缓存的 CI 辅助脚本。

同一进程确认上述全部成功后，立即执行明确的 HTTPS 远端读取：

```text
git ls-remote https://github.com/626619403/Ergora.git refs/heads/refactor/architecture-foundations
```

开始 **02:14:12.695811 UTC**，结束 **02:14:14.105685 UTC**，exit **0**，stderr 为空；stdout 为：

```text
8948335ee2b2737bd8cc53e5c33f1fdd2f35ea94	refs/heads/refactor/architecture-foundations
```

方法更正保留如下：此前 **02:10:12.011388–02:10:14.158015 UTC** 的 `git ls-remote origin` 同样返回准确候选，但 `origin` fetch URL 为 HTTPS，不能因设置了 `GIT_SSH_COMMAND` 而称其为 SSH。随后 **02:12:35.845957–02:12:36.149384 UTC** 对 `git@github.com:626619403/Ergora.git` 的显式 SSH 读取 exit **128**，错误为 `nc: Proxy error: "HTTP/1.1 407 Proxy Authentication Required"`；一次无代理双路检查亦分别在 `github.com:22`、`ssh.github.com:443` 连接超时。未修改 SSH 配置。本片终核要求准确远端 SHA，不限定读取传输；按主代理确认，以以上重新读取 CI 后立即取得的有效 HTTPS 身份完成门槛，不将 SSH 失败写成通过。

**本候选要求符合性、可维护性与交付终核均通过，无剩余阻塞 finding。** 此结论精确限定于 `8948335ee2b2737bd8cc53e5c33f1fdd2f35ea94`；后来 CR4 的文档、源码、测试及新记录工作树改动均不纳入本片审查、安装包身份或验收声明。审查者本轮只追加此报告，没有改实现、测试、依赖、配置或缓存，没有提交或推送。
