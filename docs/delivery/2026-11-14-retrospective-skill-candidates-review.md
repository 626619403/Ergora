# F10c2a 独立需求／结构与成本审查

日期：2026-11-14。Reviewer：fresh-context 独立 reviewer；未继承实现会话。项目 `Ergora`，分支 `refactor/architecture-foundations`，精确基线及初审 HEAD 均为 `396e9d175cbbcd120dac29b45a2665002984a53b`；审查对象是该基线上的未提交工作树，完整 `git status --short` 与 tracked diff、全部本片 untracked 产品文件均已检查。依 `maintainable-project-delivery`、`codebase-design`、`review-pr` 执行；本 reviewer 仅写本报告。

## 当前最终本地结论

**需求轴 approve；结构／成本轴 approve；开放 finding 0。** R1–R4 已修并按下文复核，最终本地身份为 r4 wheel `377cee68ab99b94136d32ca38b07625d3d397d9e98d20a981a72b2e5881cc8bc`。586 产品／两 RECORD（594／599）／283 原参考、291 通过／7 平台跳过、实际 Codex→Claude 双叶与原自身模板授权回退、236 原引用均已直接补核，详见文末最终验收。

此结论限 F10c2a 的完整 Skill 只读提案准备／检查。实际模型返回 null 候选；正候选身份由回归保护。未发生发布／自己的 CI，未验原生 Windows、真实改进效果、评价／采用／回退、记忆／流程候选或页面，均保留后片。以下初审与各次复核按发生顺序保留。

## 初审结论

需求轴：**request changes**。结构／成本轴：**request changes**，限下述同一组可达输入问题；未发现需要新框架、第二账本或更换 owner 的理由。开放 Medium 2 项。最终非 editable 包、实际 CLI／模型叶链、自身模板及公开 evidence 尚待提供，当前不是最终验收结论。

### R1 — Medium：原 owner 接受的 CRLF Skill 无法进入新冻结路径

位置：`src/ergora/retrospectives.py:67`；`src/ergora/skill_assets.py:22`。

`skill_assets.metadata(directory)` 通过 `Path.read_text()` 读取，Python universal-newline 会把磁盘 CRLF frontmatter 转为 LF；原 `import_bundle()` 因此接受它。新 prepare 保留原字节，`raw.decode('utf-8')` 后直接交给 `_file_manifest → parse_metadata`，后者只接受 `---\n`，CRLF Skill 必然在这里失败。这不是非 UTF-8 文件，也不是身份变更；常见 Windows／Git CRLF 资料符合原导入路径，现有合法 baseline 却无法准备复盘。

只读纯函数探针：相同正文 LF 的 `parse_metadata` 返回合法 name／description；CRLF 版本抛 `ValueError: SKILL.md requires YAML frontmatter`。原 `metadata → import_bundle` 的读取与调用路径已直接核对。

最小修正：在共享元数据 parser 内按原文本读取语义规范化换行，只用于 frontmatter 解析；冻结的 `files[*].text` 与 manifest SHA 必须继续保留原 CRLF 字节。用现有 fixture 的 CRLF baseline 路径保护这个新旧 owner 不一致，不要把 baseline 转写为 LF 来绕过。

置信度：99。

### R2 — Medium：声明有效的候选文件集可能无法构成普通目录

位置：`src/ergora/retrospectives.py:61`–`69`。

`_file_manifest` 逐条验证相对路径，但没有核文件与其祖先目录的关系。返回 `files={'SKILL.md': ..., 'SKILL.md/child.txt': ...}` 时，每条路径都通过原 `relative_path`，schema／metadata 也有效，最终 check 会给出非空 `candidate_digest`。这个集合在所有文件系统上都不可能同时写成普通文件；后续显式导入必然失败，违背本片“完整标准 Skill 文件集”的出口。`a` 与 `a/b` 是同一问题。另有 `references/Example.txt` 与 `references/example.txt` 在 Linux 上可接受、到 Windows 冲突的便携性缺口；原 definition bundle inspector 已有 casefold 前缀检查可参考。

只读纯函数探针已证实上述 `SKILL.md/child.txt` 文件集被 `_file_manifest` 接受并返回 digest `f7d36ac15b57172c953c46e03801407bb8850045f91f6efe627306b7616993eb`。casefold 示例也被接受。现有 `path` 参数实例仅测 `../escape`，不会覆盖文件与目录的冲突。

