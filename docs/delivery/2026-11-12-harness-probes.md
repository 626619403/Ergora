# F8-H1 有界探针与适配交付记录

[本片计划](../plans/2026-11-12-harness-probes.md)；文档基线 `a35123e4ea3f24b091774f1476c2e159804de560`。P1/P2 私有原生探针、P3 最小只读实现及 P4 安装／合成服务入口验收已分段完成；自身模板、完整独立审查和精确远端交付仍待收口，没有真实模型兼容或会话恢复结论。

## P1 固定 MCP 正向链

使用 H0 已核的固定 SDK／runtime 与原始直连 Python 入口，原 Ergora 非supervised 进程owner，loopback 推理服务返回预定 SSE，无真实模型／SaaS业务调用。由原随包结构审查 Agent／workflow 修订1.0.118、manifest、prepare-input 与 task MCP freeze／launch 提供五份资料；累计72,162字节，含一份71,019字节中文资源。实际6.74秒、十次模型HTTP请求、三次list与六次read；各请求仅 `mcp__ergora_task__list/read`，全文连续UTF-8到next_offset=null，逐件字节／SHA与原scope相同，manifest→input→scope身份匹配。

原MCP有两次进程启动（协议探测与实际服务），成功tools/list与九次tools/call有原回执；服务环境无loopback token。五个采样所属进程无存活，服务线程退出、拥有端口关闭；未据此推断全部短命进程。首夹具字面反斜杠n及第二夹具非hex run_id均在服务／runtime启动前失败，原文件／目录保留；第三夹具使用原schema要求的UUID，不改产品校验。

## P1 拒绝与结果校验

4.69秒四次loopback请求，故意调用未授权bash、未声明URI、65,537字节超页，三份原native tool/result均isError=true，标记文件未创建。工作区AGENTS／Skill的独立ambient标记未进入任何请求；这只证明本次标记范围。合成最终JSON使用不合法decision=accept，原结果schema明确拒绝；不能把runtime的completed当作审查批准。五个采样进程无存活、服务线程及端口关闭。此段没有通过产品后端接受结果。

## P2 已观察的失败边界

- MCP启动命令明确exit7、设置failOnStartupError=true及禁止重连，5.39秒内仍有两次模型请求，工具表未含MCP，未知list调用isError；原native最终completed且JSON本身有效。私有验证器先前错误假定必须有tools字段而KeyError，原失败保留；这是有价值的边界观察，不能改写为零请求或SDK必然终止。四个采样进程无存活、服务线程退出。
- 在模型首次请求时仅终止本scope的实际MCP服务进程，7.08秒、两次请求，read返回isError及Not connected；runtime仍completed，禁止重连。五个采样进程无存活、端口关闭。曾有tools/list不证明后来连接仍可用，适配须检查原工具错误。
- 慢模型段使用原25秒budget，25.53秒timed_out／child=-9；主动SIGINT只发给原进程owner，在第二次模型请求挂起后3.90秒cancelled。两段均在两次MCP启动中分别创建一个不detach的受控孙进程，pgrp／sid相同且两个完整PID／starttime身份均已停止；各七个采样进程无存活，无native最终结果，服务线程／端口关闭。这是原非supervised路径的真实回收，正式supervised路径另验。

正式supervised路径另起专属进程，直接使用原 `processes.run(supervised=True)` 与 `cancel_supervised`，SIGTERM只发原owner；7.66秒cancelled／child=-9，两次MCP启动的两个受控孙进程及七个采样身份均无存活，端口／服务线程关闭。这验证原subreaper清理路径，未启动Temporal或真实模型六阶段，不扩大为Windows验证。

按父研究建议另补四个定向生命周期窗口，没有更改产品进程所有者：MCP前早期启动窗口在采样到三个所属身份后0.20秒发SIGTERM，0.50秒cancelled、无MCP或模型请求；慢MCP包装在真实服务exec前挂起100秒，原supervised路径在受控孙进程身份落盘后取消，1.50秒cancelled、零请求、一个孙进程及五个采样身份无存活。相同慢MCP情形由原非supervised十秒预算收口，10.51秒timed_out、零请求、一个受控孙进程回收。另将原supervised慢模型取消段的两个受控孙进程改为 `start_new_session=True`，逐件确认与父进程pgrp／sid不同，6.65秒cancelled、两次请求、两个孙进程及七个采样身份回收。四段拥有端口／线程均关闭；这里只覆盖所测MCP前早期启动、挂起MCP及受控脱离组身份，不代表任意daemon或全部初始化窗口。

上述原生探针阶段尚无生产适配，启动失败／断连的观察只确定后续必须拒绝的场景。P3/P4再验证实际拒绝。新组件只提供composition的text-only／task-mcp，原生自由调用及workspace模式明确unsupported。

## P3 最小实现与结构

新增现有ABC下的DeepSeek实现与本族局部注册，一个独立可选环境驱动，组件配置沿原目录描述。只提供审查／实验设计／性能分析／kernel文本提案能力，不授实现者写权限。原生自由调用和workspace模式在创建protocol前拒绝。配置保存解释器、模型、API URL和凭据变量名，可调整模型上下文及输出上限；SDK和runtime均须精确0.2.2rc2，版本诊断不import SDK或调用模型。

