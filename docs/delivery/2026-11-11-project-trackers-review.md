# F7a：逐项目工单读取独立评审

日期：2026-11-11。主评审 `/root/f7a_project_issues_review`，Spec 与 Standards 分别由新的 fresh-context 子评审完成，先读用户原需求、[F7a规格](../plans/2026-11-11-project-trackers.md)和实际变更，再读作者记录；没有继承原模型判词。基线与当前HEAD均为 `0252dec5c41be1c1f6f533d86d8f32d30d178ce3`，分支 `refactor/architecture-foundations`，本片是未提交工作区候选。

已核最终27路径：9份生产源码／配置／schema、3份测试，以及README、INTEGRATIONS、PLAN、USAGE、两份当前架构文档、C6d计划／交付／原评审增量、F7计划／交付／研究和两份公开证据JSON。精确路径／字节见私有 `final-r1/index.json`，SHA256 `8cd4a078157230dba022f4501fe339544d02e2907a85db605664c6a5cbdefe14`；冻结副本全部匹配。其后仅F7交付记录将附件计数改为“19份完整附件（含tracked delta）”，与原索引一致；该文件SHA256 `79821eda7d8d712c6c588982eb4928d4828a7e0bda0b4cd581251df2ac759772`，其余26件未变。最终已读索引SHA256 `de538a3747ad300db2861b32f08fcc79045460795bd469e8847324d324259fd9`；全部生产／测试与r2候选相同。

## Standards

通过，开放finding 0；历史ST1／P3已关闭。

ST1位于[前片交付记录](2026-11-11-architecture-platform.md)第37行：原“Linux／Windows各七必要步骤”会让读者误认每个平台验证了七项，违反AGENTS的实际检查如实记录要求。原CI正文及workflow实际为Linux三项、Windows四项。最小修正已落实为“Linux三项／Windows四项、合计七个必要步骤”，最终字节与原件一致，不需重跑产品或模型。

未发现其他实证规范违背或代码异味。`issue_backends`的Interface服务GitHub、GitLab两个真实Adapter，构造／读取／诊断和本族映射集中；`bindings`委托配置校验，`tools`消费诊断，`issues`拥有项目配置快照与观察，CLI和HTTP是两个实际消费者。原生字段映射保持局部，没有上层厂商分派、无消费者的扩展框架或竞争调度器。新增检查均保护可达的配置／凭据／远端响应失败；测试覆盖可能静默出错的身份、完整读取、重定向、并发绑定快照和入口一致性，没有新增冗余CI。

## Spec

通过，开放finding 0；历史SP1／P3已关闭。

SP1位于[总计划](../plans/2026-11-01-all-in-one.md)第161、162行：原执行表仍称C6d未关闭，与本候选已结清0252dec的记录相反，恢复时会给出矛盾状态。按F7规格逐项更新计划的要求，最小修正已明确C6d精确交付完成，AC6／完整F6其余未验范围保持；最终字节与前片原件一致。

普通项目可从现有描述驱动绑定选择manual／GitHub／GitLab，无reference运行时前置。number／iid与全局native ID分开、完整嵌套namespace编码、固定项目修订／配置摘要、完整正文／响应SHA／ETag和外部错误处理符合F7a。单GET有1MiB完整读取上限和socket I/O超时，文档没有承诺整个调用20秒完成。观察仅作上下文，无任务／批准／run或远端写入副作用。未发现缺失、越界扩展或实证错误；任务映射／窄准入、回写和observe继续属于F7b–d。

## 独立核验与限制

Spec轴实际复用既有r2依赖环境运行当前源码的 `tests/test_project_issues.py`，禁写字节码及pytest缓存：14项／11.25秒通过。没有重复安装、昂贵全测或模型。作者source159项保持其原报告身份，不冒称本评审重新执行。

主评审逐字核r2 wheel、当前源码和非editable安装的442个包文件，wheel共447文件，SHA256 `7d937646df9e7151e5f6c6fa7b830fe0c39380f9885406182bbc2f74ab62bda7`；两份RECORD、基线manifest及283冻结文件相符。安装原stdout为28项／12.79秒通过，driver14.39秒、reference verify原回执另列；r1结果按原身份保留。两份[包／页面](evidence/2026-11-11-project-issues-acceptance.json)和[自身审查](evidence/2026-11-11-project-issues-self-review.json)投影的26项原件身份均直接匹配。

离线重建57份应用HTTP原请求／响应及摘要，56份200、误路由404保持；仅两次tracker绑定PUT，修订1→2→3。三次本地tracker GET路径／匿名请求／响应摘要相符，两个context-only观察保留修订2／3；安装CLI与GitLab HTTP仅观察时间不同。其他绑定及八类工作记录保持，最终只读数据库与页面原响应一致，task目录不存在。21份浏览器命令stdout摘要和截图原件／SHA已核。三段分别3检查／9.54秒失败、5检查／15.16秒失败、5检查／5.33秒通过；两次私有driver错误、缺Chrome／初始selector和首次离线audit误判均保留，不能改写为一次全过。关闭回执限定于7个已采样浏览器进程和两自有服务；本评审未重跑浏览器，也不推断未采样生命周期。

从原流核自身run `8c8263c0fd2d4317ac2ae55d50c782be`：修订1.0.90、228.07秒、exit0／approve，prepared／actual input／prompt／stdin／protocol字节一致；19份完整附件含tracked delta共253,279B，五固定scope连续UTF-8读至null，原结果及公开投影相符。字段名称／空白边界修正、r2包、浏览器与后补文档由本次独立评审覆盖，不回授原模型。模型意见不是owner批准、双后端成功或整仓验收。

研究的43份原body／SHA、33次200／2次304／1次404／7次超时及两SDK wheel与PyPI／抽取源码身份已离线核验；研究公开GET没有运行Ergora Adapter。C6d三样本六份原CI正文和原Ref指向精确0252dec，前两in_progress保留，第三双OS共七必要步骤成功；这是前片记录支持，本评审没有新发外网请求，不将该CI转授F7a。

结论仅为本片完整候选的本地两轴通过。Spec／Standards开放0／0，各一项历史P3已关闭；无开放产品finding。F7a自己的冻结后普通提交／推送、精确Git／远端身份和候选CI仍待同片终核。真实账号认证／写入、自托管兼容、第二后端推理、GPU／WSL2及项目整体完成均不在本次结算范围。
