# F10c2b2：工作流复盘候选独立评审

日期：2026-11-14。Reviewer 为本片新建的 fresh-context 独立 agent，未接收实现会话或预设结论。项目与文档根均为 Ergora。已读 `AGENTS.md`、[当前计划](../PLAN.md)、[本片合同](../plans/2026-11-14-retrospective-workflow-candidates.md)、[交付记录](2026-11-14-retrospective-workflow-candidates.md)，并应用 maintainable-project-delivery／独立评审 brief、codebase-design、review-pr。本地用户指定的 `AIHERO.md` 存在，已读其共享技能索引；没有因索引另行委派或修改产品。

固定基线及初审 HEAD 均为 `0f01fdd9736fc456cf1cdcc8d77e64dac916e8a0`，分支为 `refactor/architecture-foundations`，审查对象为完整未提交工作树。原始 tracked／untracked 文件身份及完整 patch 以本片 `review-scope-r1.json`／`review-diff-r1.patch` 留存；初审逐项核对时只有 PLAN 与本片交付的追加状态不同于该 scope，产品身份一致。上一片记忆／Windows CI 预算的发布与样式记账未当成本片产品或验收。

## 初审结论

**需求／行为轴：request changes，确认两个 P2（R1、R2）。结构／维护成本轴：未确认独立结构 finding。** 两个问题均可达并已由 reviewer 在源码公开接口定向复现，不能以已有正例通过关闭。本节为 r1 初审，不声称修后代码、最终安装、本片交付或 CI 已通过。

本片产品范围为 `src/ergora/retrospectives.py`、`cli.py`、`data/presets/presets.json`、新 `data/schemas/retrospective-workflow-proposal-v1.json`，以及新 `ergora-workflow-retrospective-author`／`reviewer` 两个完整 Agent 目录和 `ergora-workflow-retrospective` 完整 workflow／Skill 目录；同时审查原 `tests/test_workflow_definitions.py` 的新增用例、README／USAGE／架构说明。邻接 owner 包括原 `workflow_definitions`、`definition_bundles.DefinitionLibrary`、`asset_trees`、`contracts`、`handoff`、普通 Agent 结果接口及原 Skill／记忆 retrospective 调用。

|r1 文件|字节|SHA256|
|---|---:|---|
|`src/ergora/retrospectives.py`|31114|`41e707f7c088a4e384b93750cc927ef0bc54b38923b45232be3e07885b506055`|
|`src/ergora/cli.py`|83762|`b437425ba2c788cb6a11a5d9205323146151d7edce65408ee4c083b8f6a2255a`|
|`src/ergora/data/presets/presets.json`|17851|`dcfaa0444df4cf6b873af0fb24db1928e0f8fa297634ac5cafa07e721012db4a`|
|`src/ergora/data/schemas/retrospective-workflow-proposal-v1.json`|3037|`acaa01c7aff2e1fd5bd34b87fc556d10ff88f7666bfb880796286c777ad4de35`|
|`tests/test_workflow_definitions.py`|52336|`b8b47c8457673b7c124a973583f58689a224494384599e2e47cdb96395b57e9e`|

## R1：文本准入没有覆盖完整工作流资源（P2，待修复复核）

位置：r1 [完整文本读取](../../src/ergora/retrospectives.py) 第 107–118 行，以及同文件第 438–447 行的候选资源修订链。`_read_files` 只对原字节执行 UTF-8 decode，没有拒绝 NUL；工作流路径也没有像原 Skill `_file_manifest` 那样遍历全部正文拒绝 NUL。候选则直接交给原 `library.revise`；原库有意支持 Skill 内二进制附件，只检查 `SKILL.md` 与声明的正文资源，不能承担本片更窄的文本合同。

Reviewer 复用新增公开 fixture，在私有临时目录依次调用原 import／manifest、`prepare_workflow`、`check_workflow` 与 `export_workflow`，没有修改产品或活动项目。两种实证：

- 原合法目标的 Skill 支持文件为 `before\x00after` 时，prepare 成功，冻结的完整 baseline 正文确实含 NUL。
- 候选向声明的 Skill 内写 `reference.bin`，base64 解码为 `00 ff 01 62 69 6e 61 72 79`，check 成功且 export 逐字输出该非 UTF-8 文件。

原输出分别为 `{"case":"baseline-nul-supporting-file","prepared":true,"froze_nul":true}` 和 `{"case":"candidate-binary-write","checked":true,"exported_bytes_hex":"00ff0162696e617279"}`。这违反本片完整文本／二进制拒绝及 Skill 中“write 完整 UTF-8”约束；实际没有越过逻辑工具权限，不能夸大为 shell 执行或已采用。

