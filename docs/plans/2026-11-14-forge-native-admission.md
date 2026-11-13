# Forge 原生接入：调用约束与源码身份

日期：2026-11-14。基线 `f4da08b9ff7c1dae92222677a43d8b56b87c78b0`，起始工作树清洁。承接[专家计划 C2](2026-11-13-specialist-presets.md#c2第一个执行适配片的准入设计)，不更换 Forge 的固定版本或原生循环。

## 本轮可验收步骤

|步骤|行为与证据|状态|
|---|---|---|
|C2.0 调用核对|核 judge／teacher／student 的共同入口、原角色隔离、恢复预算及 CLI 辅助模型请求；保存独立源码调查|已完成[只读调查](../delivery/2026-11-14-forge-native-seam-design-review.md)，不是运行准入|
|C2.1 源码身份维护|`kernel.available` 与真实 `_call` 共用源码检查；拒绝包或执行脚本相对 HEAD 的修改以及未跟踪代码。global_config 仍按原 campaign 摘要核定|已实现|
|C2.1 验证|原 pin 的真实 CPU prepare／status，以及修改脚本／新增运行时代码的拒绝回归；隔离 wheel、原结构审查模板和新独立两轴审查|基线两 red、新安装 23 通过／9 跳过；551 产品／两 RECORD／283 通过；自身 Claude 240 秒超时，Codex 回退 37.233 秒 approve，[新独立两轴](../delivery/2026-11-14-forge-native-admission-review.md)通过，开放 0／0，本地出口完成|
|C2.1 发布|普通提交／推送当前分支并核完整远端 Ref；自己的 CI 单独记账|待做|
|C2.2 完整父合同|只有选定的真实执行入口能覆盖所有模型请求、父权限和原绝对预算，才设计冻结合同及可调用子模板|开放，依赖 C2.0 的接缝结论|

源码身份由原 `kernel.py` 所有，driver 的导入／global_config 校验及进程归属保持。不建立新 scheduler、通用 NativeBackend 或第二账本，不修改 283 个冻结参考文件。`available` 的 `installed` 只表示导入位置可用；`version=unsupported` 要能阻止 doctor 将已修改代码视作固定版本。修改错误必须在原生 driver 启动前出现。

新增辅助函数只在原 owner 内集中 Git 身份检查，避免两个调用者采用不同标准；测试复用 `tests/test_agents.py` 中的真实固定 Forge checkout／Python 接口。测试克隆到独立目录，不编辑日常 Forge 安装。源码身份不证明 Python 依赖、环境变量、模型二进制或 OS 隔离；忽略的缓存与本地配置也不因此成为受验工具链。

## 已观察到的约束

普通 teacher／student 和 judge 生成会经 `RealBackend.run_agent`；`FK_CLAUDE_BIN` 可以替换普通 CLI 启动，但不保证同进程子 agent、压缩和辅助模型请求继承完整材料。旧原生角色策略要求实际 shell sandbox，不可因容器限制静默关闭。恢复时 native 内层预算会重新计算，不能将沿用 campaign ID 等同于预算不重置。

本轮一次禁工具、禁 MCP 的真实 Claude 请求已成功；这仅证明该次只读推理可用，不能证明 native policy、异后端完整旅程或全部内部会话。全文材料／附件、真实权限交集、绝对预算、unknown 恢复／停止及外部同候选评价，仍按原 C2 完成条件逐项验收。

进度与原件身份写入[本片交付](../delivery/2026-11-14-forge-native-admission.md)，每步完成后更新。真实训练 workload 尚待操作者选定；不以合成样例关闭 B3。当前容器沙箱探针失败，完整 native 运行片仍需受支持的执行环境；可独立推进原 F8-H2 的真实只读模型兼容验收，不以放松 native policy 迁就本机。
