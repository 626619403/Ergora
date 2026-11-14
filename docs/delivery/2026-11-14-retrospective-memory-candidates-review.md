# F10c2b1：记忆复盘候选独立评审

日期：2026-11-14。Reviewer 为本片新建的 fresh-context 独立 agent；未接收实现会话或预设结论。项目与文档根均为 Ergora。先读 `AGENTS.md`、[原始合同](../plans/2026-11-14-retrospective-memory-candidates.md)、maintainable-project-delivery／独立评审 brief、codebase-design、review-pr 与本地 AIHERO 索引，再读实际完整 tracked diff、全部 untracked 产品／测试／合同和必要原调用者，最后读[作者交付](2026-11-14-retrospective-memory-candidates.md)。AI Hero 的双轴及职责／冗余检查按本次独立评审职责使用，没有再委派实现或修改产品。

精确基线为 `c4aa7acb555a5d55fec7e7a483544834e8afe44f`；初审与修复复核时 HEAD 仍为该提交，分支为 `refactor/architecture-foundations`，本片为未提交工作树。前片 Skill adoption 四份发布／CI 状态文件的差异已读作范围核对，其运行与结论不继承为本片验收。

## 本轮结论与范围

**需求轴：所审源码与 r2 实际保存旅程 approve。结构／成本轴：所审范围 approve。** 确认一项 P2（R1），已在原 CLI owner 修正并以实际 r2 CLI 原件闭合，开放代码 finding 为 0／0。最终包的全部产品／两 RECORD／283 完整身份、最终安装 suite、自身审查模板、实际模型完整 stdin／前驱、公开原引用与收尾尚待最终证据补核；本节不称本片最终交付、发布或 CI 已通过。

产品范围：`src/ergora/retrospectives.py`、`cli.py`、`data/presets/presets.json`、新 `data/schemas/retrospective-memory-proposal-v1.json`、新 `ergora-memory-retrospective-author`／`reviewer` 两个完整 Agent 目录及 `ergora-memory-retrospective` 完整 workflow／Skill 目录。另核 `tests/test_memory.py`、README、USAGE、current architecture、PLAN、活动片合同与交付。必要邻接 owner 包括原 `memory`、`handoff`、`workflow_definitions`、`asset_trees`、`agent_runs`、`agents`、`agent_backends`、`definition_bundles` 与原 Skill retrospective 测试。

2026-11-14 03:55:41 UTC 捕获的源码／测试身份如下；其中 CLI 与测试已经包含 R1 修复：

|文件|字节|SHA256|
|---|---:|---|
|`src/ergora/retrospectives.py`|20952|`f735fa10290b8d8d6a938570b8bf2bfe0e6bf47a05f17d4c7cf7e2bea4df17c4`|
|`src/ergora/cli.py`|82559|`2921e4661d0fba4a4710fb382cce376fe2983721577d3d4a4a286fdaf4e3b794`|
|`src/ergora/data/presets/presets.json`|17385|`89fcc560286b5db8f0e96dbc930376579146ef29ecaf8f12df58e9662a0817ca`|
|`src/ergora/data/schemas/retrospective-memory-proposal-v1.json`|3048|`d5d0d0ba25ca128fd5571ee4d92febe4da291bc87ea70e389c722341a3607733`|
|`tests/test_memory.py`|21074|`42b495ddbba4834b753c1f02224975dc8a9a68eea9143ed588c3e250a93d55fd`|

## R1：原保存 CLI 改变已选正文（P2，已闭合）

位置：[原 memory CLI 保存分支](../../src/ergora/cli.py) 第 1128 行，新集成路径见 [USAGE](../USAGE.md) 第 937 行和[现有正例](../../tests/test_memory.py) 第 229 行。原分支使用 `Path.read_text(encoding='utf-8-sig')`，通用换行会把 CRLF／孤立 CR 改成 LF，也会丢弃开头语义 U+FEFF。新 `export-memory` 虽然输出完整候选字节并给出 `text_sha256`，按手册执行原 `memory save --text` 后的正文却偏离已选 `save.text`。原新测试直接调用 `memory.save(**checked['save'])`，未跨过此文件读取接缝。