最小修正：在 retrospective 共享 baseline 文本读取处拒绝 NUL；在本片工作流候选资源 write 或完整候选文本准入处核 UTF-8／NUL。沿用原 base64／资源操作／图校验，不限制原通用版本库的二进制合同。原 suite 补对应真实支持文件的正反例即可。置信度 100。

## R2：冻结遗漏空目录，未请求的删除也不出现在原预览（P2，待修复复核）

位置：r1 [目标冻结](../../src/ergora/retrospectives.py) 第 380–387 行及同文件第 423–427 行的恢复。`inventory_tree` 返回完整 directories，但准备只取 files；后续 `restore_manifest` 仅由文件建立必要父目录。原 `manifest_digest` 只覆盖文件与执行位，无法检测空目录消失。原版本修订则明确通过 `accepted_candidate.directories` 绑定所有目录，且 [原资源合同](../WORKFLOW_DEFINITIONS.md) 第 334 行承诺空目录与未改内容保持。

Reviewer 构造了原库合法接受的 `skills/target-guide/references/empty` 空目录，原 `prepare_manifest` 的完整包中该目录存在。随后仅提交 description／加依赖边候选，`resource_changes.operations=[]`；check／export 成功，导出包却丢失该目录。原输出为：

```json
{"case":"unchanged-empty-directory","baseline_has_empty_directory":true,"candidate_operations":[],"export_has_empty_directory":false,"revision_directory_changes":{"added":[],"removed":[]}}
```

因此既有原预览也未显示此未请求删除：目录在预览开始前已经从 scratch baseline 丢失。完整文件 SHA 相同不能证明完整原资源保持；这是静默内容集合变化，不是普通错误文案或样式问题。

最小修正：本片冻结原排序目录集合，并让 baseline／提案身份绑定文件身份与目录集合；离线只在本片私有 scratch 沿原 portable path／inventory 限制补原目录，再进入原 revise 的 preview／accepted_candidate／export。恢复后须对完整目录集合严格相等复核，不能以补祖先或排序静默接受另一集合；导出回执区分原 manifest 文件身份与含目录 baseline 身份。无需改通用 Task 运输或另建版本库。置信度 100。

## 需求轴其余实证

- 原完整 manifest verifier 重编译全部递归 workflow／Agent，核引用 digest、各层权限上限、全部祖先资源、端口、依赖及预算；prepare 冻结完整文件正文／执行位，经原完整叶 input 门禁发布，没有截断后标记完整。结果最多 8 MiB，原结果 SHA、普通 Agent 封套、来源 selection identity、baseline 及精确引用均由原检查链核验。
- `_workflow_scope` 固定根 ID／schema／权限／limits／输入输出以及全部节点的引用、职责、权限、输入与审查要求，仅允许根 description、原声明资源内容及额外依赖边；原依赖集合不可移除，原编译器拒绝环。候选 resource path 仅限已声明根文本路径或声明 Skill 后代，不能借根候选改子定义。
- 检查用 `TemporaryDirectory` 管理完整 scratch 生命周期，先原 restore，再原 revise preview、显式 accepted_candidate 和 publish 到 scratch，最后以冻结 grant 重新 preview；因此根自身 limits 与项目 grant 两层均保留。null 仍核原 baseline；导出要求原结果 SHA 与明确候选 digest，走原完整 export／no-replace，旧输入与既有目标受保护。check／export 不构造 State、不重新读实时来源或认证作者。
- 新 preset 是普通只读 Codex 作者→Claude 审查定义，原静态依赖不自动运行端口。原编译器负责完整祖先累积与父子权限约束，原叶调用负责后端选择；审查 approve、check 和 export 均不授权正式 import／manifest 选择或质量评价。逐项比较目录 catalog 的原 27 个 preset 全部保持，只新增第 28 个。

## 结构、必要分支与测试成本轴

三个公共工作流入口由实际 CLI 消费，放在原 `retrospectives` 用例 owner 合理；不是把工作流专用语义下沉到通用文件树或 Agent 运行器。新 `_read_files` 服务原 Skill 与工作流两个真实目标，集中完整有界 UTF-8 读取；`_workflow_scope` 是本地受限修订规则；contextmanager `_workflow_proposal` 同时提供检查结果与在有效生命周期内的 scratch library，使 export 复用同次结果检查和原预览。未发现为假想消费者增加的 registry、透传类、第二调度／评价／采用 owner 或后端具体类型分派。

