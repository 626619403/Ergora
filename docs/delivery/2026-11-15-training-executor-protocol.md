# B3.3b 原生executor准入协议：逐步交付

日期：2026-11-15。固定基线为`5182bfa03f536d4090b91014f97eedda1c5d2d3a`，前片自己的CI43670140205已终态七job成功／一失败，其最小观察等待修正优先；本片只有计划和来源准备探针，没有产品实施或运行验收。

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
