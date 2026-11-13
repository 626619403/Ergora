# F9b4b 原可信 runner 登记：独立结构与维护性评审

日期：2026-11-14。评审员：fresh-context 独立结构轴 `runner_structure_review`。未继承实现对话；先读项目 `AGENTS.md`、maintainable-project-delivery 的独立评审要求、codebase-design、[原验收合同](../plans/2026-11-14-training-runner.md)，再读候选代码、原 owner 和相邻消费者，最后对照[作者交付](2026-11-14-training-runner.md)及保存的检查记录。本次只读产品／证据并写本报告，未安装、运行 suite、浏览器、模型或服务，未改产品、提交或推送。

**当前结论：结构／维护性、精确发布身份及本片自己的 CI 独立终核通过，开放 finding 0。** 固定候选 `80236fe8957c0704a3c73c7ea1440f7f288ff563` 的本地安装／交互／原件／自身、普通推送与完整 Ref 已核；自己的 CI `43523861953` 为 Success，八 job／30 必要步骤终态已由本轴直接检查原 HTTP／HTML。所查需求符合性也无额外 finding，完整需求轴另行记录，不代称其另做 CI 终核。runner 仍只支持 Linux／WSL2；真实训练／GPU及质量／性能继续保持原未验范围。以下保留各轮身份与当时待验状态，当前补核见末节。

## 固定身份与实际查阅范围

基线及查阅时 HEAD 均为 `fe26796a54b3804aac9272a9ea86643320a7f0b3`，分支为 `refactor/architecture-foundations`，候选未提交。查阅完整 tracked diff 及三份新文件全文；首轮 `static-review-r1.json` 为 3,509B、SHA256 `c10a18e2b65ed5f0a2bb521dc2d5beb1bd4356c0110f0f06ced12a1c0fad4ad6`。本轴逐件重读并独立复算清单所列 17 件长度／SHA，全部相符；按原脚本的路径＋NUL＋原字节＋NUL 算法重算八件产品／测试／CI 组合 SHA 为 `43634fafdf354cb60f212face64c28caa27e7d5f0979c32362dacfcf64f8f583`，与清单一致。

|产品／测试／CI 路径|字节|SHA256|
|---|---:|---|
|`scripts/ci/linux-groups.json`|3,417|`dd1e00a876eb1dcda6da41e8c49fa2aebe4ec1d5d997656b533b180f1bad6f63`|
|`src/ergora/cli.py`|72,178|`98d91f0fea67e7b81793c9c3f900768346e5fca1392afdfc3dabf2c1d0aba44c`|
|`src/ergora/data/console/training.js`|17,741|`48608648884a10e2036e595b8db53864459faa18935c9d164f0dcf0cd7774793`|
|`src/ergora/reference.py`|44,518|`c4034b8f619365a5044aa3f6d0b1c601de40145c7260e20789a224d230ce0ea4`|
|`src/ergora/reference_training_setup.py`|8,021|`d5925312331160d10dcbadaafe43b093c6d27e655c1bfe018d7542191ef191ff`|
|`src/ergora/training.py`|10,790|`c8f29467a4e8f9f3c04dd66a89d98ec688c218d85a8f9bed1e4e78c7bcdcff1c`|
|`src/ergora/web.py`|41,673|`be84d0092d26e2a007b2faa4255a7ece80b0cef215738eede31e909a5676b2c6`|
|`tests/test_training_runner.py`|10,421|`3e557af8d22e86917fb40a3457cb09ee3819dd53b2e60654c3147e598d8a39a1`|

另九件为 `README.md`、`docs/PLAN.md`、`docs/TRAINING.md`、`docs/WINDOWS.md`、`docs/architecture/current.md`、F9b4a 的需求／结构评审记账及本片计划／交付。旧片发布补记与本片功能证据分开。上述身份绑定首轮快照；后续计划、交付和评审状态更新不自动改变该产品身份。

相邻代码实际查到 `_TrainingProject` 的注册／路径校验、`reference_training_submission.preflight`、原 `agent_platform.training.register_runner / prepare`、原 `core.write / git / slug`、`dev_platform.adapter.safe_file / read_raw`、控制台 `ui.node / button` 与 `api`、原 baseline 六用例、训练观察／提交测试、现有 fixture、CI 分组消费者及 portability workflow。

## Findings（按严重度）

所查范围内无可证实的 P1／P2 或其他必须修改的结构、维护性 finding。以下是形成该结论的源码依据，不是以测试通过替代评审。

