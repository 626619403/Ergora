# F9b1 原生训练实时查询交付

日期：2026-11-14；基线 `8182499fa46c61adecea2f6defd2c777a433eed5`。[活动计划](../plans/2026-11-14-training-runtime.md)。产品、安装／原生CPU／浏览器／自身模板与新独立两轴最终本地核验已完成，开放finding 0／0；普通发布及本片自己的CI待验。下文保留各轮当时进展与失败，不覆盖本检查点。

原owner没有独立的只读训练transport；`perf_temporal.client`是完整操作CLI，单纯status只核binding、未固定完整历史输入。`DevelopmentTransport`属于六阶段开发spec，不能把训练Experiment伪装为Task复用。选择SDK原describe／history／query／result与原模型、workflow_id，沿现有reference子进程接缝；原连接和领域结果保持，控制面不复制调度／批准。

现有安装身份门禁只覆盖local与upstream/platform；本片新增使用的perf_temporal源码须加入显式training身份核验。公开查询默认仍离线，实时查询必须显式触发。后续start／cancel／approve与GPU不在本片。

## 实现与首轮验证

已实现training.status供CLI／HTTP共用，reference进程查询原ExperimentWorkflow，安装身份核验显式包含perf_temporal家族；页面仅手动查询、无默认网络轮询。完整原Experiment JSON历史输入、run固定、原Status／Outcome及错误区分按活动计划实现。原SDK与领域owner保持，无训练写操作、服务或数据库迁移。

首个源检查命令因证据目录被重复创建而在pytest前退出；原失败保留，产品未因该命令变化。第二轮48项中32通过／16失败：共享登记夹具只含local及upstream/platform，新增实时查询正确拒绝缺perf_temporal安装；另一个架构规则未登记新reference进程Module。已给本suite提供完整冻结安装夹具并在负身份场景还原修改，保留原共享夹具；架构规则将新Module列入原边界，同时新增perf_temporal为受限内部依赖，未关闭规则或降低身份要求。第三轮15个实时查询及原离线／reference行为共47通过／47.77秒；架构规则模块在收集时已加载旧字节，保留1条同原因失败。该轮未改产品，更新后只复验14项架构规则；最终安装包再验受影响范围。

更新后14项架构规则通过／0.31秒；产品依赖图无环，perf_temporal原内部依赖仅允许在显式reference进程接缝内。新noneditable包构建中，安装回归／真实服务／浏览器／自身及新独立两轴仍待验收。

## 安装与自身模板

noneditable wheel SHA `7ac58997490fac91b3ed15d75f6a5c13b7f36b3b4a517b7dcb069f3295e59adf`，564产品源码／wheel／安装逐字相等、两RECORD／283通过；四受影响安装suite共48通过／54.67秒，受控进程56.438秒。构建驱动的scope注记误沿用F9a文字，原件保留，独立补正记录明确本片为F9b1实时只读；产品快照与摘要未变。

自身原结构模板用授权Codex回退实际运行46.248秒、approve；14完整文件197,068B及全部祖先inline均在实际stdin，原result SHA `70d3aeb687eeb092dbfa79e1785d241188575f7103c60714cdc1447db4dfa559`，input digest `125da02d1a62301dd91543a9c42ac124d988bac23ea45e4758caac0952bb7f31`。该静态审查不冒称实际重跑服务／测试或异后端成功。

## 原生CPU验收进展

原生init／runner-add／prepare、原训练worker排队、原CLI取消与executor读取fence已实际执行；runner未启动。私有验收辅助脚本先缺asyncio导入，随后独立SDK对照缺原生模块搜索路径，两轮在验收辅助逻辑中退出，原进程owner均停止其服务并保留SQLite；产品未修改。修正辅助逻辑后仅恢复同一个数据库／workflow／run并查询，未重复prepare/start/cancel或换实验ID。完整最终状态／原件与浏览器／停止待补。

