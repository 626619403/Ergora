# Q5.1：目录级变更协议交付记录

日期：2026-11-15。基线 `750dd68ff2b1e41f6fe390d6a52e651bf41d5642`；先写[具体计划](../plans/2026-11-15-component-change-protocols.md)，再实施。

|步骤|实际状态|
|---|---|
|盘点|已恢复根合同／总计划／架构和用户手册，核AgentBackend／IssueBackend本族工厂、WorkflowInput版本族、定义库、项目／schema／state、训练／索引与测试现有owner；静态源码盘点76模块／312边无环、28JS。|
|实现|已写根入口／源码／测试／脚本三局部AGENTS、唯一分支工程指南及当前架构；76模块／312边／28JS清单逐项核固定Git750身份，公开静态清单不包含动态调用或性能证明。|
|验收／审查／发布|r1 wheel构建成功，640产品与原750源／原r1安装逐字保持、283参考不变；仓库src/ergora/AGENTS.md按原package-data规则不进入wheel，无需重新安装相同产品或重跑runtime测试。12 Markdown／259本地链接零错；自身原结构模板25.034秒approve，完整22文件／348,582B；新独立本地两轴approve／开放0／0；普通发布及自己的适用CI待完成。Q4.1固定发布已原独立两轴通过，自己的CI单独跟踪。|

本片不改业务仓库、不安装生产训练框架，不增加调度器、全局插件注册表或第二份用户手册。后续实证重构单独立片。

## 实现和验证范围

工程指南按实际owner分支，不复制用户手册；低代码变更沿原JSON／YAML定义编辑，新增真实后端沿本族ABC／for_binding和组件元数据，不在上层做具体实现分派。变更配置／持久格式、完整继承资源、原ID／unknown恢复、训练／质量证据、测试价值及目标训练项目组件协议分别给出接缝和最小检查。其他可选工具尚未全部统一为ABC，文档明确保留实际支持范围。没有修改模板资源、schema、Python、SDK、CI或业务项目。

私有原件 `.ergora/checks/component-change-protocols/`保存新wheel、package-r1.json及build-r2日志；wheel SHA256 `e6eadd281a65801d280261e9dddc9399d52b4c179bb3ab506c4ed6a9e5e758d4`。仅构建轮次身份改变，640产品内容与原包／安装完全一致；不借该构建重验旧训练。最初build输出目录不存在，shell在启动build前exit1；原错误保留，建输出目录后原构建成功，无产品修正。

## 自身原模板审查

原r1安装冻结`refactoring-quality`的structure叶，使用授权Codex替代；run `01bdb0678c554fa89b9d10cda04c2bf9`，succeeded／exit0／25.034234秒／decision approve。input `5c1fbb5d21012ddc7d205f28e1a685502fab82ea42683770b93b72e4df4dbcf9`，原result SHA256 `7c934fd9343ec2cf5ef6f6ec6c89028a072cd1c474e1f30bbf892b291cff31de`。冻结13作者文件加9邻近接口／配置，共22完整文件／348,582B，原任务和全部祖先resource在sealed input／实际stdin连续字节一致。只审供给文本，不能认证私有wheel、原安装、链接或CI；这些另交新fresh-context独立reviewer直接核原件。

## 独立本地终核

新[fresh-context报告](2026-11-15-component-change-protocols-review.md)沿真实构造／调用／恢复接口复核最终14作者文件／200,131B；固定Git750／640产品、两个不同身份wheel／原安装、283参考、76／312／28静态清单和原自身22文件／三resource／input／stdin／result均直接核同。最终作者13Markdown／262本地链接零错；需求／维护性两轴approve、开放0／0。未增加测试、CI job、runtime抽象或业务改动。报告明确新目录AGENTS在既有push过滤外，因此本片仍需自己的实际CI；前片终态前不推后继触发提交。

## 普通发布

已普通发布705cbe428dce73ff222dbdaec3c67329a310c06d，唯一父750dd68ff2b1e41f6fe390d6a52e651bf41d5642、tree9516f1710d131f7c70acd7d657a79fd66d7cdbbf；全部15blob与暂存一致，实时远端完整Ref一致。最终含报告14Markdown／277本地链接零错。前片Q4.1自己的CI及原独立终态通过后才推送；本片新目录AGENTS触发自己的CI，终态及原固定发布补核待完成，不能借750的成功认证。

原独立固定发布补核已追加原报告：15blob／完整远端Ref、固定640产品／283参考同一、14Markdown277链接及完整diff通过，新增finding0／0。自己的CI43631156705已核完整705身份，最新观察28／30、七job完成成功／Windows在途；保存的terminal-r1／terminal-r2后缀仍为中间态，不将文件名当终态认证。

## 自己CI与精确交付闭合

[Portability43631156705](https://github.com/626619403/Ergora/actions/runs/43631156705)绑定完整705cbe428dce73ff222dbdaec3c67329a310c06d，terminal-r6于2026-11-14T19:37:17UTC观察八job／30必要步骤全成功。原独立reviewer直接核官方run／完整分页／八job原页／30步骤log身份和时序，以及固定15blob／640产品／283，终态两轴approve／开放0／0、片内剩余验收0，Q5.1精确交付闭合。原11,420B报告前缀保持。

原所有早期捕获保持中间态：terminal-r5虽30步骤通过，Windows job尚在途；observation-r2的group5分页读取时在途，随后job页已完成，分别记录两个顺序观察，不冒称原子快照。只有r6提供一致的全终态；原顺序观察差异不通过重写或补跑隐藏。没有以Q1.2后继源码／wheel认证705，也没有重跑不变产品。
