# Q4.2a2 独立实现评审

日期：2026-11-15。评审对象为[有限候选与预算策略冻结](../plans/2026-11-15-training-cycle-selection.md)，不是 Q4.2a1，也不是设计批准的补签。

|评审轴|当前结论|开放 finding|
|---|---|---|
|需求符合性|**request-changes**|2：R1、R2，均为 P2|
|可维护性|**approve**|0 项独立结构／维护性 finding；R1、R2 仍须在本片 owner 中修正|

上述结论只适用于下列 r1 固定源码。本报告不认证后补修改、在途安装检查、普通发布、前片 CI 或本片未来 CI；本片尚未获得实现批准。

## 评审范围和依据

实施基线为 `d3c90e751ee9257df36b74e57e8956d38bbde848`。已核当前 HEAD 与此相同；固定范围为 ignored 验收目录 `.ergora/checks/training-cycle-selection/review-scope-r1/` 中的 `index.json`、`tracked.diff` 和九个完整文件。九文件的长度／SHA、固定 diff 的 SHA，以及开始评审时工作区对应文件与固定副本的一致性均直接核过。

本片生产变化只有以下三件：

|文件|r1 SHA256|
|---|---|
|`src/ergora/training_cycles.py`|`3a0f265fd9faf6013a15b87099b5e77207d9e5ea827bd8842c35a2b7bb606d2d`|
|`src/ergora/data/schemas/training-cycle-v1.json`|`7b23807dfacc96d97ebd89289aa6e53e112eba71c4d6d0d771cc96fe5bed4839`|
|`src/ergora/cli.py`|`19065fa8c2b45ff34213e845ab92c85b81fc59a26f59b6ca1733cce4bf890c5b`|

已读根、源码和测试 `AGENTS.md`、[组件变更协议](../architecture/component-change-protocols.md)、当前计划与本片计划／交付，应用 `ergora-codebase-quality` 的 repository-style、module-design、test-seams 三份 reference。逐行审阅新 owner／schema 和固定差异，沿 `training.check_start` → `reference_training_submission._Submission.preflight` → `reference._training_records` 核真实观察；必要原件包括注册封套／投影、State project、严格 JSON、目录发布及 `training_rounds` 的现有边界。没有依赖设计批准推断实现正确，也没有递归派生 reviewer。

## 实证 finding

### R1 · P2 · 离线读取没有要求完整注册和原观察的文件集合

涉及 [schema](../../src/ergora/data/schemas/training-cycle-v1.json) 第 48–55、67–76 行，以及 [training_cycles._decode](../../src/ergora/training_cycles.py) 第 45–57 行。

`plan.project.registration` 只要求是 object；`_decode` 仅访问 ownership marker。`baseline` 可以是空 object，`experiment.files` 只要求非空 object，没有要求实际原文件集合或 SHA 格式。这弱于本片“完整 project／registration、每份完整 check_start 观察与源摘要”的保存和离线验证合同。

在原公开 owner 生成的双候选输入上，分别作独立内存变体，经 public `read` 并传入各变体的正确完整 SHA，实测均被接受：

- 把注册 `files` 从四个原路径删至仅剩 marker；project、scope、execution 三份投影消失。
- 把首份观察的 `baseline` 改成 `{}`。
- 把首份观察的 `experiment.files` 改成 `{"state/unrelated.json": "z"}`；两份 manifest、spec 和 runner 的原文件 SHA 全部丢失，非 SHA 值仍通过。

这些是可达的离线输入边界：转存时遗漏、手工整理或其他 writer 生成的残缺 cycle，均可取得自己的正确文件 SHA。当前 reader 会将它们作为完整已验证输入返回。整份文件 SHA 能固定残缺字节，不能证明另行承诺的结构完整；该问题不涉及认证来源，也没有证明会绕过后继 start。

