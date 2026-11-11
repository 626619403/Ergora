# F7c-C3a 交付记录

基线 `93b538fd474120fa05574dcdcf376b7666502c8d`；[本片计划](../plans/2026-11-11-candidate-observation.md)。本地出口通过，SP1–SP3关闭、开放0／0；`ad331c854a6fbdbf6bacc3aac4350bb8d393713f`已普通提交／推送，作者精确29Git／ready及SSH远端同完整SHA。原评审精确Git／Ref及本提交自己的CI43042210053双OS七必要步骤终核通过，精确交付终结；历史失败保持原候选范围。

[结构化验收投影](evidence/2026-11-11-candidate-observation-acceptance.json)区分原候选、失败、修正复验和未验范围；私有原件不进入公开发行包。

## O0 设计检查点

下一片选择远端候选只读核对。普通Git push可fast-forward，不能把“不存在预检”解释为服务端create-only；本片不借force名字选项绕过现有不强推约束。原始Git／平台研究单独保留其网络账本和未验范围。

本地export收据、当前Git对象／ref和当前远端ref是三类不同时间的事实。原来源与候选绑定复用tasks和snapshot所有者；本地Git继续走reference_task_export；平台路径与响应由IssueBackend本族拥有；CLI／HTTP复用issues观察用例。无新持久记录、调度器、依赖或权限扩张。

C2a已普通推送93b538f，精确26Git与原报告／r2安装包独立核通过，自己的CI43023048173待终态；不借C2a验证本片，也不竞争推送取消它。GitLab标签研究表明严格原子合同仍不能满足，产品保持unsupported。

## O1／O2 源码与首轮验证

原`issue_writebacks._candidate`校验移至`tasks.exported_source_candidate`，两个真实用例共用，原持久task／source投影不变。原export owner增加只读inspect，校验原export／run／candidate、原base与candidate commit对象，读取当前ref，复用Git进程清理，不连接Temporal／重写收据／释放claim。`IssueBackend.repository_refs`由两家adapter实现，仓库白名单投影、两条精确ref和逐GET时间／原字节摘要；404只投影不可见或未找到，其他传输失败可见。

CLI `issue candidate-observe`与受保护HTTP共用`issues.remote_candidate`，三个比较分别返回true／false／null，无持久记录、ref／tracker写入或新依赖。base明确输入，head绑定原导出；项目修订在开始／返回前检查。祖先关系当前没有消费需求，按研究收窄为对象／ref核对，不增加merge-base调用或推送前置条件。

显式PYTHONPATH读取当前源码，使用保留C2a环境（不是本片安装包），新增观察suite、原export只读测试、原v7发布／提交／真实Git导出→fresh CLI衔接和架构suite共 **34 passed／59.16秒**（命令61.32秒）。只控制Temporal SDK／结果与通用用例的task ports；真实本地State、HTTP、Git与CLI保持。两provider各正常／漂移／404、错误namespace／精确ref／object、301／403／429和读取期间revision变化覆盖；本地导出ref移动／删除后历史收据保持；原v7CLI衔接同时保持已有评论／标签。逻辑DB、Git文件、收据／claim和SDK调用前后保持，provider观察只有GET。不是三条真实六阶段模型、真实托管平台或新发行包验收。

[第一方候选发布研究](../research/2026-11-11-candidate-publication.md)12次无凭据GET（11次200／1次301未跟随）和[GitLab标签ID研究](../research/2026-11-11-gitlab-label-ids.md)12次GET（11次200／1次404）分别保留原证据与限制。文档／使用／架构已同步实际只读入口；安装及两类审查继续。

## O3 r1安装与独立发现

标准隔离构建／新非editable安装r1成功：wheel SHA `247bea7cf47e19c7af1ce07ab6b4666482c498bd7cfa0e30c3ddab0fde661a59`，446包与源码／wheel／installed相同，两RECORD451／456及283冻结通过。八个受影响安装suite **196 passed／1 skipped／625.86秒**（命令641.60秒），reference verify退出0／0.27秒。该完整检查保留r1原候选身份，不覆盖下述后来修正。最慢单项为真实v7→fresh CLI18.61秒；不是平台延迟或容量结论。

新fresh-context独立首审Spec开放SP1／SP2两P2，Standards开放0。SP1是删除本地ref后False代替null；SP2是Git的promisor缺对象可使cat-file隐式fetch。实际本地最小owner探针可稳定复现objects0→4；同一hooks／protocol.file.allow条件下，直接加GIT_NO_LAZY_FETCH=1令缺对象退出128／objects0→0；调用者变量则被旧owner过滤。一个最初direct探针缺同一protocol选项，不作为可比依据；仅设置promisor=false但保留filter的早期control仍补取，后移除两项promisor配置才不补取，失败原件保留。所有source remote均为本地bare fixture，无外部Git网络。