Reviewer 直接读取 `.ergora/checks/retrospective-memory-candidates/native-r1/` 原件：前六个 CLI 包括 `correct-save` 均 exit 0，但候选文件有 501 个 CRLF，保存原回复正文有 0 个，UTF-8 字节不相等。候选 SHA 为 `0fcb6ce8501cbbe51c6dd0538756e358f8555935b6926f113391eee353b57360`，原 CLI 同式读取后正文重编码 SHA 为 `bc49310ce8bb5cb5d028dee5b289b99f4ec217cbfee454f6bd246f8372098fcc`。这证明保存已成功但候选身份发生静默变化；不是只检查合成脚本的断言或作者结论。

最小修正已落在原 CLI：`read_bytes().decode('utf-8')`，沿原 `memory.save` 存储、revision、expiry 与错误处理，不引入候选规范化或新旋钮。现有创建／更正两个正例改走真实 `cli.main` 保存，文本含开头 U+FEFF 与 CRLF；手册明确人工 BOM 文件现在也保留该字符。该读取只影响原 CLI 文件输入，其他 API／Web 的字符串调用及原 memory 算法均未改。

Reviewer 另用纯内存实际 `cli.main` 捕获实参，mock State／save 而不落状态：U+FEFF、CRLF、孤立 CR、LF 均原字节往返，source／ID／expected revision 不变，expiry 参数仍省略。

又直接读取 `native-r2/commands.json` 及全部 **16 对 stdout／stderr**，逐份核原 SHA；成功与选定摘要／既有目标／陈旧修订拒绝的 exit 均相符。两种候选的 checked `save.text`、导出文件原字节、receipt `text_sha256`、原 CLI 保存回复文本均相等，均保留 U+FEFF 与 501 个 CRLF；来源在 checked／receipt／保存回复间一致。更正 revision 2 保留原 expiry，history 为原 revision 1 与保存 revision 2，restore revision 3 恢复原正文和有效期；新建 revision 1 无 expiry；离线 unused-state 不存在。直接核 r2 wheel SHA `6832763f8f07ccb1c32d130e14e5da4c85dd8ce31bbc9aa607e6b00232e49b9a`，CLI 为 **当前源码＝r2 source snapshot＝wheel＝installed**。因此 R1 源码修正及实际安装集成已闭合。r1 失败原件仍保留，不倒写成功。

## 需求轴实证

- `prepare_memory` 复用原 `handoff.evidence`：先验证原包完整字节与选中完整文本，再由 `memory.catalog` 观察 canonical 当前记录及有效性。精确 ID／revision 与有效性检查在来源 I/O 后；null／revision 0 明确表示新建。冻结原完整记录、来源、expiry、观察时间和项目绑定摘要，经原 `prepare_input_from_manifest` 编译，不另截断材料。
- 模型 schema 只容许正文、假设、适用性与验证计划，允许 null；100000 字符沿原 save 合同。来源由固定 packet SHA／selection SHA 派生，ID／expected revision 来自完整基线，生成器不传 expiry。原 revision／删除冲突与保存时 expiry 保留仍由原 memory owner 处理。
- `_read_proposal` 保留原完整 input 检查、一次最多 8 MiB 原结果读取、原字节 SHA 与普通 Agent 封套；`_check_sources` 共用完整选择身份及逐项引用检查。记忆基线／项目和完整 save digest 仍由 `_checked_memory` 本地处理；check／export 不创建 State、不重新取当前来源、不评价真实效果。导出复用原 no-replace 发布器，原输入内部／既有目标拒绝与私有 staging 清理保持。
- 新标准 preset 为只读 Codex 作者／Claude 审查，父子权限无 write／shell／network。原编译器累加祖先完整资源，原 `compile_input` 检查完整 task＋prompt 容量；静态端口没有被自动执行。后端仍通过现有 `AgentBackend` 抽象、原本地注册映射及 `agent_runs` override 选择，没有在新 orchestrator 里按具体后端另分路径。
- 使用原 bundle 检查器读取新三个完整 bundle，author digest 为 `cb30b5b9f0afb4f88470f375d5b47e4927b14b408270d93d45ec3901c735a272`，reviewer 为 `bae971984fb1f9ef2ec55055b1b82a1d5d0595d3c133e691402cba619db46170`，workflow 为 `0159aa511ade1499ea580f142cd0aa308ce78b6ee7bbf6dc70610b0093e6e6c5`，资源引用均自洽。直接逐份比较原基线中的 **171 份既有 preset 定义／资源文件**，全部字节相同；目录 catalog 只追加新 preset。
- 纯内存验证实际 frozen memory task、proposal 和原 `_check_sources`；100000／100001 字符分别接受／拒绝。`deepcopy` 后旧 Skill evidence required 仍为原 `sha256/artifacts`，只有记忆请求追加 `packet_sha256`，没有污染旧请求 schema。

