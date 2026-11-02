# F3.2 独立需求、结构与性能审查

日期：2026-11-03。审查者：独立 Codex 审查上下文 `/root/f3_task_creation_review`。先读取原始 diff、新文件及相邻调用，再读取作者交付记录；未继承实现对话。遵循项目 AGENTS、maintainable-project-delivery 和 review-pr；审查者未修改生产或测试、安装依赖、操作真实服务、提交或推送。

## 范围与身份

- 分支：`refactor/architecture-foundations`。精确基线：`44e98158cdc08e15bc848e0347469fee132024ea`；审查对象为其上的未提交 F3.2 工作区。
- 生产差异：`bindings.py`、`cli.py`、`reference.py`、`reference_executor.py`、`tasks.py`、`web.py`；完整读取新增 `reference_task_creation.py` 和 `data/schemas/task-definition-v1.json`，未仅依赖 tracked diff。
- 测试差异：`test_architecture_boundaries.py`、新增 `test_task_creation.py`。对照原生 `create_task`、portable 编译/验证、`core.write/read`、safe_file/read_raw、State 锁/事务、registrations、projects 和执行器快照调用。
- 文档差异：README、USAGE、PROJECTS、AGENT_BACKENDS、PLAN、详细计划、当前架构、reference 边界及本切片交付记录；需求依据为[设计及验收](2026-11-03-task-creation.md)和[详细计划 F3](../plans/2026-11-01-all-in-one.md#f3-正式开发任务-cliapi)。
- 修正复审身份：`reference_task_creation.py` SHA256 `cd614f8f85721feb7865534eec9d2ba9175e96a41252fbe08c5de5100dd64098`；`test_task_creation.py` SHA256 `25170d591fab9977403b0a72413dc3d955d48d32c20d1cff38df358dc20fc515`。最终包及 CI 身份另行核对，不能沿用初版包结论。

## 需求符合性结论

源码及本次独立定向检查通过，初审一项 P2 已修正并复审关闭，当前无未解决的源码阻塞 finding。发行验收仍需修正后的包、适用回归、无可选 SDK 旅程和精确两 OS CI 证据，不据本报告宣称全部平台已完成。

两开发模板在父进程拥有的临时目录复用原 `create_task`/portable；preview 不发布真实任务。create 绑定明确 revision、控制目录、登记身份、定义、完整编译材料和角色快照，先存意图，再发布绑定及其余原生文件，最后发布 spec 和回执。同 ID 锁、原 immutable writer 和原意图摘要负责重试/冲突；resume 从原材料恢复，不重新编译或重选角色。外来控制目录/项目、legacy 目录及漂移内容有明确拒绝路径。CLI/API 共用 tasks，API 沿用本地同源写保护。

本地 `published` 只表示合同发布；`runtime_status: not_queried`、`execution_started_by_operation: false` 没有把原有任务实际运行状态冒充为未运行。工作流提交、批准、取消等仍属于 F3.3，未在本切片扩展第二套运行状态或生命周期。

## 已关闭 finding

**P2：大于 1 MiB 的合法创建意图无法幂等重试或恢复。** 初审位置为 `reference_task_creation.py` 的 `publish` 中无条件 `core.write(self.intent_path, record)`；关联 `__init__` 将 `core.read` 替换为默认 1 MiB 的 `document`。

独立隔离复现使用 repository-governance，一工作单元，acceptance 为 `[str(i) + ':' + 'a' * 3990 for i in range(51)]`：定义 204,167 字节，各原生合同最多 445,662 字节，意图 1,075,925 字节，均满足各自声明的上限。preview、首次 create、creation 均成功；随后相同 create 与 resume 均报 `BLOCKED: File exceeds size limit`。原因是 load 允许 16 MiB，而原 immutable writer 比较既有意图时调用了普通合同的 1 MiB reader。发布中断后的同类任务因此不能履行恢复合同。初审置信度 100。

作者采用最小修正：`run` 在同 ID 锁内 load/validate 原意图后，只有 `saved is None` 时才保存新意图；相同 create 和 resume 复用已验证的原意图。没有放宽普通合同 reader，也没有复制 atomic writer。新增合法大意图的完整发布及 spec 前中断两种回归，检查 status、resume、重复 create、逐合同上限和原意图字节保持。审查者读取修正并独立运行新增回归所在的全部创建测试；finding 已关闭。

## 结构、复用与控制流结论

范围内通过，未发现需要新增抽象或迁移所有权的维护性问题。

- `bindings.development_snapshot` 有 tasks 和 reference_executor 两个实际生产消费者，抽取保持既有四角色快照格式。创建时写快照与原执行器读取已有快照相容；旧任务首次选择的检查仍在原执行器。
- `reference_task_creation` 是固定子进程的原生边界。私有 `_Creation` 虽仅由该入口创建，但共同持有编译暂存、登记上下文、意图路径及锁内发布生命周期，集中在该 owner 有实际理由；无需通用 TaskRepository、Runtime 基类或第二套插件/任务引擎。
- 编译、JSON 内容身份、DAG/可信 portable 检查、安全读取和不可变写入均复用既有实现。新增检查位于外部定义、登记漂移、持久恢复材料和文件冲突边界；未发现为不可达状态增加分支或下沉业务到 CLI/Web 的问题。
- SQLite 写保留覆盖发布，防止 revision 中途变化；执行目录的同 ID 文件锁协调跨进程发布。锁等待和文件操作都包含在原生子进程的单次 30 秒预算内；数据库写锁等待使用既有 State 连接超时，目录清理另计，30 秒不是整个 CLI 的总时限。

## 性能审查及证据边界

未发现已证实的物质性性能回退。该功能不进入模型/阶段热路径；新发布固定七份合同，普通合同逐份至多 1 MiB、意图至多 16 MiB，portable compiled 另有原生 512 KiB 限制，不按历史任务数量扫描。重复 create 按设计重新编译以核对精确预览，resume 使用保存的 compiled/materials，不访问较新 registry 重新编译。写保留串行化同一控制库的写请求，等待成本是 revision 原子性的明确代价，不能从小合同测量推导高并发吞吐。

已检查作者初版性能脚本和 JSON：非 editable 基础包、Python 3.12.3、两模板各 20 次 preview/幂等 create/resume，总 127 次 CLI；初版包 SHA256 `15bd9d3cc38aef5cd81b463956379453947dda820bc9ef61269291b12d86f67c`。preview 中位约 354–359 ms、幂等 create 422–446 ms、resume 410–420 ms；该脚本实际检查无 fastapi/temporalio/gepa、无 requests/receipts，未测模型或工作流。上述为修正前历史观测，修正后性能与包核对待补，不把它作为当前候选的最终性能结论或优化收益。

## 实际检查与剩余验收

审查者执行：

```bash
git diff --check 44e98158cdc08e15bc848e0347469fee132024ea
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv-dev/bin/python -m pytest -q tests/test_task_creation.py tests/test_architecture_boundaries.py --basetemp=/tmp/ergora-f3-creation-review-tests
```

均通过；独立定向结果为 **36 passed，15.69 秒**，一条既有 Starlette/httpx 弃用警告。另执行前述临时目录的大意图独立复现，观察到确定失败后才发出 finding。所有运行限于隔离夹具，未运行完整测试集或真实服务。

作者记录的初版 34 项/82 项定向、初版完整 Linux 376 passed / 19 skipped / 36 子测试及初版 341 文件×源码/wheel/两安装，只保留各自原身份；不能代替修正后的最终包验收。本报告写入时，最终包、基础旅程及完整适用回归正在重跑；Windows 原生编译/读取与精确两 OS CI 尚未核验。新创建合同的真实工作流/模型/全六阶段旅程、强杀/断电及敌对目录所有者并发替换不由本次定向检查证明，F3.3/F3.4 和既有可信文件系统边界继续适用。
