# F7b.1-B1c 交付记录

基线 `4638c3b9524adcba584a9313b8fd1588b5dde64d`；[本片计划](../plans/2026-11-11-source-task-admission.md)。实现前已核 Input、submission、原 doctor／task_action、sandbox、backend、executor 与原提交故障夹具。B1b 的审查报告后补和精确交付记账属于前片，不继承为本片实现审查。

## 当前检查点

B1b依赖修正4638已精确交付，自己的CI42995785084与原独立终核通过，原655失败保留。本片在该基线上实现所选依赖，r2非editable包身份／283冻结和C1／C2定向结果已核；r1与两轮真实模型失败均按原scope保留，下文分别记录。准入的唯一变化点为版本Input报告，原入口继续拥有授权、连接、占用、提交和恢复；选中Agent的配置／程序检查不等于认证或模型消费。C3最终正向真实混合旅程、完整来源读取、原ID精确本地export和清理均已由独立评审核验；C4最终18文件独立Spec／Standards及本地出口通过，开放0／0、ST1关闭；6a7e9a1精确Git／独立Ref通过，自己的CI43003408859的Linux六例失败；ST2/P2夹具修正与新候选CI待验，不以中断的混合身份source suite作验收。

Codex 实际 command 与 `executable()/available()` 已统一采用 `options.executable`，由 CodexBackend 自身拥有该配置语义，避免上层按名字补丁。原所有者及 283 冻结发行文件保持。

B1b自己的CI暴露依赖方向失败，C1暂退回准备状态，四份产品／夹具先逐字备份还原6558671。首次source驱动误解引用venv解释器到基础Python，缺pytest而未运行；第二suite在还原源码时尚未结束，已主动中断并明确作混合身份无效记录，任何结果均不作验收。后续使用固定非editable包重验，失败原件保持。

C1首个非editable r1 wheel已核445产品／两RECORD／283冻结（SHA938af31014a958e745d13fbc7aa89b8eb5870a6e096351e2d5becc5908aa43c4）。实际安装回归发现缺失依赖错误路径的json模块未导入；原因是B1b把首context移出Input时移除了原json导入，恢复B1c补丁未新增该导入。针对性首失败复现1passed／1failed、32.90秒，明确为NameError，不作正确拒绝证明。已补回纯标准库json，另建r2；r1全套继续以原安装字节运行并保留失败，不在运行期间修改其安装或夹具，不借r1称最终候选通过。

确定性六阶段驱动已启动，先逐字保存旧v6运行数据清单。首次生命周期observer在driver尚未创建log时读取失败，未作清理证明；第二observer已按实际log出现时机等待，原失败保留。

## C1／C2 安装包定向结果

r2 非editable wheel SHA `34c80c6257b7975e607b6a046d8e598c4506378109aa3740c5e6efe69b48ef94`；源码／wheel／安装445包文件一致，两份RECORD（450／455行）及283冻结通过。r1→r2仅`reference_inputs.py`补回标准库`import json`与对应RECORD，未修改r1安装。r2的架构＋来源submission **25 passed／79.53秒**（命令81.37秒），原reference verify通过。

25项中实际运行所选程序／配置检查、七种缺失前置依赖、原policy／共享claim竞争、未知响应后的原ID恢复及input／memo冲突；v7夹具的广域doctor一旦被调用就失败。未选默认implementer／reviewer指向不存在的程序。OS probe在SDK夹具中受控，不能据此证明实际容器；实际运行另见C3。

r1九suite已完整收尾：**8 failed／158 passed／6 skipped，779.37秒**（命令793.50秒）。七失败均为上述缺json；第八为新增SDK夹具在原identifier检查前直接拼路径读取，非法`../escape`先报FileNotFoundError。仅将夹具读取改为原`core.task_spec`复用其slug检查，没有改产品或新增shim测试。r2安装包重验现有legacy boundary案例 **1 passed／57.70秒**（命令64.50秒）。r1的158项保留原候选范围；最终r2仅json导入的产品差异及fixture修正已定向覆盖，不把两次scope拼称完整新包全套通过。

## C3 确定性原协议旅程

