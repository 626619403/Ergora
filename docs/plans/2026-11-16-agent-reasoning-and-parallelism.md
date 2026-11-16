# 逐 Agent 推理设置与并行能力核对

2026-11-16。用户要求核对并补齐各 Agent 的思考强度选择与流程图并行执行。准确基线为 `eba86805e5d50824eefb5e69edd0faab099cbf42`；源码在独立 `agent-reasoning-options` worktree 实施，不与设计登记及训练服务片混写。

## 已观察的能力与缺项

- 原 `reference_workflows`／Temporal 拥有正式 review 与 work-unit DAG 调度，独立叶子有各自的后端绑定；项目与所有祖先 concurrency 配额同时有效。原 `tests/test_parallel_reviews.py` 已有实际等待／释放／峰值与窄子树测试。
- 原 `agent_backends.CodexBackend._options` 能读取外部 TOML 的 `model_reasoning_effort`，但 `data/components.json` 中 Codex／Claude 的公开 binding 没有对应字段，定义和表单均不能逐叶选择。
- 独立 `composition run-input` 只调用一个显式叶子，不执行整个图；通用混合图、硬性脚本／人类节点和一般 Repeat 继续沿原实施计划，不借此宣称已完成。

## 本片实现合同

在原组件配置中增加 Codex `reasoning_effort` 和 Claude Code `effort` 可选项，由各后端适配器投影到自己的原生命令。缺省不增加参数，保持已有配置和已冻结记录；显式 Codex binding 覆盖外部推理配置。不同后端的同名等级不承诺相同计算量，也不自动改变模型或降低请求强度。模型／账户／CLI 的真实支持由原生后端决定；原日志保留请求与结果，配置校验不冒称已测实际应用强度。

原 binding 表单根据组件 schema 渲染选择器；Agent 定义、工作流编译、正式冻结和原 invocation 继续保存完整 binding，不新增转换层、状态表、scheduler 或全局默认。不改已发布 preset 包或参考原件。其他后端不接收未实现的推理字段。

参数依据：已获取 [Codex configuration reference](https://developers.openai.com/codex/config-reference/)、[Claude CLI reference](https://code.claude.com/docs/en/cli-reference) 和 [Claude model configuration](https://code.claude.com/docs/en/model-config)。Codex 等级随模型／客户端变化；Claude 文档还明确组织 cap 可由 CLI 限低实际等级，JSON 模式警告可能只进 debug log，因此本片只保证传入明确请求，不能保证服务实际使用同等级。原网页、原生 `--help` 和版本只读检查在私有 `.ergora/checks/agent-reasoning-options/` 保存；不公开机器状态或凭据。

## 可验收节点

- [x] A1 核原接口、真正并行 owner、官方配置和现存能力。
- [x] A2 原组件 schema 和两个后端适配器完成可选字段；正式历史 binding 的原结构 reader 允许完整新字段，不改上层分派。
- [x] A3 源码45过／8原ForgeKernel与mini-swe可选依赖 skip；原13个并行节点已全部通过，覆盖异后端不同强度、祖先配额／窄子树／取消。原实际CLI进程、外部配置优先级、Agent修订及正式任务冻结已验。后继另环境8项是重复并行验证，不补齐上述skip、不计新增覆盖；独审已指出并据原JUnit更正。手册、原项目页面保存／重开及API读回已验；正式任务组合selector未在此浏览器片验证，真实应用等级另验。
- [x] A4 新 fresh-context 两轴独审approve／0；原模板Claude超时保留，按原授权Codex回退68.049秒approve，完整stdin／原结果及身份见交付，不称异后端成功。
- [ ] A5 已普通合入开发分支 `a2655c3`；待联合新安装、推送并观察准确候选自己的适用 CI。不自动合 main。

后继设计关卡、真实训练循环、可信脚本与一般 Repeat 不在本片内。每节点完成更新本页与根 `docs/PLAN.md`。
