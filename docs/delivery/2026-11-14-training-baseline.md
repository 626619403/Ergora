# F9b4a 基线初始化交付

日期：2026-11-14；基线 `fad53478c9261157b3016563b410b9d4b4d85b9d`。[准备入口计划](../plans/2026-11-14-training-preparation.md)。

本片仅接基线初始化；runner登记与精确prepare随后单独验收。r2最终实现、570／两RECORD／283、受影响20安装测试、实际无SDK和完整页面／收尾、自身两轮approve已验；首轮两个P2已最小修复，新的独立需求／结构两轴最终本地补核通过、开放0／0。产品`fe26796a54b3804aac9272a9ea86643320a7f0b3`已普通推送、原两轴固定Git发布身份通过；自己的CI `43520929146`已Success，原结构轴终核通过。各轮身份及原失败见下文和[公开证据](evidence/2026-11-14-training-baseline.json)。

F9b3已精确发布，自己的CI `43516776101`及原独立两轴终核通过；不借其成功关闭本片。真实训练／GPU、质量／性能、原证据批准／采用、runner登记及prepare不在本片完成范围。

## 实现与首轮检查

CLI `baseline-preview / init-baseline`、HTTP同名POST和训练页已接入同一training应用入口。原 `reference_training_submission` 的初始化／document／registration机械提为 `_TrainingProject`，setup与submission两个实际消费者共用；取消仍经原submission读取start身份。原reader已有baseline检查提为共享函数，仍调用perfctl原ident／commit／sha，不复制验证算法。实际发布直接用原training init所用的 `perfctl.main(init)`，保留原锁、并发重复检查、原子文件发布；不引入无关SDK依赖。Linux／WSL2初始化，原生Windows预览按现有reader支持，未本地实测Windows。

只有首次基线单文件初始化，无需第二操作账本。完整canonical内容SHA确认和原文件字节SHA分列；已有不同内容拒绝，相同内容可重试。预览先核注册／home／Git根与commit，不修改原执行目录；实际发布前拒绝外置symlink锁。页面编辑输入／切项目使旧预览失效，显式确认及双击控制沿本地状态，不新建调度／全局状态树。

最初源码命令未设置src路径，collection报ModuleNotFoundError，未执行测试；改用已有依赖环境和明确PYTHONPATH后，源码首轮20项中19通过／7.23秒，唯一失败是测试只匹配symlink文字，而原safe_file先报 `Path escapes trusted root`。产品已按预期拒绝，修正测试匹配而未改产品。该失败日志保留在私有source-r1.log，补测该项与原training／submission／cancellation在途。包／真实CLI和页面、自身模板、独立两轴与本片CI尚待，不称最终通过。

## 安装与原生入口第一轮

该失败项加原training／submission／cancellation源码补测 **38 passed／198.46秒**，与首轮19项的范围分别保留。r1非editable wheel SHA `186118240d553bd463d430e4dbd423ae13ef4bc0929992d648daea2ff04d0eed`，570产品逐字等于构建快照／安装目录，两RECORD（wheel578行／安装583行）及283冻结通过；受影响五suite安装回归在途。

实际安装CLI完成预览／错误SHA零registry写入／原perfctl初始化／同内容重试与原列表读取。实际无site-packages的`-P -S`子进程找不到temporalio，仍能初始化独立原基线。首个SDK探针把整个安装site-packages加入PYTHONPATH，断言失败，原stderr保留；修正为按spec仅装载Ergora包后通过，非产品修复或Windows实测。27份已存在原配置／基线受保护原件已保存SHA，供页面后核不变。真实页面验收刚开始，无服务／runner／训练／GPU或采用主张。

原结构审查模板已对14完整文件／245,707B运行，自身approve／49.805秒，全部内联文件和祖先／叶资源核实际stdin，结果SHA `983361a519462f19f5498d409290216d7226bd7fc094f5c7f381680e5889260f`。使用用户授权Codex回退，不称异后端成功；该轮明确安装回归／页面尚待，不替代新的独立两轴审查。私有原件集中在 `.ergora/checks/training-baseline/`；公开文档不包含机器配置或凭据。

## 独立首轮finding与最终r2

新的独立[需求](2026-11-14-training-baseline-spec-review.md)／[结构](2026-11-14-training-baseline-structure-review.md)审查发现两个P2：CLI先read_text再检查序列化容量，原文件可带大量空白越过输入界限；setup调用的原core.git写死Linux路径，不能支持Windows预览。最小修复只改两生产文件：CLI两操作在既有分支共享`rb`限读1MiB+1后解析；setup复用原 `harness.git_scope._run_git` 的PATH、os.devnull与只读Git环境清理，不引入其Task preflight限制。原capacity测试增加大量空白原文件拒绝，没有新helper／suite或修改283参考。两审查者已核源码修复有效，最终原件补核另记。

