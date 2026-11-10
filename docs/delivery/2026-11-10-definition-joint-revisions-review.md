# AC5 C3d 独立终审

**本地终审通过：Standards 通过，Spec 通过，开放 finding 0。** fresh-context 主审 `joint_revisions_review` 及分别独立的两轴审查完成；该结论覆盖既有能力的 CLI／页面验收、文档和实际自身审查证据。本片已普通提交推送，精确对象、一次独立明确 HTTPS 及自己的必要 CI 均通过，C3d 精确交付门禁终结。

审查基线和当时 HEAD 均为 `4636d77377bf63f15c357cf14660024e3ae1f939`，分支 `refactor/architecture-foundations`。固定候选为私有 `review-final/{identity.json,tracked.diff,files/}` 的 **20 文件：14 Markdown、6 公开 JSON（81,568 字节）**；identity SHA256 为 `9e91e3e255280793881049c642eb6dfeba2297f9edb469de1f6a2ece7035f98a`。本地终审时 HEAD 尚无新提交，三点 diff／提交日志为空；实际按非空固定 WIP diff 和完整 untracked 内容审查，没有将空提交范围当作无变更。

已核根 AGENTS、README、PLAN、[本片计划](../plans/2026-11-10-definition-joint-revisions.md)、[C3 合同](../plans/2026-11-10-definition-revisions.md)、ADR0005、原 schema／所有者／消费者及邻接测试源码，采用 `maintainable-project-delivery`、`codebase-design` 和 `code-review`。在初始 17 文件基础上完整补核最终八项新增或变化，没有合并或重新排序两轴 finding。本文为审查结果续记；固定快照中同名文件仍是下方保留的准备报告，当前报告另在私有 gate 中登记身份，不回写原快照。

## 精确提交、HTTPS 与 CI 终核

普通提交 `45c2de47e9119d1f07616b3307331321d38155a4` 的单一父提交为上述基线，树为 `c0a5b44c8e16305f7193625a2c02efb603300e56`；原 commit／push 回执成功。主审直接核对全部 20 个 Git blob 与 `commit-closure/ready` 的 bytes／SHA／mode，提交内报告保持本地终审 SHA `c000c7e12d0a8697fe542cc1852ea1126f7c3a165c6101a202cd045262ffb928`。相对本地终审仅五份计划／交付状态文档续记通过与待交付，六公开 JSON、手册及产品行为未变；435 包对象与复用 wheel 相同、283 冻结文件及整个源子树的 mode 保持。私有 `independent/exact-object-audit.json` 的 784 项全部通过。

2026-11-10 **11:33:25.982984–11:33:27.377041 UTC**，按本片明确授权只执行一次隔离 HTTPS ref 读取。关闭系统／全局／仓库配置、凭据助手和交互提示，只允许 HTTPS、校验 TLS、禁用重定向；原 trace 确认 `remote-https`，远端完整 SHA 与上述提交相同。该独立读取不以 SSH push 或本地 remote-tracking ref 代替，原件在 `independent/https-remote-01/`。

