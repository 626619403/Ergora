# AC3c.3 / CR2b：版本化提交与证据读取

日期：2026-11-09。状态：B1–4本地实现/验证完成，B5独立终核与精确交付进行中。源码基线`c36bcdc028def80429f674d250ee65838d2adc73`；当前HEAD`25d83ec5659e1f189a1ccd50e66cfd18b8d2e2a8`仅增加前片Windows测试跳过及记录。前片双队列worker的实际SDK/文件交换结果不代表正式Agent/候选执行。本片不更改冻结283文件，不新增调度器、账本或协议参数。

## 范围与所有者

将现有WorkflowInput两实现及局部映射移到标准库可导入的reference_inputs所有者，SDK类/Worker/Activities按实际使用延迟导入；离线文件/原始提交状态不因新版本选择强依赖Temporal。原始document和legacy spec保留双身份，统一提供提交活动名、队列、请求根和完整stage context对应检查。调用者不再分别硬编码v1的dev_submit和requests。

原_Submission继续拥有不可变creation→intent→attempt-before-send→memo→原run链。意图spec SHA绑定完整原始document，原cli admission接收同一已核legacy投影，版本所有者负责原读取器/新信封的投影差异，不能给冻结task_spec读取器直接传新wrapper或跳过doctor/policy/claim。公开v2启动与运行状态继续拒绝，直至CR3真实执行桥支持；本片不以内部端口/合成回执开放正式入口。

计划、选定job及closed-run读取沿所选submit名和request root；先核每份context的完整admission等于原始创建信封，再消费legacy spec/任务/摘要/stage。FileAdapter首先验证原注册五个base roots，然后由同一版本所有者构造各自实际请求目录。原批准、取消/未知与完整history语义保持，不允许拿同legacy但不同manifest的history或文件替换。

## 可验收节点

- [x] B1实现：标准库版本所有者与共同工厂，无SDK离线可导入；真实两版本调用者接同一interface。发行/审查状态另记。
- [x] B2实现：原提交身份保留完整document、原cli准入仍使用已核legacy；v2公开保护继续拒绝，旧提交/恢复/attempt/memo语义保持。
- [x] B3实现：计划、job和closed-run真实SDK消息/文件读取按同版本选名/路径，完整admission与原意图绑定；最终R3真实服务/两版本读者与历史重放通过，范围见下方证据。
- [x] B4：源码/最终非editable包/冻结身份、受影响有价值回归及真实SDK协议旅程；合成证据范围明确。
- [ ] B5：新fresh-context两轴审查、实际自身模板调用、普通精确提交推送及必要CI/独立终结。

正式只读review leaf的动态材料、实际Agent调用和可信verify投影归CR3；完整Supervisor栈/原始批准及故障恢复归CR4。SDK合成成功不能代替其验收。

初版已实现标准库版本所有者、完整意图/历史绑定与版本化plan/job/closed-run读取。首轮源码4 failed/139 passed（11.18秒）：静态架构门禁发现input↔workflow循环，另三项原payload测试手工__new__夹具缺新input；原失败保留。已让task_envelopes统一拥有额外context身份谓词与专用submit名，SDK只依赖该纯合同，版本所有者单向延迟载SDK；保留六阶段workflow类的原模块路径和沙箱，不规避静态环检查。手工夹具补真实所需输入。第二轮149 passed/9 fixture errors（14.57秒）：新closed读者复用夹具时漏导入既有converter，且同测试不应同时请求两个共享可变上下文；已修夹具装配与按场景只建一次，未放宽产品检查。新九例及原提交生命周期回归待收口。

后续源码联合158 passed（14.21秒）及新读者九例通过。原提交生命周期76例中75 passed/1 failed（207.52秒）：缺可选SDK时，v2拒绝被`dev_platform.workflow`导入抢先。已将真正提交所需的版本能力检查放在prepare的SDK导入前，读取历史仍可准备已支持的v2身份；不复制workflow_id。修后缺SDK入口/九类读者/架构19 passed（5.49秒）。当前另一组完整提交回归、R2非editable发行与真实SDK验证尚在途，不能沿用旧包身份。

## 最终本地证据

- 原提交/锁/plan/job/closed/original/架构联合源码174 passed（196.04秒）；进程在上述guard修正前启动，缺SDK的修后结论以单独19项及最终包为准。
- R2非editable包368源码/包/安装与283冻结一致，定向152 passed（17.07秒），真实CLI18次/ASGI5次及删源后恢复通过。新的独立审查无P1/P2；P3发现publisher将同一个admission与自己比较而重复计算两次哈希，已删除该可省参数并清理EOF。完整admission仍由unwrap核验，读者仍与原任务比较。
- R3最终非editable包368/283身份保持，153 passed（19.44秒，包含缺SDK入口），再次CLI18/ASGI5通过。R2真实自身结构模板/任务MCP由Codex `gpt-6.1-sol`执行173.70秒，完整53,021字节三页读取后approve；[原始身份](evidence/2026-11-09-cr2b-self-review-identity.json)及[结果](evidence/2026-11-09-cr2b-self-review-result.json)公开保留。它绑定R2，不能冒称R3后续删除冗余的模型重审；该小差异由独立者复核。
- R3真实Temporal/原生SDK旅程16.017秒通过：完整正式创建文档/memo与原始payload绑定，两版本各读取待批准plan的三份材料、选定job已发布receipt及closed-run六份匹配作业；各自队列/请求根、旧worker不消费v2、六阶段原协议、未终结新版取消和五份history重放保持。专用worker和服务均exit0、端口关闭。外部产物/收据/owner是合成协议材料，不代表真实模型或可信候选执行。

原验证探针曾因未配置adapter.json、未指定本地Temporal连接模式或漏传原reader参数而失败；各次原日志/服务清理均保留，修的是探针装配，无产品改动。最后成功材料在忽略的`.ergora/checks/ac3c3-transport/r3/`；真实模型原件在r2。最终新独立审查、固定scope/静态及普通提交推送/自身必要CI待收口，CR3另片推进。
