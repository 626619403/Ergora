# F10c3a 独立需求／结构与成本审查

日期：2026-11-14。Reviewer：`/root/retrospective_skill_adoption_review`，本片新 fresh-context reviewer。先读[原始合同](../plans/2026-11-14-retrospective-skill-adoption.md)、`AGENTS.md` 和仓库审查规则，再读实际 diff／相邻 owner，最后读作者[交付](2026-11-14-retrospective-skill-adoption.md)。按 maintainable-project-delivery、codebase-design、review-pr 与仓库原结构审查模板核查。此 reviewer 仅写本报告，未联网、安装、运行 suite、改产品或提交。

## 本轮结论

**需求轴：源码及已到安装／CLI 原件范围 approve，确证 finding 0。结构／成本轴：同范围 approve，确证 finding 0。** 没有已证实的源码阻塞项；原 manifest 恢复直接回归、自身原模板及公开 evidence／收尾尚待补核，不能据此把整片标成最终交付完成。前片 CI43551217945 及其发布记账不构成本片验收。最终 r1 包与实际 CLI 补核详见末节。

## 精确范围

基线与本轮 HEAD 均为 `a60a8f68513a46ef7e6c18add0832f8bcee3eccc`，分支 `refactor/architecture-foundations`，审查对象为未提交工作树；已读完整 `git status --short --untracked-files=all`、`git diff BASELINE` 的产品／测试／文档差异及两份 untracked 原文。初始完整差异为：

- 产品：`src/ergora/retrospectives.py`、`asset_trees.py`、`workflow_definitions.py`、`cli.py`。
- 测试：`tests/test_skills_evaluation.py`、`tests/test_workflow_definitions.py`。
- 本片产品文档：`README.md`、`docs/USAGE.md`、`docs/architecture/current.md`；新增 `docs/plans/2026-11-14-retrospective-skill-adoption.md` 与 `docs/delivery/2026-11-14-retrospective-skill-adoption.md`。
- 其余 tracked：`docs/PLAN.md`、`docs/plans/2026-11-14-retrospective-skill-candidates.md`、`docs/delivery/2026-11-14-retrospective-skill-candidates.md`、其 `-review.md` 和 `docs/delivery/evidence/2026-11-14-retrospective-skill-candidates.json`。已分别读 diff：除 PLAN 的本片入口外，属于前片固定发布／CI 状态与原回执索引追加，没有本片产品改动；不继承其独立通过、包或模型身份。

本轮直接读取的六份源码／测试原字节身份如下；后续补核以这些身份是否保持为前提。

|路径|字节数|SHA256|
|---|---:|---|
|`src/ergora/retrospectives.py`|12472|`5cddd81422b0da332dc66c5a72ca3098fe141085df7714f7c7c678112a71f4f5`|
|`src/ergora/asset_trees.py`|3611|`8191c4000d02bdeafd016d7d1e15d7c357ad61b83baef84889ac0da178f93fe3`|
|`src/ergora/workflow_definitions.py`|34121|`a25c4ea90a72fc25ce5701b12a02492c4483baee7544f3c222418372d7c37eb2`|
|`src/ergora/cli.py`|81175|`60f319159b65a762243f884ae1feb9087784f745cfeff63910f8b37b61dbabe0`|
|`tests/test_skills_evaluation.py`|37013|`283d847674a41a7c3f5fe5062e28e37f0a9fade0c06ec59dcb58dc98ecc6a242`|
|`tests/test_workflow_definitions.py`|39158|`2dcc3ef39f845b221e6ba171cc136e8b6710abae939d52e0be6629dd1faf7bec`|

相邻代码已核 `definition_bundles.relative_path/parse_json/read_json`、`asset_trees` 原目录身份、`skill_assets` 的元数据／导入／版本／head／回退、`evaluation.register/suite/evaluate/compare`、`skills.adopt`，及原组合 `inspect_input/restore_manifest/_prepare_bundle` 与 CLI 调用位置。原可替换后端、子权限与完整祖先资料仍由原组合编译／冻结输入负责，本片没有变更该合同，也没有新增调度或执行通路。