## 结构、必要分支与测试成本轴

新增公共入口只有实际 CLI 消费者，留在原 retrospective owner 合理。`_read_proposal`、`_check_sources`、`_export_location` 均为该 owner 内两个实际目标调用的 cohesive private algorithm；它们集中有界读取、来源关联及发布位置语义。`_checked_memory` 同时服务 check／export，导出使用同次检查的内存候选，避免二次读结果。不以同文件调用或测试伪称跨文件复用，也没有为未来目标造 registry／插件框架、透传配置层或第二记忆状态机。

新分支分别保护外部原结果／schema、当前基线失效或修订变化、误绑来源／项目／引用、null、明确选定候选、既有目标与冻结输入污染；检查由拥有该不变量的原 owner 或 target 本地负责。`revision != 0` 保护显式新建的真实误用；未发现与本片无关的参数防卫。原 Linux renameat2／Windows no-replace 支持矩阵没有被扩大为其他平台可用。

新增测试集中于原 `test_memory.py`，复用原 handoff fixture 与真实 preset／manifest owner。来源 I/O 后 revision／deleted／expired 三种可达变化、模型来源／expiry 越权、正文上限、离线无 State、摘要／导出污染以及两个真实 CLI 保存正例保护不同合同风险。原 memory 的 expiry／restore／ReMe 状态机未复制；正例里的原 save／restore 联合断言验证生成的参数是否能交给原 owner。R1 发现后将原正例改穿公开保存接缝，替换原直接调用，未追加平行测试框架。当前未确认应删除的冗余 guard／test 或把可配置行为钉死的断言。

已直接读开发 r1 原 stdout：25 passed／3 failed，三项均是候选 oneOf 外部错误文案与测试内部文案假设不同，产品已拒绝。开发 r2 原 stdout 为 28 passed／22 deselected／27.88s；此运行早于 R1 CLI／测试修复，只证明当时源码，不继承为最终 r2 包全验。其 28.2408 秒 runner wall time 与 pytest 27.88 秒分别记录，不混作同一计时。当前新增路径不是训练／并发热路径；没有新重试、轮询或模型请求，保留原 bounded I/O 与容量限制。未以静态检查宣称质量、吞吐或业务收益。

## 检查边界与剩余验收

本 reviewer 仅做源码／原件读取、廉价纯内存 schema／CLI 捕获探针、bundle／哈希核验、`git diff --check` 和写本报告；未联网、安装、运行 suite／模型、改产品或提交。`git diff --check BASELINE` 通过。

本轮已关闭 R1。最终补核仍需直接核全部 r2 安装产品／两 RECORD／283、最终七 suite、原自身结构模板与真实模型完整输入／前驱／回复、公开 evidence 原引用和收尾。作者报告的 r1 模型 null／approve 与 r2 只读复查应保留其各自实际安装身份，不能称由 r2 重跑；合成正候选也不证明真实模型生成改进。普通发布、固定 Git／full Ref、本片自己的 CI 及原 reviewer 补核另验；Windows 本地未运行，完整 Forge、流程候选、F10d、F9d／G1、GPU／真实业务与真实质量／性能继续保留原范围。

## 最终本地补核（r2）

本节由同一 reviewer 直接读取最终原件后追加，仅补核同片，未修改前述初审和失败记录。补核时 HEAD 仍为精确基线 `c4aa7acb555a5d55fec7e7a483544834e8afe44f`，产品及测试与上节所列修后身份相同。新增的总计划状态差异只记本片进度、前片 CI 依赖和未验范围，没有后续产品或新行为；后续片不在本报告范围。

**最终本地需求轴 approve；结构／成本轴 approve；确认 R1 已闭合，开放 finding 0／0。** 以下原件补齐上节列出的本地待验项；普通发布、固定提交／完整远端 Ref、本片自己的 CI 与相应独立补核仍待，本节不预批或借用前片 CI。

### 最终包、测试与原件身份

