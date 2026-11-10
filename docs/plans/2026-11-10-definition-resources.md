# AC5 C3c：完整资源修订

设计基线 `3baa619096a2ff95e2a29aedf179f3c614af103e`，分支 `refactor/architecture-foundations`。先读 AGENTS、PLAN、[C3 合同](2026-11-10-definition-revisions.md)、[本片记录](../delivery/2026-11-10-definition-resources.md)及[C3b 交付](../delivery/2026-11-10-definition-editor.md)。C3b已普通推送、独立精确对象和明确HTTPS同SHA通过；自己的CI42769849207第三份官方终态双OS七必要步骤成功，新独立06:58:51 UTC直接核原件通过。前片精确交付已终结，本片先完成设计门禁再实施产品。本计划不是资源编辑已实现声明。

## 目标和所有者

操作者可在固定原包上追加或修改 instructions、context、完整Skill树及普通附件，明确接受新内容摘要，再检查和发布一个新版本。原版本、未改附件/空目录、旧manifest及活动任务不变。Agent与Workflow共用资源派生算法，沿原完整包准入，不另建资源库、上传会话数据库或运行账本。

- `definition_bundles.DefinitionLibrary` 已由两类定义用例调用；其 `export`/`revise` 继续负责固定基准、完整暂存、清理和不可变发布。资源操作进入这一个所有者，不能在CLI、HTTP、页面各写一遍复制或摘要算法。
- `asset_trees.inventory_tree`/`digest_tree` 继续计算原文件/Skill树身份和10MB/500文件/500目录/32层边界；`relative_path` 与原包检查继续负责可移植路径、大小写冲突、链接/reparse/special-file拒绝。标准JSON仍仅由原序列化器重写，不引入新的模板格式。
- 两类 `revise` 用例和CLI/HTTP保持薄入口；页面由原 `definitions.js` 会话拥有原文、资源操作缓冲、世代、检查和发布。祖先材料和权限继承仍由原Workflow编译器决定，资源内容不授予MCP/执行/网络权限。

## 接口与交互决定

1. 固定 `kind/id/version/base_digest` 和完整标准正文。新增可选资源操作集合；没有操作时与C3b行为相同。操作只针对包内文件/目录，不接收任意服务器绝对路径。原标准 `agent.json`/`workflow.json` 只能经正文入口修改，不能再从附件通道写入。
2. 文件写入携带完整字节与可移植相对路径；CLI从操作者明确提供的本地变更目录读取，HTTP使用标准JSON中的base64字节表示。现有文件默认保留执行位，新文件默认不带执行位；修改执行位须显式声明。文本编辑只允许完整UTF-8；二进制附件原样上传/下载，不做替换字符解码。原包未改文件不重新编码。
3. 明确的删除只作用于新候选中的指定文件；不递归隐式删除未知内容，不根据上传目录缺少某文件就删除原文件。空目录的保留/明确追加沿原包语义；空目录不进入旧摘要算法，但导出必须完整保留。重复路径、大小写/文件目录冲突与有歧义的重叠操作在共同所有者拒绝，不能静默“最后一个获胜”。
4. 资源操作预览只建立临时候选、不发布：保留原包，应用操作，计算各声明资源的实际新摘要，并返回文件差异及建议标准正文。页面明确“采用资源摘要”后才将建议正文应用到已应用快照；自定义JSON/YAML仍遵循C3b同步确认。未接受或过期的资源结果不启用检查/发布。预览不是项目批准或后端认证。
5. 检查/发布携带同一操作与已明确接受的标准正文；原库重新核所有声明摘要及完整准入，而不是信任页面或旧预览。共同Owner生成的候选身份应与明确接受后的check/publish一致。变化、晚回复、同版本冲突、丢响应和显式相同重试保持C3a/b语义，原操作字节不能被回复替换。
6. 文件读取固定原包及期望摘要，经包所有者从原普通文件读取，返回字节身份与明确编码；读取不接受外部路径、不执行内容。大文本/附件采用有界窗口或明确下载，不能用截断后的内容覆盖原文件。读取历史原包不额外要求今天的后端可用。
7. HTTP仍沿原4MB请求边界；base64开销计算在请求内。较大变更使用CLI完整目录路径，沿原包10MB上限，不以“分片”引入第二套服务端持久草稿。浏览器缓存quota失败沿C3b提示并提供下载，不承诺所有最大包都能保存在sessionStorage。未应用资源操作与正文必须一并下载，不能只下载正文而误称完整工作缓冲。
8. 暂存的原文件/父目录可能只读；只调整这个新暂存树内写入/删除所需的owner位，保留原对象和未改文件。不能要求宿主权限，也不能将logical权限校验描述成OS隔离。