## 所有权、真实消费者与抽象深度

- [training.py](../../src/ergora/training.py) 的 `preview_runner / register_runner` 分别由 CLI 与 HTTP 两个实际产品文件调用。它们把选定项目、修订和确认内容送入同一原执行路径，没有另立 runner 注册库、调度、批准或训练执行权威。`_setup` 是同文件 baseline／runner 发布共用的私有算法，集中短本地 DB 预留及 revision 校验；删除后会在两条真实发布路径重新出现相同生命周期代码，有明确 Locality。
- [reference_training_setup.py](../../src/ergora/reference_training_setup.py) 第 23、70 行的 `_baseline / _runner` 各只有同文件分派调用。它们分别封装两种不同原发布算法，属于内聚私有算法，未为单次委托增加公开 Interface。`_native_bytes` 集中两种文档实际共用的序列化／容量工作，供 baseline 输入、runner 输入和规范化 runner 发布三处使用；没有另建通用 codec、插件注册或可替代执行框架。
- `_runner` 第 85–94 行只改当前隔离子进程中原训练模块的 `CONFIG`，以 `try/finally` 恢复。预览直接运行原 `register_runner` 写临时目录，再读取原 serializer 的结果。第 114–115 行用规范化文档调用同一原函数发布真实目标；字段集合、argv、Git 根验证及 timeout 算法仍由原 owner 执行。
- [training.js](../../src/ergora/data/console/training.js) 第 26–91 行的 `setupDocument` 有 baseline 与 runner 两个实际局部使用者，共用预览、内容确认、禁用、异步失效和失败恢复的生命周期。`kind` 分支只描述这两个文档的路径、字段和文案，没有把两种原生发布实现搬到页面。HTTP payload 类和路由是既有框架 Interface 的扩展；CLI 只解析输入、限读并调用应用层。

## Guard、失败处理与耦合

|位置|可达失败及保护作用|
|---|---|
|`reference_training_setup.py:74–81`|外部 JSON 不是对象，或指向其他已注册项目／Git 根；原登记器不认识控制层选定项目，需在此绑定。原 `schema_version == 1` 会接受 `True`，相邻正式 submission 第 63 行却要求真实整数，新增类型检查防止成功登记随后不能提交的文档，没有复制原字段算法。|
|`reference_training_setup.py:16–20`、`cli.py:929–932`|原始 CLI 文件与序列化文件是不同容量对象；前者的空白不会被解析后检查发现，后者须能被实际 1 MiB reader 读取。两处不是重复检查同一不变量。规范化 repo 可能增长，真实发布前再次检查规范化字节也有具体消费者依据。|
|`reference_training_setup.py:96–106`|发布确认必须匹配规范化完整内容 SHA；目标须经原 `safe_file`，已有同 ID 外项目文档在返回 `current_runner` 前拒绝。错误只含通用占用说明，不返回外项目命令。|
|`reference_training_setup.py:108–119`|预览本来需要计算已有内容状态；发布消费同一结果给出新 reviewed ID 的可操作错误，最终并发不可变性仍由原 `core.write` 的 `os.link` 与 canonical 比较拥有。发布后读取并核 SHA 保护回执所描述的真实持久内容，不承担第二写入协议。|
|`training.py:122–131`|HTTP 之外的应用调用也可能传布尔／旧 revision，原生 owner 不知道控制 DB 修订；因此在应用层短本地预留内校验。此处无 Temporal RPC；原 Git 子进程仍由既有 process owner 的超时／终止组管理。|
|`training.js:35–81`|编辑递增本表单 sequence；回复须匹配 active project、tab、control home、sequence 和原文本。发送前同步设置 `sending` 并禁用控件，因此双击不会并行发布；切项目后迟到回复不更新新页面。失败保留源文本并要求重新预览。JSON parse／确认 SHA 的异常由既有 `ui.node` 的同步／Promise handler 显示，没有吞掉失败。|

`reference.py:367–371` 将 runner 预览／登记限制在 Linux／WSL2 且需要可选 SDK，与原训练模块的 `fcntl` 和 Temporal 导入相符；baseline 分支仍 `sdk=False`，未新增 SDK 导入到其执行分支。没有发现私有机器、实验、数据集或固定 argv 进入可复用逻辑。原生 Windows OS、Temporal 服务可达性及真实 GPU 均不由这些静态观察证明。

## 测试与 CI 的价值

