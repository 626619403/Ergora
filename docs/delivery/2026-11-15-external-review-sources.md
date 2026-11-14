# Q1.2：外部审查来源交付记录

日期：2026-11-15。基线 `705cbe428dce73ff222dbdaec3c67329a310c06d`。范围、owner与验收见[具体计划](../plans/2026-11-15-external-review-sources.md)。

|步骤|实际状态|
|---|---|
|合同／盘点|已读本族IssueBackend、原review observation／正式关联、本地review_packets／GitMaterials及原HTTP／Git测试；复用已取得的一手API说明，先固定计划再改实现。|
|实现|已在本族增加repository／review_commits并保留旧repository_refs合同，来源owner复用原包及原子发布、两无State CLI；首版拒绝GitHub已merged历史比较，GitLab核start/head/merge-base。|
|源码验收|原HTTP／真实Git fixture中6新接缝通过／5.52秒，覆盖两平台精确比较／head漂移／无State离线读／源关系篡改／未就绪或矛盾refs，未调用外部平台。|
|安装／身份|r1 wheel SHA256 1ec19ef95ad96262cd6f0792546ee62d74fb66b0d5ec013c52ee041c5360f0bc；642源码／wheel／非editable安装逐字同，283参考不变；仅增来源module／schema、改cli／本族backend，repo-only AGENTS仍不打包。|
|原回归|原四suite源码113通过／4可选依赖跳过／57.71秒；独立安装含web依赖117通过／60.07秒，1项Starlette TestClient deprecation warning，不含产品失败；未新增测试文件或CI job。|
|实际CLI旅程|两原生HTTP替身＋真实分叉Git，14个新进程命令完成采集／来源及原包离线读、错SHA／已有目录／超限／缺对象拒绝；每平台8GET，无分支GET或写入，两个服务已关闭，工具控制home未创建。|
|真实平台|有界匿名GET本仓库：元数据200、明确PR1为404；保留原错误，无完整真实平台包或新平台写入。|
|审查／发布|待实施。Q5.1普通发布已完成，自己的CI及原独立补核另记，不借其身份认证本片。|

当前完成本地HTTP替身＋真实Git对象验收；真实平台只取得本仓库元数据及PR1的404，没有调用模型、执行目标项目或实现自动领域审查。后续每步据实际结果更新，私有driver／日志／包在ignored `.ergora/checks/external-review-sources/`，公开文档不依赖本机路径。

## 实际边界及原件

私有r1 wheel／安装／117项JUnit、源码两轮日志、14命令stdout／stderr与索引、两完整来源包、driver对Git／原状态前后清单的逐项比较结果及真实GitHub观察分别保留。两HTTP替身只说明原生协议与CLI合同；公开仓库元数据200不等于PR存在或完整采集成功，PR1的404保持，无重试、权限申请或平台写入。两完整包的变化源码、完整正文、原需求、显式caller／config、祖先规范和检查原件均由原本地包持有；未执行任何目标脚本、模型或训练。

## 自身与独立审查准备

已冻结基线705下16作者文件／458,742B到review-scope-r1；原r1安装调用refactoring-quality的structure叶，完整作者文件与邻近owner作为原任务、全部祖先资料保留。该模型调用当前在途，未预填decision；独立reviewer直接核源码／包／CLI及原证据，不以模型意见代替原件检查。初次套用文档补丁因一个上下文定位失败而未写入，随后修正定位后一次成功，无产品或验收修正。

两平台原Git48文件、各2份fixture状态及各2份包的前后比较在driver进程内逐项完成，r1记录保存结果数量而未单独落盘完整前后清单；后续独立审查据原driver／现存原件核对，不将结果计数称为已归档的完整前后manifest。

## 自身原结构模板结果

原r1安装的refactoring-quality结构叶采用授权Codex替代，run82be97a0299a43afb19ed1dc64d0323c，succeeded／exit0／51.667259秒、decision approve。完整23文件／511,809B；原任务和三层祖先resources在sealed input及实际stdin逐字保留。input digest4ab7c0971f91c8ee9c884c3df47fdde34f3c3bf5873113e791e4532346e50640，原result SHA256 a5151de40a6ec5943af22464ed2f2bd69bec55e59b922d3e70357177123fc1b9。仅审给定完整文本，不认证私有原件／实际运行／CI，也不把慢Claude的授权替代称为后端多样性。新fresh-context独立评审正在直接核本片源码与原件，未预填结论。

## 独立finding R1及修正（验收在途）

新独立reviewer发现P2：合法较长api_url／project组合形成的规范JSON直接作为原packet repository.id，可能超过原1024字符上限，错误拒绝合法配置。先在原HTTP＋Git fixture补两平台长代理路径／300字符project集成例；旧实现实红2失败／2.03秒并保留JUnit及完整日志。随后仅将来源派生ID改为固定前缀＋完整规范身份SHA256，封套保留完整身份，读取以同一算法核关系；没有限制配置、截断身份或放宽旧包schema。

r1 wheel／117项／14CLI与自身approve均保持原始身份，不能认证该修正。r2独立wheel／安装、受影响回归、CLI与原结构模板另验，同一fresh-context reviewer复核后才关闭R1。所有外部来源包仍是本片未发布开发原件，原本地包合同和已发布产品未改变。

## r2修正后验收

r2 wheel SHA256 `338db58dafa7f953723d1651e8952c5fab350c1bd2a9d69b83eadd1d86121f5c`；642源码／wheel／新非editable安装逐字相同，283参考保持，相对r1仅来源ID派生算法改变，原本地包schema不变。源码8接缝通过／6.34秒；原四suite在r2安装119通过／61.54秒，1项原Starlette warning。r2重新执行14CLI／两HTTP替身＋真实Git，完整读回、坏SHA／不覆盖／超限／缺对象拒绝及48原Git文件／各2state／2packet保持，服务收尾与工具home未创建均通过；原r1原件和P2实红保留。自身原模板及同片独立复核另跟踪，不以旧r1的approve替代。

## r2自身原模板

修正后原r2安装再次沿同一结构模板、授权Codex独立调用：run7a6580ee85be4996a695220d3e62e6e8，succeeded／exit0／38.799665秒、decision approve。25完整文件／535,623B，原任务／三ancestor资源／sealed input与实际stdin逐字一致；input0604ff09de688f5f02991353f8b9be3d5dc74c1e4204c5497ab4a79d01c9cf64，原result SHA256 cb8e79fc70d21ab0bf27138eb1ce541d8fca97ce54be7f72f3cb23c73d19d716。完整文本审查不认证私有原件或CI；同片独立R1复核仍另记，原r1结论不改写。

## 独立r2本地终核

同一[fresh-context独立报告](2026-11-15-external-review-sources-review.md)已追加r2：R1关闭，需求／结构可维护性及测试价值两轴approve、开放0／0。直接核旧两长配置实红／新8接缝／119安装项、642三方产品／283、r2十四CLI／两层包／原Git与25完整文件／三resource／原任务／input／stdin／result，原r1报告12,964B前缀逐字保持。不重跑已验模型或测试；其固定发布及本片自己CI须另闭合。Q5.1自己的CI终态现八job／30步骤成功，原独立终核另等，之前不推后继产品。

前片Q5.1固定705自己的CI及原独立终核现已闭合（两轴approve／开放0／0）；本片本地及独立审查均完成，后继普通发布门禁满足。原13Markdown／287链接为更新前范围，提交前含新状态的完整范围另核。
