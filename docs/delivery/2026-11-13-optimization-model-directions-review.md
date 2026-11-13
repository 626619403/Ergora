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
