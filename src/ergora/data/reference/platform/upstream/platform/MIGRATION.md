# v1.3 升级与回退

本次新增可移植契约编译器、A2A 任务入口和共享工单所有权；开发工作流本身仍执行原有 `development-v1` 状态机。无需迁移 Temporal 历史，也不应重写已提交请求。

## 新部署

1. 在云端 Linux CPU 协调主机安装完整包，保持安装文件对编码 agent 只读。模型继续使用云端 API，不部署本地模型。
2. 按 [PORTABILITY.md](PORTABILITY.md) 选择两类开发模板之一，维护者固定项目策略和运行绑定。
3. 按 [README.md](README.md) 接入真实 CI/Codex 阶段执行器与 Temporal worker。编译器、A2A 服务都不会替代该执行器。
4. 若使用 A2A，安装 `requirements-a2a.txt`，按 [A2A.md](A2A.md) 注入调用方凭据、配置私有台账、TLS 反向代理和 Agent Card 公网地址。
5. Symphony 与 A2A 的 `shared_ingress_db` **必须是同一绝对路径**；示例统一使用 `/srv/agent-control/ingress/leases.sqlite3`。它们运行在同一协调主机，使用受信的协调身份；编码 agent 无权写入此库。不要分别创建两份数据库后声称实现互斥。
6. 先做一项可逆治理任务，检查重复提交、断连恢复、人工审批、最终证据、跨调用方隔离和取消未确认，再扩大并发。

## 已有部署

1. 暂停新任务准入；保存旧安装包、配置与数据库的可恢复备份，不删除台账。
2. 让已有 bridge 任务到达安全的 `DELIVERED`。`BLOCKED_UNRESOLVED` 先由可信操作员确认所有外部作业停止，再按已有 reconciliation 流程处理。等待和取消请求不等于已停止。
3. 升级桥接代码及共享运行时模块；**不要滚动替换正在运行任务依赖的工作流控制流**。本次 `DevelopmentWorkflow` 和旧 profile 保持不变。
4. 配置共享所有权库。若旧活动记录没有 lease 标记，bridge 会拒绝开启共享模式；本版不自动推断或补写存量所有权。先完成第 2 步。
5. 再启动 A2A 网关，测试同一工单从不同入口提交会被阻止。A2A 的任务 ID、领域 task ID 和 Temporal run ID 各自保存，不可混用。
6. 恢复新任务准入。新任务可用可移植格式；已有 v1/v2 继续走旧格式，不原地改写。

共享库中的所有权不自动到期。进程崩溃后按原任务、所有者和摘要恢复；未确认的外部副作用必须保持占用。多主机部署需要单一准入服务或带事务的共享数据库适配，当前 SQLite 实现不支持通过 NFS 横向扩展。

## 兼容矩阵

| 对象 | v1.3 行为 |
| --- | --- |
| 原训练 v1 请求与 `ExperimentWorkflow` | 保留原有路径；没有迁移为可移植开发任务或 A2A 任务 |
| 原开发 v2 请求 | 继续由原注册表验证；原 profile 摘要含义不变 |
| 原 Temporal 运行与快照 | 不重写，不因新模板安装而重新解释 |
| 新 portable task/package/policy/binding | 编译为冻结 envelope，同时生成原开发 spec |
| 新任务通过 A2A | 可信操作员准入精确 envelope 哈希与调用方，保留完整快照 |
| 新任务通过 Symphony | `export-v2` 导出兼容请求，再走原有准入；额外归档 compiled 快照 |
| 原 bridge 未配置共享库 | 保留单入口兼容；不可同时给同一项目开放 A2A |
| 已配置共享库的 bridge | 活动记录存在时禁止移除共享库配置 |
| DSH / ADK / LangGraph | 本次没有完成其真实端到端适配；支持 A2A 不等于理解本平台任务数据 |

`export-v2` 是显式兼容边界：原始请求保留执行所需的范围、目标和 profile，**不包含完整 portable 策略与绑定快照**。维护者应将 `compiled.json` 与导出请求一起归档，并在准入证据中记录 compiled 摘要；旧 bridge 仍以原始请求字节摘要和受信 repository policy revision 进行准入。需要完整快照级远程准入时使用本次新增 A2A 路径。

## 哈希与版本

- `compiled_sha256`：完整冻结 envelope 的规范化 JSON 摘要。
- portable `digests`：task/package/policy/binding 各自摘要。
- runtime `request_sha256`：编译后 v2 请求的规范化 JSON 摘要。
- Symphony admission `request_sha256`：交接文件**原始字节**摘要，空白变化也会改变。
- 证据摘要：真实产物字节摘要，继续绑定实际候选提交和阶段。

这些字段不能互相替换；摘要检测内容变化，不证明来源身份。当前规范化 JSON 算法为平台既有 Python 编码规则，未宣称实现 RFC 8785/JCS。

模板文件或语义变化应发布新版本和新摘要，保留旧版本处理存量。当前 portable manifest 带 `legacy_profile_sha256`，这是首版编译目标的明确限制，不宣称任意工作流 DSL 可直接跨引擎运行。

## 回退

先停新 A2A 准入，再让活动任务完成或按证据确认停止；保存 A2A、共享所有权和 bridge 台账。不要删除租约来解除阻塞，不要把未确认取消的任务重新发给旧入口。

回退客户端或 HTML 不影响已经冻结的任务。运行中的新入口任务仍需保留兼容的网关/共享所有权代码，直到它们安全收尾；不能用旧 bridge 绕过共享所有权库继续接收同一项目任务。

共享所有权的部署与崩溃恢复细节见 [INGRESS.md](INGRESS.md)。

完整测试方法见 [VALIDATION.md](VALIDATION.md)，设计与官方资料见 [STANDARDS_RESEARCH.md](STANDARDS_RESEARCH.md)。
