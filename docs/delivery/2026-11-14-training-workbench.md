# F9 训练实验工作台交付记录

日期：2026-11-14。[活动计划](../plans/2026-11-14-training-workbench.md)。F9a 基线 `47443840b68693f63ee011dc6fbe29421a42223f`；只读产品已实现于工作树，正在验收，尚未发布。后续每个行为节点分别记录实现、验证、审查和发布身份。

## 已核事实

原训练执行由 `agent_platform.training`／`training_executor` 与 `perf_temporal` 所有；原 performance registry 是 baseline／manifest 的权威，spec保存精确manifest绑定，job／fence／approval／集成票据保持原身份。现有 `agentflow training` 可执行 prepare、start、run-local、status、result、cancel、approve，但没有控制面离线列表。Web目前只提供训练模板下载与Forge候选操作。

首片沿独立reference reader提供观察，复用原validator与有界文件读取，CLI／HTTP共用应用查询。SDK／服务／GPU不作为离线导航的依赖；读到原结果也不等于实时查询、重新测量或候选采用。GEPA仍只负责Skill文本优化。

## F9a实现与源验证

`training.inspect`供CLI／HTTP共用，校验登记的项目与训练模板，再交原reference进程读取。原 `reference.py` 中新增SDK无关的reader，复用原安全路径、有界读取、Windows reader、perfctl与Experiment validator。以项目performance registry为入口，逐字核原全局manifest／spec的绑定、项目／Git根、原request与result／gate SHA。当前baseline变化和缺结果保留观察状态；单条坏记录不阻塞后页。

`training.js`是独立训练导航，局部请求序号、DOM存活、项目与控制目录约束迟到响应；不向外部服务查询，也不在首页刷新中附加实验扫描。只显示原件、完整摘要与原生流程说明；Forge仍沿原kernel owner。无数据库迁移或原参考修改，GEPA与原训练职责保持。

新`test_training.py`登记既有Linux显式分组，覆盖原件不变、负门禁／无结果、坏条目分页、baseline变化、六种精确绑定／gate篡改、跨项目、大小／symlink及CLI／HTTP一致性。首次命令未创建basetemp父目录，14架构项通过、11夹具setup错误、0.79秒，无训练测试正文执行；原失败保留。创建本片持久目录后，源训练与架构共25通过／12.25秒，未因夹具错误修改产品。

## 当前验收状态

F9a本地核心／最终展示包、原生CPU原件、实际浏览器及自身模板已验，新的独立两轴最终本地出口已通过，普通发布／自己的CI待收口。源CLI／HTTP一致性不代表真实GPU；F9b–d、真实B3与完整C2保持开放。各轮结果与实际覆盖范围如下。

## r1实际证据与修复

r1 noneditable wheel SHA `899bee11596250376b018f3b2ce2f320e640eab699c7e5e4f5ad5c584a4b7fc3`，563产品／两RECORD／283冻结参考通过；六个安装suite共121通过／87.23秒pytest、88.869秒受控进程。该成绩保留为r1，不自动覆盖随后两处修复。

实际固定原owner的init／runner-add／prepare及LocalTrainingAdapter创建本地job请求／fence共9.488秒，通过新reader读取前后18份原配置／执行文件逐字不变；另一项目无实验泄露。没有连接Temporal、运行runner、查询MLflow、调用模型或GPU，围栏存在不证明任何远端作业已停止。

自身原 `ergora-structure-review/root/review` 以授权Codex回退实际运行59.623秒，完整11文件183,738B与祖先inline均在实际stdin中；结果为`request-changes`，原结果SHA `9bc66147a205a00f5c87d9e5f3938479667eafbee5dc6fb65b6233e8b101ec20`。它发现runner与job请求皆缺时repo核验被跳过；新独立结构评审也复现同问题，并另发现配置／状态同根的合法配置被路径相等误标来源。两方向均按原场景复核当前修复：source选择显式化，缺少两种repo见证时明确拒绝；单独保留任一真实见证仍可读。原发现和原失败保留，不以限制合法配置迁就。

修复后源训练／架构27通过／13.09秒；reference SHA `31f95d6c48c2a7462c2aa0b7b514e1d4ad21636c55c3619684b9973912d7ec94`。后续新包与页面／自身复审见下节，独立最终与发布／CI仍待收口。浏览器r1迟到响应夹具首次用错CLI函数参数而失败，未构成产品失败；修夹具后实际交错已验，原失败保留。

## r2核心与r3最终展示验收

r2 noneditable wheel SHA `5fa33e011a0b1a2e50e0346e8737d1f7604053e71043855a361f7c2d6c32650b`，563产品／两RECORD／283通过；安装训练／架构／reference三suite共33通过／16.98秒，受控进程18.616秒。r2读取原生r1记录得到同一完整观察，18原件保持。自身原结构模板的11文件187,590B完整输入及祖先资源实际交付已核，23.977秒`approve`，原result SHA `4b278acc472436d19163fb5f433d9e8724721664353f4efe4fa2a829badc3a1d`。两独立方向对两P2修复源码复核开放0，最终整体验收单独补核。

实际窄侧栏截图促成一处展示调整：复用已有卡片样式列实验，baseline显示摘要并保留完整折叠原件；请求与生命周期控制不变。r3最终noneditable wheel SHA `df85fd4c28d502f8d39c1138e317738ee716d090baf9114c1d41db9b538b285a`，563当前源码／wheel／安装逐字相等、两RECORD／283通过。该轮只有training.js渲染变化，核心33项保持其r2范围，未为可逆布局重复整套核心测试。r3原生readback同一观察／18原件保持，实际HTTP资产SHA `f754d2409ec19d002e5e076426b08d7594dc59e48969d2c212ce6da9e765ef44`等于最终源／安装包。

r3真实浏览器已验列表／详情、完整折叠基线及40位commit／文件摘要、取消围栏／unknown、另一无基线项目；实际旧详情请求后切项目、旧列表响应晚于新列表两排列均通过。1440×1000、960×800、390×844无整页横向溢出，桌面／手机截图已视觉检查。所有本地HTTP均GET；浏览器已关闭，原进程owner正常执行取消收尾，旧／新controller及监听均停止；原18件仍逐字不变。没有连接Temporal、执行runner、访问模型／数据或GPU。

原结构模板再对最终六前端文件25,122B做聚焦展示复审，23.370秒`approve`；原result SHA `1c34e2d73b59b4e47c1ae879e548951eb8566df2dc04d837771bf414dafe7f77`，input digest `a01ce102732654b2eb72a295d00f526c2766dda636229c07d57f3879117f9c31`。完整packet／祖先inline／实际stdin一致已核。两轮均使用用户授权Codex回退；不冒称异后端或独立运行的验收。

[可公开验收摘要](evidence/2026-11-14-training-workbench.json)只保留身份、摘要和范围；原始验收缓存不发布。最终新独立两轴分别核最终包、r2回归／r3展示、原生读取、自身实际输入／原result、浏览器／停止与公开摘要，本地出口通过，开放0／0。精确发布／自己的CI待补。

终版静态首次检查发现需求报告两处相对源码链接使用冒号行号，GitHub无法定位；已按实际文件改为GitHub行锚。产品无变化，修后对完整发布scope复核本地链接、私有机器标识与diff。