新增 guards 对应可达外部输入和身份风险：误选 manifest／版本、来源与引用错绑、根视图偏离完整 manifest、受限节点／权限／图变更、跨子资源、null 导出、明确结果／候选身份、冻结输入污染及既有目标覆盖。原库继续拥有资源操作 schema／路径／base64／普通文件／目录冲突与 accepted_candidate；原编译器继续拥有递归权限／端口／预算，未看到应由本片重复实现的这些算法。R1 属于本片更窄的文本合同，补在用例 owner 有必要。

新增测试留在原 `test_workflow_definitions.py`，复用原 handoff 与 bundle／manifest 接口，正例跨 check／export／原 import／新旧 manifest；拒绝例保护候选越权和旧图 gate，不是只锁实现内部函数。严格 grant 与冻结根视图 case 针对普通根 preview 不能保护的两类静默错误。没有确认需删除的无关断言或硬编码配置约束。R2 应用真实空目录保持正例修补原 fixture，而不是创建平行测试框架。

## 实际检查与未验边界

本 reviewer 已做完整产品／新增测试／邻接 owner 静态阅读、scope 字节 SHA 与 catalog 比较，以及上述两次源码定向 fixture 复现；使用已有解释器和 `PYTHONPATH=src:tests`，不把它称为最终非 editable 安装验证。未运行重型 suite、安装、真实模型、网络、提交或修改产品。

直接读开发 r1 的原 `result.json`／stdout：原三 suite `-k retrospective` 为 **39 passed／104 deselected／46.36 秒**；runner wall time 为 **46.981001993175596 秒**，分别记录。该结果早于新增严格 grant／冻结 root-view case，不能替它们背书。

另已直接读作者后来提供的 r1 安装身份／native／models 结果摘要：非 editable wheel SHA `2aa433a102927b37805ea058242b8969d5f1d8e814fbb428f0860d7ed1cef862`，602 产品／两 RECORD 610 与 615／283 reference；合成正候选实际 11 CLI，真实 Codex→Claude 7 CLI 为 candidate null／review approve，prompt 分别 100760／108460B。此处只是已读取的摘要，尚未逐个重核全部原件、安装 RECORD、实际 stdin 或命令 SHA，不把作者报告替代为本 reviewer 完整终核。模型 null 不证明能生成正候选，图准入不证明效果。

作者已接受 R1／R2，拟在同片修正并以新 r2 包独立验证；r1 原件与失败应保留原身份。本片最终验收仍待修复源码与回归复核、最终包／安装／实际 CLI、原真实模型材料在修后 checker 的精确重核、自身原结构模板、全部 evidence 引用与收尾，以及普通发布／完整远端 Ref／自己的必要 CI。完整 Forge、F10d／F9d／G1、原生 Windows 模型和真实 GPU／业务质量／性能不在本次已验范围。

## R1／R2 修复补核：r2 源码与安装定向合同

同一 reviewer 在本片继续独立补核，HEAD／分支仍为上文精确基线；保留前述初审与原失败，不改写 r1 结论。**R1、R2 的源码修正与 r2 安装定向合同通过；开放代码 finding 为 0／0。需求轴在本节已验范围 approve，结构／维护成本轴 approve。** 完整最终 suite、实际 CLI／模型／自身模板、全部 evidence 和发布／CI 仍待后续原件终核，本节不预批本片完成。

修后 `retrospectives.py` 为 **33282B／`1499cc453a8d27e209b7c9ef9196a79b20aed219e0851e907dabed7e740cce04`**；原测试文件为 **54980B／`d2bb1a93a6de819dbb0a2f2f6bd58b06f16a0d6a3e6eef6845cbd42626900bce`**，均逐字等于最终 r2 source snapshot。其余既有产品的保持范围由下述全包比较覆盖。

### 修复的实际行为与所有权

R1 已在原 `_read_files` 对每份完整 baseline 原字节拒绝 NUL，UTF-8 decode 继续保留原字节；原 Skill 已有相同候选约束，未改变其文件／元数据身份。工作流 offline checker 遍历完整冻结 baseline 同样拒绝 NUL，并核实际编码后的合计容量，不能通过自行准备普通叶 input 绕过 prepare。候选先由原 revise 核资源操作 schema／base64／路径／候选树，再对每个 write 施加本片 UTF-8／NUL 合同，最后进入原 accepted_candidate／grant 编译。原通用库、Task 运输及二进制附件能力没有修改。

