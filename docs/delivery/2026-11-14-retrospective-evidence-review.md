# F10c1 完整复盘证据选择：独立审查

日期：2026-11-14。Reviewer：fresh-context agent `/root/retrospective_evidence_review`。只读检查源码、调用者和原验证材料，仅写本报告；未安装、联网、提交或重跑 suite。原始范围为[本片合同](../plans/2026-11-14-retrospective-evidence.md)，原始 F10 候选／评价／采用要求见[总分片计划](../plans/2026-11-14-evaluated-improvement.md)。按 `maintainable-project-delivery` 的独立审查要求，并使用 `review-pr`、`codebase-design` 检查。

## 最终本地判定

|审查轴|最终判定|
|---|---|
|需求符合性|**approve；开放 finding 0**。当前 F10c1 完整离线选择合同及本地验收证据相符；不扩大为完整 F10c／F10d 或发布／CI 认证。|
|结构维护性|**approve；开放 finding 0**。R1 资源放大已修并复核；测试精确读次数的过约束也已移除。原 owner 与局部复用适当，没有为调用数配额增加抽象。|

本结论基于下文的当前源码、修后包、实际 CLI、原完整输入／stdin／reply、88 件原引用与最终文档复核。初审及修前结果保留在后文，不能覆盖本节或替代修后证明。固定基线仍为 `f1cfcddd4d0e58b657b810b1f7dc98d070d255d9`；当前候选尚未提交／发布，F10b 自己的 CI 仍在途，本片自己的 CI 尚未发生。

## 初审判定

|审查轴|当前判定|
|---|---|
|需求符合性|**pending**。源码主要行为与 F10c1 合同一致；R1 需处置，修后最终包／实际 CLI／自身模板及收尾原件仍待核。此处不认证完整 F10c／F10d。|
|结构维护性|**request-changes**，一个确认的资源成本 finding（R1）。原 owner、模块归属与复用方向适当，无需增加通用框架。|

## 固定范围与候选身份

固定基线／初审 HEAD 为 `f1cfcddd4d0e58b657b810b1f7dc98d070d255d9`，分支 `refactor/architecture-foundations`。直接核 `git status --short --untracked-files=all` 和相对基线完整 diff：

- 产品：`src/ergora/handoff.py`、`src/ergora/cli.py`；测试：`tests/test_handoff.py`。
- 本片文档：`docs/PLAN.md`、`docs/USAGE.md`、`docs/architecture/current.md`；新建 `docs/plans/2026-11-14-retrospective-evidence.md`、`docs/delivery/2026-11-14-retrospective-evidence.md`。
- 同时存在 F10b 的 spec／structure review、delivery 和 evidence JSON 发布补记。已读其 diff，只有固定发布／CI 记账，不作为 F10c1 产品证明。

初审产品／测试 SHA256：

|文件|SHA256|
|---|---|
|`src/ergora/handoff.py`|`2758b58de97c85f89fc540d7be4ac4833d90787c2cd3e9539db334dc6284d2e4`|
|`src/ergora/cli.py`|`3de916165fa7ee0518da6650f9c758b889ce6968eaaabd3c0cc6fb4208756b82`|
|`tests/test_handoff.py`|`9bb17c60d9f09c4b9fe304d6a9107fced93c8aa36c73caf5e5d3f5655ccea58e`|

## 确认的 finding

**R1 · Medium · 在 1 MiB 拒绝前累积并序列化全部选择，允许显著内存放大。** 位置：初审 `src/ergora/handoff.py:246`、`:253`、`:261`、`:262`。

