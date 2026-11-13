# U3 日常安装升级独立评审

日期：2026-11-14。评审者为 fresh-context 独立代理 `daily_installation_review`；未继承实现会话。遵循 `AGENTS.md` 与 `maintainable-project-delivery` 独立评审要求。下文先保留安装前预审，再记录同片实际原件终核；**最终需求／可维护性均通过本片本地出口，开放 finding 为 0／0**。文档普通发布尚待实现者记账。

## 范围与身份

原要求是在完整备份后，将已验收的同一 wheel 离线重装到原 home 应用 venv，保留原依赖、非应用文件与 symlink、启动器、认证及已知默认状态；随后用实际默认启动器在独立持久 `--home` 检查代表模板的完整祖先材料、manifest、单叶 input、Codex 准入和必要 HTTP 读取，并清理自己启动的 server／port。不重跑既有成功模型调用、GPU 或完整业务旅程，不把工具权限声明当 OS 隔离，不声称已实测恢复。

检查时源码为 `41dd5aa30f589b5c27a1cc3f09db59d66005a40f`，父提交为 `d683c018344fb604be115a3ed2a02bd9d50d4eff`；日常安装仍为原 452 产品／3 preset／38 distributions，Python 3.12.3。工作树同时存在其他片的文档记账，本评审仅覆盖 U3 指定五文件和必要调用链。

初始五文件完整快照的 manifest SHA256 为 `c57b3226d904ba3f93e52671521bc4c59f34d786e19333821646efca09331cbb`。已逐一核对快照和当时现行文件，全部符合该 manifest：

|文件|SHA256|
|---|---|
|[U3 计划](../plans/2026-11-14-daily-installation-refresh.md)|`89f1ae09b674fefc43d079c4a1b4ddf1fc27254055283a2992e83258fe221150`|
|[U3 交付记录](2026-11-14-daily-installation-refresh.md)|`bde0c76216c78b118a3ec9a2721b803197161545d54ddd16c69b2301dd2991fb`|
|私有 `preflight-backup.py`|`23ff3505fe373469d0cdd46929a8ad962f76448811a8b1b96b94a8116d2c9479`|
|私有 `install.py`|`79edb5c10f2f041fa665977b03295304577bab7b9203df03272eaee14c0f26ac`|
|私有 `accept-daily.py`|`15607b11c20184e2774fab3e0cdfc97e938c92508c10bae62b77a4a521e7b215`|

必要源码包括原安装布局、CLI `composition`／`serve` 分派、`workflow_definitions` 的 preset／manifest／input 所有者、`agent_runs.check_input`、Codex 准入适配器、`state.resolve_home` 和 HTTP GET 入口。未修改产品、安装器或冻结参考。

## 安装前结论

**需求符合性：预审范围内未发现问题，整体验收待完成。** 计划把 B2i 普通发布、精确候选自己的 CI 与原独立终核作为替换前的硬门槛；私有安装脚本在读取并核对发布 gate、证据摘要、原备份和当前原安装身份后，才执行 `uv pip install --offline --no-deps --reinstall-package ergora --no-compile`。检查时没有 gate、安装回执或日常验收旅程，因此没有提前替换或提前完成的证据。

**可维护性：指定五文件与必要调用链内未发现问题。** 三脚本是本机一次性私有验收驱动，复用既有安装布局、CLI、compiler、快照校验、Codex 准入与 HTTP 接口；没有新增产品抽象、调度器、账本、测试框架或正式执行路径。守卫分别保护发布依赖、原安装一致性、离线范围、包内容与 RECORD、依赖保持及所属 server 生命周期，符合本片边界。

静态调用链确认：无 `--home` 的 preset 列表不构造 `State`；其余烟测命令显式指定独立持久状态。`check-input` 只进行配置、权限和当前能力准入，不进入模型执行或创建 run 记录；认证可用性仍未被模型请求验证。HTTP 验收只读；`finally` 针对自己的 server 执行 terminate／wait，必要时 kill／wait，并检查端口关闭。

## 已独立核对的证据

