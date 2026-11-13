# F9b3 训练取消与停止观察交付

日期：2026-11-14；基线 `0d9c0a7a2e0c7d107f3a832fa9492a452df71f34`。[实施计划](../plans/2026-11-14-training-cancellation.md)。B3.1–B3.5本地验收与独立两轴通过、开放0／0；产品 `fad53478c9261157b3016563b410b9d4b4d85b9d` 已普通推送／精确Ref一致，自己的CI `43516776101` Success（8job／30必要步骤），原独立两轴CI终核通过、开放0／0。下文各轮历史进度不覆盖本段。

已核原client的cancel/query/binding、原workflow有界取消、LocalTrainingAdapter的job／fence／poll与executor所有权。真实前片的两个CANCEL_UNCONFIRMED／后来的本地CANCELLED保持，不能改写为同一停止结论。离线SDK可行性探针仅核CancelRequest编码／解码与独立操作标记保留，未发请求或改变产品；实际服务接收／worker行为仍待验。

下一步先收拢现有完整signal history匹配的真实消费者，再实现原run绑定的取消意图／attempt／对账、共享CLI／HTTP及手动页面。F9b2自己的CI与原审查发布终核仍按前片身份独立收口，不借给本片。

## B3.1 接缝与身份实现中

已将完整signal history匹配从Task runtime移入reference history Module，原Task approval／cancellation和原payload测试改为直接使用它，算法不变。第一轮源码 `test_original_payloads`＋架构边界26项通过／1.29秒；此结果只覆盖当时机械移动，非后续取消行为或安装包。开始增加训练专属取消owner，引用原start意图／run／memo，复用原client query/signal、SDK、文件锁与core写入；原runtime状态展示收拢给查询和停止观察两个真实调用者。CLI／HTTP／页面、真实SDK失败场景、安装／服务及独立审查待完成。

## B3.1–B3.5 第一轮源码检查

取消owner、CLI／HTTP、独立取消／停止面板已实现；页面按原提交回执启用，与当前实验详情读取独立。原client继续核binding／发signal，原adapter继续lookup／poll；没有新增runner／fence写入入口。取消记录引用原start，不重复大manifest。共享history算法迁出后Task批准／取消仍直接复用。

源码第一轮四suite共52项通过／130.40秒：真实SDK编码的发送前attempt、单次signal、带marker的原CancelRequest解码、丢ACK／超时、NOT_FOUND／外部同原因／错误marker、完整原input／memo／run冲突、当前spec／runner缺失恢复、已关闭零发送、原CANCEL_UNCONFIRMED与本地CANCELLED分别保留、缺job／QUEUED／RUNNING、CLI unknown退出1与只读stop-status退出0。日志为私有 `source-r1.log`；这是当时源码检查，非最终安装或真实服务验收。页面与手册已补，安装／真实CPU与浏览器、自身和fresh-context两轴仍待验。

## 原生／页面第一轮与窄屏修复

真实Temporal已接收原worker可解码的带SHA取消，直接请求及实际扣住信号ACK后unknown均已记录。页面在当前spec缺失时核原意图恢复，错误SHA／run零POST、双击一次；原prepared继续及三迟到路径（旧request读、跨detail停止观察、跨project真实已闭合not_sent回执）通过。自身原结构模板r1 approve，24完整文件318,975B、42.999秒，全部内联／祖先资源在实际stdin，原result SHA `0798bcdd2ef80eb019652ac49c07df623ed086b00fc06ee1c3a15e4c7120163e`；授权Codex回退，不称异后端成功。

初次布局检查在1440／960通过，在390发现缺spec错误描述中的长路径溢出（scroll477）。失败截图／诊断保留。修复只给训练工作台加局部overflow-wrap，不修改取消／恢复算法；正在构建r2及重验同一原始数据的缺件页面。r1安装回归、真实原history／收尾尚在跑，不作最终完成主张。

## r2最终展示与真实CPU收尾

r2 wheel SHA `6dafb5b7060c631235fa296545a4e14f0133b55a49eb0e48f15a3a550a01407b`，568产品／两RECORD（wheel576行／安装581行）／283冻结均核。相对r1唯一产品差异为训练根class与局部CSS；后端／测试逐字相同。r2页面使用同一控制state／实际取消记录和仍缺失的原spec，在1440／960／390视口及390未发送表单无横向溢出；没有另发信号。原390失败截图保留。