r1安装五suite实际 **57 passed／232.41秒**，监控234.249秒，未触600秒界限。r2最终wheel SHA `e39866028ee7e4625f814e3fb23064ee7ea274d85cb2cd509c4f06d24af5ffeb`，570产品逐字匹配当前源码／快照／安装、两RECORD（578／583行）与283冻结通过。r1→r2产品仅CLI和setup两件，另568件相同；测试只改原baseline容量用例。r2只执行受影响baseline＋架构suite，**20 passed／11.39秒**，监控12.975秒；不冒称在最终包全新重跑57项。最终`-P -S`实际无site-packages／无SDK仍能核Git并读取相同原基线回执，原字节保持。

## 实际页面与收尾

r1首组页面已通过，但第二组最后一步重复selectOption当前项目，验收脚本在视图重建时操作旧节点而timeout；未产生整组完成结果，失败原件保留。修正仅是脚本同步／避免重复选择，在最终r2包新增独立验收项目后完整重验，没有改产品或删除已有基线来重跑。

r2真实页面两组均返回passed：原preview／原perfctl init、错误SHA零POST、编辑输入后的迟到preview丢弃、双击只一次init、完整同内容重试及不同内容无覆盖按钮；真实服务器发布成功后扣掉回复，页面重读已发布原件后再确认相同内容，文件SHA保持。另将真实preview和已发布init回执延迟到切换另一项目后送回，未污染新项目。1440／960／390视口scrollWidth均等于视口，390未发送表单也通过。浏览器唯一预期网络错误来自刻意丢弃的真实初始化回复，不宣称零错误。

最初27份配置／基线原件SHA全部保持；八个独立验收项目的原baseline与确认输入一致，另一项目没有baseline。没有创建manifest／spec／job／fence／approval／integration-ticket，Git仓库status为空。两个web进程组按原monitor收尾、两浏览器关闭、两个原端口均不监听；私有 `final-observations.json` 保存终态。

最终聚焦原结构模板第二轮approve：五完整文件95,335B／23.170秒，全部输入／祖先资源核实际stdin，原结果SHA `f7a1fce083795dcfbf1aba2731c339a51136588e6a0c43845b4251134610a69e`。原首轮14文件与本轮各自保留，不混称全新完整57项回归、Windows OS实测或异后端成功。[公开JSON](evidence/2026-11-14-training-baseline.json)目前引用26份私有原件SHA；最终独立两轴与发布／自己的CI进度见下段。

原CI分组5在最终r2安装环境收集成功：357／1810（1453 deselected），新六用例suite在显式分组唯一登记；这是收集，不是357项执行通过。公开JSON追加两份收集原件，共26份SHA引用。需求轴已独立补核最终实际原件、关闭两个P2并通过，开放0；结构轴最终原件补核也已通过，两个方向开放finding为0／0。架构图／模块所有权与训练手册已同步本片入口，普通发布与本片自己的CI仍待。

## 固定发布与自己的CI

`fe26796a54b3804aac9272a9ea86643320a7f0b3`的27个Git blob与发布前清单逐件一致，唯一父`fad53478c9261157b3016563b410b9d4b4d85b9d`，11产品／测试／CI组合SHA `426d271430bdba818bd999be46c2ae5b06bdc6ec85c2b138e0318fe0712001ef`保持。普通推送当前开发分支、原完整ls-remote同候选；原需求／结构轴分别直接读固定Git对象补核通过，未用随后runner工作树代替本片产品。

自己的[CI 43520929146](https://github.com/626619403/Ergora/actions/runs/43520929146)第四份原run HTML为Success；8job／30必要步骤终态、完整候选SHA日志链接和job完成标记均核通过。最初group0瞬时upload步骤虽显示success但无完整log URL，离线parser拒绝；保留r1后取终态r2，没有放宽检查。Windows到r4才完成。原HTTP收据与页面SHA保留，未声称REST或下载artifact档案；公开JSON保留原26本地原件引用，另增28发布／CI引用。原结构轴已直接核原HTTP／固定Git／30必要步骤并通过CI独立终核；未代称需求轴另作CI复核。状态记账随下一产品片普通提交，不改本片冻结产品或宣称新本地回归。
