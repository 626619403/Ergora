# B2f 模型配方／模型验证独立审查

日期：2026-11-13。审查协调者为新的 fresh-context `model_directions_review`，另启 fresh-context `spec` 与 `standards` 两轴；两轴不交换判词。应用 AIHERO 索引对应的 code-review、maintainable-project-delivery 和 codebase-design。审查只读源码及保存原件；没有安装、运行测试／模型、请求网络、修改产品或执行 Git 发布。自身结构模板的判词不作为独立结论。

## 候选与范围

固定 baseline／HEAD 均为 `83000a1afbdbd2429efbcebe1e7c65133215ca8e`，提交列表为空。比较命令为 `git diff 83000a1afbdbd2429efbcebe1e7c65133215ca8e --`，另含全部新文件。r2 冻结十四文件清单 SHA256 为 `4616374f00e7a4aab76b5f820b5e96ee2c4a64186b1ab6e308c89e2a515092b9`；完整证据到齐后的 r3 冻结十五文件清单为 `4c4ea072ec399b6060d84834f15b8d8a0deaa070fcf43f373ed6520e3ec0e2ee`。二者只相差四份状态 Markdown 与新增公开投影；八份产品／测试文件字节保持。协调者逐件核过两份快照，终核时 r3 列明十五文件与工作树一致；本报告为后附的同片审查记录。

本片范围是两组 `ergora-opt-{recipe-model,model-verification}-proposal` 的 workflow／instructions／context 六文件，catalog 两条，原方向测试参数两项，以及对应计划、交付和手册。原始要求以[本片计划](../plans/2026-11-13-optimization-model-directions.md)、[D2 计划](../plans/2026-11-13-specialist-presets.md)及 [R9](../research/2026-11-12-optimization-model-recipe-agents.md)为依据。规范核验包括 AGENTS、README、当前架构、reference 边界、身份合同、相关 ADR、定义／后端手册、TESTING、pyproject 和上述 skill。

## Standards

Standards：通过（fresh context，D2-B2f）。规范违反 0；启发式 smell 0。

范围为固定 baseline／HEAD 及 r3 十五文件。结构：六数据文件沿原 owner 与 CLI／HTTP 消费，无新抽象。冗余／测试：只扩原参数，读取根配置，不锁合法变量；原安装 suite 27 通过。性能：无运行算法变更或实测收益声明。

已核 542／两 RECORD／283、十二来源及 R9 回执、六独立会话、36 资源 77,413B 连续 UTF-8 至 null、完整双前驱及公开投影；自身八全文仅核身份。Synthetic 不授真实模型／GPU／质量／恢复结论；七 collection 仅覆盖，进程仅限定结束观察；发布与自己的 CI 开放。

本轴原报告 SHA256 为 `63aec7058551a9c0ad5e28a94ae2f7f5400b1e471959f9171f674480aaf24c4f`，完整身份及标准来源保存在该轴私有 `review-scope.json`。

## Spec

Spec：通过本片只读资料／安装／synthetic 单叶交接出口，开放 finding 0。不授予发布、自己的 CI 或真实模型执行验收。本轴未读取另一轴报告或自身模板的实际判词。

缺失／部分需求、未要求的 scope creep、貌似实现却错误均未发现。依据本片计划第 7、9、17、18 行，两根完整 context 保留任务／权重／数据／模态身份、library／benchmark、收敛与执行区别、builder 与已有 provider 差异；验证保留十二项／四状态、canonical 条件、完整 tensor／fresh-process／mesh／next-update／独立质量及 helper 数值结果消费。来源 card 原第 58–77、698–767 行和 helper 第 1169–1187 行已交叉核对。

Catalog 由原 `workflow_definitions.py:39` 安装，生产 callers 为 `cli.py:787`、`web.py:376`；完整祖先／逐父权限仍由原 `workflow_definitions.py:158`、`:266` 装配。`test_presets.py:21` 经原安装／manifest／输入 Interface 检查新根与继承，三叶断言约束此发行形状，不限制用户修订范围。八产品／测试字节、安装、十二来源、七 collection、六叶完整读取／双前驱与公开投影均独立核准。新增资料只有既有容量内的材料开销，未改运行算法；原耗时不构成 GPU 或性能收益证明。

本轴原报告 SHA256 为 `6c8c56c98f6bc8e9518eac1cd0b85745e92b45b4759d5f86511c62789849b82a`，逐资源／逐调用及自身输入重建证据保存在本轴私有原件目录。

## 协调者已核原件