## D1 固定接口（r3，独立设计复核通过）

D2 单独形成可用的 CLI/HTTP 纵切片，冻结、安装验收、fresh-context 实现审查、真实自身模板及普通推送/自己的CI后再实施 D3 页面。下列字段是本片输入合同，不是新的 Agent/Workflow 格式；无资源参数时保留 C3a/b 请求和结果。

- 原 `DefinitionLibrary.revise(id, version, base_digest, definition, *, publish=False)` 增加可选 `resource_changes=None`、`accepted_candidate=None`、`preview_resources=False`。两类用例透传，所有暂存/字节/摘要/发布逻辑仍在原库。`resource_changes` 非空对象时，最终 check/publish 必须携带 `accepted_candidate`；preview 必须只读、不与 publish 同用。明确传入空操作集合也走资源合同；没有资源参数的旧正文修订不强迫增加预览步骤。
- 资源操作对象为 `{"schema_version":1,"operations":[...]}`，未知字段拒绝。`write` 为 `{"op":"write","path":"context/info.md","content_base64":"...","executable_bits":0}`；最后一项可省略，已有文件保留其执行位，新文件默认无执行位。执行位只接受 `0o111` 的子集，不能携带 setuid/其他 mode 位；平台不能实现明确要求时拒绝。`delete` 为 `{"op":"delete","path":"old.bin"}`，只删原候选内已存在的普通文件，缺失报错；`mkdir` 为 `{"op":"mkdir","path":"references/empty"}`，仅用于明确增加空目录，已存在的同名真实目录可保持。mkdir和write均自动创建缺失父目录（parents），不需要额外父目录操作。
- 重复操作路径、大小写拼写冲突、操作间祖先/后代重叠均拒绝。mkdir 若与写路径重叠，改为只声明写路径并让所有者建父目录；不存在按顺序解释的重命名/递归删除/最后获胜规则。根目录 `agent.json`、`workflow.json`（含大小写变体）禁止经此通道操作。普通附件允许二进制/空文件；声明为 instructions/context 的正文仍须原非空 UTF-8 合同，Skill 须完整树/正确 frontmatter。沿原路径和完整树上限；操作集合最多1500项、写入总字节最多10MB，最终包仍受原10MB/500文件/500目录/32层限制。
- preview 在完整复制固定原包后应用操作；标准正文必须沿当前 schema（新增声明可用合法64位占位摘要），仅将 `resources` 声明中的 `sha256`/`digest` 替换为原算法计算的实际值，再由原 `inspect_import` 做完整结构/资源/后端/祖先准入。它不是允许无效正文的纯文件扫描，也不会绕过当今准入；只有历史读取不要求今天后端可用。返回建议 `definition`、完整 `files/resources`、文件差异 `changes`（每项 path/before/after）、`directory_changes`（added/removed）、`published:false`、`resource_preview:true` 及 `candidate:{digest,directories}`；directories 是完整排序相对目录列表。
- 接受身份同时绑定完整包文件摘要（包括普通未声明附件、标准JSON、执行位）及完整目录列表。操作者保存 preview 的 `definition` 和 `candidate`，明确用于后续 check/publish；后者重建同一候选，**不自动替操作者刷新声明摘要**，重新完整准入并比对这两项。变更普通附件、执行位或空目录均使旧接受失效。预览和接受无服务端持久会话，不是批准、认证或执行授权。
- 空目录继续不进入旧内容摘要，不改旧对象/manifest格式。资源路径发布通过原 `import_bundle` 的可选 `expected_directories` 在最终发布锁内、任何首次建库/新对象落地/索引变更前核暂存目录与接受值；复用已索引或未索引同摘要对象时还核现存对象目录；若同摘要现存对象的目录列表不同则明确拒绝并要求新版本，不能返回暂存描述却复用丢目录的旧对象。普通旧 import 不因此引入新身份格式。实际返回/导出必须与接受的完整目录一致。
- CLI 两类 `revise` 增加 `--resources DIR`、`--preview-resources`、`--accept-candidate FILE`。DIR 内 `changes.json` 是上述操作对象，write 项省略 content_base64，字节从 `DIR/files/<path>` 读取；不得额外在清单写 content_base64，避免两个来源。由共同所有者读取真实无链接目录并转换为同一内存对象；本地目录（含清单）也受原树大小/数量约束。未列出的文件不会成为删除/写入操作，完全不扫描服务器任意路径。`--preview-resources` 隐含不发布；普通 `--check` 亦不发布；`--accept-candidate FILE` 只读取其中 candidate 对象（可直接使用保存的预览响应）。完整新正文仍用原 `--document`/`--format` 输入。示例顺序为 preview 保存响应→取建议正文→明确接受后 check→明确 publish。
- HTTP 两类原 `/api/{kind}-definitions/{id}/{version}/revisions{,/check}` body 可加 `resource_changes`、`accepted_candidate`；新增同路径 `/preview-resources` 只做 preview。body 不允许 `preview_resources` 切换普通发布的语义，不接服务器本地目录。原4MB请求上限含base64开销，大变更走CLI。没有上传/分片/草稿数据库。
- 固定原包文件读取由 `DefinitionLibrary.read_file(id, version, base_digest, path, *, offset=0, limit=65536)` 拥有，经历史 get/原完整包检查后从已登记普通文件读取并核完整SHA，offset/limit为字节，limit为1–65536，offset不超过文件长度。返回 `base/path/sha256/executable_bits/size_bytes/offset/bytes_read/next_offset/complete/content_base64`；complete 仅表示从offset0完整返回，窗口不能冒充完整文件。所有字节统一base64，页面只有完整读取且严格UTF-8可解码才可按文本编辑。CLI 两类增加 `file ID VERSION PATH --base-digest DIGEST [--offset N --limit N]`；HTTP `POST .../{id}/{version}/files/read` body是base_digest/path/offset/limit。文件路径从不解释为控制目录外的路径，未登记路径拒绝；原标准JSON可读但仍只能经正文修改。