## 需求轴

`retrospectives.export` 经 CLI 的两个必填摘要选择原结果与候选。共享 `_checked_proposal` 保留原有界单次结果读取、原 input／任务身份、完整基线、来源引用、候选路径与元数据检查；export 使用这次解析所得的完整内存候选，发布前没有重新打开结果。导出返回原 input／result／baseline／candidate 身份，并保持 `quality_evaluated:false`、`adoption_authorized:false`、`origin_authenticated:false`。

候选逐文件 `encode('utf-8')` 后二进制写入，避免文本写入的换行转换；按原执行位 chmod，再经原 `digest_tree` 验完整文件集与执行位，身份相同才发布。目录名符合原导入入口；不存在将完整候选缩成单份 SKILL.md 的路径。目标位于冻结 input 内会拒绝，已有目标与并发出现的目标不会合并或覆盖。私有同文件系统 TemporaryDirectory 持有整个写入／核验／发布过程，I/O 或发布失败会清理本次 staging；发布后的完整目标不由该清理删除。

CLI export 分支没有构造 State；目录扫描、结果解码和元数据解析均不执行候选脚本、调用模型、查询实时来源或改 head。`skill import`、可信 suite／scorer、双方同 suite 评价、eligible 比较、当前 baseline／revision、明确采用理由和曾活动版本回退仍由原 owner 持有。新增手册命令与实际 parser 一致，明确区分检查、模型审查、导出与可信评价／采用，也保留回复丢失后先核已有目标和 head 变化后重新选择评价的行为。

本片未改默认 preset、后端选择、权限继承、祖先资料传播、评分器、采用日志或调度器。记忆／流程候选、页面、完整 Forge 与真实 GPU／业务效果仍是后续范围。源码可支持所述闭环，实际安装 CLI 的正候选旅程尚未由本轮验收。

## 结构与成本轴

|新增／调整的 module interface|实际生产消费者与所有权|判断|
|---|---|---|
|`retrospectives.export`|`cli.main` 的 export 分支；完整候选校验与发布用例留在原复盘 owner|顶层用例的一处 CLI 消费者足以解释该 interface；没有把 Skill 语义塞入通用文件 owner|
|`retrospectives._checked_proposal`|同 module 的原 `check` 与新 `export`；共享本地完整验证和解析结果|局部私有算法有真实两项用例；不声称跨文件复用。原 check 的轻薄入口保留原返回合同，新 helper 没有作为另一个公开转发层|
|`asset_trees.publish_directory`|`retrospectives.export` 与 `workflow_definitions.restore_manifest/_prepare_bundle` 两个生产文件|同一具体 no-replace 发布需求已真实出现；删除它会让两处重复平台算法。旧 `_publish_bundle` 及独占 imports 已删除，无兼容转发或抽象工厂|

直接用 AST 对照固定基线的 `_publish_bundle` 与新 `publish_directory`：除函数名与两处错误文案的 composition→directory 外完全等价。Linux 仍用 `renameat2(RENAME_NOREPLACE)`，Windows 仍用其不替换目标的 Path.rename；无普通覆盖 rename fallback。原并发空目录回归迁移到了 `workflow_definitions` 的真实导入点，注入后仍通过原生产发布调用保护原组合，而非另测一份复制算法。

新增导出是显式离线操作，结果读取上限仍为原 8 MiB；内存保留原结果／解析候选，文件编码、写入与最终目录摘要为与完整内容大小相关的成本，没有新复制整套 State、读取实时来源、执行进程或网络成本。完整 input 检查与发布器每次 ctypes 加载保留原实现成本，没有热路径或训练性能改变。新增测试在原 suite 中覆盖字节／执行位／原导入／head 不动与静默目标污染风险，没有新 suite／CI 组、默认值断言或逐消费者复制原子算法测试。

## 新控制流的可达场景

