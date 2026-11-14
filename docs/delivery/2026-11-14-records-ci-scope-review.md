# G1d-CI 独立评审

评审者：`records_ci_scope_review`，2026-11-14，新 fresh-context。先读委托中的用户要求、切片合同及实际工作流／差异，再读作者交付叙述；未继承实现过程。遵循 `AGENTS.md` 与独立评审要求，仅检查原件并写本报告。

## 范围与身份

固定基线及检查时 HEAD 均为 `6c7c45f79e499dde83d9880043342710a28d7809`；候选是该 HEAD 上尚未提交的本片变更，不是已发布 SHA。

完整读取基线与当前 `.github/workflows/portability.yml`、两份新增完整文件 [具体合同](../plans/2026-11-14-records-ci-scope.md)／[交付记录](2026-11-14-records-ci-scope.md)，以及 `docs/PLAN.md` 中 G1d-CI 状态。另核 `pyproject.toml`、`scripts/ci/run.py`、`scripts/ci/linux-groups.json`、`scripts/ci/pytest_phases.py`、参考导入脚本及相关测试消费者。G1c 手册与 G1b 记录同处工作树，但不纳入本片批准。

|原件|检查身份 SHA-256|
|---|---|
|基线 workflow|`4a23020b277de1fa3d07db42918314127a013e01cad8ebf0cd9e020109774b64`|
|当前 workflow|`be814a956237b8a64258f396fa81a972ff764ceaa3ea16ffefa8e82be89a4353`|
|新增本片合同|`1433fa04072b737910f5d7e0dfa6ec07c2c4a95bf20e95435c2ef79c9838e6ed`|
|修后本片交付|`c597a59676bd14edc72f4d0965f0be2c95d889884ff87cf08d640c88c85361eb`|

## 需求符合性

**本地 approve；开放 finding 0。** 实际工作流差异仅第 6 行增加 `docs/delivery/evidence/*.json`。去掉此项后，完整配置解析结果与原件一致；当前字节也恰为基线的一次字面插入。产品、schema、测试、脚本、安装器、依赖与 CI 执行内容均无本片变化。

