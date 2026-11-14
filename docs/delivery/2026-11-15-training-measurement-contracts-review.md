# Q3.2 成对测量合同独立审查

日期：2026-11-15。评审者：fresh-context 独立代理 `training_measurement_contracts_audit`。按仓库 `AGENTS.md`、[原要求与 Q 总计划](../plans/2026-11-15-domain-review-optimization-quality.md)、[本片计划](../plans/2026-11-15-training-measurement-contracts.md)，应用 `maintainable-project-delivery` 的 independent-review brief 和 `ergora-codebase-quality` 的 repository-style／module-design／test-seams。先读原要求、完整冻结差异和新增文件，再核作者叙述、邻近 owner 与原始证据；没有继承实施会话或拟定结论。

|审查轴|当前本地结论|
|---|---|
|需求符合性|**approve**。原合同审计和安装入口满足本片本地验收；R1 文档问题已修正并由原 reviewer 复核关闭，开放问题 0。|
|可维护性|**approve**。继续复用原工具及深 owner，没有重复合同、评分器、执行或批准权威；开放维护性问题 0。|

此结论不认证 Q3.1／Q2 的产品、发布或 CI，也不表示本片已提交／推送。真实训练与 GPU、质量／收益和多轮能力均不在本次验收范围。

## 精确范围与原身份

审查基线及 HEAD 为 `2729b81a4c10e4bf8c77bd78ea4165b0a64cb0c0`，分支 `refactor/architecture-foundations`。本地冻结材料 `training-measurement-contracts/review-scope-r1` 包含完整 tracked diff、六份完整 tracked／untracked 文件；已独立核对六份长度与 SHA256。

- `scope.json` SHA256：`e0596263e23a110ecd2853e0dc586ef7c09928d917665a28dbb5621b10e69629`。
- `tracked.diff` SHA256：`0c788f4c5f7d16ee83af049d1cef6ac10197fd6178b3efc2ec5d779324dc3f0c`。

实际六文件为 `docs/PLAN.md`、`docs/TRAINING.md`、`docs/plans/2026-11-15-domain-review-optimization-quality.md`、`docs/plans/2026-11-15-training-measurement-contracts.md`、`docs/delivery/2026-11-15-training-flow-maps.md` 和 `docs/delivery/2026-11-15-training-measurement-contracts.md`。Q3.1 交付变化只有本地提交／待发布记账，不重新批准其产品。

另读 `training` → `reference.training_*` → `reference_training_setup`／`reference_training_preparation`／`reference_training_evidence` 的实际路径，冻结参考的 `local/agent_platform/training.py`、`upstream/demo.py`／`compare_runs.py`／`perfctl.py`、原 measurement／evidence 文档、`templates/training-optimization` 和原测量 Skill。审查期间 PLAN、本片交付与 Q 总计划只追加自身模板完成及独立审查在途，并将 registry 的 r1 时间误录修为 r2 的 0.987 秒；已逐行核对，合同与产品保持。

## 需求与维护性核对

|要求|实际观察|
|---|---|
|保持语义与原参照|原 baseline 绑定完整提交、配置与 workload，已登记 manifest 保留原字节；新说明要求真实模型／数据／有效配置／初态及独立质量来源，不把示例批准转成项目批准。初始锚点与本轮参照、多轮关系仍明确归 Q4。|
|完整运行与配对比较|比较器按完整 pair 索引共同重采样两臂，保留配对协方差；检查独立 run ID、两臂 source_samples 相同、匹配输入／环境／初态指纹、AB／BA、无 profiler 与 global completion window 声明。全局工作去重、实际完成边界、独立重启与硬件真实性仍须可信 runner 举证，文档没有将这些声明升级为证明。|
|质量、统计、建议和采用分开|原 gate 核 manifest、固定比较器、预登记政策、两臂代码／配置／数据／环境／初态及结构化检查／独立 reviewer 名称／integration／必要 quality，并重算比较结果。它只返回人工审查资格；质量真实性、可信 oracle 和 owner 明确采用不由比较器或模型意见替代。|
|流程图与后续干预|本片没有把源码图当瓶颈或实测速率；Q3.3 继续保留 kernel 专家评估，允许无需算子修改，Q4 的无收益／失败／不确定记录和预算未提前宣布完成。|
|已有能力与深 owner|用户入口直接定位随包原工具，复用既有字段表；没有新增产品脚本、函数、schema、数据库、统计或批准权威。计划和交付文件服务于仓库已有连续工作约定，不引入执行抽象。|
|有意义的验证|原比较器、registry、基线及归档检查覆盖各自拥有的边界，八份副本验证可达拒绝原因；无新增镜像实现测试、措辞测试、冗余 CI 或断言。文档片不需要因新入口再建立测试框架。|

## 实际证据与独立检查

**身份。** 独立核对 Q3.1 固定产品清单的 **633 个源码／非 editable 安装文件**，每份长度与 SHA256 均匹配；`include-system-site-packages = false`。本次另运行安装版 `reference.verify()`，**PASS／283 份参考**，`runtime_started=false`。没有安装依赖、改模板或产品文件。

