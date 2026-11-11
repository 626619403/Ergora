# C5c：两个内置开发组合的真实服务验收

基线 `fe45e8ff07c6cb5ec9048b506c03b6dfd4e838b3`；范围及验收见[本片计划](../plans/2026-11-11-composition-runtime.md)。原v5治理REVIEW_READY、原大变更因材料超限BLOCKED均保持。显式v6修正后两个新任务已REVIEW_READY并完成原件交接；真实自身模板、最终独立审查与精确交付继续验收。C5b自己的CI42945800414第四样本Success，独立终核另记，不转授本片。

## 环境准备

新建持久的独立Python3.12环境，按既有reference requirements.lock离线/require-hashes安装23.24秒，再安装C5b最终wheel及现有dev/web/temporal/task-mcp extras，2.07秒。无产品依赖或CI变更，旧环境不修改；最终重叠依赖版本另核，不能把完整环境称作原锁逐包未变。当前运行源码来自C5b最终非editable包，完整439文件/两RECORD及283冻结、最终142发行包与两项目冻结合同身份均已记录。

两域计划复用原public CLI、Supervisor、Temporal、scanner与WorkDelivery。确定性原生命令夹具用于验证协作和证据；真实模型、自身模板审查和全部未验范围分别记录。不会将前片144HTTP、R5的22修正检查或旧AC4真实writer复写为本片执行通过。

## R0与运行开始

独立环境完整439源/wheel/安装文件、两RECORD与283冻结核验通过；wheel保持C5b最终SHA256 `5b0e11fd31baa068a349493e4de9d996d528f3ca5e44d43522b2b894e77fae33`。最终实际142个发行包版本已单独保存，参考锁与当前extras的覆盖关系按实际记录。

两个新本地Git项目已通过原登记入口发布，内置governance/large-change精确1.0.0 preset均已preview/freeze完整manifest，再经原schema-v2预览与create发布v5合同。每writer的显式信任/覆盖和同后端理由均沿原合同，三类审查叶均保留。原活动定义库与原manifest目录已移至保留区，任务运行只能使用原冻结资产。新原生协议夹具通过真实MCP对所有声明资料逐字节读取并比对摘要，夹具读取不称模型理解。

原Supervisor/Temporal/worker/executor/A2A已启动，治理任务沿原run进入inventory/plan；两域运行、证据与handoff出口尚未完成。可信fixture checks实际核Python语法、已生成值和原baseline保持，各检查名由原owner归并同一命令；不声称这等于真实项目的六种独立质量测试。没有修改产品、冻结参考或CI。

## R1断点与同身份继续

首段治理任务实际经过精确plan批准及六阶段，到达`REVIEW_READY`，9份job全部SUCCEEDED、5次独立原生Agent协议调用，原published evidence已验证。随后私有验收驱动把读取回执误定位到原生stdout目录；实际回执按原后端合同保存在该调用的`.protocol`目录，因此驱动断言失败。不是产品或MCP失败；不将该轮整体称为通过。原脚本、traceback及所有stdout/原run/合同保持。

首段finally明确关闭本次服务，67份实际采样身份无存活；数据库和已完成任务保留。续段只从原治理run读取原终态/证据，修正回执路径后补核，再启动原已创建但尚未启动的大变更合同；不重发治理创建、批准或六阶段，也不更换ID。运行产品与同一439文件包不变，续段/清理另行记账。两域完整出口仍待验。

## 续段结果与材料超限

续段103.93秒退出1，原治理run只读补核通过：9个成功job有独立session；5次原生MCP调用实际读取23份资料、7,437字节；每个review核同一candidate、原plan/verification及完整两个writer；重复start返回原run，离线handoff原outcome一致，194事件原Temporal history重放通过。原run `01a1c873-0fa6-7866-b147-d53b0b66dd69`，candidate `d5b8c205903950e4d922d3e1f40f19c9c5810eab`。这些是协议夹具的实际协作证据，不是模型质量证据。

大变更原run `01a1c876-bd9c-785e-a608-ef6bdfa819e4` 在`work:integration-tests`失败并进入BLOCKED，可信fence确认且无未决job；原receipt明确`Composition task exceeds the supported input byte limit`。前三writer及inventory/plan已成功；没有声称integrate/verify/review完成。续段44份实际采样身份全部退出，端口/服务由本次owner收尾；原数据库、失败与先前成功资料保留，没有盲目重启或改写终态。

