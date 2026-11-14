# Q3.2：成对测量合同审计与入口交付

日期：2026-11-15。基线 `2729b81a4c10e4bf8c77bd78ea4165b0a64cb0c0`；范围见 [具体计划](../plans/2026-11-15-training-measurement-contracts.md)。产品 633 文件及 283 冻结参考沿 Q3.1，使用原非 editable 安装，不替换旧验收环境。

|步骤|实际状态|
|---|---|
|盘点／决定|已读原 baseline／prepare／evidence、冻结 perfctl／比较器／demo 及原测量 Skill。所需机器绑定已由原 owner 持有；本片补使用入口并实跑原合同，不新建指标／评分／批准权威。|
|用户入口|已补训练手册的包内 CPU 演示、逐字重算及原 gate 命令；已有合同字段表保持单一权威，不新增用户脚本。|
|安装验证|原 demo／重算／gate 及八类反例完成；原比较器9项、registry14项和原基线／归档16项通过。633 安装件未变，283参考PASS。|
|审查／发布|自身原结构模板 35.945 秒／approve；新 fresh-context 独立两轴 approve／开放0／0，R1已修正关闭；已普通发布29cdcfe、完整远端与原独立固定发布两轴通过；纯docs沿原CI过滤。|

源码图不能认证真实瓶颈，合成 elapsed／attestation 不能认证训练、质量或性能。真实资产／GPU／B3、Q3.3 新总路径及 Q4 多轮继续开放。

## 真实调用路径与机器边界

|职责|已核调用与合同|仍由可信流程证明|
|---|---|---|
|原始参照与实验|`training` → `reference_training_setup`／`reference_training_preparation` → 原 baseline／prepare；`perfctl.baseline_ok` 核 baseline ID、完整提交、配置与 workload，登记内容不可覆盖|workload 的真实算法／模型／数据含义、最终有效配置与设备实际一致；初始锚点到后继实验的多轮关系归 Q4|
|成对测量|`perfctl.gate` 核精确 manifest、比较器字节、两臂提交／配置／环境／数据／初态与预登记政策；原 `compare_runs` 重算统计、核输入匹配／独立 run ID、无 profiler 全局窗口声明与 AB／BA 覆盖|真实独立重启、输入重放／去重、全部参与 rank 完成边界、资源隔离／采样噪声，不能靠字符串或摘要证明|
|正确性／质量|原 gate 核 required checks、独立 reviewer 名称、integration 和必要 quality 的完整 artifact／摘要及候选／验证合同绑定|独立身份真实性、检查 oracle、任务质量与未覆盖路径；合成 PASS 不认证实际执行|
|保存与采用|原内容寻址 archive 保存 evidence、gate、manifest、baseline 和比较器；`reference_training_evidence` 验证原归档；owner 明确批准沿原训练入口|比较器不评价质量／P99／长程稳定性；gate 仅可交人工审查，不授予采用权限|
|预算与恢复|原 runner timeout／实验窗口和精确 start／cancel／unknown 对账 owner 保留|累计探索／多轮成本与自动停止仍归 Q4，单个 walltime 不能代表全预算控制|

没有发现需要新指标、schema、评分器或参考修改的本片缺口，未变更生产代码、依赖、模板和 283 冻结原件。Q3.1 图谱／测量建议与实际可信执行保持不同证据层级。

## 安装验证与原件

使用 Q3.1 原不继承 system-site-packages 的非 editable 安装解释器；只运行原随包工具，未安装依赖、启动服务、读模型／数据或设备。原 `demo.py --out NEW_DIRECTORY` 建立明确合成的八对 AB／BA 与原归档；`compare_runs.py` 重算输出逐字相同，结果为 `PASS`／`quality_assessment=NOT_EVALUATED`／P99未认证／`promotion_approved=false`。原 `perfctl gate` 返回 `ELIGIBLE_FOR_HUMAN_REVIEW`。