- 保存的非 editable Python3.11.15 候选 source／wheel／installed 均为 542 产品并逐字相等；wheel SHA256 为 `f5fbf80e29cfa9fc80cd8c89788bf45b2f81761186e76e97b91e6a72faa0099c`。wheel RECORD 550 行、installed RECORD 555 行的非空 hash／size 全符；283 冻结文件逐项符合原清单。baseline 536 原产品除 catalog 外及十八旧条目全部保持。
- 十二来源 464,656B 的长度／SHA 全符，并追到 R9 保存的十二 HTTP200 回执及原 body；本审查没有新 GET。原安装 suite 完整 stdout 为 27 passed／105.35 秒，外围 107.009 秒。七份正式 phase 原件重算为 1715 全集＝六组 254／250／342／312／258／299 并集，交集 0，全部是 collect-only；不作全 suite 回归通过。
- 六叶的原输入整树摘要、prompt＝实际 stdin＝protocol、结构祖先及完整 Skill 文件与 scope 原字节相等；实际 native stream 有每叶一次 list、六次 read，36 资源 77,413B 均连续 UTF-8 读至末页 null，无兄弟资源继承。最终 native JSON 与保存 result 相同；两个 measurement 的 task 逐字含本方向两份完整原前驱，SHA 在 audit／公开投影另核。实际后端均为显式 Codex，有回退理由，不授异构后端结论。
- recipe-model 的原 measurement 拒绝以 pretrain-only mock 作为真实 SFT 起点及无新质量合同的 batch32→64，并更正 profile 原输出的 sequence slots 为 nominal token slots；原输出保持。model-verification 保留 synthetic token mismatch／cosine0.98<0.99 的失败及卡声明矛盾，未把 exit0 或结构声明当实际 helper／validator／模型成功。
- 自身调用确为安装版 `ergora-structure-review@1.0.0`、`root/review`、text-only：八全文 53,365B 与实际 task／stdin 逐字相符，三份祖先／自身资料进入实际 59,552B prompt，原输入及 result 身份全符。保存的外围耗时为 25.248 秒；该原模型审查仅覆盖内联结构和测试价值。

[公开证据投影](evidence/2026-11-13-optimization-model-directions.json) SHA256 为 `745dcf72d339419cf69d800ee46c512a37c07a2856dcc66ae0352e1d50cc03ed`；协调者核过其原 audit、fixture、来源、输入／结果、安装／collection、自身和结束进程观察的绑定。结束进程原件只是一轮限定私有根与可执行名的 `/proc` 观察零匹配，不能证明全程 PID／脱离后代清理或 OS 隔离。

Spec 0 finding；Standards 0 规范违反／0 启发 finding，两轴均无开放问题。本片只读资料、安装及 synthetic 单叶交接的独立审查通过。真实模型／卡／转换、GPU、质量／恢复、性能收益、自动图和采用均未验；普通提交推送及本候选自己的完整 CI 另行验收。

## 同片最终状态补核

2026-11-13：r4 十六文件冻结清单 SHA256 为 `eeca263615b611f0846c7dea429bc99c8e5e5ffdb8c8881601b0a17deced3656`，baseline／HEAD 仍为 `83000a1afbdbd2429efbcebe1e7c65133215ca8e`。逐件长度／SHA 与冻结原件及当时 live 全符，冻结目录和 Git 跟踪差异／全部未忽略新文件均与清单精确相等，没有清单外变更。r3→r4 只有 PLAN、本片计划、D2 计划和交付记录四份状态 Markdown，以及新增本独立报告；八产品／测试与公开投影全部保持。

四处状态所述“独立双轴通过、开放 0／0、本地出口完成”与本报告原结论相符，并明确保留普通发布、本候选自己的完整 CI 及独立终核开放；没有把 synthetic、collection 或 B2e 的结果扩大为本候选真实模型／实验或 CI 验收。十六文件中 176 个本地 Markdown 文件链接全部存在。本次仅补核同片状态与链接，不改变两轴判词或原验证范围；本尾注由后续最终快照单独绑定。

## 同片普通发布与 CI 初始绑定补核

2026-11-13：普通提交 `2d13c0ee76ddeb960365b6b8e77853801def14d5` 的唯一 parent 为 `83000a1afbdbd2429efbcebe1e7c65133215ca8e`。最终 r5 十六文件清单 SHA256 为 `cc35a1d754f07f579cfba504d10e38797406b3970a9f6f57eeeb3e7bd939f9c2`；与 r4 相比只有上述获核准的报告尾注。协调者从实际 Git 对象重算十六文件长度／SHA 和 blob OID，全部等于 r5 原文件、ready.files 及 staged_objects；变更集合精确相同。ready 的辅助 `review_report_sha256` 确由本片相同 manifest 的报告条目取值，等于 `78c4edc785adc4652bc3aad4c25b2f05ef3d6c1da9193ad9845d3bc404e85c79`，没有借用前片字段。

该提交的全部 542 包文件与已核 source／wheel／installed 及 live 逐字相等；原 wheel 身份和两 RECORD 550／555 行继续符合。普通 push 原回执 exit0，argv 无 force；作者 SSH `ls-remote` 原回执 exit0，完整分支 Ref 等于上述候选。此处只核作者保存的原回执，审查者没有请求远端。

