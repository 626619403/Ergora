# AC3b.2a：可核验的完整调用输入包

日期：2026-11-09。状态：IN1–2初版源码/发行验证通过；新独立初审提出4项，r2修正后源码/发行检查通过，新独立两轴复审通过，精确交付待验。基线 `4f102da873fc19c8a805031106d7a7c4524d5908`，分支 `refactor/architecture-foundations`；前片本地门禁已通过，其精确交付单独收口。

## 本片合同

用户要求叶子完整读取所有祖先Skill/上下文，资料可长期保存且不随活动版本改变。把AC3b.2拆为2a输入快照、2b真实调用：先核完整材料/版本/容量和可恢复输入，再在最小后端能力准入到位后启用调用，避免先执行再补装载约束。正式批准/嵌套调度继续归AC3c/4，不用独立输入包替代。

- `composition prepare ID VERSION INSTANCE --grant FILE --task FILE --directory NEW --max-prompt-bytes N`，明确选择一个Agent叶子；保存完整原始任务字节、完整静态组合、完整叶子user prompt以及全部精确引用包。单叶任务由操作者提供，原端口/前驱未被执行，不冒充正式候选或自动数据流。
- 使用独立版本化`composition-input-v1.json`，不向旧Agent/Workflow v1增加隐式字段。输出`execution_authorized: false`；不调用模型、不创建/迁移State或修改源库。
- 全部引用包复用现有不可变版本库和当前准入复制到包内`assets/`，保留整个Skill树、内容/执行位、祖先来源和重复实例身份。核验时按保存的v1静态合同重编译；当前catalog删除不阻止历史核验，实际运行仍待新准入。
- 完整包用于操作者离线核验整树；选定叶子prompt只含其自身/祖先。后续adapter只投影该叶子获准资源，不能把完整assets目录当作叶子授权。
- `composition verify-input DIRECTORY [--material]`重新核树/资源/引用、完整组合和选定叶子prompt/任务/字节预算；不信任自报摘要。新准备仍核当前Agent准入；读取不授予执行能力。
- user prompt完整保存，不截断。显式字节上限为1–1,000,000，计完整静态材料和操作者任务；不是模型token容量或后端系统提示的承诺。包沿已有树检查的10MB/500文件，另限1000目录/48层；超限/内容变化/复制失败不发布半包。
- 只向新目录原子发布；源State删去后包仍可核验，复制在同平台保持身份。POSIX/Windows执行位差异沿原合同；不能宣称跨平台身份保真。

所有者：在`workflow_definitions`内增加静态叶子输入准备/核验，复用其有界编译和两库工厂；这仍是静态数据装配，不引入新运行器或插件框架。后续`agent_runs`消费完整已核输入，后端能力由原adapter拥有。新schema归contracts，CLI只转发。

## 验收节点

- [x] IN1：输入格式、准备/核验和有界复制，内容身份及完整prompt检查。
- [x] IN2：实际CLI及有价值拒绝/历史恢复合同、非editable包和冻结身份。
- [x] IN3：fresh-context独立审查/处置及手册/计划。
- [ ] IN4：精确普通提交/推送、必要双OS CI及同片远端收口。

## 先行原生配置探针（不计实现）

