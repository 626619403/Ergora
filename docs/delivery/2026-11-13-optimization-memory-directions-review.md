# D2-B2a 三内存方向独立审查

日期：2026-11-13。审查者：fresh-context `optimization_memory_directions_review`，另以两个全新上下文的 `spec`／`standards` 审查者分别检查两轴。依据项目 AGENTS、maintainable-project-delivery 的独立审查要求、code-review 的双轴流程及 codebase-design 的职责／复用原则。

本片本地独立审查通过：Spec 开放 0，Standards 初审一项 P3 状态记录问题已修复并由原 Standards 审查者复核关闭，最终开放 0。此结论只授予三个只读方向子模板和相应交付合同；不授予实际训练、GPU 收益、自动图执行或发布通过。

## 固定范围

- 基线：`e2bbde0bec4750b2e3a1d09d8597bf94196ba1bd`。
- 初审：私有 `optimization-memory-directions/review-r2/manifest.json` 的 16 份冻结文件；逐份 SHA256 核准，显式对比基线，包含全部九份新增方向数据文件。
- 最终候选：同目录 `review-r3/manifest.json`，SHA256 `e318513697ef7da461e67b6ff8f13813fa10dea4419a12bc214fd73b4163eada`；16 份文件再次逐份核准。r3 仅修改本片交付记录与 D2 计划的状态文字，11 份产品／测试及另外三份文档／证据字节与 r2 相等。
- stdin／poll-history 前置提交 `e890785`／`4076451` 作为已独立审查的依赖；不借其判词审查本片。A2、B2b、其他文档及 CI 变更不在本片出口；计划内相关状态段不授予这些工作包验收。

冻结文件为：

|文件|范围|
|---|---|
|`src/ergora/data/presets/presets.json`、`tests/test_presets.py`|三个新 catalog 选择及一个三方向参数化合同检查|
|`src/ergora/data/presets/workflows/ergora-opt-memory-tuning-proposal/`|`workflow.json`、`instructions.md`、`context/memory-tuning.md`|
|`src/ergora/data/presets/workflows/ergora-opt-activation-recompute-proposal/`|`workflow.json`、`instructions.md`、`context/activation-recompute.md`|
|`src/ergora/data/presets/workflows/ergora-opt-cpu-offloading-proposal/`|`workflow.json`、`instructions.md`、`context/cpu-offloading.md`|
|`docs/TRAINING.md`、`docs/TEMPLATE_WALKTHROUGHS.md`|选择入口、叶路径、完整材料与手动交接|
|`docs/plans/2026-11-13-specialist-presets.md`|D2-B2a 要求与本片状态|
|`docs/delivery/2026-11-13-optimization-memory-directions.md`、`docs/delivery/evidence/2026-11-13-optimization-memory-directions.json`|交付记录与公开证据投影|