`evidence` 先读取、解码并保留全部所选正文，再 `_sha(result)`，之后再次 `_canonical(result)` 才检查最终 1 MiB。原格式允许一个 receipt 有 100 件产物、不同 name 共享同一个 blob；选择的 `uniqueItems` 只拒绝相同 job/name，因此 32 个不同 name 是合法输入。一个符合原 BLOB_LIMIT 的 16 MiB ASCII blob 即可通过原全包核验且只占一个 payload，随后被选择 32 次产生 512 MiB 正文字符串。首个 `_sha` 又建立约 512 MiB JSON 字符串及其 UTF-8 bytes，拒绝前的瞬时占用可达 GiB 量级。原 packet／payload 上限无法约束这种引用放大。此为源码与原 schema 可直接推导的可达成本，未执行大内存压力运行。

后果：应明确拒绝的超容选择可能先耗尽内存，且对最终最多 1 MiB 的输出付出不必要的多次大对象分配、编码和哈希成本。最小修正是在现有 `evidence` 局部，按已核 manifest 的 blob bytes 累加每个选择的正文预算，超过 MANIFEST_LIMIT 就在读取／解码前拒绝；保留最终规范 JSON 的精确检查。该前置量只是最终 JSON 字节数的必要下界，不替代转义后的最终限额。无需新模块、缓存或专用转义算法。

作者已接受此 finding，准备修后单独构建 r2；修前 r1 包与回复保留原身份，不能传递为修后验收。

## 行为与真实调用核对

- `_verified_packet` 仅由原 `verify` 和新 `evidence` 在同一生产文件中调用，复用原受限 regular-file 读取、ZIP／manifest／receipt／引用及全部 blob 核验。它是原 owner 内的凝聚算法，不靠不同生产文件调用数证明价值。`verify` 直接返回原摘要，原返回字段与语义保持。
- 新公开 `evidence` 的实际生产消费者只有 `cli.py:670`；下一片只是明确后续消费者，不计为已实现复用。离线完整读取接口隐藏 ZIP 和身份合同，放在原 handoff owner 合适；没有新产品文件、第二存储、调度器、服务、表、迁移或依赖。
- 选择 schema 复用原 identifier／name 约束；maxItems、uniqueItems、禁额外字段保护外部输入。job／artifact 缺失检查保护精确选择，UTF-8／NUL 检查保护正文合同，最终 canonical 大小检查保护完整输出。除 R1 的时机外，未见无关、不可达或已被用处充分覆盖的新增 guard；没有新增断言或兜底状态。
- 原全包核验在任何所选正文读取前完成。第二个 ZIP reader 只使用同一份不可变内存 bytes；没有重开原路径、提取 ZIP 或执行材料。同名产物通过 job_id/name 区分，保留完整 index、原 job／receipt／artifact 身份和文本，无摘要或截断。
- 输出 hash 绑定其余规范 JSON，packet／manifest／index 身份来自原核验；原失败、未知成本及原 outcome 在完整 index 内保持。`execution_success: null`、`origin_authenticated: false` 和核验范围保留，外部 SHA 不被升级为签名、质量结论或采用批准。
- `cli.main` 的 handoff 分支位于创建 State 之前，沿现有 JSON reader 和统一错误出口消费库结果；打印发生在整个读取成功之后，坏源不会输出已选前缀。`tasks.evidence`／`tasks.handoff` 原生产入口继续拥有在线索引与收集，本片不接管其运行权威。

## 检查、成本与待验范围

已读原三 suite 回归日志：首轮 `development-r1.log` 为 basetemp 父目录缺失导致 **107 setup errors／2.68 秒**，没有执行产品行为；修正私有 harness 后 `development-r2/stdout.txt` 为 **107 passed／6.85 秒**。二者路径均位于 `.ergora/checks/retrospective-evidence/`，失败未被覆盖。没有把修私有目录说成产品修复。

已查看修前 `install-r1` 的安装身份／运行记录：wheel `5fe599953d37fb8be04618e4b524407923d8eb8d8fb142fb36d52e46878b1473`，报告 577 产品文件、非 editable、两份 RECORD、283 参考文件；六个安装 suite 日志为 **130 passed／6 skipped／13.82 秒**。这些是已读的修前原运行材料，不是 reviewer 重跑，也不作为修后最终证明。

