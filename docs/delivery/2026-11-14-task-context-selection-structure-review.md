# F10b 独立结构／维护性审查

日期：2026-11-14。审查者：fresh-context agent `task_context_structure_review`。仅继承独立任务简报，先读原始要求、仓库规则与[切片合同](../plans/2026-11-14-task-context-selection.md)，未继承实现者对话；按 `codebase-design`、`review-pr` 和独立维护性审查清单检查实际源码及调用者。本报告的写入是唯一授权修改，未改源码或安装环境，未执行 Git 写操作或昂贵 suite。

## 当前结论

- 需求符合性：**approve（最终本地候选及本片声明范围）**。修后源码、精确安装包、原日志与实际合成旅程相符；公开记录明确保留失败及未验范围。
- 结构／维护性：**approve，开放 finding 0**。原模块归属与依赖方向合理；一个 P2 到期窗口已修正，经相同探针及最终安装回归复核；另一个非阻断成本意见已按原 Skill owner 修正。

这是本地候选独立终核；本片尚未发布，也未声称自己的 CI 成功，后续发布身份与 CI 在实际发生后补核。

## 范围与精确身份

基线与当前 HEAD 均为 `a2899e84bc174c9abd331a7c9d01f7c7a63297ae`，分支 `refactor/architecture-foundations`；审查对象为其未提交 tracked diff 加新增 `task_context.py`、`task-definition-v7.json`。F10a 发布／CI 记录补充属于前片，不用来证明 F10b 成功。

实际检查全部 9 个产品文件及 5 个测试文件，并检查 `AGENTS.md`、`docs/PLAN.md`、本片计划／交付、USAGE、架构合同和以下邻接 owner：`memory`、`skill_assets`、`state`、`asset_trees`、`definition_bundles.DefinitionLibrary`、`workflow_definitions`、`reference_inputs`、`reference_workflows`、原六阶段／预算材料接口及原测试。

初审 14 文件身份集合 SHA256 为 `3fa89b148361813a2f331f41532f9849b48188a50bca33cf6679132c420a2275`；修后复核集合为 `f02fd718391d9fe783b50e6f35571d9369dd9d5a5b9a21840c344b441beb4b86`。集合算法：对下表相对路径到文件 SHA256 的映射按键排序，以 `json.dumps(mapping, sort_keys=True, separators=(',', ':'))` 编码后取 SHA256。修后逐文件身份：

|文件|SHA256|
|---|---|
|`src/ergora/cli.py`|`0a897a10db66224dc0576d416fc974e60c77bd9f77e458994bc2558d1bd52bb6`|
|`src/ergora/data/schemas/task-definition-v7.json`|`58537be6e181bc33f91e3d3774848f9ab6c201b38cf08c83372c39e4c37850ac`|
|`src/ergora/reference_inputs.py`|`c116d153b867aff6f013f1d980c9bf3c874d74013c2e32770d8b768c42aae09b`|
|`src/ergora/reference_task_creation.py`|`7bf31161ba500384b060410becea33586ea5fe1150be48ae1d0c5bf10923b173`|
|`src/ergora/reference_workflows.py`|`15cc616591bc9ab914092aa9f1245f4a95cf904311c05dff88ecd54a0c962be7`|
|`src/ergora/skill_assets.py`|`e14b2ae3d9227220e9979cce711e16776e52329060c68003b027b939cad9e096`|
|`src/ergora/task_context.py`|`2b28dd8f538d14db37d295d4bccf0419bdcb5faa83b2702aaa5bb84c83e61c55`|
|`src/ergora/task_envelopes.py`|`6f506429c9d91dd4696a8d0cd89ccefb1ca182849430bb4242d974b45f7cd2cf`|
|`src/ergora/tasks.py`|`1ed05e57a9f4c673976b965fcaeaa648457a39ac55afb5272e9fe01cf1db4ab1`|
|`tests/test_native_six_stage.py`|`8ebe1f26f5bd8c36548d286c5071f5a3915b78b68e0e40dba7e0d464a04c276c`|
|`tests/fixtures/full_stage_acceptance.py`|`2ce425abd45e349d9bd275cb95e8e349c29265b4c4c99827d092a07db8a8bf92`|
|`tests/fixtures/reference_acceptance.py`|`5398128afcc717b71e27ec59ddb5e48c8bc6e97345dd4def11070cf818fdbb04`|
|`tests/fixtures/stage_agent.py`|`f32eda82732b14689931ece96309a07e66e12f03f70b5a77b64ffec8e17d6cf4`|
|`tests/fixtures/work_delivery_acceptance.py`|`8ba563699fabb28d728d3b14248eca42ad31a32e3115207e112bff0946ae9b45`|