直接读取最终 r2 wheel 全部成员，对全部 **594 份产品**逐份比较 **当前源码＝r2 source snapshot＝wheel＝installed**。wheel SHA256 保持 `6832763f8f07ccb1c32d130e14e5da4c85dd8ce31bbc9aa607e6b00232e49b9a`；wheel 没有重复成员。两份 RECORD 的 **602／607 行**已直接逐行核内容大小与 SHA256，包括安装生成条目。原七 suite 与两份核心源码共九项也分别核当前文件＝最终快照，其原 SHA 与公开 identity 相同。

原 reference manifest 的 **283 份**已逐份核安装内容；又从精确基线 `git ls-tree` 读取全部原 blob 身份，独立按 Git blob 算法重算当前内容，且当前源码、快照、wheel ZIP external mode、安装件的执行位均与原 Git mode 相同。本片 283 份原件均为 `100644`，没有内容或执行位漂移。原有 preset 的完整资源身份继续保持。

直接读最终 `install-r2/regression-r1/result.json`、原 process stdout／stderr 与 runner：以 r2 非 editable 安装解释器 `-I -m pytest`，清除 PYTHONPATH，cwd 为最终 source snapshot；原七 suite 名单与公开记录一致。逐条原 stdout 状态确为 **188 PASSED／6 SKIPPED**，无 FAILED／ERROR；pytest **215.43 秒**，原 monitor **216.94233832415193 秒**，status succeeded／returncode 0，原 stderr 空。六个 skip 均为原 `test_windows.py` 的平台项，没有把它们称为本地 Windows 运行通过。r1 旧包的 188／6／216.27 秒与其 CLI 失败继续保留各自身份，不替代最终 r2 运行。

[最终公开 evidence](evidence/2026-11-14-retrospective-memory-candidates.json) 的 **259 份引用**已全部直接读取：路径唯一，bytes／SHA256 均相同，无缺失或差异。包含原开发 oneOf 文案失败、r1 实际保存偏离、旧／新包各自安装结果、r2 实际 CLI、模型／自身模板完整 input／stdin／原回复及摘要。初审已经直接核过的 r2 16CLI 原件也在该完整核验内，源码／快照／wheel／安装同一身份使 R1 的修复与实际保存闭合继续成立。

### 真实模型与最终 r2 只读复查

直接读原 `models-r1/commands.json` 及七组 stdout／stderr，exit 与原 SHA 全相符。两次模型调用确在原 r1 安装件执行：

|角色／后端|原 run|实际 CLI 秒数|完整 prompt 字节|input digest|
|---|---|---:|---:|---|
|作者／Codex|`9f65aeeb24c64043b54fa180df3e7795`|19.745336703024805|32558|`e7ffad046e49544daeb09c2c7f5bf68e5c2fdfee0510eb2b00114139a9fc6f68`|
|审查／Claude|`46b7b5589cdb48ca973b6f88d022ff8a`|20.76342411711812|38296|`e07d15b4ad8f312ee2a14991b820fa1efb064762e861dcf3b4934b52310201b7`|

对两次原输入再次使用原只读完整 bundle verifier：完整冻结 prompt＝实际 native stdin；每叶均包含全部三个祖先／自身资源，且无 write／shell／network 权限。审查 task 字节恰等于完整原 `check-author.stdout`，该完整 checked JSON 也逐字在审查 prompt 内；它的 request 恰为原作者冻结 task，agent_result 恰为原作者原结果。原包重新只读验证所得完整 handoff selection＝冻结 evidence，完整 canonical baseline＝`records-before`。直接以 SQLite 只读 immutable 连接检查 canonical 原记录未变，fixture Git 状态、原包与离线 unused-state 缺席状态也相符。

已读两份实际原回复，并将原 native stdout 的最终 Codex agent_message／Claude structured_output 与原 result 逐项比较。作者返回 **candidate:null**，保留失败与未记录成本；Claude 为 **approve**，明确只审阅提案、不授权保存。两次原 run 均 succeeded／returncode 0 并有 finished。作者原 stderr 有一条 **141B 的本地 Codex 日志库 quick-check 提示**，原件已保留；不把它说成 stderr 为空，也不把该次成功产出改称模型调用失败。

