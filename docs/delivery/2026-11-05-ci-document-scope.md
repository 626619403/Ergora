# V5：纯文档push与完整回归分流

日期：2026-11-05。状态：已实施一行workflow配置，本地静态核对及[新的独立审查](2026-11-05-ci-document-scope-review.md)通过；真实触发与精确交付待完成。基线为G0精确`73cd3cee8fe893b9342dcafcf0fa5cf3d9389cbe`；生产代码、测试套件、依赖及352资源保持。

## 行为与边界

原Portability对所有受支持分支push启动双OS wheel/原生回归/Windows安装。现在仅`on.push`增加原生`paths-ignore: ["docs/**.md", "README.md", "AGENTS.md"]`，全为这些文档路径时跳过push工作流；混合运行路径仍触发。`pull_request`和`workflow_dispatch`不加路径过滤，保留完整矩阵、检查名称、步骤及其结果语义。没有额外job、分类器、插件、依赖或变弱的测试断言。

冻结`src/**`中的Markdown、`docs/distribution`的HTML发行源、脚本、workflow、配置及其他未知路径不在忽略集合。默认控制面前端和正式执行器没有变化。PR和手动入口继续全量，避免把同样的路径忽略添加到必需PR工作流；本轮没有通过API修改branch protection或创建真实PR。

GitHub官方[工作流语法](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)于本日读取：`**`可跨目录，`paths-ignore`要求所有路径都匹配才跳过；路径过滤可能让被要求的检查处于Pending，故PR入口保持未过滤。该文档当前说明超过1,000提交或diff超时会运行，超过3,000文件可能受返回文件窗口影响。本片不把本地glob例当成任意大push、复杂rename或远端required-check设置的实测保证。

## 本地验证

使用实际app的PyYAML BaseLoader解析原/新workflow；仅移除新增push过滤后，两份完整配置逐项相等，包括所有原矩阵/权限/步骤/concurrency和超时。六个代表路径例中，公开文档集合匹配忽略，混合源码、冻结Markdown、发行HTML、workflow和未知文件均不匹配。它们只是静态模式例，不替代GitHub真实事件。

原始官方页面/URL/SHA、候选patch与本地核对在忽略的`.ergora/checks/ci-document-scope/`；没有新增镜像实现的生产测试或重跑本地未变全量套件。文档新增G0精确终结记账属于原阶段；下一F6计划仍按已有E1–E6验收，没有提前声称原型或效果通过。

## 交付验收

需要新的fresh-context结构/成本与正确性审查，解决finding后普通推送精确候选。含workflow修改的候选应触发原矩阵，实际run/必要步骤与其源码SHA分别核对。再以仅文档的后续提交观察公开Actions事件窗口，并按GitHub原生过滤语义说明结果；不将API查询失败或尚未出现的run记为永久不存在。

若无法读取Actions或远端设置，明确保留实测范围，不用无权限操作强行配置认证。原公开CI支持子集、G0真实旅程和本片触发验证不互相替代。随后继续F6.1原型；回退是删除这一行push过滤，原测试和执行合同不变。

独立审查已核原7文件身份、完整YAML等价性、256链接及30条实际CLI parser命令，无实现finding。公开Actions REST只读查询实际返回HTTP403 rate limit exceeded（辅助命令exit1），不作为未触发证据；后续改用公开官方HTML观察，不配置新认证。
