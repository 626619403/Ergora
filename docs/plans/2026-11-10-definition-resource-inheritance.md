# AC5 C3c D4/D5：完整资源与祖先继承旅程

候选基线 `a9778e00e81b3b2e43a4f5745c92fbb21c990c5a`，分支 `refactor/architecture-foundations`。先读 AGENTS、PLAN、[资源总合同](2026-11-10-definition-resources.md)、[D3记录](../delivery/2026-11-10-definition-resource-editor.md)及[本片记录](../delivery/2026-11-10-definition-resource-inheritance.md)。D3已精确交付：a9778e0完整26文件本地两轴、自己的CI42790499318双OS七必要步骤及原评审者官方原件终核、精确Git对象/明确HTTPS同SHA通过。J0前置已满足，J1/J2真实90CLI/55.92秒完成，11新包及24只读原对象/旧快照保持；J3三次真实读取58资源/五list页均完整，37个owned采样进程清理；J4首审234.93秒request-changes保留；补原件后483.04秒approve/27资源完整读取，十份公开证据及owned清理通过，完整24文件新独立两轴通过、RIN-S1/D1关闭、开放0；已普通提交推送4636d77；原评审者核精确对象及10:32:04 UTC一次明确HTTPS同完整SHA通过；自己的CI42799311145第三份官方样本双OS七必要步骤success/completed、原评审者离线终核通过，精确交付终结。

## 目标与范围

用当前真实入口证明三个内置领域可以派生包含新祖先上下文、完整Skill及附件的不可变定义链，按依赖顺序发布并最后发布新根；完整树可往返，旧根/manifest/input保持旧精确材料。选取真实只读审查叶子，使用任务MCP实际读取新根到叶子的全部祖先材料与Skill附件，核对原生请求/回复和完整冻结输入。

这是D2/D3已经实现能力的跨层验收，预期不新增产品模块、契约、依赖、永久测试或CI。只有实证产品失败才提出最小修正，并保留原红与受影响修后验证。不能把本片包/材料验收说成正式调度、候选批准、后端独立性或真实训练实验。C3d父子共同提权、C4画布、C5正式交接及C6规模仍保持后续。

沿已验R2非editable wheel（SHA256 `25b5a5cf8b3044696479299abcd755b1fbb992ce43589d5ce82d3577769a351f`）和当前435包/283冻结身份；没有新代码时不为状态变化重建相同包，不把R1原28项HTTP称为本片重跑。私有命令、定义、快照、模型/服务回执放在本仓库`.ergora/checks/ac5-definition-resource-inheritance/`，公开只保存必要摘要和来源身份。

## 固定旅程和所有者

|领域|原根与实际叶子|依赖更新链|
|---|---|---|
|仓库治理|`ergora-governance-delivery`，`root/review/structure/review`|structure reviewer Agent → structure-review → delivery-review → governance-delivery|
|大型修改|`ergora-large-change-delivery`，`root/review/structure/review`|该领域专用新Agent版本 → structure-review新版本 → delivery-review新版本 → large-change-delivery|
|训练优化提案|`ergora-training-proposal`，`root/measurement/review`|measurement reviewer Agent → measurement-review → training-proposal|

原定义名/版本从内置组合实际导入回执读取，不写“latest”引用。共享原定义在不同领域用明确的新修订区分，不让一个领域覆盖另一个的已接受候选。每个引用携带实际发布的kind/id/version/digest。现有`DefinitionLibrary`仍独占完整树派生和不可变发布，CLI只提供明确正文、资源目录和接受身份；原Workflow编译器负责完整结构祖先和权限，manifest/input及task-MCP保留各自已有所有者。

