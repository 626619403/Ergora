# 停止并发测试CI修复交付

日期：2026-11-15。独立分支`fix/cycle-stop-overlap-ci`，基线`1b8c2ed1e61258e97f0c39f38ea97a35fe66cd9b`。[计划](../plans/2026-11-15-cycle-stop-overlap-ci.md)限定为测试重叠前提修正，不修改产品、原clock、权威或reaper。

## 准备

原CI为[run43713822317](https://github.com/626619403/Ergora/actions/runs/43713822317)／push／attempt1／精确上述SHA，七job成功，Ubuntu3.11第5组失败。原公开HTML直接记录原双owner通知测试读取`stop-writer`的FileNotFoundError；1 failed、524 passed、13 skipped／998.57秒保持原身份。

已从精确基线建立持久独立工作树，读过原PLAN／交付、目录规则和组件变更协议。现有原b2b非editable SDK安装的652产品文件已与固定Git树逐字重核，全部相同；使用Python3.12.11，区别于远端Python3.11。未安装或修改产品，尚未运行受控复现或修后测试。

调查原件与后续派生证据分别保留，不覆盖原CI日志拒绝或原失败。下一步在仅证据副本控制writer／alpha调度，先实红，再修fixture重叠前提；独立审查、提交、发布与远端新候选CI均未开始。

## 旧fixture受控实红

完整原测试及产品均未修改，只在独立证据fixture副本让writer／alpha H等beta H就绪后再延迟1秒进入各自真实接缝。旧测试实际1失败／29.68秒（驱动31.121秒），同为原2698行读取`stop-writer`的FileNotFoundError。两个延迟H随后确实进入原writer同步／alpha owner读取接缝，原监管最终完成收尾；没有证据要求扩大为产品修复。

本次证明合法调度可以触发与原CI相同的失败；不是重建了原runner的精确调度。原件保留为`original-delayed-r1`，原CI和旧fixture失败均不覆盖。随后仅在原fixture的beta真实通知前补等待两个接缝标记，期限来自原operation剩余clock；修后验证尚未运行。

## 同一受控调度修后通过

候选只修改原`training_cycle_operations.py`：beta在真实pidfd通知之前轮询两个真实阻塞标记，每轮先核原operation剩余窗口，睡眠最多为轮询间隔或当前剩余时间。所有fixture标记先写同目录临时普通文件再rename，避免可见空文件被当作完整事件；beta通知记录也用同一完整发布。原测试正文、预算26／8／3配置和全部产品保持基线字节。

同一产品安装及相同1秒受控调度实际1通过／29.37秒（驱动30.266秒）。文件事件顺序核对：旧fixture的beta通知早于两个阻塞标记；候选中beta H仍先就绪，真实通知记录则晚于两个阻塞标记。原测试继续核通知目标完整身份、两个阻塞进程仍活、各分支unknown边界及最终回收。该检查不靠重排任务或改变产品取得通过。

修后六个适用安装接缝正在运行：原真实双owner、两个原取消边界、冷inspect、缺失当前安装的旧身份通知，以及耗尽原clock不派发。后接原源码正常双owner检查；均尚无终态，独立审查／发布仍待。

## 适用回归终态

|检查|实际结果|覆盖|
|---|---|---|
|精确基线产品的非editable SDK安装|6通过／65.73秒；驱动66.599秒|原双owner正常通知、spawn／helper两取消、冷inspect stopped后的结果读取截止、缺失当前安装时原完整身份通知、已尽原clock不派发|
|独立工作树源码|1通过／29.63秒；驱动30.505秒|原双owner正常通知及真实重叠／完整目标／最终回收断言|

以上使用同一最终fixture，安装的178份测试／示例副本已冻结；未跑无关完整group5。原受控失败和修后受控通过分别保留。后接源码／安装652产品身份、178输入与全部已知actor收尾终核，以及原自身模板；新的fresh-context独立审查由主控安排。当前尚未提交／发布或获得新远端CI。

## 最终本地交接

运行后重新核源码及非editable安装的652产品文件，全部保持精确`1b8c2ed`字节；178份当前／冻结测试和示例同一。两个相关owner的实际导入分别核为源码及非editable site-packages。四次本地检查记录内的28个完整PID／start_ticks／boot_id当前活匹配0，关联本片证据路径的剩余进程0。`git diff --check`及fixture解析通过。

自身原`ergora-structure-review`模板的12份完整文件／360,407B与三份原资源完整进入真实Codex stdin，19.938秒approve；需求／正确性与维护性均未报finding。只认证该完整供稿，不代替独立磁盘原件审查；此后的纯状态收尾未改变fixture。实际回执及结果摘要保持原件。

最终候选为四文件：根PLAN、本片计划、本交付及原fixture；产品、原测试正文、依赖和CI分组零diff。完整patch／SHA清单及所有命令、JUnit、stdout、产品／输入／actor核对集中保存在项目忽略证据目录`.ergora/checks/cycle-stop-ci-investigation/`，各检查用各自名称，原CI响应／HTML保持原位置。主控接续安排新的fresh-context独立需求／维护性审查，随后才决定提交／发布与自己的新候选CI；本片没有自行提交、推送或远端重跑，原失败run仍为failure。