**作者原件。** 直接核 r2 的 **15 组命令 stdout／stderr SHA256**，正例及八份反例的 **72 项 artifact 摘要**和对应 manifest 字节绑定。正例重算逐字相同，`PASS` 仍伴随 `quality_assessment=NOT_EVALUATED`、P99 未认证和 `promotion_approved=false`，gate 为 `ELIGIBLE_FOR_HUMAN_REVIEW`。无收益 `FAIL`、两对不足 `INCONCLUSIVE`，以及 profiled、数据漂移、内层 quality 失败、阈值漂移、复用 run ID 和过期 baseline 配置，各自原 stderr 与 exit 2 原因一致；刷新摘要后被相应规则拒绝，未把 checksum 损坏误认合同检出。

直接读原测试输出：比较器 **9 passed／0.037 秒**，registry **14 passed／0.987 秒**，安装 `test_training_baseline.py` 与 `test_training_evidence.py` **16 passed／10.53 秒**，零失败／跳过。本次没有重复运行这 39 项。r1 私有驱动末尾错误确为 package 根定位错误；旧 stderr 保留，r2 只修私有驱动路径，不把 r1 写成全流程成功。

**自身结构模板。** 原 run `41ef620684ce4c8994f36874301c6b41`，35.945 秒／`succeeded`／approve。独立核 **17 份完整文件／294,446B**均在实际 stdin，全部父／叶资源完整，冻结 prompt＝stdin；安装版重算 input digest `b45dbaf708fe7b222afd75b3dc17349092e511cf50bf4b38818d523e7f3a322c`、原结果 SHA256 `11feaec824a85a91da9b0b9438ae29b8f5fb5ac51c2e98232f604d5065cc3385` 相同，保存原结果与运行目录相同。其文本 approve 只覆盖提供的源码文本，不替代本次独立证据核验；保留实际 Codex 替代原因，不声称异后端。

**本次有界重放。** 只在新的本地 ignored `reviewer-r1` 目录，用原安装解释器依次运行随包 `demo.py --out NEW_DIRECTORY`、`compare_runs.py INPUT --output OUTPUT` 与原 `perfctl.py --root STATE gate synthetic-demo --bundle EVIDENCE`。比较报告逐字一致，状态及限制与上文相同。再次运行 demo 于已存在目录确实停止，原目录全量内容摘要保持；作者 r2 的 **274 个原文件**前后内容摘要保持。没有改作者 fixture、安装环境或原归档。

另外以同一原比较器重算一份合法、样本充分而区间跨门槛的合成输入，具体结果见 R1。这只是合同反例，不是训练或新统计方法。所有新增私有证据保留本地；本报告不包含业务内容、凭据或机器绝对路径。

## Finding 与剩余条件

**R1／P3，需求符合性，已关闭。** 原 `docs/TRAINING.md:61` 的“少量样本保留 INCONCLUSIVE，无收益或不满足预设门槛保留 FAIL”遗漏区间跨门槛时的不确定结果，容易让真实项目按点估计未达门槛将其记成 FAIL。原 `compare_runs.compare` 在区间上界也达不到门槛时才 FAIL；区间交叠时仍 INCONCLUSIVE，与样本数量充足无关。

可达复例为原八对 AB／BA、`min_pairs=8`，候选 elapsed 交替为对应 baseline 的 0.96／1.02，其他合同不变：原比较器 exit 0、点估计 0.995% 低于预设 1%，95% speedup 区间约为 −1.232% 至 3.344%，结果 **INCONCLUSIVE**。若依新增说明登记 FAIL，将丢失用户要求保留的不确定分类。最小修正是明确不足样本／顺序不足／区间交叠保留 INCONCLUSIVE，区间上界仍达不到门槛才 FAIL；两者都不通过原性能 gate。不需改原比较器或新增持久测试。

实施者接受后仅修正该句，明确样本／换序不足或区间不能区分门槛时保留 INCONCLUSIVE，按原 all／any 规则上界仍无法严格超过门槛才 FAIL，并注明不能仅凭点估计判失败。原 reviewer 对照源码第 188–229 行及上述实际反例复核，修正与原合同一致；最终手册 SHA256 为 `076ae65c7718214443e532bb84aed8b179c2f43bc9fae19786d61f0febcb00e3`。本片交付保留原 finding、反例、修正和复核状态。没有改统计规则、产品或原 fixture，也没有为文档修正重跑 39 项或新增测试。

除已关闭的 R1 外，在上述范围没有发现实质正确性、范围、维护性或测试价值问题，最终两轴 **approve／开放 0／0**。普通提交／推送与完整远端身份核对仍待完成。另读原 `.github/workflows/portability.yml`：本片相对固定基线只有 `docs/**.md`，原 push 的 `paths-ignore` 已过滤该范围，不要求创建不存在的文档 CI；发布时核精确差异及过滤适用性，633 产品自己的 CI 仍归 Q3.1 固定候选，不能由本文代为认证。未改原 CI 规则，PR／手动触发范围保持。

六文档／179 条本地链接及 fragment 的作者修后检查已读；独立复用既有本地链接检查器，仅将基线换成本片固定基线，连同本报告共 **7 份文档／181 个本地链接及 fragment／零错误**，全范围 `git diff --check` 通过。外网未验证。

未运行真实训练、GPU、profiler、Windows、模型／数据读取、独立数值／分布式／恢复／长程质量或真实收益验证；没有平台写入、提交或推送。Q3.3 总路径、Q4 多轮／预算及真实 B3／完整 Forge 的原条件保持开放。