自己的 [CI42807885966](https://github.com/626619403/Ergora/actions/runs/42807885966) 前三份官方样本均为 **In progress**，分别有 4／5／6 个必要步骤 success，当时均不计 CI 门禁通过。原 actions／run／完整两组 job 和原始响应保留，`independent/audit-ci-snapshot-01.json`、`audit-ci-snapshot-02.json`、`audit-ci-snapshot-03.json` 分别记录各自非终态；没有用后来的成功改写原样本。

第四份官方样本的实际 run 采样时间为 **2026-11-10 11:43:33.076431 UTC**，Status **Success**。主审离线独立解析原 HTML／embedded JSON：完整 SHA、分支和 portability workflow 对应本片精确提交；Linux 三个、Windows 四个必要步骤全部 `success`，两组 job 均 `completed/success`，每步的完成标记、时间和 log 路径均绑定本提交／job。五份原始响应 bytes／SHA 与采样记录全部相符，`independent/audit-ci-snapshot-04.json` 的样本及自己的 CI 门禁通过。沿用已核的 20 blob／ready、435／283 对象和上述一次独立 HTTPS，`independent/exact-delivery-gate.json` 现为 **true**，无待验项；本轮未重跑网络、HTTPS、产品、模型或测试。

作者在推送后开始的 C4a 文档工作树明确排除在本片候选外；本次精确核验只读固定 Git 提交与 ready，不用后来工作树替代。本文后续补核属于同片审查记录，不回写提交内报告或原 ready 快照。

## Standards

**通过，实证 finding 0。** 手册的父子共同修订步骤、旧快照保持、实例／资产区别与实际 `DefinitionLibrary.revise`、Workflow 编译器、输入冻结和后端准入一致。权限仍属于 Workflow／Agent 节点；页面继续消费同一用例，没有生产代码、永久测试、依赖或 CI 改动，也没有为本片追加抽象或容量配额。Fowler 线索逐项用于判断，未发现有证据的 smell。

K3 的原始失败和续接均保留：三段实际为 34.440／32.045／4.809 秒，共 71.29 秒；17 个原 HTTP 响应中有四次权限拒绝，三个发布版本和最终 preview 与原完整对象一致，15 个只读原包保持。第一次 HTTP 管理器因 stdin EOF 退出并 reap 服务、第二次明确 stop，以及两个 HTTP／七个浏览器采样身份清理，均有原件。六份公开 JSON 按当前 publisher 的声明转换在内存逐字节重建，原件 bytes／SHA、路径替换和省略范围准确。

两轴中的 Standards 原审 388 项、最终补核 269 项全部通过，私有报告为 `independent/standards-review-final.md`，审计为 `independent/standards/audit-r1.json` 与 `audit-final.json`。用量记录没有把 cached input 再加到 input，也没有将后端自报值称为账单。

## Spec

**通过，实证 finding 0。** （a）本片验收范围未见缺失需求：K1／K2 原非 editable 包实际 118 次 CLI／84.68 秒；三领域从子到父发布 11 份新 Workflow 修订、完整导出／再导入一致，八次子越父、三次旧 grant、两模式 check／run 的十二次不支持 network，共 23 次明确拒绝。每次拒绝的双索引完整前后字节不变，未登记 agent run；35 个旧对象及六棵旧 manifest／input 全树、目录和完整 mode 保持。

（b）未发现额外行为或范围扩张。原 34 次 CLI 后的私有驱动 `KeyError: directories`、页面两次超时、已发布状态和实际续接都未被抹去。network 保留域名只进入静态声明；实际只读调用在后端选择／run 登记前拒绝。新 grant 不替代正式 owner 批准，训练仍为提案；六阶段以及批准／候选／unknown 所有者保持。

（c）未发现表面实现但违反合同的行为。逐层完整结构祖先和材料来源正确，数据前驱没有成为权限祖先。只读重复根独立核得 **22 实例／46,332 材料字节**；同精确 1.0.21 子模板的两条 required 路径保持独立，advisory 使用另一个真实 1.0.45 子修订，五分支显式 all-join 完整。同资产去重不合并实例、会话或来源；实例和材料受各层实际可配置预算约束。六次逐叶 Codex／Claude task-mcp `check-input` 是配置／模式准入，不证明安装、认证或推理成功。

Spec 原审 8,393 项、最终补核 208 项全部通过，私有报告为 `independent/spec-review-final.md`，审计为 `independent/spec/audit-r1.json` 与 `audit-final.json`。[操作手册](../WORKFLOW_DEFINITIONS.md)与[交付记录](2026-11-10-definition-joint-revisions.md)对这些边界表述一致。

## 实际自身模板与主审原件核验

运行 `19917c71dd014cc0ae4713e844ef6ee2` 实际 406.36 秒／succeeded／approve，原结果 SHA256 `704873a0bbc20cd87bef99b756874b6b8720c4a30e9297f0d605f0f48229eb4f`。主审直接核对冻结输入／manifest、实际 run input、stdin、协议 prompt、scope、native 原始消息、SQLite 单 run 和原结果，没有把模型 approve 当作独立审查结论。

全部五份 scope 共 **862,776 decoded 字节**，由 41 页成功 UTF-8 回复完整覆盖；候选附件 861,261 字节／37 连续页，SHA256 `3e20674bf62cd11693276a37650e23af5fa2e76bb119a99a70856f666e993e33`。offset 528000 的两个 base64 窗口在原位置缩小重试，原回执保留。完整祖先 instructions／Skill 入口、八份保护源／驱动、40 份原 CLI 回执、三段原页面请求／响应全文均与实际冻结附件绑定。两个原定义库已移出活动控制目录并完整保留，冻结输入自包含。

原 native 自报 input 3,891,083，其中 cached input 3,653,248；output 9,603，另报 reasoning output 3,727。四个采样 owned 模型进程 PID／starttime 身份已消失，native 回执 MCP PID 当前不存在；该回执未给 starttime，不扩大为未采样进程保证。只使用已授权 Codex 回退，结论限于上下文独立，不能证明模型理解或不同模型错误独立性。

主审私有 `candidate-r1-audit.json` 2,323 项、`self-review-audit-r1.json` 592 项及 `final-candidate-audit.json` 5,259 项全部通过。最终核对 435 个 Git／source／wheel／install 包文件、两份 RECORD、283 个冻结文件和执行位保持；固定 20 文件无漂移，14 文档的 256 个本地链接／锚点有效，tracked diff whitespace 通过。收口脚本首轮误将旧 publisher 身份当不可变；保留原驱动和诊断后，只承接最终 Standards 已核的 287 字节 cleanup 投影扩展，其余审计输入保持原身份。该扩展是在已有 `--final` 分支加入自身 cleanup／usage 及原件身份，没有修改产品或原始证据。

本地终审的主审和两轴只作 stdlib 离线原件核查，未重跑产品、模型、服务、浏览器、测试、安装或网络。本地原结论登记在 `independent/final-candidate-gate.json`；之后的精确提交、一次独立 HTTPS 和自己的 CI 终核见上文，本片精确交付已终结。C4 画布、C5 正式交接、C6 容量／分页成本及实际训练仍待相应后续。

## 历史：准备阶段记录

以下为完整保留的准备结论，其“未验收”“前片 CI 在途”等状态仅描述准备当时；当前本地结论见上文，前片门禁后来已终结。

### AC5 C3d 准备独立审查

本轮结论限于**原接口与验收设计相容，未发现有证据的实质错误或漏项**；不是 C3d 实现或验收通过。审查者为 fresh-context `joint_revisions_review`，准备基线与当前 HEAD 均为 `4636d77377bf63f15c357cf14660024e3ae1f939`，分支 `refactor/architecture-foundations`。完整候选到达后，仍需按 `code-review` 的 Spec / Standards 两轴终核。

已读根 AGENTS、PLAN、本片[计划](../plans/2026-11-10-definition-joint-revisions.md)与[准备记录](2026-11-10-definition-joint-revisions.md)、[C3父合同](../plans/2026-11-10-definition-revisions.md)、D4/D5交付和审查记录，及下面列出的原所有者、CLI/HTTP/页面和相邻测试源码。采用 `maintainable-project-delivery` 及 `codebase-design`。前片审查报告的状态续记属于前片，没有据其扩大本片行为范围。

### 原接口核对

- 联合声明路径成立。[`workflow_definitions.py:96`](../../src/ergora/workflow_definitions.py#L96) 的 `_within` 检查逐层包含关系；`_workflow` 对 Workflow 上限与 Agent 节点请求分别检查。库的当前 import inspector 从该 Workflow 自身声明构造 grant 并编译完整依赖，因此可按子到父逐个发布新修订，根最后发布；新根仍需显式外部 grant。网络 origin 在静态层只作规范化及集合包含检查，不执行网络请求。
- 权限和职责所属准确。Agent v1 schema 没有 `permissions`，它属于 Workflow 和其中的 Agent 节点；v2 `review_requirement` 仅允许 reviewer Agent 节点，Workflow 引用和 join 均不接受该字段。同一精确子模板的重复引用继承相同职责；改变其中一份职责要引用另一个真实子修订。这与计划一致。
- 重复实例和资产去重没有混用。[`_workflow`](../../src/ergora/workflow_definitions.py#L266) 用结构路径独立装配实例；[`_materials`](../../src/ergora/workflow_definitions.py#L158) 只合并当前祖先链，保留 `sources.instance`。冻结包的 [`_prepare_bundle`](../../src/ergora/workflow_definitions.py#L504) 按完整 kind/id/version/digest 只保存一次同一定义资产。两份叶子的来源路径与 prompt 身份可不同，不能以共享资产推断共享实例或可变会话。现有相邻测试也分别表达这两层合同；本轮未运行它们。
- 预算确为可配置值。[`_count`](../../src/ergora/workflow_definitions.py#L252) 及材料累计使用 supplied grant 和各层实际 `limits`，不把默认 128/262144 当产品不变量。重复子树各自计入实例与完整 prompt 字节，concurrency 作为各层上限传递。本片保持原预算是此旅程选择，不限制后续合法配置；证据脚本应按实际候选和配置核对，不追加固定容量配额。
- 静态成功与实际调用拒绝区分正确。[`_admit_input`](../../src/ergora/agent_runs.py#L73) 在后端选择和 `_run_prepared` 登记 run 之前拒绝任何 write/shell/network 请求，覆盖公开 text-only 与 task-mcp。计划可准备完整输入并真实检查两种入口的拒绝和 run 数量保持；它不能据静态预览通过宣称 network 或外部 MCP 已可执行。
- 后端入口没有模板耦合。`check-input --backend` 经 `_admission` 调用现有 `AgentBackend`；保留 `requested_binding`、实际 `binding` 和理由。该检查不调用 `available`、不验证 CLI 安装/认证/推理就绪。Codex/Claude Code 的模式合同可以独立核对，无需为已知 Claude 上游失败重复调用；正式多样性和交接仍属原门禁及 C5。
- 页面复用位置正确：实际文件是 [`src/ergora/data/console/definitions.js`](../../src/ergora/data/console/definitions.js#L304)，HTTP 位于 `web.py`。表单可编辑 Workflow 根权限、Agent 节点权限和精确引用，完整 JSON 可表达其余字段；检查和发布仍到同一 `revise`。静态预览显示原上限说明。K3 的被拒绝候选保留、逐依赖发布和旧 grant 拒绝均是实际页面旅程待证，源码阅读不替代浏览器验收。

### 已检查与限制

离线读取 D4 三域所选完整链的 instructions/context/Skill 入口及全部 Skill 附件，治理和大型修改各四层、训练三层；资源来自原冻结 `new-input/assets`，保留原来源与字节身份。这里只确认本片计划所复用的旧链、字段和资源可追溯，不把 D4 的模型读取结论移交给 C3d 的新输入。

本轮未修改产品、schema、测试或 CI；未导入新 fixture、运行产品、启动服务/浏览器、安装依赖、调用模型或发起网络操作。只写本报告与私有 `ac5-definition-joint-revisions/independent/preparation-audit.py/.json`，后者保存所读源/计划/原材料的身份与工作树观察。实际候选、输出与自审材料尚未形成，K1–K4 均未验收。

准备时前片自己的 CI42799311145 仍为 In progress；现存 `exact-delivery-gate.json` 的完整门禁为 false。此状态属于已读离线记录，未经本审查者网络查询。K0 必须等前片自己的 CI 终态和精确交付核验完成；本轮没有绕过该依赖。后续状态续记和完整候选需要另核，当前无开放准备 finding。
