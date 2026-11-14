# G1a 不可变记忆模板补丁：独立审查

2026-11-14。Reviewer：`/root/memory_preset_patch_review`，fresh-context，未参与实施、未继承实施会话。依照项目 `AGENTS.md`、`docs/PLAN.md`、`maintainable-project-delivery` 及其 independent-review brief，直接核对[原合同](../plans/2026-11-14-memory-preset-patch.md)、产品、实际调用者与原件。

**最终本地结论：需求轴 approve；维护性轴 approve；开放 finding 0／0。** 此结论覆盖本片最终本地产品及已发生的安装、准备、回归、自身模板与原件总核。前继 CI、后继 G1b、本片固定发布／远端 Ref／自己的 CI 不在此结论中。

## 身份与完整范围

固定基线及审查时 HEAD 均为 `593da960f9eb4039518cfae9119ddafc1f7a847b`，分支 `refactor/architecture-foundations`。检查了 tracked diff、全部 untracked 路径和文件正文，并从基线 Git tree 直接读取全部 604 个产品文件；当前为 611 个。产品差异精确为以下八个路径，没有 Python、schema、依赖、测试、安装器或 CI 变化：

|产品路径（均相对 `src/ergora/data/presets/`）|实际变更|
|---|---|
|`presets.json`|原 `memory-retrospective` 选择新 root，保留旧依赖并追加新依赖|
|`agents/ergora-memory-retrospective-author-v1.0.1/agent.json`|同 ID 新版本与新提示 SHA|
|`agents/ergora-memory-retrospective-author-v1.0.1/instructions.md`|首行仅删除一个尾空格|
|`agents/ergora-memory-retrospective-reviewer-v1.0.1/agent.json`|同 ID 新版本与新提示 SHA|
|`agents/ergora-memory-retrospective-reviewer-v1.0.1/instructions.md`|首行仅删除一个尾空格|
|`workflows/ergora-memory-retrospective-v1.0.1/workflow.json`|同 ID 新版本与两条精确 Agent ref|
|`workflows/ergora-memory-retrospective-v1.0.1/instructions.md`|与原资源逐字相同|
|`workflows/ergora-memory-retrospective-v1.0.1/skills/ergora-memory-retrospective/SKILL.md`|与原 Skill 逐字相同|

同时读了 G1a 计划／交付／公共索引、G1 总计划及 `docs/PLAN.md` 变更。工作树中 F9d1 的计划／交付／独立报告／索引追加为前继发布记账，已辨明其范围，未以其已审结论替代本片审查。本报告是本 reviewer 唯一写入的文件；没有运行测试、模型或服务，没有安装、提交、推送或联网。

## 需求轴依据

