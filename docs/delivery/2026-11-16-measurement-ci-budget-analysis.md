# M2／M3 测量接缝的 CI 预算有限调查

日期：2026-11-16。本次为只读调查报告，不是独立审查。仅新增本文件；未运行测试、collector、网络或安装，未修改产品、测试、CI、共享 PLAN，未提交／推送。调查时主树为 `6493f30`，活动测量实现另在隔离树；二者不能混作同一候选。已读根／scripts AGENTS、PLAN、组件协议“脚本和检查”、[原成本调查](2026-11-16-ci-training-shard-duration-analysis.md)及[分组计划](../plans/2026-11-16-training-ci-shards.md)。

结论：现有证据支持只改 JSON 的有限再平衡候选：将完整 `tests/test_work_agents.py` 从现有 group5 移至 group3；也可同时将完整 `test_training_cancellation.py` 移到3，为最终r3测量争取更多余量。两文件均有完整历史 JUnit 成本、当前字节保持和已有独立模块边界支持；不增加 job、时限、测试或观察机制。但证据不足以证明任一方案已经足够覆盖新测量成本，更不能认证新候选 CI 成功或超时。先固定测量最终修正，再决定是否实施。

## 官方结果及其准确边界

以下均从已有 HTTP200 jobs／run 原件计算整个 job 的 `completed_at - started_at`，无新增请求。六 Linux job 原限时仍各20分钟，包含安装、reference verify、回归与上传；并非 pytest 独享1200秒。Windows30分钟保留。