## 已修 finding

**P2：慢 Skill 核验期间到期的记忆可以通过首次发布复核。** 初审位置：`task_context._sources` 原第 18 行及 `require_current` 原第 118 行。原先 `memory.catalog` 先固定服务器有效性时刻，随后才读取 Skill head／历史及散列所选 Skill。可达情形为记忆尚余很短有效期，而所选 Skill 的读取在到期后结束；`require_current` 正常返回，随后原 publisher 可写首次 intent。SQLite 写预留阻止修订与删除，不能阻止时间经过。最小修正为在完整 Skill 核验后观察记忆有效性，继续保留原发布锁与首次 intent 归属。

审查者用既有到期 prepared envelope 做只读、依赖注入探针：catalog 时为 expiry 前一秒，`skill_assets.get` 把时钟推进到 expiry 后一秒。修前 `require_current_returned=true` 且返回时 validity 为 `expired`；修后同一探针抛出包含 `expired` 的 `ValueError`。未写任何源码或运行数据。修后 `task_context.py:35` 在全部 Skill 核验之后调用 catalog；已有 expiry 参数项也改为在实际 Skill 核验期间推进时钟。修后定向原参数项 1 通过／10.07 秒，最终安装十 suite 原日志也确认该参数项通过；finding 已关闭。

**非阻断成本意见：显式选择不应反序列化整个 Skill 候选和事件历史。** 初审 `_sources` 使用 `skill_assets.versions(...)["active"]`，会读取全部版本文件清单和全部采用事件，纯记忆选择也支付此成本。修正为原 `skill_assets.versions` 的显式 `heads_only=True` 投影，默认返回保持；无 Skill 选择时跳过 Skill 目录。只读 fake connection 追踪确认投影仅执行一次 `SELECT skill_heads`，不访问 versions/events。没有新增 SQL owner、store 或单次浅包装。未做吞吐优化主张；记忆目录仍扫描全项目最新记录，当前无证据证明其构成实质性能回归，保留为已知启动成本。

## 结构核验依据

- `task_context` 的真实生产消费者为 `tasks._definition` 的监督准备与 `reference_task_creation` 的 preview／首次发布复核；删除模块会把 canonical 来源与资源派生语义分散回两个 owner，独立文件有实际深度。
- 派生使用完整原 manifest 的私有副本及 `DefinitionLibrary.revise` 的资源 candidate 预览／采用；同一根 ID 仅改显式 version、追加声明及完整资源，不包新模板，不改子引用、成员路径、grant、limits 或全局 Skill head。初始及复制后 manifest 摘要、根引用、逐文件摘要和执行位分别保护来源变化与复制完整性，并非同一重复检查。
- 原 `_Compilation` 继续拥有完整祖先继承、同名 Skill 冲突、URI 可读、子权限收窄与 scope 容量；`_composition` 继续拥有后端／模式准入和实际完整文件冻结。新入口未加资源／权限解释器。原冲突、read ceiling、text-only 附件及容量拒绝测试仍位于这些 owner 的接口。
- `task_envelopes.selected_context` 拥有冻结选择、正文／来源／期限、附件 inventory／执行位与同 ID 根差异绑定；它不读 live store。下层保持 stdlib，可由原 bridge／离线读者使用；YAML 改为 Skill metadata 时局部导入有真实 SDK-free 调用理由。
- v11 Input／Adapter／Workflow 是既有版本映射与 Temporal 声明所需，继承原 v10 原生六阶段、预算、候选、审批、attempt-before-send／unknown 与证据 owner；无新 scheduler、表、head 或批准权威。
- 首次发布来源复核位于 `budget_run` 的原 `BEGIN IMMEDIATE` 及任务锁中、写首次 intent 前；无持久 intent 的 resume 直接拒绝。已有完整 intent 后的恢复不再读 canonical 来源，不重编译或延长预算。临时派生树位于原 supervised scratch，正常退出由 context manager 清理，强制退出继续由原 preparation owner 清理。