|位置|可达条件与所保护的行为|
|---|---|
|`retrospectives.py:180`|原 check 支持 null；显式 export 无候选时必须在创建输出前拒绝|
|`retrospectives.py:182`|用户所选候选摘要与这份原结果不一致；防止导出未经明确选择的候选。原结果摘要在共享验证处先核|
|`retrospectives.py:185`|目标末级目录名不同于元数据 name；原 Skill importer 也要求此关系，在导出写入前给出错误|
|`retrospectives.py:187`|直接或经现有父目录 symlink 指向冻结 input 内；避免新增目录污染原完整输入|
|`retrospectives.py:189`|目标已存在或为悬空 symlink；提前拒绝，末次竞争由 no-replace 发布器处理|
|`retrospectives.py:200`|文件系统不能保留选定执行位或写入后完整身份不符；拒绝发布已变身份的目录。Windows 的 chmod 能力不能假定等同 POSIX|
|`asset_trees.py:64`|原 Windows 发布路径；Path.rename 的平台行为保留。未在本机冒充 Windows 动态验收|
|`asset_trees.py:66/68/72/75`|Linux 缺 renameat2、系统调用失败（包括并发目标）或不支持平台；保持原显式失败，不降级为可覆盖发布|
|`retrospectives.py:192` 的资源作用域|磁盘满、权限错误、模式不符及竞争发布失败均可达；TemporaryDirectory 在传播错误时清理 staging，无新吞错 handler|

其余验证分支是原 check 实现移入局部 helper，未添加新的兜底、重复评分、回退状态机或无关参数限制。路径／类型／内容身份继续使用原 owner；候选模式不支持时显式失败属于合同所要求的行为。

## 实际检查与待验

已直接读 `.ergora/checks/retrospective-skill-adoption/development-r1/{result.json,stdout.txt,stderr.txt}`：原命令以既有 venv 解释器执行 `tests/test_skills_evaluation.py tests/test_workflow_definitions.py -k 'retrospective or concurrently_created_empty_destination'`，exit 0，stdout **18 passed／99 deselected／18.41s**，stderr 空，外层计时 19.025 秒。该记录是开发源码定向验证，不是新非 editable 安装验证。

Reviewer 另以 `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src` 和既有解释器 `-B` 做纯内存探针，通过：文件清单顺序不改变摘要；LF／CRLF 保持不同原字节身份而元数据一致；执行位变化改变摘要；`../escape`、文件作父目录、大小写文件／目录冲突、`CON` 和反斜线路径均被原候选验证拒绝；原发布器与迁移后 AST 等价。没有创建探针文件或运行 pytest。`git diff --check BASELINE` 通过。

首轮列出的最终验收接续项（以下保留当时范围，后续补核见末节）：

1. 最终非 editable 包／源码快照／已安装产品相同，两 RECORD 和 283 参考文件；适当原 suite 覆盖组合准备与 manifest 恢复。
2. 实际安装 CLI 的完整正候选检查→显式导出→原导入→同 suite 双方评价／比较→明确采用→原回退，以及陈旧采用拒绝时 head 不动。保留原 input／result／digest／run／revision 与可信 scorer 身份，合成提案与 fixture scorer 仅证明合同。
3. Ergora 自身原结构模板的实际完整输入／后端／原回复、失败或回退，以及公开 evidence 的原件引用与收尾。模型 approve 与独立 reviewer 结论分别记录。
4. 前片 CI 及原补核终态后，本片普通发布、精确固定提交／完整 Ref、本片自己的 CI 与原独立补核。该项不由本轮源码通过提前关闭。

本轮两轴 finding 均为 0，剩余项为明确未完成的验收，不虚构缺陷，也不以静态源码或历史通过替代这些实证。

## 最终 r1 安装与实际 CLI 补核

直接读 `install-r1/{setup.json,source-manifest.json,package-identity.json}` 与构建／安装验证脚本，再自行只读遍历 wheel 和已安装文件。wheel SHA256 为 `d78d387cccdb5571d866c8b096e8dbf2d7a52d584ff989f233e87dbd25157893`；**586 个产品文件逐字 current=source snapshot=wheel=installed**。wheel RECORD **594** 行和 installed RECORD **599** 行的声明字节／SHA 均逐份核过，原 reference-manifest 的 **283** 文件身份相同；没有 editable 安装。这六份源码／测试身份与首轮表一致，五份已跑 suite 也与当前源码逐字相同。