最小修正：在本片 schema／owner 要求原 State project／registration 和 check_start 的实际必要字段、类型与非可选文件集合；注册文件集合沿 `reference.registration_paths`，观察的 baseline／manifest／spec／runner 路径及原 SHA 沿已保存身份核对。保留有效扩展字段及原 legacy 等价投影语义，不另造投影发布器，不读取当前注册或原文件，也不把解析后的 JSON 重算成原文件 SHA。在现有 `test_training_submission` 离线读入口补一组删字段／删文件／坏 SHA 的反例即可，无需新 suite 或矩阵。

### R2 · P2 · 候选之间相等不能替代候选与自身原观察的一致性

涉及 [training_cycles._decode](../../src/ergora/training_cycles.py) 第 66–84 行及 [schema](../../src/ergora/data/schemas/training-cycle-v1.json) 第 77–90 行。

`_COMMON` 比较不同候选的 manifest，并比较 `baseline_files`；它没有把每份 manifest 的初始 baseline 与本份 `observation.baseline` 四元组绑定。第一个候选只成为 anchor，因此允许一个候选的情况没有该关系检查。spec 也只核 binding／URI，没有核保存的运行上限与 manifest／observation 的对应关系。

直接复核的两个独立变体，均在正确完整 SHA 下被 public `read` 接受：

- 保留首个候选与首份 admission，把 manifest 的 `baseline_id` 改成 `another-baseline`，已保存的 `observation.baseline.baseline_id` 和 experiment 的原 baseline ID 保持原值。
- 在原双候选输入中仅把首份 `spec.max_run_seconds` 改成 `1`，manifest 和 experiment 的值仍为 `120`。

原 `reference._training_records` 已明确核 spec 的 `max_run_seconds` 与 manifest 相同，原 `perfctl.baseline_ok` 明确核 baseline ID／commit／config／workload 四元组。离线 reader 返回上述矛盾输入时，没有兑现本片的“验证内部关系”承诺。后继重新准入仍然必须保留，不能拿其未来拒绝替代当前 reader 的合同。

最小修正：在每份 admission 内核 manifest 与保存 baseline 的上述四元组，并核已保存 experiment 摘要字段、spec／manifest／runner 的必要身份及限额关系；候选间的共同合同比较继续保留。只使用保存的内容，不查询 SDK、服务、Git 或当前项目，不重新授权旧 ready。沿原 fixture 在离线 `read` 入口保留单候选 baseline 冲突和 spec 上限冲突的最小反例。

## 亲自复核及已有证据

离线复现采用现存 `native-journey-r1/frozen/cycle.json`，原件为 19,967 字节、SHA `379ab6acde2be7b127697426e9c83e2c9d248f5b8f7d6be94702de0a3d5c140a`。实际调用 public `read`，仅将该路径的读取流换为内存字节，目录／普通文件检查仍走原路径，预期 SHA 使用各内存变体的完整字节。没有把变体写入验收目录或修改原件；结束时直接确认原文件字节保持。变体结果如下，便于后续精确复验：

|变体|字节|完整 SHA256|r1 结果|
|---|---:|---|---|
|仅剩注册 marker|17,989|`d6d5c4443ac2bded249daf3b8209992ecd806e33a84eca8522c8b15813912bf6`|接受|
|单候选 baseline ID 冲突|12,994|`6a10fe95a682587f3497993e29a68b6a29d4e1ea8df12d838ab06f270387fe0b`|接受|
|空 observed baseline|19,504|`962b8b50279b1b6b66a810ab560fa313c62303b6757fcd6c18f7040bb27e7a41`|接受|
|spec 上限冲突|19,965|`bb891f4392d7b0b65bf1eb3c50eaa019838a2fde0a74720ed670bfdb62ca6def`|接受|
|原 source files 丢失且非 SHA|19,468|`ce57ac2a080f33b88c233e77919c0efb1fb911535f5c32b437d836807b4c74d8`|接受|

另从固定 r1 文件装载 reader，作 13 个纯内存边界复核：bool W、float C／T、T 为 0／61、C 为 0／等于 W、33 候选、重复实验、重复 JSON key、超过 64 层、超过 100000 值和超过 10,000,000 字节，均明确拒绝；合法原输入通过。这是本地 JSON／owner 接缝检查，不是训练、服务、安装测试或完整边界矩阵。