驱动在每调用原protocol目录内建立新home／ID，固定sdk-minimal与公开patch，仅保留所需推理环境和原MCP；追加原schema提示并保存完整native prompt。完整原生事件／终值先保存，Adapter再拒绝非completed、任一tool isError和非严格JSON；结果schema、MCP readiness、未知／取消记录继续由原所有者处理。没有新增数据库／状态机、基础依赖、调度器、上层工具名分支或CI。

独立Standards预核发现ST1：诊断JSON原先Python版本在前，旧regex也不接受PEP440的rc。用真实已安装--check复现其误投影3.12.11，保留red原件；将发行版本放前、原共用regex支持a/b/rc，不加厂商分派。既有readiness测试按实际reported_version参数化，22项通过。组件旧投影测试改为按原工具身份保护旧字段，允许新增工具；矩阵增加新合法配置，基础CLI缺SDK检查也涵盖DeepSeek。新增七个必要接受／拒绝测试，未建立永久真实SDK／模型测试框架。

## P4 已完成的安装与实际入口

源码首轮49通过／6跳过、27.86秒；独立新非editable包452件，wheel／安装RECORD457／462行、原283冻结与当前源码身份通过。构建10.43秒、离线安装5.32秒。基础requirements保持原样，可选SDK仍在独立环境。

实际原CLI的task-mcp正向11.90秒succeeded，十次loopback请求、固定五资源与无额外工具；工具错误段8.95秒failed，原native仍可completed但Adapter拒绝，未发布结构结果。对原run_input的私有native-launch失败注入保留正常preflight，4.09秒failed；有效终JSON被原MCP readiness检查拒绝，未称零模型请求。它有一次loopback，函数入口进程exit0只代表返回失败记录，不能当CLI成功；正向／工具错误段为真实CLI。均保存原run ID、完整输入与事件，拥有服务线程／端口及采样进程清理通过。后续断连、整体超时、完整身份／全文审计与自身／最终独立复核继续。

原r1非editable包七个受影响suite共189通过／7跳过、170.60秒；未借此宣称全仓库或Windows全套。真实CLI断连8.74秒failed，原tool error阻止有效终JSON通过；native15秒调用预算的慢模型段端到端17.36秒（包含preflight／清理），timed_out。五段原State记录、input快照、protocol prompt／附加schema、原scope及资源源文件、请求原body／摘要和native终值均离线核过；正向五份72,162B连续UTF-8读取至null，全部原件相同。五段分别6／6／5／6／6个采样身份无存活，五个拥有端口关闭；未推断未采样进程或新正式六阶段通过。

真实已安装doctor显示0.2.2rc2，installed=true、authentication和task_availability仍not_checked，ST1红／绿证据保持。最终r2仅重打新README元数据，452件产品文件与r1逐字相同；新wheel两RECORD／283及reference verify通过，没有重复既过suite或五段SDK调用。自身模板与完整新独立两轴继续，H2真实网关／同模板候选和H3会话恢复未关闭。

r2独立安装再通过原CLI接收一次受控HTTP500，11.63秒failed／exit1，原native finish_reason非completed，由Adapter拒绝；只有一次推理HTTP请求，固定 `maxRetries=0` 的本次失败没有隐式重试。六个采样身份无存活，拥有服务线程／端口关闭。仍是合成loopback，无真实模型或SaaS调用；五段全文审计不借此扩大为该失败段曾读取完整资料。

原独立评审已按源码及真实red／doctor原件关闭诊断ST1，并独立重算r1／r2两个RECORD、452件源码／安装字节和283冻结身份，确认只有METADATA／RECORD变化；五段原State／input／prompt／scope／request及正向72,162B全文重建通过。上述为分段原件复核，完整切片判词仍待自身模板及最终清单，不记为完整Spec／Standards通过。

## 实际自身模板与最终出口

以已核r2非editable安装实际调用随包结构审查模板，新增审查修订1.0.120只追加本次冻结证据Skill／材料限额。Codex／gpt-6.1-sol／high使用授权回退，159.93秒succeeded／approve，原CLI退出0。二十六份完整源／规格／交付／所有者／审计和结果附件共192,448字节；原manifest→prepared→实际input→prompt／scope／原native终值身份一致，五scope资源全部连续UTF-8读取到null。四个采样所属身份无存活，原list／read没有失败。模型只审阅提供的完整材料，没有独立运行脚本／测试／网络，也没有收到全部原HTTP、SDK历史或包原件；这些原件由另一独立评审核对，不能借模型判词扩大其范围。未宣称双后端成功、H2真实模型兼容、Windows新SDK、完整六阶段或OS隔离。

当前十九份完整公开候选初版静态检查：357个本地链接目标、六个已加载秘密值、私有路径、JSON及diff空白issue0；不检查远端链接、Markdown锚点或浏览器渲染。完整新独立Spec／Standards、最后静态候选及本地出口继续；随后普通提交／推送和本提交自己的既有双OS CI，未提前记为通过。

新的fresh-context协调者及两轴已[终核完整十九件](2026-11-12-harness-probes-review.md#完整十九文件与本地出口终核)，Spec／Standards开放0／0，ST1关闭，本地出口通过。评审独立重算两包／283、五段产品与补充生命周期原件，并从实际自身模板原stream重建全部五scope、二十六附件和原结果，未只采信作者passed字段。源码／测试保持已核r2和模型冻结身份。最后静态、十九件精确Git／Ref与本提交自己的CI继续；不重跑既过产品／模型，不借前片CI。