官方 Actions 初始列表原 JSON 的唯一完整 commit 链接、run 原 HTML 和 UI job-groups 原 JSON，均绑定本候选自己的 [CI43426570060](https://github.com/626619403/Ergora/actions/runs/43426570060)。三份 HTTP200 原回执的长度／SHA 与 body 一致；列表、summary 与 UI metadata 的身份字段一致，八个不同 job ID 恰好覆盖 plan、六 Linux 组和一 Windows 组，逐 job href 均属于该 run。初始原页为 In progress，plan success，其余七 job 在途；本次只通过初始身份绑定，自己的 CI 终态和全部必要步骤仍待独立核准，不使用 B2e 的 CI 结果。

发布后状态补核 P3-1 已关闭：`docs/PLAN.md:10` 的旧 B2c 和 `docs/plans/2026-11-13-specialist-presets.md:217` 的旧 B2a 曾误写 B2f 的新提交／CI，可能让恢复者错误归属候选证据。实现方仅将两处历史段落恢复为已提交 HEAD 原字节；协调者重读逐字一致，B2f 最新条目保留。除本报告尾注外，当前更新只涉及本片四份状态 Markdown。176 个本地文件链接均存在。该修正不改变已发布产品和原两轴结论；普通发布身份补核通过，CI 终态继续开放。

## 本候选自己的 CI 终态独立验收

2026-11-13 13:26–13:29 UTC：协调者沿同一官方 UI 路径各取一次 run 原 HTML、当前 job-groups 原 JSON 及八份 job 原 HTML，十份 HTTP200 原回执的 URL、长度和 SHA256 与保存 body 全符。终态 r2 原件使用新目录，早期在途及受限观察完整保留。run 原页明确为 Success，完整 commit 链接仍绑定 `2d13c0ee76ddeb960365b6b8e77853801def14d5` 的 [CI43426570060](https://github.com/626619403/Ergora/actions/runs/43426570060)；当前 UI 的 totalCount 为 8、hasMore 为 false，八个不同 job 均 completed／success。

`ci-run-html-r2` 原 body SHA256 为 `93f75c389d5c2f1f7c6057e84009ca9a3716ef1ad4747ba2beee36c7bc018977`；`ci-job-groups-r2` 原 body 为 `abad91a70e2d16941850eeb56b030d98e31e28af96964b3bfa082dbcac4b3e85`。逐 job 的 `ci-job-<ID>-html-r2` 原件、回执和步骤身份由独立原件审计逐项绑定。

| Job | 官方 job ID | 必要步骤数 | 原生回归秒数 |
|---|---|---:|---:|
| plan | [131889315431](https://github.com/626619403/Ergora/actions/runs/43426570060/job/131889315431) | 1 | — |
| Linux group 0／Python 3.11 | [131889393569](https://github.com/626619403/Ergora/actions/runs/43426570060/job/131889393569) | 4 | 253 |
| Linux group 1／Python 3.11 | [131889393518](https://github.com/626619403/Ergora/actions/runs/43426570060/job/131889393518) | 4 | 246 |
| Linux group 2／Python 3.11 | [131889393553](https://github.com/626619403/Ergora/actions/runs/43426570060/job/131889393553) | 4 | 235 |
| Linux group 3／Python 3.11 | [131889393659](https://github.com/626619403/Ergora/actions/runs/43426570060/job/131889393659) | 4 | 164 |
| Linux group 4／Python 3.11 | [131889393536](https://github.com/626619403/Ergora/actions/runs/43426570060/job/131889393536) | 4 | 178 |
| Linux group 5／Python 3.11 | [131889393493](https://github.com/626619403/Ergora/actions/runs/43426570060/job/131889393493) | 4 | 211 |
| Windows all／Python 3.12 | [131889393640](https://github.com/626619403/Ergora/actions/runs/43426570060/job/131889393640) | 5 | 600 |

必要步骤与候选 workflow 对照：plan 的 `Read explicit test groups` 一项；七个 native job 各自的 `Build and install wheel`、`Packaged reference identity`、`Native application regression`、`Upload regression observations` 四项；Windows 另有 `Windows PowerShell 5.1 installer and upgrade`。共 30 项均恰好出现一次，conclusion 为 success，开始／结束时间非空且带 `data-job-completed`，日志 URL 非空并严格含完整候选 SHA、对应 job ID 和步骤号。六 Linux 回归为 164–253 秒，Windows 回归为 600 秒，PowerShell 5.1 安装升级为 36 秒；这些是官方步骤时间差。

独立原件审计 `ci-independent-terminal-audit-r2.json` 为 15,571B，SHA256 为 `ae2f26b9b59d3a15a992c8b3a69ee3cb3a8bd31fa02d5e13fc5d4765ca21b045`，结果 passed=true、issues=[]、job_count=8、required_step_count=30。该审计另从原 HTML／UI JSON 核验，与复用原解析器所得 r2 结果一致。已验证的是完整 SHA 日志 URL 与官方步骤元数据；没有下载日志正文或 artifact 归档，没有执行本地测试、安装或模型。

结合前节普通发布身份补核，本片已提交 B2f 候选的发布及其自己的必要 CI 独立终态验收通过，原 Spec／Standards 开放问题继续为 0／0。结论范围为上述精确候选；后续 README 或试用文档变更按其自身证据验收。真实模型／卡／转换、GPU、质量／恢复、性能收益、自动图和采用仍未验。
