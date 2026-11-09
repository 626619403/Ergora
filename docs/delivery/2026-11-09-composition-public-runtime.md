# CR3c / E4：公开单叶组合运行入口

日期：2026-11-09。状态：公开入口实现、真实Temporal旅程及自身模板审查通过；最终包内134项及独立两轴审查通过，精确8948335普通推送、自己的双OS CI42548357813七必要步骤和02:10:14.158015 UTC独立远端核同SHA已完成。固定基线`6826047031aebddb7eb6c5fcf43cfe91ebb45ada`；CR3b自己的双OS CI42545445322及独立远端终结已通过。本文件不声明未验行为可用。

本片接通已支持形状的v2 start/status和常驻executor双请求根扫描，复用原Submission的创建核验、attempt-before-send、memo及原run恢复，复用原Temporal六阶段与受监控Executor。它不增加另一套调度或正式账本；Supervisor完整生命周期和备份出口分别仍属CR4/AC3c.4，多成员嵌套执行属AC4。

## 调查与拟定改动

- `CompositionInput.require_submission`目前无条件拒绝；`tasks.status`也拒绝。将单只读review叶、所有结构祖先task直接映射且无依赖的形状检查归到标准库`task_envelopes`，供版本输入和实际Executor共用。创建/历史读取仍能保存并核验未来尚不支持的静态组合；只有执行准入拒绝，不把可读性与可运行性混为一谈。
- `reference_task_runtime._status`目前把原文档当legacy传`workflow_id`/poll；改用`execution_input`的legacy投影计算ID与原transport调用，`VerifiedSpecClient`保留完整原文档核历史身份。公开`tasks.status`向它发送保存的完整admission，不能只发legacy投影。
- 版本输入注册映射拥有请求根；常驻executor从这个合同取得所有根，复用现有active/receipt/rejected处理与并发上限。旧冻结executor继续只读旧根。不能在常驻线程内构造_Creation。
- 历史摘要的runtime_supported只表示当前运行桥支持的静态形状，不能表示后端已认证、服务就绪、完整图端口已执行或任意成员调度已实现。需要公开说明当前限制及实际调用来源。

## 验收节点

- [x] P1：单形状规则只有一个所有者；可支持单叶通过，多成员/非只读/非直接输入在任何Submission dispatch/intent之前明确拒绝。创建、历史和无SDK诊断顺序保持。
- [x] P2：v2公开查询同完整历史身份，same-legacy/different-manifest拒绝；原not_found/unknown与只读行为保持，v1合同回归。
- [x] P3：常驻双根实际消费，不重复执行，原候选/批准/receipt绑定，原型别worker不误消费；未支持形状明确失败。
- [x] P4：非editable安装包上的真实本地Temporal/worker/常驻executor公开CLI旅程，原owner批准和原回执，至少一条v2和一条v1；模型协议合成与实际模型能力分别记账，不把fixture当真实模型。
- [x] P5：发行与283冻结身份、相关合同回归、fresh-context独立两轴审查、自身结构模板实际调用、普通推送及精确必要CI/远端。

每一验证结果按真实原件/源身份追加；先完成内部执行桥再开放入口，不能把先前手工调用六阶段fixture当本片Temporal验收。测试和源码范围按实际变更收敛，保持既有CI矩阵。


## 实施进度

单叶形状规则迁到`task_envelopes.review_member`，版本输入、实际executor和历史摘要共用；原本executor的重复形状遍历已删除。原manifest JSON解码复用一个标准库私有函数。`request_roots`从版本实现局部映射构造，不在scanner按版本写分支。公开status保留完整document给VerifiedSpecClient，只用legacy投影计算原workflow ID和poll。


首轮源码合同134项中132 passed/428.93秒，两失败是新fixture直接创建已由本模块其他场景建立的共享`.venv`；未触达生产执行。已沿既有fixture惯例保留已存在解释器，并补跑两个实际安装包start/丢响应恢复场景，结果待验。真实CLI探针第一轮在`task preview`漏写既有`--definition`参数，保存原日志后改用正确公开参数，新目录重建，未启动服务或改生产代码。不能把这两类测试装配失败写成框架执行成功。

## 当前验收原件

