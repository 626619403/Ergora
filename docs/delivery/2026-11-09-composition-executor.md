# AC3c.3 / CR3：可信执行与首条正式审查

日期：2026-11-09。状态：CR2b精确8151a1c/双OS CI42538555105及独立终结完成；先实施[CR3a可信verify](2026-11-09-trusted-verification.md)以解决投影路径前置。尚未开放v2入口，后续单叶调用及完整整栈仍待实现。每个可验收节点单独更新记录。

## 范围与实现位置

首条正式组合只支持一个纯只读reviewer叶子，根task端口直接传入，结构祖先只贡献固定资源与权限上限。多成员、join或依赖另一个节点的输入仍明确拒绝，留AC4。原inventory/plan/work/integrate/verify/review调度、单checkout写所有者、人工批准、候选和文件收据继续复用；基础控制端不增加必需SDK。

- `reference_executor`在任何原执行器副作用前，核v2 context等于已发布创建信封、编译spec和冻结bindings；随后仍调用原构造/claim。v1沿现有选择，v2审查沿所选独立成员。不得在多线程executor中构造会替换全局`core.read`的`_Creation`，只复用其纯核验合同或在专用进程调用现有入口。
- 对原verify分支做有限迁入：新旧任务共享同一个本地verify实现，原scope harness/命令/基线比较/回执保持；给harness写单独、内容一致的legacy投影，完整v2 `task.spec.json`保持原字节。其余五阶段继续继承原执行器。不全局patch写入、子进程或STATE，不复制整个scheduler。
- 从信封保存的manifest完整字节恢复私有目录，复用`inspect_manifest`及当前准入；不读取活动Agent库。路径、内容、权限与容量均沿原资产规则核验。原始包或当前能力不满足时，在调用前拒绝。
- 正式review保存同候选动态材料：完整stage context、原模板指令、依赖产物及明确范围的候选源码/diff。容量不足拒绝，不截断。固定祖先材料仍由原input装配消费。输入和输出、成员后端、policy、prompt摘要、实际原生MCP回执关联同一个job/context/candidate。
- 原进程monitor继续拥有超时、fence和取消；原`stage_driver`消费正式composition请求并调用现有受限叶子执行能力。低层input标明自身并非正式授权，只有已核外层stage/候选和可信receipt代表正式证据。与普通独立调用的来源区别必须出现在保存的正式调用快照中。
- executor以同一版本合同扫描legacy和composition请求根；旧executor仍只看旧根。受支持的v2准入/只读status在执行桥验收后才开放，不以manifest静态存在推断可运行。

## 可验收节点

- [ ] E1：核原创建/编译/选择且在原构造副作用前拒绝不匹配；单叶支持检查，v1兼容与原文件身份保持。
- [x] E2本地实现/验证：可信verify有限迁入并验证scope、命令、基线失败及v2不可变wrapper；不沿用旧成功文件伪造新候选通过。
- [ ] E3：完整祖先/实际动态证据冻结，运行输入身份与候选绑定；通过原monitor启动受限Agent，保存原始结果和MCP材料；缺资源/能力/容量明确失败。
- [ ] E4：版本化扫描、公开入口和真实单叶正式旅程；同legacy不同manifest、超时/取消/恢复及旧v1回归。
- [ ] E5：发行与冻结身份、相关回归、fresh-context独立审查及工具自身模板审查；普通推送、必要CI/远端终结。Supervisor整栈与恢复出口归CR4。

动态候选源码的读取范围必须同时满足项目/任务范围及叶子read上限；固定资源继承不会赋予仓库任意文件访问权。Git对象中的链接/子模块或非UTF-8、超容量不能静默省略后声称完整审查。只读模型工具限制仍不等于主机OS隔离。
