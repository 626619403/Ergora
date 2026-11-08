# AC2：Agent 后端独立审查

日期：2026-11-08。审查者：`/root/agent_backends_review`，由全新上下文开始；需求与 Standards 另由两个全新上下文独立补查。先读原始要求、审查边界、基线和实际差异，再读作者交付说明。遵循项目 `AGENTS.md`、`maintainable-project-delivery` 的独立审查规则及 AIHERO 的 `code-review`、`codebase-design` 原则。

初审结论：需求轴在所查运行合同中未发现行为回归；可维护性轴有一项 **P3 / R-1 待处置**。它没有已证实的错误准入，但本片所有权整理尚未完整，不应在处置和同片复核前登记完成。

## 输入与身份

基线及初审 HEAD：`556410a7a482b11172bc5f66779dc6463fa0322f`，分支 `refactor/architecture-foundations`。审查的是未提交工作树；初始差异与十文件身份固定于 `.ergora/checks/ac2-backends/review-tracked.diff`、`review-scope.json`，没有用空的 `baseline...HEAD` 代替实际差异。

十文件为 `docs/PLAN.md`、`docs/architecture/current.md`、`docs/plans/2026-11-08-agent-composition.md`、`docs/delivery/2026-11-08-agent-backends.md`，`src/ergora/agents.py`、`bindings.py`、`stage_driver.py`、`tools.py`、新增 `agent_backends.py`，以及 `tests/test_agents.py`。随后补查 `README.md` 和 `docs/AGENT_BACKENDS.md` 两处接入导航。实现和测试始终匹配初始 scope；计划及交付记录追加包内检查结果，已按当前内容检查，其新身份另存 `independent-identities.json`。

AC2仅整理既有 Codex、Claude Code、mini-swe-agent、command 的共同 Interface 和局部实现；不把后续多成员、专长资源、嵌套、祖先强继承、权限或持久调度算作本片已实现。原六阶段、候选证据、进程生命周期、旧数据和公开 schema 来源是保留合同。

## Standards / 可维护性

### R-1 · P3 · 注册准入仍重复拥有 command 正式协议规则

