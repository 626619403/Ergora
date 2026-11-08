# AC3d：工作流定义与静态继承编译独立审查

日期：2026-11-09。r1结论：**Standards通过，保留1项非阻断P3维护建议；Spec request changes，2项P2待修正。** 本报告不登记完整AC3d交付完成。

## 身份、范围与依据

审查协调者使用新的独立上下文，Standards与Spec另由两个`fork_turns: none`上下文并行检查，均未接收实现会话或预设结论。按AIHERO索引中的`code-review`、`codebase-design`，以及`maintainable-project-delivery`独立审查brief执行。只读源码、必要调用者、已有证据；仅写本报告，未安装、修改源码、提交或外部写入。

基线与开始审查时HEAD均为`9bb84c6437bd4b38f928defcaad0ec678fa24a5e`；基线至HEAD提交列表为空，审查当前未提交变更。使用`git diff 9bb84c6437bd4b38f928defcaad0ec678fa24a5e -- <固定范围>`与新增文件正文。固定范围为`.ergora/checks/ac3d-workflows/review-r1-scope.json`中的34文件（13 tracked变更、21新增）；该scope文件SHA256为`676102be8a95019fc2a8326817d2ac8e62712d33e25d710f8bc1d2b57412de31`，tracked diff文件SHA256为`65b71960ca140125fa8809908e2ac9cc9947cef23eb2c9b616a8f280c2dd3fde`。

开始及发行身份核对时34项均匹配。2026-11-08 17:04:56 UTC结束复核时32项仍匹配；`docs/PLAN.md`及本片交付记录仅追加WD5包、CLI、性能与自审在途状态，WD1固定合同未变。两项新的文档SHA256分别为`6fc3b7d0adfff632e91bd77c7226f8d6119bc6e6f301cb3b597ef696e716d5de`、`5fde67e7b71cbb018b7a4c66f54a7a086af7086cee688c60cfa7767b837d9a60`。