新测试沿原 suite 增量保护完整非 ASCII 正文、不同 job 同名、原失败／未知成本、同次字节读取及 CLI 不泄出部分正文。路径替换检查触及私有函数是为了验证真实 TOCTOU 风险，没有借此引入产品注入接口。三个正文拒绝用例同时保护已读成功项不会先打印；未见为普通可见失败另建大量冗余测试或默认值硬编码。R1 暴露了“最终拒绝”尚未证明“拒绝前成本受控”，需补一个小成本的别名选择预算回归。

正常成本为一次受限原包读取、完整 blob 核验，再读取所选完整正文；二次 ZIP 只解析已核内存包，原验证有的工作没有复制为第二套规则。全包扫描是原合同的必要成本。本片不涉及训练热路径、GPU 或测得性能改进。

最终复核待：R1 修正及定向结果；修后候选与非 editable 包逐件身份／两 RECORD／283；实际离线 CLI 原包读取、坏源／超容拒绝和无 State；自身原模板输入、后端、原回复与收尾；计划／交付及完整差异终核。原生 Windows、完整 F10c 候选／评价／采用／回退、F10d 页面、真实 B3、完整 Forge、F9d／G1 与 P2／P3 均不由此审查认证。发布／完整 Ref／本片自己的 CI 仍须发生后再按原流程核对。

## 修后复核与 finding 处置

**R1 关闭。** 当前 `handoff.py:249` 在每个选择上累加原已核 manifest 的 blob bytes，alias 分别计数，超过原 MANIFEST_LIMIT 即在 `archive.read`／decode 前拒绝。原全包核验已核实际 blob 大小，计数不是相信未经核实的声明。最终 `_canonical(result)` 精确限额保留；前置计数仅用于必要下界，不会拒绝本可满足最终 canonical 限额的选择。最坏所选原正文累积降为 1 MiB，原包缓冲、index、字符串表示及 JSON 转义仍有额外成本，不宣称整个进程只用 1 MiB。

已直接读 `alias-red-r1/stdout.txt` 的 **1 failed／0.34 秒**，失败点确为超预算 alias 被读；`alias-fix-r1/stdout.txt` 为 **1 passed／0.17 秒**。此定向检查使用约 322 KiB 的共享正文，不依赖 GiB 压力运行。没有新增泛化资源模块或第二套 JSON 转义实现。

**低优先级测试意见关闭。** 新回归末行原本要求 `len(reads) == 1 + allowance`，会阻止将来合法的更早整批预检。当前 `tests/test_handoff.py:213` 仅要求 `<=`，保持预算上界。已直接比较当前与 r2 安装快照，只有这一处断言放宽；安装解释器另跑当前完整测试文件内该用例，`alias-final-r1` 原记录为 **1 passed／1.20 秒**，monitor **1.624 秒**。该 copy 与当前测试 SHA 逐字相同，没有为测试意见重复安装或重跑完整 suite。

当前三文件身份：

|文件|当前 SHA256|
|---|---|
|`src/ergora/handoff.py`|`2cd20c1c4bd953f4a74948a82c4da5dab2df348ca9c392bb1c1a4dc8bc61cdcb`|
|`src/ergora/cli.py`|`3de916165fa7ee0518da6650f9c758b889ce6968eaaabd3c0cc6fb4208756b82`|
|`tests/test_handoff.py`|`23dc35b52c4753e1f6d88eaf8e28cb7407e6e89f368e76a871b688e50213b779`|

r2 整 suite 与自身模板实际使用的测试 SHA 为 `1f2f0c0594d849e5cf39185538276e66786763d84e6884e2d023c4c586214130`；原输入和记录没有被改写为当前测试身份。两份产品源码及全部 577 产品文件在此次测试放宽后保持 r2 字节身份。

## 最终原件、公开记录与收尾