## D3 会话采用与恢复合同（D2不实施页面）

原 `definitions.js` 保持一个共同会话所有者；不创建通用编辑框架。已应用快照含标准正文、**已采用** resource_changes 与 accepted_candidate；工作检查点另存未应用文件/上传/正文原文。读取窗口是只读缓冲，完整下载/合并前不能作为write。preview只产生建议，不修改任一已应用值。

“采用资源摘要”须使用该请求的固定基准/会话世代、完整操作字节及建议正文，原子加入一份已应用历史；若任一正文/资源pending已变化，旧回复只能提示重新预览，不能替换缓冲。正文或操作改变立即使检查失效，并同时清除preview与accepted_candidate；candidate含标准JSON，版本等正文字段变化同样须重新预览/采用。撤销/重做同时恢复三项，保留S5约束，不能把未应用缓冲放进applied history。发布前仍显式check与确认，不让未应用资源时发布另一份旧快照。

刷新恢复需共同转换已应用JSON/YAML、验证资源缓冲形状/完整字节与基准；无效缓存保留原始下载并拒绝继续发布。检查结果/preview回复不持久复用，恢复后清空并重新检查；已采用的候选身份可以恢复，但只有重建匹配后才可发布。切home/基准与迟到/未知发布保持C3b身份保护。历史上限继续50快照/4MiB并计入资源字节；quota失败完整下载正文及所有已应用/未应用操作字节，明确不含未编辑原包（需另行export），不得误称完整独立包。


## 可验收节点