## 已读证据与限制

已直接读取开发记录：r1 为 6 失败／36.42 秒，r2 为 6 失败／54.52 秒，r3 为 6 通过／59.96 秒；材料 r1 为 1 失败／37.02 秒，r2 为 1 通过／56.92 秒。前两开发失败和首材料失败保留，未改称成功。以上通过早于本次到期／目录成本修正，不能作为最终源码身份的通过证据。

已读修前 `install-r1/package-identity.json`：non-editable wheel SHA256 `123a0b1b4704f9222db24a34f265e28b2e4217518822b1449d459025364288bc`，产品 577 文件、wheel RECORD 585 项、安装 RECORD 590 项，冻结参考 283 文件；它属于修前身份。上述历史结果不替代以下修后最终证据。本审查未自行重跑昂贵 suite 或安装。

## 最终本地补核

最终候选 wheel SHA256 为 `3f677bcf50ffcb514c1a029ae9ca78857f12aaf4a72d5d32ecf17f25f79e1a21`。直接读取 [公开证据摘要](evidence/2026-11-14-task-context-selection.json)、`current-identity-r2.json` 和所有 164 条引用的原文件，逐件校验大小／SHA256，全数一致。14 件产品／测试仍为上表修后身份集合 `f02fd718391d9fe783b50e6f35571d9369dd9d5a5b9a21840c344b441beb4b86`。

审查者的补核均为本地只读检查，没有重放创建／采用／HTTP 操作、网络调用、安装或昂贵 suite：

- **包与兼容原件。** 当前源码、`install-r2/source`、wheel 与 installed 的完整产品文件集合及 577 件内容逐字相等；实际读取两份 RECORD，585／590 项全部校验。原基线 Git 的 283 个参考 blob 及执行位与当前源码、wheel、installed 一致，未借上一片候选的 CI 成功。
- **原安装回归。** 直接检查 `install-r2/regression-r1` 的原命令、returncode、stderr／stdout：原十 suite 229 通过／6 跳过，pytest 412.30 秒、monitor 414.162772 秒，成功退出；六项为 Linux 上的 Windows 限定项。更正／删除／Skill head revision／慢 Skill 跨期限、持久 intent 后丢源恢复、旧版本与 stdlib 读取均有该候选原记录。
- **九 job／七叶实际材料。** 直接读取原 intent、各 job 的 formal-call／request／materials／invocation／prompt／实际 stdin、附件 coverage 和清理 witness；原 intent 文件 SHA256 为 `d9962eee18104398ed180d56d20a7b24e5b8c8a0ae3a3c6002bb59a330a65474`。九个原 owner 的 stopped／collection-stopped 均 confirmed，七个 model slot 数与原预算一致；每份 selected_context 相同、完整祖先 prompt 与所选记忆正文进入实际 stdin，七份所选附件各 75,600B 全覆盖。只读 canonical 数据库确认记忆正文／来源已清空删除、head revision 为 2、源 Skill bundle 与 manifest 已消失。stdlib 进程仍可完整 `unwrap`／读取冻结来源，未加载 YAML／JSONSchema／Temporal／MCP。
- **实际 CLI／HTTP。** 七条原命令确实使用最终安装 Python，均退出 0；四个原请求状态为 200／200／200／400，原响应大小／摘要一致。CLI／HTTP 预览及 show envelope 相同，canonical 删除／head 移动／丢源后的 resume-create 与原发布结果相同，旧选择 preview 明确拒绝；原业务 Git status 保持。原 cleanup receipt 确认线程／端口收尾，本地 `/proc` 检查该端口无监听。首 harness 的 `KeyError(detail)`、首只读续核的父目录误判与零重复 mutation 续核均单独保留，未称首脚本无人干预成功。
- **三项准入反例。** 祖先同名 Skill 冲突、完整材料容量超限均由原 v7 prepare 的已保存 stderr 给出精确原因，原 outcome 为 failed 且 cleanup confirmed，scratch 已清除、没有 creation intent 或正式 task。read 的原静态父 manifest 可由原 inspector 完整验证；生产 selected_manifest 因新增来源 URI 超出原 read ceiling 而拒绝，临时派生树已清理。这项只证明有效静态父图上的生产派生拒绝，不扩大为精确 read 的完整原生六阶段执行。r2／r3 harness 失败及不重复 conflict prepare 的续核范围与报告相符。
- **自身原模板。** 直接核 packet-index、归档 task／prompt／stdin／composition 和原结果：15 完整文件 288,364B 及全部祖先资源进入同一实际 stdin，prompt SHA256 为 `68230712f1748039708549eb7c915001655b1efbfab2fede33a1cbec897c2091`；38.840 秒原结果为 approve，结果 SHA256 为 `5b0fc07c370c1fbff6f011c54e14a048390bb28760a69ea867de1f222d0bd158`。其中文档保持当时在途身份，最终状态由本次独立核验补齐；该回复本身仅为源码建议，不充当 fresh-context 独立审查或异后端成功。

