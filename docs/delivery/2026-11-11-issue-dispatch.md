# F7b.1-B1b：冻结工单来源的新任务

基线`3c4ef3928fe756bf596fd1da1cc80c7eb1e6578d`；[计划](../plans/2026-11-11-issue-dispatch.md)与[独立设计](../plans/2026-11-11-issue-dispatch-design-review.md)。B0自己的精确CI／原评审终核已结案；本片来源合同、最终r3安装包和离线CLI／HTTP验证已完成，自身首审及聚焦复核、两轮实际材料读取补核通过；完整32文件独立两轴与本地出口通过，精确提交／远端／自己的CI继续。

## B1a选型与B1b实现

采用definition3的`source.snapshot_sha256`选择本项目已保存快照，creation3仍恰好七个native合同，完整正文仅进入task.spec的v7 `issue_source`。纯标准库`issue_sources`集中快照runtime校验与API身份解析，由issues／tracker／envelope和creation共同消费；不在native纯读取路径加载jsonschema／SDK。原观察修订可旧于当前执行修订，只要provider／完整API base与path／namespace及local ID相同。新来源不能借旧hostless登记证明host，native ID由精确snapshot SHA绑定；checksum不称服务器认证。

合法`IssueSourceInput／Adapter／Workflow`复用v6六阶段、活动和named-source材料，新增自身queue／request根；没有临时离线注册表、占位worker或另一调度／占用账本。`artifact_protocol`和`stage_material`由输入实现提供，执行器复用旧资料所有者，完整来源实际加入work／review材料；来源不能授予权限。正式start仍原广doctor，本片不提前证明窄准入或真实Agent已消费；B1c负责所选依赖矩阵和真实运行恢复。

离线交接选择完整`contract.original_input`及其canonical SHA，复用原index／handoff合同；v7在导出／核验时核其legacy投影、来源／冻结项目选择、原outcome admission SHA。它与manifest合计仍受原1MiB索引／packet manifest限制，容量不够明确拒绝；本片没有另建source blob或放宽预算。旧v1–v6和旧packet语义保持。

静态来源容量在两个实际所有者提前拒绝：原leaf prompt编译器核每个已选叶的祖先提示＋完整来源／已知root输入这一必要下界；原creation核完整首inventory context和七文件／intent限制。v7 Input的纯标准库`inventory_context(expected_sha)`由creation与v7 Workflow共用，包含原spec／admission及全部确定stage字段，运行时超限仍转原StopWork；其他动态阶段仍沿原继承实现。动态产物／candidate diff仍在原阶段按完整材料拒绝，不称preview保证整次运行一定适配。没有截断、隐式摘要或修改限额。

## 已运行检查

首轮当前源码加载上一片安装环境的依赖，八个受影响文件212通过，pytest108.65秒／driver109.70秒；范围含原快照／读取、creation、composition tasks／runtime／workers、evidence index和handoff，不是全仓或新wheel验收。随后补了公开prompt编译接口复用、handoff可选字段投影和新来源回归，这些后改由下一轮验证覆盖。

新增回归首轮14通过／1个setup错误，21.74秒：GitLab夹具注册使用`team/repo`，既有bind helper实际选`team/sub/repo`，被原登记来源检查正确拒绝。已修夹具使用其真正namespace，没有改产品或策略迎合测试；原stdout／stderr保留。随后新增来源测试与原执行器确定性协议旅程共16通过，driver44.19秒：完整来源进入work／review的实际材料和task.txt，后续declared artifacts不递归携带旧composition-materials；这使用CLI夹具，不是真实模型／Temporal服务消费。

独立非editable安装r1的12个受影响测试文件343通过，pytest298.61秒／driver300.55秒，原reference verify通过。其后仅`issue_sources.py`的严格正整数／有限值校验变动，因此另建最终r2：449个wheel文件中的444个包文件逐字匹配当前源码与安装位置，wheel及installed RECORD均通过、283冻结文件通过；r2三个来源相关测试文件40通过，pytest48.39秒／driver50.59秒，reference verify通过。保留r1范围和身份，不借其结果称后改未经复验代码通过。

最终r2安装包的实际CLI／loopback HTTP旅程11.87秒、15项检查通过：两次显式GET保存两个不同正文；停止tracker并删除token后，用内置治理组合离线预览，CLI与HTTP完整结果一致；creation3恰好七文件，丢响应重试保持；同task ID更换来源明确拒绝，另一ID显式保存新来源。更换当前绑定并删除提交的manifest后，两入口按原intent恢复，两个任务原文件字节保持。未启动任务、Agent或Temporal；所有自建HTTP／tracker端口退出后关闭，tracker线程结束。验收摘要见[公开投影](evidence/2026-11-11-issue-dispatch-acceptance.json)，原回执和驱动保存在忽略的本片checks目录。

