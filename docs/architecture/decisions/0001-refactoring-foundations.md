# ADR 0001：重构基础边界

日期：2026-11-01。状态：采纳为 R1–R8 的实施约束；下述目标不是已经迁入的实现。[A1 审计](../2026-11-01-audit.md) · [兼容基线](../2026-11-01-compatibility.md) · [详细计划](../../plans/2026-11-01-all-in-one.md)。

## 组件描述与执行

R1 用一个随包发布的内置组件描述保存层/角色、能力、配置字段、平台、默认值及安装配方身份；agents/tools/projects、Web 目录/表单和 SDK 安装器消费它。描述采用 JSON，运行时读取只用标准库，不通过字符串动态导入任意插件。配置选项描述与 probe、协议执行、授权分开；安装状态/认证/服务连通/任务验收分别报告。

这替代现有多份 Python/JS/脚本工具字段，不增加通用插件容器或 Agent 基类。执行仍复用 agents/kernel 等真实所有者和 SDK；新增工具需相应 adapter、能力/取消验收和文档。数据声明不能制造实现尚无的能力。允许注册的是明确内置实现；第三方发现/热加载留待真实消费者。

组件描述是当前 7 个 Agent 角色和 5 个支持层的共用配置接口，价值来自现有消费者。没有为未来工具构造调用者。表单只解释已支持的字段，不允许配置删除可信 integrate/verify 或改变批准权限。

## schema 和校验依赖

R2 采用 JSON Schema Draft 2020-12 描述共享结构，选择 `jsonschema==4.24.0` 做核心结构校验；届时单独变更依赖、验证两 OS wheel/CLI 和错误路径。A2 不安装它、不改现有校验。版本选择依据是已可读取的发行元数据和标准接口，不声称它是最新或已完成目标环境验收。

|方案|适用性与代价|决定|
|---|---|---|
|继续各处手写 dict 校验|现有简单规则可保留；若同时驱动共享表单/schema，需维护第二份结构规则|不作为新增共享结构的总方案|
|Pydantic 成为核心依赖|Web 已依赖，DTO 方便；把可选 Web 栈带入所有 CLI；默认 coercion、对象 dump 可能改变旧输入/摘要|保留为传输 DTO，不以其 dump 重算旧合同|
|jsonschema + 原生 JSON dict|标准数据可给表单/文档复用；不要求模型类；增加 attrs/specifications/referencing/rpds 依赖，rpds 含 native wheel|采用；R2 验证包分发与严格类型策略|

本地发行元数据比较：jsonschema 4.24.0 为 MIT / Python ≥3.9；其本体及上述四项已安装依赖约 1.67 MB（不含测试/字节码/额外 format 依赖）。对照 Pydantic 2.11.5 本体+pydantic-core 约 6.76 MB，仍不含它的其他依赖。这只是当前 Linux 安装文件字节数，**不是 wheel 下载体积、Windows 实测或性能比较**。参考来源：[jsonschema 4.24.0](https://pypi.org/project/jsonschema/4.24.0/)、[Pydantic 2.11.5](https://pypi.org/project/pydantic/2.11.5/)、[Draft 2020-12](https://json-schema.org/draft/2020-12)。

结构库不替代业务规则：revision、有限预算、精确候选、可信评分和批准仍在责任边界。R2 必须固定 Python strict-int / bool / finite number 与额外字段、未知版本、空值的实际语义，防止 JSON Schema 对 `1.0` 的整数定义或 DTO coercion 静默改合同。现有不一致先以输入矩阵记录，不能靠改 golden fixture 掩盖。既有编译、Skill、评价摘要继续各用原编码；不让新 schema 注入默认值后再重算旧批准。

未采用自研完整 schema validator、私有 DSL 或把所有规则塞进传输 DTO。若目标平台 wheel/依赖兼容失败，保留现有校验并重评方案，不自动改用另一格式；本次未引入任何运行时兼容层。

## 状态权威与迁移

继续按域拥有事实：控制面项目/资产、Temporal history、reference 作业 ledger/证据、Forge native 状态、MLflow 观测分别保留。正式任务查询是带来源的投影，不建立第二套页面状态机；命令成功、native_finished 和验收通过不能映射为同一个 success。

R3 将控制面 DDL 和有序版本迁移放到存储初始化边界，业务模块保留 SQL 事务与特定查询，不引入 ORM/万能 repository。旧格式是 SQLite user_version=0、16 表及 JSON 文档；合成夹具覆盖这些表和文件资产。R3 在变更前还须落实备份、事务失败恢复、较新版本拒绝、旧客户端访问新库的隔离办法。**旧 0.2.0 二进制本身没有版本检查，不能仅设置 user_version 就宣称它会拒写。** 该问题是 R3 的显式验收项，A2 未实施迁移。

ReMe 是可重建检索投影；删除/修订传播仍须核对。Skill 头原子更新、研究预算/取消、Forge 未知状态的对账不能因集中存储而丢失。CLI/Web 共用完整用例；采用编排上移，资产/评分不通过相互导入做业务协调。

## reference 和生命周期

283 冻结文件与旧 HTML 保持原字节；local/bootstrap 的 21 对镜像有分发消费者。R6 先以版本化适配和新任务快照接入，不原地改冻结源码，不切换在途任务引擎。复用 DevelopmentRuntime、DevelopmentAdapter 和训练 ClusterAdapter；不增加竞争的调度器或覆盖所有域的巨型 Backend。

保留 Executor/mini environment 的实际框架 hook。POSIX 进程组、专用 stage_driver subreaper、Windows Job 和研究抓取监控分别实现其真实生命周期；Job 不是访问隔离。研究/取消意图与终止确认不同；unknown submission 需对账，不增加自动重提兜底。

训练 prepare 不启动执行；control worker 只排队，run-local 需操作者确认 manifest SHA。F9 若补自动 runner，须另验执行授权/生命周期，不能把既有 worker 宣称成已支持。回退遵循逐节点正常提交和相应数据备份；不能用代码 revert 代替已发生的数据库降级。