1. **冻结身份与最小补丁成立。** 原两 Agent 与 root 的全部七个文件，与基线 Git 原字节及 `originals.json` 的长度／SHA256 均相同。逐字比较两新提示，恰好各删首行末尾的一个 ASCII 空格，余下全部字节保持。逐字段构造预期定义后比较，新 Agent 只变 version／资源 SHA，新 root 只变 version／两条 ref；权限、limits、ports、边、输出、角色及后端请求均保持。catalog 与基线相比恰好为合同所列修改，28 个 preset、其他 27 个条目保持，没有新别名。
2. **定义摘要独立重算相同。** 按原文件摘要与执行位清单算法重算，新 author 为 `90e09768e797c95b746892f517676a325c478096f86994043d9c78f8bc6ad1e2`，reviewer 为 `1a6c669477fa24fed91b000914adadcdafd2d8f74965e6ad2c3e37c94ca984ec`，root 为 `f80ea1f1512d5ac0d31ec90cd16a4c1360fd06aeee56a46eca76f04d419cd18b`；全部与实际引用、`versions.json` 一致。
3. **安装件对应最终产品。** 直接读 source snapshot、wheel 与实际 site-packages，611 个产品文件逐字相同，并与当前源完整路径集合一致。wheel SHA256 为 `a2009e901fefb6e0507d6fedb14dff27c662feabeddf71b5e5f6a6a89f4619f9`；619 个 wheel 文件及其 RECORD、624 行 installed RECORD 的有摘要条目逐件重算符合。direct_url 未标记 editable。283 份参考文件同时符合冻结 manifest 与基线 Git 原字节。
4. **实际旧库升级与新叶完整输入成立。** 直接读 `journey-r2.py`、24 条 CLI argv／exit／原 stdout／stderr，全部 exit0，逐份输出 SHA 与 commands 记录相同；原结果为 20 项／9.56140538584441 秒。旧客户端先安装 1.0.0，新客户端两次明确安装相同 1.0.1，返回四 Agent／两 workflow 的旧新精确引用。七个旧 library 对象文件、旧 manifest 与两输入的完整 37 文件集合和字节保持；新客户端读回旧 root／两输入的完整 JSON 相同，沿同一旧 manifest 再准备，两叶 digest／完整 prompt 相同。
5. **祖先资源、权限与后端保持。** 独立重算新 manifest／两 input 的完整树摘要及 request 的 prompt／task SHA。新 propose／review prompt 分别为 4,146／4,203B，均包含完整原 task、root instructions、完整 root Skill 与各自叶 instructions；各有三份资源，来源实例精确为 root 和本叶。子权限等于原 root 的只读上限，write／network 为空、shell 为 false。图仍为 propose→review→gather，默认请求仍为 Codex／Claude Code；request 的 execution_authorized 为 false。任意深度嵌套与额外祖先的支持，本片依据未改的递归 compiler 审查，不将这两直接叶准备扩大为新增的全深度动态验收。
6. **失败、回归与审查证据归属明确。** `journey-r1` 的 24CLI exit0、末尾 `KeyError: 'ok'` 与无 passing result 均保留；直接 diff 两私有驱动，r2 仅改输出目录和 reference verify 的 `status`／`files` 字段读取。最终安装原 `test_presets.py`／`test_memory.py` 的 stdout 为 48 passed／155.29 秒，原 process owner 为 succeeded／returncode0／156.773716093041 秒。读了实际 fixture，记忆回归跟随本次 install 返回的 root version，没有钉旧默认版本。

## 维护性轴依据

真实生产入口 `cli.py` 与 `web.py` 均调用原 `workflow_definitions.presets`／`install_preset`；catalog 的目录名用于定位完整配置包，定义身份仍由 ID／version／digest 决定。安装仍先导入全部 Agent 再导入 workflow，原 `DefinitionLibrary.import_bundle` 按版本追加、冲突拒绝、重入校验既有对象，因而这次 catalog 扩展有实际消费者和正确依赖顺序。

继续检查了 `workflow_definitions._Compilation`、`_materials`、`_within`、`compile_input`、`prepare_input_from_manifest`、`definition_bundles.DefinitionLibrary`、`agent_definitions` 及 `retrospectives.prepare_memory`。原 owner 分别负责精确引用、递归资源累加、祖先权限上限、完整材料容量与冻结输入；记忆准备接收显式 manifest／instance，无 1.0.0 分支。新静态版本复用这些边界，完整包副本符合不可变定义的自包含要求，没有引入新层、wrapper、registry 或第二记忆／评价／采用权威。

本片没有新增函数、分支、guard、fallback、产品断言、测试或 CI。两原 suite 与实际公开升级准备验证覆盖本次风险；没有为机械空白变化要求额外镜像测试。基线其他产品原字节完整保持，也未将新材料资源扩大为工具授权。未发现需要修正的正确性或维护性问题，最小修正项为空。

## 自身模板、最终原件与收尾

直接读最终安装件的原 structure-review 驱动、admission、native 回执、原 result 与完整 response。run `4f7fd8e3a1284ef582dc092b29268141` 为 succeeded／exit0，19.567424814682454 秒，decision 为 approve；requested_binding 为 Claude Code，binding 为授权 Codex 回退，理由在原记录中。没有将其写为异后端成功。