最小修正：在现有局部 `_file_manifest` 中核完整文件集：任何文件不得是另一文件的路径祖先，并核所有路径前缀的大小写拼写一致；拒绝而不是覆盖或删文件。无需新增公共抽象、临时 materialize 目录或导入候选。给原参数化反例增一项实际不可能的树，确保 CLI 在失败前不输出候选。

置信度：99。

## 直接检查的结构、复用与权威

- `retrospectives.py` 是顶层复盘用例 owner，生产消费者仅 `cli.py` 的 prepare／check 两个入口，不能称作两个独立生产文件复用，也没有已实现页面消费者。它聚合 evidence、current Skill、原输入及提案检查，保留在单一用例 module 有具体 locality 理由；塞进 handoff、原 Agent runner 或通用 bundle 库会反向耦合候选语义。
- 私有 `_encoded` 的两个位置使用同一规范 JSON 身份；私有 `_file_manifest` 在本 module 的 baseline prepare／check／候选路径复用。不以内部重复调用或测试冒充跨文件复用，局部算法留在 owner 合理，R2 应在这里补齐。
- `asset_trees.manifest_digest` 的真实生产调用文件为 `asset_trees.py`（原 `inventory_tree`）与 `retrospectives.py`；逐字保留原 `json.dumps(sort_keys=True)` 身份，没有把 handoff 的紧凑 UTF-8 canonical JSON 混用为 Skill 身份。
- `skill_assets.parse_metadata` 的真实生产调用文件为 `skill_assets.py`（原 `metadata`）与 `retrospectives.py`；归原元数据 owner 合理，但 R1 显示共享实现尚未共享完整读取语义。
- `definition_bundles.parse_json` 的真实生产调用文件为 `definition_bundles.py`（原 read／convert）与 `retrospectives.py`（外层结果／内层 response）；仅公开原重复键拒绝 parser，无新 JSON parser。其既有读取合同未改。
- 新 Schema 是供模型与 checker 共用的提案数据合同。两 Agent、一 Workflow、祖先 Skill 均是现有 preset 配置接口；依赖顺序与角色／后端由原 composition／Agent owner 持有。新模块没有根据 Codex／Claude 类型分派。模板角色是提案作者／复核者，不是评分器或采用者。
- prepare 沿 `handoff.evidence` 读取原完整 index 与显式选中 artifact 正文，核项目、精确 Skill name／digest／head revision，冻结完整文本／执行位并调用原 `prepare_input_from_manifest`；没有另拼模型调用。check 沿原 `inspect_input` 全树／task／prompt／原祖先资料校验，验证外层 Agent result、内层 proposal、frozen evidence canonical SHA、baseline manifest SHA 和引用集合；无需 State／实时源。
- 原 `_Compilation` 累积所有祖先资源并核权限与容量；新 preset 的 write／shell／network 均为空。原 `agent_runs._admit_input` 仍持有只读调用准入、backend override 和实际调用。原 Skill／evaluation／skills 仍持有导入、可信评价、明确采用与回退。check 仅返回数据，未写目录、数据库、活动 head、可信评价器或项目配置；`quality_evaluated`／`adoption_authorized`／`origin_authenticated` 均明确为 false。对来源内容真实性／泛化质量不作认证，这个限制与范围一致。

## 控制流与成本

已逐项追查新增 guards 的可达情况：跨项目资料、同 digest／不同选择名、baseline 文件变动、1 MiB 完整文本上限、当前 head revision 冲突、有界结果／可选原 SHA、原输出合同、来源／基线／引用错绑、候选名变更、无观察却给候选、NUL／`.git`／越界路径，均落在外部输入或冻结身份的 owner，未发现与本片无关的参数门禁。R2 是完整集合缺项。

prepare 对 baseline 的前后 `skill_assets.get()` 各执行一次磁盘目录身份校验，中间有有界完整读取；第二次用于检出读取期间目录／执行位变化，不能简单视作无理由重复 guard。内存 `_file_manifest` 重算冻结身份用于证明文本／执行位与原 digest 同一。handoff 沿已存在的 72 MiB packet／64 MiB payload、1 MiB selection 上限；本片没有重新实现 ZIP 校验或放大 alias 副本。check 的结果读取上限为 1 MiB，候选文件最多 500；其成本集中在原输入完整校验与有界 JSON／文件 SHA，本片不进入训练／模型 hot path。未作性能优化成功主张，也未跑额外 benchmark。