|节点|实施内容|验收出口|状态|
|---|---|---|---|
|D1 资源接口合同|结合现有两个库/CLI/HTTP/会话真实调用，固定操作、读取、摘要接受、无效缓冲与恢复合同|共同所有者及实际消费者明确；不复制原摘要/准入/权限算法；独立设计复核通过，前片CI终态已核后再实施产品|r3新独立Spec/Standards设计门禁通过，DRD-1–6关闭，前片CI已终结；D2接口片开始|
|D2 共同所有者与CLI/HTTP|[独立接口纵切片](2026-11-10-definition-resource-interfaces.md)：固定原包文件读取、完整暂存操作/资源预览，现有两类修订接同一操作，薄CLI和HTTP|两类文字/二进制/Skill多文件与空目录都可完整派生；check不发布；采用摘要后CLI/HTTP同候选；只读原文件/目录可用；原包/未改附件不变|本地I1–I5出口完成，完整34文件新独立两轴终核通过、零开放finding；R3包435/283、46受影响项/三域81CLI37HTTP、第二轮approve及11公开JSON均已核；34文件已普通推送80375d3，自己的CI42779236273双OS七必要步骤成功、原评审者独立终核通过，HTTPS/精确对象同SHA通过；精确交付终结|
|D3 页面资源会话|[页面资源会话计划](2026-11-10-definition-resource-editor.md)：原编辑器内列资源/文件、读取或上传、追加/修改/明确删除、差异和摘要接受、正文/资源共同缓冲|两类浏览器实际操作；未接受摘要/未应用文件不能发布旧快照；切home/迟到/历史/恢复/quota不丢操作字节；二进制不误当文本；下载准确说明范围|E0 r2独立设计通过；E1/E2已实现，RDE-I1最小修后同片17探针关闭；R2包435/283、两类主/17项错误/并发home未知重试/历史容量/完整树双布局通过，未定面板收起观察保留，自身模板282.12秒approve/19连续UTF8已核、9公开JSON/2截图，完整26文件独立两轴通过、RDE-I1/I2关闭，本地出口完成；26文件已普通推送a9778e0；自己的CI42790499318双OS七必要步骤及原评审者官方终态核验通过，精确对象/明确HTTPS同SHA通过，D3精确交付终结|
|D4 完整资源与继承旅程|三领域完整包往返；祖先/子模板新增上下文及Skill附件；权限和旧快照不变|完整附件/执行位/空目录/新资源导出再导入同身份；祖先材料完整可读、工具权限未扩张；新根最后发布；训练保持提案范围|[D4/D5计划](2026-11-10-definition-resource-inheritance.md)J1/J2真实90CLI/55.92秒、11完整树往返/24只读原对象及三旧快照保持通过，J3三次真实只读调用21/21/16资源完整逐字节及37owned采样清理通过；J4首审RIN-S1补原件后第二轮483.04秒approve/27资源完整读取，十份公开证据/清理通过；完整24文件新独立两轴/RIN-S1/D1关闭，本地出口完成、精确交付待办|
|D5 完整交付|最终非editable包、实际CLI/浏览器、两本手册、结构/冗余审查及自身模板|原红保留/受影响回归、fresh-context完整两轴/真实自身模板、公开证据和清理通过；普通提交/自己的CI/明确HTTPS分别终结|D4的J1–J3验证通过；J4自身模板两轮/十份公开证据/清理完成，首审拒绝保留；完整24文件新独立两轴通过、RIN-S1/D1关闭/开放0；本地出口完成、精确交付待办|

每节点完成更新本计划、交付记录和PLAN；完整实现片取得新fresh-context独立审查，不以C3b审查代替。D2固定为独立CLI/HTTP接口片，单独冻结/验证/新fresh-context实现审查/真实自身模板/提交并核自己的CI后再接D3；不发布一半页面能力。资源读取/保存均不启动Agent或项目任务。

## 保持的范围

不在本片修改283冻结参考文件、六阶段、owner批准、candidate/attempt/memo/unknown恢复或Temporal调度。资源声明、权限授权、工具可用性是不同事实；新增Skill不创建MCP工具或执行权限。父子共同提权的完整新根旅程仍需C3d；嵌套画布/差异属C4、正式输入交接属C5、规模容量属C6。训练定义资源往返不代表真实训练优化实验已实现。
