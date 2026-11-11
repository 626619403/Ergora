# C6a 容量测量独立审查

日期：2026-11-11。审查者 `/root/composition_capacity_review`，fresh context；另由两个 fresh-context 子评审分别检查 Spec、Standards。同片发现与修正由原评审者复核，没有实现代理。遵循项目 `AGENTS.md`、原始 AC 要求、C6 计划、`maintainable-project-delivery` 及独立评审 brief，并采用 `code-review` 两轴和 `codebase-design` 的所有权准则。

**Spec：C6a 限定测量纵片通过；Standards：通过。开放 finding 为 0／0。** 两个原 P2 已关闭，状态记账 P3 已关闭。两次真实自身模板的原结论仍为 `request-changes`；第二次仅确认聚焦修正，不提供完整候选模型复审通过或最终模型 approve。本结论来自本次完整独立原件核验，不以模型自报、作者审计或前片 CI 代替。

## 固定边界与完整候选

基线及审查时 HEAD 均为 `3d6d1220bd600817e748c19f6a9c0fa1332f6ca9`，分支 `refactor/architecture-foundations`。产品、测试、依赖和 CI 与基线无差异；本片尚无提交或自己的 CI／远端交付。C5c 收尾两文只核与新片的状态边界，不递归复审原片。

先核 `review-r1` 八文件及 tracked.diff，再核 `review-r2`、`review-r3` 十文件。R3 索引 SHA256 为 `bf59d3796788e024fabdec83bff78a2591d76c28ec2c9305b83db75e03f26922`；十份冻结 bytes／SHA 均有效。最终工作区九份与 R3 相同；self-review 投影有唯一明示增量：原 `coverage` 改名为 `actual_scope` 并增加 `disposition`，原 identity／read_audit／response／sources 全同。该增量 22,898B、SHA256 `1a9708e9d174eeb89c3ef49882d3267c25ffe49a5e473ece35f068c1274d51dc` 已逐字段核验。

完整十文件如下；本审查报告自身和后续状态收尾属于同片记账：

- [总计划](../PLAN.md)
- [C6 计划](../plans/2026-11-11-composition-capacity.md)
- [AC5／C6 规格入口](../plans/2026-11-09-composition-console.md)
- [C6 交付记录](2026-11-11-composition-capacity.md)
- [C5c 交付收尾](2026-11-11-composition-runtime.md)
- [C5c 原独立审查收尾](2026-11-11-composition-runtime-review.md)
- [原计量投影](evidence/2026-11-11-composition-capacity-metrics.json)
- [原页面／HTTP 投影](evidence/2026-11-11-composition-capacity-browser.json)
- [fit 补验投影](evidence/2026-11-11-composition-capacity-fit.json)
- [两次真实审查投影](evidence/2026-11-11-composition-capacity-self-review.json)

## Spec

Spec 子轴及主评审均直接核保存原件；以下范围通过。

1. **身份与输入。** 按旧身份表显式读取 439 个源码文件、439 个安装文件及对应 wheel entry，全部 SHA 相同；wheel SHA 为 `aca2ea19761a0011d4b2b10851962733a5f77990dfc4f8e34450ad6901ecf9d5`，两份 RECORD 的包条目相符，含 283 个冻结参考文件。没有重建安装或递归扫描 venv。37 个已发布定义／75 个对象文件的完整树摘要、可执行位与原 bundle／内置 preset 相符。
2. **实例与材料。** 五份成功 preview 均为六 workflow、六 join 和其余 Agent，五个结构子组；50／200／500 分别有 38／188／488 个叶子，显示节点为 62／212／512、关系为 92／392／992。逐件重组 preview 摘要、全部 940 叶的完整祖先资源声明、3,046 份材料及 3,046 来源原字节、完整 Skill 树摘要、prompt 正文／SHA／字节与权限；均相符。原 grant 保持 512 实例／1,000,000B，子权限未扩大。内置 500 的原 import 拒绝、同输入补核、未发布根与索引缺席保持；没有截断材料。
3. **原编译与页面。** 五组各三个原计量样本、两个原页面 preview；中位数与记录吻合。浏览器 stdout 返回对象、保存结果、driver SHA、五组／118 检查及零 page error 相符。静读驱动确认实际 await 两帧；检查覆盖全量实例路径、端口与关系数量、查全 reviewer、末叶键盘定位、折叠关系的原来源、所选叶完整 facts／资源／prompt、dispose 和精确选择恢复。原检查不是逐端口／逐边端点穷举，原 fit 仅有点击计时，后者由独立标识的补段补齐。
4. **原 HTTP 与状态。** 全部 47 组 metadata／request／response 原字节、长度与 SHA 通过，31 GET／16 POST 均为 200；十次 preview 请求精确等于原 id／version／grant，响应 JSON 同保存原件，另六次仅正文转换。实际 81 个控制文件 SHA、只读 SQLite 逻辑 dump 与原 before／补核相同，16 张业务表为空。没有把格式转换、HTTP 服务或静态展示称为正式 Agent 执行。
5. **fit 补段。** 独立复算五组原几何数值：定位末叶后的视口均未包含全图；适配后带标签边界的最小余量约为 35 CSS 像素，满足一像素容差，且 `epsilon × zoom = 1`。zoom 在实际 renderer 限额内，model bounding box、节点数、边数及所选实例不变。全部 26 项结果与原 stdout 相符。补段 40 组 HTTP 三件均为 200，30 GET／10 POST；五次精确 preview 同旧原件，另五次为无保存转换。原 81 文件及逻辑 dump 仍完全相同。916×538 补段与 1076×538 原段不作受控速度比较。