r1真实CPU流程440.370秒完成：四个原run均只有一次start与一个request_cancel；逐项核完整初始输入、原memo／操作SHA、原history和每ID唯一实际run，25份准备件最终逐字保持。原Outcome两个CANCELLED／两个CANCEL_UNCONFIRMED，后来四个本地executor均CANCELLED且无started／训练命令0；原结果不改写。原已结束工作流的额外取消为already_closed／not_sent。原生3个服务、额外r2服务和两个浏览器均已停止；7233与两个随机web端口不监听。最终r2实际 `-S` 无site-packages子进程确认找不到temporalio仍能读取原closed取消记录；初次探针误将整个site-packages加入路径、断言失败的原件保留，修正装载范围后通过，不是产品修复或Windows实测。

r1安装九suite收集155项，在显式600秒上限停止（status=cancelled）；原日志89项逐项PASSED、无FAILED结果，未生成整套成功摘要。保存原中断和精确155项清单，仅将未完成66项移至r2包补测，不重复已完成项；最终分段结果待更新。私有材料：`native-r1/result.json`／四原history／cleanup、`browser-r1`三行为脚本与原输出、`browser-r2/final.stdout`／截图／cleanup、`final-observations.json`、两包identity和`test-partition-r1.json`。没有真实训练／GPU、质量、统计优化或采用主张。

## 最终本地验证与发布前出口

r2仅补未完成66项，**66 passed／278.86秒**；与r1的89个逐项PASSED精确互斥并覆盖原155项收集。r1的600秒cancelled原件保持，不能改写为整次成功；没有为纯展示差异重跑已过检查。原分组5收集成功：351／1804（其余1453 deselected），新suite只登记一次；此命令只收集，不当作执行通过。

完整未跟踪no-index静态核查发现新增history尾部空行；去掉该一换行后构建r3。最终wheel SHA `11cc353a2b0812e9f06503105a5ca69dff1a305eb7321d6961c9d4bc93bbd878`，568产品／两RECORD／283，全部产品对当前源码逐字相同；相对r2只有该EOF字节，原算法AST相同、另567产品完全相同。最终r3再次以实际无site-packages／无Temporal SDK子进程读取原closed取消记录，CLI帮助通过，三监听停止。r2布局与r1真实运行各保留其包身份，不冒称全新r3真实训练或全套重跑。

自身最终展示聚焦r2原模板approve：5完整文件50,537B、23.219秒，全部输入与祖先资源核实际stdin，原result SHA `d6ef2f6be708840cd5104de77886f53af440894f9a8663b38fbdfa9f261dc415`。初次24文件评审与聚焦展示评审是两轮，各自原输入／后端／回执保留；最终EOF格式差异由静态／AST与独立最终核验覆盖。公开范围见[证据JSON](evidence/2026-11-14-training-cancellation.json)，需求和结构两轴报告分别见[需求](2026-11-14-training-cancellation-spec-review.md)／[结构](2026-11-14-training-cancellation-structure-review.md)。普通精确提交／推送和本片自己的CI尚待，后续F9b4准备控制面、F9c精确evidence批准、F9d真实GPU不在本片完成范围。

两位新的fresh-context审查者已对最终r3产品、两轮安装精确分区、真实CPU／页面、自身原模板、25份公开引用原件SHA及完整静态范围完成本地补核，需求／正确性和结构／维护性均通过，开放finding **0／0**。20产品／测试／CI路径组合SHA为 `a58b2a5eba7ec124e2bbe6eefa8202afd5c152e8a02ab7e6dbb73d33a2e779cc`。本地出口完成；接下来普通提交／推送当前开发分支并核本片自己的CI，不自动合入main。

## 精确发布与自己的CI

产品 `fad53478c9261157b3016563b410b9d4b4d85b9d` 唯一父为原基线；35个提交blob与最终静态清单逐字／长度／SHA一致，本片568产品与r3包一致、283冻结保持，完整diff-check通过。普通推送开发分支及完整远端Ref已核；原两审查者固定Git对象的发布补核通过，没有将后续F9b4工作树当作候选。

自己的[CI 43516776101](https://github.com/626619403/Ergora/actions/runs/43516776101)最终官方run HTML为Success。按固定候选Git blob的分组配置核同run官方UI batch、8个job HTML及30必要步骤，全部success，完整SHA的step log路径相符；Windows的原生回归及PowerShell安装／升级步骤也通过。保留前几轮in-progress，不改写为早已成功。原件为私有 `ci-terminal-r4.json`、`ci-run-html-r4`、plan首轮、六Linux第二轮及Windows第五轮HTML；公开JSON另列25份发布／CI原件SHA。原两独立审查者已分别重算并完成CI终核、开放0／0；这只属于F9b3，不代表F9b4、真实GPU或整套未验工作完成。
