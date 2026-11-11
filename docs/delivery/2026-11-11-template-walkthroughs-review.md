# C6b/c 独立审查

2026-11-11，Codex fresh-context 独立评审；另以两个 fresh-context 子轴分别核 Spec 与 Standards，主轴直接检查限定原件。依据仓库 `AGENTS.md`、本片 W1–W6、原用户要求，以及 maintainable-project-delivery／independent-review、code-review、codebase-design 的适用规则。作者叙述、模型结论与静态回执均未作为预设结论。

**本地候选审查通过：Spec／Standards 开放 finding 为 0／0。** 独立发现的 C6BC-SP1（P2）与 C6BC-ST1（P3）均已最小修正并复核关闭。本结论不授予 W6 提交、自己的 CI 或精确远端交付；不关闭 C6d、AC6／F6 或后续项目阶段。

## 固定基线与完整范围

固定文档基线及审查时 HEAD 为 `f9574895525e3c19bfe7094636c407359baed007`，唯一父为 `3d6d1220bd600817e748c19f6a9c0fa1332f6ca9`；本片尚无新提交。使用 `git diff f9574895525e3c19bfe7094636c407359baed007` 与 `git ls-files --others --exclude-standard`，包含未跟踪文件；没有用空的 HEAD 三点差异替代工作区候选。

最终实质候选为九份 tracked 文档增量：`README.md`、`docs/PLAN.md`、`docs/TRAINING.md`、`docs/USAGE.md`、`docs/WORKFLOW_DEFINITIONS.md`、`docs/plans/2026-11-09-composition-console.md`、`docs/plans/2026-11-11-composition-capacity.md`、`docs/delivery/2026-11-11-composition-capacity.md`、`docs/delivery/2026-11-11-composition-capacity-review.md`；旧片仅审本次状态记账，不递归审其旧验收。

六份新文件完整读取或结构解码核验：`docs/TEMPLATE_WALKTHROUGHS.md`、本片计划／交付记录，以及 `docs/delivery/evidence/2026-11-11-template-walkthroughs.json`、`2026-11-11-template-backends.json`、`2026-11-11-template-self-review.json`。加本报告共十六份公开文件。基线与父提交之间、当前候选与基线之间的 `src`／`tests`／`scripts`／`.github`／`pyproject.toml` 无差异，既有冻结参考手册和 HTML 未改。

相邻接口按实际问题核对：安装器、安装 profiles、可选依赖声明、CLI 参数／页面模板应用、项目登记／组合配置、`services.py` 的执行器解释器、`reference_executor.py` 的准入、`task_mcp.py` 的 Linux／依赖要求、`workflow_definitions.py` 的快照／提示／继承及 `asset_trees.py` 的内容身份。使用与训练等既有手册用于核入口和交接规则，未把全部链接源码或整仓代码宣称为逐行审查。

## Spec

结论：本片 W1–W5 的声明范围符合要求，开放 finding 0。