按 packet-index 从原 task 中逐份提取并重算 24 份全文（112,775B），每份与记录长度／SHA 相同；同时核原 input、run snapshot 与实际 stdin 的 119,658B 完整 prompt 相同、完整 task 和三份祖先／本叶资源均在 stdin。独立重算 input digest 为 `b0348a3608e1dafa5c1356bc8ff000dbac26eee10086982ed5301fafa8c54587`，原 result SHA 为 `b1ac719487805472a6477304f06dfe08eeee2f88aa2760cc355bac93721e4ab3`。该模型仅审提供的完整正文，其 approve 没有替代本 reviewer 的磁盘与调用链审查。

直接读最终 audit／collector 源码与原结果，并逐件重读[公共索引](evidence/2026-11-14-memory-preset-patch.json)的 **416 个唯一原件／2,700,168B**，全部长度／SHA 相同；规范 references 数组 SHA256 为 **`97061b95645d726c19817b1e1104aee05f3eaf427b547da51c063fe5e5e11e38`**，与 `collection-r1.json` 相同。没有重生成聚合，没有将本报告递归入索引。audit 所记所属服务 PID 为空；独立只读 `/proc` 观察亦无匹配本片的服务进程。tracked `git diff --check` 通过，另逐份检查七个 untracked 新产品文件，无尾空白或缺末尾换行，未把 tracked-only 检查冒充完整新文件检查。

本地验收可闭合，需求／维护性开放 finding 均为 0。计划和公共摘要可据此登记本地终态；本报告不批准尚未发生的发布与 CI。前继 F9d1 自己的 CI 及其原 reviewer 门禁闭合后，后续普通固定提交／完整远端 Ref、本片自己的必要 CI 与原 reviewer 补核仍须分别取得原证据。模型生成记忆候选、真实采用／训练／GPU／质量、Windows 本机、业务默认 home 升级、状态回退与跨机交接未在本片执行，继续按其原合同开放。

## 固定普通发布补核

2026-11-14，原 reviewer 按本片原合同，只读补核完整候选 **`506cc576874e92bc922644a8dd9f244151b08e4b`**：**发布门禁需求轴 approve、维护性轴 approve，开放 finding 0／0。** 本节为发布后追加，保留原本地结论及其发生时的范围；本轮未联网、安装、执行测试／服务、改产品、提交或推送，本片自己的 CI 继续待验。