新增测试 1 fixture、3 测试函数／6 实例复用原 suite 与 handoff fixture；完整中文附件、来源删除后的离线检查、name／digest 目录身份对齐、当前 head conflict、null 候选及误绑／越界无部分 CLI 输出分别保护真实合同，没有固定 preset 文案断言。没有另建测试框架。R1／R2 尚未覆盖。

## 检查、身份与待补证据

已读 `AGENTS.md`、`docs/PLAN.md`、F10 总计划、本片活动计划／交付；逐项检查完整 status、固定基线 tracked diff、本片全部 untracked 产品内容、相邻原 owner／调用者。旧 F10c1 发布／CI 文档补记未当成本片产品改动。

直接读原 `development-r3/stdout.txt`：6 passed／18 deselected／6.13s；该运行早于随后加入的 frozen evidence canonical SHA 门禁，不能代替最终包验证。r1／r2 失败仍保留，未继承通过。本 reviewer 未安装、联网、改产品、运行 suite 或发外部消息；仅以 `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python` 做上述无文件写入纯函数探针。

待：两项实证修正与同 slice 复核；最终包／两 RECORD／283 原参考身份、实际 CLI 作者→原结果→复核叶的完整 input／stdin／reply／原后端失败与授权回退、自身结构模板、公开 evidence 和收尾原件。未到的验收不预设结论。

## 同 slice 首次修正复核

R1：**源码修正通过**。共享 parser 仅在解析局部把 CRLF／CR 转为 LF；prepare 的原 `raw.decode`、文件文本及 digest 未改。新增 `test_retrospective_accepts_crlf_metadata_without_changing_frozen_file_bytes` 经原 import→prepare→check 路径，逐文件用重新编码字节对比原磁盘字节，确实保护本 finding，未用转写 baseline 绕过。最终包身份另核。

R2：**部分修复，仍开放**。新的 folded parts 排序／邻接 prefix 检查已拒绝 `SKILL.md/child.txt` 与 `skill.MD/child.txt`，新增两参数实例保护该行为；没有逐层 join 的平方开销。但 `references/a.txt` 与 `References/b.txt` 的共同目录前缀仍被接受：两完整 folded 文件 tuple 不相等、也无完整 file tuple 是另一文件祖先，故当前条件为 false。Windows 上两前缀只能是同一目录拼写，不能保留声明文件路径；实际 inventory manifest 将与候选声明不同。原报告的全路径前缀大小写一致性未闭合。只读纯函数探针直接确认此集合仍 `ACCEPTED`。

最小后续修正仍可用相邻排序：保留原 parts 与 folded parts，比较相邻路径共同 folded 前缀的原部件拼写，遇不同拼写即拒绝；保持现有 file-parent 检查，无需逐层构造字符串前缀或新 trie。建议把目录前缀冲突作为现有参数测试的一项。

直接读取 `review-fixes-r1/stdout.txt`：**3 passed／24 deselected／3.22s**。本 reviewer 只做纯函数只读重核，未重复 suite。当前需求／结构成本轴仍 request changes，开放 Medium 1 项（R2）；R1 最终安装回归证据待。

## 同 slice 第二次修正复核

R2：**源码修正通过**。现有局部算法保留 folded／原 parts，按 folded tuple 排序后比较相邻文件：先拒绝 file-parent／完整 case collision，再只沿共同 folded 前缀比较原部件拼写。这样目录前缀组在排序中连续，邻接变化即可检出不一致，不需要逐层 join 字符串或新 trie；新增成本是有界文件集排序与总路径比较。新增 `directory-case` 用 `References/new.txt` 与 fixture 原 `references/evidence.md` 走实际 CLI check，确实保护原遗漏。

只读纯函数重核：文件祖先、大小写文件祖先、浅层／深层目录前缀拼写、完整文件 case collision 均拒绝；同目录正常不同文件接受。直接读取 `review-fixes-r2/stdout.txt`：**4 passed／24 deselected／4.24s**。另读 `review-red-r1/stdout.txt`：原修前安装件在这四例 **4 failed／24 deselected／4.06s**，具体失败为三种非法文件树被接受，以及 CRLF baseline 被拒绝，原包未被改写。