直接读 `install-r1/regression-r1/result.json` 与 `process/{stdout.txt,stderr.txt}`：隔离 `-I` 解释器从构建快照运行原 `test_skills_evaluation.py`、`test_workflow_definitions.py`、`test_architecture_boundaries.py`、`test_compatibility_baseline.py`、`test_windows.py`，**140 passed／6 skipped／65.23s**，monitor **66.792842s**，status succeeded／returncode 0，stderr 空。六个跳过均为原生 Windows 项，不能宣称本机动态验过 Windows。实际 stdout 覆盖原完整祖先／权限、并发空目录、完整字节／执行位、原导入／采用回退和架构身份保护。

另直接核 `native-r1.py`、`native-r1/result.json`、`commands.json` 及全部 **14** 组原 stdout／stderr：每次均为最终安装件的 `python -I -B -m ergora`，原输出哈希与回执一致。错误摘要、已有目标和陈旧采用三次均 exit 2、stdout 空且有原错误；其余 exit 0、stderr 空。完整已保存 input 经原 inspector 重算、原结果经原 check 重算，与实际 CLI 输出一致；导出的两份完整候选文件逐字／执行位／目录摘要相同，`unused-state` 不存在。

|合同身份|直接核实值|
|---|---|
|原 input digest|`90f78d08e5e4b93416d92896dfdf5bc3b7f64b6faf56bbf656a0e31b2fac0af2`|
|原 result SHA256|`ebbf2dbfea351731254c7f6002c9a52de949dc64bdc8397fdd6bfd239df3eee2`|
|baseline digest|`928cd6ba6bd5b44e6e0d769a0ce29662a78416c8cb19dd95f2e81dd0ebc09115`|
|candidate digest|`ab781d6af6ee49c7506225ad42326f182d9c4d21afa784fb76300be1faac70ae`|
|双方同 suite digest|`a41767dc16dc5da7f0f2a1436fd4762293b27bb2d7581ae4fcda862fe021d6f3`|
|预先固定的 fixture scorer SHA256|`de2dbca088f58b6a04dcf9c7e1d60070d7c4b73360c947fd4831d1534f032c14`|
|双方原 run ID|`69b94a212dbe4887a4bbd208be305aee`／`a24b721193dd4e7887268d0f9b785e65`|

可信 scorer 在合成提案构造前写入，后由原 register 固定；其判断“是否含 fixture 指定句子”，明确只测合同。双方原评价的六份 case stdin／stdout 已逐份核：同三 split／同 fixture input，skill_dir 分别指向精确 baseline／candidate，均 passed、cost 0；合成得分 baseline 0、candidate 1。原 compare eligible，采用证据精确为上述两 run；导出与导入前 head 为 baseline revision 1，明确 adopt 后 candidate revision 2，陈旧 adopt 拒绝，rollback 后恢复原 baseline revision 3。最终只有 baseline／adopt／rollback 三项历史；实验 Git status 与原保存回执相同。

本次补核未发现新 finding，**两轴在源码、最终安装件及实际合成 CLI 合同范围均 approve／开放 0／0**。仍有一项具体覆盖缺口：五 suite 没有 `tests/test_composition_manifests.py`，原 `test_carried_manifest_is_atomic_on_interruption_and_retry_uses_the_same_bytes` 与 `test_untrusted_carried_manifest_never_publishes_outside_or_with_different_identity` 才直接调用本片迁移的 `restore_manifest`。已向实现者列明此原 suite／原用例，待同一安装件补核；属于验收待项，未当作源码缺陷。自身模板、公开 evidence／收尾及后续固定发布／自己的 CI 仍待，不从本片 fixture 合同推导真实模型改进、泛化、性能、GPU 或业务效果。

## 最终本地补核