独立比较 r1／r2 wheel 的全部 594 产品：唯一变化精确为 `ergora/cli.py` 原 memory save 的 `read_text(encoding='utf-8-sig')` → `read_bytes().decode('utf-8')`，其余 **593 份**逐字相同，retrospective 生产／检查与后端未改。最终 r2 对原作者结果的实际离线 check stdout 与原 r1 checked stdout **逐字相同**，SHA256 为 `bc086eac169891610cf03b4c795dbdbe578063e707e6ea42a8e881e2eed8b32e`；reviewer 另以当前原 checker 作纯只读检查，所得完整对象也相同。因此保留原两次真实模型证据的实际 r1 身份合理，无需重复模型请求；本节没有声称它们由 r2 重跑。正候选仍仅来自 r2 合成 CLI 合同旅程。

### 原自身结构模板及成本、收尾

最终 r2 自身审查的原根为 `ergora-structure-review 1.0.0`，digest `996c55d50e307943ae5dc77b2c929baea0d996a924fa66ab8c86a41e813c40c9`。原 run `5dba301b185e4c71be0d44c437b2d154` 记录 requested Claude、实际显式选择 Codex，原 reason 与 admission／run／summary 相同：依据前两片保留的 Claude 大输入 360 秒超时采用既有授权选型。本片未制造一次新的 Claude 大输入失败；实际小提案仍由 Claude 审查。

直接核原 packet index 的 **14 个完整文件／157589B**：从原冻结 task 按文件标记和原 byte count 取出每份完整内容，逐份 SHA 相符；全部 12 个产品／测试文件恰覆盖当前全部产品／测试差异，并与最终当前文件逐字相同。两份计划／交付按调用当时原字节保留，之后仅追加状态，不冒称模型审过未来结果。完整 **162920B prompt＝实际 stdin**，task 和全部三个祖先／自身资源完整包含；input digest `230d8c844c26031193c7913ae4570e15aa5d0bed80d34915124ad19bb0ea58a4`、prompt SHA `0871876c6e8d8272e1d52a68c864f330b58ac14a2ddb9ffc485826aee3bfc2b2` 均相同。实际 native stdout 最终回复＝原 result＝保存的 original-result，result SHA `2e59b6e31c320ef1cf945f81628bca90fd282b898bdd22937f3551b51f6708d3`；**41.792663663160056 秒／approve**。原回复明确仅为完整 supplied-file 静态审查，未独立执行测试或证明质量；本报告的独立结论没有由它替代。

本片最终 r2 suite 重跑针对已经确认的全局 CLI 读取修正，且原 suite 保护原 owner／preset／兼容合同；未添加第二状态机或平行测试框架。真实模型不因无关的保存读取修复重复调用；新私有共享算法仍留原 owner，没有新缓存、轮询或调度层。没有新增结构／成本 finding。

两次安装 monitor 原记录均为终态；三次模型／自身模板原 run 均为 succeeded／finished，未见本片在途调用。`cleanup-r1.json` 记录可访问 proc cwd 中无本片进程，11 条不可读；reviewer 另直接重查 `/proc`，同样无本片 cwd，**11 条不可读**。实际 CLI／模型／自身模板脚本未启动服务／端口／浏览器；suite 内既有 HTTP fixture 的短生命周期监听与 finally 清理属于测试自身范围。此范围不证明不可读进程或系统全部后台活动，不作 OS 隔离保证。

本次仍仅直接读取、原只读 verifier／checker、哈希／协议比对和追加本报告；没有联网、安装、重跑 suite／模型、改产品或提交。文档链接及 `git diff --check BASELINE` 通过。此前初审的 R1 是本片唯一确认代码问题，已修复；**最终本地两轴 approve，开放 0／0**。原记忆明确写入／expiry／revision 权威和来源认证／效果限制保持；发布与本片 CI、原生 Windows、完整 Forge、流程候选、F10d、F9d／G1、真实业务／GPU／质量／性能仍按各自范围后验。

## 固定普通发布补核

固定候选为 **`0f01fdd9736fc456cf1cdcc8d77e64dac916e8a0`**，唯一父提交精确为本片原基线 `c4aa7acb555a5d55fec7e7a483544834e8afe44f`。补核开始时工作树只有七份发布状态文档变化，没有再改产品／测试，也没有后片产品。此节仅核本片固定发布及所承载 CI 修正的身份／依赖范围；后片不在审查范围。