两个真实原export回归在未变r1安装包上先得到 **2 failed／23.09秒**：分别核null和Git对象不写，原失败保留。首次回归driver误用resolve展开venv符号链接，基础解释器缺pytest，未运行产品；修正driver后的第二次才是上述两失败，不借其exit1冒称产品复现。

最小修正只影响inspect：缺失ref比较返回null；原Git进程对inspect强制GIT_NO_LAZY_FETCH=1，并在任何对象读取前要求Git>=2.43／未知版本拒绝，以本次实证版本作为保守支持下限，避免旧版本静默忽略选项。原显式export fetch、历史收据／claim及两类writeback格式不变。沿现有删除旅程补一断言，加一个真实本地promisor缺对象回归；r2构建与受影响复验继续，实际自身模板将消费修正后原件。

C2a的93b538f自己的CI43023048173现已Success／双OS七必要步骤，原评审终核并精确交付；前三In progress、REST403／lazy-matrix404保持，不借它核本片。

## O3 r2受影响安装复验

继续标准隔离构建，构建器用`python -I -m build --installer=uv --wheel`，不是关闭隔离。构建11.89秒，新非editable环境安装9.03秒。r2 wheel SHA `a999eb34bc320e6d2ccaf68de58847574d39b5121e964d19e917bd4de38e55f8`；446个包文件与源码／wheel／installed逐字相同，两RECORD451／456及283冻结再次通过。逐文件比较r1→r2，产品只变`reference_task_export.py`；其他包文件保持，未为两个inspect修正重跑原八suite196项。

受影响安装检查 **49 passed／1 failed／250.68秒**（命令252.68秒）。唯一失败是新promisor回归对接口错误文案的断言：对象／任务文件、claim与SDK调用保持的断言已过，接口实际返回`fatal: git cat-file...`，而断言期待内部`cat-file failed`。只修测试为匹配实际`git cat-file`诊断，无产品／包变化；该回归补验 **1 passed／9.17秒**（命令9.88秒）。其余49项包括两provider协议／CLI／受保护HTTP、本地ref移位／删除三态、原显式export与原ID中断未知恢复、真实v7→fresh CLI和架构。不是宣称一份最终50项全新运行，也没有把原失败改记为通过。

修正后安装owner最小promisor探针，缺对象退出128、对象文件 **0→0**，与先前红探针区分保留。实际原任务回归也明确在缺对象处报错；没有tracker账号写入或外部Git网络。reference verify退出0／0.27秒。实际自身将使用修正后13份完整源码／测试／规格／交付附件；完整独立、最终静态与本提交自己的精确交付待核。

## O3 实际自身首审与SP3

内置`ergora-structure-review`／`ergora-structure-reviewer`保留原提示、Skill和祖先上下文，只追加完整证据Skill、局部修订和材料预算。冻结manifest后移走在线定义索引，由原task-MCP以list/read读取。实际Codex运行`4eec0d1776b94def80af7515f796caa5`，**306.03秒／request-changes**，13份完整附件318,545字节。离线重建manifest→prepared→actual input→prompt/stdin→五scope→全部连续UTF8页至null→原结果，摘要与内容一致；MCP失败0，四个采样所属进程退出后无存活。自报token计数有原始来源，缓存量属于输入子集，不把它重复累加或推算费用。Claude原失败及用户授权Codex回退保持，不称双后端独立成功；完整最终公开文档不在这13附件内。

首审提出SP3／P2：`cat-file -t`默认尊重`refs/replace`，原candidate对象缺失时可读取另一个现存commit，误报原对象已核。独立评审回到原源码后也确认该合同问题。保留r2安装包上先运行扩展的原任务回归，**1 failed／8.79秒**（命令9.53秒）：文件不写检查已过，但inspect没有报错。小探针只用本地bare promisor与缺失原对象：原owner返回commit；同flags禁replacement、或仅删除replacement ref，分别退出128。三个对象文件集合均2→2、原对象始终缺失，排除新fetch和仍有原对象；没有外部Git网络。

最小修正仍在原Git owner，仅inspect过滤环境后强制`GIT_NO_REPLACE_OBJECTS=1`，原显式export不变。原缺对象旅程用False／True两种replacement配置：保留无replacement用例继续保护SP2；追加配置保护SP3，避免一个replacement掩盖原lazy-fetch回归。r3只复验新增保护、相邻真实Git／v7CLI及架构，后续聚焦自身与完整独立继续，首审request-changes不改写。

## O3 r3安装复验

