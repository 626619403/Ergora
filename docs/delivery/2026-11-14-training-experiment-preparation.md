# F9b4c C1 实验准备交付

日期：2026-11-14；基线 `80236fe8957c0704a3c73c7ea1440f7f288ff563`。[计划](../plans/2026-11-14-training-experiment-preparation.md)。

## 实现范围

CLI／HTTP共用training应用入口，隔离子进程暂存调用原register_runner及prepare，预览完整原manifest／spec及精确发布计划。确认固定项目revision与canonical SHA，原state先不可变保存同一恢复意图，实际三文件发布继续原prepare；只对暂存spec的manifest URI映射真实路径，binding仍用原manifest字节。status无SDK读取各文件事实，重复prepare不自动继续部分发布，resume需原intent SHA并重核source与原文件。无本工具意图的旧原文件不接管，源漂移／异内容不覆盖。

新增reference_training_preparation是三件发布／恢复的领域所有者；复用既有context、有界reader、原write／registry lock、本地file_lock、process monitor。serializer从setup机械移到context供两真实模块调用，应用层短revision预留由实际publish callable复用。283冻结文件不改，无第二实验库、调度、批准或训练执行。页面准备／恢复是后续C2，本片只接CLI／HTTP，既有页面可读取已准备原实验。

## 首版验证与历史范围

- 源码首轮38通过／1失败／95.88秒：外项目runner在该项目尚无baseline时先报缺文件。已将runner归属立即检查移到读baseline之前；失败原件保留，不作为通过。
- 修后源码 `test_training_preparation / test_training / test_architecture_boundaries`：39通过／64.93秒。新12用例包含原write后真实os._exit(73)的intent／global／project／spec四中断边界、新进程显式恢复、原件／来源漂移／冲突／孤立外项目、真实发布后丢回复等。
- noneditable r1 wheel `cd3e98c1bcce0448efaeb38839f0f1a75509e88dff7a43ac7281a57a3498691e`，571产品、wheel579行／安装584行两RECORD及283冻结已核。安装包／构建快照逐字一致；后续文档与无行为注释更新不继承未核当前树身份。
- 安装r1六suite（preparation／baseline／runner／training／architecture／submission）65通过／212.14秒，原process monitor214.042秒；不是全库运行。
- 真实安装CLI11操作完成baseline、runner与实验预览／错误SHA零发布／精确准备／同意图重试与resume／原reader；实际`-P -S`无site-packages且找不到Temporal SDK仍可读preparation。
- 真实loopback HTTP完成preview、错误SHA、发送实际prepare后客户端关闭且不读响应，服务端捕获原200；GET读回同intent，错误intent拒绝、显式resume与同prepare保留原字节。没有以TestClient替代本次实际网络旅程。
- 原8件配置／baseline逐字保持，CLI／HTTP两实验各三原文件精确匹配intent，manifest原字节SHA与spec binding一致；无job／fence／start／批准或runner命令执行，验收Git clean，monitor停止web组且原端口不监听。
- Ergora原结构审查模板实际Codex授权回退：15完整文件／260,874B（含原prepare／core.write／perfctl owner），38.091秒approve；实际stdin含完整输入及全部祖先／叶资源，原结果SHA `3f5ad224625b181b29d5a529b4fcae1c3f2e7cde5c1b5dd02b9f0f52635ad6fc`。不把内联核对称阅读理解或异后端成功。
- 新fresh-context需求／结构两轴已启动，结论待回；目前无独立通过主张。

分组5原插件仅收集376／1829，1453 deselected；新12项唯一归属，不称376项执行。[公开证据](evidence/2026-11-14-training-experiment-preparation.json)列26份原件摘要。私有原件在`.ergora/checks/training-preparation/`。前片runner自己的CI43523861953按固定候选单独收口：第三官方run HTML Success，八job／30必要步骤均完成success，原结构轴独立终核通过，未代称需求轴另核CI；不借其成功验本片。

## 剩余验收

最终r2包、本地运行与新fresh-context两轴均已收口，尚待普通提交／推送／精确Ref／自己的CI。C2页面、F9c证据批准与F9d／真实B3另片，不以CPU文件合同替代GPU或质量验收。

## 独立评审修正中

需求轴发现：完整发布后的显式resume会在检查job／fence／start之前提前成功返回，与明确拒绝条款有歧义。已把原ensure_unstarted上移至完整早返之前，重复prepare保持只读；增加三类后来checkpoint的参数化回归。原r1验收保持其旧产品范围，最终r2包与修后受影响运行已通过，新的独立两轴最终本地补核已通过。占用检测明确限于本项目manifest／共享global manifest及spec／同ID准备意图，不声称跨项目扫描人为删除全局原件后残留的manifest。

最终r2构建的私有安装脚本曾误把已有依赖缓存路径从r1替成不存在的r2，venv阶段失败；保留原setup与stderr，继续用既有固定r1依赖缓存安装已生成的同一r2 wheel，不改产品或依赖。

## 修后最终包与验收

最终r2非editable wheel `cc96e63433d647a0e9db33f2de52ff056090d274ae211863c36e591606df0935`；571当前源码／快照／wheel／安装逐字一致，wheel579／安装584行两RECORD、283冻结全部通过，11件产品／测试／CI组合SHA `4414d4f7f8fba705e18373c53a827f6eca0691d2a04fd5a48a452208dfa0e983`。受影响preparation suite **15通过／69.67秒**，monitor71.393秒；包括三新checkpoint及原四真实中断／来源漂移／冲突／CLI HTTP恢复。r1六suite65项保持修前范围，不称最终全库重跑。

r2再次实际运行11条CLI、真实`-P -S`无SDK status、loopback HTTP实际写后丢200回复并GET原ID读回、错误SHA／同prepare／显式resume。原8件及两实验各三件字节／binding保持，无job／fence／start／批准／命令执行，原monitor停止web组、端口关闭。分组5最终只收集379／1832，1453 deselected，不称379项执行。

最终自身原结构模板再审15完整文件／265,212B（含原owner）、33.487秒approve，结果SHA `b7c4144e5e198f7d878a86088cf611407d408a3ebabdab08bd3b1b9e6f8bc0c4`；实际stdin及全部祖先资源保持。用户授权Codex回退，无异后端成功主张。[公开证据](evidence/2026-11-14-training-experiment-preparation.json)保留26件r1原件，再增26件r2原件。新fresh-context [需求](2026-11-14-training-experiment-preparation-spec-review.md)／[结构](2026-11-14-training-experiment-preparation-structure-review.md)已直接核最终源码、原owner、r2全包／两RECORD／283、实际安装与CLI／HTTP／原件／收尾／52引用。需求轴首轮P2修后关闭，最终本地通过、开放0／0。普通提交／推送、完整Ref与自己的CI仍待，不借前片CI关闭本片。
