# F4.3a：待批计划材料读取独立审查

日期：2026-11-04。审查者：`/root/task_plan_review`，新的 fresh-context 独立上下文；以原始范围、验收和实际差异为准，核查邻近调用、实现记录与运行证据。项目和文档根分别为 Ergora 与其 `docs/`。遵循 `AGENTS.md`、maintainable-project-delivery 及 independent-review 要求。

需求符合性：**本地实现与验收范围通过**。可维护性：**通过**。本次检查范围内无正确性或可维护性 findings，无待修源码阻塞。精确提交、两 OS CI 及实时远端核对尚未执行，需同片后续复核；本报告不将 F4.3a 或完整 F4 记为最终交付。

## 精确范围

基线及检查时 HEAD 为 `581144c3d6205bb400577a79b694f53a8638cf15`，分支 `refactor/architecture-foundations`；审查的是其未提交差异和新文件。

- 五个生产文件：`src/ergora/tasks.py`、`reference.py`、`reference_task_approval.py`、`cli.py`、`web.py`（后四者同属 `src/ergora/`）。新测试为 `tests/test_task_plan.py`，SHA256 `6a9b2ae3f893de6314244eb18f32ab8527c9c3162a19fecd3b32b08427c8f41f`。
- 七个文档：`README.md`、`docs/PLAN.md`、`docs/USAGE.md`、`docs/architecture/current.md`、`docs/plans/2026-11-01-all-in-one.md`、本片实施记录及 F4.2c 组合旅程记录。审查落盘后本报告加入范围。
- 独立重算源码、wheel 及开发/base 两非 editable 安装的全部348文件相等；283冻结 reference 文件与前片身份相等。wheel SHA256 为 `4160cfdd64a69e0dbb713bda584a57c2cfad939eb1895c28d055836a62c90037`；五个生产文件逐项对应本片 `package-identity.json`，结束前再次核对未变化。

邻近只读核查包括 `_Submission`、`_Creation`、原运行验证、控制状态连接、原生 workflow/adapter/activities/contracts、CLI 错误合同、HTTP 错误映射及现有 CI 发现规则。未修改生产或测试源码、安装依赖、提交、推送或发任务信号；唯一项目文件写入为本报告。

## 需求与维护性依据

