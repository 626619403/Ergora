# B3.3b 原生executor准入协议：逐步交付

日期：2026-11-15。固定设计基线为`5182bfa03f536d4090b91014f97eedda1c5d2d3a`，实际实施基线为`75bc99d788a9cef292b7c41eb7e01ac03d13de47`。设计、本地产品／安装验收、普通固定发布`6c7e9d924f822e60a54ce8c0686a56758ae0359a`与其自己的CI及原独立终核均已闭合，两轴approve／开放0／0。原518的七job成功／一失败保持，75bc独立接续已先闭合。下列分段保留各节点当时的状态。

[计划r1](../plans/2026-11-15-training-executor-protocol.md)选择保留原v2.2／283不变的显式派生协议：新的空目录、固定delta及完整来源身份，在原executor锁内给出窄admission接缝，并拒绝不确定started或手工接管受管命名空间。原Git、runner、archive、track和result算法不复制；预算owner能力、执行请求／attempt／ack／stopped和自动循环均不在本片交付。kernel专家留在v3优化路径。

r1离线来源探针只在ignored新目录复制原单个源码文件并用现有Git check／apply固定delta，两个命令exit0，完整派生字节与预期SHA相同。原、delta、派生SHA见计划；没有修改产品、旧安装或原283，也没有运行executor、runner、服务或训练。它不构成安装或并发准入验收。

下一步固定计划／原来源及探针清单，交新的fresh-context评审者两轴计划审查；通过后实施b1来源准备与b2原锁内接缝。前片固定CI／终核未闭合前不推送本片产品。当前不新增测试或修改共享runtime。

## b0独立设计审查进行中

新的fresh-context评审者已启动，冻结13份来源的scope SHA256为`dd23b56ae2fd8fc16d58b13d3abeb01d4c3e5e4a364e310c28a35b246397512b`；原要求、固定delta及Git探针一并交付。审查只读来源／调用者，可做便宜探针，不运行服务、训练或安装；[报告](2026-11-15-training-executor-protocol-plan-review.md)由评审者维护。

实施前盘点另发现半成品边界：复制完原source但尚未发布descriptor时若中断，目录可能被legacy校验接纳。拟以新目录内的独占空descriptor标记不完整准备，最后才写固定完整descriptor；已声明但无效时始终拒绝fallback。新协议还拟核完整279个platform来源文件，legacy保持原Python校验范围。这两点已交原r1评审者独立核查，尚非已实现行为或已通过验收。

## b0 R1接受与r2修正

独立r1需求R1（P2）已由真实518 validator复现：复制完原platform但尚无descriptor的新目录被当作legacy接纳。接受并将计划升r2：复制前先独占创建并同步空descriptor／新目录，失败声明不fallback；完整279个platform来源和唯一override核过后才发布并同步最终固定descriptor。Linux／WSL2承担源码准备／目录同步，来源识别不扩张原生执行支持；legacy原校验范围保持。delta和hook字节未变，待原reviewer设计复核，当前无产品变更。

## b0设计通过、前置CI修正优先

原r2计划已获同一新fresh-context reviewer需求approve／结构维护approve、开放0／0，R1在设计层关闭。10组便宜探针保留其真实来源／flock／异常started范围，详见独立报告。B3.3a自身CI的Linux group5出现两项原final故障测试超时，最小[观察等待修正](2026-11-15-phase-publication-wait-regression.md)先独立交付；本片仍只有设计，无产品实施，不借设计审查或前片本地通过关闭CI。

## b1／b2开始实施

实际实施基线为CI接续`75bc99d788a9cef292b7c41eb7e01ac03d13de47`，原协议基线518和v2.2／283字节保持。来源准备及识别留在既有`reference.py`，CLI只有薄入口；新增固定descriptor＋delta两个data文件。准备在新目录复制前同步空descriptor，Git严格check／apply后先核完整279来源，再同步完整descriptor并复核；失败声明不fallback。legacy仍按原用途核Python，新协议始终核279全部文件（唯一override）。

原native executor仅在固定派生delta中增加同锁admit／started／managed命名空间接缝；原283不改，Git／runner／Sandbox／archive／track／result算法不复制。两个原suite补源码身份、半成品／非py篡改、真实CLI及真实flock／外层预检后crash竞态；一个独立进程fixture仅在正常业务回归替换Sandbox和MLflow叶，实际Git／runner和原process主体保留。源码两suite回归正在运行，未预记通过；应用仍不消费queued request或启动实际训练。kernel路径不变。

## b1／b2源码与b3新安装

源码两个完整原suite已39 passed／75.63秒，外层77.210秒，包含真实锁争用、callback拒绝、外层预检后原native写started并crash、partial／dangling命名空间与started、正常无hook的真实Git／runner负gate及已有result只读。正常业务场景只替换Sandbox和MLflow叶，不把它当作原sandbox／MLflow或训练验收。原request、result／started语义与负结果路径保留。

新r1 wheel SHA256为`cf9c1caed3bb5b0bff70f198872484cdaf63b29a5193f136cbc8805fe635a676`；core／SDK各650源码／wheel／实际site-packages逐字相同、283参考PASS与依赖检查通过，只有cli／reference变化及两个新固定data，core无Temporal，SDK为1.34.0。新安装五个原suite（含完整架构边界）合并验收正运行，174份tracked＋新fixture输入已冻结；完整结果待返回。

