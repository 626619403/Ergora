# AC3b.1：历史完整性与当前准入独立审查

日期：2026-11-09；初审完成时间：2026-11-08 17:56:25 UTC。初审为Standards无finding、Spec两项P2。**当前r2本地复审两轴通过：SP-1代码修正关闭，SP-2有依据的文档纠正处置关闭；精确CI及远端交付仍待验。**原始发现和初审证据保留如下。

## 审查身份与精确范围

协调者为fresh-context reviewer `definition_admission_review`；Standards与Spec分别由其新建的fresh-context子审查者`standards`、`spec`完成，均使用`fork_turns: none`。按[AGENTS](../../AGENTS.md)、[AC3b.1原计划](../plans/2026-11-08-agent-composition.md#ac3b的下一批可验收切片)、[本片合同](2026-11-09-definition-admission.md#合同与职责)及maintainable-project-delivery、code-review、codebase-design技能审查；先读原要求/合同及实际diff，再读作者实施叙述。未预设通过。

分支为`refactor/architecture-foundations`；基线与初审HEAD均为`833d46fd42e2064f8417f30b430c44069ac03a61`，`git log <baseline>..HEAD`为空。本次明确审查未提交工作树，因此使用下列基线到工作树的diff，覆盖技能默认的HEAD三点diff；新增交付文档另读全文。

```bash
git diff 833d46fd42e2064f8417f30b430c44069ac03a61 -- \
  docs/AGENT_DEFINITIONS.md docs/PLAN.md docs/WORKFLOW_DEFINITIONS.md \
  docs/architecture/current.md docs/plans/2026-11-08-agent-composition.md \
  src/ergora/agent_definitions.py src/ergora/definition_bundles.py \
  src/ergora/workflow_definitions.py \
  tests/test_agent_definitions.py tests/test_workflow_definitions.py
```

固定输入为本地忽略的`.ergora/checks/ac3b1-admission/review-r1-scope.json`（SHA256 `5d94eaa10dc7f73e649b9e35f39216d7947398fd0c2755a7a3b14069f443c35e`）与`review-r1-tracked.diff`（SHA256 `048d272f42ca3c7b030ab169d1f1054129f6623777bd7ea59f986906c48bc470`）。11项范围如下；协调者逐项核对工作树字节与清单一致，重算tracked diff摘要也一致：

|文件|初审SHA256|
|---|---|
|`docs/AGENT_DEFINITIONS.md`|`f7612a379fa01f5164c1e449f2da028d7edc4d2647d165b6628a8291caf630f0`|
|`docs/PLAN.md`|`ec3ebd57e914078db28b1c9357a553384b8f4e0fa35390d18dd8f5cf6457375a`|
|`docs/WORKFLOW_DEFINITIONS.md`|`b88df1c798520c2fe89fb4430c016f235159e8c81af0e8a5b141c739eff548a6`|
|`docs/architecture/current.md`|`476f88a82d0ce168858874799b18c0523ede8abefba565e232f33888207cfc83`|
|`docs/delivery/2026-11-09-definition-admission.md`（新增，全文）|`e7a0ddca0511105f37e57d1f8dadf8fddb9897d13ad91ed491ce06df92dd4ced`|
|`docs/plans/2026-11-08-agent-composition.md`|`4be27f4d4b084bfae2004f8e3c8275e78ec868fc711fc366eb54e6b10c589b60`|
|`src/ergora/agent_definitions.py`|`d53c9650ceb888e09665e78fc46e403373a4a32b3b4f2870ca9b222d12bfcf54`|
|`src/ergora/definition_bundles.py`|`3306a065e785ba2d6cca1df89c3d02f4bb8c1a2b2a3f3b2c9fccefc578effcc5`|
|`src/ergora/workflow_definitions.py`|`47df05926a5e28748c7ca5426ac05ad0f2b3d6da7f41ee0f11dee88d61afd0c5`|
|`tests/test_agent_definitions.py`|`512350715710fa2a96bd76bfe6bbbefb877876b8965c5cf9a1f1031def1cc1d6`|
|`tests/test_workflow_definitions.py`|`dc4b1d5e0f0445b9d560f5a245294055e740f780b1f85f2e0817f1dd617ea62e`|

前片`2026-11-09-workflow-definitions.md`与其review报告的状态归档不属于本片实现范围；代码没有排除。另只读必要调用者，包括`cli`、`backups`、`agents`、版本化schema、相关原测试和基线公开手册。根目录没有CONTRIBUTING/CODING_STANDARDS；冻结upstream内部标准不当作wrapper修改规则。本报告及稍后的证据/状态归档不冒充已在上述11项中受审。

## Standards

**无finding，限定于上述实现及必要调用者；不替Spec轴作结论。**

依据AGENTS、当前架构、合同/身份文档、ADR0004/0005及公开手册，未发现所有权或依赖方向违规。按code-review的完整Fowler smell baseline逐项考虑，也未确认有可操作的判断性smell。

- `definition_bundles.py:88–90,128–135`的导入检查由Agent和Workflow两个不同生产所有者实际消费；源包和暂存副本均在发布前检查。
- `agent_definitions.py:13–31`将当前准入留在Agent所有者，并复用既有`agents.validate_binding`。私有静态inspector有清楚的历史完整性职责。
- `workflow_definitions.py:160–177,306–317`在同一有界遍历中选择是否执行当前Agent准入，历史备份复用静态规则。两个库工厂直达`.import_bundle`均保留准入，没有新增公开跳验开关。
- 新增检查有可达条件；新增测试覆盖实际策略变化、历史恢复和损坏拒绝，未发现仅镜像实现的断言。

独立定向16项通过。另以隔离临时探针在第二次准入时拒绝，确认Agent/Workflow各自首次及幂等导入共4种情形均不发布新内容、不改变既有索引，并清理暂存目录。未验证发行包、原生Windows或远端CI；未修改仓库文件。

## Spec

**初审未通过：两项P2。以下保留本轴原始发现，未与Standards合并或重排。**

### SP-1 / P2：历史角色过滤仍依赖当前catalog

原要求：“读取、列表及备份只依赖其版本化结构和完整内容身份”（[原计划第42行](../plans/2026-11-08-agent-composition.md#ac3b的下一批可验收切片)）。[cli.py](../../src/ergora/cli.py)初审第282行仍以当前`ROLE_CAPABILITIES`限制历史列表的`--role`。隔离探针移除`reviewer`后，`agent definition list --role reviewer`在解析阶段exit 2，无法查询已保存历史。库层`definitions(state, role="reviewer")`仍正常返回`architecture-reviewer`，证明拒绝来自CLI的当前目录耦合。

最小修正：取消历史列表过滤参数的当前角色choices，沿用库层字符串过滤；执行入口继续检查当前角色。用真实CLI入口验证移除已保存角色后的筛选。

### SP-2 / P2：Workflow历史读取未落实明示的递归完整性合同

[交付合同](2026-11-09-definition-admission.md#合同与职责)初审第9行明确：“get/list/export及完整备份/恢复只检查……递归引用”“篡改/缺失/引用漂移仍拒绝”。但[workflow_definitions.py](../../src/ergora/workflow_definitions.py)初审第106行给历史库配置本包inspector，公开入口第294、298、302行均未递归验证。

Spec轴及协调者分别以隔离State导入Agent→sub→outer，再令当前binding拒绝并删除Agent对象，结果均为：

```text
get outer: ACCEPTED missing nested Agent
list: ACCEPTED missing nested Agent
export outer: ACCEPTED missing nested Agent
verify_store: REJECTED FileNotFoundError
```

本轴判断这是本片明示合同未满足，虽基线已有相同行为。“只导出当前包”限定复制内容，并不妨碍导出前验证引用。按该合同履约的最小方向是历史入口复用无当前准入回调的有界遍历，同时保留单包输出范围；内部引用解析须避免重新进入自身遍历。

未发现额外扩范围行为。其余检查显示当前准入覆盖源包、暂存副本、幂等导入、两个库工厂直达导入及Workflow preview，备份遍历使用静态校验。独立重跑新增参数案例5 passed，另完成上述两组隔离探针；未独立重跑完整140项、发行包、原生Windows、CI或冻结资源身份。

## 协调者的范围核对与待处置点

SP-1由协调者独立复现：库层返回历史定义，公开CLI exit 2并给出`invalid choice: 'reviewer'`。这是原计划“列表不受当前catalog影响”的实际漏拆；初审新增测试只覆盖库层，未覆盖这一公开筛选入口。

SP-2的原始运行事实成立。协调者另核基线公开手册：[show展示本包材料](../WORKFLOW_DEFINITIONS.md#运行示例)，[export只导出当前包，完整备份递归核引用](../WORKFLOW_DEFINITIONS.md#修订分享与恢复)；基线读取也没有递归核验。这说明该发现不是本次静态/当前准入拆分引入的回归。原AC3b.1要求解除catalog耦合，未明确要求扩大原读取路径；新增交付合同把不同操作的核验范围写成了一句，确实形成更宽的书面承诺。

实现者须对SP-2作可核的处置：按明示合同补实现，或依据原计划及基线公开合同解释不扩展历史单包读取，并修清交付记录与手册中“本包完整性”和“完整备份递归核验”的各自范围。后者是合同表述纠正，不能宣称上述读取探针变成了递归拒绝。该处置及同片复核到位前，SP-2保留open；不以作者解释或Standards通过直接删除Spec原发现。

## 实际验证与限制

作者提供的Python3.11.15最终源码命令为：

```bash
PYTHONPATH=src .ergora/checks/ac3a-definitions/wheel-venv/bin/python -m pytest -q \
  tests/test_agent_definitions.py tests/test_workflow_definitions.py \
  tests/test_state_backups.py tests/test_schema_contracts.py
```

协调者读取`final-source-tests.log`，内容为140 passed、2 native Windows junction skipped、1条既有FastAPI/httpx弃用警告；这是作者运行日志，未冒充独立重跑完整四套。

协调者及Spec轴各自独立重跑以下两个参数化案例：

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 \
  .ergora/checks/ac3a-definitions/wheel-venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_agent_definitions.py::test_historical_assets_survive_current_admission_changes \
  tests/test_workflow_definitions.py::test_nested_history_is_readable_but_new_admission_is_rejected_after_policy_change
```

两次各5 passed，不将重复运行相加成独立案例数。Standards轴另执行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  .ergora/checks/ac3a-definitions/wheel-venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_agent_definitions.py tests/test_workflow_definitions.py \
  -k 'historical_assets or nested_history or source_change_during_copy or concurrent_imports or copy_failure_and_failed_reference_publication or failed_first_workflow_publication or local_graph_and_schema' \
  --basetemp=/tmp/ergora-ac3b1-standards-tests
```

结果16 passed、85 deselected。其第二次准入拒绝探针使用临时State和`unittest.mock.patch.object`：第一次`validate_binding`调用原函数，第二次抛出`ValueError("Staged admission rejected")`；Agent/Workflow各自首次与幂等工厂直达导入共4种情形均准确拒绝、调用数为2；首次无已发布库、已有索引字节不变、无导入暂存残留。探针经stdin执行，未另存脚本或日志，原输出4行分别确认first/existing publication protected。

协调者运行`git diff --check <baseline>`通过。所有临时探针只改隔离State及进程内mock；审查者只新增本报告，没有改生产、测试、依赖或CI，没有安装、调用模型、提交或推送。

本轮没有算法变化，不制造性能基准。非editable最终包、完整冻结283身份、本片精确提交/必要CI/即时远端终结均未由本报告初审验证；前片AC3d的CI不能替代本片证据。后续新增identity文件和状态记录须另行复核，不能从本次11项scope推导通过。

初审报告形成时作者告知，前片AC3d的Windows CI暴露测试helper默认CRLF与声明SHA不符，已将`tests/test_workflow_definitions.py`既有helper的一处文本写入改为显式UTF-8字节写入，另由前片原reviewer复核。该单行使当前工作树不再完全等同本报告的r1输入；本报告保留原始scope，不借该说明把未核修改算作通过。待前片普通修正提交、新父基线以及本片SP-1修正/SP-2处置固定后，使用新scope做同片复核。

初审计数：Standards 0项；Spec 2项，最严重为P2。下一步为SP-1修正、SP-2有证据处置及同片复核；随后再核DA3发行身份与DA4精确交付。

## r2同片复核：范围及身份

2026-11-08 18:06:12 UTC，原协调者及两个原审查轴完成同片复核，没有把本片原reviewer用于下一片。基线与HEAD现为`460702f9866080756883501eefc5132b8a345a38`，其唯一父为原`833d46fd42e2064f8417f30b430c44069ac03a61`；没有历史改写，基线到HEAD提交列表仍为空。协调者实际读取两基线间diff，确认测试源码仅有前述helper从`write_text`变为`write_bytes(text.encode("utf-8"))`的一行；前片交付状态归其原报告，不借此关闭本片CI。

r2固定输入为`.ergora/checks/ac3b1-admission/review-r2-scope.json`（SHA256 `456e06d81397f7a931054964931a77669071b27e28295c0f2fcdc9a6ff7209c1`）及`review-r2-tracked.diff`（SHA256 `30cef7072c4e4ed8a6e639d69430ab61bf0b1941f7924f4c07060c168ef3a1b4`）。协调者和两轴独立重算14项文件与tracked diff均匹配。

范围为原11项，加`src/ergora/cli.py`、本报告、`docs/delivery/evidence/2026-11-09-ac3b1-local-identity.json`共14项。`docs/WORKFLOW_DEFINITIONS.md`、`docs/architecture/current.md`、`docs/plans/2026-11-08-agent-composition.md`及三个准入/发布生产文件与r1字节相同；其余八项r2身份如下。报告自己的摘要指此次追加前的受审版本，追加结论属于同片审查归档。

|文件|r2受审SHA256|
|---|---|
|`docs/AGENT_DEFINITIONS.md`|`a6cba1017314a5740d6c26ef9e75787928813a6e34085d8f6088d3ddfc1970a9`|
|`docs/PLAN.md`|`062c4a739f0fdd4e71f115498474e00182ac431b6af26321320ce1c04a029c0b`|
|`docs/delivery/2026-11-09-definition-admission-review.md`|`b769d478e5413c15a441ce5002f7ef2ea19868735d1847c6aeb489eff2f90380`|
|`docs/delivery/2026-11-09-definition-admission.md`|`7e6ffe9034c17d8cfb9b114cc9675068a70b23f0027d7710854a9af700656012`|
|`docs/delivery/evidence/2026-11-09-ac3b1-local-identity.json`|`8b7ffdcd21a029bbcc2072feddb3c92eb253109a8edf17636c87dbedfe7fc635`|
|`src/ergora/cli.py`|`3d21f1f09296a4aa68067f0080f54235ac4fbceba88897381ae4b4a6b85b99fb`|
|`tests/test_agent_definitions.py`|`e706d7dd3f40fcab04af3983f0505b8c4444ab8ecaa36342927e9cbec5016d97`|
|`tests/test_workflow_definitions.py`|`2d32c10813225ae30881b94ea4a954d5e697e1d541c1379701d6d89c8ef4620a`|

前片两个Workflow交付报告仍只作状态记账排除；没有排除本片代码。生产冻结后如再改源码/测试，须重核对应身份和受影响证据；后续计划/状态归档单独核范围。

## r2 Standards

**无新增finding；保留r1结论及其原验证身份，不替Spec轴裁决。**

`cli.py:282`只解除历史角色筛选的当前catalog限制，`:294`仍保留执行入口的当前角色choices；CLI继续调用原库过滤，没有新增代理、重复规则或公开跳验参数。新增断言放在既有三种策略变化案例，检验真实`cli.main`输出，没有新增镜像测试。交付合同现明确本包完整性与递归备份的分工，符合实际所有者；原发现与处置理由保留。三个准入/发布生产文件字节未变，r1的暂存拒绝探针无需在本轮无变化地重复。

独立源码执行原策略变化参数案例：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  .ergora/checks/ac3a-definitions/wheel-venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_agent_definitions.py::test_historical_assets_survive_current_admission_changes \
  --basetemp=/tmp/ergora-ac3b1-standards-r2-tests
```

结果3 passed。另stdin隔离解析探针移除`implementer`角色后确认历史list仍接受该标签、实际run仍exit 2拒绝。未重复完整四套、暂存探针、包测试、原生Windows或CI；未改文件或安装。

## r2 Spec及逐项处置

**当前Spec通过：两项原发现均有可核处置，无新增finding。**

- **SP-1：代码修正关闭。** 独立真实`cli.main`探针移除`reviewer`后，历史过滤列表exit 0并返回`architecture-reviewer`；同角色`agent run`仍解析exit 2。新源码及最终包中的原3策略变化案例都覆盖历史CLI输出，实际运行仍核当前角色。
- **SP-2：接受文档纠正处置关闭，没有新增历史读取的递归校验。** 初审的合同/实现不符事实及原报告保留。原AC3b.1目标是解除catalog耦合、保留既有完整性检查；结合基线实际行为、原公开手册的本包展示/导出与完整备份递归验证，未见原始要求明确升级所有历史读取为递归验证。现合同第9行清楚区分两条路径，处置成立。单包输出范围本身不能推出免验递归引用，因此没有只凭“export单包”关闭发现。

Spec轴独立以与初审同样的两条参数化node ID执行源码定向检查，结果5 passed。另stdin临时探针制造自洽对象/索引下的递归引用漂移：get/list/export仍接受完整本包，`verify_store`与backup均静态拒绝、未发布无效备份；随后篡改根包资源，get/list/export全部拒绝。上述历史检查调用当前准入函数0次，分别验证纠正后的检查范围及其独立于当前catalog的性质。未修改文件，未重复完整四套、包测试、冻结身份或原生Windows/CI。

## r2协调者的发行与证据复核

协调者读取r2-source-tests.log与r2-wheel-tests.log，分别记录Python3.11.15源码及Python3.12.3非editable包的同四套140 passed、2 skipped、1条原警告。这些完整suite为作者执行；本轮没有把读日志称作独立重跑。初版日志和包在r1前缀及dist/r1保留，没有将两轮计数相加。

独立核对[公开最终身份](evidence/2026-11-09-ac3b1-local-identity.json)六份源码/测试SHA均与工作树及r2 scope一致。用标准库读取最终wheel ZIP，逐项比较源码与现有安装，确认三个文件集合及359份原字节全部一致；最终wheel SHA256为`f08d482d52b4dd11f691cf1d7d08d4dd502d45be7e3cd842f4ad502f582219bb`，匹配公开记录。使用现有包环境的`python -I`确认从`site-packages/ergora`导入，`reference.verify()`返回PASS、283文件、`runtime_started: False`。源码和包逐字一致，冻结283身份也由此覆盖。

随后在临时工作目录，以现有Python3.12.3的`-I -B`隔离模式先断言实际导入路径为安装包，再通过`pytest.main`执行两条新增参数化node ID：

```text
test_agent_definitions.py::test_historical_assets_survive_current_admission_changes
test_workflow_definitions.py::test_nested_history_is_readable_but_new_admission_is_rejected_after_policy_change
```

结果5 passed。该次专门核最终安装包的CLI历史筛选、当前准入、完整备份恢复及递归损坏拒绝；没有安装或构建新环境，没有重跑无关全套。协调者`git diff --check 460702f9866080756883501eefc5132b8a345a38`通过。

本地可维护性及需求复核现可通过；Standards当前0项，Spec原2项均已关闭、当前0项未解决。没有算法或性能新声明，未额外跑模型/基准。原生Windows本地运行、本片精确普通提交、必要双OS CI及即时远端终结仍待后续证据；前片460702f的CI不替代本片DA4验收。