新增七个测试通过公开 training／CLI／HTTP Interface 触发真实原登记器，不 mock 字段算法或另写一个预期 serializer。marker argv 检查误执行，前后文件字节及内容 SHA 检查真实不可变性；错误 SHA／旧 revision、同 ID 变命令、发布后丢回复、共享 config 的项目归属和 symlink 逃逸均有静默破坏风险。失联后的同内容并发测试保护恢复稳定性；不能据其单独宣称已经实测两个竞争首写者，但原 writer 的原子机制已查源码。

容量／布尔 schema／walltime／注册漂移测试包含普通可见错误，但它们同时保护“不可发布不可消费文档”或原件不变的外部合同，规模有限；没有足够证据建议为删行而拆删现有覆盖。测试使用临时 repo／config 和真实配置值，未把特定机器路径或默认维度当算法不变量。

`scripts/ci/linux-groups.json` 只把新 suite 加入已有第六组一次；既有 phase plugin 检查全部 collected 路径均有且仅有一个归属，workflow 安装 temporal extra。没有新增重复 job、默认值断言或另一套 CI 协议。原 baseline 回归有实际理由：本片同时改了其 CLI 参数共享、原 setup 函数位置和公共页面生命周期。

## 已做检查与剩余材料

本轴执行的检查只有只读源码／diff／调用者读取、17 件字节与组合 SHA 复算，以及 `git diff --check`（退出 0）。`source-r1-final.json` 记录源码三 suite 共 27 passed／45.25 秒；已读实际命令及保存的局部工具输出，原文件明确把这项称为 observed source invocation completion，本轴未重跑，也未扩大为安装包或 Windows 结果。

`install-r1/source-manifest.json` 已读，八件产品／测试／CI overlay 身份与本轮一致；其计划／交付 overlay 比首轮状态文档更新，属于正常记账范围。发现的 package-identity 文件只视为待核证据入口；安装回归、实际 CLI／页面／SDK-free、原件保持／收尾、自身模板与公开证据仍待作者给齐原件后同片补核。还需本片普通精确提交、远端完整 Ref 和自己的 CI；F9b4a 的发布或 CI 不能关闭这些条件。

**本轮没有产品修改建议，也没有阻塞性结构 finding；未完成的验收材料保持开放。** `prepare` 多件发布／恢复、F9c／F9d、原 evidence SHA 批准／采用、真实训练及 GPU 的责任范围继续沿原计划。

## 最终本地原件补核：通过，开放 0

本次仍仅阅读原件、复算字节及 SHA，并更新本报告；没有运行 suite、浏览器、模型、服务或远端操作。固定 HEAD／基线保持 `fe26796a54b3804aac9272a9ea86643320a7f0b3`，八件产品／测试／CI 组合 SHA 仍为 `43634fafdf354cb60f212face64c28caa27e7d5f0979c32362dacfcf64f8f583`。追加前，独立复算 `static-local-final-r1.json` 的全部 20 件均一致；该清单为 4,427B、SHA256 `b62f238ad4a5d2fc8580f5464d4d1a04ef93276e9951e011ea34720364858df3`。本报告随后追加属于评审记账，不改变受测产品。

**安装身份与必要回归。** 独立打开 r1 wheel 并逐件比对当前 `src/`、构建快照、wheel 及真实 site-packages：570 件产品字节全等，wheel SHA256 为 `8d53c60ee378fecfdbbb994cbe174e6eda5657211bcede3fe46050ce59222860`。两份 RECORD 的每个有摘要条目均重新核长度／SHA，wheel 578 行、安装 583 行；283 件冻结参考文件逐件符合 manifest。安装元数据的 direct URL 为该 wheel archive，没有 editable 标志。读取完整 regression argv、stdout 和空 stderr：runner／baseline／原 training 观察／架构四 suite 实际 40 passed／65.54 秒，monitor 67.543 秒，退出 0；与源码首轮 27 项明确区分。

分组 5 的原 CI plugin argv 含 `--collect-only`，phase 原件只有 identity／coverage／partition／collected／finish，没有执行测试事件；选中 364／全部 1817、1453 deselected。分组文件 SHA 与本轮产品相同，新 runner 七用例只有该组的一次归属。公开记录将这项称为收集检查，没有把它写成 364 项通过或本片 CI 成功。

