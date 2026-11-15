# BR 主线联合整合：独立审查

日期：2026-11-16。Reviewer：fresh-context Agent `/root/mainline_template_joint_review`，未继承实施会话。固定基线／当前 HEAD 为 `d5b58912e4f20c96a52f7c0138b8c7c3d1a97b50`。先核原始要求、实际变更和消费者，再读实施结论；原独立报告与自身模板的 verdict 不作为本次 verdict。

|审查轴|结论|开放 finding|
|---|---|---|
|需求符合性|approve，限本轮定义／文档／fixture 及下列联合安装原件|0|
|维护性／职责／测试接缝|approve，限同一范围|0|

所审范围未发现需要修正的可达缺陷，没有源码或维护性阻断项。原 HTML 在 390px 下的 70px 溢出仍是未通过的历史布局观察，本结论不改变它，也不认证厂商服务、异后端、后继 cycle 服务或发布。

## 范围与独立性

已读根、src、tests 的 AGENTS、[组件协议](../architecture/component-change-protocols.md)、当前 PLAN、本轮[计划](../plans/2026-11-16-review-reporting-mainline-integration.md)与[交付](2026-11-16-review-reporting-mainline-integration.md)。采用 maintainable-project-delivery 的 independent-review brief，以及 ergora-codebase-quality 的 repository-style、module-design、test-seams。未再委派 Agent；授权仅为只读调查及本报告。

原始要求包括：后端可选、优先异后端并保留 Claude 不可用时 Codex 回退边界；把官方审查资料落实到对应 PR Skill，分清厂商能力与实际 Ergora 调用；增加只读报告作者／模板，参考指定 HTML 文章生成 Markdown 和静态自包含 HTML；保持旧资源不可变、完整祖先继承、权限收窄、六阶段及原证据／批准身份，不增加重复调度、账本或测试体系。联合范围另含已审 7025 fixture 修正对本线原子 marker 的适配。

精确范围为 ignored `review-reporting-mainline/joint-review-r1/files.json` 中 **33 文件**。逐项核当前文件、冻结 `files/` 正文的字节数、SHA256 和执行位，全部匹配；`complete.patch` 为 **168,673B**，SHA256 `cba1cff9566e6a5789a93cef790c83a00b5d3d5e6c073f9f845ee697dd767b96`，与 scope 相符。所有私有原件以下均相对本项目 ignored `.ergora/checks/review-reporting-mainline/`。本报告另列，不改变冻结 scope。

实际新产品是 catalog 修改和 11 份新版本资源，没有 Python 产品、schema、依赖或 CI 修改。读审了新资源全文、catalog／测试／fixture 的实际 diff、用户手册及研究／本轮记录，沿 `workflow_definitions` 的安装、资源合并、权限准入、manifest／输入，以及两个 backend 的实际命令核职责。历史两源／隔离组合报告保留其身份及原时间范围；没有重做其 1,024 原件全审，亦未递归验收排除的 c1b1／后继设计／WA 状态记账。

## 需求符合性

[后端 Skill](../../src/ergora/data/presets/workflows/ergora-pretraining-review-v1.0.1/skills/ergora-review-backends/SKILL.md)准确区分普通结构化调用、原生命令、公开插件／自建 CI 与厂商托管审查。与现有 `CodexBackend.command` 的 `codex exec`、`ClaudeCodeBackend.command` 的 print／JSON 路径一致，没有新增 native review 或托管 API 调用。Claude task-MCP 的 bare 环境凭据要求与原实现相符。Skill 明确实际 backend／mode／会话／输入身份及覆盖，回退不得冒充异后端成功；本地 advisory approve 也没有变成平台批准。

两领域新根还原 version 并移除新增 Skill 后，与各自旧 definition 完全相等。独立核基线 **216 个旧 preset 文件**的原字节及执行位保持；catalog 共 33 项，原领域条目只切换新根、追加依赖，30 个无关条目保持。直接对读本轮保存的两个新 composition 及八份 prompt：叶引用、backend request、permissions 与旧图相同，各叶完整提示含来自 root 的共享 Skill。八对 old／again 输入全树字节相同；原 invariant 脚本及 exit0 原件另覆盖每领域 24 个旧 object、旧 index 映射、manifest 与输入保持。没有把可追加 index 的整体字节当作冻结合同。

[报告作者](../../src/ergora/data/presets/agents/ergora-evidence-report-author/skills/ergora-evidence-report/SKILL.md)和[操作页](../EVIDENCE_REPORTS.md)将来源观察、记录事实、推论、失败、反对及未验范围分开。root／author 为单叶、read=[definitions]、write=[]、shell=false、network=[]；原祖先资源与权限 owner 继续生效。Markdown／HTML／sources／limitations 是原 response 字符串内的作者约定，未增加可信 schema、sanitizer 或事实认证权。HTML 转义、自包含、无脚本、量化来源及原件留存要求齐全；显式导出沿原结果，不覆写首次模型输出。

来源研究将官方产品说明、历史文章与 Ergora 的实施选择分开；HTML 文章归属个人经验，gallery 数字明确虚构。此次核研究／资源的来源归属及原真实消费者，没有重新联网确认 11 月 15 日后的厂商文档，也未重新审计两源全部网页原件。历史审查已做的原网页／gallery／报告输出检查仍只具有其原身份。

## 维护性与 fixture 接缝

定义由原 `DefinitionLibrary` 安装、编译和冻结；调用仍由原 AgentBackend／agent runs 拥有，没有第二调度器、实验账本、报告服务或具体后端分派。两根中同字节 Skill 是可独立导出完整包的资源副本，长比较集中在研究文档；单叶报告有明确 catalog、手册及 CLI 消费者，未引入空转封装。