新core安装实际四CLI来源旅程通过／2.960秒：原verify283、新含空格目录prepare、无SDK完整来源核验、重试拒绝且280个来源／descriptor字节保持；未建控制State／venv、未装依赖或启动服务／runner。原始命令和source字节清单另存；这只认证来源准备。手册、reference边界与当前架构已补新来源／锁内接缝及实际受管执行待办。自身原结构模板与新的fresh-context产品审查随后进行，前置75bc自己的CI43672292421仍由原reviewer跟踪。

## b3完整安装与自身模板通过

同一r1产品／wheel／两安装保持，冻结174份输入的五个原suite（reference、training runtime、registrations、training、完整架构边界）实际129 passed／137.80秒，外层138.984秒；没有失败或跳过。新协议来源、真实锁和crash、legacy注册／读取／SDK边界、CLI／HTTP及原图边界均在该命令实际选择范围。没有重复未改budget phase的24项或真实Temporal流程。

Ergora自身原`ergora-structure-review@1.0.0`采用已授权Codex回退，75.791秒完成、需求approve／结构维护approve。20份全文393946B及三份祖先资源实际完整进入同一stdin，结果SHA256为`dc78a345f7abbba712dfe20ff0d66c587b000911a466b487b7ad40844328ef10`；仅供给源码文本审阅，不认证私有安装／运行或CI。

新的fresh-context产品reviewer已开始对固定14份作者文件及原要求／r2合同、旧调用者和实际原件做独立两轴评审；没有委托其修改产品或运行昂贵测试。当前未新增执行能力、自动runner或循环，也没有GPU／真实训练／质量／收益证据。待其结论与前置75bc自己的CI终核；不提前推送后继产品。

## b3新独立本地产品审查通过

新的fresh-context reviewer已完成固定r1的需求与结构维护审查，两轴approve／开放0／0，详见[独立产品报告](2026-11-15-training-executor-protocol-review.md)。其独立便宜探针4.447秒通过：实际核复制前空descriptor文件／目录fsync顺序，首copy前、完整base后Git前和最终descriptor半写三类中断均拒绝fallback；legacy用途范围／Path返回保持，新协议普通来源读取仍核非Python文件。还核完整派生AST仅增加既定接缝、真实flock内callback拒绝无业务副作用和六种started／managed形态。没有重跑昂贵验收或授执行权限。

同reviewer逐项核30份证据索引、14份作者候选、174份实际输入、650源码／wheel／两安装、283参考、129五suite分布及20全文＋三祖先资源实际stdin和原结果SHA。产品／测试从固定r1后保持；三份状态文档另行冻结补核，不替换原候选或原失败。前置75bc自己的CI及终核、最终静态检查、普通精确发布及本片自己的CI仍分别待办。下一片B3.3c先固定真实执行／停止的完整设计，再交新的独立计划审查；kernel专家保留在原v3路径。

## 前置门禁闭合、准备固定发布

前置75bc自己的CI43672292421／attempt1八job／30必要步骤全部success，原新独立最终两轴approve／开放0／0，精确接续闭合；原518失败保持。本片产品／测试继续等于已审r1，源码39、安装129、两安装650／283及四CLI和原自身模板证据保持。最终文档补核已通过，现做完整staged静态检查与普通精确发布；本片自己的CI及固定发布独立续核仍待，不把前置成功转授本片。

首次完整staged diff-check将新data patch的三个空白context行报告为trailing whitespace；这些行的前导空格是unified patch语法，不能删改已固定的协议delta字节。原检查失败单列保留；在`.gitattributes`仅为`data/native-runtime/*.patch`设置`whitespace=-blank-at-eol`，其余文件及其它空白检查保持。该仓库元数据规则不改变650份产品／wheel／安装身份，不为此重建或重跑未改产品；最终完整检查及同片独立补核另记。

## 普通固定发布与自己的CI待核

已普通发布`6c7e9d924f822e60a54ce8c0686a56758ae0359a`，parent75bc、tree`47da648db4a690cb844382eaf577592237979b75`。最终17blob／5Python AST／242个Git tree链接及完整staged diff-check通过，原七产品／测试与已审r1逐字相同；独立已审16份其它blob保持，报告仅追加评审者终核字节。普通push exit0／5.574秒，完整SSH Ref同一；提交后仅c两份文档草案未跟踪，没有后继产品混入。原产品reviewer已接续核本固定提交、首方远端及自己的CI；当前未记该门禁闭合。

## 固定发布与自己的CI终核闭合

同一原产品reviewer已独立核固定6c7／parent／完整远端Ref、17个首方raw与Git blob、固定650源码／wheel／两安装及174测试输入。自己的Portability [43674493548／attempt1／#231](https://github.com/626619403/Ergora/actions/runs/43674493548)八job／30必要步骤全部success，含Windows原生回归与PowerShell5.1安装／升级；原[独立报告](2026-11-15-training-executor-protocol-review.md)发布／CI终核两轴approve／开放0／0。67捕获、104原件另存；五个匿名REST限流403保持，首方HTML／navigation／固定raw提供本次证据，未声称下载完整日志或产物。

私有`product-audit/ci-publication-r1/final-ci-audit-r1.json` SHA256为`71e5941ac25803be20ed8312f00d1994de67389e5c53ff68aca4e034200c7c81`；原review最终15,572B／SHA256为`d4d114be71674972bf08e07d94169eef3b070c2dd1fb4802fc9c11b0e2e9671f`。本片精确门禁闭合，后继c1现在可按其自身本地／发布／CI合同推进；本片未授实际训练执行权，kernel路径保持。
