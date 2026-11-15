# b2b0：训练循环离线读取独立审查

日期：2026-11-15。审查者：fresh-context独立Agent `training_cycle_offline_reader_product_audit`。未继承实现对话；依据原始要求、实际源码、调用者和原始验收证据审查。权限限于只读检查及本报告写入，未修改产品／测试、安装、提交、联网写入或重跑昂贵suite。

|审查轴|最终本地结论|开放问题|
|---|---|---|
|需求符合性|approve：满足本片行为保持的原读取参数整理|0|
|可维护性|approve：依赖归属、真实调用迁移与验证范围适当|0|

结论仅覆盖以下候选和本地验收；不表示普通发布、前置CI或本片自己的CI已经闭合。

基线为`d1c728087423d85ed55f06010ec81e5e1d4b2fd1`，分支`refactor/architecture-foundations`。先审查`review-scope-r1.json`、对应冻结文件和`review-tracked-r1.diff`，终核更新后的`final-scope-r1.json`、`final-scope-r1/`与`final-tracked-r1.diff`。证据根目录为项目内私有`.ergora/checks/training-cycle-offline-reader/`。

最终八文件为：`docs/PLAN.md`、`docs/architecture/current.md`、`docs/plans/2026-11-15-training-cycle-stop-supervision.md`、[本片计划](../plans/2026-11-15-training-cycle-offline-reader.md)、[本片交付](2026-11-15-training-cycle-offline-reader.md)、`src/ergora/training_cycles.py`、`src/ergora/reference_training_budget.py`及`src/ergora/reference_training_worker.py`。已逐字核对当前文件、冻结副本及清单SHA；最终tracked diff也与当前Git差异逐字一致。`final-scope-r1.json`为1,322B／SHA256 `b1061e68f5a2a7318888aa07f338f8fab61a5a66bade45cdd913d0e3351a0a75`；`final-tracked-r1.diff`为24,236B／SHA256 `a1ee9a98fe02a976713b340d6f1cee00a52c08bdd1354057c3e00394d1f47a16`。本报告是审查新增记录，不在该八文件实现清单内。

已读取根、源码及测试`AGENTS.md`、[组件变更协议](../architecture/component-change-protocols.md)、maintainable-project-delivery独立审查指引，以及ergora-codebase-quality的风格／模块／测试接缝参考。适用范围还包括[停止监管设计](../plans/2026-11-15-training-cycle-stop-supervision.md)、`state`、`registrations`、`training_execution_protocol`、v3／kernel定义和所选原测试／fixture。

需求核对结果：

- `training_cycles.py:182–262`原五私有函数只把`State.root`依赖表达为`home: Path`。独立从Git基线AST施加这五个参数及对应调用的预期机械变换后，三个完整模块均与当前AST相同；共核17／4／2处调用。公共API、原`State`构造／生命周期以及其余模块算法保持。
- `reference_training_budget.py:259`的`source`仍构造原`State`、加载完整记录、核binding／来源并返回原四元组；`permission`和固定父history仍经原owner。`reference_training_worker.py:27`仍在原native adapter／registry路径执行完整核对。没有遗漏其他生产调用者，也没有在本片把这些既有应用路径改成新的只读入口。
- `state.py:156`的构造确实解析home、创建目录、取得schema锁、打开数据库并可能迁移。原记录算法的下游`registrations.published_project`只读原journal／result；`_load`的schema2 ready路径调用`CycleAdmission.validate_lock()`时保持默认`synchronize=False`，只核现存普通空锁。五函数现在可由后继H直接复用，无须构造State、伪造State或复制校验器。
- 原读取容量、严格JSON、完整canonical／raw SHA、registration来源、ready身份／时间、原clock、锁及异常路径均未改。没有新增函数／类／产品文件、wrapper、registry、schema或分派；没有异步operation、fan-out、总Workflow或公开自动执行入口。v3仍通过`kernel`节点引用原kernel assessment／kernel专家；相关资源逐字保持。

可维护性核对结果：实际依赖仍由原`training_cycles`拥有，另外两个生产文件只传原`state.root`。无需新reader层或可替换接口；没有新增guard、assert、fallback、重复校验或tracked测试／CI。保留原测试接缝并用安装实际调用和原件读取共同验证，比为五个参数各加浅层测试更能覆盖本片风险。未发现需修正的产品或结构问题。

实际核验与证据边界：

- 独立重核652个产品文件：当前source、wheel、core site-packages及SDK site-packages逐字一致；原manifest SHA／大小一致。与完整Git基线相比仅原三owner变化，没有增删产品。wheel SHA256为`e0b0364c3d88bc4ded4e38339a4d5bf24567b51aa48003dd5b00641f32505f6e`。两份原reference检查均为283／PASS，依赖检查退出0；core无Temporal SDK、SDK环境为1.34.0。这些证明安装身份与完整性，不代表运行过全部产品能力。
- 177份测试／示例的当前源码、原Git基线、冻结副本及清单独立重核相同。原新SDK安装回归`installed-r1.*`终态27通过／57.10秒，驱动58.688秒；JUnit为27／失败0／错误0／跳过0，stdout与退出0一致。包括11个展开的授权／完整binding／来源／恢复／可见stop／排空／真实registry gate场景及完整16项架构。已读所选原测试及实际子进程fixture；未重跑该suite。
- 原core离线证据`offline-originals-r1.py/json`确实持有真实schema排他锁并禁止State构造。审查者另用实际core安装重复只读加载两份原schema1／2，额外禁止`State._open`和`sqlite3.connect`；原文件SHA清单、完整字节及目录集合均保持，不存在的home仍不存在。原故意`confirmation=1`损坏授权与`offline-originals-r0-corrupted.*`身份一致，独立重读仍按完整canonical SHA拒绝，未修复或换写原件。此项证明原读取可脱离数据库初始化，不授予重新授权、执行或停止成功。
- 自身原结构模板的`self-review-r1.json`及原result SHA一致，20.475秒／approve；独立核16份完整文件共427,107B确实存在于原prompt，且prompt与真实stdin逐字相同。原运行记录还核三个祖先资源；该回复明确只覆盖供稿，回归当时在途，不将其当作本次终态审查或异后端成功。
- `owner-closure-r1.json`记录本次1个原budget owner活匹配0、验收路径进程0；审查者另核该原owner完整进程身份已不活跃。没有发送信号或全机器无进程主张。最终`git diff --check`及变更文档本地链接目标检查通过。

审查中指出初稿交付仍写“当前只有计划与原码调查”，与后文实现状态冲突；作者已改为立项调查及下文逐步记录，并以最终scope重新供审。该记录问题已关闭，没有开放最低修正项。

本地片可以按原计划收束。普通发布仍受前置43d自己的准确CI终态及原独立门禁约束，本片发布后还需自己的适用CI；本报告未联网终核它们，也不转授前片批准。后继b2b1／b2b2仍须独立完成异步operation、冷inspect固定截止、spawn取消回收、具体owner并发通知和实际停止链验收。本片没有真实GPU、业务ML训练质量或性能收益验收结论。