**真实 CLI 与 SDK-free。** `native-r1.py`、四次真实安装 CLI argv／退出码／stdout／stderr已逐项对照：预览为 `not_registered`；错误 SHA 退出 2 且检查点未创建真实 runner registry；登记为 `registered`；重试为 `already_registered`，两者文件字节 SHA 完全相同。返回规范化 repo 和完整 canonical SHA 与真实原文件一致。SDK-free 检查以真实 `-P -S` 子进程加载安装包，代码在执行前后检查找不到 Temporal，且 sys.path 无 site-packages；保存的 stdout 为首次 `initialized`，stderr 空，目标 baseline 与原输入全等。这里证明受影响 baseline 初始化分支可在该无 SDK 进程工作，不冒称 Windows OS 实测。

**实际页面与异步生命周期。** 已读 runner／lifecycle／baseline 三组完整脚本、工具退出记录、stdout 内原结果及服务器 `requests.jsonl`。延迟和丢回复分支均先 `route.fetch()` 取得真实服务器回复，再 hold／abort；没有用合成成功响应代替真实发布。将 stdout 中 runner 初次登记、丢回复前登记、切项目前已成功登记及 baseline 初始化四份完整 receipt 重新序列化，其长度／SHA 各自精确匹配服务器捕获的一份 HTTP 200。服务器记录也保留首次与重试两次 loss-contract 登记、browser-contract 的一次双击登记、slow-contract 的一次真实登记及 baseline 的一次双击初始化。

三组原结果均 passed，涵盖错误 SHA 零 POST、编辑后迟到预览、切项目后迟到预览／真实登记回执、真实写后丢回复再预览原件及同内容显式重试、同 ID 不同内容无替换按钮，以及共享 config 外项目 ID 的 400 且不含命令。1440／960／390 三种布局结果均无横向溢出；另有 390 未发送表单。独立查看了保存的 390 未发送表单与 960 冲突截图，控件与完整原 JSON 展示符合记录。console 恰两项：刻意 abort 的登记回复和外项目 ID 的 HTTP 400；默认 Chrome 缺失的最初 open 退出 1 原件保留，之后 `open-r2` 沿已有浏览器配置退出 0，没有产品修复或新增平台支持主张。

**原件与收尾。** 不只采用 final-observations 的布尔值：逐件重算 `protected-before.json` 所列 32 份原件，全部保持；四个 runner 原文件与各自规范化输入全等，两个 baseline 与原输入全等。真实目录中只有这四个 runner，其他三个项目未登记 runner；runtime 的 training 目录仅有 projects，没有 manifest／spec／job／fence／approval／integration-ticket，marker 不存在。只读 Git 查询确认验收 repo clean。已读 browser close 原回复与原 monitor 的 web group cancelled／-9 记录，并只读 `/proc/net/tcp{,6}` 确认保存的原端口无 listener；未另启服务或发送网络请求。

**自身模板与公开交付。** 已读原 `ergora-structure-review` 调用脚本、完整 packet index、prepared input、实际 run input／stdin 和原模型结果。10 件完整内联文件共 214,529B，逐件按实际 task 中的字节切片重算长度／SHA，八件产品与当前候选一致；两件计划／交付属于模型调用时的首轮状态。三份祖先／叶资源、叶 prompt 和原 task 均在实际 stdin，prepared prompt／run prompt／stdin 逐字相同，prompt SHA 为 `0b2820733ef2325f080e924a7268e1eda91c6f527f91f83de5db8b98c7de3d97`。原模型结果与 run result 字节相同，SHA256 `b972a28c8ff913ff8d43e129da4eb98af8859a6749d383e80162a49f536b32d0`，approve／53.359 秒。原回复明确未获得未内联 native owner 的实现，且当时运行证据在途；本报告没有把这份局部自身审查扩大成独立完整审查，也没有称其异后端成功。

本轮[公开证据](evidence/2026-11-14-training-runner.json)为 7,966B、SHA256 `7ad999676b6294e2a3690aa1d128288b21bdba47caf7193fa35cc6409593b260`；引用的 30 份私有原件全部独立复算长度／SHA 相符。其实现、安装、页面、自身和未验范围与原件吻合。之后常规更新独立审查状态不应被当成新产品重测。

**最终本地结构／维护性与所查证据通过，开放 finding 0。** 无需产品修改或额外 guard／抽象／测试。剩余为本片普通精确提交、完整远端 Ref 与自己的必要 CI 固定身份补核；不借 F9b4a 的 CI 关闭本片。F9b4c prepare、F9c／F9d、真实训练／GPU、质量／性能、证据批准／采用和原生 Windows OS 实测继续保持原责任范围。