八份独立合成副本保留全部改动、输入／输出和原 stderr：无收益重算 `FAIL`，两对不足样本重算 `INCONCLUSIVE`；profiled、数据漂移、结构化quality失败、预登记阈值漂移、复用baseline run ID、过期基线配置也均被原 gate 拒绝，exit 2。副本的artifact摘要按其真实内容刷新，未用损坏摘要掩盖实际所测规则。没有改原正例或归档。

原比较器自测 **9 passed／0.037 秒**，原registry **14 passed／0.987 秒**；原安装 `tests/test_training_baseline.py tests/test_training_evidence.py` **16 passed／10.53 秒**，零失败／跳过。后者覆盖原基线确认／冲突／丢回复恢复、原归档／字节损坏／容量／只读与 CLI／HTTP 共用合同。没有新增测试或 CI；633 产品逐字保持、283参考PASS。

第一版私有演示驱动已完成工具调用，但末尾身份检查误将包内 data 目录当 package 根而报 FileNotFoundError；原日志保留。仅修私有检查路径后完整 r2 成功，未改产品或伪记第一次全流程成功。私有证据在本地 ignored checks 保存；公开文档不含机器路径或凭据。

## 自身模板

原结构模板 run `41ef620684ce4c8994f36874301c6b41`，**35.945 秒／succeeded／approve**；17 完整文件／294,446B，完整 task 和全部父／叶资源均在实际 stdin，冻结 prompt＝stdin。input digest `b45dbaf708fe7b222afd75b3dc17349092e511cf50bf4b38818d523e7f3a322c`，原结果 SHA256 `11feaec824a85a91da9b0b9438ae29b8f5fb5ac51c2e98232f604d5065cc3385`。沿用户授权选 Codex 替代，记录此前大材料 Claude 超时原因，不声称异后端成功。

所给完整文本的审查确认直接复用原工具／owner、命令与接口一致、统计筛选／质量／采用分开，没有提出实质修正或额外测试框架。它不认证安装／运行／CI／私有证据；这些由原检查和新的 fresh-context 独立审查分别核对。

## 独立审查修正

原 fresh-context 评审实证 R1（P3）：手册将“不满足门槛”笼统写为 FAIL，会误述置信区间交叠时的不确定结果。评审用原安装比较器的八对合法 AB／BA 样例验证：点估计约0.995%低于1%门槛，但区间约[-1.232%, 3.344%]，结果为 INCONCLUSIVE。现仅修手册说明：样本／换序不足或区间不能区分门槛保留不确定；按原all／any规则连区间上界都不能严格超过门槛才失败。产品与统计规则未改，不新增测试框架；原 reviewer 已用原源码与实际反例复核关闭。

## 独立本地终核

新 [fresh-context 独立报告](2026-11-15-training-measurement-contracts-review.md)先核原要求和六文件快照，再直接检查实际 owner、633 源／安装身份、283参考、15组原命令日志及九bundle的72个artifact摘要。原 reviewer 另在新目录完成原demo→重算→gate、重复目录保留和阈值交叠反例；作者274个原文件前后摘要保持，自身模板17份完整材料及原输入／结果也独立核同。最终需求／维护性两轴 **approve／开放0／0**，R1关闭。七Markdown／181本地链接与fragment零错误，外网未验证。

本片全为 docs Markdown，沿原Portability push过滤，不新增文档CI或假称新产品CI。普通发布及完整远端身份待核；633产品的CI仍归Q3.1自己的固定提交。

## 固定发布终核

已普通发布 `29cdcfe2f45a66dcaad1835c0860c24a78290529`，唯一父2729b81，七份Markdown实际blob与暂存清单逐字一致，完整远端Ref同一。最终作者文档检查七MD／182本地链接与fragment零错误（新增终核链接前的独立计数为181）。原reviewer已补核七blob、实时远端、固定633源／wheel／安装与283参考、产品／测试／依赖／CI无差异及原docs push过滤，两轴approve／开放0／0；精确文档交付完成。Q3.1自己的CI仍单独跟踪，不用更新中的Q3.3产品替代633身份。