本节为原 fresh-context reviewer 对同片最终本地证据的补核，取代前文的本地待验状态。HEAD／基线仍为 `a60a8f68513a46ef7e6c18add0832f8bcee3eccc`，完整 status 已重新读取；产品／测试 tracked 差异仍只有原六份，没有后续产品混入。新增 untracked 为本报告及[公开 evidence](evidence/2026-11-14-retrospective-skill-adoption.json)，连同原本片计划／交付均已读。

原 manifest 恢复覆盖缺口已关闭：直接核 `install-r1/regression-restore-r1/{result.json,process/stdout.txt,process/stderr.txt}`，同一最终 r1 安装件、隔离 `-I` 解释器运行原 `tests/test_composition_manifests.py`，**14 passed／8.59s**，monitor **9.924464s**，status succeeded／returncode 0，stderr 空。stdout 直接列出原中断后完整恢复／同字节重试、外写／身份反例、完整祖先资料与离线备份等用例。该 suite 当前原字节等于构建快照；与前五 suite 的 **140 passed／6 skipped／65.23s** 分别记账，没有混称一次全套或新增测试体系。

最终身份已再独立只读核过：**586 产品 current=source snapshot=wheel=installed**，wheel SHA 保持 `d78d387cccdb5571d866c8b096e8dbf2d7a52d584ff989f233e87dbd25157893`，两 RECORD 的 **594／599** 行逐份摘要／字节相同。另直接从固定基线读取 **283 个 Git blob**，与当前参考文件原字节、执行位及 reference-manifest 逐项一致。本片六份源码／测试与首轮记录保持；新增恢复 suite 的 SHA256 为 `65a4cb2dd91c4d6904fdd422c5c3045e7526a20f04a3f212494ea474c66be935`。

自身模板原件已直接核 `self-review-r1.py`、`self-review-r1-fallback.py`、两次 admission／native stdout／stdin／冻结 input／原结果及两份汇总 JSON：原根为 `ergora-structure-review` 1.0.0，`root/review` 的三项继承 resources 全在原 prompt。**8 份完整文件／213,087B** 与原构建快照逐字相同，六份产品／测试还与当前原件逐字相同；当时冻结的两份计划／交付保留原身份。完整 prompt **217,620B**，原 task 全文与每份完整文件均在实际 stdin；原 input 和两个 run 自带快照经原 inspector 重算相同：

- input digest：`6e259ad52c19f39bec9954892e35df75aa30469d0713c88227ec5585fd96e868`。
- prompt SHA256：`e7c9d91a1f9216c5c4357cb5d41fe53425de92646edd2f699a7030ebd2b36625`。
- Claude Code 原 run `b06815c1e14d46b5bc137c756dfbb1fd`，**360.685605s／timed_out**，CLI exit 1，无 review result；失败原件保持。
- 授权 Codex 新原 run `eb9712fb21174665b20f7e191b76c9b9`，显式保留 fallback reason 与前 run 身份，精确复用同 input／stdin，**58.630926s／succeeded／approve**，CLI exit 0。原回复 SHA256 为 `90414ffd2f022439eb7a292304b18f094a30fc781cc64d488091d2984d9570a0`，保存副本与 run 原结果逐字相同。

已读模型原回复：结论只限所给完整文件的静态结构／正确性检查，明确未独立检查未提供的相邻 owner 和运行测试。它不是异后端成功、独立 reviewer 结论或真实质量评价。本 reviewer 的需求／结构与成本结论仍依据前述实际相邻 owner、源码、安装、CLI 和原件核查分别成立。

公开 evidence 的 **130 份原引用**已逐份读取，路径唯一、字节数与 SHA256 全部相同，无缺失。公开汇总的七份 current／snapshot 源码及测试身份、两项分开记录的安装回归、14 次实际 CLI、两次自身模板身份与原件相符；publication 仍为 pending。原 `cleanup-r1.json` 的终态记录与已见调用／harness 原终态一致：可访问 `/proc` cwd 范围内无本片在途进程，**10 个不可读条目**、未启动服务／端口／浏览器的范围和“不证明系统全部进程”限制均保持。`git diff --check BASELINE` 再次通过。此 reviewer 本次仍仅作读取／纯函数校验和追加本报告，未联网、重跑 suite、安装、改产品或提交。

