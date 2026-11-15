# Q4.2c0.2b2a：原阶段两帧codec整理

日期：2026-11-15。产品基线固定`43d215af0ed372d7d1502bbe244b5631ee6d9b24`，分支`refactor/architecture-foundations`。承接已独立通过的[b2监管r3设计和具体节点](../plans/2026-11-15-training-cycle-stop-supervision.md)。b1本地与固定发布两轴通过，自己的CI在途；本片可以本地实施与验收，普通推送仍等待前片CI闭合。

范围只在现有stdlib `training_execution_protocol`持有`PhaseFrames(identity, output, result_limit)`，由原`_BudgetPhase`装配并迁移真实`record_phase`读取。原budget的selector、start／poll／stop／finish／supervise、原身份／两帧顺序、首帧65,536B／结果2 MiB、目录、原clock与唯一reaper保持。后继cycle operation将另用32 KiB结果上限；该消费者本片不实施，不为了复用伪造BudgetedStart，不增加公共入口、fan-out或总Workflow。

原`parse_json(..., finite=True)`与现有stdlib `decode`均拒绝重复key／非有限数；共享codec复用后者，不引入State、SDK、yaml或jsonschema。有效帧及原unknown／stopped事实边界保持，原parser的人类错误文本不作固定合同。只移动职责，不新增解析器、transport或reaper。

实际读取者已在固定源码核过：poll／finish消费帧与问题，`BudgetedStart.record_phase`另读首stopped帧；这些读取须共同迁移，其他执行owner保留。已有真实phase的TERM／peer／新session后代回收、大stdin、final观察阻塞及坏／缺帧为主要回归，不重复不变的完整训练suite。另用无site包解释器核共享codec真实调用的依赖边界与完整响应容量，保留其实际原件。

当前开始实施，尚无本片安装、产品测试或审查结论。每一状态更新本记录和根PLAN；本地必要检查后运行自身原结构模板并启动新的fresh-context产品reviewer，前片review不转授。kernel专家保持v3。

## 首轮实现与安装

两原owner已完成局部迁移：新内聚`PhaseFrames`复用既有stdlib decode；原budget仅装配response并改其poll／finish／record_phase读取，移除原重复receive与唯一parse_json导入。没有第二套selector、property兼容层、registry或执行分派；原身份和结果形状不变。原始四文件baseline与实际diff保存在私有`training-phase-frames/baseline/`，产品新增文件0、删除0。当前只有budget一个生产模块消费新codec，b2b具体cycle消费者已在原设计固定，不虚构已有调用者或开放插件接口。

原真实parent pipe／TERM／execute清理窗口接缝源码一通过／1.22秒（驱动2.019秒）。随后新core／SDK两个非editable安装各652源／wheel／site逐字、原283和依赖通过；实际源仅两owner变化，测试与fixtures沿原版本。最终安装中正运行原phase／peer／后代／大stdin／坏帧／final／人工release及完整架构接缝，没有终态结论。

另在新core安装的真实`-I -S`解释器调用codec：相同完整响应在32 KiB结果容量保留stopped并拒绝超限，在2 MiB容量保留全部结果；错身份第二帧仍保留原stopped、拒绝结果。0.081秒，原JSON与脚本SHA见私有`stdlib-codec-r1.*`和`stdlib-codec-child.py`；实际未载入SDK／State／yaml／jsonschema／native模块。此项只认证纯解析／依赖边界，不认证通知、训练或实际停止。没有新增跟实现逐行对应的tracked测试或重复CI矩阵。

## 09:38 UTC接续

恢复时已核原分支、固定43d基线、两owner完整diff及原在途PID；未重复构建或启动第二份回归。自身原`ergora-structure-review@1.0.0`模板已真实结束：33.094秒、14份完整文件／382,834B、三个完整祖先资源均进入原stdin，需求／维护性两轴approve；用户已授权的Codex回退，不声明异后端成功。原回复明确安装回归当时尚未结束，故不据此认证运行或发布。