- 三个脚本通过 AST 解析；仅解析，没有执行脚本或 suite。
- 原前像为 452 产品／3 preset／38 distributions；限定一次 `/proc` argv 观察记录为 0，默认业务状态不存在。此结果不扩大为全系统、无竞态或脱离后代的隔离保证。
- 直接读取完整备份归档，独立核得 38,626,813 字节、SHA256 `a22ee071849df6995ec59f6733dd2a6ac4f77057757d0c2d771fdfedf3a2e735`、6,190 成员；5,051 普通文件及 symlink 的身份逐项等于当时原 venv，启动器解析与链接保持，默认状态仍不存在。没有提取或恢复归档。
- 直接读取候选 wheel，独立核得 SHA256 `34e6b375c8771fa67bb1b02a71070f289ec72d5b0c99badac3afd28373fee208`、559 文件／559 RECORD 行、551 产品与精确候选 Git 归档逐字相等，全部非空 RECORD 摘要和 283 冻结参考摘要正确。此项尚不是原日常 Python 3.12 环境的安装后验证。
- 从原产品 `5ab6d350024de8515487d0bedb3b950be60ac867` 到候选的 `pyproject.toml` 差异仅许可元数据，没有依赖声明变化。原依赖检查私有回执记录 exit 0；尚未独立运行依赖检查或采用其结果关闭安装后要求。

原件身份、机器路径和检查审计留在本片私有材料；本报告不包含凭据或 inference 配置内容。

## 预审时开放验收

以下是尚未完成的验收证据，不是已发现的产品缺陷：

1. B2i 自己的 CI 终态及其原独立终核，随后绑定精确候选和原证据摘要的 release gate；门槛满足前保持原应用。
2. 实际离线重装原件：安装命令、551 产品／两个 RECORD／283 冻结身份、38 distributions 和其余非应用文件／symlink、启动器及已知默认状态的前后保持。
3. 真实默认启动器的 23 preset 列表，以及八个代表根的完整祖先／资源／manifest、选定单叶 input 和不授权执行的 Codex 准入原件；其余代表边界以实际产物核准，不借旧模型旅程代替。
4. 必要 HTTP 原 body 与摘要、所属 server 退出及 port 关闭证据；确认没有模型 run、默认业务状态污染或额外业务执行。
5. 更新后的公开计划／交付记录与最终私有脚本身份，由本评审者在本片补核。最终公开文档的普通推送及精确发布状态由实现者另行记账。

预审没有阻止按上述门槛继续的 finding；U3 不得据此标记完成。实际安装、CLI、HTTP 与清理原件到齐后，再给本片最终需求与可维护性结论。

## 实际安装、日常旅程与自身模板终核

同一评审者获同片后续授权，只读检查已生成的实际原件。产品候选仍为 `41dd5aa30f589b5c27a1cc3f09db59d66005a40f`；原三脚本逐字保持初始快照。新增私有投影脚本 SHA256 为 `8ef04a078053e5afb65bd3f379bd20dc229c02b4fab461547eff824bb1919e23`，自身模板驱动为 `f69b472d3e8cc0f303e80b07903f056d956b7f5816bc890e619034f62baf0695`；已完整静态读取并解析。它们仍是本机私有驱动，没有进入产品或增加正式接口。最终检查包含更新后的本片计划／交付、公开投影、原 gate／安装／命令／HTTP／清理原件及自身结构审查输入与结果；训练手册只作为该模型调用的完整输入身份检查，B3a 的需求评审归其所属片。

**需求符合性：通过 U3 日常安装与验证的本地出口。可维护性：通过。需求／可维护性开放 finding 为 0／0。** 预审的发布门槛、实际安装、CLI／HTTP 和清理待做项由以下原件补核关闭；没有要求重跑原成功方向模型、suite、GPU 或业务旅程。新增自身模板调用是另一份输入与状态，独立分账。