**最终本地需求轴 approve；结构／成本轴 approve；确证 finding 0／0、开放 0／0。** 本地待验项已补齐，原实际 CLI 的合成提案／fixture scorer 只证明完整合同及采用／回退门禁；不声称模型生成了正候选、真实改进、泛化、质量／性能、GPU 或业务效果。原生 Windows 六项仍跳过，完整 Forge、记忆／流程候选、F10d 页面、F9d／G1 保留各自范围。前片 CI43551217945 的 Windows 终态／原补核、本片普通发布／精确固定提交及完整 Ref、本片自己的 CI 与原独立发布／CI 补核均尚待；本节不预先批准或借用这些结果。

## 固定普通发布补核

固定候选为 `c4aa7acb555a5d55fec7e7a483544834e8afe44f`，唯一父提交精确为原基线 `a60a8f68513a46ef7e6c18add0832f8bcee3eccc`。补核开始时 HEAD 为该候选、分支保持 `refactor/architecture-foundations`，完整 status 只有 PLAN、本片计划／交付／evidence 四份发布状态文档变化。补核中随后出现的后续记忆候选计划／交付不在本报告范围，未审其内容；没有后续产品／测试变化。

从固定 Git object 直接读取全部 **18 个变更 blob**，路径集合、字节数和 SHA256 与原 `static-final-r1.json` 完整清单全部相同。固定独立本地报告原字节为 **19,680B**／SHA256 `b22b1560cfbb891c6ff35641e0c912f9f0092441666ff4460bb476368fc64be5`，恰为本 reviewer 的最终本地补核版本。六份本片源码／测试与原最终 r1 已验快照、当前源码逐字相同；又直接从固定 Git tree 读取全部 **586 个产品 blob**，逐份核为 **fixed Git=current=source snapshot=wheel=installed**，wheel SHA 保持 `d78d387cccdb5571d866c8b096e8dbf2d7a52d584ff989f233e87dbd25157893`。前五 suite 加原恢复 suite 的六份测试文件也与固定 Git／原快照／当前原件逐字相同。此前已核两 RECORD **594／599**、283 原参考身份、140／6 与另 14 项恢复、14CLI 与两原模板调用的实证因此适用于此精确发布候选，没有在验收后偷换产品身份。

直接读取 `commit-r1.json`、`push-r1.json`、`ref-r1.json`：三份 exit 均为 0，candidate 均为上述完整 SHA；普通 push 命令精确为 `git push origin HEAD:refs/heads/refactor/architecture-foundations`，无 force 或 main 目标。完整 Ref 原回执 stdout 精确为 `c4aa7acb555a5d55fec7e7a483544834e8afe44f\trefs/heads/refactor/architecture-foundations\n`，stderr 空。此 reviewer 核的是保存的原提交／push／Ref 回执，未重新联网。

固定提交的公开 evidence 含 **130** 份原引用；发布后工作树前 130 项与固定列表逐项相同，原路径、字节数、SHA 均未变。仅追加 static-final／commit／push／Ref 四份回执，合计 **134** 份；已逐份重新读取核验全部 134 项 bytes／SHA，无缺失或差异。发布后的四份状态文档只追加普通发布、完整 Ref、130→134 对应关系与自己的 CI 待发现状态，没有新增运行或效果主张。`git diff --check BASELINE` 通过。

前片原 reviewer 的 CI 终核记录已明确关闭前片精确候选的八 job／30 必要步骤；该记录只处理既有发布依赖，不作为本片 CI 验收。**本固定发布需求轴 approve；结构／成本轴 approve；开放 finding 0／0。** 原 Claude 超时／同 input Codex 授权回退、合成正提案／fixture scorer 合同及全部未验范围保持。本片自己的 CI 当前仍为 `pending_discovery`，尚未获得终态或本 reviewer 的 CI 补核，不能借前片 CI 或本地运行宣称该候选 CI 通过。