- 上述两个修正后的非editable包场景 **2 passed /14.11秒**；生产源码未因fixture修正改变。首轮日志未保存完整shell命令头，不能补造精确原命令；已核六文件范围为`test_composition_tasks.py`、`test_composition_runtime.py`、`test_composition_workers.py`、`test_composition_transport.py`、`test_task_submission.py`和`test_task_runtime.py`，重新collect为134项。最终包内运行的完整argv另存，待实际结果，不把132+2写成同一轮134通过。
- R1发行 **369源码/wheel/非editable安装文件一致，283冻结保持**；wheel SHA `306677fdd8df02fbac1b862e5dec4ac6d572bd52a3d88e5ce96af8ff18e03d3a`。原件位于忽略的验收缓存，公开只保留相对源码与内容身份。
- R2旅程探针手工建ledger目录0755，原doctor正确要求0700而拒绝。R3只修测试装配目录权限，没有改生产或绕过doctor。
- R3真实公开CLI旅程 **304.47秒通过**：[结果与源身份](evidence/2026-11-09-cr3c-public-journey.json)。实际启动本地Temporal、双版本worker、A2A及常驻executor；用公开`preview/create/start/status/plan/approve`，登记的test-operator经原owner批准链确认。治理v2、大型变更v2、治理v1均`REVIEW_READY`、各6原成功receipt；完整原输入、实际workflow类型/队列及SDK历史重放分别通过。先删除原manifest和活动定义库再执行；v2/v1分别走两请求根，不降级完整信封。finally停止的都是探针自己启动的进程。这里的Agent为确定性协议程序，证明真实调度/门禁/证据流程，不证明模型质量或真实业务owner人工批准。
- 自身结构模板真实调用 **119.66秒approve**，Codex `gpt-6.1-sol` / high / task-MCP，run `fea235c8430b4a97abefe04223f8cb3c`：[身份](evidence/2026-11-09-cr3c-self-review-identity.json)、[原结果](evidence/2026-11-09-cr3c-self-review-result.json)。独立者从原stdout/MCP核连续0→30000→60000→90000→116000→141000→157273至null，附件、结果及14源身份相符。此调用审提供的源码，没有执行测试或证明所有依赖；不替代fresh-context审查。Claude不可用按用户授权回退，未冒称模型错误独立。

当前验收缓存分为R1源码/包及模型、R2失败装配、R3真实CLI旅程和R4最终包内合同，身份分别保存。完整Supervisor生命周期、故障/取消/恢复归CR4；完整备份恢复出口归AC3c.4。普通提交、自己的CI及远端待实际终结。


## 最终包内合同与文档收口

R4使用R1同一非editable安装和未变化生产源码，明确执行`python -I -m pytest -q tests/test_composition_tasks.py tests/test_composition_runtime.py tests/test_composition_workers.py tests/test_composition_transport.py tests/test_task_submission.py tests/test_task_runtime.py`（完整argv另含本片持久basetemp），**134 passed /424.33秒，exit0**。最终重核源码/wheel/安装369文件一致，283冻结身份保持；没有重新打包未变化源码。首轮132/2失败和修正后2项仍保留，不改写为同一轮通过。

新独立者已核三条完整history、原输入/类型/队列、全部65份artifact摘要、owner/human批准和157273字节MCP完整六页；源码两轴无阻塞finding。指出的旧“全部v2拒绝”及README正式批准待接入措辞已在当前架构、总/AC计划和运行桥同步收窄，历史段落保留其原范围。静态检查首轮发现新增README锚点拼写错误，修正后10份Markdown/201本地链接及75条CLI parser通过；加入最终独立报告后再核完整scope。最终fresh-context报告、普通提交/推送、自己的双OS CI/远端分别记账，不借用CR3b结果。

[本片fresh-context独立报告](2026-11-09-composition-public-runtime-review.md)本地两轴与原件核验通过，范围内无剩余阻塞finding；最终静态11份Markdown/206链接及75条CLI parser通过。下一普通提交、自己的必要CI和即时远端终结。

本片精确提交`8948335ee2b2737bd8cc53e5c33f1fdd2f35ea94`（22文件，父6826047）已建立，普通推送与自己的必要CI/即时远端仍跟进。最终提交前11份Markdown/207本地链接及75条CLI parser、全部staged whitespace通过，scope清单已冻结。后续CR4本地推进不修改本片生产身份，不能在本片CI未结束时推后片取消它。

精确交付完成：`8948335ee2b2737bd8cc53e5c33f1fdd2f35ea94`自己的[双OS CI42548357813](https://github.com/626619403/Ergora/actions/runs/42548357813)七必要步骤全部success，独立02:10:12.011167 UTC核官方HTML后立即经fetch URL读取，02:10:14.158015 UTC核远端同SHA。固定Git对象22文件及369/283身份均由原审查者终结；后续CR4的取消路径修正属于新候选，不借用此CI。