- **安装前置。** release gate 的五份证据摘要全部重算相符，绑定精确候选、B2i 普通发布、自己的 CI `43459951488` 及原独立终核。已读原独立报告、8 job／30 必要步骤的最终审计和 crosscheck；三者时序及不变安装脚本的 gate-before-reinstall 路径相符。gate SHA256 为 `d13c6047f857d4a271552c42eee6338ad4ae386e06f4da6002f8b8f893ace323`。这是原独立 CI 结果的门槛绑定检查，没有另行联网或重做 CI。
- **原环境实际升级。** 五个原安装操作均 exit 0，重装实际 argv 仅选择 `ergora`，具有 offline／no-deps／no-compile 和原 Python 参数；基础及四选配的七项 requirements 满足，前后依赖原 stderr 均明确 38 包兼容。直接读取当前 venv，核准 551 产品等于已绑定候选的同一 wheel、安装 RECORD 的 564 行全部非空摘要正确；结合已核 wheel RECORD 和产品逐字身份，283 冻结保持。38 distributions 的版本逐项等于前像；4,550 非应用文件／symlink 逐项等于完整归档前像，原 launcher symlink／目标及 shebang 保持，默认业务状态仍不存在。安装回执 SHA256 为 `ed1b63242ca301329a1b4f3923e18d2b9937528f4d80fbd500e6f54e34a49fbd`。没有恢复归档、重新安装或执行依赖检查来制造新的结果。
- **真实入口与完整材料。** 独立检查全部 65 条原命令、exit 和原输出；首条是无 `--home` 的真实默认 launcher 列表，其余应用命令显式指向独立持久 state，另有三条仅作用于本地 fixture 的 Git 命令。23 项 catalog 与安装包一致。八个代表根的 16 份 manifest／input 完整树摘要、引用集合和全部资产逐项匹配实际安装定义；38 个叶节点的 175 份资源共 213,338 字节，其全部结构祖先／自身来源、原正文和完整 prompt 均核准。八个选定单叶的 task／prompt／input 摘要及 Codex task-MCP 准入逐项相符，均不授予正式执行权限。
- **HTTP 与所属资源。** 10 个原 GET 均为 200，原 body 共 620,206 字节，逐份核 bytes／SHA256 与 server 访问日志。页面 23 项与 CLI 相等，bootstrap 绑定独立 state；首页及四静态资源与实际安装字节相等。原旅程最后的 runs 输出和只读 SQLite `agent_runs` 均为 0，仅证明这份 65 命令状态未运行模型。原摘要的 72 检查全部通过，SHA256 为 `8680973ba82b75d56dda4728dbb68ec1dc73976d1ebde130547d1974372b3389`。同一 console 的启动／完成 PID、完整 shutdown 日志、原 finally 的 wait／port 检查和作者后观察相符；本评审另行只读 `/proc`／TCP 表确认该 PID 不存在、该端口没有 LISTEN，不发起连接。controller exit 0 是作者保存的原工具完成转录，未将它冒称为独立原生执行 trace；后观察不扩大为全程后代或 OS 隔离证明。
- **自身模板的新输入补验。** 原 `ergora-structure-review` 的独立 text-only 调用 `b3877e22073340d3b3887030cbf99123` 为 succeeded／exit 0／approve，记录耗时 41.303 秒。五份完整文件共 54,066 字节均与 packet index、当前原文件和实际 task／stdin 逐字对应；三份原祖先／自身资源与已安装定义相等，原 input 与保存 input 的完整树均为 `d09257dedbc490298853dd917ea3773e8949da6d267cb0baa1e523e6f2ba832a`。prompt／stdin SHA256 为 `a54923348d4d2df696505ffe3a0686185903bf60d65a5419f49327f9391229a9`，最终 native JSON、原 result、保存 result 与独立 state 的唯一 run 一致，结果 SHA256 为 `d66062a1905ce5f3031c63ef99a3f8a0a90c5b220c366cef69d0679005113f43`。已全文读原 response：只作所供手册／四脚本的文本结构判断，没有实证 finding，不证明 MCP、异后端、安装、CI 或 GPU 验收。实际启动路径由作者原工具 argv 转录绑定原 venv Python；3.12.3 来自原 preflight 和保持的安装身份，未伪造本次运行内的 `sys.version` 字段或独立 OS exec trace。此状态含一次模型 run，与原旅程状态的 0 分开。
- **公开投影与记录。** [6,832 字节公开投影](evidence/2026-11-14-daily-installation-refresh.json)的 SHA256 仍为 `f777e48385ed3cdf79f4bc5dd60f78581acc11649e604252121b4f84ab4e6d51`；全部字段与八项原件 SHA 映射独立核准。其 no-model scope 仍仅指原安装／65 命令／HTTP 阶段，不包含后来的自身模板调用。计划和交付已区分升级前记录与当前状态，两份状态也明确分账。

私有独立审计分别保存安装后逐项对比、日常旅程、原自身模板链和最终文件身份。评审只执行标准库的读取／摘要重算及私有审计写入，没有执行产品 CLI、模型、网络、安装、suite 或恢复，也未读取／输出 inference 配置内容或凭据。

没有新增或遗留实证 finding。完整 venv 备份与内容核验不等于恢复演练；已知默认 state 不存在不等于全 home 扫描；文本审查与工具声明不等于狭窄权限 OS 隔离。完整六阶段、原生 GPU／实验、业务状态迁移／恢复及 C2 全部会话／权限／总预算／后代停止继续保留其原未验范围。文档普通提交／推送和精确发布回执尚待实现者执行及记录，不由本报告提前关闭。
