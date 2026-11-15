# c1d M1a：rounds 纯内容提取独立审查

日期：2026-11-16。Reviewer：`round_content_extraction_review`，本片全新独立上下文，未参与实现。使用 `maintainable-project-delivery` 的 independent-review brief，以及 `ergora-codebase-quality` 的 module-design、test-seams、repository-style。先读[原始要求](../plans/2026-11-16-training-round-content-extraction.md)、[已审 wire 的纯提取边界](../plans/2026-11-16-training-cycle-measurement-wire.md#原-contextnative-最后-gate-与最小纯提取)、[原设计审查及同片复审](2026-11-16-training-cycle-measurement-wire-review.md)和真实基线／diff，再读作者交付。

**源码范围：需求轴 approve／开放0；维护性轴 approve／开放0。** 在下述准确源码范围内无 findings，无需源码修正。该结论不包含安装、自身模板、固定提交、发布或 CI 验收，不开放 ordinal1。

## 准确对象与权限

项目及文档 owner 为 Ergora；只读产品树为 `.ergora/worktrees/training-round-content`，分支 `refactor/training-round-content`，HEAD／实施基线均为 `fa2fd17620192ac1341a72f1050dc37faaee623f`。独立核对 Git 状态恰有下列三个未提交路径，无新增文件；完整实际 diff 与私有 `source-r1/source.diff` 逐字节相同，后者 SHA256 为 `c86e13f56cfb4c38a8067dc1c35115c17a52d912a434399d3193948fb751400b`。

|已审文件|SHA256|
|---|---|
|`src/ergora/training_rounds.py`|`ad9fba3d3f675ec0a91dc07a4224852482e0b75730218b5feaecb3f342abe310`|
|`src/ergora/training_execution_protocol.py`|`bd5f1b2878c533aeadd6e69d2c5b3a830e52b135f808e12d283f9251c8068a09`|
|`tests/test_training_evidence.py`|`5f49ddb029c8e4b8f402caceac22fadaaf5e543e6783fe778f4401046f3a335c`|

基线 `training_rounds.py` SHA256 为 `d4ca342b902f9d8c869171bbefa78b7fa6c0f0b129f57ea162b505e1d5124e7a`；独立读取固定 Git blob，并确认私有差分使用的 baseline 原件逐字节相同。已读根、产品树根、src、tests 的 AGENTS、主 PLAN、[组件协议](../architecture/component-change-protocols.md)中的执行／证据、配置／持久格式、脚本／检查职责，以及相关 CLI、protocol 隔离依赖和原 round fixtures。

本 reviewer 仅做文本／Git／哈希／AST／JSON 原件检查，只写本报告；未运行测试套件、产品程序、服务、安装、网络、模型或训练，没有修改产品／测试、提交或推送。

## 需求与维护性判断

`training_rounds.py:17–19` 仍先执行原 `contracts.validate`，再调用 `execution.validate_round_content`。新纯函数在 `training_execution_protocol.py:69–121` 明确以 schema 已验证报告为输入；没有复制 schema、来源认证或 archive 接受算法。reviewer 独立作内存 AST 对比，确认所移四个 helper、coverage 及 schema 后完整 `_check` 算法仅作符号重命名／schema 与 docstring 分离，校验顺序、原异常类别／信息和全部原分支保持。

`training_rounds.read` 仍持有目录／普通文件约束、原始字节读取、10,000,000B 上界、完整 raw SHA 及 schema；`create` 仍持有 State／training 原观察、project revision 复核、旧 prefix 和 previous 原文件绑定、不可覆盖发布。CLI 的 create/read 仍调用这两个原入口。pretty 编码仍是 `ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False` 的 UTF-8 JSON 加一个 LF，轮 SHA 继续散列该 pretty 字节；原完整文件 SHA 没有改成重新编码后的身份。coverage 的低覆盖／不授执行、授权与晋升含义保持。

新符号集中在现有已 pin 的 protocol，没有新增模块、包装 reader、插件接口或第二算法。当前直接生产调用文件只有 `training_rounds.py`：create 使用编码／SHA／comparison／anchor／coverage，`_check` 使用纯内容校验；不能将同一文件内调用或测试算成多个生产 caller。将这组内聚算法移入现有 protocol 的理由是已批准的 native 依赖隔离边界；未来前驱 gate 尚未实现，本审不把设计消费者记作现有接线。删掉该提取会令 native 再依赖带 schema／State 的 rounds 或复制算法，因此这个所有权调整有具体作用。

`ARTIFACT_LIMIT` 集中原数值，`training_rounds.MAX_INDEX_BYTES` 保持同值入口；原 `cycle.json` 的显式 10MB 读取仅改成同值常量。protocol 已在原 `GATE_SOURCES`，本次没有改 source inventory、schema1/2、schema3、WorkflowV2、gate、ordinal guard、批准或 archive 语义。顶层导入链仍只含 stdlib 和既有 stdlib-only 本地模块；新内容函数本身无 IO。没有新增校验分支、异常处理或无实际用途的防御层。

唯一新增回归沿原 experiments fixture 创建实际报告，并用真实 `-I -S -B` 子解释器复核 Unicode pretty bytes／raw SHA，再对 evidence revision 作变更并重算轮 SHA，要求内容绑定仍拒绝；它能发现“只验自洽哈希便接受错误原观察”的静默风险。所有原 fixture 测试保留。没有必要为每个搬移分支增加永久重复测试，也不要求纯函数对任意未经 schema 验证的输入承担结构检查。仓库 pyproject 未配置额外 formatter／linter／type-checker 门禁，本审未套用其他仓库的风格要求。

## 检查原件与结论范围

原件位于项目忽略目录 `.ergora/checks/round-content-m1a/source-r1/`。reviewer 读取 `identity.json`、`run.py`、`prepare.py`、baseline、完整 diff、原始日志／JUnit、差分 plugin、全部81条事件和六份完整报告，以及隔离／静态脚本及结果；独立核对 `artifact-sha256.json` 所列23个原件全部匹配，源码身份也与实测 identity 相同。

|实际证据|核对结果与限度|
|---|---|
|源码原完整 evidence module|原开发 Python 3.11.15、工作树显式 PYTHONPATH、禁止 bytecode；JUnit 为14 tests、0 failure/error/skip，33.008秒；原 stdout 为 **14 passed／33.02秒**，runner 34.365821秒。reviewer 未重跑。|
|固定 Git 基线差分|81次比较来自4个 round 测试接缝：8 create（6成功／2拒绝）、11 read、62 check（6原报告／56变体）。plugin 对实际新旧返回／异常类别与信息作比较；六次成功 create 比完整文件字节、结果／coverage、raw SHA与每轮 SHA。不是81个独立业务实验。|
|差分篡改|事件实际包含 coverage、parent、round hash、revision、binding、files、comparison、anchor、approval 和两次 prefix。approval 变体 `{}` 被原 schema 拒绝；本审不将它误称为全部语义 approval 分支的独立覆盖。原接受 prefix／baseline 漂移、负结果、unknown／lost-ack 仍由保留的真实 fixture 保护。|
|完整报告原件|六份 raw SHA与事件、manifest匹配；reviewer 直接读取六份报告并用规定 JSON 参数重新编码，均逐字节等于保存原件。原两轮 prefix 和低覆盖字段可见。|
|真实隔离子解释器|`isolated-result.json` 保存准确 `-I -S -B` argv、当前 source 包目录和 Unicode 报告 raw SHA；exit0、stdout/stderr空、0.095970秒。脚本真实调用纯算法、比较完整 pretty bytes／SHA并拒绝重算 SHA 后的 revision 篡改，核未加载 training／State／jsonschema／YAML／Temporal／dev_platform；这证明 source 依赖隔离，不代表新后继 gate 或安装验收。|
|静态保持|作者原件记录完整搬移 AST 等价及 `git diff --check` exit0；reviewer 另独立核全部六项搬移 AST 等价，直接审完整 diff，未执行作者脚本或产品。|

## 剩余验收

本次源码 review 已闭合，阻断 findings 为0。新非 editable wheel、隔离 core／SDK 的实际 site-packages／依赖／283参考身份及适用安装检查、自身原结构模板的真实后端输入／回复，仍由父任务按[实施计划](../plans/2026-11-16-training-round-content-extraction.md)接续并提供原件；源码通过不能替代这些证据。

最终固定提交与这三个已审文件／完整 diff 的身份、普通导入／推送的准确远端和该候选自己的适用 CI 仍待后续检查。同一源码片可由本 reviewer 做安装／固定身份补充复核；若产品字节或行为再变，需明确新增差异及受影响证据。本结论不认证 M1b、M1c、collect／reconcile、measurement acceptance、native 最后 gate、V2 或真实两轮训练。PLAN 与交付的实施／源码 review 状态由父任务统一更新，不据此提前记整个 M1a 完成。

## 同片最终补充：安装、自身模板与固定提交

日期：2026-11-16。原独立 reviewer 对同一 M1a slice 补核新增原件；以上初审对象、结果及当时未完成项作为历史记录保留。没有新的产品修改，也没有递归审查报告。

**本次固定源码／安装／自身模板证据的需求轴 approve／开放0；维护性轴 approve／开放0。** 初审列出的新 wheel、安装、原模板和本地固定／导入身份现已具备准确证据；没有新增 findings。准确远端、普通推送及该候选自己的 CI 不在本次认证范围，仍由父任务另验。

### 固定与导入身份

产品固定提交为 `5cb4cb903486d37356a5511c75e094a195558912`；主树实际 HEAD 为普通 merge `bd479050ddd2d9c6b6964f89fe44cfc895273d6b`，其两个父提交准确为原基线 `fa2fd17620192ac1341a72f1050dc37faaee623f` 与上述固定提交。reviewer 从两个提交各自读取三个 Git blob，SHA256 均与初审表逐项相同，并与主树／隔离树现存文件相同。

独立读取 `git diff <原基线> <固定提交>` 及 `git diff <原基线> <merge>` 的**完整**结果，两者均逐字节等于初审 `source-r1/source.diff`，SHA256 同为 `c86e13f56cfb4c38a8067dc1c35115c17a52d912a434399d3193948fb751400b`。导入仍恰为原三个文件、120行增加／83行删除；未夹带额外产品差异。主树未提交内容是公开文档记账及后继出生设计，没有产品／测试差异；后继文档不纳入本 M1a 行为批准。

### 新非 editable 包与安装检查

私有原件为 `.ergora/checks/round-content-m1a/package-r1/`。reviewer 读取构建／安装脚本、每步实际 argv 与 exit、包清单、引用核验／依赖原 stdout、冻结清单、安装测试 request／result／raw stdout／stderr／JUnit、实际 core 隔离结果与 post-validation 身份；没有运行脚本、安装或重跑套件。

|证据|独立核对结果|
|---|---|
|新 wheel|文件实际 SHA256 为 `a4a26ff3e7782bffff7b1c0cdaf436a0fbf9ab6c4b1b29491fdd7b2fae1c4e7f`；原 `build --wheel` 和两次新环境安装均 exit0。两环境 `direct_url.json` 均指向此 wheel 的 archive，没有 editable 安装。|
|source／wheel／site-packages|core 与 SDK 清单各663个包文件，无新增／删除，相对基线仅两个已审产品文件变化。reviewer 直接读取 wheel ZIP、当前源码及两套实际 site-packages，核全部文件字节、清单 SHA／长度、完整安装集合及 executable bits 一致，差异0。四个 owner 的记录导入路径均在各自 site-packages。|
|原283参考／依赖|原核验结果两套均 PASS／283。reviewer 再沿两套安装内原 manifest 直接散列全部283个文件，差异0；`uv pip check` 原 stdout 与 exit0表明两套依赖兼容。core 当前磁盘无 temporalio 包／dist-info；SDK 为 `temporalio-1.34.0`，与安装记录一致。|
|安装原 evidence module|request 为新 SDK Python 3.12.11 的 `-I -B -m pytest`，无 PYTHONPATH，在冻结 tests/examples 副本运行；原 stdout **14 passed／30.55秒**，JUnit 为14 tests、0 failure/error/skip、30.547秒，driver 32.018306秒、exit0，stderr空。不是初审 source 差分重跑，也没有扩大为服务／训练验收。|
|实际 installed core 隔离|`core-isolated-r1.json` 的真实 `-I -S -B` 子解释器只加入 core 的 site-packages 路径，stdout明确打印该安装的 protocol 文件；校验同份 Unicode 报告、pretty bytes／SHA并拒绝重算 SHA 后的 revision 篡改，exit0、stderr空、0.081715秒。未加载 State／training／jsonschema／YAML／Temporal／dev_platform。|
|冻结输入与事后身份|`post-validation-identity.json` 明确在安装14项及自身模板之后记录差异0；reviewer 又直接核848项 source／tests／examples／配置／CI冻结字节与执行位、663项完整产品字节与执行位，以及179份实际 tests/examples副本字节，差异均0。冻结记录仍保留实测时原 HEAD＋未提交 diff 身份，未把后来的固定提交伪作先前运行 argv。|

### 自身原结构模板的实际后端结果

私有原件为 `.ergora/checks/round-content-m1a/self-review-r1-codex/`。reviewer 读取 scope、原 manifest／composition、request、command、admission、实际 run、stdin、原 JSON 回复及 review 正文。原 `ergora-structure-review` 1.0.0 的 `root/review` 请求后端为 claude-code，实际显式使用已授权 Codex fallback；原件没有宣称本次 Claude 运行成功或异后端成功。命令通过本次新 SDK 安装运行，真实 run `52ceb81619204601833a0792b6da5c5c` 为 succeeded／returncode0，driver 36.762488秒，实际 decision=approve，无 findings。

reviewer 直接核11份完整供审文件合计140,045B的 SHA／长度，并确认每份完整内容均在 task 和实际 stdin 中；实际 task／stdin 恰有两个显式 `BASELINE COMPLETE FILE` 段，分别是固定 Git baseline 的 rounds 与 protocol 完整原文件；原测试文件正文作为完整当前测试文件的未变前缀逐字节包含，并非第三个独立 baseline 段。完整已审 diff 也逐字节包含。三份祖先资源是原 workflow instructions、原 reviewer instructions 和原 reviewer SKILL.md；与本次安装内原 preset 文件逐字节相同，且完整包含于实际 stdin。实际 stdin 为241,065B，SHA256 `ddaf3c40272a5135ef60950ea271f618154048dc4c4c7953fd16595c18a19cca`；真实 result 与保存的 original-result 相同，SHA256 `84c40fc16b49990cfc54c4d7b5882880b364b579107ede911b196ce7c14fc8f4`，均与 admission／run 绑定一致。

该后端明确说明仅审完整 supplied text，没有文件系统／工具访问或独立重跑；回复也将当时未提供的安装与发布留为 pending。它提供的是准确候选的实际原模板结构审查证据；本 reviewer 的安装／Git 原件复核补足本节所列范围，不能将后端文本回复升级为安装、现场或 CI 运行证明。

本次补核仍只执行只读文本、Git、ZIP、哈希与 JSON 观察，只追加本报告；未重跑测试、模型、服务或安装，未改产品／测试或提交。M1a 的已审固定实现及本地安装验收现已闭合；发布／准确远端／自身 CI 仍另记，M1b及后继多轮能力继续保留原停点。