1. **包与冻结身份。** Reviewer 运行一次约 0.15 秒的只读标准库核验：wheel `0157f1942bd2e605fe00c23473b9dc3ca14f5c3cbea9cfe2ba190d49f6df092c`，585 件 wheel 文件／577 件产品；577 件当前产品逐件等于构建快照、wheel 和非 editable installed。wheel 与 installed RECORD 的每个非空 hash／size 均重算通过，installed RECORD 590 行。参考 manifest 283 件逐件核 SHA256，另直接读基线 Git tree，283 个原 blob 匹配；完整 diff 无参考文件或 mode 改动。没有把作者的 `true` 字段直接当独立证明。
2. **修后安装回归。** 已读 `install-r2/regression-r1/result.json` 及原 stdout：原 handoff、下载、任务 index、架构、兼容基线、Windows 六 suite **131 passed／6 skipped／13.93 秒**；monitor **15.813 秒**、exit 0。六项跳过均为原生 Windows 项。未自行重跑 suite；当前测试的一行放宽由上述单项安装运行补充，整 suite 保留原快照身份。
3. **实际 CLI 与完整材料。** 逐件核 `native-r2/commands.json` 八个命令的退出码及原 stdout SHA；前三个离线 verify／index／selection 成功，错误外部 SHA 为 exit 2 且空 stdout，四次离线调用的 home 不存在。直接读原 ZIP，对完整 index、每件正文、job／receipt／artifact 身份与字节数、包／manifest／index SHA 和输出 canonical SHA 重算相符。原失败、未知成本、null／false 事实保持。规范 JSON 是 **60,990B**；实际缩进 CLI stdout／叶 task 都是 **62,561B**，逐字包含于 **64,960B** 原叶 prompt。交付曾把 canonical 数字标成实际输出字节，已指出并由作者纠正；原件无需改动。
4. **原输入与自身模板。** Reviewer 用最终安装件只读 `inspect_input(..., material=True)` 重新核 native 与自身两个完整 bundle：digest 分别为 `9e9d73330ef86e7153187ab6d89bc5e3a5c9fd0e27aa6cacb5f10e0ba8b8c220`、`8fd373a8c7531644e03aab8cc4215b8fb2f7b6e3f4f4c26f43c1001d02a659df`，各三件祖先资源均在 prompt。自身 r2 五完整文件 **124,685B** 的 inline 内容逐件 hash 与 packet-index 相同，**129,661B** prompt 与归档的实际 stdin 逐字相同。原结果 approve／**36.836 秒**，reply SHA `8447b8daf8ebfc99011a199b1fefb2b754edcb5000ed09e8557036ff2110a9a2`；归档 result 与原 run result 逐字一致，review.md 与原 response 相同。prompt SHA `5c2129476907a84504df80201329c6e5c25bcebaa13f5d197708cf20e9e3188c`。修前自身 r1 的 request-changes／63.528 秒保留，不能作为修后通过。实际使用用户授权 Codex 回退，此回复不作为异后端成功或 fresh-context 独立判断。
5. **引用与文档范围。** [公开摘要](evidence/2026-11-14-retrospective-evidence.json) 的 **88 个原件引用**全部直接读回，size／SHA256 相符，无重复路径；未引用私有 inference 配置。最终完整差异已核：原 tracked 十路径、新计划／交付／公开 evidence 及本报告均已纳入；F10b 四份发布补记保持独立历史范围。最终 PLAN、计划、交付、USAGE 与架构描述相符，最终审查状态留待本报告后记账，没有提前冒称已发布或 CI 成功；本片新文档链接及原件位置均可解析。
6. **过程收尾。** 八个实际 CLI 均已终态；安装与定向 monitor 成功。自身 r1／r2 原 run 都是 succeeded、returncode 0 且有 finished，现有 process owner 在 finally 等待／清理进程组。只读检查这些精确运行路径的进程命令行标记，未见存活匹配；这不是全宿主进程审计。native 旅程只做离线读取和原静态组合准备，没有启动模型、服务、浏览器或端口；自身模板调用已经结束。原包 SHA 仍为 `36089e0e7813a21d7cf2d0860e715c3542006d460f8ea480b03a44300bb8c7bb`，没有采用候选、写活动 Skill 或启动正式 Task。