本片计划／交付／PLAN 现记录相同最终本地候选与失败边界，未提前宣称发布或自己的 CI 成功。本审查范围无新增 finding，原 P2 与成本意见关闭。发布、精确远端与自己的 CI 仍由原交付流程后补；UI 选择 F10d、复盘候选 F10c、原生 Windows v7 准备及 GPU／模型质量／测得性能改善均未被本结论认证。

## 固定发布身份补核

2026-11-14：上文是发布前的本地结论，本节追加已发生的普通发布事实。固定候选为 `f1cfcddd4d0e58b657b810b1f7dc98d070d255d9`，唯一父提交为 `a2899e84bc174c9abd331a7c9d01f7c7a63297ae`。本次只读 Git 对象及已保存私有原件，没有联网、重跑测试或用后续工作树替换该候选。

- 直接读取固定提交全部 29 个变化 blob，路径集合、字节数及 SHA256 与 `static-final-r1.json` 完全一致，包含原 F10a 状态补记与 F10b 本片产物；本报告在固定提交中的 Git blob 为 `71e3ccefd1eb0b4b89b076bd379f5dc55a7fa572`。
- 固定提交全部 577 个产品文件的集合与内容，逐件等于 r2 构建快照、wheel 和 installed；wheel SHA256 仍为 `3f677bcf50ffcb514c1a029ae9ca78857f12aaf4a72d5d32ecf17f25f79e1a21`。14 件产品／测试集合身份仍为 `f02fd718391d9fe783b50e6f35571d9369dd9d5a5b9a21840c344b441beb4b86`；283 个参考 Git blob 及 mode 与唯一父提交一致。因此前述安装、材料与独立结论确实归属于这个固定候选。
- 固定公开证据 JSON 保存 **164** 条原引用，逐件大小／SHA256 通过；发布后工作记录为 **168** 条，保留原 164 条不变，仅追加 `static-final-r1.json`、`commit-r1.json`、`push-r1.json`、`ref-r1.json` 四件发布原件，也全部核对通过。固定提交并不含发布后才产生的四件引用。
- 原 commit／普通 push／ls-remote 记录均退出 0，candidate 均为该完整 SHA；原 ref 回复精确为该 SHA 与 `refs/heads/refactor/architecture-foundations`。该结论来自已保存发布时原件，没有声称本轮重新联网查询当前远端。

固定发布身份补核 **approve**，需求／结构维护性结论保持，开放 finding **0**。本片自己的 CI 仍处发现阶段，本节不作终态成功主张；后续 F10c1 产品工作树不属于本固定候选。此次写入至此结束，CI 证据到齐后再另补。