|准确候选／自己的 push、attempt1 run|Linux组0／1／2／3／4／5整个job秒数|准确结论|
|---|---|---|
|`59b74ceb4e3b90c2c875bb5eca56bbf8a102c384`／[43769505506](https://github.com/626619403/Ergora/actions/runs/43769505506)|420／264／487／241／336／1166|八job全success；group5距1200秒34秒|
|`833966d4ba21fa7bcb6670e9908d05f058cf8fdd`／[43773202173](https://github.com/626619403/Ergora/actions/runs/43773202173)|418／326／580／303／342／945|六Linux及plan全success；整体failure来自Windows；group5距1200秒255秒|

原件分别在 ignored `round-content-m1a/publication-r1/20261115T225324Z-{run,jobs}-response.json` 与 `cycle-v3-birth/publication-r1/20261115T233025Z-{run,jobs}-response.json`（均相对 `.ergora/checks/`）。这些目录没有保存当前候选逐文件 JUnit／phase artifact；jobs 的回归 step 时间也不能分配到单文件。两次 group5 相差221秒不能解释成新增／删除成本，也不能选择较快一次作为未来固定上界。6493f30或活动测量片的自己的官方终态不在本调查证据内。

更早 `478c98891522930817fa7005a8ac96e408f37230` 的43737570677确曾group5超时取消；它属于拆分／再平衡之前。原失败保留，不能套给本次测量候选。

## 新测量选集：已完成与尚未证明

本次读取时 run-12、package-r2安装测量已经各有结束结果与完整JUnit，故不继续称为在途。它们仅是21项 `round_` 选集，均归 `test_training_submission.py`，不是完整 group5：

|已有原件，相对 `.ergora/checks/cycle-measurement-collect/`|结果|JUnit suite／case合计秒数|外层秒数|
|---|---|---|---|
|`source-r1/run-09/{result.json,junit.xml}`，原patch1c99f999范围|21 passed，exit0|178.598／177.903|178.889|
|`source-r1/run-12/{result.json,junit.xml}`，r2修正范围|21 passed，exit0|189.861／188.974|190.362|
|`package-r2/installed-measurement-r2-result.json` 与 `installed-measurement-r2.xml`|21 passed，exit0|303.710／302.107|305.105|

安装原件绑定基线 `23ad171bf8228bf80b070d6ad866f79d63986d56`＋冻结patch SHA256 `08926a95aa9be4593bf0a79940cea59d464b20d08c4de536fe88343e1a5544eb`，wheel SHA256 `fd8dbc471301fc7dc03b2e5ee26339048e88e3d0fed4bcfce2fa28eccbc25983`；非当前主树或后续r3。源码run-12 manifest的submission SHA256为 `c7fe0477032792d80d8ed424282e049433ee21b3cc6ef2c10fbdc9fb4323ff40`。自身模板指出的内部reader诊断修正尚待另冻r3，本表不能认证它。本次未消费仍在变化的安装兼容流程为完成结果。

本机源码与安装选集本身相差约114秒，已足以反对把178秒直接加到某次远程945秒或1166秒，从而宣布成功／失败。还有fixture摊销、远端机器、最终测试集合和安装开销未知。此处只证明新真实测量选集确有显著串行成本。

## 有完整旧测量支持的整文件候选

限定读取 `.ergora/checks/ci-training-shards/installed-py311-r1/group-5/ci-results/junit.xml` 与 `complete-summary.json`。它们属于 `b6538cf0e5026f27c1c5983aa586926a666e4788`、Python3.11.15、旧非editable wheel081aab45；539节点＝537passed／2skip，suite2444.931秒，外层2446.667秒，exit0、冻结输入结束未变。该组包含后来已移走的release／external status，不能当作当前组5总时长。

|当轮完整文件|节点数|case合计秒数|本次用途|
|---|---:|---:|---|
|`test_training_submission.py`|111|1135.248|旧正文／旧选集，不能推断现在全文件成本；不建议整文件移给group2|
|`test_training_cancellation.py`|13|170.861|可与work_agents一起5→3；直接导入submission的prepared／service及runtime installation，须保持fixture闭包|
|`test_work_agents.py`|25|162.478|首选有限候选：5→3；b653至当前HEAD正文无diff|
|`test_composition_tasks.py`|50|79.714|较小备选，亦有跨模块fixture导入；没有必要同时搬动|

现有group3在上述两次近期官方run为241／303秒，明显短于同期group5。work_agents旧完整成本约162秒，支持把已有工作从长组向短组转移的方向；**303＋162或945−162均不是新组合的预测／实测**。没有同一最终测量候选、同一远端环境的逐文件数据，不能证明只移一个文件即可稳定留足余量。

|有限候选|旧b653完整文件的case成本，只有方向意义|取舍与未知|
|---|---:|---|
|work_agents单文件5→3|25节点／162.478秒|改动最窄；新r2安装选集本机303.710秒，而较慢59b官方group5只余34秒，不能证明单文件足够|
|work_agents＋training_cancellation两文件均5→3|38节点／333.339秒|依然仅两条JSON归属变更；比单文件移出更多已有串行工作，结合833余255秒、59b余34秒，方向上更有理由给最终r3留出余量；接收组成本和最终r3新增成本仍未知|

两文件旧case和333.339秒不是可从59b／833 job线性扣除的远端节省，也不是303秒接收组可直接相加的预测。旧b653 runtime／产品、安装、节点集合与新测量均不同；module fixture开销及runner差异仍须候选自己的证据。若主控希望在最终r3发布前主动再平衡，两文件方案比单文件更合理地分散现存工作，但不构成预算保证；本报告不要求为推测追加suite、job、时限或新拆分。

已逐字核旧b653与当前工作树：work_agents SHA256 `208a002cf7c7fefecc825bb86a70cfcd9fd6529e865266ffdb414222a647a709`、training_cancellation `a97730396bfc42787e9a6dd8b18e59c5620ab1df05cb9bf01d5685a79a651142`，两者均相等。此处只核这两个文件，不声称其所有导入依赖或最终r3输入保持。

`test_work_agents.py` 的本地work_graph／work_creation为function scope，导入 `test_registrations.installation/registration`、`test_task_creation.creation_project` 和workflow定义资源；不导入其他模块测试函数。installation原为module scope，按请求模块构造，不依赖必须与submission同进程的共享对象。cancellation的submitted以及导入的prepared／service为function scope，其installation同样是按请求模块构造的module fixture；移动时可以沿原显式导入获得fixture，不需要连同submission测试收集或复制测试。两文件之间没有直接fixture／测试函数导入；观察到的结构支持各自整文件移动，尚未证明全局不存在运行组合耦合。group3已有其它registration消费者。仍须核真实fixture闭包、Linux提前skip、依赖可用性和进程收尾；静态查看不是新组合行为通过证明。

## 最小后续验证，不建立第二套检查

现有 `scripts/ci/pytest_phases.py` 按收集节点的完整文件路径选组，拒绝重复分配、缺失文件、未登记收集文件及空组选集；runner使用一个pytest子进程，无xdist。当前JSON六组文件数13／14／12／16／13／18，共86个。若只移work_agents到3，应为13／14／12／17／13／17；若两文件均移到3，为13／14／12／18／13／16。Windows all选集不因Linux归属变化。

后续实施须另取fresh独立review，不能把本报告当作approve。必要步骤是：

1. 等最终测量修正冻结，消费它自己的源码／非editable安装既定验收；保留run09／r2原成绩及限制，不为预算分析重跑这些选集。
2. 若采纳候选，只改原JSON所选一／两文件归属。使用现有runner／plugin的collector核覆盖、六组唯一、存在、无漏项；比较固定前后完整node multiset及各组归属，要求仅所选完整文件的节点5→3、总集与Windows all不变。纯JSON不改节点名，不需要旧拆分片的路径归一；不新增collector框架或测试。
3. 不因搬组无差别重跑所有本机组。针对最终候选受影响的3／5沿既定安装／CI验收消费JUnit、phase、退出码、输入摘要和原进程收尾；已有旧组完整结果只作定位证据。若官方CI承担新组合执行，应明确没有本机新组成本，而不能把旧结果移记；出现实际fixture／组合故障再补相应接缝。
4. 最终候选自己的官方六Linux job须在各自原20分钟内完成，Windows照原要求；新节点／配置与精确head、event、attempt绑定。若失败，先读原phase／JUnit确认具体节点／setup／call／teardown，再决定下一片。保持全部预算、断言和生命周期／恢复保护。

调查至此停止，没有深搜无关缓存。当前证据足以给出小候选，尚不足以认证新远端容量；选择暂不改JSON并先观察最终候选准确CI也符合现有证据。

JUnit SHA256：b653完整group5 `54b6a172f1412621ab72632f869e10e1ce025ee1f57bb91c242fe356912ea52c`；run09 `376cf499dfcd62e24d8bf2622ee4b2443e76df59b02126805f32230caf084e83`；run12 `d9ef26d1b29cf8fe2e786f454a9ad7a442156360d85368dff149d1ae10a08191`；安装r2 `e838a8ec5214c8579663033c23ad089ea76da9e760ef2ff6d9f44da27724e203`。