- [tasks.py:188](../../src/ergora/tasks.py#L188)、[CLI:119](../../src/ergora/cli.py#L119)、[Web:303](../../src/ergora/web.py#L303)：必须提供原 run 与精确 plan SHA，输入在项目/原生访问前检查，预算为1–60秒；CLI/GET API 进入同一任务用例。控制库读取在网络调用前结束，没有新增 `BEGIN IMMEDIATE` 或持续写锁。
- [reference_task_approval.py:19](../../src/ergora/reference_task_approval.py#L19)：复用原 `_Submission.submitted/lookup_run`，因此创建快照、spec、原提交回执和 SDK memo 归属保持同一所有者。要求运行中、`AWAITING_PLAN_APPROVAL`、原 request SHA 及所选 plan SHA；没有建立另一状态机。
- [reference_task_approval.py:36](../../src/ergora/reference_task_approval.py#L36)：实际 SDK 按100分页流式读取连续原 history 前缀，在原 plan 的 `dev_submit` 调度处停止；使用该连接的 converter/codec。解码前的单 payload 守卫覆盖 SDK 类型提示可能忽略额外 payload 的可达情况；解码后核上下文、冻结 spec 和 job。请求 envelope 必须与原 context 的精确规范 JSON 身份一致。
- [reference_task_approval.py:68](../../src/ergora/reference_task_approval.py#L68)：本地 receipt 的 canonical SHA 必须等于当前待批 SHA，再核 job/state 关联。已查原生 workflow 第196行确实对接受的整个 plan receipt 求摘要；这里无需复制原 FileAdapter 对已接受 receipt 的完整校验器，也不会误用 execution-plan 文本摘要作批准身份。
- [reference_task_approval.py:74](../../src/ergora/reference_task_approval.py#L74)：只读冻结 profile 的 plan 材料，复用安全路径、no-follow、常规文件和有界读取；逐文件核 SHA、严格 UTF-8，单件256 KiB、完整响应1 MiB。缺失、超限、路径、编码及内容错误均失败，不以截断或空材料成功返回。保留 receipt 身份不要求读取其中额外日志。
- [reference_task_approval.py:248](../../src/ergora/reference_task_approval.py#L248)、[reference.py:356](../../src/ergora/reference.py#L356)：读取分支不构造 `_Approval`，不发布 owner receipt/decision、不 authorize 或 signal；环境加载前确定只读操作，使超时/未找到/RPC失败指向原 run 状态查询。现有批准过程保留，错误分支没有引入隐式恢复。
- 所有权和复用适当：`tasks.plan` 有 CLI/Web 两个生产消费者；reference 函数是现有原生边界端口；单调用的 `_plan` 是同一审批所有者内的完整私有读取算法，未为它新增通用文件、包装层或资产服务。新增守卫针对外部输入、原持久身份、网络与文件变化，没有要求删除的无依据防御分支。
- 成本与测试边界适当：不累计整份 history，只处理所需前缀和冻结材料；响应序列化计入大小界限。新32项使用轻量文件和真实 SDK 消息/分页/codec，原批准/运行集成检查沿用现有夹具。现有 `portability.yml` 自动发现 `tests/`，无需新增 CI 步骤；未删除旧反例、平台检查或放宽超时。没有基于这两条小计划推导大规模性能提升。

## 实际核验

1. 独立执行 `env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv-dev/bin/python -m pytest -q -p no:cacheprovider tests/test_task_plan.py --tb=short`：exit0，32 passed、1既有 Starlette 弃用 warning，1.62秒。覆盖错误 run/phase/plan/request、连续前缀、缺 plan、多 payload、上下文/envelope/receipt/job 身份、缺材料、摘要/UTF-8/大小/路径/symlink/目录、边界完整返回、网络错误及 CLI/API 转发。
2. 核作者原命令与原日志：联合源码90项 exit0（266.68秒），最终安装包新合同32项 exit0（1.93秒）；两者证据和范围分别保留，未替代当前完整回归。作者早期测试失败和修正没有被记为通过。独立 `git diff --check` 通过。
3. 独立重算发行348文件及283冻结身份；核 base 无 Temporal SDK 的记录、非 editable `direct_url.json` 和包安装命令。真实 plan CLI/HTTP 均由 base 环境进入登记的原生 runtime；旧 status 仍按自己的 SDK 合同使用开发环境。
4. 核真实 `native-acceptance-v5-command.json` exit0、16.69秒，逐项重读两模板 CLI/API 原响应、命令及请求。每模板三材料完全相等，并独立对当前原 artifact 重算字节/摘要/UTF-8：合计6849/7889字节；HTTP 响应9412/10403字节。receipt canonical SHA 与原 pending SHA 相等。错误 run 均 CLI exit2、错误 plan 均 HTTP400，拒绝文案正确。
5. 审查者另直接调用原 Temporal 服务，只 describe/query/history，不运行验收脚本：两原 run 均 RUNNING、待批、无活动 stage，原 spec 与 submission memo 严格匹配；各112个连续事件、零 signal、唯一 plan 调度事件56；原 context/envelope/receipt 身份一致。这是独立实时观察，区别于作者 CLI/HTTP 转录。
6. 独立重算当前54份原生文件，与 F4.2c `native-after.json`、本片 before/after 全部相等。核脚本 HTTP 在 finally 被 SIGTERM 并 wait，记录 exit -15，审查者确认该 PID 已消失；不将其表述为自然 exit0。核 retained-services 原命令 exit0，报告原五服务 RUNNING、training-worker STOPPED。
7. 文档初核原记录为7文件303链接/锚点、27条 README parser 命令通过；README/USAGE/current 三份公开行为说明仍与该检查摘要相同。状态记录已追加本次结果，最终全范围文档检查由提交前步骤完成。

原生验收前四轮失败（端口占用、GET 就绪路径、旧 status 的无 SDK 调用、错误退出码预期）分别检查了保留脚本/原日志；最终通过只绑定第五轮。没有为这些验收假设修改生产合同。

证据位于本项目私有 `.ergora/checks/f4-task-plan/`：`source-targeted-*`、`wheel-plan-*`、`package-identity.json`、`native-acceptance-v5-*`、`native-acceptance.json`、各模板 `*-plan-cli.*` / `*-plan-api*` / `*-wrong-*`、`native-before/after.json`、`http-command.json` 与 `retained-services-*`。本报告不复制私有运行路径、凭据或计划正文。

## 限制与后续

本地审查未重新执行共享重型90项、完整 Linux 回归或 Windows运行；已核它们各自现有证据的实际范围，当前精确候选 CI 仍待产生。无源码 findings 不等于已提交或远端已验。最终静态文档检查、精确提交/两 OS CI/实时远端身份应在完成后补同片复核。页面材料/批准/取消/导出和后续观察仍属于各自后续切片，本次没有验证这些尚未实现的页面流程。