## 固定候选自己的 CI 终核

2026-11-14：只读补核固定 `f1cfcddd4d0e58b657b810b1f7dc98d070d255d9` 自己的 [Portability run 43545573942](https://github.com/626619403/Ergora/actions/runs/43545573942)。原 `ci-run-html-r3/page.html` 的官方状态为 **Success**，完整 commit 链接及分支相符；原 HTTP 200 receipt 的大小／SHA256 与 HTML 逐字一致，观察时间为 `2026-11-14T02:38:02.525744+00:00`，body SHA256 为 `707c0c8c2c3dcc60fe0871684291b183cd907d68f556b41b2cc304c1ac58f6c5`。

已读 `parse-ci-html.py` 并用独立只读解析复核，没有运行其写文件部分。`ci-ui-metadata-r1.json` 与其原 job-groups UI JSON、原 run HTML 的摘要及八组 job ID／name／href 逐项相符；此早期 metadata 只证明身份绑定，不用其在途状态证明终态。固定提交的 `portability.yml` 与 `linux-groups.json` 确定 plan、Linux Python 3.11 六组及 Windows Python 3.12 全组，原 job HTML 与此集合完全一致：

|job|ID|必要步骤数|最后必要步骤完成时间（2026-11-14 UTC）|
|---|---|---|---|
|plan|132295977366|1|02:18:44|
|Native（ubuntu-latest, 3.11, group 0）|132296020866|4|02:22:40|
|Native（ubuntu-latest, 3.11, group 1）|132296020789|4|02:23:06|
|Native（ubuntu-latest, 3.11, group 2）|132296020747|4|02:22:50|
|Native（ubuntu-latest, 3.11, group 3）|132296020752|4|02:21:13|
|Native（ubuntu-latest, 3.11, group 4）|132296020816|4|02:22:52|
|Native（ubuntu-latest, 3.11, group 5）|132296020748|4|02:25:58|
|Native（windows-latest, 3.12, group all）|132296020795|5|02:36:10|

plan 的必要步骤为 `Read explicit test groups`；七个 Native job 均包括 wheel 构建安装、参考身份、应用回归与观察上传，Windows 另含 `Windows PowerShell 5.1 installer and upgrade`。全部 **30** 项 `data-conclusion=success`、`data-job-completed`、开始／完成时间齐全，开始不晚于完成，完成不晚于原样本观察时刻；每项 log URL 均精确包含本固定完整 SHA、对应 job ID 与 step number。Windows 应用回归于 `02:35:18Z` 完成，PowerShell 于 `02:36:09Z` 完成，观察上传于 `02:36:10Z` 完成。

本次校验 11 份原 HTTP body 及对应 receipt，共 22 件：最终 run r3、身份来源 run r1、原 job-groups UI JSON、plan／六 Linux 的 r1 job 页及 Windows 的 r3 job 页。页面最终 URL、HTTP 200、字节数和 SHA256 均通过；`ci-observation-r3.json` 的全部投影与原 HTML 一致。CI 补充原件身份另列于本节：observation SHA256 `2d6f894167e640b773cfe39f07d0d2cadac22379f277b9c3928feab921a633c0`；metadata SHA256 `eeb9a08ef1e5868ac2fd7465a1e743c9aa115e6f0a791e00b68fdfb25ce9279b`；parser SHA256 `111ffdfc5c11a7ec807bba9a54472db33f1ed84d2a0c956420fce52d1345c597`。运行级 r1／r2 及 Windows 早期在途样本保持历史身份，不改标成功；固定公开原引用 **164** 条与发布后 **168** 条仍保持，CI 补充未重写这两个集合。

CI 终核 **approve，开放 finding 0**；固定候选的需求／结构维护性及发布结论保持。本轮未联网、调用 REST、下载日志正文／artifact 或重跑测试，仅追加本报告；成功范围为该候选官方 CI 状态与必要步骤元数据，不扩大为原生 Windows v7 准备、GPU／模型质量／性能验收。当前 F10c1 工作树不属于此结论。
