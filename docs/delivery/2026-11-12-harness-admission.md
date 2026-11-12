# F8 Harness 准入交付记录

产品基线 `784da65da89bdd2fed4742e57e3f904c0f295216`；[本片计划](../plans/2026-11-12-harness-admission.md)。H0研究与固定安装身份、实际自身模板已完成，最终五文档新独立两轴0／0；a35123e十MD精确交付终结；H1a只完成分段loopback探针，尚无产品后端或兼容通过结论。

## H0 启动

已核现有 `AgentBackend` 抽象／局部映射、`Invocation` 及独立可选环境 `data/drivers/mini.py` 先例；基础依赖保持 Python >=3.11。正式组合模式除结果格式外还要求完整资料读取与权限能力，不能把native可运行直接算作正式准入。将按官方源码／文档／包信息核OpenHands SDK与DeepSeek Harness，再确定最小接入范围。D3c提交自身CI独立收口，不借其行为或判词覆盖本片。

## H0 固定版本安装与身份

官方候选为 `openhands-sdk==1.62.0`／源码tag提交 `504a88cab0fb48ee5226238ad7b8f1d865fa84a8`，要求 Python >=3.12。用 `uv venv --python 3.12` 及 `uv pip install --python ... openhands-sdk==1.62.0` 在持久工具目录的独立版本环境安装；实际 Python 3.12.11，共134个固定发行版本，含mcp2.3.0、fastmcp4.1.8、litellm1.105.7。Ergora基础依赖未改。安装步骤退出0，包安装阶段77.94秒；没有导入SDK运行时或调用模型。

独立metadata／RECORD核328件带哈希文件，323件实际分发源码与官方固定tag字节相同；源码目录中6件AGENTS／README文档未分发，逐件保留清单。首身份驱动错误地要求源码AGENTS.md必须在wheel，exit1／无pass记录保留；修驱动只比较实际分发文件后通过，未改SDK。此结果只证明安装身份，不证明构造、工具、会话、取消或Windows可用。

一手源码初核发现1.62.0的会话会追加ambient插件，工具filter不覆盖全部内置工具，stdio MCP还可创建新session；正式受限组合是否可准入须核公开关闭／生命周期接口，不能依据可安装或tools=[]宣称兼容。后台报告继续核来源与DSH选择；目前没有为这些缺口引入私有patch或新的产品选项。

## H0 DSH固定环境与H1a准备

另在独立版本环境安装 `deepseek-harness-sdk==0.2.2rc2` 与 `deepseek-harness-runtime-bin==0.2.2rc2`，同Python3.12.11，共7个固定发行版本。两安装步骤退出0（包安装89.49秒）；SDK／runtime分别11／14个带hash RECORD通过，SDK六个Python文件与官方固定源码 `e8f7b93a344964de3dca1ace9e72b6e4d6de87cb` 字节相同；runtime二进制由该commit构建未获证明。此时尚无SDK执行或模型调用，不称兼容通过。

H1a收窄为私有loopback可测性：每次新显式home／session，sdk-minimal末层patch关闭五个默认工具及DeepSeek官方路由，显式pi-ai loopback路由；先核实际请求工具表与严格JSON结果，再核原进程owner下停止及固定stdio MCP后代。该步骤不改组件目录／后端／模板，不在源码缺口未实测时注册一个看似可选的工具。H0终稿与独立审查另行收口。

## H0 选择与待审出口

[一手研究](../research/2026-11-12-harness-admission.md)已完成，核18次官方GET（17次200、一次404）和两份固定源码、SDK包及MCP依赖原件；研究者没有安装／import／运行SDK，其结论与本交付的安装／探针分开。OpenHands1.62.0保留评估、暂缓受限正式准入：ambient插件无公开关闭入口，默认工具自动追加和MCP新session也不能借配置或现有CI声明满足。下一个候选只选DSH Python SDK的sdk-minimal及固定末层patch，先做H1a，未将它注册到生产组件。

已有AgentBackend／Invocation、结果验证和进程owner可承接真实接口，不另造协议、派工或账本。本地H0出口须等最终独立复核完成，H1a不继承研究的兼容通过结论。

