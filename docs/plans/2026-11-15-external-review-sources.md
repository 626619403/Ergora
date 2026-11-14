# Q1.2：外部 PR／MR 的只读精确材料采集

日期：2026-11-15。源码基线 `705cbe428dce73ff222dbdaec3c67329a310c06d`，640产品／283冻结参考。Q4.1自己的CI及原独立终核已闭合；Q5.1协议片已普通发布，自己的CI与原发布补核另记。承接[Q总计划](2026-11-15-domain-review-optimization-quality.md)的Q1.2，先固定本计划再实施。

## 行为与边界

操作者提供明确的GitHub／GitLab来源绑定、仓库内PR number／MR iid、已经具备所需精确对象的本地Git对象库、原需求、显式调用者／配置和检查原件。采集只对平台执行仓库元数据及单个PR／MR的GET；以该次原生观察里的固定commit构建原本地审查包，再不可覆盖地发布来源封套及原包。后续head变化必须发布新目录，原包不变。

平台diff可能分页或截断，不承担完整源码身份。本片复用`review_packets`／`GitMaterials`：完整变更／完整blob／祖先AGENTS／显式上下文、容量拒绝、二进制／LFS／子模块的原支持范围保持。缺对象显式失败，不自动fetch、checkout、hook、filter或运行项目。首版只支持同仓库端点，fork明确拒绝。GitHub以原base SHA及head求唯一merge-base（首版拒绝已merged的GitHub PR，避免将当前base误作历史比较）；GitLab以`diff_refs.start_sha`和head计算，并核对原`base_sha`（merge-base）与`head_sha`，异步未就绪的diff_refs拒绝采集。

不伪造task／candidate／export，不复用正式候选关联冒充外部审查。原生正文及检查是待审资料；没有模型调用、训练、正式批准、评论、标签或合并。封套仅证明所保存资料的内部身份，不认证平台来源、当前head、仓库归属、检查可信度或完整评论／CI上下文。绑定文件只存凭据变量名，发布包不带凭据。

## 现有owner与最小扩展

- `issue_backends`保留平台HTTP、原生身份和字段解释。本族增加实际消费者需要的独立仓库读取及精确比较端点接口；旧`repository_refs`复用仓库读取，返回合同保持。采集／CLI按共同契约调用，不按具体tool分派。
- `review_packets`继续唯一拥有本地源码包及离线完整性。新的来源用例负责两类观察与原包的关系、来源封套、原子发布及离线读回，不另建平台客户端或Git reader。
- CLI提供显式采集和来源读取入口，位于State初始化之前；本片无需项目登记、服务、SDK或模型。既有本地prepare／read／verify合同不变。
- 原`tests/test_review_associations.py`的HTTP接缝及`tests/test_review_packets.py`真实Git fixture复用；尽量把新增集成接缝留在原测试文件，不增加CI job或重复原本地包全矩阵。

一手依据复用本轮2026-11-15读取的[GitHub单PR API](https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#get-a-pull-request)与[GitLab单MR API](https://docs.gitlab.com/api/merge_requests/#get-single-mr)，以及[已固定的审查工具研究](../research/2026-11-15-pr-mr-review-tools.md)。它们分别解决平台快照解释和原生来源接入；不整体迁入第二套审查器或把API字段说明视为兼容验收。

## 验收与进度

|步骤|完成条件|状态|
|---|---|---|
|Q1.2a 合同|明确平台字段、固定commit、来源与本地包关系、离线身份、未覆盖范围及owner|已盘点接口／一手字段并固定本计划；同仓库／GitHub未merged限制明确|
|Q1.2b 实现|两后端共同接口、原包复用、不可覆盖来源发布、无State采集／读回|已实现两后端接口／原包复用及两CLI；新6接缝源码通过，642安装身份及117项通过，独立审查待完成|
|Q1.2c 接缝|两平台真实Git对象＋HTTP替身；目标推进与merge-base区分、head漂移新包、错源／fork／未就绪／冲突／缺对象／超限拒绝、离线无服务且原包保持|原6接缝源码通过；R1新增两例旧代码实红2失败，修后8通过6.34秒，原四suite最终r2安装119通过；平台替身与真实平台分开|
|Q1.2d 安装与实用|独立wheel／非editable安装身份，运行适当原回归及实际CLI旅程；公有API可用则有界只读验证，失败保留；283参考不变|r2独立wheel的642源码／wheel／安装逐字、283不变；14实际CLI／两平台替身、Git原件及原状态保持／服务关闭；真实GitHub仓库200／PR1为404保持，无完整真平台包|
|Q1.2e 审查与发布|自身原结构模板、新fresh-context独立审查；修实证finding；普通push及完整Ref／自己的适用CI／原终核|原r1自身Codex51.667秒approve；新独立发现合法长配置R1，旧实现2例实红并修来源派生ID，r2新wheel642／283、安装119项和14CLI已过；r2自身Codex38.800秒approve，同片独立两轴approve／开放0／0、R1关闭；普通发布及自己的CI待完成；Q5.1自己的CI终态及原终核前不推后继产品|

每步更新[交付](../delivery/2026-11-15-external-review-sources.md)及PLAN。Q2.3再接精确材料到领域审查运行／报告；Q4.2仍沿原预算／生命周期；kernel专家保留在已发布优化路径中并可给出无需kernel修改。