从固定 Git object 直接读取全部 **30 个变更 blob**，路径集合与 `static-final-r1.json` 完整清单相同，每份 bytes／SHA256 全相符。固定本报告的原字节为 **19410B**／SHA256 `0e5e8271dd5473c11bf2708b04d3a08ef243515b08eceb2b496ad7e31e525998`，恰为本 reviewer 最终本地补核版本，未在验收后替换。又直接读取固定 Git tree 的全部 **594 个产品 blob**，逐份核为 **fixed Git＝current＝r2 source snapshot＝wheel＝installed**，wheel SHA 保持 `6832763f8f07ccb1c32d130e14e5da4c85dd8ce31bbc9aa607e6b00232e49b9a`。原九项核心源码／七 suite 文件也与固定 Git、当前文件、最终快照逐字相同。此前直接核过的两 RECORD602／607、283原内容／执行位、188／6、16CLI与模型／自身模板原件因此继续绑定此精确候选，没有将旧 r1 安装结果冒充最终发布产品。

直接读原 `commit-r1.json`／`push-r1.json`／`ref-r1.json`：三份 exit 均为 0，candidate 均为上述完整 SHA。普通 push 原 argv 精确为 `git push origin HEAD:refs/heads/refactor/architecture-foundations`，无 force／main 目标。保存的完整 Ref stdout 精确为 `0f01fdd9736fc456cf1cdcc8d77e64dac916e8a0\trefs/heads/refactor/architecture-foundations\n`，stderr 空。本 reviewer 核的是已保存的原提交／push／Ref 回执，未重新联网。

固定记忆 evidence 的 **259** 项与发布后工作树前 259 项逐项相同，仅追加 static-final／commit／push／Ref 四份回执成为 **263** 项；已全部重新直接读取 bytes／SHA，无缺失、重复路径或差异。独立 CI 预算 evidence 也保持固定 **23**／发布后 **27** 的原列表前缀及相同四回执追加关系，27 项原 bytes／SHA 均直接核过。两个 evidence 除 publication／implementation 状态与四引用追加外的所有字段相同，包括记忆原 `publication_dependency_adjustment`，没有追加运行成功或效果主张。七份发布后状态文档只记实际普通发布、完整 Ref、原引用数量及新候选 CI 待验状态。

共同候选里的 `.github/workflows/portability.yml` SHA256 为 `4a23020b277de1fa3d07db42918314127a013e01cad8ebf0cd9e020109774b64`，与独立 CI reviewer 已审身份完全相同；固定该 reviewer 报告 SHA 为 `63faa9219c14897e34c48acac8476ed854cca1ac50ff44b2c60c703234a9f265`。直接比较原基线／固定候选的完整 workflow，恰为 native timeout 一行 `20` → `${{ matrix.os == 'windows-latest' && 30 || 20 }}`；原分组 JSON、CI runner 与 Windows installer 三份入口逐字保持。该独立小片的架构／预算结论归其[原 reviewer](2026-11-14-windows-ci-budget-review.md)，本节只确认已审修正准确进入固定候选，没有替它重作独立 CI 审查或预批真实 GitHub 表达式／30分钟充分性。

已读前片原 reviewer 的终态补核及具体 CI 计划：原 `c4aa7ac` 自己的 CI43553150941 是 **Cancelled，29／30 success**，Windows installer 被原 20 分钟总 job 上限截断，未称该候选全部 CI 成功。记忆 publication dependency 的调整限定为：保留原取消及其原 reviewer 原因核查，将已独立本地验收的记忆产品与已独立审过的一行预算修正一并普通发布，由**新完整 SHA 自己的原八 job／30 必要步骤全部成功及原 reviewer 终核**关闭验收。它改变承载修正的发布候选和先后关系，不减少测试／安装／上传，也不借用前片29项抵扣新检查；该范围与所审合同保持一致。

固定差异最后另跑 `git diff --check c4aa7ac...` 得到 exit 2：新 author／reviewer 两份 `instructions.md` 第1行各有一句末尾空格。这是此前文件尚未跟踪时该命令未覆盖的范围；此前记录的 diff-check 通过只适用于当时已跟踪差异，不能提升为完整30blob静态通过，本节纠正该范围。两处空白不改变所核资源身份或运行结论，不构成新增需求／结构 finding；工具项如实保留，没有改产品或把失败回执改为成功。