最终本地范围无新增或开放 finding，两轴均 approve。剩余交付条件是 F10b CI 终态后按原授权普通发布本候选、核完整 Ref 和本片自己的必要 CI；本报告没有联网验证这些尚未发生的状态。F10c2／c3、F10d、原生 Windows、真实业务来源认证、模型质量／测得性能改善与前述其他开放工作包均保持未验边界。

## 固定发布身份补核

2026-11-14：上文保留发布前的本地验收状态，本节追加实际发布事实。固定候选为 `396e9d175cbbcd120dac29b45a2665002984a53b`，唯一父提交为原基线 `f1cfcddd4d0e58b657b810b1f7dc98d070d255d9`。本轮只读固定 Git 对象、原发布记录和原验收件，没有联网、推送、安装或重跑测试；只追加本报告。

- 直接读固定提交全部 **15 个变化 blob**，路径集合、字节数与 SHA256 均与 `static-final-r1.json` 精确一致。原报告在该固定提交内的 Git blob 为 `ab92a06638b59275d3d9e0f0d5dfebaab219c015`，本节属于发布后的补充。新增于最终清单的 F10 总分片计划与 F10b 发布／CI 补记均已读实际 diff，属于状态记录，没有增加未审查的 F10c2 产品行为。
- 固定提交全部 **577 个产品文件**逐件等于 r2 构建快照、wheel 和 installed，wheel SHA256 仍为 `0157f1942bd2e605fe00c23473b9dc3ca14f5c3cbea9cfe2ba190d49f6df092c`；**283** 个参考 Git blob 及 mode 与唯一父完全相同。因此前述包、CLI、完整输入与源码结论绑定到该固定候选。固定测试 SHA `23dc35b52c4753e1f6d88eaf8e28cb7407e6e89f368e76a871b688e50213b779` 与原 `alias-final-r1/test_handoff.py` 逐字一致；整 suite／自身模板保留 `1f2f0c0594d849e5cf39185538276e66786763d84e6884e2d023c4c586214130`，两者差异仅末行 `==` 改为 `<=`，没有把单项结果冒充整 suite 的新字节运行。
- 固定公开 evidence JSON SHA256 为 `f4c09f9a0bcbe71cf3ba144d16c4898cadfd1fe6db00d4a533081360f5f882bd`，保存 **88** 份原引用，当时 publication 为 pending。发布后工作树保存 **92** 份，原 88 份元数据逐字保持，只追加 `static-final-r1.json`、`commit-r1.json`、`push-r1.json`、`ref-r1.json` 四件。已分别读回两个集合的每份原件，size／SHA256 全部通过，无重复路径；固定提交不被声称包含发布后才有的四份引用。
- 原 commit／push／ref 三份记录均 exit 0，candidate 均为上述完整 SHA。原 push 命令为普通 `git push origin HEAD:refs/heads/refactor/architecture-foundations`，没有 force 或 main 合并；保存的 `git ls-remote` stdout 精确为该完整 SHA 与 `refs/heads/refactor/architecture-foundations`。远端结论仅限原 receipt 的 `2026-11-14T02:42:01.205550+00:00` 观察时刻，本轮没有再次查询当前远端。

F10b 自己的 CI Success 与原结构轴终核已记录，仅解除上一片发布依赖。本片自己的 CI 此时仍为 **discovery pending**，不作成功或终态主张。后续工作树产品及 F10c2a 不属于本固定候选，也不继承本片验收。

**固定发布身份补核：approve；需求／结构维护性结论保持，新增／开放 finding 0／0。** CI 原件到齐后再按同一固定候选补核，本次写入至此结束。

## 固定候选自己的 CI 终核

