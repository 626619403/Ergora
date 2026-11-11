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

## 同片精确交付终核（2026-11-11）

本段结清F7a自己的提交与CI出口，上文“当前HEAD／未提交／待核”保留为原评审快照。唯一代码候选为不可变提交 `9f010079126f374c01272ecf2f0ec85284e4e2cc`，唯一父提交是原基线 `0252dec5c41be1c1f6f533d86d8f32d30d178ce3`。主评审已逐件核28个Git blob、`100644`模式及changed-path集合，与ready-r1精确一致；ready manifest SHA256 `03dd8868ee582d281fc557311b5ab348d45b6d0e507b93830957b78e454c6d39`。原r2包／安装／283冻结核验沿用其原始观察时间，没有拿后续F7b工作区与F7a包比较。

独立官方HTTPS Ref GET实际返回匿名限流403，原280B正文及回执保留，不改称HTTPS成功。随后按授权只用既有origin push URL执行一次SSH `ls-remote`，远端 `refs/heads/refactor/architecture-foundations` 返回上述完整9f01007，exit0、7.067秒、stdout86B／stderr0B；没有更改认证、remote或网络配置。其stdout SHA256 `fe656c57e8fc25afec64ebc511cce86337d3073835027305dd617b4e0b97ee1e`。

本片自己的[Portability #145](https://github.com/626619403/Ergora/actions/runs/42974715330)对应push、上述分支与完整commit，attempt1、workflow `.github/workflows/portability.yml`。主评审逐字核作者保存的官方运行汇总HTTP200原页：`Status → Success`、`2 jobs completed`。汇总不含必要步骤属性，因此本评审又分别直接GET一次[Ubuntu／Python3.11 job 130370989713](https://github.com/626619403/Ergora/actions/runs/42974715330/job/130370989713)和[Windows／Python3.12 job 130370989224](https://github.com/626619403/Ergora/actions/runs/42974715330/job/130370989224)，均HTTP200、请求与最终URL相同。两页均显示`succeeded`，各`check-step`带`data-job-completed`，`Complete job`为success；成功步骤的log链接均精确含本片完整commit及各自job ID，开始／完成时间有效且早于取样时间。

|不可变workflow中的必要步骤|Ubuntu|Windows|
|---|---|---|
|Build and install wheel|success|success|
|Packaged reference identity|success|success|
|Native application regression|success|success|
|Windows PowerShell 5.1 installer and upgrade|skipped，符合Windows条件|success|

所以实际为Linux三项／Windows四项、合计七个必要步骤成功。没有从HTML推导pytest数量。以下原页均已独立核字节数／SHA256与各自receipt一致；私有证据根为 `.ergora/checks/f7-issues/`：

|原页证据ID|字节|SHA256|
|---|---:|---|
|`commit-closure/actions-run-02/page.html`|156947|`2769ae69dccb4c72643315650de09917b9fa879a14784058a0709abf8bf9a5ca`|
|`independent/commit-9f01007/actions-job-linux-01/page.html`|161497|`cbdae8a62c20ef5a2941659ca2940bea96b287a6c8b7b82403a8f3ea01f61aed`|
|`independent/commit-9f01007/actions-job-windows-01/page.html`|159583|`f92459016f7fba505f74b847120d3fb5d135ea46df4e614337e881b9ada82333`|

完整离线终核见私有 `independent/commit-9f01007/ci-html-terminal-audit.json`，15513B、SHA256 `4c275a3d09662c7abdddf4f0c48fba2957f48649c67f4cfc9a0cd8821ae27602`；同目录保留`git-objects-audit.json`、HTTPS原件及`ssh-ls-remote-receipt.json`。较早`actions-page-01`的IN_PROGRESS及`snapshot-api-01`／`snapshot-api-02`两次REST403仍按原状态保留；汇总页的通用局部加载提示、两警告一notice也未删除。终态依据是官方公开HTML的状态与步骤属性，没有终态REST响应或下载的完整job日志。本次没有重跑CI、安装、产品、浏览器或模型，没有审查F7b源码／运行时，也没有远端写入。

在上述范围内，F7a的同一候选精确Git／远端身份及自己的必要CI均已终核，精确交付可关闭；Spec／Standards开放finding仍为0／0。此结论不构成F7b、完整F7或整个项目验收，原列未验范围继续保持。