已直接查看原记录，但没有重跑相应检查：

- `source-tests-r2` 的 XML／stdout 保留四失败、四通过；修正注册封套后 `source-tests-r3` 八通过／35.61 秒，恢复后 `source-selection-r2` 八通过／38.46 秒。通过项不覆盖上述离线反例。
- r1 package 元数据报告 core／SDK 均 645 源／wheel／安装逐字相同，wheel SHA `a4a49cbab5dccaf49dc047497d8cf8e03be13a64ed6da9719e278d228652d6a9`；两份 reference 记录为 PASS／283 参考保持。亲自另核两实际 site-packages 中本片三个生产文件均与 r1 快照逐字相同；没有重新审计其全部 645 文件映射或重建 wheel。
- `native-journey-r1.json` 记录原公开 owner 准备双合成 CPU 合同、无 SDK 安装执行创建／正确 SHA 读／错误 SHA 拒绝三条 CLI，退出码 0／0／2；47 个原文件及 DB dump 保持、空 control 目录未创建。已读取该记录和完整 frozen 输入，没有重跑旅程或逐件重新认证 47 个原件。
- 自身原结构模板 `c089fb1aefc6463188a92f547d5f73e1` 的记录为 succeeded／68.642 秒，decision 为 `request-changes`；其提出的两个情形已由本次独立内存复核确认，未把模型结论本身作为实证。
- 截止本次观察，`installed-tests-r1.xml` 尚不存在，stdout 仅有进度点；不判为完成或通过。后补结果须单独核记录及适用源码身份。

## 需求与维护性判断

已经符合且能从源码／现有接缝判断的本片边界：有序显式 1–32 候选及完整 manifest SHA、不重复实验；create 逐份调用原 `check_start` 并拒绝既有 submission，保留完整观察，检查项目 revision；候选共同合同包含数据／初态／环境／验证／质量／比较和性能政策，各自 track／allowed_changes 没有被并入共同约束；W／C／T 为严格整数且必要关系正确，T 的文档明确为原用例 timeout 上限；最终完整 UTF-8 字节与严格 JSON 边界在发布前核验；沿原 `publish_directory` 不覆盖发布。离线分支不构造 State，不读当前项目／原训练文件，不调用 SDK 或服务；coverage 明确未认证来源、未授权执行、未起算预算。

维护性方面，新 owner 隐藏了选择合同、逐份收集、内部关系和不可变保存的实际调用义务，具有真实 CLI 消费者；CLI 变化局限于传输输入及应用调用。没有新增第二套训练、证据、批准、评分、预算时钟、运行表或调度，`training_rounds` 未改且继续只做索引，Kernel 及 v3 路径未改。沿原 fixture 和既有 suite 加接缝，没有无必要的新测试文件／CI job。项目没有对这些路径配置额外 formatter／linter／type-checker，未把其他框架的风格当本仓库要求。R1、R2 的修正可局限于当前 owner／schema 和原测试入口，不需要扩大架构。

本地实现开放项为 R1、R2。安装四 suite 终态、修后自己的适用验证、自身模板与同一独立 reviewer 复核、普通发布及自己的 CI／精确终核，均按本片原门禁继续。Q4.2b／c 的重新准入、运行归属、停止、不可续期 deadline、跨恢复预算、双向 Temporal payload／history 和结果存储边界仍属后继验收；本次不要求在 a2 实现它们，也没有将本地 CPU 输入合同扩大为自动循环、实际训练、GPU、质量或收益验收。

## r2 修后复核与最终本地结论（追加）

日期：2026-11-15。本节由同一独立 reviewer 追加；前面 r1 报告的 10,923 字节全文保持，SHA 为 `378fc70f0851918260a57cc70e89342f28ddf5692c2b04d736b74e1439a0f38d`。以下结论更新本片修后状态，不撤销原实证或把 r1 通过项转授 r2。

