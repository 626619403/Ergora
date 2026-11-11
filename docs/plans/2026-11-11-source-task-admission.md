# F7b.1-B1c：按所选能力准入并运行来源任务

实现基线 `4638c3b9524adcba584a9313b8fd1588b5dde64d`，分支 `refactor/architecture-foundations`。承接[来源合同与独立设计](2026-11-11-issue-dispatch.md)。B1b 本地出口及精确提交／普通推送已完成，原 Portability 42991272992 的依赖失败已由4638c3b修正并普通推送，完整20文件同片独立两轴通过；修正自己的CI42995785084已Success、双OS七必要步骤与同片原评审终核通过，B1b精确交付终结，原655失败保持。C1已在该基线上实现。

## 行为和所有者

显式 input v7 的 start 只检查实际选中的 inventory／plan 角色、工作叶和审查叶，以及原六阶段所需的本地执行条件。未选 A2A、MLflow、LangGraph、Symphony 和默认 implementer／reviewer 不成为必需依赖。旧 v1–v6 仍使用原 doctor。工单快照已经冻结，start 和未知恢复不再读取 tracker 或 token。

沿用原 `cli.task_action` 的 policy、可信 checks、Temporal connect、同一 hostless ingress claim 和原 transport。保留 intent、lookup-before-start、attempt-before-send、原输入／memo、冲突及未知状态；unknown 只查询原 ID，不重发、不追加模型准入。输入、来源、候选、批准及历史身份均保持。

|位置|改动与归属|
|---|---|
|`WorkflowInput.admission_report`|共同 Interface 接收原 report 与冻结 selection；默认调用原 report，只有 v7 实现所选依赖检查。SDK／native 导入仍按需，标准库读取保持。|
|`IssueSourceInput`|从已核输入的 profile 和 creation 的 agent-bindings 选 inventory／plan，从 composition 选工作／审查叶。复用 AgentBackend 的 schema、invocation、mode、policy、executable availability；MCP 只对所选 MCP mode 检查。|
|`_Submission.dispatch`|在已有专用进程内作用域替换 doctor report，和 transport／spec 一起 finally 恢复；仍调用原 task_action。不新增 scheduler、claim、journal 或全局版本分派。|
|`CodexBackend`|可用性和实际 command 使用同一配置 executable；差异由本实现负责，上层不按后端名改路。|
|现有 submission／backend 测试|复用 durable SDK fixture，v7 不用恒真 doctor 掩盖新增检查；原入口保持旧 fixture。新增回归只保护所选依赖与恢复的真实差异。|

本地检查保留 execution_enabled、当前容器身份与信任确认、实际 Git／timeout／native Python。实际 Temporal 连接仍由原入口完成。本地程序可用与配置兼容不证明认证、配额、worker poll、模型质量或 OS 隔离；这些分别由实际运行或未验说明承担。不得放宽材料／文件预算。

## 可验收节点

|节点|验收|状态|
|---|---|---|
|C1 所选依赖|源码与已安装包：无关包／服务和未选后端缺失仍可 start；所选后端、MCP、runtime、执行禁用／容器不匹配具体拒绝；v1–v6 原 report 保持|r2 非 editable 包身份／283冻结及架构＋准入25项通过；r1九suite8失败／158通过／6跳过按原范围保留，八失败已定向修验|
|C2 原提交恢复|原 policy／可信 checks／同一 claim 竞争；丢接受响应与原输入／memo 错配；unknown 仅 lookup，即便新准入不可用；恢复原 ID／原文件保持|r2定向25项包含原policy／共享claim、丢响应与input／memo错配；夹具改用原task_spec后旧identifier边界1项重验通过|
|C3 原六阶段|独立 home 的已安装包＋Supervisor／Temporal worker／executor，冻结工单后 tracker 下线；显式批准精确计划、精确候选、证据／handoff／事件 replay 与所属进程清理|r1确定性9job／236事件已核；最终r2正向混合5真实叶、9job全成功REVIEW_READY、386事件重放／handoff／原ID重复与精确本地export通过，87＋2采样清理、23资源7437B／五来源回显均经独立原件终核；两失败原run／对账保留|
|C4 完整审查与交付|Ergora 自身真实审查模板、完整祖先／来源读取原件，新 fresh-context 独立两轴；安装／受影响检查／手册；普通推送、精确身份与自己的双 OS 必要 CI|自身144.57秒approve／12完整附件与五scope读取；完整18文件和最终正向原件独立Spec／Standards及本地出口通过，ST1关闭、开放0／0；精确Git／远端及自己的CI待终核|

所有验收原件保存在 home 下忽略的本片 checks；公开文档仅保留去环境化身份／范围投影。原失败不覆盖，未执行范围不写通过。默认不向真实 tracker 写入。

r1→r2逐文件核验：两wheel路径相同，唯一产品差异是`reference_inputs.py`补回`import json`（另有RECORD）；r2 SHA `34c80c6257b7975e607b6a046d8e598c4506378109aa3740c5e6efe69b48ef94`，445包文件、450wheel／455安装RECORD行及283冻结均核。r2定向25项79.53秒，失败分支已在新包实际运行；未将r1错误分支或确定性fixture等同真实模型验收。

本片不实现 F7c 的远端写意图／恢复、F7d 的 observe/UI、F8 harness、F9 实验或 F10 演进。每节点更新[交付记录](../delivery/2026-11-11-source-task-admission.md)和[PLAN](../PLAN.md)；完成本片后继续[总计划](2026-11-01-all-in-one.md)。
