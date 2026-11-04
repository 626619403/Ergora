# F5.3：受约束的离线证据交接包

日期：2026-11-05。状态：F5.3a原生导出/离线验证已实现，本地发行/原run验收通过，初审两项P2已修、103项及同片独立复核通过；精确87538b3已正常推送、远端及归档/静态/同片独立提交复核通过；双OS CI41921284766及同片最终独立终结均通过，F5.3a完成。源码基线`bb4e4617a6f412b7d2ec94e9433fcc4c6e8147f7`，前置F5.2精确双OS CI41914631896及同片终结通过、已完成。F5.3b HTTP下载按独立切片后续实施；a通过不代表完整F5.3完成。来源：[F5计划](../plans/2026-11-05-evidence-handoff.md)。

## 格式与证明范围

采用标准ZIP存储、UTF-8 JSON与SHA-256，不引入新DSL、依赖、执行账本或导入执行器。v1包只含`manifest.json`与`blobs/SHA256`，产物按内容摘要去重，不使用原材料路径作为包内可写路径。manifest包含格式名/版本、完整F5索引及其规范JSON摘要、每个blob的字节数；在收集前固定索引和引用集合，收集时重新核实际字节SHA，最终才发布完整文件。保持原摘要规范，不混用控制库/Skill树的摘要方式。

包携带冻结spec/Agent绑定、原候选与回执、原outcome及原观察到的预算/用量，供逐项复查。离线校验检查包文件集合/大小/SHA、索引内部合同与回执/材料关系，原创建/提交/context/history的摘要仍是引用；不携带完整服务history、原创建/提交意图或Git对象，不能据此离线重验它们的来源、执行器身份、审查独立性或候选代码。检查成功表示已收字节与声明匹配，不代表工作流通过、合入许可或来源认证；原失败/取消与未知费用保持。可选外部整包SHA只证明与独立取得的期望摘要相符，不自行制造签名或身份认证。

只导出完整材料观察：原索引须`published_evidence: verified`，没有unresolved/unexpected job；取消或失败的原业务结果并不阻止完整证据交接。缺失/损坏材料明确失败，不产生看似完整的部分包。收集范围仅冻结索引及原回执指定产物，不扫描环境、凭据、当前配置、任意用户目录或整个仓库。

v1限制：manifest最多1 MiB，每blob最多16 MiB，去重blob总字节最多64 MiB，ZIP最多4096个文件/72 MiB；仅ZIP_STORED、普通文件和精确成员集合，拒绝重复/多余/缺失成员、非规范/逃逸路径、链接、加密及不支持的压缩。校验直接读ZIP成员，不提取或执行。该上限约束交接收集/返回及有界源文件，不改变原索引完整history/FileAdapter核验的既有总IO成本；不宣称ZIP库峰值内存等于成员数或响应上限。

## 入口与所有权

- `ergora task handoff PROJECT TASK --run-id RUN --output PATH [--timeout 20]`明确收集到新的本地文件，不替换已有目标。复用`tasks → reference → _Inspection`的原提交/闭合run/完整history/FileAdapter及1–60秒查询预算，父进程另5秒；元数据经既有JSON边界返回，包字节写指定输出而不经过stdout/base64。输出采用同目录临时文件和仅创建发布，异常清理临时文件；不会改任务记录、模型、信号、fence、lease或ref。
- `ergora handoff verify PATH [--sha256 EXPECTED]`在基础Python安装、无控制库/SDK/服务下验证本地包；可在Windows原生运行。它不导入/恢复工作流，不执行材料中命令。输出整包摘要、项目/原run/候选引用及真实证明范围，不将自带SHA当来源认证。
- 独立`handoff`领域模块拥有格式、受限ZIP读写和离线内部一致性；外来包读取入口使用现有`contracts.StrictValidator`及版本化JSON schema，收集端消费已由原生边界核验的内部索引、核完整性/内部引用并重算实际材料SHA，不重复执行外来JSON Schema校验。Schema库仅在离线verify入口延迟导入，原生collector不需要控制环境的依赖。模块不导入tasks/reference/CLI/Web/State或SDK。真实消费者为原生`reference_task_reconciliation`的收集分支和CLI的离线校验；原生FileAdapter通过一个实际读取端口提供唯一产物的字节，路径/可信根继续由原边界负责，不复制第二个执行器。
- HTTP下载接在同一用例：只在明确请求后收集到本次临时文件、读受限包字节并保证清理，不允许浏览器传服务器目标路径。CLI显式文件与HTTP临时下载分别验收；F5.4页面只调用该入口，不在浏览器拼装证据或选择任意本地源路径。若实现/审查规模需要，原生+离线包与HTTP下载可按F5.3a/b分别交付，不以某一端通过标完整F5.3完成。