1. 三组合在新的隔离控制目录导入；保存全部原对象字节、目录、执行位/只读mode及两类索引。为每个原根先准备完整manifest及所选叶子的输入，固定全树身份，后续不重新生成来冒充旧快照。
2. 在根、各结构祖先Workflow和所选Agent的新修订中添加独特UTF-8 context、完整Skill（SKILL.md、文本引用、非法UTF-8二进制附件和空目录）；用带标记内容识别材料真正来源，按各原预算选择小材料，不提高预算。另加入普通未声明附件验证包保留与资源授权的差别。保留原resources，所有permissions、limits、职责/端口/后端请求不变。
3. 通过CLI资源目录及原preview/check/publish完成每个完整新包；文件/目录/Skill摘要用原所有者生成。祖先更新须携带刚发布的实际子引用，不能填预计摘要。先用引用尚未发布子版本的新根验证准入拒绝及原索引/根保持；再按依赖发布，最后发布新根。失败不是跨库回滚：已发布独立子版本可见，旧根继续可用。
4. 对全部新包export，并在有原固定依赖的新隔离库按Agent→内层→外层→根重导入，逐文件字节/执行位和完整目录一致。保存全部原对象和旧manifest/input身份；新组合预览核新增祖先材料、完整来源、相同权限链及叶请求。验证不依赖“模型说读过”。
5. 从每份新manifest准备所选叶子的新输入；任务正文明确只核材料与提案，不执行代码/服务。固定manifest/input后将该验收库的原定义目录完整移到控制目录外私有保留，以真实`check-input`/`run-input --mode task-mcp`调用新输入。三次只读审查可使用已授权Codex回退，原因留原回执，不反复尝试已知失败的Claude上游，不声称不同模型审查。
6. 每次必须核实际native `list/read`连接、scope/manifest/输入/提示/结果身份；所有结构祖先instructions/context及SKILL.md和其完整引用附件应按原字节读取。UTF-8正文按成功页连续覆盖，若窗口返回base64则同offset缩小重试后才推进；真正二进制附件允许完整base64读取并逐字节核对。缺页/失败/截断须明确记录，不以approve替代投递。普通未声明附件留在包内不自动成为MCP资源或工具权限。

每个模型进程沿原运行所有者和持久回执；不新增模型调度器或另写临时MCP server。凭据只引用外部`LINGZHI_API_KEY`，配置只含推理字段并为0600。若真实后端不可用，保留原失败，区分离线完整输入和实际模型读取，不能把不可用伪装成通过。

## 可验收节点

|节点|交付|验收出口|状态|
|---|---|---|---|
|J0 前置与范围固定|核D3精确对象/自己的CI/HTTPS，核三领域真实引用和原接口|D3终结后才执行；明确使用已有安装与原入口，不重复D2/D3浏览器全套|完成；D3精确门禁/435安装及283冻结身份已核|
|J1 三领域依赖顺序派生|实际CLI完整资源目录、预览/接受/检查/发布、新根最后|未发布依赖拒绝不改原根；每个新包候选一致，旧对象/权限/预算保持|通过；90CLI/55.92秒，11新定义按依赖发布，三个缺子根明确拒绝/索引不变|
|J2 完整树/冻结输入往返|全部新包export→重导入、旧/新manifest/input、来源与权限链|新树全部文件/执行位/空目录一致；旧快照全身份不变，新祖先材料无截断|通过；11完整树往返相同，24只读原对象及三旧manifest/input保持，全部实例权限相同|
|J3 三领域实际只读调用|固定新输入、原定义库移到控制目录外保留、原task-MCP/Codex调用及连续读取审计|原生scope/list/read真实连通，全部祖先与完整Skill附件按原字节覆盖；无额外工具/写权限|通过；三run合计256.97秒，21/21/16资源、五list页/58read完整逐字节；原库移置完整，37采样进程清理，旧快照复核保持|
|J4 完整审查和D5交付|新fresh-context两轴、真实自身模板、两手册/计划/架构的必要事实续记|实证finding处置；公开原件可追溯、owned进程清理；完整范围终核后普通提交/自己的CI/明确HTTPS|第二轮483.04秒approve/27资源1,056,021B全部连续读取、十份公开证据/owned清理通过；完整24文件新独立Spec/Standards通过、RIN-S1/D1关闭/开放0，本地出口完成；4636d77普通推送、精确对象/独立HTTPS同SHA通过；自己的CI42799311145第三份官方样本双OS七必要步骤success/completed、原评审者离线终核通过，精确交付终结|

每节点更新本片记录、总资源计划和PLAN。只针对新的实证问题重测受影响范围。D4/D5以一份完整候选记录验证和交付，避免为同一安装状态新增重复运行；验收不能替代C3d联合提权或F9真实实验。