R1／R2 均已源码关闭；开放 finding 0。源码需求／结构成本轴 **approve within inspected source scope**，最终本地验收仍 pending，不能借旧安装件 r1 的正常 suite 或模型调用覆盖修后候选。新增 README／USAGE／当前架构 diff 已读：命令沿原准备／显式两次叶调用／后继完整 checked JSON，null 候选与评价／采用限制有明确说明，未见新增 finding。

## 自身模板意见的独立判定与 R3

已读 `self-review-r2-claude/review.md` 原回复；它基于提供的 17 完整文件作静态审查，未得到 handoff／composition／Agent／contracts 相邻 owner。本 reviewer 对照这些实际 owner 独立判定如下，未把其 request-changes 当作自动结论。

### R3 — Medium：可完整冻结的合法基线，其完整提案会被较小的结果上限拒绝

位置：`src/ergora/retrospectives.py`，check 的 `stream.read(handoff.MANIFEST_LIMIT + 1)` 与 1 MiB 结果门禁。

此项由自身模板 M2 提示，已用更强的可达输入确认，不依赖“基线近 1 MiB”或模型可选的 Unicode 转义。取实际 `native-r2/author-input` 的原任务和原 composition，仅把 baseline 的一个完整 reference 文件设为 35,000 行 `{"key":"value"}\n`（560,000 字节），重新计算原 Skill manifest 身份。`_REQUEST` 与 proposal schema 验证通过；调用原 `compile_input(..., 1000000)` 得到完整 task **740,837B**、完整含祖先 prompt **745,317B**，准入确实可达。

该 baseline 的完整候选只在 SKILL.md 增加一条短规则，保留 reference，inner proposal 使用紧凑 JSON／非 ASCII 原文；按原 `agents.invoke` 的 outer `json.dumps(..., ensure_ascii=False, sort_keys=True)` 输出 **1,050,977B**，仍超过当前 **1,048,576B**。普通双引号与换行在两层结构里的必要转义已足够触发问题。另一个合法 400,000B 反斜杠参考文件的 task 为 805,837B、结果 1,600,977B。这不是任意新增过长文件导致的通常容量失败，而是现有完整 baseline 可以进入模型、等量完整候选却无法返回的合同不一致。

后果：符合原输入容量、保留完整支持文件的有依据建议仍在模型调用后被拒；操作者只能丢失原文件或放弃正候选。最小修正：结果容量由复盘用例单独拥有，例如 8 MiB，并在 CLI／USAGE 明确输入与结果分别有完整容量限制；保留有界读取和原 prompt 容量。不需要降低原输入限制、引入最坏编码预估或自动截断。用现有用例保护一份 input 可准入而双层结果超过 1 MiB 的真实完整候选即可。

置信度：99。当前源码需求／结构成本轴恢复为 **request changes**；开放 Medium 1 项（R3），R1／R2 保持关闭。

其他自身模板意见：

- M1“reviewer 分支 dead”不成立：原 compile_input 明示端口未执行，自有只读 proposal-producing leaf 可以声明 reviewer role 并依原 `result_schema` 返回 decision 与 proposal；分支可达。preset 的实际 reviewer 接收完整 checked JSON、返回 prose，USAGE 沿原 prepare-from-manifest 明确操作，不调用 retrospective check。最小澄清是说明 prepare／check 面向输出 proposal 的叶，而 preset reviewer 使用已列出的原路径；不应为了 preset 特例禁止所有 reviewer-role 自定义叶。
- L1 的容量归属可随 R3 修正。L2 的一行 canonical JSON 与原 handoff 的公开 selection SHA 定义逐字一致，是当前固定数据合同；无需为消除一行局部编码而扩公共函数，未列阻塞项。以后原 owner 有实际离线 evidence 验证消费者时再收口完整验证更有价值。
- L3 删除第二次 get 不采纳：原 per-file SHA／内存 manifest 不覆盖读取期间新增文件、删除或执行位变更，末尾完整目录核验有具体行为，不是无理由重复。
- L4 把现有跨 suite fixture 搬到新 helper／conftest 没有现成复用收益，非必要。反例匹配自身 stderr 有小而实际的价值，可避免未来提前在不相关门禁失败而假绿；原安装件四例实红已经证明当前 finding 的实际原因。

## R3 源码修正与新增 R4

