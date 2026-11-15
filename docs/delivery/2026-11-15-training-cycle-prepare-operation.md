# c1b0：普通准备操作逐步交付

日期：2026-11-15。基线`d1fcfa5b78e912004114f00275c32e6dfac6dcb0`，分支refactor/architecture-foundations。[具体计划](../plans/2026-11-15-training-cycle-prepare-operation.md)先交付SDK总投递需要的原compute∩control有界S-H边界，真实caller为已验的controller意图准备；kernel专家保留v3。

已核`validate_cycle_operation`与`cycle_operation_remaining`、原`_CycleOperation`四任务／取消、S-H唯一reaper、原prepare的本地reservation及既有fault fixture。当前已知mode仅用total，不能用于普通动作；原单次_training_process也不保存同一BOOT窗口。本次只写计划，产品未变；跨重启恢复／实际SDK派发／服务及Workflow未实现。下一步先独立核具体设计，再在原两owner实施并保留实际验证。

独立设计初审指出取消措辞可能误指吞掉原CancelledError；已明确只有超时／有结果的停止观察返回unknown，调用者取消仍沿原shield真实回收后重抛。元数据可残留但不删／不重开clock。源码验收补明阻塞H时的并行asyncio心跳观察。设计终核待补，未改产品。

## 设计终核与实施

新的fresh-context设计需求／维护性两轴approve，开放0／0，R1文档取消语义已关闭。[设计报告](2026-11-15-training-cycle-prepare-operation-plan-review.md)8,307B／SHA256 `642e6c9d67ff4d3df3d020207e3cc27a9dabfedcfdadfdbb5654ea97cf6f9d4d`；其快照只含计划，不批准后续产品。

已在原protocol／worker实现prepare-controller mode。constructor在spawn前固定一次原compute∩control窗口，静态验证原boot／compute上界／control跨度；原compute已尽可保留过去的截止而不spawn。父pipe／wait、S stop_requested与H active均调用同一remaining；H组合原c1a1准备，返回完整typed facts及原意图路径／canonical SHA。停止mode保留原total，cold inspect原观察截止保持，原budget入口／reaper／cycles不改。

复用原fault fixture，在H的State._open阻塞与S匹配stopped后的结果读取阻塞两接缝分别验control先到／compute先到，并在同父loop同时记录阻塞进程仍活、窗口仍有效时的独立心跳；还验真实准备幂等、恶意窗口扩张拒绝、compute耗尽不spawn而stop仍可用cleanup reserve。源码r1与新wheel／两安装r1在途，尚无这些运行终态或产品批准。

## 源码与新安装

源码r1终态24通过／60.55秒（外61.443秒），原完整before／after SHA同一；真实control／compute阻塞、同loop心跳、stopped后结果、耗尽普通不spawn而停止reserve可用及原cold／spawn/helper取消和架构均过。两新非editable core／SDK各652源码／wheel／site逐字，原283/PASS与依赖均过，core无temporalio；只有原protocol／worker两个产品文件不同于基线。

自查新心跳可能在故障marker创建而尚未写完时读取；将原fixture的marker发布改为先写普通pending再rename，避免空JSON被误作产品问题。没有产品变化或新故障主张；r1源码结果保留原测试身份，最终安装冻结新的测试副本并核实际运行。随后自身模板、新fresh-context产品两轴与收尾另验。

## 最终安装、core真实调用与自身模板

同一r1产品wheel上的最终冻结r2测试副本33通过／156.96秒（外158.013秒）：新普通准备／两个阻塞与心跳／计算耗尽及stop reserve、原cold与spawn/helper取消、原总时钟耗尽、c1a1完整准备与三I/O clock接缝、完整父binding、真实双owner独立停止、原完成证据／人工release、SDK-free旧历史及架构检查。178份测试／示例绑定独立清单，不能称一次全仓库或真实训练验收。

真实core安装中实际异步S-H准备1.157秒通过；确无temporalio，父State._open／sqlite3.connect／_load／_read_bytes／protocol.read_raw均被禁止，5原cycle文件、DB rows与原window保持，H仍完成幂等准备。自身原`ergora-structure-review`模板Codex26.433秒approve，16完整文件456,339B及3原资源同一stdin；为所供文本范围，不宣称异后端或替代独立原件审查。新fresh-context产品reviewer已核源码与上述实际终态，最终两轴／原件与已知actor收尾仍待。

## 本地独立终核闭合

新的fresh-context产品reviewer最终需求正确性／结构维护性两轴approve，开放0／0；[产品报告](2026-11-15-training-cycle-prepare-operation-review.md)11,212B／SHA256 `7d1afec0a75967226fc2c4de0576b589434a88fc3feabdda5cb17b2363e1e253`。独立重算最终9文件scope、两安装各652产品、178冻结输入、自身模板及33项安装终态；22记录actor活匹配0。恢复后再次核四份产品／最终测试SHA与报告相同，没有重复构建或回归。

本地验收及独立产品门禁闭合，接续固定本片普通提交；报告之后仅更新状态文档，原产品／测试身份保持。远端仍逐片等前置准确CI／独立终核，不以当前HEAD覆盖前片。下一可实施片为原SDK总投递attempt／唯一start／固定run receipt及对账，先固定实际SDK返回与读写边界；当前准备成功不是执行许可，跨重启恢复、独立服务／配额、Workflow及真实CPU两轮仍未交付。

已固定本地 `3947b1e28b2cbc27ddc53cab584cced0c8d971a6`，唯一parent为c1a1 `d1fcfa5b78e912004114f00275c32e6dfac6dcb0`；十份staged blob与commit tree同一，提交时工作树干净，原产品报告身份保持。私有`local-commit-r1.json`记录完整文件／blob，本片尚未远端发布；后继研究文档不是该固定候选的一部分。
