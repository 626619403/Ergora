# C5c：内置开发组合的六阶段交付验收

基线 `fe45e8ff07c6cb5ec9048b506c03b6dfd4e838b3`，分支 `refactor/architecture-foundations`。接续[C5分片](2026-11-10-composition-handoff.md)；C5b本地完整23文件独立出口通过并已普通推送，其精确CI/远端续核另行完成，不能转授本片。R0最初复用C5b最终439文件非editable wheel；实际失败后按显式新版本修正规格构建独立v6候选。原v5任务/合同/环境保持，新任务使用另一持久环境。

## 范围与所有者

1. 以现有锁定参考依赖和当前wheel建立独立持久环境，记录最终实际版本；重叠依赖按当前extras解析，不能宣称所有最终包仍等于参考锁。
2. 通过公开CLI统一登记两个本地Git演示项目，安装内置精确preset，执行preview→freeze完整manifest→schema-v2正式preview/create。每writer显式选择原支持的可信执行边界；后端同源回退附理由，不冒称不同模型独立。
3. 治理组合采用两个独立writer与三个并行reviewer；大变更采用contract→server/client并行→integration-tests，再接三个reviewer。原WorkDelivery核分配、传递依赖、全部叶和预算，原Temporal/Supervisor/scanner拥有调度，不增加第二套流程。
4. 两任务均实际执行inventory→plan→原精确计划人工决策入口→work→可信integrate/verify→review。演示批准由验收操作者显式提交，不能用模型意见代替。原candidate/plan/approval/memo/request/receipt/actor身份不变。
5. 核完整祖先资源与工作资料、前驱来源、原可信检查与commit、审查candidate绑定、重复start原run、证据/离线handoff及每份原Temporal history重放。固定任务后撤出活动定义库，验证运行依赖冻结包；保留原包，不删除验收数据。
6. 实际服务及原生命令进程验证协作合同；确定性协议夹具不是模型质量证据。真实模型调用及其读取回执单列；既有C5b页面与AC4真实writer结果保持其原版本范围。训练继续只读proposal，不启动GPU实验。

## 验收节点

|节点|出口|当前状态|
|---|---|---|
|R0 环境和输入|独立非editable439/283及最终依赖身份；两个项目登记、精确manifest和冻结合同；无旧对象修改|离线安装23.24/2.07秒，439/两RECORD/283与最终142发行包记录完成；两项目和精确完整manifest/v5合同发布，活动库撤出并保留|
|R1 两域运行|两种真实Supervisor/Temporal六阶段、精确批准及既有门禁；按原run查询，真实后端和夹具分别说明|治理REVIEW_READY/9job/5调用；续段核完原治理run。原大变更v5在integration-tests因完整输入超限BLOCKED并保留；新显式v6两任务均REVIEW_READY，9/11jobs及5/7次native全部成功|
|R2 证据交接|逐job原件与祖先输入、依赖/完整叶、candidate/检查；重复提交不重跑，history重放、handoff验证；只关闭本次owned服务并记录实际采样范围|原v5治理出口及原失败保持。新v6两域evidence/原ID/handoff及194/240事件重放通过；12次native共54份17,740B按冻结manifest/input/scope/fixture完整补核；134/2采样无存活。收尾私有驱动错误保留，同run补验未再调用Agent|
|R3 出口|两手册/架构按实际范围更新，原证据脱敏；实际自身审查模板与新的fresh-context独立两轴；普通提交/自己的必要CI/远端身份|手册/架构及四份公开证据已更新；原独立SP1/ST1关闭，实际自身229.91秒approve/五scope完整读取通过；完整27文件独立两轴及本地出口通过，开放0；普通提交/自己的CI/远端精确交付待验|

不重复无关取消/崩溃测试，不新增测试/CI作业来镜像驱动。出现真实失配时保留原失败，从原owner诊断并另建最小候选；不放宽路径/预算/权限来制造通过。无宿主权限、GPU或未配置外部平台的范围继续明确标注。C6容量/分页成本及F7–F10/G1仍是后续节点。

## R1发现：运行材料增长，先修后继续

离线按原失败envelope和原producer receipt重建同一work输入，3.59秒复现`Composition task exceeds the supported input byte limit`：1,928,864字节。两直接前驱各约478KB；同一产物同时进入`dependency_artifacts`和`work_inputs`，仅删除前一副本后的材料JSON为977,107字节，完整task为977,667字节、加祖先后prompt为980,984字节；前驱中的`composition-materials`和`composition-prompt`又递归携带旧资料。不是MCP资源读取失败，也不是放大业务夹具后触发的压力测试。

将C6中有实际证据的材料增长问题提前为当前依赖；[C5c-M修正规格](2026-11-11-stage-result-materials.md)选择显式新版本传递全部声明产物/可信检查/意见，审计保持原件。保留原失败任务及v2–v5恢复合同；祖先资源和显式端口数据不得静默截断；不得仅提高1MB上限或减小夹具来制造通过；不能引入第二调度器。独立审查指出并纳入控制依赖、非默认profile可信检查及审查意见三项边界。新候选现已通过两域真实服务协议旅程，范围及驱动失败/续段见交付记录；没有重启原BLOCKED任务。

进度和原失败记入[本片交付记录](../delivery/2026-11-11-composition-runtime.md)，每次状态变化同步总PLAN。