离线重建原失败stage的输入，3.5869秒以同一错误拒绝，输入1,928,864字节。直接前驱client/server的完整产物表分别478,527/478,540字节，并被同时放入work端口和依赖表；去掉后一副本的单变量尺寸探针为材料JSON 977,107字节（完整task 977,667、全部祖先prompt 980,984字节，低于1MB；这不证明后继review或更长合法链可用）。两前驱自身又包含约191KB的materials与约190KB的prompt，递归携带前一代。原envelope/receipt/业务数据未改，未启动Agent或服务；复现原task摘要`78a019a5664ab57ee6e0a7f828de5ef430dedcc84c53eb1d19e91f15eefccb57`。

原三个假设按顺序为重复表、递归审计、编码放大。当前两个尺寸探针证实前两者，尚未通过修正候选。C6的运行材料问题提前成为本片阻塞依赖；先独立检查版本/数据与审计边界设计，再实施最小候选。原文“当前只有环境准备”已随实际状态更新；两域出口和R3仍待验。


## M0设计审查与M1实现开始

新fresh-context评审者核原109份产物SHA、治理23份完整读取、原history/handoff和清理身份通过；确认B方案设计可实施，并要求控制依赖、非默认profile可信检查及review意见三项边界。规格按“全部声明阶段产物与可信检查/意见”描述，不称完整模型响应。原v2–v5完整审计内联不改，新work-units-v2发布admission-v6并复用原调度算法，阶段材料明确v2/stage-artifacts-v1。

当前源已增加新版本输入族注册、可信结果投影/单来源表和新建页面协议，仍待完整候选验证。探索性首轮源检查129.17秒，3通过/1失败/20未选；新旧创建路由和未内联审计篡改拒绝通过，长链在两个原生writer的MCP preflight失败、monitor124后停止。该轮混用在写源和旧已安装包，不作最终候选证据；原错误保留，不推断这就是超时原因，不扩大生产超时。首次用运行环境no-isolation build因没有setuptools拒绝；随后沿既有离线uv build及独立新环境构建，不修改原运行环境。


## M1候选与R2安装包

沿原离线uv build构建11.78秒，独立环境按参考锁安装23.77秒/当前wheel及extras 2.33秒，最终包SHA256 `aca2ea19761a0011d4b2b10851962733a5f77990dfc4f8e34450ad6901ecf9d5`。439源/wheel/安装及两RECORD逐件相等，283冻结身份保持；没有依赖或CI改动。

该安装包下原测试入口5通过/19未选，pytest94.18秒（外层97.56秒）：v5/v6创建路由、v6四writer扇出/扇入和未绑定端口的控制依赖、未内联composition-prompt篡改仍拒绝、原v5完整产物表与原调用返回保持。随后仅扩展原results用例，加入建议结构审查request-changes→两个必需审查者，pytest42.68秒（外层46.88秒）1通过/23未选，完整可信意见及原FAILED回执传递通过；生产包未再变化。没有额外镜像测试或CI作业。

两个全新v6任务在另一持久安装环境运行，不重启或改写原BLOCKED任务。治理已REVIEW_READY，原大变更场景的新任务进入VERIFYING，尚未声明两域完整出口。驱动非空读取回执只作初步检查；公开“全部读取”结论要以原scope/manifest逐URI、字节、SHA与连续分页补核为准，独立评审亦检查此边界。


## M2 两域原运行出口与读取补核

R2实际服务驱动269.30秒退出1：两个任务均已REVIEW_READY，但大变更收尾把每个review的结果来源误写成全部writer，断言失败。冻结图只将最终integration-tests结果绑定到review，contract/server/client属于完成闭包；治理直接绑定两个writer，故该假设碰巧通过。没有向产品输入偷偷补上游全集，也没有把驱动失败改写为产品失败或整轮成功。原traceback与所有原件保留。

同身份续段只启动原Temporal，未启动worker/executor或再调用Agent；14.62秒外层／11.88秒服务步骤通过，补齐大变更evidence、原ID重复start、handoff和history。治理原checkpoint及已完成history直接复用。两新v6任务分别9／11个job全部SUCCEEDED、5／7次独立native调用，原history分别194／240事件实际重放通过。1,677份原v5的runtime/control/config文件前后摘要完全相等；首段134个、续段2个实际采样PID/starttime均无存活，数据库与全部失败资料保留。