## 验收与后续

1. 轻量合同测试覆盖正常/取消/失败原结果、重复引用去重、二进制产物、原摘要规范、索引/manifest关系、缺失/篡改/重复/逃逸/特殊成员/大小边界、外部期望SHA及未知来源；坏输入不得覆盖已有文件，不执行命令或初始化控制库。
2. 实际原生收集及CLI/API接线、超时/输出错误与清理、旧external-status/对账输出保持；以最终noneditable包、更新资源数和冻结283身份验收。新格式/模块的实际消费者、必要守卫和数据来源需独立审查，不增加无关CI或重跑宽矩阵。
3. 两正常原run及取消原run从最终包导出，再在无SDK独立基础安装中离线校验，逐blob与原receipt/产物SHA对照；核原139文件/history/outcome/Git/leases保持、不开worker/模型、正式退出专用Temporal并保留数据库。精确提交/普通推送/双OS CI与新独立审查终结后关闭本片，再接F5.4页面和F5.5综合验收。

二进制包是可复查材料快照；完整运行迁移、签名/组织认证、Git bundle与外部观测投影不在本片隐式接入。

## F5.3a 实现与本地验证

新增`handoff.py`及`task-handoff-v1.json`，真实接线复用`tasks → reference → reference_task_reconciliation._Inspection`；CLI离线验证在State初始化前独立分派。JSON元数据和包字节不混流，目标只在明确指定的新路径发布，普通异常清临时；强制进程退出/超时的残留与目标须先检查，公开手册已说明。新增格式轻量测试跨平台收集，原生SDK/FileAdapter测试仍遵守Linux/WSL2边界，现有CI直接收集，无依赖或CI作业变更。

初包`ee0ea8000cf61e4c39ab38f1dcf02d3573e238235734435637248f5cf0c40205`的352资源/两安装/283冻结和96项定向通过，但真实导出失败`No module named rpds.rpds`。实测控制Python3.11、原生3.12且原生没有jsonschema；跨进程PYTHONPATH只为Ergora源码提供位置，却连带暴露控制site-packages的3.11二进制扩展。未通过安装额外包或扩大运行时依赖掩盖该问题：收集的输入已有原生校验，外来manifest才是Schema应负责的边界，故将Schema库延迟到verify入口。补充真实子进程阻止jsonschema/rpds导入的collector回归；保持原`_task_operation`协议与冻结运行时不变。

修包`2a0f8297489b3f650effb761917ec6fd1e23b04517f267300ce01feb098358f5`的352源码/wheel/两noneditable安装及283冻结身份通过；基础安装仅默认依赖，无Temporal/Web库。最终包定向97 passed：40格式/离线、36索引/原生、12原payload、9架构，保留一个TestClient上游弃用warning。旧两模板external-status/reconcile代表4项在首包通过，其既有所有者源码与修包相同；没有把首包的完整模块集合视为修包身份，也未重跑无关重型矩阵。

三个原run从修包真实收集，接收者使用独立基础安装离线核对；manifest内索引与前片F5.2实际观察逐字段一致，每blob与原receipt指定字节及SHA一致：

|原任务|材料引用/唯一blob|材料字节|整包字节|保留原结果|
|---|---|---|---|---|
|repository-governance正常|23 / 23|105296|135834|REVIEW_READY|
|large-change正常|19 / 19|156248|185003|REVIEW_READY|
|repository-governance取消|1 / 1|59|11562|CANCEL_UNCONFIRMED|

