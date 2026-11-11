# F7c-C2：按原生 ID 追加候选标签

实现基线 `b5ee397e6571f95393b0f8d6e9ee7e6d947b0935`，分支 `refactor/architecture-foundations`。接续 [C1 评论回写](2026-11-11-issue-writeback.md)和[第一方标签研究](../research/2026-11-11-issue-label-writeback.md)。立片时C1自己的CI43015595781进行中，现已由原评审终核双OS七必要步骤并精确交付；原两份非终态样本保持。C1的通过不能替代本片验收。

## 选择与范围

C2a 先实现 GitHub 的 `addLabelsToLabelable(labelableId, labelIds)`。原 REST 读取将原 issue number／native ID、repository 和既存 label 映射到服务返回的不透明 GraphQL ID；不自行编码 ID。冻结精确单项标签和完整原生 mutation 请求，经操作者确认该意图摘要后发送。名称只是准备入口，不作为写入目标；不创建、移除、替换或按失败后的新名称重新定位标签。正文、标题和模型输出仍不参与授权。

C2b 的[固定版本第一方研究](../research/2026-11-11-gitlab-label-ids.md)已补足完整读取／返回schema及GID证据，但`updateIssue(projectPath, iid, addLabelIds)`没有原issue ID／expected版本条件；原label ID在预检后改成scoped name仍可移除人工同scope标签。严格原子合同当前无法满足，保留unsupported；有限非原子模式没有立项或默认启用。当前 C2a 对 GitLab 标签动作明确拒绝，原评论功能保持，不退回 REST `add_labels`，不称 F7c 已全部完成。GitHub Enterprise 的正确 `/api/graphql` 路径可由原 REST `/api/v3` 推导；schema 不兼容须可见拒绝，不声称跨版本实测。

同一来源、原 creation／run／export candidate 只有一个候选标签追加语义槽。首次准备即冻结 operand；另一个名称不得获得新槽，已有 attempt 更不能通过重新准备、更换 write ID 或更换 SDK 重发。新业务工作使用原任务所有者的新候选身份。标签可以表示本地候选事实，不表示批准、远端发布、合并或工单完成。

## 复用与结构

- `issue_writebacks` 继续拥有准备／确认／attempt／result／观察的单一生命周期，CLI 与 HTTP 共同调用；真实第二种动作需要本域内的窄 action Interface 和局部 registry。C1 已发布 intent／attempt／result／正文字节及 digest 规则保持，按 kind 选择真实合同；不建立通用远程副作用框架、第二账本或调度器。
- `IssueBackend` 本族拥有原 REST 读取、固定认证、GraphQL endpoint、请求和严格返回映射。GitHub 具体实现提供标签能力，其他实现通过同一 Interface 明确 unsupported；上层不按 provider 分派。完整 HTTP 传输复用无 redirect／无重试／1 MiB 上限，具体操作声明预期 200 或 201，不引入两个 SDK。
- 沿原 `tasks.creation / show / export_status`、source snapshot、project revision 和 State 短事务；backup 共用正常 load 校验。C2a 无需新表或修改原 v7／283 冻结文件。发送前比较相关绑定、主体、来源、候选和标签身份，不依赖无关 Agent 配置保持不变。
- 准备和发送前读取的响应摘要是当时事实；网络读后仍有竞态。原 mutation 收据须是完整 200，无 GraphQL errors，回显相符，返回原 Issue／repository，且原响应选中的有限标签页包含原 label ID／名称／所属仓库。nullable／部分结果、错误主体／目标、首 100 项未见目标、截断或结果保存失败均不确认；`clientMutationId` 只作回显，不当幂等键。
- 原 attempt 提交后才允许一次 mutation。未知状态永不重发。observe 只查当前原生资源的一页；命中、未命中、人工删除或空页均不证明原 attempt，不能补足丢失收据。原响应已含目标可确认，不要求把其他所有标签读完；有限页未命中不表示标签不存在。

## 可验收节点

|节点|行为／出口|状态|
|---|---|---|
|L0 定向研究与切片|REST／SDK／ID GraphQL 的第一方依据；区分新增对象、scope、幂等、membership 与部署限制|完成；23 次初查＋8 次 ID 后补 GET，失败保留；不是产品实测|
|L1 单生命周期与 C1 兼容|同域 action Interface／局部映射；原 C1 已保存记录逐字可读、原发送及 unknown 语义保持；不增加 State 表／版本|源码67项／r1安装117项通过，原C1序列化合同保持；自身approve，完整独立两轴开放0／0，本地出口通过|
|L2 GitHub ID 原生协议|原 issue／repo／label GET 映射；同源 GraphQL 路径；变量传 opaque 名称；完整单次 mutation 与只读有界页|原生协议已随源码67项／安装117项检查；完整独立通过，GitLab此动作明确unsupported|
|L3 CLI／HTTP 与故障旅程|新增 label-prepare，共用 status／send／observe；明确确认；并发一 mutation、丢响应／部分 200／删除重建／改名、人工删除后不重发、当前修订变化；原 comment 与 backup 保持|源码67项与r1安装117通过／1跳过；仅本地loopback，不写真实tracker|
|L4 安装、审查与交付|新非 editable 包／两 RECORD／283；必要受影响回归与原生 v7 export→新 CLI；实际自身审查模板、fresh-context 两轴；普通提交／推送及自己的双 OS CI|r1安装117通过／1跳过；最终r2包446／两RECORD／283与r1产品相同、自身256.52秒approve；完整26文件独立两轴及本地出口通过，ST1关闭，93b538f精确26Git／ready及作者SSH Ref独立通过，自己的CI43023048173双OS七必要步骤终核通过，精确交付终结；C1模型／CI不替代本片|
|C2b GitLab 后续|先补官方返回／ID／授权证据，明确 scoped rename／路由竞态及支持合同，再实现相同 Interface|固定版本研究完成；路由／scoped rename无原子条件，严格能力继续unsupported，不称已接入|

标签名称作为完整不透明变量传递，不做 casefold、Unicode 归一化或 CSV 拆分。原生通知、事件和外部自动化可能发生；本工具不承诺静默，不自动补偿人工标签，也不维护互斥工作流状态。删除／替换、分支推送、PR／MR、close／merge 和 F7d 页面／事件继续另片。

每个节点更新[交付记录](../delivery/2026-11-11-issue-label-writeback.md)与 [PLAN](../PLAN.md)。持久原件存忽略的 home 检查目录；公开材料不含凭据或私有环境状态。