|评审轴|r2 最终本地结论|开放 finding|
|---|---|---|
|需求符合性|**approve**；R1、R2 关闭|0|
|可维护性|**approve**|0|

范围仍以 `d3c90e751ee9257df36b74e57e8956d38bbde848` 为实施基线，修后固定件为 `.ergora/checks/training-cycle-selection/review-scope-r2/` 的完整十一文件、index 和 tracked diff。已逐件核长度／SHA 和 diff SHA；四个生产文件在本次结束时仍与固定件逐字一致。后补计划／交付记录不替代该产品身份。

|r2 生产文件|固定 SHA256|
|---|---|
|`src/ergora/training_cycles.py`|`cf8aa3ee65b1cc304fa11ee6a0471de7ff71c5e53225a3d23147b16e44722ef1`|
|`src/ergora/data/schemas/training-cycle-v1.json`|`c93425cb2bf99a6c2635459c4ec73e2eeb1da0854b388bf5f9eab8168bb99792`|
|`src/ergora/cli.py`|`19065fa8c2b45ff34213e845ab92c85b81fc59a26f59b6ca1733cce4bf890c5b`|
|`src/ergora/registrations.py`|`01e3c273e2a9bc214a2db9535ad10a7205d3015734677b4366009e4e5821e09e`|

### R1、R2 的实际处置

R1 关闭。schema 现在要求完整 project／registration 和原 admission 的必要字段、版本、类型及未启动观察；owner 要求四份注册投影与原 owner 的纯投影一致，要求 baseline、两份 manifest、spec、runner 的原 source SHA 库存及两份 manifest SHA 的绑定。没有把重序列化后的 parsed JSON 伪作原文件摘要。

R2 关闭。每份 admission 内核保存 baseline 的 ID／commit／config／workload 四元组，核 experiment 摘要与 manifest、spec／manifest／binding／runner 的必要身份及上限关系；原候选间共同合同仍保留。这个检查只针对保存内容，不调用当前准入或把旧 ready 当执行授权。

亲自从固定 r2 装载 reader，再经 public `read`、内存字节流和各变体的正确完整 SHA 复核：原五个反例全部拒绝，合法 r1 原输入仍接受。另复核十二个反例：scope 投影冲突、runner ID 冲突、manifest file SHA 冲突、缺 project bindings、缺原 job_request 标记、manifest／project／registration 版本 2、范围内 spec 上限 60 与 manifest／observation 的 120 冲突、有效 64 位 SHA 但错误 source 库存、baseline config 冲突、runner 上限超过 spec；全部明确拒绝。其中范围内 spec 和合法 SHA 变体分别证实关系／库存检查，不只是普通范围或格式检查。本次总计十七个破坏变体，原磁盘输入字节保持。

复核时把 `training._project`、`training.check_start`、`State.project`、`reference.registration_io` 替为越界即失败，合法读与所有反例仍走上述结果。原十三个预算／选择／严格 JSON 边界也在固定 r2 下重验，全部拒绝。它们是本地 owner／JSON 接缝，未运行服务、训练或额外矩阵。

### 原注册调用与维护性

已审阅本片新增的 `registrations.publication_files` 及 `_prepare`、legacy import／重复注册调用。对基线原四文件 dict 作参数名替换后，与 helper 返回表达式的 AST 一致；在原保存的 registration 上直接调用 helper，也得到完全相同的四文件投影。helper 只有纯数据投影，实际消费者为原注册和新离线校验，未移动发布、锁、journal、状态事务或恢复行为。

原 `_prepare` 对相同登记摘要保留既有 files 的分支未改，legacy import 仍以策略成员相等准入并保留原顺序／字节。独立构造非空两成员的保存策略逆序，正确 SHA 下 public `read` 接受并逐字保留该顺序；本次不是对 training-only 空列表作无效反转。原注册 suite 还覆盖了实际 import、旧字节保持、后续重复注册及恢复，见下方安装结果。

