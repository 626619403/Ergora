# Linux CI：完整覆盖、独立进程与可中断观测

承接[原CI状态及有界采样](../delivery/2026-11-13-publication-status.md)和[独立成本调查](../delivery/2026-11-13-linux-ci-profile-review.md)。应用基线为B2c普通提交`d2dac8d`；本片只改CI选择／观测和维护说明，不改变产品、测试语义、冻结参考、运行owner或依赖。

## 已有事实与待定项

原精确00922远端Linux在整个job的20分钟上限取消，Windows四步骤成功。原Linux3.11采样在4500.222秒固定边界停止：1696 collected、1463完成teardown、233未完成；已记录4489.013秒phase成本，九个research失败保留。最慢完整文件是task export约586.729秒，其次reconciliation约542.369秒；不能把这些数字或末条位置当成远端死锁证据。

来源抓取首case的紧凑red／green定位到自定义计时主模块缺spawn入口保护；同产品／解释器的整个research模块两种正确入口分别11通过／1跳过。原九份终态trace没有写出，不能凭补测补造原trace。233未完成原nodeid已沿独立pytest入口续测，227通过／6跳过／36子测试通过，退出0／393.593秒。原1696项的分段并集相等、交集0；去掉未完成setup及重复子报告后4875.574秒，75文件按整文件贪心平衡成六组，估算各812.58–812.63秒，低于900秒工作目标，保留20分钟上限内安装／上传与波动余量。完整成本见[公开投影](../delivery/evidence/2026-11-13-linux-ci-costs.json)。这些分段数据是覆盖／成本证据，不是一次连续全suite成功。

## 最小实现

1. 增加CI所属的pytest plugin，保留`python -m pytest`主入口；即刻写完整collection、实际选中nodeid及setup／call／teardown起点、耗时、失败正文和终态。硬终止后缺finish仍为incomplete。已用研究模块、受控失败和实际中断证明独立入口及落盘接缝，不在产品中新增监控器。
2. 以显式JSON文件清单按实测文件成本分组，保留整文件内的顺序／生命周期检查。plugin在完整collection后选择一组，拒绝重复分配、未分配的已collect文件、失效路径、越界组和空选择。新的测试文件需在一个JSON清单登记；不会静默落在未执行范围。分组数量由该JSON生成CI matrix，新增／移动组不同时修改Python分派和workflow固定数字。
3. 提取原workflow的pytest启动／日志和annotation到小的CI脚本，供workflow与本地重跑共用；保持wheel安装接缝、原Linux五个suite选择、Windows tests＋contracts及PowerShell5.1安装升级。每组独立runner／State／进程，不引入xdist或删除故障／恢复测试。job上限仍20分钟；分组余量由完整测量记录解释，不能只增期限制造通过。
4. 每个job上传已落盘的request、完整stdout、phase／coverage和JUnit；`always()`不保证job硬截止后仍能上传。真实依赖／平台skip原样保留，记录collect跳过与失败；不把cancelled或缺原件当作green。

## 可验收节点

|节点|出口|状态|
|---|---|---|
|CI1 完整成本|原全部1696 nodeid的终态phase或明确incomplete；分段／失败保留，每文件成本和未完成项可定位|完成，保留原失败／截止，非连续suite通过|
|CI2 选择和覆盖|新候选完整collection与各Linux组并集相等、交集为空；未知文件／重复组等可达漏测错误明确失败|正式脚本／plugin／六组已实现；新候选1708全集＝六组并集且交集0，重复／漏登记／越界负向均明确退出4|
|CI3 运行接缝|非editable Python3.11；原research模块、代表性生命周期／新方向检查通过；受控失败和中断观测真实保留|非editable521／两RECORD／283身份核准；代表检查r1为31通过／5跳过57.86秒，wrapper修正后r2同结果58.00秒／103phase全部有起点；正式fixture七探针达预期：失败exit1／正文，中断cancelled且无finish；旧夹具失败保留|
|CI4 审查与精确发布|自身原结构模板、fresh-context Spec／Standards；普通push／精确Ref，新候选自己的全部必要job和步骤终态|修正后自身原结构模板48.881秒approve、六全文／实际输入核准；完整12文件及全部原件新独立双轴通过，Spec两P3关闭／两轴开放0，本地出口完成；精确发布／自己的CI开放，不借旧Windows或其他候选CI关闭|

原pytest用例和283参考文件不变。源码／配置改动以本片明确差异为准，真实CI结果仍由自己的精确候选核准；原00922 Cancelled、两次被截止的采样及其失败范围继续保留。完成后更新本计划、[PLAN](../PLAN.md)和本片交付记录，再接续后续优化方向。