R2 已冻结原 `inventory_tree` 的完整排序 directories，prepare 在完整文件读取前后核原 inventory 不变。`baseline.manifest_digest` 保留原文件／执行位身份，`baseline.digest` 则重算 canonical `{manifest_digest,directories}`，提案绑定后者。offline 先核该组合身份，以原 restore 恢复文件，只在本片私有 scratch 用原 `relative_path` 补目录；随后原 inventory 的目录清单须与冻结清单严格相等，再以原完整 manifest verifier 复核。原资源 preview／accepted_candidate 因此以真实原目录集为基线，原 export 保留空目录。回执分别给出 baseline digest、原 manifest digest、原目录和候选目录，手册亦明确区分两种身份。

该修复集中在已有用例 owner：没有扩展通用 restore 的所有消费者，没有另造目录树校验器或新状态／采用权威。对 NUL 的新检查保护复盘更窄的文本合同；目录组合身份与严格 inventory 检查分别保护提案错绑和恢复时静默规范化，职责不同。保留原两个 grant／根视图反例，二进制四例新增于原 suite，空目录保持补进原完整正例，没有增加独立测试框架。

### Reviewer 的最终 r2 安装定向实证

使用 r2 安装解释器 `-I`，只把 **r2 snapshot 的 tests 目录** 加入模块搜索路径以复用 fixture，确认生产 `ergora.retrospectives` 实际来自 r2 非 editable 安装；没有导入源码包、安装、运行重型 suite 或调用模型。以下八项均由 reviewer 在私有临时目录实际执行：

- 完整正候选经原 check／export 后仍含 `skills/target-guide/references/empty`；receipt 的候选目录包含它，原 manifest 身份与含目录 baseline 身份分别相符。
- NUL 与非 UTF-8 两种候选 Skill 支持文件分别被拒绝，未导出候选。
- 目录清单倒序、删除父目录但保留空后代、`../escaped` 越界目录、修改目录但不更新组合 digest，四种冻结输入分别被拒绝。前两种反例重算了组合 digest 并同步 proposal，因此证明 strict inventory 生效，不只是被旧 digest 提前拦住。
- 通过未受限制的原通用库成功发布一个含 NUL 支持文件的合法 workflow／完整 manifest，再自行构造符合新文件与目录身份的普通叶 input；其 `candidate:null` 仍在 offline checker 被 `Retrospective baselines require UTF-8 text without NUL` 拒绝，证明补加的冻结 baseline 门禁实际可达。

直接读取修后开发原 stdout 为 **16 passed／132 deselected／29.58 秒**，runner wall time **30.335953750181943 秒**；该运行早于最后补加的冻结 checker 门禁，后者由上面的安装实证覆盖，不倒写开发结果。

### r2 包身份与原件保持

Reviewer 独立读取 wheel 全部成员并逐份比较 **602 份产品：当前源码＝r2 source snapshot＝wheel＝installed**，无重复 ZIP 成员。wheel SHA256 为 **`8aa28152a77e9f4e3aa6a3843c3d3b1f12a5350fccd06d81340f283dc321f58c`**。两份 RECORD 的 **610／615 行**逐行核原大小与 SHA256，包含安装生成文件，没有只信 package-identity 摘要。

从固定基线 `git ls-tree` 取得 **283 份 reference** 原 Git blob，逐份按 Git blob 算法重算当前内容并核当前执行位；其 bytes 又与 r2 snapshot／installed 相同。原 **178 份既有 preset 定义／资源 blob** 同样与基线完全相同；catalog 的原 27 个入口保持，仅追加第 28 个。本节的包身份通过不替代尚在执行或待读取的完整运行验收。

最终原 native／模型／自身模板及 suite 证据将另节核对。特别是实际调用器的 fixture、生产安装件、目标 manifest 与结果须分别记录精确身份：复用不同 fixture 产生的目标不能被冒称含原空目录；私有调用器失败也不能改写为产品通过或直接当作源码缺陷。

## 最终本地终核：最终 r2 原件与完整证据

本节由原 fresh-context reviewer 同片追加，保留全部初审、修正与失败历史。终核时 HEAD 仍为 `0f01fdd9736fc456cf1cdcc8d77e64dac916e8a0`，尚未发布本片。**最终本地需求／行为轴 approve；结构／维护成本轴 approve；R1、R2 已闭合，开放 finding 0／0。** 本结论覆盖当前完整产品、测试、实际旅程及下列原件；普通发布、完整远端 Ref、本片自己的必要 CI 和相应固定发布补核仍待，不借前片 CI 背书。