当前 schema 负责保存结构和类型，owner 负责内容之间的关系，原 `check_start` 继续负责当前准入。离线持久输入需要自己的结构／内部关系检查，不能删去后寄望未来 start；这些检查没有把整个 native preflight、执行器或批准状态机复制到本片。CLI 未因修正增添领域分支，原 `training_rounds`、Kernel 路径和执行 owner 均保持。没有发现新增的阻塞结构问题或需要新增测试文件／CI job 的缺口。

### r2 实际验收原件核对

以下均是这次直接查看或重新核对的 r2 原件；除明确写出的轻量复核，没有重跑作者的完整 suite 或旅程。

- `installed-regression-red-r1` 的 XML／stdout 为旧 r1 安装一失败／1.35 秒；新离线破坏接缝确实观测到原缺口。`source-tests-r4` 为修后八通过／35.78 秒。r1 四 suite 的六十通过仍只归 r1。
- r2 wheel 的实际完整 SHA 为 `ec11cc24535bf287556d4da39771d4d5451ca1ee081f2d32d15e92f5d4f13c5a`。亲自遍历两套 package map 的全部 645 文件，逐件核源码、wheel 条目和真实 site-packages 字节／SHA／长度，两套均零不符；四个生产文件也与固定 r2 一致。core 无 SDK，SDK 安装为 1.34.0；两份 reference 记录均 PASS／283。
- `native-journey-r2` 的双候选输入为 19,967 字节，完整 SHA `f2709a9cb42b4de4919d706f37bc88f6033f0f41530e5250af5c5692bfcaf9b1`。直接核该文件、三 CLI 保存 stdout／stderr 的摘要和退出码 0／0／2、完整读回内容；before／after checkpoint 相同，当前 47 个原文件的实际摘要及只读打开的 DB dump 均与 checkpoint 一致，空 control 目录不存在。另亲自运行一次 r2 core 的 `-I -B -m ergora ... cycle-read`，成功并返回同一完整 plan，仍未创建空 control。该脚本经原公开 owner 准备合同，未调用 start、runner、模型或服务，不声称实际训练。
- `installed-tests-r2.xml` 与 stdout 的终态为 **148 通过／304.32 秒**，failure／error／skip 均 0，只有既有 TestClient 弃用提示。七 suite 分布为 training 13、submission 21、runtime 15、cancellation 11、registrations 53、schema contracts 20、architecture boundaries 15；使用 r2 安装解释器，r2 包身份按上项另核。
- 自身原结构模板 r2 原 run 为 `6cbcb6d6ca634c35bc90687ad494d288`，succeeded／78.648 秒／approve；完整 21 文件 393,898 字节及三份祖先资源进入 stdin。其 scope 中四生产文件摘要与本次 r2 相同，`original-result.json` 实际 SHA 与记录的 `4064d443206247722ee3968dfb18248d2f36864e890aba9acdc466a8c5debcc3` 相同。模型只评审当时提供的源码／记录，本次独立原件复核不由其结论替代。

原 `build-r2` 的工具环境错误和 `self-review-r2` 的脚本引号错误仍保留；成功依据是对应 retry 与上述实际产物／run。审查自身首个快照装载脚本也曾因快照未含未变的注册 schema 而中止，随后先核当前注册源码与固定件字节相同，再正常装载并完成轻量复核；该装载错误未计作产品结果。

本片 r2 的最终本地两轴 approve、开放 0／0。普通发布、自己的适用 CI 和固定发布精确终核尚待；a1 的 CI／终核归其原报告，不转授此片。前述 Q4.2b／c、真实训练／GPU／质量／收益和完整 Forge 的独立开放验收条件保持。

## 固定发布复核与首次 CI 观察（追加，在途）