2026-11-14：只读补核固定 `396e9d175cbbcd120dac29b45a2665002984a53b` 自己的 [Portability run 43547736558](https://github.com/626619403/Ergora/actions/runs/43547736558)。原 `ci-run-html-r3/page.html` 的官方状态为 **Success**，完整 commit 链接及分支相符；HTTP 200 receipt 的 URL、最终 URL、字节数及 SHA256 与原 HTML 一致，观察记录为 `2026-11-14T02:59:14.868599+00:00`。本轮没有联网、调用 REST、重跑检查或读取当前 F10c2 产品来替代该候选。

已读 `parse-ci-html.py`，未执行其写文件部分；另用只读 HTMLParser 独立解析原页面，重算全部投影。`ci-ui-metadata-r1.json` 的八个 job ID／name／href／原状态，与 `ci-job-batch-r1/body.json` 完全一致。原 run r1 HTML 中的 `jobGroupsFetchUrl` 正是该 run 的官方 UI batch 路径；UI JSON 的 `totalCount=8`、`hasMore=false`，metadata 所记 run／source SHA 也与两份原 HTTP body 相符。早期 JSON 的在途状态只证明当时身份，不用来证明终态。

固定提交的 `.github/workflows/portability.yml` 与 `scripts/ci/linux-groups.json` 定义 plan、六组 Linux Python 3.11 和 Windows Python 3.12 全组，与原八个 job 页面集合完全一致。逐页核各自 `selectedJobId`／run 链接及全部必要 `check-step`：

|job|ID|必要步骤数|最后必要步骤完成时间（2026-11-14 UTC）|
|---|---|---|---|
|plan|132302867638|1|02:42:13|
|Native（ubuntu-latest, 3.11, group 0）|132302926216|4|02:47:44|
|Native（ubuntu-latest, 3.11, group 1）|132302926222|4|02:45:51|
|Native（ubuntu-latest, 3.11, group 2）|132302926250|4|02:46:24|
|Native（ubuntu-latest, 3.11, group 3）|132302926230|4|02:44:53|
|Native（ubuntu-latest, 3.11, group 4）|132302926236|4|02:44:58|
|Native（ubuntu-latest, 3.11, group 5）|132302926227|4|02:48:04|
|Native（windows-latest, 3.12, group all）|132302926200|5|02:57:04|

plan 必要步骤是 `Read explicit test groups`；七个 Native job 均包括 `Build and install wheel`、`Packaged reference identity`、`Native application regression`、`Upload regression observations`，Windows 另含 `Windows PowerShell 5.1 installer and upgrade`。全部 **30** 项都有 success、job-completed、开始／完成时间，开始不晚于完成，完成不晚于其原 receipt 观察时刻。每条 log URL 精确绑定完整候选 SHA、该 job ID 和 step number。Windows 应用回归于 `02:56:18Z`、PowerShell 于 `02:57:03Z`、观察上传于 `02:57:04Z` 完成。`ci-observation-r3.json` 的所有 job／step 投影与原页面逐项相符。

CI 原引用独立列在本节，不改写固定公开 **88** 条或发布后 **92** 条集合；本轮也重新读回 92 份原件，size／SHA256 保持。下表路径相对 `.ergora/checks/retrospective-evidence/`，body 默认是目录中的 `page.html`，只有 batch 使用 `body.json`；receipt 均为同目录 `receipt.json`。共 **11 份 body／11 份 receipt** 全部核过 HTTP 200、最终 URL、size 与 hash，表中数字为字节数。

|目录|body bytes／SHA256|receipt bytes／SHA256|
|---|---|---|
|`ci-run-html-r3`|213285／`1543deebec71ae4d5972e189f32aa6add3091d6b4b3fb053c8c7fe666c06d047`|5970／`ebe499b8c8dd2a91701cdb683ed46ba316e367f9ff3e3133e69f20f3843c38a0`|
|`ci-run-html-r1`|176263／`3bb36ae136421e8ce6ba72811be2b41746b53f595100635eea2f681b97aa323f`|5965／`aad43099bc49b93a044a1a4e9b70a1c0972014896c13d8ae774cdce0cea71745`|
|`ci-job-batch-r1`|2721／`f4ef3ba95bef12e8bcb353e8c262d183e7d84a510e7f4404240511b9d3b892dc`|766／`ce38873551925226e8ae0b87b60c75b54dfc79d9804dbbfd5aee672fac635cd3`|
|`ci-job-132302867638-html-r1`|158824／`e0d5c9ff54a07040a1ca0371a8cb85057e8706e19c8e73ddb986c104894ec0fb`|5992／`e1cf93f33a65a3989201805eb7355935f28a9591299e45ab59ae3a4ae4c99ce7`|
|`ci-job-132302926216-html-r1`|162517／`ae5b27256be7424bee997b8baa1f130a055904ee8f3e1315717b4de61d88c898`|6008／`93bf9581fd8fd494521f8cba338be3b60eec4ca16ce16589fe1dd90f3884ee41`|
|`ci-job-132302926222-html-r1`|162517／`5d4dc913e491d1bad3d95e2e9f75f0a6d379e5cdbaec5cb5f3ba86df430530cb`|6008／`84dbde42a7d0b904279e9f3cbb1d69eaad7f416e0fbace9dbd4f9a1b730ae73d`|
|`ci-job-132302926250-html-r1`|162513／`57f34d280d958815b5a6d6f3307b5092c4270300df1742e48527e4ef59533943`|6006／`0d4fe7799a208245796e434c117b971dd658047fe16847c0f3469377b310fb29`|
|`ci-job-132302926230-html-r1`|162517／`ef7a4421614f33d097bfd8b4aad66d8060b5e3b911062013ba3d1cfa99c74ed5`|6012／`69863b619da4f339a7bf0f3f048ff4325f7f2752525e1c6ac9d00df491f7dd91`|
|`ci-job-132302926236-html-r1`|162513／`ffc6fbd67b39d2273cb99e7dbaef82d1f6fee4f213995490677a0f1b929bc47e`|5998／`8b68c1612c741cb8892ea5c0ae4c777b0c61e8360d635441735abea381937e81`|
|`ci-job-132302926227-html-r2`|162004／`3eac9ff8991399fda1c1604f8285350bf7e96d8bb7d0e15d41cba87ec341adee`|6006／`322595a768c5eca4637da40193751461727de1e6762ea837d25785fc79c2a783`|
|`ci-job-132302926200-html-r3`|160098／`8ac416ce7f40cba55adce39a6aa0bd7b872e05222e2cb6f622a2ca27b0b97b58`|6004／`49e7cf1d8194984561099373b46edcdbd22a431eb364d56b519eeb5e393f9e0e`|

补充投影／解析器身份：

|文件|bytes|SHA256|
|---|---|---|
|`ci-observation-r3.json`|13357|`4f5e06c85ffeab8bc8a5fae5b05b2befbd2eb332e27c4f9182ab73ee571cffce`|
|`ci-ui-metadata-r1.json`|2125|`7f1398abebdf9fdd5cfb20e1f1b7bc6dff701304421b9fa8960cf2691974bb6b`|
|`parse-ci-html.py`|3980|`111ffdfc5c11a7ec807bba9a54472db33f1ed84d2a0c956420fce52d1345c597`|

运行级 r1／r2、Windows r1／r2 及 Linux group 5 r1 的早期在途材料保留原状态；本节采用 run r3、Windows r3、group 5 r2 和其余六个 job r1 的原终态页面，不回写历史成功。检查范围为官方 run／job／必要步骤元数据，没有下载日志正文或 artifact，不能据此扩展本地原生 Windows 支持、真实业务来源认证、GPU／训练／质量／测得性能结论。当前 F10c2 产品不属于本固定候选。

**自己的 CI 终核：approve；新增／开放 finding 0／0。** 固定候选的需求／结构维护性和发布结论保持；本轮仅追加本节，至此停止写入。
