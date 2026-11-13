# 2026-11-13 Linux CI 分组与可中断观测

承接[实施计划](../plans/2026-11-13-linux-ci-shards.md)、[原发布状态](2026-11-13-publication-status.md)与[独立成本调查](2026-11-13-linux-ci-profile-review.md)。应用基线为普通提交 `d2dac8d`；本片只调整仓库 CI 脚本、workflow、分组数据与维护说明，不修改产品、原测试、依赖及 283 份冻结参考。

## CI1：成本与覆盖

原 Python3.11 采样在 4500.222 秒固定边界停止；1,696 collected 中 1,463 完成 teardown，九个 research 失败和原 cancellation 保留。仅原 233 个未完成 nodeid 的独立入口 tail 退出0：227 passed／6 skipped／36 subtests passed，pytest391.72秒，控制器393.593秒。两完成集合交集0、并集为原1,696，不是一次连续 suite 成功。首case的采样驱动 spawn 故障、整个 research 模块的独立补测及原缺失终态trace各保留自己的范围。

[成本投影](evidence/2026-11-13-linux-ci-costs.json)按每 node／phase 的最终父报告计算，避免重复累加36个子报告，并剔除原未完成node的1.104574秒setup。阶段成本4,875.574秒／75文件；最慢文件export586.729秒、reconciliation542.369秒。按整文件递减贪心分组，首个满足每组低于900秒工作目标的组数为6，估算各812.58–812.63秒。仍保留每job20分钟上限；这是当前机器上的历史估计，自己的远端候选必须实际验证。

## CI2：实现与完整选择

- `scripts/ci/linux-groups.json` 是唯一文件分组配置，workflow从其组数生成六个Linux／一个Windows matrix，不重复硬编码N；空配置在plan job失败。各组仍安装wheel并核reference，Windows完整suite与PowerShell5.1安装升级步骤保留。
- `scripts/ci/run.py` 提取原workflow的pytest子进程、stdout和错误annotation。入口仍为独立 `python -m pytest`，只增加CI plugin／Linux reference导入路径，应用从已安装wheel读取。`-c`固定本仓库配置，避免外部结果目录改变pytest root。`--collect-only`可核选择，不代表执行通过。
- plugin在完整collection后选整文件组，拒绝漏登记、重复分配、缺失文件、越界组、空选择。每次使用新结果目录，记录完整／选中nodeid、阶段起点／结果／失败正文、report类型、collection异常、session终态。workflow `always()`尝试上传，硬终止后不保证上传；没有finish／result即保留incomplete。

新独立Python3.11.15环境安装B2c wheel SHA `e91f7d2daf15dd0a8bd58afd366670909af43b9f6aa004c598ae64c1aa312837`，源码／wheel／安装521文件相等，两RECORD529／534行及283参考身份核准，非editable。依赖版本与原采样一致。新候选1708项全量与六组254／250／342／312／251／299的并集相等、交集0；原1696只是成本基线，没有替新候选授予通过。

## CI3：行为检查

正式plugin下research、processes、installation、task_submission_locks四模块31通过／5原条件跳过，57.86秒；包含spawn抓取、正常／超时子进程清理、安装升级和提交锁生命周期。没有重复完整小时级suite，完整远端回归仍待自己的CI。

小型独立fixture使用正式runner／plugin，验证全量与分组、unittest子报告类型、重复分配／漏登记／越界选择、真实失败正文和中断起点留存；它只验CI基础设施，不是产品reference验收。首r1夹具的AdapterTests未继承unittest且输出在夹具外，退出4，原件保留。r2纠正夹具并把结果放在夹具内，七探针通过；随后为支持合法的外部输出目录，正式runner固定 `-c`，r3用外部输出复验。r3七探针全部达到预期：全量／分组退出0；重复、漏登记、越界均退出4；受控失败退出1且有正文；原owner中断为cancelled／-9、仅有call起点无finish。最终配置修正后的七次collection再次核全量1708＝六组并集、交集0；不改写r1失败。

私有原件在本仓库 `.ergora/checks/linux-ci-shards/`，旧采样在原publication目录；使用／本地重跑见[测试维护说明](../TESTING.md)。

独立Spec初审发现五个setup skip在普通hook前就被pytest跳过，原结果有记录而起点缺失（P3）；原red投影保留。已将三phase hook改为外围tryfirst wrapper，原返回／异常透传。正式r4夹具覆盖提前skip和xfail(run=False)，七探针达预期且每个phase都有起点；新selected-r2四模块31通过／5跳过58.00秒，103份phase全部有起点，包括五个setup skip。最终wrapper候选再核七次collection仍1708完整分组。计划最慢文件过期P3同时修正为export586.729秒；不覆盖原审查。

## CI4：审查与发布

自身原结构审查模板已实际调用：67.247731秒succeeded／approve；六文件21,629B与全部三个祖先／自身资源逐字进入原prompt／stdin／protocol25,947B，result SHA `d0df2970baca7ae2f5b24f4b32bda259c12e769a92e084e753f52cd9a4066e05`。这是该聚焦材料的结构审查，独立两轴与原件复核另计。修正后自身模板48.880621秒succeeded／approve，六全文22,097B／实际prompt、stdin和protocol26,663B及全部三个资源核准，结果SHA `44ef04dba3bf72750be1bf496f8ee65ed34d8d11244a14c68bc5f7c6195136a7`。完整12文件及全部原件的[新独立双轴终核](2026-11-13-linux-ci-shards-review.md)通过：Standards0，Spec初审两P3已关闭／开放0。本地实现／验证／审查出口完成，精确发布尚待完成。原00922 CI的Windows通过／Linux20分钟取消保持，不能作为本候选CI通过。普通push与精确Ref、该候选自己的六Linux／一Windows必要步骤另行核准；不自动合main或强推。