原始要求按[本片WD1](2026-11-09-workflow-definitions.md#wd1固定合同)、[工作流手册](../WORKFLOW_DEFINITIONS.md)、[AC计划](../plans/2026-11-08-agent-composition.md)与[ADR0005](../architecture/decisions/0005-composable-workflows.md)核对：精确有界复用、串并行/all-join、完整结构祖先材料、只增资源/冲突拒绝、整链授权、独立稳定路径、根全局预算，以及旧Agent/Skill/工作流入口和完整备份兼容。当前仅静态包库与预览；模型装载、正式准入、冻结manifest和Temporal执行仍归AC3b/c/4，未当成本片缺漏。

## Standards

**通过：0项硬违规，1项非阻断判断建议。**

未发现违反已读仓库标准的实证问题。`definition_bundles`有Agent、Workflow两个实际生产消费者；图、继承和权限语义仍归Workflow所有者。Agent转发入口有明确兼容要求，不计为Middle Man。检查分支保护外部输入、持久身份或真实预算条件，未发现应删除的防御控制流。

**ST-1，P3，可能的Duplicated Code，非阻断：** [workflow-definition-v1.json](../../src/ergora/data/schemas/workflow-definition-v1.json)第151行的`$defs/version`重复第26行根`version`的完整规则，包括`"maxLength": 64`和同一三段数字正则。根对象校验及索引发布消费前者，引用的`version`消费后者；未来调整可能导致根版本与引用版本接受集合漂移。最小修正：引用版本直接使用`"$ref": "#/properties/version"`，删除重复`$defs/version`。这是维护建议，当前规则一致，无已知行为错误。

Standards子审查只读源码、合同、示例与已记录测试日志，未复跑或写文件。共享库重构保留公开入口、磁盘布局、包身份和首次/增量原子发布的实际合同，未发现新增单消费者框架或无实际用途的扩展参数。未发现需要新增一套永久检查框架或镜像测试的依据。

## Spec

**Request changes：2项P2。** 未发现额外范围扩张。

**SP-1，P2，定义库权限路径未执行固定语法：** [workflow_definitions.py](../../src/ergora/workflow_definitions.py)第21行。WD1第37行要求“逻辑挂载只含…`definitions/{agent,workflow}/ID/VERSION[/path]`；`definitions`可授整个只读资产库”。实现只检查前两段。Spec审查者与协调者分别在临时State中端到端复现：根、叶子及grant使用`definitions/agent`或`definitions/agent/architecture-reviewer`，均成功导入并预览。由此接受合同未定义的跨ID/跨版本授权范围。最小修正：除裸`definitions`外，要求完整kind/ID/精确VERSION，并验证其格式；分别覆盖定义请求和显式grant。

**SP-2，P2，network接受明确禁止的origin：** 同文件第27行。[手册](../WORKFLOW_DEFINITIONS.md#权限路径和预算)第71行要求“精确规范HTTP(S) origin…不接受…通配符”。`urlsplit`加当前比较未验证hostname。两位审查者分别复现：将根、叶子及grant的network设为`https://*.example.com`或`https://api example.com`，实际导入及预览均成功。静态编译因此把禁止或无效的网络请求标为有效。最小修正：明确拒绝通配符、空白及无效authority，保留精确origin比较；补充合法origin的兼容验证。

检查覆盖祖先正文、实际Skill加载名、去重后的逐来源授权、全局/子树预算、串行/汇合端口、递归备份和旧入口；上述之外无substantiated finding。Spec审查者独立执行旧`workflow --help`成功，`reference.verify()`当前PASS/283。未启动模型或改生产状态。

## 独立核验与证据限度

- 协调者使用既有Python3.11.15环境，显式`PYTHONPATH=src`、禁写bytecode及pytest cache，在临时目录独立重跑`test_workflow_definitions.py`、`test_agent_definitions.py`、`test_state_backups.py`、`test_architecture_boundaries.py`：**115 passed、2 skipped，5.69秒**；跳过项是原生Windows junction用例。通过结果未覆盖上述4种非法权限输入，不能覆盖Spec发现。
- `git diff --check`通过；283冻结文件逐一核对当前内容、manifest与基线Git对象SHA一致。重新执行经阅读的静态文档检查脚本并禁止其落盘：17文档、308链接、57 CLI parser均通过；写入本报告后再次核对18文档、316链接、57 parser通过。
- 独立逐字比较359份源码、wheel及实际site-packages文件，并核作者身份记录一致。r1 wheel SHA256为`1a4064c15efecde47567042e7fcf7e6f7f18f1898686064e25987dac3f59c3c0`。作者9套源码与非editable包各177 passed/8 skipped的原始日志已核读；协调者未独立复跑这9套，未将其计为独立115项。
- 核对作者26次CLI的原始argv、退出码与stdout，独立读取恢复库重编译，恢复前/后及实际库预览完全相同：`fcf1279f5d3bacd0056c5662b75d4d6a2eb9f36731daddb29628d08731dbd455`，10实例、13,213静态prompt字节。独立调用`backups.verify`通过，4 Agent/5 Workflow、两库索引与备份manifest身份吻合；恢复库0个Agent运行。
- 性能只核读`r1-preview-performance.json`的原始5样本及声明条件：Python3.12.3安装包、同进程顺序、warm OS缓存，4/22/102实例中位13.7/19.9/53.8毫秒。没有独立重测，不外推调度、模型吞吐或最大容量。每次编译按精确引用/材料标记缓存读取，完整树检查与逐叶完整prompt计费有明确职责；当前无可证实性能finding。

作者原始证据在本地忽略目录`.ergora/checks/ac3d-workflows/`：`r1-source-tests.log`、`r1-expanded-source-tests.log`、`r1-wheel-tests.log`、`package-identities.json`、`r1-cli-journey.json`及其逐命令输出、`r1-preview-performance.json`、`static-documents.json`。原初跑失败、构建环境缺wheel及更正记录保留在[交付记录](2026-11-09-workflow-definitions.md)，未当作产品通过。

当前阻断项是SP-1/SP-2；修正后需验证非法路径/origin拒绝、合法输入兼容并同片复审。ST-1保留为非阻断维护建议。Ergora自身真实reviewer仍待原始回执，最终修订包、必要双OS CI及精确候选/远端终结均未由本报告登记通过；后续运行权限强制和实际模型装载不在本次静态审查通过范围。

## 固定34文件清单

```text
README.md
docs/AGENT_DEFINITIONS.md
docs/PLAN.md
docs/USAGE.md
docs/architecture/contracts-and-identities.md
docs/architecture/current.md
docs/delivery/2026-11-09-workflow-definitions.md
docs/plans/2026-11-08-agent-composition.md
src/ergora/agent_definitions.py
src/ergora/backups.py
src/ergora/cli.py
src/ergora/contracts.py
tests/test_agent_definitions.py
docs/WORKFLOW_DEFINITIONS.md
examples/composition/README.md
examples/composition/agents/correctness-reviewer/agent.json
examples/composition/agents/correctness-reviewer/instructions.md
examples/composition/agents/test-value-reviewer/agent.json
examples/composition/agents/test-value-reviewer/instructions.md
examples/composition/correctness-review/instructions.md
examples/composition/correctness-review/workflow.json
examples/composition/kernel-delivery/instructions.md
examples/composition/kernel-delivery/workflow.json
examples/composition/parallel-review/instructions.md
examples/composition/parallel-review/workflow.json
examples/composition/preview-grant.json
examples/composition/structure-review/instructions.md
examples/composition/structure-review/workflow.json
examples/composition/test-value-review/instructions.md
examples/composition/test-value-review/workflow.json
src/ergora/data/schemas/workflow-definition-v1.json
src/ergora/definition_bundles.py
src/ergora/workflow_definitions.py
tests/test_workflow_definitions.py
```

两轴计数：Standards 1项非阻断P3（最高ST-1）；Spec 2项P2（SP-1/SP-2），均待修正。

## r2同片修正复核（2026-11-09）

当前结论：**Standards与Spec均通过；ST-1、SP-1、SP-2全部关闭，未发现新增substantiated finding。** 上述r1发现与当时结论原文保留。此结论限于静态实现和本节实际证据，不登记完整AC3d交付完成。

沿用本片原协调者及两个独立审查轴，未用作者自检代替复核。基线/HEAD仍为`9bb84c6437bd4b38f928defcaad0ec678fa24a5e`、无新增提交。2026-11-08 17:12:43 UTC独立核对r2固定38文件全部匹配：scope `.ergora/checks/ac3d-workflows/review-r2-scope.json` SHA256 `f823884990ca047e73dc45f101bde4096de18347e08ca9873b3c6e730ab594b0`；对应tracked diff SHA256 `6e58b984a525b9018bc68ac7e011eea5f25ec5ba8b22110cec69451aa9b22085`。38项为原34项加ADR0005、本审查报告及r1自身reviewer的两份公开JSON。之后本报告追加属于同片审查记账。

修正实现身份：`workflow_definitions.py` SHA256 `ded6ff0856602c42186fa618123e585cd752503bfacddbecb05d483be0060601`；工作流schema SHA256 `b349b292af84a6c19f5066691c7b7cec7feebd032fe4a8db36019115741c7a61`；对应测试SHA256 `1e9531a53d347259b66bfbf4c699ffa082d2114174ab25455f6c1ac5163a617b`。共享库、Agent兼容入口及示例正文未因修正改变。

### Standards r2

**通过；ST-1关闭，无新增findings。**

ST-1原P3判断建议已修正：[schema](../../src/ergora/data/schemas/workflow-definition-v1.json)的节点引用版本现在使用`"$ref": "#/properties/version"`，重复`$defs/version`已删除。根定义、节点引用、`DefinitionLibrary`索引及新增权限版本校验均消费同一版本规则，原先的漂移风险已消除；不需要新增抽象或永久镜像测试。

新增定义路径及origin校验仍归Workflow所有者。新增分支处理真实外部输入；DNS/IP使用标准库解析配合局部语法检查，未引入通用框架。九项新增合同覆盖公开导入/预览入口的拒绝与合法输入兼容。ADR明确区分静态实现和后续运行能力；新增自身审查结果及身份记录明确属于历史r1，没有将其approve冒充r2最终批准。

Standards轴此次未独立复跑或写文件；协调者及Spec轴的实际复跑另列。

### Spec r2

**通过；SP-1/SP-2关闭，本次修正及相邻静态调用范围内无新增substantiated finding。**

SP-1：[workflow_definitions.py](../../src/ergora/workflow_definitions.py)第27行现要求完整kind、合法ID、精确版本。原`definitions/agent`、`definitions/agent/architecture-reviewer`及新增非法ID、`latest`，在定义、Agent节点权限、显式grant三处均拒绝。合法Agent与Workflow精确包范围仍成功导入、预览，祖先正文保留。

SP-2：同文件第32行现验证DNS/IP及规范authority。原通配符、空格主机，以及空端口、显式默认端口，在上述三处均拒绝。合法DNS、punycode、localhost、IPv4、压缩IPv6和非默认端口均成功导入、预览；[手册](../WORKFLOW_DEFINITIONS.md#权限路径和预算)已明确这些有限格式要求。

原Spec审查者独立执行共**24次非法输入拒绝、7组合法完整旅程**。显式grant探针采用其本可覆盖的合法精确包请求，确认拒绝来自语法校验。另独立运行新增合同测试：**9 passed、35 deselected**；两个schema的`check_schema`通过。仅使用临时目录，未安装、写源码或生产State。

### r2实际证据与剩余门禁

- 协调者以原Python3.11.15、显式源码路径及禁写cache配置，独立重跑原四套加`test_schema_contracts.py`：**144 passed、2 skipped，9.48秒**。两项跳过仍是原生Windows junction。作者同五套源码144/2及Python3.12.3非editable包144/2日志已核读，包内这144项未由协调者再次运行。
- 独立逐字比较最终359份源码、wheel和实际安装文件及身份记录一致，283冻结身份保持。r2 wheel SHA256为`fa3bc27cf5cfc73f6f6412f6ba20cc220af380fd2b9eef80353bf326a3a33ccf`。旧r1 wheel及`r1-package-identities.json`另存，未用新包覆盖其历史结论。
- 核对r2的26次CLI原始argv/退出码/stdout，独立读取恢复库并重新编译，与恢复前后预览完全一致，仍为10实例、13,213字节及`fcf1279f5d3bacd0056c5662b75d4d6a2eb9f36731daddb29628d08731dbd455`。独立`backups.verify`通过，4 Agent/5 Workflow、两库索引一致、0个Agent运行；r2备份manifest SHA256为`f372c82f6f042b2d8ccf4c841d62d5eda1e1722f16e07a8da577e7e87c4718bf`。
- r2性能记录绑定上述实现SHA和Python3.12.3安装包，仍为warm缓存、同进程顺序、每种5样本；4/22/102实例中位16.2/23.6/52.4毫秒，单独测量的tracemalloc峰值约4.50/4.51/4.56MB。仅核原始样本及范围说明，未独立重测，不据此判断运行吞吐或容量。
- r1自身Claude审查[原样结果](evidence/2026-11-09-ac3d-self-review-r1-result.json)与[身份](evidence/2026-11-09-ac3d-self-review-r1-identity.json)已独立核对：25项保护源码对应r1 scope、manifest和实际prompt SHA一致，公开结果与本地原始结果逐字一致，CLI及原生回执成功；run `8841724392044f9d9f060cae38782abb`，decision approve。它漏掉SP-1/SP-2，保留为旧r1历史审查，不覆盖原发现。r2自身调用已启动，当前尚无回执，未登记通过。
- 2026-11-08 17:18:10 UTC结束复核时，除本报告同片追加外，其余37项仍与r2 scope逐字匹配；`git diff --check`及禁止落盘的19文档、327链接、57 CLI parser检查通过。

r2本地原始证据为`.ergora/checks/ac3d-workflows/r2-source-tests.log`、`r2-wheel-tests.log`、`package-identities.json`、`r2-cli-journey.json`及其逐命令输出、`r2-preview-performance.json`。待验项仍为r2自身真实reviewer、必要双OS CI及精确候选/远端终结；实际装载、权限强制和持久执行继续按后续切片验收。

r2两轴计数：Standards 0项未解决（ST-1已关闭）；Spec 0项未解决（SP-1/SP-2已关闭），无新增finding。

## WD5最终范围与自身审查核证（2026-11-09）

**WD5本地证据及同片独立复核通过，无新增finding；Standards与Spec均无未解决项。** 上文r2时尚在途的自身审查现已有实际回执；WD6普通提交/推送、必要双OS CI及精确候选/远端终结仍待后续核证。

2026-11-08 17:41:44 UTC，协调者独立核对`.ergora/checks/ac3d-workflows/review-final-scope.json`全部44项逐字匹配。scope SHA256为`8da22fb5dbe60e629754df59305b19f64ee7c1bc121ee48065f96a38a7dfe782`，`review-final-tracked.diff` SHA256为`91c6ef93c402d243dc3c160adacfeba5fff0c7f06d57df8b53aa482450ff7208`，后者与当时限定范围的实时`git diff`字节一致。基线/HEAD仍为`9bb84c6437bd4b38f928defcaad0ec678fa24a5e`，分支`refactor/architecture-foundations`，尚未提交。

相较r2的38项，新增`docs/AGENT_BACKENDS.md`、可分享本地身份JSON、r2自身审查的结果/身份JSON、r3自身审查的结果/身份JSON，共6项；其余增量是计划、ADR、交付及本报告的状态记录。源码、测试、schema和示例均与已复核r2相同，未重跑无关测试。新增手册说明按实际后端允许只读检查方式；AC3b细分计划仍明确后续责任，没有将静态预览升级为运行能力。

### r3真实输入与回执

实际调用沿现有`ergora agent run`、`repository-governance`模板和reviewer角色，后端为Codex；未独立识别其默认模型。run `5abc348026a94c20a367199479c2cfcd`于2026-11-08 17:36:20 UTC完成，CLI与SQLite运行记录逐字一致，原生returncode 0、status succeeded，结构化decision approve，无新增finding或建议。

独立读取实际协议目录、运行数据库、CLI原始输出及[公开结果](evidence/2026-11-09-ac3d-self-review-r3-result.json)/[增强身份](evidence/2026-11-09-ac3d-self-review-r3-identity.json)，核得：

- 25项保护源码/测试/示例均与当前文件及manifest匹配，manifest SHA256重新计算一致。4份关键新文件在实际任务文本内各有完整正文，逐字等于当前文件。
- 原任务文本124,278字节，SHA256 `cbc3c3f91102edf46594c7beb443caf35b6f6b123f7141b4e288283ea605421e`；最终交付125,097字节，SHA256 `68f0436d675b70c03f6c2e4cf49656d21345d9404fbb53d5aae239c028cdcd4c`。两者之差逐字等于`agent_runs`按实际模板添加的reviewer要求及result schema，结构化结果亦通过该schema校验。
- 公开结果与运行记录指向的原始result及本地留存result逐字一致，SHA256 `b0ec8904661ed4f28bfc5cab8bf7e98a48104420a178d485e5a6222664783883`。

审查报告声明实时git diff/log及独立hash命令遇沙箱挂载错误；原生事件也保留`bwrap: Failed to make / slave: Permission denied`。不能将这次调用描述为所有命令通过，也不以它证明OS隔离。协调者另外直接核对了44项实际文件、实时tracked diff及上述协议身份，未把审查者依赖manifest的身份判断当作独立hash执行。该调用没有重跑项目测试，不替代原fresh-context两轴及源码/包/恢复证据。

### 历史结果与交付边界

r1旧快照approve仍保留其漏掉SP-1/SP-2的事实。独立核对r2运行数据库与[原始结果](evidence/2026-11-09-ac3d-self-review-r2-result.json)/[身份](evidence/2026-11-09-ac3d-self-review-r2-identity.json)：Claude run `2fad7f1f057545de95a706d44f7a157e`为timed_out、returncode -9；Codex回退run `f5b368d0b4ab4679be5f907151c4e980`为succeeded、returncode 0、request-changes。它因任务文本限制而未能完成新文件检查，没有建立源码finding，未当作通过。r3修正的是检查输入与读取方式，生产实现未变。

[可分享本地身份](evidence/2026-11-09-ac3d-local-identity.json)与实际最终包、26次CLI及性能原始记录一致，未将r1扩大回归与r2受影响检查混加。最终包仍为`fa3bc27cf5cfc73f6f6412f6ba20cc220af380fd2b9eef80353bf326a3a33ccf`，前节独立核验的144/2、359/283及完整恢复预览证据保持原范围。此时未提交，尚无本候选CI或远端终结结论。

WD5两轴计数：Standards 0项未解决；Spec 0项未解决；原3项均关闭，无新增finding。下一核普通提交的完整Git对象、必要双OS CI及即时远端身份。

2026-11-08 17:45:03 UTC补核：`git diff --check`及20文档、362链接、57 CLI parser均通过；检查脚本禁止落盘。除本报告追加外，其余43项仍与固定final scope匹配。公开本地身份与r3保护源码清单逐项相同。

## WD6候选Git对象核证

2026-11-08 17:45:48 UTC独立核候选`833d46fd42e2064f8417f30b430c44069ac03a61`：唯一父为`9bb84c6437bd4b38f928defcaad0ec678fa24a5e`，变更路径恰为固定44项，每个Git对象内容均逐字匹配上述final scope，没有漂移。另从候选Git archive读取`src/ergora`全部359文件，其完整身份表与已验r2 wheel `fa3bc27cf5cfc73f6f6412f6ba20cc220af380fd2b9eef80353bf326a3a33ccf`一致。

候选含的是stage前的本报告版本；本次WD5核证及后续Git/CI/远端记录属于随后同片状态归档，不改变已审源码。后续若开始AC3b工作树，AC3d仅按此固定候选验收。此次尚未登记push成功、必要双OS CI或即时远端终结。

## WD6首次CI失败与Windows夹具修正复核

原候选`833d46fd42e2064f8417f30b430c44069ac03a61`的[Portability CI42506504390](https://github.com/626619403/Ergora/actions/runs/42506504390)实际失败，不能因WD5本地通过而关闭WD6。协调者只读解析保存的官方run/job页面、jobGroups和Windows失败annotations：Ubuntu job为success，Windows job为failure；Windows回归为**3 failed、554 passed、448 skipped、16 subtests passed**。保存位置为`.ergora/checks/ac3d-workflows/ci-r1/`。

三项失败均位于原工作流测试：重复引用及祖先来源、收窄权限不能删除继承材料、版本导出和完整备份。官方annotations分别显示`sub-instructions`、`inherited-instructions`、`review-instructions`的resource SHA mismatch；其中收窄权限测试因提前遇到该错误，未到达其原本断言的“Required inherited resource is not readable”。

根因已独立确认：[test_workflow_definitions.py](../../tests/test_workflow_definitions.py)的`write_bundle`将含LF的字符串用默认newline的`write_text`写出，而声明的SHA按原字符串UTF-8字节计算。Windows将换行写为CRLF，因此资源校验按实际字节正确拒绝。协调者用标准库内存文本流显式模拟CRLF翻译，复现旧写法SHA不符，并验证精确UTF-8字节与声明SHA一致。JSON文件自身仍按实际包树计身份，无此预先声明正文SHA的问题。

建议修正通过本地独立复核：仅将该instructions写入改为`write_bytes(text.encode("utf-8"))`。`.ergora/checks/ac3d-workflows/portability-test-fixed.py`与固定833d测试对象严格相差这一行，SHA256为`5c8de4dfe017b353ca2d486c551463015740c7f1fbd710fc124848cce3266c0f`。不需要修改生产读取、摘要算法或283冻结内容。

隔离树`portability-source/`的699个受版本控制文件逐项与833d比较，唯一差异为上述测试文件，且等于待stage的固定blob；没有混入AC3b变更或额外非cache文件。作者原隔离日志为44 passed/2.42秒；协调者另用显式隔离源码路径、禁止cache，在该树独立重跑原工作流套：**44 passed/1.83秒**。这是Linux定向验证，尚不能替代新的Windows CI。

交付记录如实保留首轮失败、夹具根因、单行修正和AC3b隔离边界，无新增生产finding。支持将固定原测试加该单行及两篇原片报告作同片普通修复提交；下一核新提交的精确Git对象、完整双OS必要步骤与即时远端身份，未登记修正后Windows或完整AC3d完成。

## WD6最终双OS CI与即时远端终结

**AC3d完整交付可关闭。** 原ST-1、SP-1、SP-2均已关闭，Windows夹具修正通过新候选实际双OS验收，无新增finding。首轮失败、各次自身审查结果及其限制保留原记录。

2026-11-08 18:13:35 UTC独立核修复候选`460702f9866080756883501eefc5132b8a345a38`：唯一父为`833d46fd42e2064f8417f30b430c44069ac03a61`，恰有3个变更路径——原工作流测试、本片交付记录、本审查报告。测试Git对象SHA256为`5c8de4dfe017b353ca2d486c551463015740c7f1fbd710fc124848cce3266c0f`，与已审固定blob逐字相同，严格只有上述一行修正。候选`src/ergora`全部359个文件的身份表与已验r2 wheel `fa3bc27cf5cfc73f6f6412f6ba20cc220af380fd2b9eef80353bf326a3a33ccf`一致，未包含AC3b.1生产或新增测试。核验时本地HEAD `4f102da873fc19c8a805031106d7a7c4524d5908`不是本次验收候选。

协调者于2026-11-08 **18:17:19–21 UTC实际GET**[官方CI42507828386](https://github.com/626619403/Ergora/actions/runs/42507828386)的完成run、完整job列表及两个完成job。run为Success，完整列表`hasMore=false`、`totalCount=2`；两job均completed/success。

|实际读取的job|必要步骤及结果|完成页面读取时间（UTC）|
|---|---|---|
|[Ubuntu / Python3.11](https://github.com/626619403/Ergora/actions/runs/42507828386/job/128814198582)|Build and install wheel、Packaged reference identity、Native application regression，3项全success|2026-11-08 18:17:21.900397|
|[Windows / Python3.12](https://github.com/626619403/Ergora/actions/runs/42507828386/job/128814198683)|上述3项及Windows PowerShell 5.1 installer and upgrade，4项全success|2026-11-08 18:17:21.888948|

逐项核验必要步骤有完成标记，全部step log URL绑定完整`460702f9866080756883501eefc5132b8a345a38`及对应job ID；无failure/cancelled/timed_out步骤。实际响应SHA256：run HTML `c01fa01124d3b0898f9f4dcb1e92480d5ada8f21a6f9403c56158a5cfb65d1b1`，完整job列表 `1df77382cc2913dd75ef4e0c31a66f340b5c466891baa3b54a8da1d1eee94e7d`，Ubuntu HTML `88962d5cd2aa77cd76e775975991f83bf2c5f20c1b92cbebbe57a860f470515e`，Windows HTML `a59259718e075b96be9d3d1b86ee37320747a4f1e50ecf1612a9e68e7722db09`。

随后于2026-11-08 **18:17:26.050635 UTC**实际执行RSA `git ls-remote`，returncode 0，核得`refs/heads/refactor/architecture-foundations`恰为`460702f9866080756883501eefc5132b8a345a38`。SSH配置只在进程内读取，未输出私钥或SSH命令配置，未执行push。

本段为原切片最终状态归档。AC3d验收仍限静态定义、完整继承编译、不可变库及备份/预览合同；实际资源装载、权限强制、正式manifest准入和持久嵌套执行继续归后续AC3b/c/4。最终两轴：Standards 0项未解决，Spec 0项未解决；普通候选、必要双OS CI及同片即时远端终结全部具备实证。
