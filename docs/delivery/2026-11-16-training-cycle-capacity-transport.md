# c1d M1c-T：现存完整传输边界验证

2026-11-16。状态：定向安装检查**9 passed／150.23秒**，[fresh独立证据范围审查](2026-11-16-training-cycle-capacity-transport-review.md)需求／维护性两轴approve、开放0／0，**M1c-T限定验证闭合**；没有产品或测试修改，不认证完整M1c。[已审分期](../plans/2026-11-16-training-cycle-measurement-capacity.md)保留完整观察／ref／V2及父请求留存义务。此片只验证现有旧transport在M1b固定字节上的行为，不把将来的新wire能力记为已实现。

对象为M1b固定产品提交`67ab9b4e446527fd27a61eff1aa6acb8d24feb01`，相对`bd479050ddd2d9c6b6964f89fe44cfc895273d6b`的完整九文件diff SHA256 `a15d116c62aa3bebb123823a0290479952e2bfee5fb8aced8ede0ce35fee334c`。测试沿同一新非editable SDK wheel `1ed714c885686d134033ac610ac0367fe275288d2ce45b8e6c4f1058dc801292`的实际Python3.12 site-packages，用`-I -B`、无`PYTHONPATH`和冻结测试副本。core／SDK完整包及848／663输入证明复用[M1b交付](2026-11-16-training-cycle-v3-birth.md)，不重新运行已通过的整片回归或模型。

选择现成接缝：

|接缝|可验证的实际范围|
|---|---|
|`test_cycle_sdk_capacity_counts_metadata_and_rejects_without_truncation`|默认SDK DataConverter的完整Payloads含metadata计量，不能以JSON自身合界当作SDK可发送。|
|`test_cycle_workflow_signal_rejections_do_not_poison_the_next_valid_stop`|原V1 sandbox真实signal/query/outcome路径，错误／超限signal之后有效stop仍保持原命令语义。|
|`test_cycle_sdk_capacity_failure_finishes_peers_and_keeps_original_bytes`|实际SDK ActivityEnvironment＋原S/H／reaper，operation-request、oversized-stdout、oversized-frame三参数；peer收尾和已有stdout引用按各自真实情况确认。原operation-request仅确认构造拒绝和peer收尾，**不证明完整被拒父请求留存**。|
|`test_cycle_sdk_branch_construction_failure_preserves_peers_and_complete_reason`|完整分支失败reason保留；能否返回由最终整体容量决定，不截断reason以凑界。|
|`test_cycle_sdk_launch_capacity_keeps_occupied_intent_without_another_offer`|实际大launch材料容量失败仍占原intent，不返还start机会。|
|`test_cycle_sdk_stop_keeps_all_66_real_branch_refs`|原N32 stop的66分支加inspect原件引用，实际SDK完整结果整体编码；不是新v3测量／接受或所有inline unknown组合的验收。|

实际完整argv／cwd／env、日志、JUnit与结果保存于本片ignored `cycle-capacity-transport`，退出码0，**9 passed／150.23秒**，driver151.25秒，无失败／error／skip。上述使用真实S/H与SDK，但remote controller/native业务依赖包含原服务替身；没有启动真实Temporal、训练或GPU workload。原848＋663冻结输入在补验后又与普通合并后的主树逐项核SHA／执行位相同，产品未变；复用既有包与自身模板，不因纯验证／记账重复模型。独立审查仍须核实际assertions与所报范围，不能以绿色JUnit关闭未实施的新边界。

fresh reviewer现已核六函数九case的原argv／结果／JUnit、实际assertions、SDK原wrapper与S/H路径；另独立重算848＋663原输入及117份冻结测试副本全部同一。限定通过只针对本表现存边界，需求与维护性均approve、开放0；没有把`operation-request`构造拒绝当作完整raw留存，或把旧N32全ref当作新v3／任意inline组合。此为证据审查，没有额外重跑测试、服务、安装或模型。

仍开放：真正合法完整observation在M−1/M/M+1／多字节UTF-8／LF／大于1MiB、各原reader合计超M、写入/fsync/deadline/reply loss、真实ref各consumer、V2输入/Memo/全部SDK边界及inline unknown N32、新源与ROOT检查。完整超界父请求原字节留存仍须独立有界监督设计，不能以本片构造异常、另一个operation UUID、error文案或已有历史替代。全部后继接受／collect／native执行与ordinal1门禁按各自计划保留。
