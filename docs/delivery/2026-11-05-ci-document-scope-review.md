# V5：文档push分流独立审查

日期：2026-11-05。审查者：新的fresh-context独立代理 `ci_document_scope_review`。按根AGENTS及maintainable-project-delivery的independent-review brief开展；只读核查并写本报告，没有实施、提交、推送、访问受限Actions API、安装、重跑矩阵或启动服务／模型。

## 结论

**需求符合性：本地实现通过，精确交付和远端触发验收待完成。可维护性：通过。** 在下面的固定范围内没有P1／P2／P3 finding，也没有要求修改实现的阻塞项。该结论不能登记V5完整完成；剩余证据见末节。

原问题是受支持分支的纯文档push也启动双OS wheel、原生回归及Windows安装。当前仅在原`on.push`加入`paths-ignore: ["docs/**.md", "README.md", "AGENTS.md"]`，使用已有平台配置表达规则。`pull_request`和`workflow_dispatch`未过滤，原分支范围、矩阵、检查名称、测试／安装步骤、权限、并发和超时保持。未新增生产模块、包装、分类器、依赖、job或镜像实现的测试／断言。

## 固定身份与范围

审查时分支为`refactor/architecture-foundations`，HEAD和基线均为`73cd3cee8fe893b9342dcafcf0fa5cf3d9389cbe`。逐项核对以下7文件的SHA256等于`.ergora/checks/ci-document-scope/review-scope.json`，Git实际tracked差异与`review-tracked.diff`逐字相等；新增交付记录完整读取。工作流候选SHA256为`cb71926d527a85a23c470d3df0738caf87119575e88bf193ac47abf90c785043`。

- `.github/workflows/portability.yml`
- `docs/PLAN.md`
- `docs/delivery/2026-11-05-ci-document-scope.md`
- `docs/delivery/2026-11-05-new-user-acceptance-review.md`
- `docs/delivery/2026-11-05-new-user-acceptance.md`
- `docs/plans/2026-11-01-all-in-one.md`
- `docs/plans/2026-11-05-new-user-acceptance.md`

除工作流外，改动是V5说明／当前计划，以及原G0审查者的精确终结追加／状态记账。它们没有提前宣布V5实际触发通过，也没有改变已结束G0的生产、测试、依赖或352资源。本审查不重开G0，不把其历史运行视为V5验收。

## 行为、成本与边界

过滤位于拥有事件语义的原workflow，没有另建规则所有者。官方原生`paths-ignore`在全部变更路径均匹配时跳过；任一不匹配路径仍运行。`docs/**.md`限根`docs/`下的`.md`路径，根README／AGENTS分别列明；冻结`src/**` Markdown、`docs/distribution` HTML、workflow、脚本、配置和未知路径均不在忽略集合。只减少符合规则的push调度，PR／手动完整门禁保持；没有依据支持删除旧反例或生产守卫，本片也未做这些更改。成本收益限于可跳过的调度范围，未量化节省比例／时长。

独立核原官方页面SHA256为`683333d8e24140a39426beb7f605bd0122c7289b127f87ac241612ab2b43ca3a`，大小2,104,448字节，与`source.json`一致；抽读[GitHub工作流语法](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)的路径排除、通配符、diff及Pending段。官方`**.js`跨目录例支持本片模式解释；当前文件窗口为3,000，超过1,000提交或diff超时会运行，不能套用旧300文件口径。

未过滤的PR入口避免把同一文档过滤直接施加于PR必需工作流。但未读取实际branch protection／ruleset，也未创建真实PR，故不能声称任意远端required-check设置已验。大diff窗口、复杂重命名及新分支／多提交的服务端diff仍受平台语义约束；六个本地模式例不是这些远端事件的实测保证。当前交付记录保留了这些限制。

## 实际核查

独立从精确Git基线取原workflow，用现有应用解释器的PyYAML BaseLoader解析原／新配置；移除唯一新增push过滤后整份对象相同，并核实际文本恰为一行插入、工作树workflow字节等于`candidate.yml`。因此保留矩阵、完整测试、原必要步骤及执行配置的结论来自实际配置比较。

阅读`prepare.py`、`preparation.json`、`workflow-verified.json`与六类代表路径：公开文档忽略；mixed／冻结Markdown／发行HTML／workflow／未知均不忽略。此处只接受它们作为静态示例，不把Python fnmatch或YAML解析当成GitHub执行器。

