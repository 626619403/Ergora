# F7d-D3a：原候选的当前分支观察页面

基线 `c69dedf82512ce87d6a72a249626c26dadca4c3c`，工作分支 `refactor/architecture-foundations`。接续[来源任务页面](2026-11-12-source-task-console.md)及[F7逐项目工单](2026-11-11-project-trackers.md)；D2精确交付已终结，自己的CI43146853654双OS七必要步骤及原评审终核通过，不借给本片。

## 用户行为与所有权

操作者从正式任务的原导出记录进入“观察当前候选分支”。入口仅对已导出的原v7来源任务出现；保留原任务、run、候选及导出分支，明确输入远端目标分支并点击查询后才读取。打开、编辑、关闭或换项目不自动访问工单平台。查询通过原受保护 `POST /api/projects/{id}/candidate-observations`，由 `issues.remote_candidate` 复用 `tasks.exported_source_candidate / inspect_export`、既有provider和修订fence完成读取；页面不分派provider、不验证Git对象、不写新的持久记录。

页面分开显示历史导出、当前本地ref、当前远端head／base、原任务base、逐项比较、每次读取的时间／响应身份及完整安全文本。404明确为不存在或不可见／未知，不能当作相等或未发布。几次独立读取不代表同一时刻快照、CAS／ABA证明、原推送者、正式批准或执行权限。修订改变、来源改绑、凭据及原记录错误沿原owner错误清楚反馈，不能以旧成功掩盖新失败。

目标分支编辑使旧结果失效；迟到查询不能替换新选择、关闭重开后的对话框、别的任务／run或项目。再次查询需明确点击；没有自动重试、轮询、fetch／push、评论／标签、PR／MR创建或执行。已有PR／MR关联和显式写回页面留给后片D3b／D3c；稳定Trigger先确定真实consumer。

## 结构与范围

现有 `tasks.js` 拥有原任务／run／导出生命周期，只增加入口与独立于旧modal内容的调用者存活条件。完整观察交互放在专用 `candidate-observation.js`，以一个入口隐藏表单／异步代际／安全展示；只有一个真实生产调用者，此拆分基于连续交互的内聚性及原tasks体量，不宣称多调用复用。沿用 `api.js`、`ui.js` 与原受保护HTTP；不增加后端、schema、数据库、依赖、SDK、CI或长期测试框架。三旧模板、六阶段和283件冻结参考文件保持。

## 节点与出口

|节点|验收|状态|
|---|---|---|
|O0 立片|核原导出、原v7准入／观察返回和页面生命周期，记录范围／基线|已完成|
|O1 页面|原导出入口、固定原候选、明确目标分支和显式查询、安全完整结果／unknown与迟到隔离|已实现，安装／页面见O2|
|O2 实际验收|新非editable包／RECORD／283；必要原suite；真实安装页面两provider匹配／漂移／404／错误／修订／迟到回复；原合同／导出／快照及零外部写／零执行保持；清理拥有进程|r1安装40／主页面40／生命周期23已验；首夹具失败保留；r2包449／两RECORD／283及最终视口5项通过；125HTTP／49 GET／原资料与拥有资源清理已核|
|O3 文档与审查|入口／使用／架构及截图；实际内置审查模板；新的fresh-context完整独立Spec／Standards，检查结构／冗余guard／test与成本|本地出口通过；自身124.17秒approve／五scope全文，后class／CSS另验；完整20文件新独立Spec／Standards开放0／0，ST1／SP1／SP2记账关闭，冻结前补最终静态身份|
|O4 精确交付|普通提交／推送、精确Git／Ref与本提交自己的双OS必要CI|待交付|

验证可用本地两provider和原生Git／任务owner；如仅控制Temporal SDK并合成REVIEW_READY结果，须明确不是新的真实六阶段／模型执行。原v7夹具的冻结API来源必须保持，不修改旧验收树以伪造新环境。实际模型与独立审查分开记账，不将文档静态或Linux浏览器扩称真实SaaS／原生Windows工作区验收。

每完成节点同步[PLAN](../PLAN.md)与[交付记录](../delivery/2026-11-12-candidate-observation-console.md)。
