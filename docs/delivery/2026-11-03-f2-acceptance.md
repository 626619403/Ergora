# F2.4：安装、诊断和服务综合验收

日期：2026-11-03；分支 `refactor/architecture-foundations`，候选源码/测试 `67d88eccb209ab77b31b13461ff6b237a8224e08`。用户授权持续推进、每大节点审计并记录结构/性能；F2.1–F2.3已交付，最终包/精确两OS CI及独立最终审查通过。本切片完成独立综合验收，不改变冻结参考文件或实际用户服务。

## 验收与复用

复用F2.1的同源安装配方、F2.2的分项诊断、F2.3的所选服务用例。Linux以新安装目录和新控制目录执行公开命令；开发服务使用真实Supervisor4.3.0/原生launcher和无模型进程fixture，与真实Temporal/MLflow服务效果分开记账。Windows以精确两OS CI中的PowerShell5.1实际安装/升级及原生支持边界为证据，不从Linux推断Windows可运行Supervisor。

1. 使用完整预备离线缓存，从control升级development/research，重复安装与降组合，持久项目/绑定/数据保持；缺缓存和外来命令明确拒绝。核对安装源码与当前wheel一致。
2. 单一注册后通过CLI/API查看相同有效配置、诊断与发布状态；模拟缺工具/缺凭据/缺服务，维度和修复指引保持，不调用模型，不把TCP可达当任务可用。
3. 公开CLI显式启动所选服务，跨进程重开控制面后状态与PID保持；API读取有界日志/游标，缺确认/旧revision拒绝；显式停止、重复停止、重启、关闭并确认，无未选服务启动。检查原ini、注册投影与项目修订不被服务操作改写。
4. 复用F2.3最终包完整回归、身份及精确两平台CI；本切片新增旅程仅补验组合行为，不无意义重跑相同测试。完成后安排fresh-context独立审计，并检查结构/性能边界；随后进入F3.1正式任务只读入口。

## 当前进度

综合旅程已通过，实际结果与边界见下文。原始辅助代码/日志保存在忽略目录 `.ergora/checks/f2-acceptance/`。没有新的生产抽象、依赖、数据库或调度器。历史L0的真实模型/服务/GPU结果保留其当时身份；本切片不继承这些效果结论。


## Linux综合旅程与审计准备

当前非editable软件包为F2.3最终wheel，SHA256 `4d9f23118c434cbf368de33da037add286de44e342f340e78f214ef17e3526fe`，源/包/开发/基础两安装338文件一致；本轮实际Bash安装的338文件也完全一致。Linux安装脚本在Python3.12.3的独立路径运行5次：control→development→research→research重复/叠加旧参数→control，22条CLI通过；项目绑定、修订和持久哨兵保持。空离线缓存明确失败，没有可运行入口，预备缓存安装不访问索引。无模型或服务启动；降低组合不会卸载已有SDK，与手册一致。

综合服务旅程通过15次实际CLI及两次重新创建HTTP应用：从CLI统一注册、投影一致性和有效配置，到仅启动temporal命名的受控非模型进程、跨进程保持PID、8192字节中文tail/API→CLI追加游标、拒绝旧revision/缺确认、停止/重复停止/重启/关闭确认。项目文档、修订、原ini和投影保持。真实Supervisor4.3.0和冻结launcher用于进程生命周期，**该进程不是实际Temporal server**，没有启动worker/其他服务或模型。辅助脚本首轮误把内部规范化definition直接当公开输入，schema按设计拒绝；补齐顶层schema/id/repo后整个旅程通过，不改产品校验。

诊断旅程通过11次CLI及同源API：不存在的命令→installed=false/blocked；ReMe端口可达但指定token未设置→credentials_missing/blocked；绑定未监听端口的Temporal→not_confirmed且任务不可标available。各层有修复指引，主动CLI/API结果相同，项目文档不变；本机含CLI进程开销2.946秒，主动预算5秒，仅用于边界验收，不是速度优化结论。没有向真实模型发请求或保存凭据。

复用当前F2.3完整适用Linux回归324 passed、19 skipped、36子测试和24项定向/1跳过；精确候选两OS CI41514705189已通过，Windows实际范围见下一段。当前变更只有进度文档，未新增模块、数据库、重复功能或性能热路径。已完成fresh-context独立综合审计，范围内无阻塞finding；原始脚本/摘要见上述忽略目录，原始fixture目录按finally清理。


最终跨平台证据：[CI41514705189](https://github.com/626619403/Ergora/actions/runs/41514705189)精确绑定 `67d88eccb209ab77b31b13461ff6b237a8224e08`，Ubuntu和Windows均成功。Windows实际PowerShell5.1覆盖control→research→research旧参数叠加/重复升级及外来入口保护；没有单独Windows development安装或本地Supervisor实测。官方HTML步骤已由verify-ci.py核对，ci-html-status.json记录原始来源SHA。F2.4没有新增生产代码，复用该精确候选CI，不将新的文档提交伪称重新执行测试。


## 阶段出口与下一项

F2.4及完整F2完成。[独立综合审计](2026-11-03-f2-acceptance-review.md)核对需求、模块所有权/调用方向、实际复用和性能范围，未发现阻塞finding；自跑架构/组件15项通过，独立核Git归档执行/测试/CI/打包375文件、338包资源×五份内容及官方CI完整SHA/两job步骤。生产代码仍为67d88ec，本节点只有文档和忽略目录的验收辅助产物。

F2最终范围是SDK组合安装、分项诊断及Linux/WSL2的显式Supervisor运维。Linux5次安装/48次CLI、API及两次HTTP应用重开通过；Windows由精确CI实际覆盖control/research安装与升级/外来入口保护及支持边界。没有取得宿主机权限、修改实际用户服务、调用模型、自动后台探索或新增调度器。性能按真实Supervisor受控进程下的有界日志与status测量记账；实际Temporal/MLflow/模型效果仍为未重验维度。下一项[F3.1](2026-11-03-tasks-read.md)先提供现有正式任务只读入口，再按分段增加编译、提交和批准。