已安装r1（不是最终r2）的独立运行，实际Supervisor只启动Temporal／worker／executor；未安装A2A、MLflow、LangGraph，无A2A配置。显式loopback GitHub读取后冻结完整工单，随后关闭tracker并移除该token。原内置治理delivery的两工作叶＋三审查叶使用独立native协议进程；inventory／plan为command夹具，**没有实际推理或不同模型证据**。

原run `01a1c9f7-fcdd-7b8d-8112-fcd414e739b6`，显式批准计划SHA `293f8f57ea10c23078277ce8047d5f4181a9fb52493a4e3fed3d5437d85ddd46`；九个job全成功并到`REVIEW_READY`，候选`e52109ffef3e4169bd1b73fc1a493f861cdf5f62`。重复start保持原回执，离线handoff核验通过；236事件重放SHA `fe8522cf71b86c243d3e43334e42b59b35a723b4dae0c0701946658d4dd42df1`，handoff SHA `b3a727549d31f4016a89c3bb19730f9191ced18ac0bb8da5882546815222ace3`。运行157.60秒／wrapper171.12秒，所属observer采样70进程、无存活，端口关闭；旧v6的2,356原文件前后身份保持。

五个native进程保留4–5份完整祖先资源读取回执（合计7,437字节）；driver已核每个工作／审查materials的完整issue_source等于冻结原输入，以及stage-artifacts-v1的非递归命名产物。实际manifest→input→prompt／回执全链和连续字节页仍待独立补核，不以回执存在或计数代替完整读取。r1成功路径不代替r2失败分支测试；下一步在r2独立运行真实Codex工作／审查叶，再做Ergora自身审查和新fresh-context完整独立审查。

r2独立hybrid旅程已启动：inventory／plan仍为确定性协议，内置两工作叶与三审查叶改为真实Codex；小型provider／consumer源码受保护，只允许新增治理文档与stdlib架构测试。原完整工单中独有的中英marker将与实际prompt／输出核对，祖先资料逐页读取另核；结果未知，未声称全真实Agent或模型质量验收。新的独立评审者已开始审整个B1c实现与r1原件，后续追加实际r2结果后完整复核。

首轮真实hybrid run `01a1ca03-4d6c-7469-9b94-f1517ee9c2de`已以`BLOCKED`终结，183.99秒。两工作叶真实Codex结果成功，但可信检查运行unittest生成`tests/architecture/__pycache__/test_dependencies.cpython-312.pyc`；三项unittest本身OK，原只读检查检测到工作区变化后返回126，可信work回执为FAILED并建立fence。没有放宽原门禁、接管原run或称通过；后续审查／handoff／replay未执行。44个所属采样进程无存活、端口随原shutdown关闭，旧v6的2356文件保持。验收driver给Python检查及其unittest子进程加`-B`，下一独立环境继续用同一个r2产品包，另开新任务／证据，原失败字节保留。

独立review已完成r1五叶manifest→input→prompt／stdin→scope→native回执重建，23次祖先资源交付／7437B与12398B命名依赖产物、每叶完整来源字节相符；这是确定性协议的原件结论，无模型理解或分页压力推断。发现文档ST1/P2两处仍称v7依赖原广doctor；已只更新这两处旧状态，保留升级、预算与旧版本限制，待原评审核准。

## C4 自身模板与独立审查

Ergora内置structure-review的独立精确证据修订已实际运行：run `d8db8ed0df1242feb30e5dc3c7c362c2`，Codex／gpt-6.1-sol／high，144.57秒，原结果`approve`；12份完整附件123194B含三产品、两个变更测试、原submission测试、原生doctor／cli／sandbox／processes和冻结计划／交付。后补公开文档及后续真实旅程不在该冻结判词范围，另由完整独立审查覆盖。

已离线核manifest→prepared／actual input→prompt／stdin→scope／native receipt→原result，五scope资源均以连续UTF8页读到null、失败MCP调用0，四个所属采样进程无存活。附件SHA `a81b19a4529d50f01346ba8a8c6a16dcfbd57b46e8523bda7d07769c3d22a219`，原result SHA `ddedc27d862b9a4e9d3315fc3c082be7c7c6c1546e14852c70b9d4883f305724`。[公开原判词与读取投影](evidence/2026-11-11-source-task-admission-self-review.json)保存实际scope。后端上报input245874／cached201472／output3596／reasoning2297，cached属于input、reasoning单独列出，不重复加总或称计费。