R3：**源码修正通过**。`BASELINE_LIMIT=1_048_576`、`RESULT_LIMIT=8_388_608` 归复盘用例所有，check 仍只读一次有界结果、先核原结果 SHA 再解析；原 composition 1,000,000B 完整 prompt 上限未改。新大候选 case 用真实 560,000B JSON reference 经原 import→prepare→check，核结果大于原 1 MiB、保留完整 reference 与原 response，针对已证实条件，没有新增容量预估框架。CLI／USAGE 明确输出提案叶、preset 文字审查叶和后继另过完整容量，未加角色特判。七反例增加各自 stderr 原因匹配，采纳了自身模板 L4 的有价值部分。最终红绿／包待。

### R4 — High：新增正文断言在 Windows 的实际全套 CI 必然失败

位置：`tests/test_skills_evaluation.py:440`、`:542`、`:552`。

fixture 在 `:397` 用默认 `Path.write_text` 写 LF 字符串；Windows 上默认 newline 会写为 CRLF。产品 prepare 正确保留 `raw.decode`，新 full-baseline 测试却用 `Path.read_text()` 的 universal-newline 结果（LF）与 frozen text（CRLF）比较，必然不等。R3 大 reference case 的 `write_text(reference)`／`frozen_text == reference` 有同一问题。此项已有真实生产 CI 消费者：`.github/workflows/portability.yml` 的 `windows-latest`／Python 3.12 配置 `group: all`，原 `scripts/ci/run.py` 会收集这些未跳过的新测试。

纯内存标准库探针用 `TextIOWrapper(..., newline='\r\n')` 模拟 Windows 默认写入，原字节正文为 `...\r\n`、默认文本读取为 `...\n`，与上述实现和断言逐字对应；未冒称已在 Windows 跑验收。Linux 通过不能覆盖此条件。

最小修正：普通 fixture 和大 reference 明确写 UTF-8 原 bytes／LF，或把完整冻结断言统一为 `frozen_text.encode('utf-8') == path.read_bytes()`；不要修改产品冻结原字节。已有专门 CRLF case 继续负责合法 CRLF 接受与字节身份。修后只需相关测试重核及自己的 Windows CI，毋须额外测试框架。

置信度：99。R1／R2／R3 源码关闭；需求／结构成本轴当前 **request changes**，开放 High 1 项（R4，测试可移植性）。

## R4 源码修正复核

R4：**源码修正通过**。普通 fixture 的 SKILL.md／中文 reference 改为显式 LF UTF-8 bytes；完整正文断言用原 `frozen_text.encode('utf-8')` 对比 `read_bytes()`；大 reference 用 `write_bytes(reference.encode('utf-8'))`，因此其与 LF reference 的比较不再依赖平台 newline。专门 CRLF case 继续把确定的 LF 原 bytes 转为真实 CRLF，再逐文件核冻结 bytes；没有改变产品或把换行规范化后冒称原字节一致。

七个拒绝参数实例各匹配对应错误原因，已逐项源码核对。活动计划新增独立基线／结果容量及每叶完整 prompt 限制，和 CLI／USAGE 一致。

R1–R4 **源码全部关闭，开放 0**。两轴源码范围 **approve**；最终 r4 非 editable 安装、红绿／原 suite、原实际双后端叶、原自身模板复审、公开 evidence 和收尾仍为 pending。r1／r2／r3 的包与运行保持原身份，本 reviewer 未把它们继承为 r4 验收。

## 最终 r4 本地证据补核

最终 HEAD 仍为原 `396e9d175cbbcd120dac29b45a2665002984a53b`，本地改动未提交。重新检查完整 status 与基线差异：本片 15 份 source／test 包括 5 份原 owner／catalog、9 份新增产品文件与原 suite；README、USAGE、当前架构、F10 总计划和本片记录已读。旧 F10c1 发布／CI 补记保留其独立范围。本片没有新增迁移、数据库、调度、模型执行分派、评分器或采用者。

直接校验最终 r4 wheel 全部 586 产品文件与当前 source、构建快照、非 editable 安装逐字相同；wheel／安装两份 RECORD 分别 594／599 行，其全部带摘要条目的 bytes／SHA 正确。原参考 283 项另与固定基线 Git blob 及执行位逐项核对，未变。公开证据中的 15 份当前 source／test SHA 全部匹配，测试与 r4 快照一致。