已阅读[Codex配置](https://learn.chatgpt.com/docs/config-file/config-reference)、[MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)和[Skill](https://learn.chatgpt.com/docs/build-skills)官方文档，并查看已装CLI帮助。安装版Codex0.166.0与Claude Code2.1.312分别对本地合成Responses SSE/Messages服务成功交付显式文本，不用真实密钥、不调用托管模型。Codex关闭shell/goals/hooks/apps/plugins/网页/自动Skill后仍暴露request_user_input，但不暴露命令或文件工具；Claude restricted/safe-mode/空tools及strict空MCP的请求tools为空。证据在忽略的`ac3b2-resources`检查目录，保留初版与修正配置。

这仅证明该版本在该受控配置下的原生请求，不是认证、模型质量、OS/网络隔离、ambient MCP全面隔离或生产适配已完成。AC3b.2b/3/4仍须任务资源加载、MCP允许/拒绝和真实能力矩阵的证据；Claude不可用可按用户授权回退Codex/ChatGPT，不绕过审批。

## IN1实现与本地源码证据

现有`workflow_definitions`新增prepare_input/inspect_input及共有字段构造，复用原私有有界编译和两DefinitionLibrary；先Agent、再子→父复制，逐包核引用摘要及整个输出限制，全部验证后才发布新目录。输入核验重新生成整图、完整材料/user prompt，验证声明摘要而不信任自报内容；不走当前后端准入。源库/State不写，目标不允许位于不可变定义库内部。仅新输入schema及CLI转发，无新调度器、DB、依赖、后端实现或CI作业。

Workflow源码65 passed；随后四套相关源码159 passed/2原生Windows junction skipped（Python3.11.15），一条既有FastAPI/httpx警告。新增19个行为案例覆盖真实CLI、祖先Skill完整树、中文UTF-8/BOM/CRLF、精确容量及少一字节拒绝、源库删除/后端收紧后离线核验、伪造prompt摘要/任务/组合/资产/额外文件拒绝、类型/路径/目录拒绝、复制中断及三个单包合格但聚合超10MB时不发布。原始日志在忽略的`.ergora/checks/ac3b2-inputs/{source-tests,related-source-tests}.log`，未把Linux通过外推为Windows。

示例真实预备smoke展开原10实例，结构审查叶子完整user prompt为4,797字节（当次英文task），原源库未变；独立审查/最终发行还待完成。上面的原生合成协议探针与这里的静态准备分别记账，尚未用本片代码调用实际后端。

## IN2发行与独立初审处置

初版Python3.12.3非editable包同四套159 passed/2原生Windows跳过；360份源/wheel/安装逐字与283冻结身份通过。6次真实CLI覆盖准备、完整读取、不足容量/已有目标/篡改拒绝、源State移开后的独立核验，未创建新State或Agent运行。初版包、身份及旅程保留为r1，不用于后续修正版的身份声明。

[新独立两轴初审](2026-11-09-composition-inputs-review.md)Standards无finding；Spec指出IN-SP1/2两个P2、IN-SP3一个P3，协调者另指出IN-R1 P2。四项均接受：

- 发布改用Linux `renameat2(RENAME_NOREPLACE)`／Windows原生不覆盖rename，竞争出现空目录时保留原目录并失败。没有原语的Linux系统或其他平台明确失败，不降级成覆盖式发布。
- 完整组合及request以规范化JSON比较，保留布尔、整数、浮点类型差异；空白与字段次序仍不改变语义。
- 私有暂存库每次复制后删除不再使用的锁，再核聚合限制；500份最终文件可用，501份仍拒绝。
- 核验前后完整inventory必须一致，覆盖索引字节、额外文件、目录及执行位变化。输入仍须由操作者保持稳定；双遍检查不是对同用户恶意反复替换目录的原子快照、作者认证或OS隔离。

修正后Python3.11.15源码与Python3.12.3非editable包同四套各166 passed/2原生Windows跳过，原FastAPI/httpx警告保留。新增7例覆盖三种弱等值变化、核验中索引修改、发布前竞争目录以及500/501边界。360源/wheel/安装文件与283冻结身份一致；r2 wheel SHA256为 `22ec691788490be970eab0faf97aeccc41d3f30da486c4d278e5944fdde06f16`。测试参数随后仅简化为相同数据，针对该3例再核，不重复无变化生产代码的整套检查。

本轮最初两次测试命令分别因误用未安装包的系统Python、备份suite文件名拼错而未收集测试；原日志 `r2-source-tests.log`、`r2-related-source-tests.log`保留排除。有效检查为 `r2-corrected-source-tests.log`／`r2-wheel-tests.log`，不把前两次当通过。尚待同片复审、精确普通提交及自身双OS CI；真实后端仍属AC3b.2b。

IN3完成：[同片两轴r2复审](2026-11-09-composition-inputs-review.md)通过，四项原发现关闭，无新增finding。独立重核360/283身份、7个新增回归和平台/一致性探针；另在r2安装包独立执行3次真实CLI（prepare/verify/重复prepare，0/0/2），中文路径及BOM/CRLF字节保持。原生Windows及本片精确CI仍待验，不把分支模拟计作原生通过。下一IN4普通精确交付，随后按AC3b.2b调用切片推进。