新的fresh-context[独立两轴报告](2026-11-11-source-task-admission-review.md)已写阶段结论；ST1已由原评审核准关闭，当前无开放产品finding。真实混合旅程终态／全部原件、最终完整公开候选与本片精确Git／远端／自己的CI仍待，未标记整片完成。遵循已授权Claude失败后的Codex回退，不声称成功不同后端验收。

## 真实审查拒绝与原任务收尾

仅为验收检查加`-B`后的第二真实run `01a1ca08-99be-7528-811f-e98260ebb3f3`，两工作叶、integrate／verify均成功。structure原生结果为`request-changes`：内置acceptance要求治理图链接架构负责人，示例没有提供owner证据，map只能注明未确认；该拒绝合理，未推断负责人或强迫批准。其他两审查调用被原fence取消，workflow原结果为`CANCEL_UNCONFIRMED`，wrapper289.36秒，81个所属采样进程无存活；不称五叶模型全成功。

两失败run都已只启动其原Temporal，在原ID完成证据、显式reconcile、离线handoff和history replay，没有启动worker／executor或重跑Agent。首pyc失败的216事件SHA `c587ed8ac89ea6b0904112049f270da366181aef55d6bc44e70d01311e69b0bb`、handoff `9fda6d772c7a767c8e982dadb7f4a24b390e855a522aa8311d18c0a2adc6bae8`，15.30秒；审查拒绝的386事件SHA `8b8ab871edb6cb574154a679c31fe73a4c4db9e5efb8116fbb3a27f1dd375f18`、handoff `d772ecf4dae109dec8de5473a65d9f9b9619fe58898615a6ad1c30779a30d66a`，16.62秒。两次reconciled都释放精确原claim，原BLOCKED／CANCEL_UNCONFIRMED逐字保持；各收尾observer只采样Temporal的2个所属进程，均无存活、端口关闭。租约释放和原成功结果明确区分。

下一正向验收由操作者向新的隔离示例提供并保护`OWNERS.md`，明确为Acceptance Maintainer这一fixture角色；原acceptance、完整父链、审查者、预算、checks及r2产品包均保持。新task `source-repository-governance-task-r4`不接管或改写任一旧run，结果另验。[公开验收投影](evidence/2026-11-11-source-task-admission-acceptance.json)逐轮保存实际范围；首真实两writer的8资源／2671B已独立核完整读取，其中一次`list(context)`失败后成功读取全scope，失败没有消失。

第二真实轮的5个native JSONL已离线逐页复算：23资源／7437B全部连续UTF8到null，完整issue_source与冻结原输入、各实际task／prompt／stdin相等；保留两次失败MCP请求及随后的完整读取。只有两writer与structure三个调用有原成功result，并在run元数据附native回执、回显精确来源marker；另两调用读取后取消，run元数据缺native字段且无成功result。独立评审另核两份原MCP native日志均有五次成功read／closed及匹配scope SHA；这些原始读取记录不证明审查完成。审计driver初次假定取消调用也有native字段而KeyError，未产生通过报告；改为记录元数据实际缺失并独立核JSONL覆盖后完成，不制造或补写原生回执。

## C3 正向真实混合旅程及精确本地导出

补齐operator提供的owner资料后，同一个最终r2包的新task `source-repository-governance-task-r4`、run `01a1ca12-9887-7dcb-a7e9-473466c5a600`已到`REVIEW_READY`，九job全成功；两工作叶与结构／正确性／测试价值三叶均为真实Codex，三个独立上下文审查都approve，inventory／plan仍是协议夹具。实际已确认的计划SHA `2ea36f2461e516437fbf96cac866ada059710bbbf07e5c4d36c8cbb509d85f59`，精确候选`51410f67017b9bac5083bb7d9386bafb6ea31f52`。

运行296.78秒／wrapper309.87秒；386事件history replay SHA `876cebdf4fe8b368c21e256303e6d82a3395ae56fdf250a2d41f62e0e569f55f`，handoff `f162f2afea1b0bfcbb6fc83ce17513796ed344845543c13c0a797fc0f5e433d4`离线核验通过，重复start保持原回执。五个原模型调用的23资源／7437B都逐页UTF8到null，完整来源与manifest／input／task／prompt／stdin／原result链相符，五份输出均回显只在来源中提供的完整中英marker；保留四次失败MCP请求及后续成功读取，不把可恢复的错误隐藏为零。MCP动态任务数据当前内联，四次无效资源查找的易用性／调用开销留给后续按实证改进，不扩大本片权限或重写旧模板。87个所属采样进程无存活、端口关闭，旧v6的2356文件前后相等。