## 普通发布与完整 Ref 补核：通过，自己的 CI 待验

本轮仅从固定 Git 对象和保存的发布原件读取产品身份，没有读取下一片产品工作树，也没有运行 suite／服务或发出远端请求。候选为 **`80236fe8957c0704a3c73c7ea1440f7f288ff563`**；直接读取 commit 对象确认唯一父提交是原基线 `fe26796a54b3804aac9272a9ea86643320a7f0b3`。父→候选实际恰有 23 个改动路径，与 `static-final-r1.json` 的完整集合相等；逐件以 `git cat-file blob CANDIDATE:PATH` 复算长度／SHA，23 件全等。

八件产品／测试／CI 按固定 Git blob 重算的组合 SHA 仍为 **`43634fafdf354cb60f212face64c28caa27e7d5f0979c32362dacfcf64f8f583`**。将原 r1 wheel 的 570 个产品条目逐字对照候选 Git blob，全部一致，因此原本地包、安装回归和真实交互证据仍绑定同一产品。该提交内本报告为 16,697B、SHA256 `d96006ac58634480d6e4668919cd70c9d73732af992cd5ccab42b953e8c9aa76`，恰为前述最终本地通过报告；之后补记不改变候选。

对两个固定提交运行 `git diff --check`，退出 0。以候选 Git tree 解析改动 Markdown 的 245 个本地链接，全部存在；23 个改动 blob 未含原检查列举的私有机器字符串。候选内公开证据为 8,173B、SHA256 `c2df66a9b8a714779bcc2d4e372bb09d0025534420038d2588e97a3764d37e91`，所引 30 份私有原件长度／SHA 再次逐项匹配。其 `publication: not_committed` 与发布／CI pending 是提交前记录，本节补充其后的实际发布事实，不把旧状态改写为当时已完成。

已读 `commit.py`、`publish.py` 和三份发布原件。提交脚本约束固定父提交、开发分支、精确 23 个 staged 路径、完整 staged whitespace 检查及提交后 Git blob 匹配；保存的 commit 退出 0，记录同一完整候选。原普通 push 目标为 `HEAD:refs/heads/refactor/architecture-foundations`，没有 force／mirror 或 main 合并参数，退出 0，原回复记录 `fe26796..80236fe` 前进。之后原 `ls-remote` 退出 0、stderr 空，stdout 精确为该 40 位候选与完整 `refs/heads/refactor/architecture-foundations`。远端结论绑定这份实际回执的当时状态，没有额外查询当前远端。

|发布原件|字节|SHA256|
|---|---:|---|
|`static-final-r1.json`|4,938|`5b68aae6a5ae6db4e4d616d246b96e201f79cb35552215688e4be1c5aefac409`|
|`commit-r1.json`|949|`a248c55525fbb11b41d9cc98e350ecd5f4d272c9a84f0e7e075968d7e1754514`|
|`push-r1.json`|750|`90bf3f156226d46b28f3e3e8ce474b2cb9cacd98376486d6105a05d82b16d281`|
|`ref-r1.json`|738|`47c2cbe39f1d775f47d841bd6d4d3395400776c032634d5eeea34c55950f331f`|

同提交的 F9b4a 交付／评审／公开证据及准备总计划更新只记录旧片自己的发布／CI，不是 runner 产品变化或 runner CI 成功。**本片精确产品、普通发布及原完整 Ref 补核通过，结构轴开放 0；本片自己的 CI 尚待发现和官方 run／必要 job／step 终态原件。** 下一片 prepare 及既有未验平台／GPU责任范围均不由本次发布补核关闭。

## 本片自己的 CI 独立终核：通过