原服务无 finally 回执的事实保持，旧 HTTP 身份当前不存在、原端口无监听；原浏览器仅能证明命名 close。补段原 finally／before／after 回执存在，HTTP 身份消失、端口无监听；六个已采样浏览器 PID／starttime 均无存活。补段 exit0 的来源明确是原编排工具终态的转录，非进程自产回执，本评审没有重新取得该工具调用或重启服务。旧审计字面常量、原源和原结果保留，新审计读取该明示来源；补段清理不转授旧段。

### 已关闭的 Spec findings

- **CAP-SP1／P2，计时范围。** 原 `prepare-capacity.py:78` 开始，在 `:80` preview 后还执行数量／类型断言及 `:87` JSON UTF-8 序列化，才记录 seconds；原交付第14／16行只称“编译”会误归因随体积增长的开销。最小修正已落实：[交付第14行](2026-11-11-composition-capacity.md#c6a0-原编译器与两种材料配置)和 metrics 的 `accepted_seconds_scope` 精确标明边界，原数值／原件保持，没有重跑未变样本。关闭。
- **CAP-SP2／P2，fit 结果证据。** 原 `browser-capacity.js:109`–`:112` 只有点击和两帧；此前 locate 已适配叶子，空操作 fit 仍可通过原 118 项。新 `fit-supplement.js:36`–`:45` 先证明非包含视口，再验实际结果；上述原数值和 HTTP／状态链已独立核验。没有改产品或增加永久测试。关闭。

### 实际自身模板及覆盖意见

两次实际 run 分别为 `4f2bb5a4c6b24ff685fc0d5521d7f9eb`／143.37秒、`297041ec0aba432b931b05d408448e3f`／128.74秒。独立重组 manifest、prepared／actual input、prompt、admission、MCP scope、原 native 事件、result 和公开投影，精确身份一致。每轮五个 scope 文件均有连续成功 UTF-8 读取直至 `next_offset:null`，0 失败；附件分别为 133,605B／17 文件和 100,465B／15 文件。两轮各四个已采样进程均无存活；这不证明所有短命进程均被采见。

首轮发现上述两个 P2。第二轮明确认可修正，但其 task／原 identity 的“完整候选”措辞与实际聚焦材料包不符，缺少部分首轮驱动／结果／投影，因而仍返回 request-changes；该覆盖意见成立。当前交付、计划和投影保留原 task／scope／decision，另用 actual_scope／disposition 准确限制第二轮，不声称省略材料已再审或最终模型 approve。此处置充分：原要求是实际模板审查加完整独立审查，没有要求取得特定最终模型判词；本片未新增产品行为，原测量包、聚焦修正和完整独立核验已分别留证。无需为取得 approve 重复未变大输入。

后端用量原事件逐字段相符：首轮 input419,729／其中 cached354,688／output2,600／reasoning1,046；第二轮 input333,671／其中 cached269,440／output3,426／reasoning1,674。缓存属于 input，reasoning 单列，没有重复相加，不推导账单、模型质量或不同后端错误独立性。

## Standards

Standards 子轴最终结论：**通过；硬规则与 Fowler 启发性开放 finding 均为 0。** 文档归本项目 docs，恢复入口、当前计划和交付记录相符；四个公开 JSON 的原件 bytes／SHA、对应字段与明示省略均通过，50 个本地链接／锚点、JSON 和 whitespace 检查通过。

无新增生产 Module 或 Interface。私有测量驱动沿原不可变库、编译器、HTTP 和图所有者工作；图仍消费原 compiler levels，端口仅为显示锚点，结构祖先与依赖关系分开。无第二套调度器、浏览器编译器、通用插件框架、后端重复分派、新依赖或永久测试／CI。新增 fit 断言覆盖一个确实可能静默通过的空操作，其他补核只处理实证缺口。43 个未归因 long task／6,630ms 不能支持源级优化；本片未作这种推断，未发现有证据要求的产品优化。

**C6A-ST1／P3，已关闭。** R2 的 `docs/PLAN.md:18`、console C6 行及交付首段仍是“两投影／准备自身审查”，与下文四投影／首审 finding／补验不一致。可达影响是恢复者误判当前工作。R3 已同步实际两次 request-changes、原两 P2 修正、聚焦覆盖限制与独立终核状态；最小状态修改已复核。

## 实际检查、原件清单与限制

本评审仅执行有界离线读取、标准库字节／JSON／SQLite 只读核验及 `/proc` 身份／监听表读取；未安装、启动浏览器／服务／编译器／模型、发送网络请求、改源、提交或推送。原退出、续段错误、拒绝和失败均保留。

私有独立原件保留在 `.ergora/checks/ac6-capacity/independent/`：`originals-audit.json`、`final-audit.json`、两份 `self-review-r*-audit.json` 与对应标准库脚本／日志，及两个轴的独立报告。`inspected-files.json` 是完整有界文件清单，逐件记录路径、字节、SHA 和核验类型；区分语义审查、字节身份读取与仅状态边界。清单覆盖上列十文件、指定驱动／原失败、五份完整 preview、47＋40 组 HTTP 三件、81 控制文件、74 bundle 源文件、两轮各52份输入／scope／事件／结果文件及439项显式包清单；没有扫描全部 checks 或 venv。必要相邻源仅核原编译／材料继承／导入／转换路径，图所有者完整读取，不把文件哈希称为整仓代码审查。

通过范围仅为 C6a 静态容量、材料预算、暖页面交互及上述清理事实。时间包含各自记录的验证／序列化或自动化／网络／两帧开销，没有隔离 CPU、冷启动、真实500 Agent 执行或优化加速证据。可信容器及 `--no-sandbox` 不构成新增 OS 隔离。C6b 三域／v6 页面、C6c 后端／成本／平台和 C6d 手册／本片必要 CI／精确远端交付仍待；本报告不关闭 AC6／F6 或后续 F7–F10。
