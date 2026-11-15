# 停止并发测试的明确重叠前提

日期：2026-11-15。独立分支`fix/cycle-stop-overlap-ci`，精确基线`1b8c2ed1e61258e97f0c39f38ea97a35fe66cd9b`。本片是原发布CI的测试修复，不接入主工作树的后继产品。

## 原始问题与边界

[原run43713822317](https://github.com/626619403/Ergora/actions/runs/43713822317)的Ubuntu3.11第5组终态为1 failed、524 passed、13 skipped；唯一失败为原双owner并发停止测试读取尚不存在的`stop-writer`标记。原测试只等待beta通知，而writer和alpha各自的真实S/H没有先到业务阻塞点的保证。公开HTML确认失败位置；其具体调度仍需可控复现。

只修原fixture在beta真实通知前的重叠前提及必要诊断，不修改产品、授权、原clock、reaper或显式CI分组；不靠单纯增加固定sleep或在通知后补等标记声称重叠。原通知目标完整身份、blocked writer／alpha仍活、unknown边界及最终回收断言保持。

## 可验收步骤

|顺序|动作|完成条件|
|---|---|---|
|1|冻结固定baseline、原失败和现有非editable安装身份|完整产品652文件与1b8逐字相同；原CI失败保留|
|2|仅证据副本延迟writer／alpha进入真实接缝|旧fixture在beta先到的合法调度下实红；记录失败位置和所有actor收尾|
|3|原fixture在beta真实notify之前等两个真实阻塞标记|使用原operation剩余窗口；缺标记明确失败；不续发或延长原budget|
|4|同一可控调度及正常双owner场景验证|真实目标身份、重叠和最终回收断言均通过|
|5|适用原取消／耗尽／冷inspect／旧身份接缝回归|源码和匹配baseline非editable安装分别记录，不跑无关完整第5组|
|6|完整candidate、原件身份和收尾交接|主控安排新的fresh-context独立审查；本片不自行提交／推送／远端重跑|

若可控复现暴露超出测试顺序的产品问题，先回报主控，不扩展产品修复。完整堆栈／CI工件可补原现场信息；API限额前不重试。自身模板及独立审查仍须保持实际覆盖，不把本地新候选认证给旧失败run。

当前状态与每次实际结果见[交付](../delivery/2026-11-15-cycle-stop-overlap-ci.md)。