位置：[registrations.py](../../src/ergora/registrations.py#L78) 第78行、[agent_backends.py](../../src/ergora/agent_backends.py#L170) 第170行、[bindings.py](../../src/ergora/bindings.py#L18) 第18行。

实际注册开发模板且 command 绑定省略 `protocol` 时，`registrations._prepare` 先以普通模式调用通用校验，再按 `implementation == "command"` 自行拒绝；正式任务快照则通过 `agents.validate_binding(..., formal=True)` 由 `CommandBackend` 拒绝。同一规则在两个真实生产路径保留了两份实现。当前拒绝结果一致；问题是本片已经提供实现所有者，却遗漏这个正式消费者，后续调整正式协议仍需跨层同步。

不能仅凭出现厂商判断就判错：模板是否走正式开发执行属于注册领域，普通数据校验也可保留。此项依据是 AC2 明确把后端正式配置归各实现，以及现有 Interface 已能直接表达该规则。

最小修正：注册模板的 Agent 角色统一调用 `agents.validate_binding(role, binding, formal=template != "training-optimization")`，移除内层 command 分派与协议检查，保留训练/开发模板的领域判断和外层通用绑定校验。三个模板的 `contract["agents"]` 均为 Agent 角色；无需新包装或 schema。复用既有开发模板缺协议拒绝检查，并核训练模板普通 command 原行为。

其余所查职责没有新增 finding：ABC 的四个实现有真实选择和调用路径；`Invocation` 聚合实际调用资料；构造、原生结果提取、Codex 配置和平台拒绝位于本实现。`agents` 的兼容入口、通用结果验证及摘要有独立职责；`tools` 复用诊断与固定探测。类映射只在后端家族本地，公开配置和能力仍由未改动的 `components.json` 提供。未发现需要删除的空包装、无消费者的扩展或新冗余 CI。

## Spec / 需求符合性

所查运行合同无正确性 finding。四种后端使用共同 ABC 和局部映射；原命令参数、stdin、结果归一化及公开兼容入口保持。结构化结果只在进程成功后校验，非成功、错误 envelope、缺失或非法结果不会成为验收证据。超时、取消和后代清理由未改动的 `processes` 及原监控器拥有。

doctor 的 command 后端不产生任意 argv 探测；请求内按完整绑定去重、统一主动预算、凭据输出丢弃及版本提取保留。`stage_driver` 统一转交 `codex_config`：唯一正式请求构造者 `reference_executor.model` 始终提供该字段，非 Codex 实现不读取其文件。未将手工删字段的内部请求视为已有公开合同，也未建议恢复上层厂商分派。

本轴没有观察到新组合、资源权限或调度越界；R-1 是上述所有权要求留下的局部缺口。

## 检查与限制

- 独立核源码、wheel ZIP 和非 editable 安装的353个文件身份一致，wheel SHA256 为 `788f44c07d790edb764d431fd114da5c424230d816ec357c74d55f959af6ebfe`；283冻结文件匹配公开 manifest。证据为 `independent-identities.json`。
- 独立运行 `independent-probes.py`，20项检查通过：与基线对照四后端 argv/stdin及正式 Codex 配置；缺失/非法配置、非法绑定、非 Linux 平台拒绝；真实本地 Python 输出合法 JSON 后非零退出或超时仍不接受。命令构造对照使用模拟 runner，不能当真实厂商 CLI 验收。
- 新 wheel 独立复用三组 doctor 检查，4 passed / 1.82秒，覆盖任意 command 不执行、Codex 固定探测去重和输出丢弃、真实子进程耗尽统一预算。命令及限制见 `independent-validation.json`。
- 已核作者原始命令与日志：源码125 passed / 12 skipped；新 wheel 50 passed / 15 deselected / 零skip，包含原 command/Codex 四组合六阶段、模板说明拒绝及取消清理。此处区分作者实际运行与本审查者的独立检查，没有重复整套矩阵。

未实测真实模型、认证、MCP装载、权限强制、mini/Forge固定 SDK、原生 Windows、嵌套恢复、性能或本候选远端 CI；模拟平台拒绝不等于原生 Windows 验收。静态文档记录为6份 Markdown / 262链接 / 30条 parser，初审未把它当最终归档身份。尚待 R-1 处置、受影响验证及同片复核；提交、普通推送与精确 CI/远端终结另行记账。

## 同片 r2 复核与当前结论

初审正文及初始证据保留；以上三处源码链接仅修正为仓库内可解析的路径和行锚点。修后输入固定于 `review-r2-scope.json`、`review-r2-tracked.diff`：在原范围上增加 `registrations.py` 与 `tests/test_registrations.py`，原后端实现和测试身份保持。已重新检查实际差异、两个审查轴的补查结论及作者逐项处置。

**R-1 已关闭；需求符合性与可维护性两轴在本片范围内通过，无未解决 finding。** `registrations._prepare` 现统一调用 `agents.validate_binding(..., formal=...)`，保留模板领域判断；后端单独拥有正式 command 的协议和能力拒绝。新增训练单模板普通 command 注册检查经公开入口核发布与绑定保存；已有开发模板缺协议、缺能力和无发布副作用检查保留。它不证明示例外部命令能够执行，也不新增授权语义。

已核实际修后证据：源码 `test_registrations / test_project_configuration / test_architecture_boundaries` 为69 passed、零skip；最终非 editable 包的受影响注册及导入图检查为17 passed、45 deselected、零skip。首个受影响命令误列不存在的 suite、exit4且零执行已单独保留，不作为通过。原125项源码与50项包内结果仍绑定初版；未把不同范围相加为一个新矩阵。

独立核最终源码、wheel ZIP 与非 editable 安装353个文件逐字一致，283冻结文件继续匹配 manifest；`independent-final-identities.json` 记录最终 wheel SHA256 `14eb4dca11f798daa06aa8064321fc845b0772f9eac0e43f56f802215f883ffe`。独立比较两包确认只有 `registrations.py`、README说明对应的 METADATA 和 RECORD 变化。因此初版后端探测和生命周期证据仅延续到字节未变的实现，注册变化由上述修后检查另行覆盖。

本地实现及独立复核可收口。前述未验范围保持；本候选普通提交推送、最终文档身份及精确双 OS CI/远端终结仍待后续登记，不从本次本地通过推导远端验收。

## 固定候选、CI与即时远端终结

2026-11-08，同一独立审查者继续核固定候选 `cc7f95f8ab1a696f2f0df2f8216e23b383011b35`。其唯一父提交为 `556410a7a482b11172bc5f66779dc6463fa0322f`；15个提交文件逐项匹配 `final-scope.json`，原 tracked 差异精确匹配归档，源码与测试保持修后身份。14:58:34 UTC已核最终7份文档、267本地链接及30条 parser 的身份和处置记录；独立输入副本在 `.ergora/checks/ac2-backends/independent-final-inputs/`，初版记录未覆盖。

独立于作者的汇总，15:13 UTC实际只读 GET 官方 [CI42492287287](https://github.com/626619403/Ergora/actions/runs/42492287287) 的 run、两个 job 和明确 `attempt=1&batch=0&size=200` 批次。run 为 Success，批次 `hasMore=false` 且完整列出两项 completed/success 作业。Ubuntu `128767072083` 的构建安装 wheel、包内参考身份、原生应用回归三个必要步骤全部 success；Windows `128767072294` 的同三项及 PowerShell 5.1 安装升级四个必要步骤全部 success。各步骤均有完成标记，日志 URL 绑定完整候选 SHA 和对应 job；未见失败、取消或超时步骤。证据为该目录内 `independent-live-fetches.json`、`independent-ci-verification.json` 及原始页面；未下载测试日志或重跑行为矩阵。

取证过程的局限已核清：作者首次所记“辅助脚本已增加批次大小”实际未生效，原默认响应仍为 `hasMore=true`。作者已明确纠正并保存前态；独立复取和作者实际修正后的完整批次均为两项、无后续页。未把不完整批次、无认证 API403 或空日志链接误取的主页当通过证据。此处只修取证辅助流程及记录，仓库 CI 工作流未改。

**15:14:45 UTC 独立 `git ls-remote` exit0，远端 `refs/heads/refactor/architecture-foundations` 精确为 `cc7f95f8ab1a696f2f0df2f8216e23b383011b35`。** SSH设置仅在进程内读取既有配置，未打印、修改或推送；记录为 `independent-remote-verification.json`。候选之后的工作树仅有三份已告知的状态/计划文档追加；AC3a备份恢复后的定义/资源身份要求仍是待实施验收，未混入新生产代码。

**固定候选、必要双 OS CI及即时远端终结通过，无新增 finding；R-1保持关闭，AC2可完整关闭。** 本候选CI补足其配置范围内的 Windows 原生回归和安装升级步骤；真实模型、认证、MCP装载、权限强制、固定 SDK、嵌套恢复及性能等未验范围仍保留。后续状态归档不改变本次固定生产候选与原证据范围。