2026-11-14 22:22 UTC，由同一 reviewer 核固定提交 `1b58e929aaf495c16f448454c78de23718786ae9`，parent 为 `d3c90e751ee9257df36b74e57e8956d38bbde848`，tree 为 `f2980c9741332e580814021e78252687794054ab`。实际通过 `git show` 核 `.ergora/checks/training-cycle-selection/publication-r2.json` 的十五个 blob ID、完整长度及 SHA，集合与该提交相对 parent 的十五个变更路径完全相同；没有用工作区代替固定 Git 对象。

固定 Git 的 645 个打包产品逐件与 r2 wheel、core／SDK 两套实际安装的字节和 package map 相同，零不符；`src/ergora` 的额外 Git 条目仅为不进入包的 `AGENTS.md`。r2 原测试文件、用户手册和四生产文件均保持已评审身份，283 参考内容随完整产品映射保持。普通发布只补计划／交付和 a1 已由其原 reviewer 认证的终态记录，不包含 b1 计划／评审或实现；本次不把 a1 结论转授 a2。

匿名官方 commit API 独立返回相同完整 commit／parent／tree，官方 Ref API 返回 `refs/heads/refactor/architecture-foundations` 的完整值仍为 `1b58e929aaf495c16f448454c78de23718786ae9`；与已保存的普通 push／remote-ref 原记录相同，没有合入 main。