标准隔离构建／新非editable环境r3，wheel SHA `7a346be467c7c5bd03035aae7331f9947be7c4ddb3a58dc3de2f534e1e4364de`；446个源码／wheel／installed包文件相同，两RECORD451／456及283冻结通过。r2→r3产品仍仅原Git owner变化；README发行元数据保持。原对象缺失且存在replacement的安装owner探针现退出128，所有对象文件保持2→2。

受影响安装检查 **18 passed／82.43秒**（命令84.33秒）：缺promisor对象有／无replacement、当前ref移位／删除三态、原显式导出、真实v7→fresh CLI及架构；reference verify退出0／0.27秒。原r1 196／1、r2 49／1及文案补验、SP3实际red保留其独立候选和范围，没有把r3小范围复验称作重跑全套。聚焦自身使用八份完整原owner／消费者／测试／规格／交付及原首审／读取audit；最终完整文档与独立审查另核。

## O3 聚焦自身复核

实际内置模板新修订1.0.100运行`1026f3500a504828b165b05b4dc4b70e`，**164.79秒／approve**。八份完整附件114,634字节；离线audit重新核manifest、prepared／actual input、prompt／stdin、task-MCP scope、全部五scope连续UTF8页至null和原结果，全部一致，MCP失败0，四个采样所属进程无存活。模型明确只批准SP3聚焦修正，未称重跑原13附件、独立核安装包或最终公开文档。首审306.03秒request-changes及其原SP3仍保留；两轮均是实际Codex回退推理，不冒称不同后端独立成功。

最终公开候选的静态／完整独立与普通提交、精确Git／远端和本片自己的CI继续；尚不据模型approve关闭本片。

首次最终静态检查覆盖29份公开候选文件、393个本地链接、JSON／diff空白、私人home路径与六个已加载秘密值，issue0。只核相对目标存在，不宣称验证锚点、外部URL或Mermaid渲染。后续C3b研究单独留待下一片，不混入本片候选或借本片验收。

## O3 完整独立出口

原fresh-context评审完成同片最终29文件核对，清单SHA `6d0b51e8c6f7af095afa99c5a4dcc549a63767a7ffbc964eeaafb5092cdc46e4`。独立重核r3包／两RECORD／283、真实red与18项复验、两轮manifest到实际native流／连续UTF8页至null／原结果及最终文档范围；[报告](2026-11-11-candidate-observation-review.md)两轴开放0／0，SP1–SP3全部关闭，无新增finding。终核报告快照SHA `a52afa14fc30fa91da6ffe65dee9eafdcd1ba337d7c87d03a9614eb505a47516`；后续状态追加不冒充原清单字节。

本片本地出口完成；精确提交／普通推送、远端同完整SHA及本提交自己的双OS必要CI仍属O4，不用C2a结果替代。最后记账与报告字节将随ready清单冻结；C3b两份设计资料独立留在下一片。

## O4 精确交付进行中

`ad331c854a6fbdbf6bacc3aac4350bb8d393713f`普通提交／推送完成。29个Git blob和执行位逐一符合ready清单，清单SHA `f0b220682f1af5237cef3d0bebba78843038085fe1ef3aa0616f27de8a69d3a7`；提交内审查报告SHA为上节终核快照。push退出0／44.75秒；作者SSH `ls-remote`退出0／29.73秒，返回该分支同完整SHA。最新静态29文件／395本地链接／六个已加载秘密值issue0，r3发行元数据含最终README原字节。

本提交自己的首次匿名Actions REST读取返回403，原body／摘要保留；这是读取限制，不是CI失败或成功REST。继续以官方run／job HTML核精确提交与必要步骤，尚未记为CI通过。原独立评审负责Git／Ref及最终CI原件终核；后续C3b未提交变化不回写本提交或冒充原r3已测候选。


## O4 原评审终核完成

本提交自己的[CI43042210053](https://github.com/626619403/Ergora/actions/runs/43042210053)后份官方run HTML为Success；Linux130596697924三项、Windows130596697242四项必要步骤均completed／success，步骤log路径绑定原完整ad331c8 SHA。原评审离线重建七份原响应／receipt并核对原workflow与结果投影，Spec／Standards仍开放0／0，无新增finding。精确29Git／ready、r3包／283、普通推送及作者SSH同完整Ref的原件已独立核过，C3a精确交付终结。

匿名REST403、matrix404、早期run In progress及中间job未齐的投影分别保持，不改写为当时已通过。这里只核官方HTML终态和必要步骤，不称成功REST、完整job日志或评审者独立直接网络成功。[原报告](2026-11-11-candidate-observation-review.md)包含逐原件摘要、七步时间和最后结论。下一片C3b有自己的候选、验收和新独立评审。