原始要求来自[D2-B2 计划](../plans/2026-11-13-specialist-presets.md#b2按决策粒度发布资料子模板)、[R5 来源研究](../research/2026-11-12-optimization-memory-agents.md)，以及共同的逐实例职能／后端、完整结构祖先继承和子权限上限合同。没有用未经筛选的 `baseline...HEAD` 代替未提交片的明确冻结差异。

## Spec

新鲜上下文 Spec 审查结论：范围内无实证 finding。未发现缺失／部分实现的本片要求、范围扩张或错误实现。

三个可独立选择的根精确复用 `ergora-training-analysis@2.0.0`、`ergora-measurement-review@2.0.0` 及 designer／analyst／measurement reviewer，所有三个叶继承完整方向 context；没有增加 Agent、role、运行器、schema、调度或账本。单次 `run-input` 仍只执行一个叶，原完整前驱由操作者传递；原 runner／owner 保有执行、停止、恢复和采用权。固定知识版本与实际运行版本明确区分。

Spec 审查者独立核了最终 16 文件、506 产品文件／两 RECORD／283 冻结身份、五个旧 catalog 条目、九个原调用链及自身审查包；安装结果与模型调用均未重跑。源事实支持 estimator 遗漏项、重计算控制、卸载机制、PP 限制与 graph 例外；三份 measurement 原件均保留缺执行／质量证据的 `request-changes`。

## Standards

初审 P3：r2 的 D2 计划第 217 行仍称“当前仅数据／检查准备”，第 223 行仍称九叶／交接在途，而本片交付表和原安装／调用记录已完成这些检查。违反 AGENTS 的恢复记录同步要求和计划第 185 行的验证状态更新要求。恢复工作的人会得到冲突状态，并可能重复已完成的模型调用。最小修正为更新本片检查点，区分已完成验证与未完成的独立审查／发布。

原 Standards 审查者对 r3 同片复核：P3 关闭，开放 0。最终 16 个 SHA256 全部核准，11 份产品／测试不变；计划现已记录安装、九叶及前驱交接完成，并保持独立审查／发布和自己的 CI 开放。报告链接有效。本次修正没有产品、模型或测试重跑，也不授予 A2、B2b 或 CI 验收。

范围内无其他实证规范违例或需处理的启发式 smell。方向差异放在工作流资源中，共享专家与原运行 owner 不变；显式 bundle 登记符合配置入口职责。新增测试用现有 manifest／输入 Interface 检查方向 context 可能被漏传、错误专家版本、只读权限及删除活动定义库后的离线重建；它不限制用户可修订的实例数、模型参数或通用算法配置。未发现重复算法验证、无真实消费者的抽象或应新增而缺失的运行保护分支。

## 原件与验证边界

聚合审查者使用独立只读脚本及原公开检查 Interface 复核原件，不只读取作者汇总：

|证据|独立核对结果及实际范围|
|---|---|
|非 editable wheel|SHA256 `06f9ad909396597409dcebe86c6fbe63bffefd0aec16867d56fbe238e4aa039a`；506 产品文件在隔离 source／wheel／安装目录逐字相等；wheel 与安装 RECORD 的 hash／size 全部核准|
|兼容身份|五个既有 catalog 条目逐字段不变；100 份旧 preset 文件及 283 冻结参考文件与本片基线逐字相等；11 份本片产品／测试与安装 source、最终快照相等|
|原安装检查|直接读取命令回执和 pytest stdout：15 passed／59.22 秒，外部控制器 61.03 秒；包括三方向重复安装、精确叶／只读／完整 context 来源及删除活动库后的输入重建|
|保留的首轮失败|源码原件为 4 failed／11 passed／50.52 秒。三项误从 workflow 实例读取仅 agent 叶具备的 resources；一项源码父进程与旧安装 CLI 子进程混用候选。后续测试读取正确资源所有者，同候选安装验证 CLI；未改产品 Interface 掩盖失败|
|九叶原调用|每个原 result／request／完整 manifest／input／prompt／实际 stdin／protocol／固定 scope／native stdout 链相符；每叶只读且固定 v2 专家；Codex 显式回退原因保留，不称异构后端成功|
|完整资源读取|所有结构祖先和自身 Skill 树共 54 个资源出现、88,611B，与 scope、固定附件和 native 连续 UTF-8 页一致并读至 null；核的是完整交付／读取，不据此声称理解或训练收益|
|手动前驱|每方向 measurement 的 task／stdin 均包含 design 与 profile 两份原始结果全文并核 SHA；三份原审查均因缺实际运行、数值／质量／容量／配对测量及恢复证据返回 request-changes|
|原自身结构模板|11 份完整产品／测试正文 46,784B 与实际 task／input／stdin／protocol 相等；三份结构／自身资源完整；原 native 最终消息与保存结果相符，42.021 秒 approve，结果 SHA256 `66cc297403e7709b7cb1486321cb46017a3e68da9d6db4ca8276cc41004e8bb9`。此聚焦判词不替代完整两轴审查|

另逐份验证 R5 的 12 份原始来源回执、固定 URL、长度与 SHA256，直接核 Bridge `55694838ce73cd23b00ff95bd00512aefb963ce0`／0.8.0 和 Core `928ce7ce256b734f00f1c81ddd3a8958d6b61ebf` 的相关实现。estimator 的 Adam／SP／selective 假设和 allocator／workspace／graph／offload／full-recompute 遗漏项明确；空 selective control 没有被旧标签清单排除。层级卸载的 PP=1／recompute 互斥、fine-grained 的 PP／VPP 与 eligible-group fraction、optimizer 的 precision-aware AdamW／wrapper 要求没有混为一个开关；Core full-iteration 例外没有被说成 Bridge model-spec 已执行。产品为本项目短知识综合与来源引用，没有新上游工具／Skill 的安装或正文再分发。

私有审查留存于本片 checks 的 `independent-review-r2/`：明确快照差异、`verify_raw.py`、`verified-raw.json`、`verified-structure-original.json`、`verified-sources.json`、`final-r3-delta.json`；最终文档身份见 r3 manifest。[公开证据投影](evidence/2026-11-13-optimization-memory-directions.json)保持实际 scope。

本审查没有新模型调用、训练／GPU、安装、服务启动、Git 变更或远端操作。目标硬件可行性、实际性能／质量、checkpoint 恢复、B3 实验采用、普通提交／远端及本候选自己的必要 CI 留给各自原 owner；不能从本地资料片结论外推。

最终：Spec 初审／终核开放 0；Standards 初审 1 项 P3、已关闭，最终开放 0。
