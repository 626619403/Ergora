# 准备完整的单叶输入

简体中文 · [English](../../../definitions/workflows/leaf-calls.md) · [文档目录](../../../README.zh-CN.md)

先完成 [kernel-delivery 依赖导入](compose.md#运行示例)。从包含[示例 grant](../../../../examples/composition/preview-grant.json) 的源码 checkout 运行这些命令，或将该路径替换为你已明确审阅的 grant。然后创建 UTF-8 任务文件。 `review-task.txt`

```bash
ergora composition prepare kernel-delivery 1.0.0 root/review/structure/review --grant examples/composition/preview-grant.json --task review-task.txt --directory ./prepared-review --max-prompt-bytes 30000
ergora composition verify-input ./prepared-review
ergora composition verify-input ./prepared-review --material
```

准备操作仍检查当前Agent准入；它不调用模型、不执行前驱/端口，也不批准工作流。任务由操作者明确提供；例如把执行结果交给审查者时，操作者需要自行提供对应的任务材料，不能把此输入包当作已验证的自动数据流。

输入包含 `request.json`、完整 `composition.json`、原始 `task.txt`、完整 `prompt.txt` 和 `assets/` 中所有精确引用包。Skill目录的脚本和附件一并保存；资源正文仍按root→leaf完整装载。`verify-input --material`会重编译包内静态组合并核完整user prompt，源State删除后仍可使用，不依赖当前后端catalog。核验不会执行Skill或后端。

`max-prompt-bytes`必须为1–1,000,000，计完整user prompt的UTF-8字节，超过就拒绝，不截断。它不证明模型token容量或后端额外系统提示能容纳。整个输入包最多10MB/500文件、1000目录和48层，复制过程中也检查；失败不发布半包。只能保存到新目录，且不能写进不可变定义库。原子不覆盖发布支持Linux（需要renameat2）与Windows；不支持时明确失败。核验前后会检查整树一致，操作者应保持输入目录稳定；此检查不隔离同用户进程。输入包摘要包括任务、组合、提示和所有资产；它证明内容一致性，不认证作者或授予执行权限。跨平台执行位及同平台保持字节的限制与定义包相同。

输入元数据使用 [composition-input v1](../../../../src/ergora/data/schemas/composition-input-v1.json)，包内保留所引用 Agent v1 及 Workflow v1/v2 的原格式。实际调用按下面的独立入口重新准入。

## 调用一个准备好的叶子

先[注册项目](../../projects/registration.md)，并安装、认证所选的[Agent CLI](../../agents/configuration.md#安装与认证-agent-cli)。`prepared-review`沿用上面准备的完整输入包：

```bash
ergora composition run-input my-project ./prepared-review --timeout 300
ergora composition run-input my-project ./prepared-review --backend codex --backend-reason "Selected Codex for this call" --codex-config /PATH/TO/codex.toml --timeout 300
ergora composition run-input my-project ./prepared-review --backend claude-code --timeout 300
ergora agent runs my-project
ergora agent output my-project RUN_ID
```

默认采用叶子精确定义的后端；`--backend`和`--model`仅覆盖本次调用。跨后端时重新选择model，不沿用另一后端的model名。执行/审查应尽量选择不同后端；Claude不可用时可显式选Codex/ChatGPT，并用`--backend-reason`记录原因。不会在失败后暗中重试另一后端。超时为1–3600秒；成功返回0，模型失败/超时/启动配置或结构错误返回1，输入包或模式准入错误返回2。

也可在叶子精确定义中配置[DeepSeek Harness只读后端](../../agents/deepseek-harness.md#deepseek-harness-只读叶后端)，保留完整解释器、模型、API服务与凭据变量引用；调用时不使用不完整的`--backend`覆盖。支持本节两种只读模式。该后端不支持原生workspace执行、正式任务恢复或持久会话。项目持久会话使用[当前Codex会话合同](../../../agents/deepseek-harness.md#project-native-development-sessions)。

默认模式为 `text-only`。完整祖先指令、上下文、Skill的`SKILL.md`和原任务进入模型；Skill附件仍保存在快照中，但本模式没有文件/命令/网页/MCP工具，不能按路径读取其他资料或编辑项目。提供审查任务时应把候选代码及必要证据放入任务正文。请求write、shell或工具network权限的叶子会在调用前拒绝；例如示例执行叶子不能通过本模式运行。原生结构化响应工具或交互工具可能保留。

运行使用新空cwd、原生CLI的规则/工具关闭选项和独立会话。它们约束模型可使用的工具，不提供OS/网络隔离；用户进程及模型服务本身的通信不受此模式隔离。后端不支持所需选项时明确失败。Codex可通过`--codex-config`显式提供推理配置：只消费model/provider/推理强度/service tier及provider的URL、凭据环境变量引用等字段；其中的工具、MCP、Skill、审批和sandbox设置不会覆盖此模式。使用Codex原生登录时可省略该文件；Claude使用原生认证或对应环境变量。不要把密钥写进定义或任务正文。

每次运行在State的`runs/`下保存经过完整核验的输入副本、新空工作目录、完整prompt、实际argv、stdout/stderr和结构化结果，复用原Agent运行列表/输出及完整备份。记录绑定输入摘要、项目修订、请求/实际binding和覆盖原因。运行列表只带资源身份及来源，完整正文可对返回的`input_path`使用`composition verify-input --material`按需核读。读取返回的`result`文件可查看`summary`、`artifacts.response`；审查者另有`approve/request-changes`。进程成功和审查approve分别判断。

单叶调用的任务由操作者提供，图前驱和端口没有执行；原输入仍为`execution_authorized: false`，本次调用也不创建正式候选/批准。正式串行/并行调度及候选、批准使用上文的[正式审查](contracts.md#正式只读审查的数据端口)和[工作单元](contracts.md#专长执行者与原工作单元)入口。

## 按精确 ID 读取原组合运行

`agent runs`只列最近100条；`agent output`提供有界stdout／stderr。需要原组合run的完整输入和结构化结果时，使用其精确ID：

```bash
ergora composition inspect-run my-project RUN_ID > ./original-run.json
ergora --home /path/to/control-directory composition inspect-run my-project RUN_ID \
  --max-result-bytes 16777216 > ./original-run.json
```

这会按项目和ID读取原记录，以及当前控制目录中原`runs/`槽位的完整input、调用prompt和结果，不要求源仓库、后端程序、认证或网络。复制完整控制目录后，历史metadata的绝对路径保持原样，读取使用新控制目录下的原槽位；不能只复制数据库而丢弃run文件。旧的普通`agent run`仍用`agent output`，这个完整读取入口面向`composition run-input`等原组合运行。

返回`run`保留原状态与实际后端／原因；`input.available`核完整输入及其原digest／request／prompt身份，`prompt.available`独立核原调用prompt与原记录的SHA和字节数。输入也可核时，再逐字比较冻结prompt，标记`prompt.input_compared: true`；输入不可核时该标记为false，不妨碍保留仍与原记录匹配的调用prompt身份。`result.available`核完整原result SHA并读取其JSON，正文在`result.document`中，不截成stdout预览。默认结果容量8,388,608B，超限明确返回不可核，可提高正整数容量后再读；原保存内容不变。

每项缺失、身份不符或超限都会在对应`error`中说明，仍可核的其它资料和原run状态继续显示。命令成功读回观察时返回0；脚本必须检查各项`available`和`run.status`，不能只用exit0判断审查完成。这个读取不重新跑当前后端／schema准入，也不把历史结果升格为正式批准；后继报告按可信reviewer合同解释建议。

原调用prompt来自各后端共同保存的`protocol/prompt.txt`。实际传输可能经stdin或后端request文件，不能由这份观察宣称所有后端的stdin交付已认证。原native历史仍按[后端手册](../../agents/backends.md)读取。失败或unknown先保留并对账，不自动重发模型调用。

## 调用前查看能力与权限

在实际调用前，可以先检查同一输入、后端及模式：

```bash
ergora composition check-input my-project ./prepared-review
ergora composition check-input my-project ./prepared-review --mode task-mcp --backend codex
ergora composition check-input my-project ./prepared-review --mode task-mcp --backend codex --codex-config /PATH/TO/codex.toml
ergora composition check-input my-project ./prepared-review --mode task-mcp --backend claude-code --backend-reason "Independent review backend"
```

该命令和`run-input`共用当前准入。结果的`policy.permission_ceilings`按所供grant、root到leaf列出整条结构权限链，`requested_permissions`是叶子请求，`context.resources`保留全部祖先/自身资源来源。read路径是许可上限；列出workspace不会自动提供项目文件工具。完整内联材料和固定附件的支持分别展示，text-only不会声称附件可读。

`policy.capabilities`把支持范围分为`enforced`（可信CLI/任务URI服务实现的机制）、`advisory`（请求/提示，未提供强制保证）及`unsupported`（没有对应能力）。Codex实际传read-only请求，但不因此宣称宿主隔离；Claude关闭native工具，没有额外请求OS sandbox。任务MCP只提供固定声明资料的list/read；实时workspace、写、shell、工具network origin及外部MCP继续不支持。基础设施推理HTTP、stdio进程、日志/状态写入仍存在。

这是实现合同和本次准入报告，不启动server/模型、不创建运行，也不检查CLI版本或认证。使用Codex的`--codex-config`时，检查和运行共用推理字段解析；文件不可读、无效TOML、不合法provider表或不能编码的字段在建立运行前拒绝。它不验证提供商是否接受配置、模型是否可用或容量是否足够；Claude忽略该Codex专用选项。task-mcp只检查Linux及SDK顶层存在，真正SDK兼容/连接在运行时预检。检查成功不等于正式批准，`formal_execution_authorized`仍为false。实际运行重新执行准入并保存同结构`policy`，不会把先前检查结果当成授权票据。

## 通过任务 MCP 读取固定附件

在Linux/WSL2中，用运行Ergora的同一个Python环境安装可选依赖。仓库根下执行：

```bash
python -m pip install '.[task-mcp]'
ergora composition run-input my-project ./prepared-review --mode task-mcp --backend codex --codex-config /PATH/TO/codex.toml --timeout 300
ergora composition run-input my-project ./prepared-review --mode task-mcp --backend claude-code --timeout 300
```

此模式保持完整祖先指令、上下文和Skill说明的内联交付，另向模型提供`ergora_task`服务的`list`、`read`工具。先`list`查看虚拟URI，再`read`读取本叶子全部结构祖先及自身声明的资料和Skill附件。普通正文仅开放声明的文件；Skill开放其固定完整目录。它不开放兄弟模板、未声明的同目录文件、整个输入资产库或项目实时文件。资料不作为可执行程序运行；写、shell及工具network请求继续在调用前拒绝。

每次调用生成独立的[task-mcp-scope v1](../../../../src/ergora/data/schemas/task-mcp-scope-v1.json)，保存原始字节、摘要及来源，最多10MB/500文件，完整序列化scope最多16MB；超限拒绝。服务核验scope后只查询内存，不把模型提供的URI当作宿主路径。Linux的固定资源读取逐级使用不跟随链接的文件描述符，拒绝symlink/hardlink/特殊文件；当前Windows新模式会给出Linux/WSL2指引，既有Windows功能继续可用。

`list(path="",offset=0,max_entries=100)`按授权URI分页，每页条目元数据最多约64KiB；`read(path,offset=0,max_bytes=65536)`按字节分页。返回文件大小、SHA256和`next_offset`；可解码块为UTF-8，二进制或跨编码边界为明确base64。继续请求`next_offset`可取得完整内容，不以一次工具响应代表整个目录或文件。

### 核验完整附件读取

若任务要求完整检查每层资料，在任务文件中明确要求：分页列出全部 URI，再逐个从 offset 0 读到 `next_offset:null`，包括所有祖先 instructions/context、每个 Skill 的 `SKILL.md` 和全部引用附件。UTF-8 文本若因窗口切开多字节字符而返回 base64，可在同一 offset 缩小 `max_bytes` 后重读，再按成功文本页推进；真正的二进制附件按完整 base64 字节处理，不运行。空目录保存在完整包中，不会成为可读文件；普通未声明附件也不会自动进入任务 scope。

运行成功及最终 `approve` 都不证明附件读全。核验时比对冻结输入、`task_mcp.scope` 的 URI/大小/SHA/来源，以及本次原生事件里的实际 list/read 回复；各文件的成功页应连续覆盖原字节，保留失败或重复窗口。scope 保存的是可用材料，原生读取记录才说明本次模型实际请求过哪些字节。准备好的输入可在源库移走后使用；应先核验并保留源库及完整输入，避免误删唯一副本。

MCP配置只在本次调用生成。Codex只选择该server的两工具，native MCP资源发现/响应或交互入口可能保留；服务不注册额外resources/templates/prompts。Claude使用`--bare --restricted`、空native工具及strict显式MCP；bare模式只使用其支持的API环境认证，不读取常规OAuth/keychain。需要OAuth登录的用户可继续使用text-only，或为该模式设置后端支持的API环境变量；无需把密钥放入定义、scope或聊天。不同后端不会自动共享模型名或认证。

运行记录的`task_mcp`包含固定scope身份、预检结果和本次native连接回执。预检与native回执分开；后者必须是该scope的实际SDK成功`tools/list`且工具恰为list/read。旧握手及新版无握手请求分别记录实际协议和`handshake_observed`；没有真实服务回执时，即使最终模型JSON成功也登记失败。scope与回执跟随State完整备份，运行列表继续只显示摘要；这不提供OS隔离，也不扩张模板或项目授权。

运行还检查本次原生后端已经报告的任务MCP传输错误：即使模型随后重连并返回合格结果，该次运行仍记为failed，保留原始stdout。未知资源或非法URI等服务端领域拒绝允许模型纠正后继续；它们不等于连接失效。Claude在此模式保存stream-json原始事件并提取最终结构结果，普通native/text-only输出处理保持。此检查不提供持续heartbeat，不能检测没有后续调用且无原生错误事件的静默失联。