## H1a 已开始的有界探针

首段真实SDK／runtime使用原Ergora进程组owner和独立home／session，45秒整体时限后timed_out，loopback模型请求0；收到原inbox与turn/start，没有终值。SDK的15秒request_timeout不覆盖后续通知等待，与原源码边界一致；根因未判定，不把该失败改写为SDK不可用或配置成功。采样的三个所属进程均无同一存活身份，服务线程停止；它不证明未采到的短命进程或整个MCP后代范围。

诊断续段仅给原生runtime增加公开dsh_bin入口的stderr tee，未改SDK／runtime／patch语义，使用新home／session。实际23.35秒成功，一次本机OpenAI-compatible SSE请求；请求工具表为空、严格JSON及原review schema通过，原session_id与finish_reason=completed已保存。四个采样所属进程无存活，服务线程停止；真实模型／SaaS调用0，usage为合成fixture，不能计为真实用量。此结果只覆盖该诊断wrapper分段；首段超时保留，不能宣称一次无失败运行、原直连已通过或正式任务接入。

第三段回到原始直连SDK路径，使用新home／session，9.54秒成功；一次loopback、空工具表、严格JSON与原schema通过，三个采样所属进程均无存活、服务线程停止。它只新增原直连路径的分段证据，不抹去首段超时，也没有覆盖MCP或真实模型。随后首次MCP探针的私有夹具把JSON末尾换行写为字面反斜杠n，导入时JSONDecodeError；服务及runtime均未启动。这是夹具生成错误，原文件和失败目录保留，不归因于产品或SDK。

接下来只续验固定task MCP全资源／坏工具／断连、慢模型与MCP孙进程停止，再决定H1b产品适配；没有为文档或安装检查重跑既有全套、浏览器或真实模型任务。

## H0 实际自身审查与独立复核

使用随包结构审查模板及原调用所有者，用户授权Codex回退，后端Codex／gpt-6.1-sol／high，修订1.0.117；234.64秒成功，原结构化判词approve。冻结附件含十一份完整文件：本片研究／计划／交付记录、原AgentBackend／agents／processes，以及OpenHands两份和DSH三份关键一手源码。附件333,323字节，SHA256 `a1bfbb57fa51ffa2660fe1529cae97ce202a567ab3210d9c5b690c034c3318f5`；输入、manifest、prompt、原回执及五scope连续UTF-8全文读取通过，四个采样所属进程无存活。后端自报input1,472,345／cached1,350,144／output5,387／reasoning2,191；cached包含在input中，不重复累加或换算账单。

判词只覆盖该冻结架构候选；RECORD／安装原件、其他一手实现及原直连第三段不在模型附件内，其安装、完整MCP、会话和后代行为没有被该模型独立复现。模型明确保留这些限制。第三段及后续记账由新的独立审查按原件核查，不借旧模型approve扩大覆盖。

新的fresh-context协调者及Spec／Standards两轴初轮均开放finding0；已独立核18缓存原件、77固定源码链接／8本地链接、45个引用源码与archive一致，两持久环境实际RECORD及源码身份通过。最终五文档、第三段探针及自身原件／全文审计已由同片两轴复核，开放0／0；[独立报告](2026-11-12-harness-admission-review.md)确认H0本地出口通过。H0没有产品代码、schema、依赖、测试或CI变更；后续MCP探针不在本次H0判词内。

## H0 精确交付

十件Markdown静态检查218个本地目标、6个已加载秘密值issue0；普通提交／push `a35123e4ea3f24b091774f1476c2e159804de560` 退出0／6.79秒，精确十Git与static字节相同，作者既有SSH Ref为同完整SHA。原独立评审离线核上述原件及原workflow，全部十路径命中既有docs Markdown忽略规则，没有本提交产品CI要求；不借D3c CI。评审者一次官方Ref API限流403原件保持，不称独立直接网络成功。H0精确交付终结，后续原生探针与产品决定见[H1记录](2026-11-12-harness-probes.md)。