### 最终身份、原 suite 和静态范围

直接核 `current-identity-r1.json` 的全部 12 份产品／测试：当前 bytes／SHA256 与前节 r2 身份、r2 source snapshot 及实际 Git index 中 staged blob 均相同。前节独立全包／两 RECORD 的 **602／610／615** 核验继续有效；最终 wheel SHA 保持 `8aa28152a77e9f4e3aa6a3843c3d3b1f12a5350fccd06d81340f283dc321f58c`。再次逐份核 **283 个原 Git reference blob**，当前／snapshot／wheel／installed 四处原字节及执行位全部相同，未改原参考实现。

直接读最终 `install-r2/regression-r1/result.json`、原 runner 与 process stdout／stderr：r2 非 editable 安装解释器以 `-I -m pytest` 运行原七 suite，cwd 为 r2 source snapshot，并移除 PYTHONPATH。七份测试文件均逐字等于当前文件；原 stdout 逐条状态为 **204 PASSED／6 SKIPPED**，无 FAILED／ERROR，pytest **250.00 秒**，原 monitor **251.46630791993812 秒**，status succeeded／returncode 0，原 stderr 空。六个 skip 均为 Linux 上的原 Windows 平台项，不称原生 Windows 运行通过。

已读实际 `staged-static-r1.json`，并由 reviewer 再运行 `git diff --cached --check`，exit 0。全部新增 Agent／workflow／schema 产品均已入实际 index，与上文 12 份完整产品／测试范围相符，克服 tracked-only 检查不覆盖新增文件的问题。该静态结果只代表实际检查时的 staged 内容，之后追加的审查／状态记账仍由发布前最终暂存检查覆盖。

[最终公开 evidence](evidence/2026-11-14-retrospective-workflow-candidates.json) 的 **411 份原引用**已全部直接读取：路径唯一，逐份 bytes／SHA256 相同，无缺失或差异；包含旧结果、调用器失败、最终包／suite、模型及自身模板完整输入／stdin／原回复和收尾。没有把“文件存在”替代为逐份身份核验。

### 最终实际 CLI：空目录、双身份与原导入选择

直接读 `native-r3/commands.json` 及全部 **11 对原 stdout／stderr**，逐项核命令使用最终 r2 安装解释器 `-I -B -m ergora`、exit、stdout／stderr SHA。成功与明确候选错绑、既有目标和同版本冲突的 exit 均相符；拒绝输出未混入成功 JSON。

原目标完整 manifest、作者冻结 input、check、export receipt 与导出树已交叉核验：全部 baseline 文件原 bytes／执行位、原完整目录与组合摘要相同。原 manifest 文件身份为 `55ffd812908240781b92667435fbf3c47180ed45ad50950fe84c6d6fc569276b`，含目录 baseline 身份为 `97613672c669ad001762ca562d6d098d04088280c331c266762a2be8936297a8`；两者明确区分。候选为 `17edeb4b1b1c734f8a0e1db8ee100d76ce1b2c366ac2ccef9303ff79285c9454`，导出全树、原 preview 的 accepted_candidate 及 receipt 的 candidate directories 完全相同。

原 `skills/target-guide/references/empty` 在完整目标和导出包均存在；候选 instructions 与模型格式的合成 proposal base64 解码后原字节相同，保留 **300 个 CRLF**。原完整 check／import／repeat-import 的 digest 相同；同版本不同内容被原库拒绝，原候选未被覆盖。新 manifest 使用候选根／原 grant，并包含新增依赖边；重新选原版本的 manifest 与原完整 composition 相同。原全部旧定义、源包、原 input／result 和 fixture Git 状态均保持，离线 unused-state 不存在。此正候选明确来自合成合同 fixture，不称真实模型生成了改进或证明效果。

另直接核保留的 `native-r2` 原 check／export：其选中 baseline 的目录清单本来就不含该 empty，receipt 也无此目录；实际私有脚本确从 r1 snapshot tests 导入旧 fixture。该调用器在新增 empty 断言失败，不能归因为最终产品丢失已选目录。`native-r3` 修正为 r2 snapshot fixture，未改变最终产品，以上原件独立证明 R2 的实际 CLI 修复。该失败记录与首个 suite 调用器漏传参数、r1 旧包／模型／自身结果均继续保留原身份。

### 最终真实 Codex／Claude：完整祖先、前驱与原回复

