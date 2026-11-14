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