随后仅启动原Temporal，按精确run／candidate显式导出到隔离示例仓库的`agent/source-repository-governance-task-r4`，Git分支逐字指向该candidate且原HEAD保持。重复export返回原回执，`lease_released:true`；没有checkout、merge或远端推送。再次核原outcome逐字不变、386事件重放及同handoff SHA；导出收尾18.13秒，2个所属采样进程无存活、端口关闭，没有重跑Agent。正向模型证据仍不表示全真实Agent、不同后端独立性或生产质量；本片默认没有向真实tracker写入。

## 本地出口

完整18文件已由新的fresh-context评审者完成Spec／Standards，开放0／0、文档ST1/P2关闭；最终r4原件、原IDexport及五次模型完整读取均独立通过。提交前再核最终r2源码／wheel／安装445文件、两RECORD及283冻结一致，包SHA不变。普通提交／推送及本片自己的双OS必要CI单独收尾，不借B1b的终态。

## 精确提交与自己的CI

6a7e9a1da1ce13e1035b1f544fa36b9b1a0237d7已普通提交／推送，18个Git对象及模式与ready清单逐字相等；ready SHA `f55c5acdf9641f0f2ac7e2902eae65c05b0dab1e98b73b7df66653f7de0bb3f4`，冻结独立报告SHA `a13cc694c8ec43f58ee2515058a820d771f438bb16c149af8ec05db8d6a41011`。作者SSH Ref同完整提交；原评审精确对象／独立Ref另核。最终静态18文件／138本地链接／6个载入秘密值扫描issue0；只核文件目标，不声称外链或Mermaid运行。

本片自己的[Portability 43003408859](https://github.com/626619403/Ergora/actions/runs/43003408859)已由官方Actions index按完整提交与workflow匹配，首样本In progress；匿名REST403原件保留，没有据此称CI通过或借前片4638结果。该首样本时终态及双OS七必要步骤尚待，实际失败终态见下节。

## CI失败与可移植夹具修正

原6a7e9a1自己的CI43003408859已Failure。按页面matrix身份核，Windows job130464821531的四必要步骤均success；Linux job130464822022的build／reference成功、native regression失败：6 failed／1394 passed／87 skipped／36 subtests，1015.45秒。六例都在新准入报告被实际选中的claude-code审查叶缺程序阻断；原测试只给Codex及inventory／plan提供显式程序，本机环境恰有claude，导致旧本地通过范围未暴露该外部依赖。产品拒绝缺失的选中后端正确，不改准入、不跳过检查、不安装真实Claude以掩盖夹具问题。原HTML目录曾按顺序误贴OS名称，原URL／SHA保持，公共投影按页面matrix和job ID识别，不能按目录推断平台。

原独立评审登记ST2/P2并重新开放该测试环境finding。最小修正只在source_submission的临时config目录提供显式claude→测试Python symlink，将该目录加入该fixture的PATH；仍执行真实后端available／配置和原提交门禁。原Codex配置、选择、测试数量和产品445字节身份均保持。F7c的十份产品／测试草稿已逐字保存并移出当前候选，不混入本次修正。新的安装包定向回归与完整候选复核继续；旧6a7e9a1失败不会改写为通过。

修正后仍用原最终r2非editable安装，以初始`PATH=/usr/bin:/bin`运行同一13项来源submission：**13 passed／69.80秒**（命令70.51秒），fixture SHA `f97f973c56b691c81bbb64ebad2ca8215fe4169cee1d7768a729bf1e0616fae2`。没有复制、增减或跳过原测试；旧本地与CI失败保留。产品／wheel／安装445文件、两RECORD／283再次相等，产品wheel SHA仍34c80c6257b7975e607b6a046d8e598c4506378109aa3740c5e6efe69b48ef94。原自身模型的产品附件保持；这次夹具小改由同片独立评审复核，不借原判词声称它审过新测试字节。完整修正候选与新提交自己的CI另核。