直接读最终 `models-r2/commands.json` 及 **7 对原 stdout／stderr**，命令均使用最终 r2 安装产品；重用旧 fixture 的实际路径没有把生产包切回 r1。两次原 run 均 succeeded／returncode 0 并有 finished：

|角色／实际后端|run|实际 CLI 秒数|完整 prompt 字节|input digest|
|---|---|---:|---:|---|
|作者／Codex|`2ed7ec90e1cb4773a51a8e1f9f5c091a`|21.73237976571545|101883|`7f2ab7e1cd074f117298224d1fef16989f2ffe581e22e16913e3cc95e23fbcf0`|
|审查／Claude|`3b80cc675af042ebbe6969830de3c76a`|23.055363167077303|109689|`4b141b4488f91c492c66901e97e2b0ee8121680a9cdff2880e144284488b1d49`|

对两份原 input 重新使用只读完整 verifier：prompt SHA、input digest 和原 run 相符，完整 prompt 逐字等于实际 native stdin；每叶均完整包含原三个祖先／自身资源，write／shell／network 为空。review task 字节恰等于完整 `check-author.stdout`，该完整 checked JSON 也逐字存在于 review prompt；其中 request 恰为原作者冻结 task，agent_result 恰为作者原结果。原 handoff 完整选择经原 owner 再核与冻结 evidence 相同；原 target 文件／执行位／目录全部保持，原库定义、fixture Git 与离线 State 缺席状态相符。

已读两份实际原回复，并核 Codex native stdout 的最终 agent_message／Claude structured_output 与保存结果逐项相同。作者返回 **candidate:null**，明确失败机制、成本、比较与因果证据不足，保留并行分支及原 gate；Claude **approve**，明确仅审阅提案，不授权 import／manifest 选择／执行。没有把 null 与 approve 冒称模型正候选或质量评价。实际模型目标由其原 r1 fixture 构造，不含 empty；新 baseline 含目录组合身份与原 r2 request／checker 确实生效，但模型旅程不证明空目录场景。该场景由最终安装 suite、实际 native-r3 及独立安装探针负责。

作者 CLI stderr 为空，实际 Codex native stderr 另有 **141B 本地日志 SQLite quick-check corruption 提示**；原件已保留。该 run 仍成功并产出上述完整原结果，不把 native stderr 称为空，也不把本地 Codex 日志库提示冒称 Ergora 数据库错误。Claude native stderr 为空。

### 最终自身原结构模板与收尾

直接核 `self-review-r2-codex` 原根 `ergora-structure-review 1.0.0`，digest `996c55d50e307943ae5dc77b2c929baea0d996a924fa66ab8c86a41e813c40c9`；run `7d988a17a2b74afe9526fde53fda5e14` 的 requested Claude／实际显式选择 Codex 及原因与原 summary 一致，沿此前保留的两次 Claude 大输入 360 秒超时使用既有授权。本片没有制造新的 Claude 大输入失败，小提案审查仍由 Claude 实际运行。

从完整原 task 按文件标记及原 byte count 取出 **14 文件／207574B**，逐份核 SHA；其中 **12 份产品／测试恰覆盖当前完整产品／测试差异且逐字相同**。两份计划／交付为调用时的完整原字节，后续状态追加不冒称模型已审。完整 **213062B prompt＝实际 stdin**，原 task 与三个祖先／自身资源均完整包含；input digest `5c22829587dd3296807733256b7b3bfb4ca1df39fb8053fcc7e5ad5c42e26b5e`、prompt SHA `ed34c86ec299ddece42421216646adeedeaf1e60e895a6c9f795e6dc9e5621d9` 均相符。原 native 最终回复＝原 result＝保存的 original-result，result SHA `a89856eefb2c9060ab02162c4928395f7bd5d993159a47aab841af65efb5fd22`；**35.499301604926586 秒／approve**，native stderr 空。原回复明确只做 supplied-file 静态审查、未执行测试或核未提供的 owner，不替代本独立两轴审查，也不证明效果。

已读收尾记录并由 reviewer 再核：可访问 proc cwd 下无本片残留进程，**11 个不可读 proc 项明确未验**；实际 suite／模型／私有调用器均有相应终态。本片没有服务、端口或浏览器旅程，不作 OS 隔离主张。最终本地证据已闭合；发布与本片自己的必要 CI、完整 Forge、F10d／F9d／G1、原生 Windows 模型及真实 workload／GPU／质量／性能仍按各自范围继续。