独立核`static-documents.json`六文档摘要与上述scope相同，并重新只读检查256个本地链接／锚点、使用现有app实际parser解析README的30条命令，全部通过；未执行业务示例。`git diff --check`通过。已核原静态命令exit0及记录内容，不改写原证据。未重复本地重型回归、Windows矩阵、G0模型或退出检查。

## 剩余交付与限制

实施者应将本报告及审查状态纳入最终scope／静态清单，普通提交推送含workflow的精确候选，核实际自动run、对应源码完整SHA和原必要步骤；随后用仅文档提交观察公开Actions事件窗口，保存查询方式、时间和实际结果。查询失败或窗口内未见run不能写为永久不存在。若外部读取受限，明确保留未验事实，不以修改认证／branch protection替代证据。

取得这些证据后由同一审查者终核精确提交／实时远端及实际Actions事实，才能登记V5完整完成。当前无成功Actions观察结果可供本审查核验；没有将其推断为CI未触发。F6独立原型及后续审查属于另一切片，不在本次范围。

## 精确提交与同片最终终结

2026-11-05，同一审查者独立核Git对象：实现提交`51284fd87943c426b5420a9782483cdadc3e3e44`唯一父为原基线`73cd3cee8fe893b9342dcafcf0fa5cf3d9389cbe`，完整8文件及各blob SHA256逐项等于`final-scope.json`，原tracked部分逐字等于`final-tracked.diff`。初审后仅补原报告及状态说明，workflow仍是原已审一行过滤；追加终结前原报告字节保持。后续文档提交`df0a908893970d12208b3a2026d19b4591f83989`唯一父为51284fd，恰含PLAN及本片交付记录两份Markdown，摘要等于`docs-only/scope.json`；未改变workflow或运行路径。两个精确提交各自Git archive内352资源均逐项等于原包身份表，没有借用后续工作树替代提交内容。

独立核两次普通push的实际exit0原记录、正常前后提交范围、`HEAD`到原工作分支及无force参数；原ls-remote回执分别绑定实现和文档候选。审查者复用既有授权的每命令传输设置，于 **2026-11-05 02:03:23.175189 UTC** 另行只读实时ls-remote，实际exit0，远端`refactor/architecture-foundations`完整SHA为`df0a908893970d12208b3a2026d19b4591f83989`，与精确候选一致。未输出或落盘传输命令及凭据。

独立重核`ci-html-status.json`六份来源的字节数／SHA256，并解析原官方列表、run和两个job HTML：[Portability 41950353820](https://github.com/626619403/Ergora/actions/runs/41950353820)确为`Triggered via push`且`Success`，对应完整51284fd源码和原workflow路径。Ubuntu job`126992566188`／Windows job`126992566519`的selectedJobId、矩阵名称、wheel安装、包身份、原生回归及Windows安装升级必要步骤均逐项核实为success／completed，实际日志URL绑定51284fd完整SHA和各自job；未见failure／cancelled／timed_out步骤。原矩阵已成功结束，没有将初始In progress或历史生产CI充作本次通过。

文档候选普通push回执时间为01:55:21 UTC。独立核`docs-only/window-summary.json`及两份原官方HTML／观察记录的摘要：**01:57:07.628016及01:59:09.383829 UTC** 两次HTTP200的分支Actions列表各含25行，均未见df0a908提交行，均保留51284fd的原Portability run。结合精确两文档集合与已核原生过滤语义，这是本次有限窗口内符合预期的观察；不能证明未来永久不存在run，也不能替代真实PR／manual／branch protection验收。原矩阵实际成功，未因这次文档push被取消。

终结前核最终静态记录实际exit0，7文档258本地链接／锚点和30条README parser命令的摘要绑定当前记录，`git diff --check`通过。提交后两文档仅追加实际CI／窗口结果与阶段状态，未扩大本片运行变更。F6独立原型的进度记账不构成本审查对其功能、CSP方案或性能的通过，须另片验收。

**V5需求符合性、可维护性及精确交付全部通过，无未解决finding，可登记完成。** 本次只追加本报告；未提交、推送、安装、重跑G0／模型／本地重型矩阵、访问受限REST或改变远端规则。PR和手动入口未过滤是配置核实，实际远端规则、大diff的3,000文件窗口／1,000提交及超时语义、复杂重命名等未验范围保持；后续状态归档不需递归审查。
