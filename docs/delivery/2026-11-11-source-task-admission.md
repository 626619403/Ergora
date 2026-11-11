# F7b.1-B1c 交付记录

基线 `6558671f128c320f01785f9b28c673442cf76089`；[本片计划](../plans/2026-11-11-source-task-admission.md)。实现前已核 Input、submission、原 doctor／task_action、sandbox、backend、executor 与原提交故障夹具。B1b 的审查报告后补和精确交付记账属于前片，不继承为本片实现审查。

## 当前检查点

C1 准备已完成；产品原型已备份还原，先完成B1b依赖修正的独立验收和精确交付。准入的唯一变化点为版本 Input 提供的报告，原入口继续拥有授权、连接、占用、提交和恢复。选中 Agent 的配置／程序检查不等于认证或模型消费；C2/C3/C4 尚未验收。没有新的行为测试结果或独立审查结论。

已确认 Codex 实际 command 采用 `options.executable`，原 `executable()/available()` 则固定查找 `codex`；将由 CodexBackend 统一，避免上层按名字补丁。原所有者及 283 冻结发行文件保持。

B1b自己的CI暴露依赖方向失败，C1暂退回准备状态，四份产品／夹具先逐字备份还原6558671。首次source驱动误解引用venv解释器到基础Python，缺pytest而未运行；第二suite在还原源码时尚未结束，已主动中断并明确作混合身份无效记录，任何结果均不作验收。后续使用固定非editable包重验，失败原件保持。
