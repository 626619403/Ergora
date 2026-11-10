# AC5 C3c D2：资源修订接口纵切片

固定产品基线 `3baa619096a2ff95e2a29aedf179f3c614af103e`，分支 `refactor/architecture-foundations`。先读 AGENTS、PLAN、[C3c合同](2026-11-10-definition-resources.md)及[本片记录](../delivery/2026-11-10-definition-resource-interfaces.md)。D1 r3独立设计复核及C3b自己的CI终态独立核验均已通过，进入产品实施。D3页面会话不在本片。

## 行为与所有者

按C3c D1固定字段实现两类定义资源修订：固定原包历史文件窗口；明确完整字节write、单文件delete、空目录mkdir；完整临时派生；仅预览时建议资源摘要；操作者明确接受完整candidate后原库重新check/publish。现存原文修订入口保持兼容。未改附件/目录/执行位、原定义与旧manifest保持。操作不启动后端或任务，不扩大工具权限。

`DefinitionLibrary` 是完整复制、文件读取、操作、候选/目录身份及原锁内发布所有者；`asset_trees`/原包inspector继续拥有内容摘要、树上限及可移植路径检查；Agent/Workflow已有use case、CLI与HTTP只适配输入。已有两个真实定义消费者，不创建通用patch/plugin/upload/session模块。资源HTTP仍4MB，CLI本地目录与最终树沿原限制。读历史不要求今天后端可用，预览/检查/发布都走今天完整准入。

影响文件：原 `definition_bundles.py`、`agent_definitions.py`、`workflow_definitions.py`、`cli.py`、`web.py`；现有 `test_agent_definitions.py`、`test_workflow_definitions.py`、`test_definition_console.py` 中添加有价值的合同覆盖，不新建测试框架/CI。若需要相邻所有者改动先记录原因。两本公开手册在原条目补可复现CLI/HTTP说明。

## 节点和验收

|节点|工作|出口|状态|
|---|---|---|---|
|I1 固定资源读写所有者|共同操作合同、CLI目录读取、历史有界文件读取、完整暂存及摘要建议|原树/未知附件保留，文字/二进制/执行位/空目录完整；路径/重叠与只读暂存有原owner处理；窗口明确完整性|本地完成；R3安装与三域实际读写/完整树/窗口通过，RIF-1–3独立关闭|
|I2 接通最终准入/发布|accepted_candidate绑定完整文件摘要和目录，原锁内同摘要目录冲突拒绝|preview/check不发布；变更未声明附件/执行位/目录使旧接受失效；同候选显式重试；旧索引/对象不变|本地完成；R3安装与三域实际读写/完整树/窗口通过，RIF-1–3独立关闭|
|I3 两类CLI/HTTP|原revise可选参数、两类file命令、preview/read HTTP与可选body|两类CLI和HTTP得到相同候选；无操作原合同保持；4MB/完整包上限及实际能力错误可见|本地完成；R3安装与三域实际读写/完整树/窗口通过，RIF-1–3独立关闭|
|I4 实际安装与旅程|非editable wheel、原受影响回归、三领域CLI/HTTP资源往返|完整Skill多文件/普通附件/空目录导出再导入；只读文件/目录；历史后端不可用仍可read；新准入失败无发布；旧manifest保持|R1六组191通过1平台跳过保留；R3包435/283、46受影响项19.43秒与三领域81CLI/37真实HTTP49.05秒通过，原对象/manifest保持，三轮服务清理|
|I5 审查及交付|新fresh-context完整实现两轴、真实内置自身模板、两手册/公开证据及清理|实证finding处置复核，所有原红保留；普通提交/推送/自己的必要CI/明确HTTPS分别核验；再接D3|完整34文件新独立Spec/Standards本地终核通过、零开放finding；两轮模板/11公开JSON原件/清理及16文档248链接107parser均已核；普通提交/推送、自己的CI与明确HTTPS待验|

每节点完成更新本计划、本片记录和PLAN；测试只覆盖真实合同与可能的静默错误。I1–I3共同形成一个实现片，不在半接通时发布；D1设计审查不替代I5。冻结283参考文件、六阶段、执行/批准/证据所有者及旧输入格式保持。完整祖先新增/父子提权旅程仍由C3c D4/C3d承担，不把本片附件往返当运行闭环或训练实验。
