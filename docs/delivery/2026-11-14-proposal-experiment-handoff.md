# D2-B3a 提案交接交付记录

日期：2026-11-14。按[本片计划](../plans/2026-11-14-proposal-experiment-handoff.md)推进，源码基线为`41dd5aa30f589b5c27a1cc3f09db59d66005a40f`；B2i发布CI和U3安装分别记账。本片只补文档及原产物走查，不改产品或283冻结参考文件。

## 当前状态

已核原baseline／experiment／workload／runner模板、`training.prepare/register_runner`和`perfctl.validate/baseline_ok/gate`：canonical提交在prepare补别名，真实commit必须存在于runner仓库；baseline／workload／比较器匹配，批准合同之后冻结manifest。`checks_required`是非空唯一列表，不强制把模板全部检查用于每个workload；`quality_required`显式，N／A必须为true。runner执行walltime与排队加执行窗口分开。

自由文本提案及原result不自动转实验合同，摘要也不能代替代码／配置／数据内容身份。原source引用和手动追溯可记录于说明表；原validator不会自动核该表或证明实际运行。现有训练手册22／6／6字段说明、B2i四原产物及完整前驱走查、新fresh-context需求／可维护性两轴均通过，开放0／0；资料已随6d4006e普通发布。完整B3仍缺真实workload与实验／独立评价／批准，保持开放。

## B3a.1 手册与B3a.2走查

现有[训练手册](../TRAINING.md#从专家提案填写原实验合同)增加操作顺序和字段来源表，覆盖原experiment22字段、baseline6字段及runner6字段，说明canonical／alias、最终配置／数据／初态、可变检查列表、质量、原比较器与统计、queue-plus-run与walltime、自由文本追溯及人工evidence SHA批准。没有新schema、转换器、运行器或数据库；完整原证据格式仍是权威来源。

复用B2i的四个真实Codex原result，逐项核run／input／result SHA和已保存原native产物；kernel两份及measurement三份完整原前驱仍在其原task中。直接阅读design与measurement的完整响应，保留measurement的request-changes；输入明确是synthetic，缺真实candidate／baseline／配置／数据／初态／oracle与质量。22字段追溯表逐项区分可引用提案与缺失真实身份，没有据此创建experiment manifest、运行训练或批准。八份原模板／执行／gate／比较器／证据格式文件与41dd5aa Git字节保持。

[公开小型投影](evidence/2026-11-14-proposal-experiment-handoff.json)为8,212B，SHA256为`8c216f5f05ce593575320b52d489cf7fa437c3d13098dfb02c02dbfcc76cc0c8`。本片新模型调用0，源码与GPU运行0；真实B3验收保持开放。下一为文档静态检查及新fresh-context独立两轴审查。

文档比例静态检查通过：195个本地目标／14个锚点、4个凭据值、283冻结文件及diff均无问题。未新增测试或运行suite；本片没有产品行为变更。完整候选已交新fresh-context独立评审，尚未以作者检查替代独立结论。

## B3a.3 独立审查

[新fresh-context报告](2026-11-14-proposal-experiment-handoff-review.md)已核六文件完整快照、所有原result响应、四input树／task／prompt／run／MCP原件与两处完整前驱，八源与283冻结、相关23本地目标／10锚点和diff通过。需求／可维护性两轴通过，开放0／0，无必要修正。报告6,101B，SHA256为`7252a86848f9f8db9e8646d365ebd1b6eeca71f0eac8cd70e2a0c25c08454d80`；作者较宽工作树的秘密值检查未冒称独立重读。资料本地出口完成，普通发布仍待做；完整B3真实项目与实验链保持开放。

## B3a.4普通发布

本片已审资料随十七文件文档提交`6d4006e4cde609da90a97b88f0ce871923385c9f`普通推送，父41dd5aa；最终快照manifest SHA256为`4b00445fb6fc14e9b2d955d99909d786d1822321a63320d2d71fdcd82f18140d`，staged与Git blob逐项相等，push退出0、作者完整SSH Ref核准。文档比例静态208目标／17锚点、4凭据值、283冻结及diff通过，没有新产品行为、依赖、测试或CI改动，不声称文档自己的完整CI通过。B3a资料交付完成；真实B3实验与C2接入保持各自开放范围。