直接读取 [GitHub 官方路径过滤说明](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#example-excluding-paths)及[文件路径模式说明](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#patterns-to-match-file-paths)：模式从仓库根匹配完整路径，`*` 不跨 `/`；全部变更路径被忽略才省略 workflow，任一路径未被忽略仍运行。因此：

- 在原有分支过滤条件下，直接子级交付 JSON 与已有忽略项组成的纯记录 push 可以省略矩阵。
- 嵌套 JSON、其他文档资源，以及产品／schema／例子／测试／脚本／依赖／工作流自身的变化仍保持原触发；混合 push 不会因包含交付 JSON 而跳过。
- `pull_request` 与 `workflow_dispatch` 保持原入口，权限、concurrency、artifact、时限、完整 jobs 与步骤保持。原六 Linux 分组加 Windows 和 plan 仍为八 job，原 30 必要步骤未削减；这不是本候选已运行成功的主张。

生产／测试／脚本及依赖文件中未找到该证据目录消费者；包数据仅来自 `src/ergora/data`。邻近的文档读取是安装帮助或参考 HTML 导入，不读取该 JSON 目录。现有实际边界支持把它视为交付摘要，而不是随包资源或测试输入。

## 可维护性与冗余

**本地 approve；开放 finding 0。** 改动位于拥有触发语义的现有 workflow，复用 GitHub 原生过滤；没有新包装层、过滤脚本、CI job、产品断言或镜像实现的测试。完整 jobs 与分组消费逻辑未变，必要真实行为覆盖保持。

私有一次性静态检查只证明语法、原件身份及范围，没有接入产品或另造 glob 解释器。减少纯记账触发的收益可由官方规则推导；本评审未测量 CI 时长、额度或产品性能，不据此扩大性能结论。未来若接入该目录为实际输入，合同已要求同步修订触发边界。

## Finding 与处置

**R1／P3，已关闭。** [交付记录](2026-11-14-records-ci-scope.md)第 5 行初稿仍写“尚未修改配置”，与第 9 行及实际差异冲突；恢复工作时会混淆本地实现与发布状态。最小修正是明确“配置已在本地修改，尚未普通发布或实测云端触发”。作者已按此修正，评审者直接复读完整文件并核上表修后身份；无开放项。未发现本片其他需求或维护性问题。

## 已检查与限制

- 独立核完整基线／当前 workflow、tracked diff、两新增文件及相邻消费者；产品／测试／脚本／依赖 diff 为空。
- 使用现有 PyYAML 6.0.2 `BaseLoader` 独立核配置与字节差异；完整 jobs 相等，六 Linux 分组和 Windows 选择保持。
- 只读核私有 `records-ci-scope` 域中的 `static-r1.py`、`static-r1.json`、`workflow.diff`；保存的基线／当前／diff 指纹与现场相符，diff 指纹为 `d735ce469edb676c115b00ab2fc1f3c48fd59e3a79095fe1ba3d44f4ad5b2aff`。未重跑会写产物的原脚本。
- tracked `git diff --check` 返回 0；两新增完整文档的 no-index 检查均无空白诊断。未安装依赖、运行产品测试、取消 CI、提交、推送或外部写入。

本结论只批准上述本地切片。静态解析和官方规则核对不能替代 GitHub 实际触发与最终候选 CI，也不批准 G1c 或整个工作树。

## 尚缺的终核材料

1. G1b 自己的 `43589988699` 终态原件及原 reviewer 闭合。委托与记录将其列为在途，本评审未查询远端最新状态，也未取消它。
2. G1c 分别审查后共同候选的精确提交、完整含新增文件的发布范围、普通推送与完整远端 Ref，以及本 reviewer 的固定发布补核。
3. 该共同候选因变更 CI 文件而产生的自身原八 job／30 必要步骤终态及原 reviewer 终核；不能借 G1b 或其他候选的成功。
4. 完成该候选后，最终纯记录同步的实际路径适用性、普通推送与完整 Ref 核验；保留前述候选真实 CI 原件，后续无新 run 不构成产品通过证据。

以上材料到齐前，本片不能标记精确交付闭合，本报告不预批未来运行。

## 最终本地汇总身份补核

2026-11-14，同一 reviewer 复核新增[公共摘要](evidence/2026-11-14-records-ci-scope.json)、更新后的本片合同／交付全文与四份固定原件。HEAD 仍为 `6c7c45f79e499dde83d9880043342710a28d7809`，workflow 仍为上表 `be814a…`，产品／测试／脚本／依赖 diff 为空。

|本次本地记录|SHA-256|
|---|---|
|本片合同|`79ffaf481f226fda35285e7056862bea06cfd4890c7bfe6e5923070d189ab897`|
|本片交付|`4f6478b26a9622094db0812cf1103dd9ce4233ade2e57d67b75546c2dd83b101`|
|公共摘要|`092070970fe59358ce3e6e10de58112efd830a1fc4c694ccbfdbe10de9bd5f2e`|

摘要的 `validation` 与原 `static-r1.json` 完全相等；本地两轴结论、开放 0／0 和 R1 关闭均准确投影原独立报告。四个不同引用逐件核字节与 SHA-256：`static-r1.py` 2,570B、`static-r1.json` 1,176B、`workflow.diff` 534B、`independent-local-r1.md` 5,871B，合计 **10,151B**，全部匹配摘要。独立快照身份 `84dff15a1e601e3d05a9cb0ac1f667503957394f6b41ad7d223fb7e554a9393c` 与追加本补核前的完整报告相同；追加内容不冒称已经包含在旧快照中。

本片合同仅新增勾选本地独立审查，交付保留 R1 修后句并追加实际结论和原件索引；固定发布、自身 CI 与最终记录同步在合同和摘要中仍为待验。三份记录的完整新增文件空白检查无诊断，没有新增测试或外部操作。

**最终本地需求／维护性均 approve，开放 0／0。** 上述终核缺项保持；G1b 的 CI 仍按提供材料记为在途，本次未查询远端，也不预批后续共同候选、自己的八 job／30 步骤或最终纯记录同步。