本轮继续只读固定 `80236fe8957c0704a3c73c7ea1440f7f288ff563` 的 Git 对象及保存原件，没有读取下一片产品工作树，没有发出远端请求，也没有运行 suite 或服务。[本片 Portability run 43523861953](https://github.com/626619403/Ergora/actions/runs/43523861953) 的第三份官方 run HTML 为 **Success**。本轴直接重算该 `page.html` 的 213,287B／SHA256 `410a3e3d8aa7784100812bb7ab94602bf166489191b36ac8fb07ba4d2fea47f6`，与同目录原 HTTP 收据相符；请求 URL、final URL 均为该精确 run，HTTP 200，页面含完整候选 commit 链接及开发分支。

没有用 `ci-terminal-r3.json` 的布尔结果替代原页面检查。先核原 job batch 的 HTTP 200、完整 URL、2,733B 及 SHA256 `6698fcd0f6117950767ba8cc79843fcca8507f9ef19cf15ab602fa93b5891e4b`，直接解析 `jobGroups`：totalCount 为 8、hasMore 为 false，八个 job 名称／ID／run 路径与 metadata 逐项相同。metadata 引用的首轮 run SHA 也对上其保存原页及完整 commit 链接。首轮 batch 的 Windows 状态仍 in_progress，只用于识别原 job，不作为终态证据。

从固定候选的 `.github/workflows/portability.yml` 与 `scripts/ci/linux-groups.json` 读取真实预期：六 Linux 分组、plan 和一个 Windows all，分组配置 SHA256 为 `dd1e00a876eb1dcda6da41e8c49fa2aebe4ec1d5d997656b533b180f1bad6f63`。随后分别直接解析 plan／六 Linux 的 r1 原 job HTML，以及 Windows 的 r3 原 job HTML；九份最终 run／job 页的 HTTP 状态、请求／final URL、原字节长度及 SHA 全部核对。

30 个必要步骤为 plan 的 `Read explicit test groups` 一项，加六 Linux 各四项，以及 Windows 五项：构建安装、参考身份、原生回归、上传观察，Windows 另加 PowerShell 5.1 安装升级。每一项均直接核到 `data-conclusion="success"`、非空开始／完成时间、时间先后正确、`data-job-completed` 标记，以及精确 `/626619403/Ergora/commit/80236fe8957c0704a3c73c7ea1440f7f288ff563/checks/JOB_ID/logs/STEP` 路径。未接受短 SHA 或只显示成功却缺日志路径的状态。

|job／原 ID|原 HTML 字节|必要步骤|最后必要步骤完成（UTC）|原 HTML SHA256|
|---|---:|---:|---|---|
|plan／132224632469|158,829|1|23:01:09|`94fb0b8bbe9a6380d347b740750788647c47705fc85670acb83f060e94e93ed1`|
|Linux group 0／132224701507|162,520|4|23:05:38|`1ee294a06f7b9982c150270fb44419c3606776dea94ef6bdfdcfba7e04325e5c`|
|Linux group 1／132224701569|162,519|4|23:05:15|`c327c79e74e2b8181c8dcbcf479143cd91db53902cbc2ff862c447a86d1c8f4c`|
|Linux group 2／132224701543|162,520|4|23:04:50|`fe69aca64d41b81b4b6068656f953b1f14fa21e9b886a65b64e9658aebd6f08d`|
|Linux group 3／132224701511|162,519|4|23:03:38|`553934aeffbae2a68f19bda14db5fbc1b5b34fbe8c081d299012efe6ddab9654`|
|Linux group 4／132224701514|162,519|4|23:04:27|`d790b3a985f738412195a4a354a71cd2111016902b37f3757323885e4b932f4f`|
|Linux group 5／132224701454|162,524|4|23:06:36|`d59f61ee2f379576e0e0dae10a16f1b45e137cfeda8fb3ea56b80a8090c4b229`|
|Windows all／132224701578|160,100|5|23:16:34|`5c5f6f90655466336e2e9842025228ce409caafc034c2d11a5965dd201d405b1`|

表中时间均为 2026-11-13。Windows 原生回归于 23:15:44 完成，PowerShell 5.1 安装升级于 23:16:33 完成，上传于 23:16:34 完成；均早于最终原页抓取。其 r1／r2 原件仍是回归及后续步骤未完成、无完整日志路径的在途状态，已保留；r3 提供终态，没有放宽条件。独立解析所得八 job／30 步及各 body SHA 与作者终态 JSON 相符；该 JSON 为 13,357B、SHA256 `4b5541994df0e0a9d3048e154eeb64a373766eff6d820e72c8acc13addc3e2dd`。

**本片自己的 CI 固定身份与必要步骤终态通过，结构轴开放 0。** 该结论覆盖官方 UI HTML 所呈现的 workflow／job／step；没有声称另取 REST 结果、下载 artifact 档案或读取完整测试日志。Windows CI 成功不改变 runner 的 Linux／WSL2 支持范围，也不把 CPU 合同当成 GPU、训练质量或性能验收。原发布／完整 Ref／23 个 blob／570 包文件的精确绑定沿前节保持；没有借用 F9b4a CI，也没有代称需求轴另做本轮 CI 终核。
