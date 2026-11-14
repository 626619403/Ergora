# F9c C3：训练证据审阅与精确批准页面

日期：2026-11-14；基线 `1eef90d7453c64579ddc25bd5a7775eecd20c2cc`。[C1／C2合同](2026-11-14-training-evidence.md)／[精确批准](2026-11-14-training-release.md)。C2与C1换行修正的共同候选自己的CI仍独立核对，本片不借其成功。

## 页面合同

在已有训练实验详情增加局部证据／批准面板，只消费原 C1／C2 HTTP；不修改 Python、API、原凭据或执行／授权逻辑。独立挂载在当前原件读取成功与否之外，当前manifest／runner／archive缺失时仍可读取原批准意图并对账。保持原start／cancel／runtime／prepare入口。

1. 显式读取原evidence／gate／归档manifest、baseline、comparator和artifact索引，完整来源／binding／摘要可展开。声明的artifact内容仍是not_read；无归档、原件错误与容量限制明确显示，不合成训练或质量成功。
2. 用户选原索引内artifact、确认本次完整evidence SHA、填写字符offset／limit才读取一个原SHA核对的UTF-8窗口，可沿原next_offset继续。HTML validity与整数校验拒绝无效指数／非整数；选择／重新读取／切实验或项目后旧响应失效，错误不显示旧正文为当前材料。
3. 本地批准记录独立读取。首次approve须已有本次原accepted archive及原已提交run，展示原身份后输入完整run ID和evidence SHA并显式确认；仅Linux／WSL2提供mutation。prepared／unknown只确认原intent SHA，恢复不以当前evidence读取成功为前提；unknown明确只查原历史、不重发。owner receipt创建unknown与signal unknown分开呈现。
4. mutation期间禁用本面板控件、防重入；丢回复后仅提供读取原批准记录的入口，再明确按原intent恢复，不自动重试或换ID。旧read／mutation结果不得覆盖新实验／项目／home／tab，亦不得清掉当前操作的锁。
5. requested仅投递；展示authorization_status未评价。原integration_ticket.record及原task_id／URL单列；提供现有正式任务页的手动入口，让用户绑定原候选／evidence完成集成复验，不自动创建Task、工单、合并或采用。

## 结构与复用

新增内聚的 `data/console/training-evidence.js`，唯一生产调用者为 `training.js`详情；持有证据／文本／批准面板的完整局部交互，避免把它们塞进原列表／setup／start owner。复用api／ui primitives、原selected生命周期闭包和现有tasks页render入口；不引入前端状态库、通用registry、第二实验状态或checkpoint。原详情的外层read失败仍保留此面板；读取与mutation分开的请求序号只管理展示，不作为业务状态。

## 验收与进度

- 最终非editable包、两RECORD／283与当前产品相符；相关现有回归，不为可见文案重复堆unit tests。
- 真实loopback服务／浏览器：原metadata与Unicode窗口／分页；错误SHA与数值零POST或GET；真实批准及receipt落盘／signal丢回复的显式恢复；缺原资料时原意图仍可读；双击、防重入、旧响应交错／切项目失效；原start／cancel／详情回归；1440／960／390及展开长资料无横向溢出，视觉核截图。
- 原24等准备／原archive／receipt／attempt保持、操作各唯一原signal／原本地票据；process monitor关闭浏览器／web／worker／Temporal及端口。合成归档不代表GPU／训练／质量／性能／真实复验／采用。
- Ergora自身原结构模板、新fresh-context两轴；普通精确发布／Ref、自己的必要Windows／Linux CI与原结构轴终核。C2候选CI终态前不推下个产品，以免concurrency取消。

当前首版已实现，安装／浏览器验收及独立审查在途。逐步更新[交付](../delivery/2026-11-14-training-evidence-console.md)与[主计划](../PLAN.md)；F9d／B3、F10／G1继续另验。

首版局部面板已写：独立证据／文本／批准读序号，显式SHA与run／intent确认、防重入、丢回复读取恢复，父详情读失败仍挂载；原ticket手动任务页入口。未修改Python／HTTP／CI。两JS语法通过；r1非editable包575产品、两RECORD（583／588）与283冻结核对一致；现有web／evidence／architecture回归运行中，实际浏览器待。

## 最终本地检查点

- [x] 局部页面与原owners复用，S1同source读／锁生命周期及无效重绘、可选null修正。
- [x] 最终r4包575／两RECORD583／588／283，源码／快照／wheel／安装相同；33相关既有回归／25.02秒，JS语法。
- [x] 原首三run的批准／两类中断恢复、第四run缺四来源及丢HTTP回复、真实读响应交错、三宽视觉、原ticket手动入口；分别保留r3／r4范围与夹具失败／人工续交互。
- [x] 原四history各1signal，原receipt字节／expiry及24／109原件保持；四sources恢复，四进程组／两浏览器／三端口收尾。
- [x] 最终自身原结构模板10完整文件97,136B／48.701秒approve；README／训练手册实际步骤更新。
- [x] 新fresh-context需求／结构两轴最终本地approve，开放0／0，143引用直接核对。
- [ ] 普通精确发布／完整Ref、自己的CI与原结构轴终核。

迟到mutation／旧finally隔离与home切换只有静态合同核对，旧start／cancel没有本片实际mutation旅程或对应suite；不冒称浏览器全矩阵。完整F9d、真实B3／GPU与后续F10／G1另验。原证据与已验界限详见交付及143引用摘要。
