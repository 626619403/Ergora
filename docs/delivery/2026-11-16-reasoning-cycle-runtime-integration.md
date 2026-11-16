# 逐Agent推理配置与训练服务生命周期联合验收

2026-11-16。当前实施／验证中，未发布。源基线 `eba86805e5d50824eefb5e69edd0faab099cbf42`，联合产品 `c540939d3b3f38f3851b0de965c9cd0f969eea77`，独立固定树 `reasoning-cycle-runtime-integration-r1`。本片不修改产品或扩大执行范围，仅核普通合入后的同一包、必要接缝和发布身份。

## 范围与原审查

- [cold fixture修正](2026-11-16-schema3-cold-fixture.md)产品 `e3a4369`，只修旧测试的显式版本，保留生产拒绝与无副作用。
- [逐Agent推理配置](2026-11-16-agent-reasoning-options.md)产品 `0dcbc20`，源码fresh两轴approve／0；原模板Claude超时、Codex回退approve。配置经原组件、完整binding冻结与各后端原生命令投影；正式DAG持有并行与祖先配额。
- [V2a服务生命周期](2026-11-16-training-cycle-v2-runtime.md)产品 `82c6595`，准确r3源码fresh两轴approve／0、新安装65＋6通过与core六skip；原模板Claude超时、Codex回退approve。四SDK poller共享两业务许可，正常路径完整drain；外部直接终止SDK run保持incomplete／unknown。

上述普通合入没有冲突修正或新增产品逻辑。其各自通过保留原身份，联合安装仍需本次实际证据。S1项目登记修正版仍在独立作者树，本包不包含它；V2b最终SDK容量、真实服务旧queue正向、完整M1c、真实CPU／GPU质量及通用Repeat／混合画布均在后继。

## 验收清单

- [x] 固定联合HEAD与2,071项原输入；完整基线差异SHA256 `db1a7646801071506aa69d81db39a6ed7bd5334c324b59b120a25e844457b6db`。
- [x] 从该固定树构建新非editable wheel，SHA256 `630fae78261a7718f7289bd1337ca5fd6dda8eb7c6c5773750e14ae0b36f2ce2`；core／SDK各668完整包内容及执行位与source／wheel同一，三训练owner实际从site-packages导入，283参考及依赖逐项通过。core无SDK，SDK为1.34.0。
- [x] 复用原定向接缝，**33 passed／34.808秒**：实际两CLI参数传递、配置优先级、Agent版本／正式任务冻结、异后端并行／祖先配额、SDK服务生命周期与实际S/H共享许可、显式schema3 cold拒绝。整批runner36.278秒，80个捕获的自有进程身份在结束后均absent；不外推全系统。没有重跑无变化的完整业务／GPU套件。
- [ ] 更新计划、普通提交／推送开发分支，核精确远端及本候选自己的适用CI；不自动合main或强推。

私有原件位于 `.ergora/checks/reasoning-cycle-runtime-integration/`。安装不修改用户运行home，不启停其他owner服务或业务项目；凭据只引用环境。源码、安装、受控SDK、真实服务、业务质量和CI分别记账。

## 产品组合核对

相对公开源基线，本包恰好改变 `agent_backends.py`、`data/components.json`、`reference_training_worker.py`、`task_envelopes.py`，新增／删除包文件均为0；与两已审产品及普通合入差异相符。新安装测试输入来自同一固定树，原argv、JUnit、raw、包比对与进程身份分别保存在 `package-r1/`。该机械组合不增加产品分派、接口、表或新的执行能力；各源码独审与自身模板结果保持原报告身份。
