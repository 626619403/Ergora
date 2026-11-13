# D2-B2h：低精度／量化子模板

日期：2026-11-13。承接[专家计划](2026-11-13-specialist-presets.md#同事试用入口与剩余专家清单)，产品基线`8f0b5802274f5db80b804d99979d074cdd3e1338`，开始时工作树清洁。该基线为已推送的B2g；其自己的CI独立进行，期间仅相关Markdown发布记账可能继续。本片新产品待B2g CI收口后再发布。

## 范围与归属

新增`optimization-low-precision`配方与`ergora-opt-low-precision-proposal@1.0.0`只读根，复用原training-proposal v2的四叶形状：analysis下design／profile、kernel、measurement下review。根提供原创方向context，专家仍为精确实验设计／性能分析／kernel设计／测量审查v2。每次只调用选定叶；kernel手动接收design／profile完整原结果，measurement接收全部三个完整原结果及实际实验材料。静态边不运行整图或实验。

区分PTQ／搜索／导出、QAT／QAD质量恢复、TE训练低精度；逐项核模型／模块／融合组、格式／算法／scale／packing、目标runtime、质量与总预算。搜索成本模型、checkpoint／返回值、导入成功和短loss不替代真实支持矩阵、可部署产物、训练恢复或独立质量／性能。原runner、native search／checkpoint与评价／采用所有者保持唯一。

只增加workflow／instructions／context三文件、catalog一条和原测试方向及四叶预期；更新两手册、README与计划／交付。保留21旧catalog、共享v2、545旧产品除catalog外字节及283冻结参考文件。不安装／执行ModelOpt、AutoRound、TE、Bridge或Olive，不建量化运行器／搜索账本，不更改后端、依赖或默认模板。真实实验属B3；带内部模型的完整系统属C2。

## 固定资料与验收

复用[R2](../research/2026-11-12-optimization-quantization-agents.md)18份固定版本原件470,878B，原HTTP200回执与正文SHA已核，新研究请求0。覆盖ModelOpt0.48.0 API／PTQ／QAT-QAD／Bridge例程，Skill固定`9aeff419f3afa1b27e7bcc10dc6a90cc68df4d77`的搜索／iteration／PTQ门禁／QAD／evaluation，TEv2.21.0 recipe／availability，Bridgev0.7.0混合精度／量化，AutoRoundv0.16.1指南／AutoScheme实现及Olivev0.13.0搜索／engine。只分发原创综合，来源URL不是运行时抓取或安装授权。

|节点|可验收结果|状态|
|---|---|---|
|H0 来源与计划|原件／回执、基线与分支核准，执行边界明确|完成|
|H1 数据定义|四叶只读根、catalog及完整父资料继承，旧定义保持|已实现；545旧产品除catalog与21旧条目保持|
|H2 隔离安装|noneditable wheel、source／installed及两RECORD／283，原preset suite|完成：548产品／两RECORD／283，29通过／115.59秒|
|H3 实际交接|四真实task-MCP调用，完整资源读取及两处完整原前驱手动交接|完成：四叶23资源63,232B完整读取与原前驱；measurement保留request-changes，仅synthetic资料|
|H4 独立审查|自身原结构模板、新fresh-context需求／可维护性两轴|自身30.278秒approve／五全文48,318B与新fresh-context两轴完整原件终核通过，SP1/P3关闭、开放0／0|
|H5 发布|普通推送、完整远端身份、该提交自己的完整CI与独立终核|待做|

Synthetic资料包含任务门槛0.2个百分点与候选0.6个百分点下降、SM90上误提TE NVFP4、effective_bits当尺寸／加速、未声明的vision量化／prompt变化、融合组不兼容、不同模型／数据复用搜索state、AutoRound混合类型导出、Olive全失败返回best及QAD漏teacher成本。只验提案辨别与证据交接，不能升级为执行过这些工具、模型、硬件或质量实验。

结果逐步写入[交付](../delivery/2026-11-13-optimization-low-precision-directions.md)。下一片B2i独立kernel根；B3／C2真实实验与原生嵌套另验。
