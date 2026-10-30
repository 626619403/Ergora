# v1.3 验证记录与实际边界

核验日期：2026-10-26。Python 3.12、temporalio 1.34.0、a2a-sdk 1.2.3；A2A 线协议 1.0，JSON-RPC。没有运行真实模型、生产仓库 CI、训练或性能优化任务。

## 复跑

从解压后的套件根目录执行：

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r platform/requirements-a2a.txt
RUN_TEMPORAL_INTEGRATION=1 PYTHONPATH=platform python -m unittest discover -s platform/tests -v
RUN_TEMPORAL_INTEGRATION=1 python -m unittest discover -s symphony/tests -v
```

仅使用原入口时可只装 `platform/requirements.txt`；A2A 相关测试在可选依赖未安装时明确跳过。未设置 `RUN_TEMPORAL_INTEGRATION=1` 时跳过临时 Temporal 服务测试，不能声称已完成端到端集成验收。

## 本次结果

- 平台 **185 项通过**：原平台 93、可移植契约 27、共享运行时 8、共享所有权 10、A2A 47。
- Symphony / bridge **50 项通过**：原有 41，新增共享所有权集成 9。
- 合计 **235 项通过，无跳过**。其中 12 项使用真实临时 Temporal 服务（开发流程 8、A2A 端到端 2、bridge 2）；A2A 另包含官方 SDK 的 loopback TCP 测试。
- 另在仅安装基础依赖的环境确认：三个 A2A 测试模块按预期跳过，不因缺可选 SDK 导致原平台测试加载失败。

另已验证：

- 九份 JSON Schema 2020-12 均通过结构校验；两套完整实例的 18 份快照通过实际 jsonschema 4.25.1 校验。
- 新格式编译后的 spec 与原 v2 编译结果逐对象相等，保留原请求/profile 摘要。
- 与上一份 HTML 内嵌部署包逐字节比较，原开发 workflow、contracts、registry、已发布 task profiles 与训练运行时共 30 个文件未变化。没有重写存量 Temporal 历史。
- HTML 桌面/手机交互、全部下载目标、包字节、复制、清单保存、搜索、折叠与打印已按浏览器验证记录检查。

## 新增覆盖

| 边界 | 验证内容 |
| --- | --- |
| 可移植契约 | 两类任务无损转换、拆分包校验、冻结深拷贝、纯快照恢复、注册表、范围/风险/容量/基准与能力拒绝 |
| 不可信输入 | 重复 JSON 键、非有限数、未知字段、包摘要篡改、符号链接、路径逃逸、不支持的工作流和角色独立性变更 |
| 共享运行时 | 唯一执行 ID、原始输入核对、已结束任务不重启、网络错误不当作不存在、取消只传递意图 |
| 多入口所有权 | Symphony / A2A 排他、持久重启、并发认领、精确摘要、已释放修订不可重开、旧释放不影响新任务 |
| A2A 协议 | 官方 SDK 的发现、Send/Get/List/Cancel；实际 ASGI 路由与 loopback TCP；版本、不可用能力、请求大小、调用方隔离 |
| A2A 可靠性 | 重复消息、响应丢失、重启附着、过期准入、取消先于启动、跨网关台账身份、晚到/过期候选证据 |
| A2A + Temporal | SDK 经协议网关进入真实临时服务；等待人批准后交付候选；取消未确认保持 input-required 并阻止其他入口 |
| 可信清理 | 准确任务/快照/run 绑定、运行未结束时拒绝、人工停止证据、先存终态和审计再释放、重复恢复不可替换证据 |
| 原有开发与桥接 | 原契约、DAG、审批、真实 Git 范围、harness、训练兼容、bridge 恢复和取消语义回归 |

独立审查复现并修复了“等待资源后过期任务仍启动”“取消后的未启动任务仍启动”“不同网关台账共用所有者导致错误释放”三个问题；另补齐终态消息、版本错误响应和人工恢复边界。相关场景已经加入回归测试。

## 证据边界

真实 Temporal 测试使用临时测试服务和明确标记的 synthetic executor。它证明协议、编排、审批与状态转换接通，不证明真实模型已生成正确代码，也不代替项目 CI 和身份验证。测试服务报告的 heartbeat capability 警告不影响本次无 heartbeat 阶段模型；未据此验证生产心跳恢复能力。

A2A 测试使用官方 SDK，但没有运行完整官方规范认证套件；本平台严格拒绝未知扩展，未宣称全功能或全规范认证。未实现 SSE、push、REST/gRPC、0.3 兼容、多租户路由及任意远程角色执行器。

当前 bridge、A2A ledger 和共享所有权使用单协调主机持久本地 SQLite。多副本高可用、NFS、跨主机事务存储、组织 SSO、云部署、真实目录 ACL、真实 Codex/CI 与证据下载服务仍须按项目接入验收。绑定中的能力声明不是权限凭证。

最终 REVIEW_READY / A2A completed 只表示交付候选；不自动合并、生产迁移或部署。合并前需在当前目标分支和现行策略上重新验证。没有宣称形式化证明全部代码正确。