**C6BC-SP1／P2，已关闭。** 原指南把 `task-mcp` 安装只放在训练段，开发用户按 control／development 安装后创建 v6 合同可成功，运行却会被 executor 的 MCP 依赖准入拒绝。三个安装 profile 均不包含此 extra，`services.py` 用启动 Ergora 的 `sys.executable` 创建 executor。修正在[指南共用运行准备](../TEMPLATE_WALKTHROUGHS.md#2-登记自己的项目)：开发组合与训练叶共同声明 Linux／WSL2、同一 Ergora／executor Python、默认安装器解释器的安装命令；训练段回链。复核与安装器、profiles 和实际准入一致，未改生产依赖或扩大安装范围。

三域完整包、逐 writer 的显式 Codex／current-container 选择、v2 定义／v6 信封及原 ID 读回均有原件。页面创建不承担运行、批准或项目质量证明。训练实际覆盖两个只读叶；两次成功 Codex 调用读取完整结构祖先资料，Claude 真实失败没有模型读取证据，同输入回退明确保留失败和理由。未将本片创建环境或新配置借用 C5c 六阶段结果，亦未声称 GPU、完整训练 DAG、成功双后端或独立模型错误率。

指南保留六阶段、精确 plan SHA 批准、candidate 证据、evidence SHA 采用和原 ID 恢复；持久 home、可信当前容器／用户与完整两份冻结参考手册的范围清楚。静态资料能力、合同创建、实际模型调用、可信实验及人工采用分别有明确入口。

## Standards

结论：本片维护性、所有权及记录准确性通过；硬规则与判断性 smell 开放 finding 0。

**C6BC-ST1／P3，已关闭。** 原自身 R1 被概称为“完整 tracked 文档 diff”，但冻结 `public-docs.diff` 实际包含七个所选 tracked 路径，未含无需递归的旧片审查记账。原件不需补模型或改写。修正在[交付记录](2026-11-11-template-walkthroughs.md)和[自身审查投影](evidence/2026-11-11-template-self-review.json)的 `scope_disposition`：列精确七路径、排除旧片审查记账与后续状态增量，明确保留原 task／result／scope 的过宽原文。已对照冻结 diff 逐项复核，模型原输入、附件和结果身份保持。

新指南承担跨手册入门旅程，详细规则回到原安装、项目、组合、训练和恢复所有者；没有第二套调度、账本、DSL 或批准流程，没有新增生产抽象、依赖、测试或 CI。未发现需要为纯文档修正重跑未变模型、439 包或回归测试的实证理由。耗时为自动化／调用墙钟，用量为后端自报；cached 与 reasoning 不重复相加，不推导加速、账单或模型质量。公开投影明确省略原件内容，未见具体机器路径、凭据值或个人认证身份。

## 直接原件核验

离线脚本由本评审者编写，仅在授权独立目录内写报告；未执行作者的带 CLI／socket 副作用审计脚本。

- CLI／完整包：核 `prepare.py`、`preparation.json`、`commands/01..21` 的 metadata／stdout／stderr、`manifests.json`，三份完整 manifest 的全树内容身份及二十四份去重 bundle 与已安装原 preset 一致；两条 `readback-commands` 对应原 task ID。原非 editable 包记录的 wheel SHA 与文档相同；未重建或重核全部439文件／两 RECORD。
- 页面／状态：成功驱动及被动 ASGI 驱动作语义核对，保留的 r1／r2 驱动作字节身份与失败结果核对；全部六十九组 HTTP metadata／request／response 字节相符，65 GET／4 POST，66个200及三个精确 submission GET400。两个 preview／create 与七份发布合同、创建意图／回执及锁绑定，默认 work-units-v2／v6、全部实例分配、后端和显式边界保持。178保护文件、控制库物理及 SQLite 逻辑内容相同；新增20文件恰为两组合同／意图／回执／锁，无 Agent run 或六阶段提交。
- 训练／后端：核 `training-leaves.py`、三次 result／run／task／admission／采样记录、准备及实际输入、原 stdin／protocol、完整 bundle／结构祖先 scope、native 原事件和原 result；设计完整回复逐字进入两次审查正文。两成功调用各四文件1,447／1,351B，实际 list 完整、UTF-8 read 从0连续至 null；Claude 无 list／read／native-ready。原输入与 prompt 摘要在失败与回退之间相同，回退原 decision 为 request-changes。两个最小 Claude 对照均为同一400，未推导适配器原因或成功修复。原审计失败与修正未覆盖原失败调用。
- 实际自身模板：独立重建两轮 manifest→prepared／actual input→stdin／protocol→scope 来源→native list／read→原 result／用量。R1 为171.01秒 request-changes，22嵌入文件／168,594B附件；R2 为130.97秒 approve，8嵌入文件／45,110B附件，仅复核原两个指南意见。每轮五 scope 全文连续 UTF-8 至 null，base64 同 offset 重试保留，无失败调用。R1 没有内联大 HTTP／合同／native 原流；R2 未覆盖后来的独立依赖修正，均未被宣称为最终整候选模型批准。
- 三份公开投影的七十一份显式来源定位、字节／SHA，及自身原解码结果／读取审计／冻结索引，均与限定原件相符。公开文件本地链接、Markdown 锚点、三份 JSON 解析与 `git diff --check` 通过。原服务退出、finally 回执与已采样进程清理记录相符；不推导未采样短命进程的全部生命周期。

完整有界逐件清单与原检查结果保留在 `.ergora/checks/ac6-walkthroughs/independent/`：`originals-audit.json`／`inspected-files.json`、`self-review-audit.json`／`self-review-inspected-files.json`、`final-audit.json`／`final-inspected-files.json`，及对应标准库脚本。首轮清单768项、自身审查清单123项为各次字节／结构检查记录，存在重叠，不能相加当作独立文件总数或全文语义审查数量。独立脚本首版误将 join 当带 ref 的实例，原错误及源已保留，仅修正离线枚举，未改原件。

## 限制与后续

没有网络、服务、浏览器、Agent／模型、安装、打包或产品测试重跑；没有读取个人 shell 认证配置。没有扫描全部 checks／venv，未重验未变439包／283冻结集合；本次对源身份和选定原包内容的核验不替代其原验收。没有新 GPU／原生 Windows／WSL2 端到端实测，没有重新执行六阶段。

C6a 的 CI 终态由原评审者同片记账负责，本评审仅检查其新增记录和范围，不访问其原件或冒称再次独立核过。下一步固定本片十六文件候选，普通提交／推送，核本片自己的必要 CI 与精确 Git／远端身份；W6 完成后再继续 C6d。上述出口未完成前，本报告仅是完整本地文档／验收片的独立通过。

## 精确提交与一次远端尝试

2026-11-11 同片收尾，独立检查已普通提交的 `c1f31fcfa38ac25085e287c507377be422786026`，唯一父为文档基线 `f9574895525e3c19bfe7094636c407359baed007`。全部十六个 Git blob 均为 mode100644，原字节／SHA256逐件等于 `ready-r1`；changed paths 精确等于冻结候选。`src`、`tests`、`scripts`、`.github` 与 `pyproject.toml` 的 Git 对象均与父提交相同，未用后续工作区状态替代精确提交。原对象身份见私有 `independent/commit-c1f31fc/git-objects-audit.json`。

获明确授权的一次官方无凭据 Git Ref API GET 于05:13:34.789827→05:13:44.799532 UTC尝试读取本分支，10.01秒后 curl exit28连接超时。请求禁用curlrc、凭据和代理，无自动重试、重定向跟随、SSH改写或TLS放宽；未收到HTTP响应头／正文，也未取得远端完整SHA，不能据元数据的缺省TLS字段推导握手或证书验证成功。完整1,825B curl元数据、92B stderr和0B头文件原件保留在私有 `independent/commit-c1f31fc/`，原正文没有产生。未追加网络请求。

本次只通过精确 Git 对象检查，远端身份和本候选自己的 CI 仍待；没有模型、产品、包或旧片验收重跑。本段状态记账不改变上述已经独立核定的十六个已提交对象。

## CI 终核与作者 Ref 样本离线核验

2026-11-11 同片后续，独立离线核 `snapshot-api-01..04` 的八份 runs／jobs 完整原正文及四份 `ci-sample.json`。来源字节／SHA256、官方请求／最终 URL、HTTP200、完整提交 `c1f31fcfa38ac25085e287c507377be422786026`、分支、push 事件、Portability 工作流、run143／attempt1、check suite 和两个 job 身份始终相符。各 job 开始时间不变，状态仅前进，已经完成的原步骤结论和时间逐项保持。

前三份05:12、05:16、05:26 UTC样本仍为 `in_progress`，第三份仅Windows已成功；这些原件没有改成通过。第四份05:31:29.377594 UTC记录确认本候选自己的 [CI42964143325](https://github.com/626619403/Ergora/actions/runs/42964143325) 整体及两OS均为 `completed/success`：

|Job|原ID|必要步骤|
|---|---|---|
|Ubuntu latest／Python3.11|130337322819|3／3 completed/success|
|Windows latest／Python3.12|130337323299|4／4 completed/success|

七个必要步骤为两OS的 Build and install wheel、Packaged reference identity、Native application regression，加Windows PowerShell5.1 installer and upgrade；与该精确提交的原工作流逐项相符。Linux的Windows专用步骤为原条件要求的 skipped，其余初始化／收尾步骤成功。第四份 runs 正文12,004B／SHA256 `d0e5a63e4440cb792f5edf208ae8dbcc575fedb3f39058d5ea917c0041c2fe25`，jobs正文5,208B／SHA256 `8f425cd5abf50b67bf62c188fcab31b970473456a4a6e0d10d4e94faa09d8e2b`。完整核验见私有 `independent/commit-c1f31fc/ci-four-samples-audit.json`。

作者另于05:33:09.698136→05:33:10.713747 UTC取得一次独立记录的官方 Git Ref API HTTP200样本；本评审仅离线读取其原正文／元数据／头字段文件和脚本，没有发新请求或运行作者脚本。脚本明确使用 `ssl.create_default_context()`，保留默认网络环境，无显式源站认证／Cookie头或TLS放宽。429B原正文SHA256为 `3f041341aaed4e6d424c96056183202357b302b78621fe76258c807cef2dfd6e`；原ref、commit类型、完整SHA和官方 canonical `/git/refs/` URL均与上述精确提交相符。1,329B头字段文件是响应字段的序列化，非线路抓包；807B元数据明确actor为author。原件身份和实际范围见私有 `independent/commit-c1f31fc/author-ref-offline-audit.json`。

原评审者那一次无代理请求仍为连接超时；作者另一次smart-Git TLS失败也不由新样本回写为成功。这里通过的是**作者官方Ref样本的独立离线核验**，不是本评审者直接网络取得SHA的成功。结合先前十六个精确Git对象与本候选自己的必要CI，**C6b/c按上述证据范围精确交付终结，Spec／Standards开放finding仍为0／0。** 本次仅作原片记账，没有网络、模型、产品或构建重跑，不授予C6d或整个AC6／F6完成。