只读读取补核从原admission的完整manifest与资产出发，重新核验每个prepared input的原图和资产身份，再在独立输出目录构造期望scope，全部12份与原scope逐字节相等。fixture的URI集合、完整base64正文、SHA、字节数和连续分页覆盖均匹配，共54份／17,740字节；native成功read次数与回执页数匹配。原fixture页回执只保存offset/bytes/encoding，没有存每个next_offset，不能声称独立看到了原null字段；完整覆盖与fixture停止逻辑属协议证据，不等于模型理解。独立审查者另从原件补核。

治理阶段task为11,445–26,736B、含祖先prompt为14,595–30,631B；大变更task为12,521–26,300B、prompt为15,734–29,617B，其中integration-tests为26,300／29,617B。新版本不再内联递归审计，原FileAdapter全审计I/O保持；两轮Git候选／时间／协议不同，这些尺寸不能解释为受控性能加速或模型质量提升。保存调用分支静态同基线，原v5和新v6的terminal receipt发布后重复返回已实测；本轮没有实测提交后、回执发布前的崩溃恢复，不扩大声明。


## M2 独立复核及公开原件投影

原fresh-context评审者从冻结admission资产、完整prepared graph/input到每份scope与fixture正文独立核验，54份／17,740B、54个UTF-8页、0个base64页全部相等；20个job的154份产物摘要、两份history的原SHA/数量、handoff的SHA/CRC及1,677文件前后保持也通过。这里只说明本轮实际UTF-8范围，不称覆盖二进制分页。C5C-SP1按新v6两域协议旅程关闭，M1-ST1完整读取漏检关闭；PLAN已同步，最终候选仍待同片复核。

已公开脱敏的[运行与失败记录](evidence/2026-11-11-composition-runtime-runtime.json)、[两版安装包及定向检查](evidence/2026-11-11-composition-runtime-package-tests.json)和[完整读取及独立补核](evidence/2026-11-11-composition-runtime-resource-reads.json)先标原字节数/SHA，再明确删字段/衍生字段与路径占位符。完整私有原件保持；未公开大表不冒称已由这些投影证明。当前真实自身结构审查已用这些完整材料与标记投影完成，结果及限制见下节。


## M3 真实自身结构审查

已用实际非editable包的bundled structure-review证据修订1.0.84启动Codex，229.91秒返回approve，Spec／Standards均无具体finding。附件261,486B包含完整六产品源、两测试文件、两规格、实际交付记录及选定原始驱动/回执；包/读取大表的省略明确标记，不冒称这些省略内容由模型逐件检查。原定义库已撤出活动目录但保留，实际input/manifest/native/result及全部五scope身份核符。

模型实际对完整scope逐URI读取；candidate连续UTF-8覆盖到null，原8次base64窗口同offset缩小后重读保留，失败read为0。离线审计确认最终纯文本重建等于全部261,486B，不能把base64窗口本身当模型已理解的文本。全部受保护源未变。原后端自报input_tokens1,922,542（其中cached_input_tokens1,761,536）、output_tokens3,900，单列reasoning_output_tokens1,583；cached已含在input中，reasoning不再次相加，这些不是账单。采样清理只覆盖实见CLI/子进程，无全量短命进程声明。

[真实审查／完整分页／用量与采样](evidence/2026-11-11-composition-runtime-self-review.json)保留原件SHA和投影范围。当前没有新v6页面浏览器验收，也没有回执发布前实际崩溃恢复或不同模型独立性结论；已通过行为不因状态记账重复执行。完整最终候选独立审查、本地出口、普通推送、自己的CI及远端精确身份继续验收。


## 完整最终候选本地出口

原fresh-context评审者已终核完整27份Git候选，Spec／Standards开放finding均为0；C5C-SP1、M1-ST1、M1-ST2全部按各自实际范围关闭。[独立报告](2026-11-11-composition-runtime-review.md)另核439源/wheel/安装及两RECORD、283冻结，五scope共263,137B完整读取、真实结果和四份公开JSON的26条投影均相符。没有重复模型/服务，也没有增加测试或CI。

本地出口再核259个文件/锚点链接、5份JSON、JS语法、六个改动Python文件AST与whitespace通过，公开候选未包含六个已加载凭据值或私有路径。最终非editable原439文件表及wheel SHA与R2完全相同。状态与审查记账只更新本片文档，不另开递归评审。当前允许普通提交/推送；自己的CI、远端精确对象及独立HTTPS同SHA仍待，不借用C5b结果。下一可执行项为C6的容量/材料与分页成本、三域公开旅程，项目整体未完成。