作者明确采用非阻塞样式项处置：保留已发布固定源、资源摘要、Agent1.0.0、模型和包身份，不为纯行尾空白修改同一不可变 ID／version 或重跑模型／suite；后续两 Agent 有实质指令修订并发布新不可变版本时一并清理。该项归入作者发布工具的覆盖缺口，后续在暂存全部已审文件后使用 `git diff --cached --check`，新片编辑时也检查新增文件行尾；本节仅记录该处置，不称已经修复这两个固定 blob 的样式检查失败。

**本固定普通发布需求轴 approve；结构／成本轴 approve；开放需求／结构 finding 0／0，另有上述两处非行为空白工具项。** 最后所读公开记录已发现新候选自己的 CI43555532175，状态为 `in_progress`；本 reviewer 尚未获得其终态／CI原件补核，本节不将状态记账当真实 CI 验收，也没有将固定发布等同完整交付完成。R1修复、r1模型原身份、合成正候选、来源／当前有效性／质量限制及全部未验范围保持。此轮仅仅读取 Git／原件、内存哈希比对和追加本报告，未联网、重跑 suite／模型、安装、改产品或提交。

## 自己的 CI 终态补核

本节核固定候选 **`0f01fdd9736fc456cf1cdcc8d77e64dac916e8a0`** 自己的 [run43555532175](https://github.com/626619403/Ergora/actions/runs/43555532175)，官方终态为 **Success，八 job／30 必要步骤全部成功**。补核时 HEAD 仍为该固定提交，但工作树已含后继流程候选编辑；本节的产品身份比较只读取固定 Git 与原记忆候选 `install-r2/`，未审查或接受后片产品，也未使用后片新包／模型。前节关于当时 current 身份的记录仍按其原核验时点理解。

直接读取原官方 UI batch、run／job HTML 及回执，逐份核 HTTP200、精确请求／最终 URL、bytes 与 SHA256。终态 `ci-run-html-r6/page.html` 为 **213305B**，SHA256 `3b1b7637361d9360b15aa46c3a37fc7f3b95d0337b1b80b6bed376ba4581f75f`，回执时间 `2026-11-14T04:37:11.534111+00:00`；其完整 commit anchor 指向上述 SHA，原 Status 明确为 `Success`。`ci-job-batch-r1/body.json` 为 **2715B**／SHA256 `e48f596f233365fc192b92f951842ce8fbd9ec0474ec996631a35a64444a24ba`，官方列表 totalCount8／hasMore false；它与 `ci-ui-metadata-r1.json` 的八组 ID／name／href 逐项相同，原 metadata 的早期 in_progress 状态保持历史身份，没有倒写成终态。metadata 的 source／早期 run-summary SHA 也与对应原字节相同，早期 run 同样绑定完整提交。

从固定 workflow 和原 `linux-groups.json` 独立推导 plan、六个 Linux group 与 Windows all 的必要步骤，再用独立只读 HTMLParser 逐项读取各原 `check-step`。八个 job 与终态取样如下；每份 body 的原 SHA 均已直接核验：

|job|原 ID|HTML 取样|成功必要步骤|
|---|---:|---|---:|
|plan|132327423814|r2|1|
|Ubuntu 3.11 group 0|132327455134|r2|4|
|Ubuntu 3.11 group 1|132327455232|r2|4|
|Ubuntu 3.11 group 2|132327455189|r2|4|
|Ubuntu 3.11 group 3|132327455179|r2|4|
|Ubuntu 3.11 group 4|132327455120|r2|4|
|Ubuntu 3.11 group 5|132327455130|r2|4|
|Windows 3.12 group all|132327455188|r6|5|

plan 的 `Read explicit test groups`、每个 native job 的 build/install、packaged reference identity、application regression、upload，以及 Windows 额外的 PowerShell5.1 installer/upgrade，共 **1＋24＋5＝30** 项，全部 conclusion success、有开始／完成时间且 `data-job-completed` 存在。每项 log URL 都精确为 `/626619403/Ergora/commit/0f01fdd9736fc456cf1cdcc8d77e64dac916e8a0/checks/<该jobID>/logs/<该step编号>`，未用短 SHA 或别的 run 抵扣。独立重建的完整八 job／30 step 对象与原 `ci-observation-r6.json` **逐项相同**；未执行会写观察文件的作者 parser。

Windows 终态 HTML 为 **160112B**／SHA256 `db8f636ebb63ac7120785fbefac28e0e4307340c15ea61c80c7f069e91f6f493`。原时间显示 application regression 为 `04:14:14Z–04:33:38Z`，installer/upgrade 为 `04:33:38Z–04:34:38Z`，upload 为 `04:34:38Z–04:34:39Z`，三项均 success；从 HTML 首个 setup step 的 `04:13:25Z` 至上传完成经过 **21分14秒**。这次固定 workflow 的 Windows30／Linux20 预算让原 installer 完整执行并上传，原 `runner.os == 'Windows' && !cancelled()` 条件与原入口保持；不将单次成功推广为所有负载的30分钟充分性。CI预算小片的结构／预算结论仍归其[独立 reviewer](2026-11-14-windows-ci-budget-review.md)。

公开 memory evidence 的原 **263** 引用已全部重新直接读 bytes／SHA：固定提交原 **259** 项是逐项不变的前缀，其后仍仅为 static-final／commit／push／Ref 四回执；另外新增的 **68 个 CI 引用**也逐份直接核验。两集合各自路径唯一、互不相交，合计 **331** 份无缺失或哈希差异，早期在途观察与最终成功原件共同保留。再次读取固定30个变更 blob，全部与原 `static-final-r1.json` 清单相同；固定本报告原19410B／SHA256 `0e5e8271dd5473c11bf2708b04d3a08ef243515b08eceb2b496ad7e31e525998` 也保持。

又直接从固定 Git tree 批量读取全部 **594** 产品 blob，逐份核 **fixed Git＝原 memory r2 source snapshot＝原 memory r2 wheel＝原 memory r2 installed**，四者产品路径集合也完全相同。原 wheel SHA256 仍为 `6832763f8f07ccb1c32d130e14e5da4c85dd8ce31bbc9aa607e6b00232e49b9a`；两 RECORD 的 **602／607 行**内容／大小／SHA256 重新逐行核过，原 **283** reference 的内容、原基线 blob 身份及 snapshot／wheel／installed 执行位相同；九份核心源码／七 suite 文件固定 Git 与原快照及公开 SHA 也相同。本节没有比较后片正在编辑的当前源码，没有把后片产物接到本片身份上，也没有重跑原188／6或原模型。

另独立重核 `full-fixed-diff-style-r1.json` SHA256 `730943b80c2dde558f40770ea7e92a77d9c0fe493775f1f67a960f933522ce39`，并仅对原基线／固定提交重做原完整 `git diff --check`：exit **2**、stdout／stderr 与原回执逐字相同，仍是两 Agent `instructions.md` 第1行末尾空格。上节所记非阻塞样式处置及早期 tracked-only 覆盖缺口继续保留；CI成功未修复该静态失败，不称全部静态检查通过，也不修改既有不可变Agent1.0.0／包／模型身份。

原前片 evidence 与原 `ci-observation-r5.json` 仍保留 `c4aa7acb555a5d55fec7e7a483544834e8afe44f`／run43553150941 的 **Cancelled、29 success／唯一 installer cancelled**；本次直接核该观察原件 **13362B**／SHA256 `608a8f7112affd667bff9a1f01b704a98006e02f59f64be358c6271c40062b64`，八 job／30 step 的原结论未改。新成功只属于 `0f01fdd` 自己的八 job／30步骤，未借用旧29项；依赖调整要求的新完整候选 CI 门禁及本片原 reviewer 终核现已满足。

**本片固定发布及自己 CI 终核：需求轴 approve；结构／成本轴 approve；R1 已闭合，开放需求／结构 finding 0／0。** 两处非阻塞空白工具项仍按原处置保留。此处远端结论以已保存官方 HTML 的 job／step 状态和完整SHA链接为范围；没有下载 artifact archive 或完整远端测试日志，不据此声称远端 pytest 数量或远端 wheel 的逐字身份。原 r1 真实模型身份、r2只读复查、合成正候选及来源／当前有效性限制保持；原生 Windows 真实模型／完整 runtime、完整Forge、后续流程候选、F10d、F9d／G1、GPU／真实业务／质量／性能仍按各自范围另验。本轮仅直接读取 Git／原件、执行廉价内存哈希／HTML／RECORD 比对及固定diff-check，并追加本报告，未联网、安装、运行suite／模型、改产品或提交。