- 直接读取固定 Git 对象，唯一父为原完整基线 **`593da960f9eb4039518cfae9119ddafc1f7a847b`**。20 个变更路径与 `static-final-r1.json` 集合相同，每个固定 blob 的长度／SHA256 均符合清单。原本地报告在固定提交中为 **9,249B／`8f4781869a0d89ddd4cae674a3447e79edf44db8ffd828f3d618671f0c3c27fc`**，与保留的 `independent-local-r1.md` 逐字相同；没有把本节写成发布前已经存在的审查。
- 从固定 tree 读取全部 **611 个产品文件**，完整路径集合、每份长度／SHA 和原 `product-mapping.json` 相同，且逐字等于最终非 editable 安装与原构建 source snapshot。产品变更仍精确为原七新增与 catalog 一修改，没有新增 Python、schema、依赖、测试、安装器或 CI。本地已审的两个旧提示原字节、三新定义身份、旧输入保持和祖先材料证据由相同产品身份承接，未冒称重新执行回归。
- 固定其余 12 个路径为所属计划／交付／本报告／公共索引、前继 F9d1 发布与 CI 终态记账，以及 G1b 的初始计划／交付。已直接读固定文档差异，G1b 当时仅记录待执行合同，没有日常应用替换或运行通过主张。当前工作树的 G1b 隔离安装／旧 schema 旅程与后续记账不在本次固定 G1a 实现审查内。
- 固定提交的 `raw_evidence.references` 与发布后 metadata 逐项相同，仍为 **416 条／2,700,168B**，规范数组 SHA256 仍为 **`97061b95645d726c19817b1e1104aee05f3eaf427b547da51c063fe5e5e11e38`**。416 份原件再次逐件重读，全部长度／SHA 相同。发布后单列的 `publish-r1.py`、`static-final-r1.json`、`commit-r1.json`、`push-r1.json`、`ref-r1.json` 共 **五条／12,621B** 也全部重算符合 `publication_evidence`，与原 416 路径不交叉，没有重生成本地证据或原聚合。
- 直接阅读发布驱动及回执。commit exit0，唯一 push argv 为 `git push origin 506cc576874e92bc922644a8dd9f244151b08e4b:refs/heads/refactor/architecture-foundations`，exit0，没有 force、`+` refspec、main 或 merge 操作。保存的 `git ls-remote` 在 **2026-11-14 10:53:08.569130 UTC** 返回同一完整 SHA 与该分支；本机 remote-tracking ref 也相同。远端结论绑定原回执的观察时刻，本 reviewer 没有重新联网查询。
- 前继门禁已在本次提交前闭合。固定 metadata 的前继 candidate 为完整 `593da960f9eb4039518cfae9119ddafc1f7a847b`、自己的 Portability run **`43585798832`**，publication 状态 complete。直接读其 `independent-terminal-r1.md`，需求／维护性均 approve、开放 0／0，与本次固定提交中的前继报告 **31,151B／`73ee557769b1f48c81e94ab00f1291d60a0c334314de81e6362f700883af4dc9`** 逐字相同。前继 48 条 CI 引用／3,326,398B 逐件摘要符合；原终态记录时间 **10:48:13.661145 UTC** 早于本次提交 **10:52:58.495952 UTC**。另直接解析八份最终 job HTML，状态 completed，其 **30 个必要步骤**的 success、完成标记、时间与精确完整候选 log URL 全部符合原终态投影；最终 run HTML 的 Status 为 Success，正文 SHA 为 `f8e3ad6680b24b009b3ed9ab4a6cab014cca92ed911d44f2ac23f062c8e6ffd3`。这些证据仅确认前继出口，没有充当 G1a 自己的 CI。
- 原静态清单记录暂存后完整 `git diff --cached --check` exit0，涵盖全部新文件。118 条变更文档本地链接另从固定 tree 解析，目标均在同一 tree 中存在。固定摘要如实记录原本地 approve／0 finding，并将当时尚未发生的固定发布／自身 CI 保持 pending；发布后 metadata 单列完整候选和五份回执，没有预写本次独立发布结论或自身 CI 成功。

**G1a 的最终本地与普通固定发布两个门禁均已闭合，两轴 approve、开放 finding 0／0；该固定候选自己的必要 CI 仍须单独取得终态与原 reviewer 补核。** 本轮没有确认 G1b、日常应用升级、状态回退或跨机恢复；原本地未验范围保持。

## 自身 CI 终态独立补核