标准库`-S`读取、合法v7 Workflow／Adapter构造和sandbox prepare、完整原输入start路由、旧输入／worker／transport、来源错配／正文替换／预算拒绝、发布中断恢复和来源handoff的范围，分别由上述来源回归与12文件安装检查覆盖；不把SDK构造／伪Client当成真实Temporal派工、历史事件replay或模型消费。

## 实际自身模板

使用内置`ergora-structure-review`启动独立Codex会话，保持原指令／Skill，仅新增本片冻结证据Skill和显式版本／材料额度；20份完整附件359,090字节。实际run区间288.75秒，原结构化回执为`approve`，Spec／Standards在供给范围均未报告阻断问题。原先Claude失败保留，本轮沿用户已授权Codex回退，不称不同后端都成功。

离线补核manifest→prepared input→实际run input→stdin／protocol prompt→scope／native receipt→原result的完整身份，五份固定MCP资源均连续UTF8读取到`next_offset:null`，原base64页按相同offset缩小重读，工具失败0；附件逐一全文SHA核准。后台采样观察4个所属进程，无采样存活进程。后端原计数input2,238,908／cached2,089,856／output6,208／reasoning2,310保留，cached已在input内、reasoning单列，不二次相加或推算计费。原件有限公开投影见[自身审查证据](evidence/2026-11-11-issue-dispatch-self-review.json)。

该模型实际供给的是实现、测试、计划／设计及当时交付记录20文件，未供给后补安装／旅程状态、公开投影、相邻未改源码或整仓；其判词不覆盖这些范围，也不替代fresh-context完整独立review、正式owner批准或新来源任务的真实六阶段消费。

## 独立审查与修正

新fresh-context评审者核完整候选与相邻调用后提出两项P2及一项P3。平台P2：来源发布夹具选Linux/WSL2的workspace执行却未限制Windows；已仿原work_creation添加fixture平台限制，纯快照严格校验改用原source夹具、保留跨平台执行。最终r2产品上的修后15项23.03秒通过，没有放宽产品权限或新增CI。

预算P2：原`spec+admission`下界遗漏首stage已知393字节，评审者实证下界恰好1,000,000而真实inventory1,000,393字节仍可预览。已以上述同一纯首context组装所有者修正，补ASCII／中文的精确1,000,000与多一个编码字符、发布／运行拒绝及与原context逐字等价回归；新的source及非editable包受影响验证正在运行，原r2与模型首审不覆盖该后改。P3：删除v3中已经由无条件required涵盖的dependentSchemas冗余分支，v2保持，不为无效遗留字段增加拒绝测试。

首轮预算补验16通过／2个精确边界夹具失败，pytest45.86秒：原正文含换行，按raw正文长度换成无转义填充导致实际context为999,999字节。已将填充计算改为完整JSON编码贡献，没有改产品上限；独立评审者用真实旧preview纯内存已验证原溢出反例现在拒绝、ASCII／中文精确1,000,000通过且等于原继承context、多1／3字节在creation与runtime分别拒绝。最终r3新非editable包／两RECORD／444文件／283冻结已核，修后来源17项、版本worker10项与原执行器协议1项共28通过，pytest57.09秒／driver59.14秒，reference verify通过；原失败保持。

最终r3再次执行同一实际CLI／HTTP离线旅程，11.90秒／15检查通过，11次CLI／11次HTTP与两次tracker GET，退出端口／线程清理通过；没有重跑此前343项或把早包结果改称r3全套。自身聚焦复核7份完整附件93,009字节，实际run区间106.72秒返回`approve`；五scope连续UTF8全文读取、manifest／实际input／stdin／原result与7全文附件SHA补核通过，工具失败0、4采样进程无存活。聚焦模型未收到随后完成的r3测试／旅程和最终文档，不借模型判词覆盖后补状态；这些交由[完整独立评审](2026-11-11-issue-dispatch-review.md)终核。

完整32文件的新fresh-context独立评审已终核上述最终源码、相邻调用、安装／旅程原件、两轮自身实际材料和全部公开投影：Spec／Standards开放0／0，SP1、ST1、ST2关闭，本地出口通过。最终静态32文件／356个本地链接／6个已载入秘密值扫描issue0；初两份静态记录保留评审报告旧`.py:line`链接的失败，已改为GitHub可用锚点后通过。精确Git对象、普通远端推送与自己的必要CI单独结算，不提前称完整F7或项目完成。

本片持久原件在忽略的checks目录，公开记录只投影实际范围；没有真实远端工单写入，没有以本片静态材料称真实业务／模型／六阶段已通过。每节点完成后更新本记录及[PLAN](../PLAN.md)。
