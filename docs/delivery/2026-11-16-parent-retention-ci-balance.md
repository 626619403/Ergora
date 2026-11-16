# 父请求留存后的 CI 有限再平衡

2026-11-16。当前状态：配置／collector及新的fresh独立审查闭合，固定9a35174；新联合候选自己的CI待发布。依据[只读预算调查](2026-11-16-parent-retention-ci-budget-analysis.md)，固定基线 `c4c0946060ba781eb8b2cb2e7e9d3ad2798dcd5a` 已含内部父留存产品1f57ca4。

只改 `scripts/ci/linux-groups.json`：完整 `tests/test_composition_tasks.py`、`tests/test_services.py` 从group5移至group1。六组86唯一文件保持，文件数为13／16／12／18／13／14；不改产品、测试正文、CI job／runner／时间上限／Windows全选。新JSON raw SHA256 `5995dfe1bd13235475fbbfd79b2ff51dc2065f302924e465e4fa1474456241df`，原JSON `9923dbdb2ab8282e9840a98f1b22828189d441e8ea7758b9b188f8e9ecdf4608`。

选择两文件的依据是准确a0d533d自己的CI group5已用18分43秒、group1为3分58秒；新增22项真实留存保护本机安装选集为116.27秒，存在额外成本。两文件旧完整JUnit有各79.714／52.196秒的已有工作，正文与旧基线逐字保持，原fixture闭包可独立模块收集。两文件比单文件分散更多已知工作，但旧131.910秒不等于远端节省，不能把本机新增成本与官方job线性相加减来承诺20分钟内通过。最终仍用新候选自己的CI认证，原Linux20／Windows30分钟保持。

使用新父留存非editable SDK Python3.12，实际 `-I -B scripts/ci/run.py --collect-only`，无源码PYTHONPATH；原runner只加入CI plugin及包内参考导入。实际收集 **2317 = 原2295＋恰好新增留存22**，无删除；新增集合逐node与固定r3安装JUnit22同一。原86文件全有归属，无重复或遗漏。现有PhaseLog selector映射回放核仅两完整文件的70个既有node由5→1，其他node归属不变；group1为355、group5为436，其他组349／409／453／315。Windows all不会读取Linux归属JSON；本机未执行Windows。

原件在ignored `parent-retention-ci-balance/`，含原／新JSON、准确变更身份、实际完整argv／stdout／stderr／phase／JUnit、2317 node原集和selector回放／comparison。只执行collector及纯映射，不执行新组合测试body；没有复跑无变化留存组、全六组、模型或训练。原collector／selector由已有脚本提供，私有校验driver不加入产品。配置自身维护性和影响范围将由新的fresh reviewer核对后再固定；独立通过、发布与准确CI均未预记。


新的[fresh独立审查](2026-11-16-parent-retention-ci-balance-review.md)需求／维护性两轴approve、开放0。配置固定提交 `9a351740de95eebc3376bc1454162e030b1a1731`，唯一父c4c0946、只一JSON两增两删，新raw身份保持；审查报告SHA256 `c8db2caaa8af418bcd014cd3f1cb0bd46f9d22498ec6be3cb9ba67a3611d05ae`。该小片完成，不重跑产品／模型或无变化body；新组合由后续联合公开候选自己的CI验收。