## 自己的 CI 终态与取消原因补核

本节核固定候选 `c4aa7acb555a5d55fec7e7a483544834e8afe44f` 自己的 run **43553150941** 的已保存官方原件。结论是 **Cancelled，完整 CI 尚未通过**，不是 CI 成功批准。补核时 HEAD 仍为该固定候选，但工作树已含后继记忆候选及 Windows CI 预算修正；本 reviewer 不在这里审这些变更，也不让当前工作树冒充固定候选。

直接解析 `ci-run-html-r5/page.html`、Windows `ci-job-132319976802-html-r5/page.html` 与其余七 job 的 r2 HTML，并核各自 receipt 的 URL／HTTP 200／原字节／SHA。run 原页面的 commit 链接精确指向上述完整 SHA，Status 为 **Cancelled**；八个 job 的 **30 个必要步骤**均有原 `data-job-completed`、非空开始／结束时刻，log URL 全部精确落在该 SHA 和本 job ID 下。每项开始不晚于结束，结束不晚于对应原 HTML 取得时刻。原 `ci-ui-metadata-r1.json` 的八个 job ID／name 来自该 run 的原 UI JSON batch，batch 与初次 run summary 的 SHA 绑定保持；早期 in_progress 状态没有覆盖为成功历史。

独立从固定提交的 `portability.yml` 确定必要步骤，再从原 HTML 投影核对：plan 的 1 项、六个 Linux job 各 4 项共 **25 项成功**；Windows 五项中 **4 成功／1 cancelled**，总计 **29／30 success**。原步骤投影与 `ci-observation-r5.json` 一致，`required_steps_passed:false`。Windows 原步骤如下，时刻均为 2026-11-14 UTC：

|Windows 必要步骤|原时段|原 conclusion|
|---|---|---|
|Build and install wheel|03:44:38–03:45:38|success|
|Packaged reference identity|03:45:38–03:45:40|success|
|Native application regression|03:45:40–04:04:00|success|
|Windows PowerShell 5.1 installer and upgrade|04:04:00–04:04:31|cancelled|
|Upload regression observations|04:04:31–04:04:33|success|

run 和 Windows job 两份原 HTML 均有官方注释 **“The job has exceeded the maximum execution time of 20m0s”**。固定候选的原 native job 确实设置 `timeout-minutes: 20`。原 job 从 03:44:30 开始；应用回归用时 18 分 20 秒并成功结束，installer 开始时已消耗 19 分 30 秒总 job 时间，随后 31 秒即被取消。upload 使用原 `if: always()`，其成功不能补足 installer 门禁。原 HTML 没有给出 installer／upgrade 完成成功的证据，故这个范围仍未验收；这里只核官方超时原因和可见步骤终态，没有下载或声称读取 artifact archive／完整远端测试日志，也不另报远端 pytest 数量。

公开 evidence 独立列出的 **66 份 CI 引用**已逐份直接读 bytes／SHA，无缺失或差异；与原非 CI 引用集合不重叠。固定 Git blob 内的 **130** 份原引用仍与发布后列表前 130 项逐项相同；原发布后的 **134** 份也全部重新读取核过，仅原四份 static／commit／push／Ref 回执追加关系保持。CI 的多次未终态采样和最终取消原件分别保留，没有混充固定提交引用或改写失败历史。`git diff --check` 通过。

**本次终态／取消原因核对完成，完整 CI 不通过，剩余范围明确为 Windows PowerShell 5.1 安装／升级门禁。** 前述源码、本地合同及固定普通发布结论保持各自范围，不能提升为该候选全部 CI 成功。后继 Windows 30／Linux 20 的预算修正由新独立 reviewer 审查，并将与后继已本地验收的记忆产品以新 SHA 普通发布；须验新 SHA 自己的完整必要 CI，本报告不预批该修正或新运行，也不重写原 `c4aa7ac` 的取消结果。本 reviewer 此轮仅读取本片固定 CI 原件和追加本报告，未联网、运行 suite、修改产品或操作 CI。