直接读取原安装 `install-r4/regression-r1/result.json` 和 stdout／stderr：八个原 suite **291 passed／7 skipped／219.22s**，monitor **220.7436761688441s**、returncode 0，stderr 为空；解释器为 r4 wheel venv，`-I` 运行。7 项为 Linux 上的 Windows 平台跳过，未当作 Windows 运行通过。另直接读取 R3 的 `capacity-red-r1`：不改的旧 r2 安装件 **1 failed／1.48s**，明确失败于旧 1 MiB 结果门禁；`capacity-green-r1` 的 source 用例 **11 passed／11.27s**，最终 r4 的相同大候选回归另在上述 291 项中通过。

实际 `native-r4` 八 CLI 的 stdout／stderr SHA 逐份核对，七项 exit 0、错误原结果 SHA 一项按预期 exit 2。原 Codex run `4829040588ba4076ae4b25196def1567` 与 Claude run `084c2b1354d042a680186009e55d353b` 均 succeeded。使用原完整 input inspector 重核每份冻结图／task／prompt／digest，逐字比较实际 stdin、全部祖先资源与原结果 SHA；后继包含整份原 checked JSON。重新执行的只读 check 与保存输出逐字段相同，未创建 unused State，也无部分错误 stdout。作者为 **candidate:null**，Claude 为 **approve**，这是一条完整的合理无改进旅程；完整正候选／CRLF／误绑／路径／大结果由安装回归证明，不扩为真实正候选或测得收益。

另以 SQLite `mode=ro&immutable=1` 直接读取原 Skill 表，与 `versions-before.json` 比较，versions／heads／history 全部相同；原 stored baseline 目录 digest、原 packet SHA、fixture Git status 均直接比对未变。prepare／check 的原 authority 范围由源码和实际原件共同保持。

原自身模板 Claude run `a8c8749c37084bb7b838a239d89ed374` 的 **timed_out／360.552s** 保留，无 result；用户授权的独立新 Codex run `266f540bd3c94c0e9285c47bb0b17610` **succeeded／45.359s／approve**，明确保存 fallback reason。两个原 input inspector 的 digest 同为 `10b4e93a376dff1bb0047540f4e1ee4bae690dec13de09fc5aa642d5356cd0df`，prompt SHA 同为 `d2016ca8b22c18e160b83a19e0d2b9d0e262094cc35e37faac0bda36e0e68f07`；310,068B prompt 与各自实际 stdin 完全相同。原 packet 的 **23 份／303,397B** 按每份声明字节长度直接从冻结 task 取出核 SHA，均完整，包括原 request-changes 回复与必要相邻 owner。最终回复 SHA `56649e900dba67998a838b061e33d0bd7838bd5c273058280979a7d8d4922c38` 已核；其静态 approve 没有替代本独立审查，也没有冒称本次自身模板异后端通过。

公开[最终 evidence](evidence/2026-11-14-retrospective-skill-candidates.json)的 **236 份**原引用逐份核 bytes／SHA，无缺失或不一致；prepare 读原 State、check 离线无 State 的说明修正后又核过全部引用。公开汇总没有机器绝对路径、凭据或服务地址。原 cleanup 记录全部本片调用／harness 终态，可访问 `/proc` 范围内无本片 cwd 进程，10 个进程不可读；未启动服务／浏览器／端口。该范围未扩大为全 OS 进程证明。

文档已明确独立基线 1 MiB／结果 8 MiB、每个后继完整 prompt 的独立容量，preset 的文字审查与 proposal-producing 叶入口不同；后继手册指向原 `evaluation run`／`skill adopt`／`skill rollback`。F10c3a 优先闭合现有 Skill 的原评价／采用／回退，再扩记忆／流程，属于后续顺序调整，无新产品混入。相关文档路径／既有手册锚点和 `git diff --check` 已核。

**最终本地需求轴 approve；结构／成本轴 approve，R1–R4 全部关闭，开放 0／0。** 无其他已证实阻塞项。本 reviewer 未联网、安装、运行 suite、改产品、提交或发送外部消息；执行的均是源码／原件读取、纯函数探针和只读身份校验。普通发布、完整远端 Ref、该候选自己的 CI 及固定发布补核仍待，不能从此前候选或本地验收继承。F10c3a／记忆流程／页面、原生 Windows、真实业务／GPU／质量与完整 Forge 保持后续责任。
