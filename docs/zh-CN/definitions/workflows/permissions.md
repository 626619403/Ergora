# 完整继承与冲突

简体中文 · [English](../../../definitions/workflows/permissions.md) · [文档目录](../../../README.zh-CN.md)

每个叶子按 root→parent→自身的顺序拼装全部祖先 Skill 指令与上下文，以及各层初始指令。组合模板本身不额外调用模型。预览给出每份正文、内容身份、全部来源、完整拼装正文和 SHA；Skill 的必读正文是 `SKILL.md`，目录里的脚本和其他附件仍属于按需资源。

相同逻辑资源ID对应不同内容或种类会拒绝。同名Skill按实际frontmatter加载名称检查，不同树拒绝；同名同树可合并，但保留全部逻辑ID与来源，并检查每个来源都可读。不会用最后写入覆盖祖先。兄弟和前驱的Skill不会成为继承材料，前驱只有端口数据；重复引用不共享可变会话。

静态材料完整交付预览不证明模型理解、遵从或已实际读到。实际调用固定原实例和本次任务正文，再检查完整输入容量并保留装载证据；不足时拒绝，不静默截断。正式`dag-v1`按其封存版本加入明确绑定的前驱产物（v6为上述声明产物与可信检查/意见）；单独`run-input`仍只调用一个叶子。

## 权限路径和预算

预览grant文件使用 schema 中 `$defs/grant`：`schema_version: 1`，以及完整 `permissions` 和 `limits`。示例 [preview-grant.json](../../../../examples/composition/preview-grant.json) 供演示，操作者应按自己的项目收窄；它目前只是显式静态输入，没有与项目配置或正式批准相连。

|权限字段|精确语义|
|---|---|
|`read`|可读逻辑子树数组，如 `workspace/src`、`definitions/agent/architecture-reviewer/1.0.0`；`definitions`代表整个定义资产库。|
|`write`|可写工作区子树数组，如 `workspace/src`；不能向定义库声明写权，写权不隐式授予读权。|
|`shell`|是否请求运行子进程；Skill脚本不凭其存在获得此权。|
|`network`|精确规范 HTTP(S) origin 数组，如 `https://api.example.com`；主机须为小写ASCII DNS名（国际域名使用punycode）或IP字面量，IPv6使用压缩形式，默认端口省略；不接受路径、凭据、查询、fragment、空白或通配符。|

路径使用 `/`，按大小写敏感的路径段包含判断，不能用 `workspace/src` 授予 `workspace/src-other`，也不接受 `..`、宿主机绝对路径或 glob。逻辑 `workspace` 预留给待执行的项目工作区；`definitions/{agent,workflow}/ID/VERSION/path` 表示精确包资源。它们不是当前操作系统挂载点，不会由预览自动创建或强制执行。

根请求必须在grant内；子工作流的请求不得越父级；Agent节点不得越所属工作流。每一层都检查，因此传递地满足全部祖先。每个必读资源的全部来源路径必须在当前实例的read内，Skill需要整个目录可读；收窄后读不到祖先材料会失败，不会丢弃材料或偷偷提权。预览中的 `backend_request.sandbox` 只是后端请求，不能覆盖此链，更不证明OS隔离。真实 `enforced/advisory/unsupported` 装载矩阵见[调用前能力检查](leaf-calls.md#调用前查看能力与权限)。

`limits` 四项都必填，拒绝布尔、浮点与超出支持范围的数值：

|字段|计数与支持上限|
|---|---|
|`depth`|根深度为1，每个结构节点再加1；每个子树重新从1计其局部深度，但所有祖先及项目深度仍同时检查。最大16。|
|`instances`|包括根、每次Workflow引用、每个Agent和all-join，重复引用逐次计数；每子树及全局共同约束。最大512。|
|`concurrency`|各结构作用域的共享并发配额，叶子预览列出全部作用域。正式并行审查同时遵守项目和全部祖先作用域上限，等待窄子树的分支不占用祖先配额。最大64；独立叶子调用不调度整图。|
|`material_bytes`|所有叶子完整静态prompt的UTF-8字节总量，包含来源标记，重复调用分别计算；每子树和全局共同约束。最大1,000,000。未含未来端口值。|

这些是有限静态格式的硬上限，不是性能、模型容量或任意并发可运行的承诺。使用更小的项目或子树限额可在编译时拒绝超限组合。

独立分支可以选择不同的后端、模型及[思考强度](../../agents/backends.md#为每个-agent-设置思考强度)。例如在正式任务的 `composition.backend_overrides` 中分别设置：

```json
{
  "root/structure/review": {
    "binding": {"tool":"codex","reasoning_effort":"high"},
    "reason": "结构设计审查采用较高推理强度"
  },
  "root/correctness/review": {
    "binding": {"tool":"claude-code","effort":"medium"},
    "reason": "正确性审查使用独立后端"
  }
}
```

路径须对应本次 manifest 的实际叶子，所有后端均须通过该模式的能力检查；使用任务页面的组合配置可生成相同 binding。正式审查和 work-unit 运行器会按依赖就绪顺序及共享配额启动分支；执行者与审查者的异后端策略继续按原 `diversity` 配置检查。`composition run-input` 仍只调用一个叶子；任意混合节点和一般 Repeat 的执行范围另见实施计划。

这些显式逐 Agent 等级保存在精确定义和冻结任务绑定中。请求值、投影到原生 CLI 参数／配置的值，以及实际观察到的原生值是不同事实；没有原生证据时，实际应用仍为未知。统一 fixed／preset／planner／automatic 调优选择仍是后续工作；已有工作流 preset 不实现调优 preset。等级／模型回退或预算增加都不是隐式动作。各模式限制见[后端手册](../../agents/backends.md#为每个-agent-设置思考强度)。