本 SHA 唯一适用 [Portability run 43647584681](https://github.com/626619403/Ergora/actions/runs/43647584681) 为 push／attempt1，head SHA、branch 和 `.github/workflows/portability.yml` 均与固定发布相同。首次直接 GET 官方 run、jobs 和页面的观察时间为 **2026-11-14 22:22:43 UTC**，HTTP 均 200；run 为 `in_progress`、conclusion 为 null，plan 成功、六个 Linux 分组及一个 Windows job 仍在运行。完整八 job 的 run／SHA／attempt 身份无冲突，按固定 workflow 的三十个适用必要步骤计算，当时二十二项成功；未将尚未执行的步骤或在途 job 计为成功。

|首次直接 GET|响应字节|正文 SHA256|
|---|---:|---|
|本固定 commit API|127,935|`d1a1ae71e3d385e6a179abde3870eecce481324cea76a7ba6e163a8859d79dd3`|
|完整 branch Ref API|429|`621ffe9420aedf098788b858048d1fb12aeacd2406c31ba7b9310ff92e79035b`|
|本 SHA 的 runs API|11,995|`41de2e8ade0b1a6b174f0bafdae72f18470e5742a99682ea8e597de1c33edae3`|
|本 run API|11,959|`20193a7c2ad41b95f3c77a8dc62549ea599a9fa0c7ab7069f37ddb085d28623b`|
|本 run 的完整 jobs API|18,545|`5f25c5fdc7f24bfa01c84c37c46c06180e446ef5bf936c048b0fe0bb29c903e2`|
|官方 run 页面|159,012|`a9eb606bfa0c55be7c18887118193727d6bce3c9094ce41d4df29c0cb6183e8a`|

GET 来源复用原 a1 collector 的匿名官方接口模式，本次直接读取内存中的响应并记录上述时间／状态／摘要，没有写其他本地文件。固定发布两轴继续 approve，实现 finding 仍为开放 0／0；精确交付尚待 **本 SHA 自己的 CI 终态**，在途观察不是终核通过。

## 本 SHA 自己的 CI 终核（追加，已闭合）

**最终结论：需求符合性 approve／可维护性 approve，新增 finding 0，开放 0／0。** 同一 reviewer 于 **2026-11-14 22:46:09 UTC** 完成匿名官方 API、run 页面及八个官方 job 页核对：[Portability 43647584681／attempt1](https://github.com/626619403/Ergora/actions/runs/43647584681) 为 `completed / success`。run 的完整 head SHA 为 `1b58e929aaf495c16f448454c78de23718786ae9`，push 事件、branch、workflow 路径和全部 job 的 run／attempt／head SHA 均无冲突，八 job 及三十个适用必要步骤全部成功。

|官方 job|job ID|必要步骤成功数|终态|
|---|---:|---:|---|
|plan|132608699436|1／1|completed／success|
|Linux group 0 · Python 3.11|132608733233|4／4|completed／success|
|Linux group 1 · Python 3.11|132608733231|4／4|completed／success|
|Linux group 2 · Python 3.11|132608733189|4／4|completed／success|
|Linux group 3 · Python 3.11|132608733200|4／4|completed／success|
|Linux group 4 · Python 3.11|132608733173|4／4|completed／success|
|Linux group 5 · Python 3.11|132608733267|4／4|completed／success|
|Windows all · Python 3.12|132608733169|5／5|completed／success|

必要步骤直接依据固定提交的 workflow／六组配置核定：plan 的显式分组读取；七个 native job 的 Python 设置、wheel 构建安装、打包参考身份、应用回归；另加 Windows PowerShell 5.1 安装与升级。逐个解析已保存的八个官方页面，三十项均只有一个匹配步骤、conclusion 为 success 且完成时间非空，与官方 jobs API 相同；没有把上传观察、收尾或非适用步骤凑入三十项。官方终态 Ref API 仍返回完整 `refs/heads/refactor/architecture-foundations = 1b58e929aaf495c16f448454c78de23718786ae9`。

此前在途事实继续保留：22:22:43 UTC 为二十二／三十；22:32:44 UTC 的另一次完整官方观察为六 Linux＋plan 成功、二十八／三十，Windows 两项尚未完成；22:44:46 UTC 的 Windows 页确认应用回归成功，22:45:32 UTC 确认 PowerShell 步骤也成功。最终 API／页面采集发生在这些观察之后，未倒填早期状态或借用 a1 的 CI。

后获明确落盘授权，后续只读采集器、响应正文及对应 URL／UTC／HTTP／SHA 清单保存在 ignored 的 `.ergora/checks/training-cycle-selection/ci/`；原先内存读取的六份响应没有追造正文。精确证据索引为：

- `reviewer-collector-provenance-r1.json`：三个采集／验证脚本来源于原 a1 实际脚本，只替换本 commit、run、Windows job ID；未复用其观测结果。
- `reviewer-observe-r1/`：本片自己的二十八／三十在途 run／jobs／官方页与明确未通过终核的 validation。
- `reviewer-windows-observe-r1/` 至 `reviewer-windows-observe-r26/`：仅监测原固定 Windows job 的完整官方页、元数据及步骤观察，不重新抓取每轮完整 API／全部 job。
- `reviewer-terminal-r1/`：终态 run／完整 jobs／run 页、八个官方 job 页、最终完整 Ref、各自 HTTP200 元数据及三十／三十验证。
- `reviewer-ci-terminal-r1.json`：完整独立终核汇总，**62,353 字节**，SHA256 **`a07eb41afcf26945cd0ce5709b27e7d0b43ddedd21b8aee9df69ad35a1ec39b0`**。其 117 件原件清单不含汇总自身，逐件核字节／SHA；索引的 41 次原始 GET 均为匿名 HTTP200，正文与元数据完整匹配。汇总同时绑定固定 commit／parent／tree、十五 blob、r2 wheel 身份、八 job、三十必要步骤和终态完整 Ref，violations 为空。

发布时原评审的 18,361 字节前缀仍逐字保持，SHA 为 `12a27cf60adf6c429b1d3ca4f0b757c1703177cc66c624dd82036b63d29e655a`；更早 r1 全文和原失败均保持。提交前 staged diff 与实际 parent→本提交 diff 也逐字相同，SHA 为 `10be1711ea788b147cf9ffe69effd784142e293c074a46c2d9d6f4f0ce277c30`。终核不读取后继工作区充当本片源码，没有重跑产品 suite／模型，也没有修改源码、配置、安装、服务或推送。

Q4.2a2 固定发布 `1b58e929aaf495c16f448454c78de23718786ae9` 的精确交付门槛已闭合。该结论只归本片；Q4.2b1 及后继提交／预算／停止／自动循环和真实训练验收继续使用各自合同、候选、适用 CI 与独立评审。