三次已有目标拒绝覆盖，错误原run/跨项目均拒绝且无输出，错误外部整包SHA拒绝，离线verify未创建指定control home。实际导出约1.73–1.94秒，基础CLI离线验证约0.22–1.01秒；仅为本次1–23blob、11–185KB包的命令整体观察，不声称峰值内存、最大上限吞吐或性能提升。收集复用一次完整history扫描和原FileAdapter，再对唯一内容实际读取核SHA；verify有界读取整包和成员，不执行或提取。首包和失败命令/日志保持独立，不覆盖历史失败。

三原history/outcome、139原证据文件、两业务repo的内容/HEAD/refs/worktrees及三claim/零active lease前后完全相同。正式shutdown confirmed，两个owned进程已退出、四端口已关闭、三个持久数据库保留，最终离线139文件/租约重核通过；未运行worker、模型、批准、fence、租约或Git变更。私有命令/日志/包及原字节对照保存在忽略的`.ergora/checks/f5-task-handoff/`。新fresh-context独立审查、精确提交/普通推送/双OS CI及同片最终终结尚未完成；HTTP下载归F5.3b，不算本片通过。


## 初审修正与最终包

[新独立初审](2026-11-05-task-handoff-review.md)提出两项P2：外来回执可接受空白check ID/末尾LF标识，以及COMPLETED/null或其他闭合Temporal状态/对象outcome的矛盾组合。先用2a0f829包运行六个全部相关摘要均重算的反例，6 failed、均为未抛错；原日志保留。随后仅在新schema将check ID约束为非空白、digest/identifier/candidate/blob key改为ECMAScript兼容的绝对末尾匹配，并条件限定COMPLETED有对象outcome、其他闭合状态为null；不改原业务状态，也不修改冻结FileAdapter或生产收集器。

最终wheel `cdf4ab628a8856ee39c30d6e1857f243c3a5c718ee209371162e8d79f6ee3c0c` 的352源码/wheel/两noneditable安装及283冻结一致。源码与最终包各103项定向通过（46格式/离线、36索引/原生、12原payload、9架构；各保留一个上游弃用warning）。最终包相对真实导出所用2a0f829包，唯一变化为外来包schema；全部collector/CLI/native用例源码逐字节相同。未重复启动原生服务或重收相同材料；用最终无SDK/Web基础安装重验原三个交接包，整包SHA/原结果/43材料字节计数保持，指定control home未创建、服务未启动。这里明确区分实际生产收集包和最终reader身份，不将初包或历史CI算作最终候选验收。

两项finding的作者侧修正与验证完成，同片独立复核待完成；之后精确提交、正常推送、双OS CI及同片最终终结仍为必要步骤。完整F5.3的HTTP部分及后续页面不在a片中关闭。

同片独立复核已通过，两P2关闭，无未解决finding：最终cdf4ab包352资源/两安装/283冻结、六坏例与四种合法非COMPLETED/null、三原包及43材料、139文件保持、生产收集/最终reader身份均独立核实。下一精确提交/正常推送、Git归档同包、精确双OS CI及同片最终终结；a和b继续分开交付。

精确候选87538b3dcafb13ca5bbc8191f84e5a4b0fbf0083已正常快进推送，352 Git archive与cdf4ab最终包完全相同；11份文档348链接/锚点与30命令终核通过，同片独立提交/blob/包/静态/普通推送及实时远端复核通过，无新增finding。精确CI41921284766仍进行，最终双OS与同片终结待完成；F5.3b工作树不计入本片候选。

F5.3a完成：精确CI41921284766的Windows126894160085与Ubuntu126894160730全部必要步骤成功；[同片独立最终终结](2026-11-05-task-handoff-review.md#精确-ci-与同片最终终结)再次核精确Git/包、原HTML和实时远端通过，无未解决finding。F5.3b仍按自身独立验收推进，不据此标记完整F5.3/F5完成。