2026-11-14，原 reviewer 对完整候选 **`506cc576874e92bc922644a8dd9f244151b08e4b`** 自己的 Portability [run `43587371986`](https://github.com/626619403/Ergora/actions/runs/43587371986) 进行只读补核。**需求轴 approve，开放 finding 0；维护性轴 approve，开放 finding 0。** 本轮只读取固定 Git 对象、原官方 UI HTML／JSON／receipt 与 metadata，追加本报告；未联网、下载日志正文或产物、执行测试／服务、安装、改产品、提交或推送。

### 需求轴

- 独立解析 `ci-list-html-r1/page.html` 的官方 embedded JSON，完整候选 commit anchor、`.github/workflows/portability.yml`、`refs/heads/refactor/architecture-foundations` 唯一对应上述 run，run number 为 **207**。其发现时的 In progress、旧 run／Windows 页面原样保留，没有用终态覆盖早期观察。初始 run HTML 的完整 SHA anchor、UI batch 与原 `ci-ui-metadata-r1.json` 绑定相同。
- 最终 `ci-run-html-r5/page.html` 的实际 Status 卡片为 **Success**，完整 commit anchor 为本候选。原 URL 与 final URL 均为本 run 的官方页面，HTTP200；receipt 时刻为 **2026-11-14 11:13:40.733549 UTC**，正文 **213,318B／`3c0df940623b4aacfe0f5705b29a3d12dad2187395f9b023e952f7091f5311ec`**。原 bytes／SHA 已直接重算相同。
- 从该固定 tree 读取 workflow 与 `scripts/ci/linux-groups.json`，预期为 plan、六个 Linux 分组及 Windows all，共 **八 job**。UI batch 的 `totalCount=8`、`hasMore=false`，八个 ID 唯一，名字／run 路径与 metadata 逐项相同；早期 batch 的在途状态只用于归属，实际终态分别读取下表原 HTML。

|Job|固定 job ID|最终原件目录|必要步骤成功数|Complete job UTC|
|---|---:|---|---:|---|
|plan|132424650111|`ci-job-132424650111-html-r1`|1|10:53:14|
|Linux group0|132424679298|`ci-job-132424679298-html-r1`|4|10:58:10|
|Linux group1|132424679308|`ci-job-132424679308-html-r1`|4|10:58:43|
|Linux group2|132424679336|`ci-job-132424679336-html-r1`|4|10:57:29|
|Linux group3|132424679319|`ci-job-132424679319-html-r1`|4|10:56:31|
|Linux group4|132424679323|`ci-job-132424679323-html-r1`|4|10:56:29|
|Linux group5|132424679307|`ci-job-132424679307-html-r1`|4|10:59:25|
|Windows all|132424679505|`ci-job-132424679505-html-r4`|5|11:12:01|

- 用独立 HTML parser 从实际 `check-steps`／`check-step` 重建结果，八 job 均为 completed，且各有唯一成功、已完成的 Complete job。**30 个必要步骤全部 success、带完成时间与 `data-job-completed`**：plan 的 Read explicit test groups；七个执行 job 的 wheel 构建安装、参考身份、原回归、观察上传；Windows 额外的 PowerShell 5.1 installer and upgrade。此处采用固定 workflow 的实际条件，六个 Linux job 跳过 Windows 专属步骤符合原规则。
- 全部 **76 个 success 步骤**的 log URL 均精确包含同一完整候选 SHA、各自 job ID 与实际 step number，开始不晚于完成、完成不晚于原 receipt 时刻。另有 **六个 skipped**，恰为六 Linux job 的 Windows 安装步骤，无其他失败或跳过。独立重建的八 job／30 必要步骤完整投影与 `ci-terminal-r1.json` 逐项相同；该原终态文件 **13,357B／`00da739ba8638b5ff4af7cfbfcedece68d57e84d11c78b2ecf35b09fae80923d`** 已直接重算符合。

### 维护性轴与证据保持

直接阅读发现、fetch、UI metadata 与离线 parser 脚本，未执行它们。全部 **18 组官方页面／UI batch receipt** 的原 URL、final URL、HTTP200、正文长度和 SHA 均与保留的原件相同；job 路径、run 路径分别精确落在上述 run／job 集合。此次依据是官方公开 UI HTML 和 UI job JSON，不扩大为读取步骤日志正文、REST 响应或下载 artifact 归档，也不据此编造测试 case 数。

新单列的 **47 条 CI 引用／3,256,342B** 已逐件重读，路径唯一、长度／SHA 全部相同，与原 **416 条本地验证**及**五条发布**路径互不交叉。原 416 数组仍与固定提交逐项相同，规范 SHA256 仍为 `97061b95645d726c19817b1e1104aee05f3eaf427b547da51c063fe5e5e11e38`；416 原件和五发布件再次逐件符合。固定 20 个 blob 仍符合静态清单，全部 611 产品仍逐字等于原产品映射、当前源与最终安装件，未出现新产品／测试／CI 改动。

原本地及发布报告快照分别保持 9,249B 与 13,708B 的原身份，均为本报告未改的完整前缀；本节只追加新的 CI 门禁结论。当前公共 metadata 正确记录该固定候选自己的 run 已观察 Success、原 reviewer 终核 pending，可依据本节同步终态；未借前继 F9d1 的 CI，也没有将 G1b／G1c 工作树资料纳入此固定 tree 的 CI 身份。

**G1a 此固定候选的最终本地、普通固定发布、自身必要 CI 三个门禁均已闭合；需求／维护性两轴 approve，开放 finding 0／0。** 结论只覆盖 G1a 原合同与上述实际证据，不批准 G1b、G1c、日常应用替换、旧状态回退或跨机恢复。原本地所列模型、训练、GPU、质量及本机平台未验范围保持；Windows 结论仅归属本候选自己的上述 CI。