原SDK对照在恢复时取得真实`CANCEL_UNCONFIRMED`，辅助脚本原来预设`CANCELLED`的断言因此失败；确认窗口在两轮中断期间过期，本地executor的CANCELLED不能覆盖领域Outcome。原结果及42事件历史已保留，不改产品迎合预设。最终仅重启同一私有SQLite／原worker读取该原run：新查询与SDK完整Outcome相等，运行时`CANCEL_UNCONFIRMED`、离线结果`CANCELLED`同时保留；21份原配置／训练文件在查询前后逐字不变。完整历史首输入已核；恢复读取3.617秒，不计作新的prepare/start/cancel旅程或训练执行。页面与最终进程收尾继续验收。

## 最终浏览器与收尾

实际安装页面默认进入训练／选择原件后共30个HTTP请求，没有实时status请求。手动查询显示离线`CANCELLED`与实时`CANCEL_UNCONFIRMED`，可展开完整原Outcome与原run。真实status响应延迟后切项目、重新选择同一详情、同页两次status倒序返回三种排列均通过，旧响应未回写当前视图。1440／960／390三视口无整页横向溢出，桌面／手机截图已视觉核可读；实际HTTP training.js为8,075B、SHA `ded3344bb32ddcb31028d92ae8da999444d0c1d408f470aa7dbe987b9d820060`，与最终源码／包一致。API完整回复等于原SDK绑定查询。

最终45个HTTP均GET／200，其中6次显式status；21原配置／训练文件逐字保持，564当前源码与安装一致。浏览器关闭，原monitor记录已停止本片Temporal／worker／Web（受控cancel、returncode=-9），controller／已知browser PID与两个监听均不在；私有SQLite与全部失败／原Outcome保留。仅证明本片演示进程的收尾，不能把它当作远端／GPU作业停止证据。提早打开浏览器时endpoint尚未产生的私有命令错误也保留，不构成产品失败。

新的独立两轴源码均无finding；需求轴另用真实SDK/protobuf/DataConverter的9场景离线Service探针，结构轴核两个目录、全部非默认有效Experiment时限和忽略协程取消时外层6.016秒进程回收。两名原审查者随后分别只读补核最终564包／两RECORD／283、48安装检查、原42事件和负Outcome、21原件／唯一start与cancel、完整14文件实际stdin／祖先资源、45GET／三交错／三视口及进程停止；最终本地出口通过，开放0／0。详见[需求报告](2026-11-14-training-runtime-spec-review.md)与[结构报告](2026-11-14-training-runtime-structure-review.md)。普通发布与自己的CI仍待完成。F9b2写操作、F9c可信采用、真实B3／完整C2保持开放。

[可公开验收摘要](evidence/2026-11-14-training-runtime.json)保存精确身份、实际负结果和范围，不发布原始私有缓存。

## 精确发布检查点

产品 `106481a80abfd168f5b45fbba7381063505239d0` 的25文件与最终冻结字节／Git blobs相等；221本地链接、私有机器标识与diff检查通过，10个产品／测试／CI文件组合SHA `4399454c62e491baa801638257d437cee0fd49c2c87b0ba8804a82df2c067bf0`。已普通推送开发分支并核完整远端Ref；原两轴发布补核及自己的CI单独推进，不借F9a。

## 自有 CI 收口与旧静态范围更正

本候选自己的 [Portability 43504031945](https://github.com/626619403/Ergora/actions/runs/43504031945) 已 Success，精确 `106481a80abfd168f5b45fbba7381063505239d0` 的8job／30必要步骤成功；原独立结构轴只读核官方run与全部job终态HTML／HTTP身份并重算必要步骤。详见[原结构终核](2026-11-14-training-runtime-structure-review.md#本候选自己的-ci终核)。原需求轴已核精确发布，未把它记作另一次CI终核。

旧静态脚本仅对tracked执行diff检查，遗漏当时untracked的本片结构报告EOF空行；原基线到候选完整Git对象检查退出2，唯一诊断为该报告新增EOF空行。原失败保留，工作树报告已修正，随F9b2普通文档提交发布；不回写旧检查成绩或重写历史。后续完整静态覆盖tracked与untracked，产品564身份不变。F9b1精确发布及自己的CI完成，不借给F9b2。