新的fresh-context产品reviewer正在检查原调用／生命周期及私有原件，当前只有早期源代码观察，没有最终审查结论。原安装回归继续运行，结果、已知子进程收尾及最终候选身份仍待。前片自己的官方CI于09:37 UTC仍in_progress，run43698966489／attempt1／push／完整43d SHA及本分支匹配；未推本片。kernel专家继续保留在v3优化路径。

## 最终本地验收

原安装回归已终态：27通过／290.65秒，驱动291.725秒；JUnit的27测试、错误／失败／跳过均0与stdout、退出码一致。覆盖原phase并行peer、TERM／新session后代、跨截止回收、大stdin及held reader、坏／缺帧、不阻塞的final发布和原人工release；完整原架构接缝在同次运行中通过。没有宣称这组CPU／进程接缝验收了实际GPU、ML质量或性能收益。

`final-identity-r1.json`重新核当前source、原wheel manifest及两安装652文件逐字相同；177份原测试／示例与冻结副本及原SHA相同，未重跑无变化的回归。`owner-closure-r1.json`核本次两run的10个原owner身份，活匹配0；`/proc`的本验收路径进程观察0，没有按字符串发送信号或作全局清理主张。`git diff --check`通过。原自身模板只认证其供稿时点，不继承这次终态；本次实际原件另交新的独立reviewer终核。

两owner产品与本地验收已完成；独立最终本地结论、普通发布和自己的CI仍待，前片CI在途。下一片为已批准设计中的b2b异步operation／独立writer、逐owner通知、drain与观察，不开放总Workflow或公共自动执行。kernel专家仍在v3。

新的fresh-context[产品审查](2026-11-15-training-phase-frames-review.md)已最终本地需求／维护性两轴approve，开放0／0；原9,168B报告SHA256 `e44b414c27e509bac6af0f4066def896b26b92613912a9474ae6dd892b619911`保留。其独立核八文件完整scope、652双安装／原wheel、177测试副本、27项终态、原模板与额外peer／descendant／supervisor标记：共19个不同原actor身份、活匹配0。此独立计数扩大已核范围，不覆盖或改写原implementer的10个owner统计。源码无需修正。本片本地门禁闭合；可以固定本地提交供后继恢复，普通远端推送继续等待b1自己的CI终态及原reviewer核对；自己的固定发布和CI另验。

## 固定发布与自己的CI接续

前置43d自己的官方run43698966489／attempt1／push／准确SHA终态八job与30必要步骤全部success，原fresh reviewer已最终两轴approve／开放0／0；原403和中间态保持。随后仅普通推送本片固定d1c728087423d85ed55f06010ec81e5e1d4b2fd1，parent43d、九Git对象及完整远端Ref相同，没有推当前后继HEAD。原本片reviewer已对固定发布需求／维护性两轴approve／开放0／0，原报告11,755B／SHA256 `e7163cc733c4060a456a881072430d38d334827f7ff445534bc179ac680e2746`，9,168B原本地前缀保持；重新核652固定Git产品／原wheel／两安装及177冻结测试同一。

本片自己的官方run43704101013／attempt1／push／完整d1／本分支当前in_progress；尚无终态结论。后继877e1e4及1b8c2ed仍待本片准确CI和原reviewer终核才逐片推送；各自本地验收及原件保持，不借此发布接续完成后继。kernel专家保留v3路径。

## 自己的CI终态与接续闭合

11:23UTC重置后官方REST200：run43704101013／attempt1／push／完整d1c7280及本分支精确匹配，八job与30必要步骤全部success，原403和各中间态保持。原fresh-context产品reviewer已追加准确CI终核，最终需求／维护性两轴approve／开放0／0；报告14,102B／SHA256 `317b6ffecaeb23ac40c682088f8e6d06c869c5c081f1cef76c2938346fcc0492`，原本地／固定发布前缀保持。b2a发布与CI门禁闭合；后继可逐片接续自己的发布／CI，不扩充本片验收。