[既有 preset 测试](../../tests/test_presets.py)将冻结／移走源库恢复接缝参数化为两个 profile，叶路径、role 和祖先集合跟随参数。它保护真实安装幂等、旧身份、权限及完整材料恢复，没有新增措辞断言、测试文件或 CI 矩阵。

[fixture](../../tests/fixtures/training_cycle_operations.py)保留真实阻塞 fault 和真实 `notify_identity`，只在 beta 通知前等待 writer 与 alpha reader 的实际 marker，耗用原 `cycle_operation_remaining`，没有重开 clock。`mark` 用各 PID pending 文件原子发布完整 JSON，避免通知标记部分可见。沿原 `test_cycle_stop_notifies_peer_while_writer_and_other_target_reads_block` 核对，原测试仍检查真实目标身份、两个阻塞进程当时存活、三个分支结果和最终清理；没有以 fixture 伪造成功结果或放松断言。原 candidate fault、产品 reaper 和 CI 保持。独立读取本轮三份完整 marker，含 writer／reader 身份及 beta sender／target；安装精准用例也确实包含该并发接缝。

## 联合原件核验与限制

直接核本轮构建／安装命令与日志，再独立逐文件比较 wheel 和两个非 editable site-packages：**663 个产品文件**的集合、字节及执行位与源码一致。源目录 `AGENTS.md` 按原打包规则排除。wheel SHA256 为 `4c938c8fbddfa9f2e7c27a25b4b811e435807d24d128dd90d05717ebe507f079`；core 无 Temporal SDK dist，SDK 为 **1.34.0**。两个 reference 原件均 PASS／283，依赖检查原 stdout／stderr 均兼容通过。178 tests／examples、228 preset data 的当前及冻结副本逐项匹配输入清单，没有重用隔离缺 fixture 的旧结果。

直接读取精确命令、stdout／stderr 和 JUnit：

- `installed-regression-r1` 是 **50 passed／208.52 秒**，外层 209.734 秒；JUnit 50 cases、failure/error/skip 均 0，stderr 空。
- `ci-fixture/installed` 是另一命令的 **8 passed／106.07 秒**，外层 107.303 秒；JUnit 8 cases、failure/error/skip 均 0，stderr 空。取消接缝展开 spawn／helper／loop 三 case，不能记作单次 58 项 suite。
- 三个 preset CLI install／报告 show、报告 manifest／input／verify 的原命令与结果保持；报告 Agent／根 digest 为 `f82e5acec681e9f23506fad1289c179bca83d2253450d8ee7de85c92fbc37008`／`67541349b69458a58be8ee9e5fc7fccbe405aba4e0f106bac29342972022c441`。9,279B 报告 prompt 检查不含新模型调用。

自身原 `ergora-structure-review@1.0.0` run `c058db5070d04399b1785834078ea691` 为真实 Codex／text-only、succeeded／29.200 秒／approve。独立核 **37 文件、653,196B** 全部匹配其 scope 副本且全文进入 task，task 和三份祖先资源完整进入 **809,109B** prompt；prompt 与实际 stdin 逐字相同，SHA256 `30293705f7de5785fbe8396a82535435cea6f46cb98f74f72c0deb9ed48d84e4`。保存结果与 original-result 字节相同，SHA256 `5031b93a28c27a15a4e0b756d099b34934a3f0e7fea6599b8de0c555b5eb7f26`。该供稿把回归写为在途，模型结论仅属当时供稿；终态测试由上述原件独立核验。实际 binding 是 Codex，未认证 Claude 或后端多样性。

`cleanup-r2` 原观察为本轮 418 JSON（含无扩展 marker）、15 个完整进程身份、active match 0／unknown 0／oversize skipped 0；不代表全 OS spawn 清单，也不是非父进程的 wait 证明。较窄 r1 原件保留。`git diff --check` 通过。

本次只执行读取、hash／字节／执行位比较、原图／提示／结果／JUnit 核对及 Git 静态检查，没有重跑 50／8 suite、模型、浏览器、安装或训练，没有修改产品、测试、其他文档或其他树，没有提交／推送或外部写入。公开远端、自己的准确 CI、厂商原生／托管服务、真实 GPU／训练／质量／性能、通用报告准确率、sanitizer 和后继服务均未由本片验收。原 run43713822317 的失败、7025 自己 CI 尚未观察到及 API403／配额0 的既有记录不能改记成功。主控可记录本联合片独立两轴 approve；固定候选、发布与准确 CI 仍按原门禁继续。

## 固定提交身份收尾

2026-11-16，同一 reviewer 仅核固定提交 `6725e62511aa4a5b68baf684ec3cbc1f0470d3e6`，其唯一父提交为上述 d5b 基线。40 文件提交中的全部 **14 个 src／tests blob**及执行位与 `joint-review-r1` 固定 scope 一致；**28 个导入文件**与 `imported-files` 原正文、SHA 和执行位一致。提交内本报告原文亦逐字同一，为 **9,773B／SHA256 `46911b17f6696e0b9bc8da3e4f5223da49f1199a6b7cd669db180e483c0e5712`**；本段为固定候选后的追加身份记录。

没有额外 Python 产品、测试或 CI 改动。另有的 c1b1 原报告收尾、已独立通过的 c1b2a 设计／审计、WA pending 及 CI／本地闭合记录不扩大本片产品范围；scope 中随后更新的本轮计划／交付／PLAN 仅记录独立门禁闭合。原两轴 approve／开放 0／0 保持。本次未重跑 suite、模型、浏览器或旧原件全审，未按隔离服务树源码评价该提交。普通推送、该精确候选自身 CI 与发布仍由主控继续，不自动合入 main；既有 CI 观察不替代新候选结果。
