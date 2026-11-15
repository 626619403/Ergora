# c1d M1a：rounds 纯内容校验提取

日期：2026-11-16。状态：源码／安装各14项、实际基线字节／错误差分、native 隔离、自身模板及 fresh 终核两轴 approve／0 已闭合。产品固定 `5cb4cb903486d37356a5511c75e094a195558912` 并普通导入 `bd479050ddd2d9c6b6964f89fe44cfc895273d6b`；发布／自己的 CI 另验。承接已独立批准的[严格 wire 合同](2026-11-16-training-cycle-measurement-wire.md#原-contextnative-最后-gate-与最小纯提取)及其[设计审查](../delivery/2026-11-16-training-cycle-measurement-wire-review.md)。这里只执行 M1a，不把后继版本的设计写成产品能力。

## 基线与前置

开发分支为 `refactor/architecture-foundations`，实施基线 `fa2fd17620192ac1341a72f1050dc37faaee623f`。c1c 固定产品 ec6dcbc 已普通导入 5b04b2b，且[最终 fresh 独立审查](../delivery/2026-11-16-training-cycle-workflow-final-review.md)核准准确提交／实测字节，两轴 approve、开放 0；公开文档已随 fa2fd17 推送。远端精确身份及该候选自己的 CI 单独观察，不由本片认证。

提取前 `training_rounds.py` SHA256 为 `d4ca342b902f9d8c869171bbefa78b7fa6c0f0b129f57ea162b505e1d5124e7a`，`training_execution_protocol.py` 为 `b8f8c8292b134491ddbaf6820fd5a9c455465bc3a78d3922e6832fbf54c63e38`。动手前重核真实 Git／文件身份，使用持久隔离工作树，不修改旧验收原件。

## 行为与所有权

`training_rounds.create/read` 仍是唯一公开索引入口：schema 验证、普通文件／目录检查、完整 raw SHA、上界、原项目观察、不可覆盖发布及 State 访问仍留原模块。CLI 的 rounds-create/read 沿同一入口；没有新增 reader、账本或执行器。

把原 `_check` 在 `contracts.validate` **之后**的纯算法，以及它使用的 pretty 编码／轮内容 SHA、comparison／anchor 和 coverage 常量，移到现有已 pin 的 `training_execution_protocol`。rounds 调用原 schema 验证后复用此算法，create 使用同一原编码和比较提取。可集中原 10,000,000B artifact 常量并保留 `training_rounds.MAX_INDEX_BYTES` 同值入口；不改数值、不新增配置。函数名跟随现有 owner 风格，以实际调用解释边界，不增加别名包装或通用插件框架。

这个纯函数的输入是已经通过原 schema 验证的完整报告；它不承担 schema 或来源认证。保持原覆盖范围、校验顺序、错误类别／信息、prefix 链、project／revision／manifest／submission／approval 绑定和 baseline anchor。`origin_authenticated=False`、authorization not_evaluated、promotion false 保持，不能把内容自洽解释为可信来源或执行许可。

原编码必须仍是 `ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False` 的 UTF-8 JSON 加一个 LF。原每轮 SHA 散列这份 pretty 字节；不能替换为协议内其他 compact／semantic hash。read 仍按原始文件字节散列，不重新编码来接受替换文件。previous_report 指向原完整文件，旧 prefix 原内容不得变化。

当前直接生产 caller 是 rounds 的 create／check，纯算法是为已审定的 native 最后前驱 gate 解除依赖，后继调用尚未实现。本片不虚构多个当前 caller，也不新增未来 gate 的占位调用。native 的实际接缝是现有 protocol 的 dependency-isolated import；不能因此引入 training、State、jsonschema、YAML、Temporal SDK 或 dev_platform 的顶层加载。

## 可验收检查

1. 复用 `tests/test_training_evidence.py` 的原离线 create/read、负结果／unknown、已接受前缀及 baseline 漂移、丢 start acknowledgment 接缝。必要新增只覆盖提取可能静默破坏的绑定／prefix 或编码关系，不为每个分支复制实现测试。
2. 在同一原 fixture 形成的报告上，以提取前后实际入口比较完整 pretty bytes、轮 SHA、完整文件 SHA、结果／覆盖字段和真实篡改拒绝；原实现可从固定 Git 基线在私有检查目录加载，不提交第二算法。
3. 使用真实 `python -I -S -B` 子解释器，只添加当前源码包目录，装载 protocol 并运行所提取纯校验，证明不依赖 site-packages／State／SDK。复用现有隔离测试模式；不为这一步启动服务。
4. 源码定向检查通过后，构建新非 editable wheel，在隔离 core／SDK 环境核真实 site-packages、依赖和原 283 reference 身份；运行适用的原索引检查及隔离接缝。记录源码与安装范围，不无理由重复 c1c 的 53 项或真实服务矩阵。
5. 新 fresh reviewer 从固定基线、实际全部 diff 和检查原件分别审需求／维护性；修复实证 finding 后复核。大项使用 Ergora 自身原结构审查模板，保留真实后端／完整输入／回复，用户已授权的 Codex 回退照实记录。
6. 原产品行为及 review 闭合后固定提交，普通导入／推送开发分支，核精确远端及适用 CI。每一步更新本计划、主 PLAN 和[交付](../delivery/2026-11-16-training-round-content-extraction.md)。

## 明确后继与停点

本片不改 schema1/2 出生／恢复，不实现 schema3、V2 Workflow、collect/reconcile、measurement acceptance、predecessor gate 或 ordinal1；也不改 source inventory、283 参考、SDK 预算／取消、archive 算法、runner 或批准策略。提取完成不表示 c1d 多轮实现完成。

下一片仍按 wire 表的 M1b 出生与兼容进行，完整编码 M1c、H 接受／唯一 collect 与 durability、最终 gate、新 V2 和真实 CPU 两轮逐片推进。WA4 产品取舍保持等待用户真实答复，不由本片推断。
