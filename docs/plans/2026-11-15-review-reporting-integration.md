# BR1／BR2 隔离整合计划

日期：2026-11-15。整合基线 `a4371c8e19ddf32d5dbe1d57cf88f9e638baf373`，独立分支 `integrate/review-reporting`。原始范围见[并行计划](2026-11-15-backend-review-and-reporting.md)，实际进度见[交付](../delivery/2026-11-15-review-reporting-integration.md)。主工作树的 c1b1 候选及其验证保持原身份。

## 范围与既有 owner

合并从 `f00bfdfd15173ceb0e961681679d6d3d62254bed` 开始的两个已审候选：BR1 后端说明／两个领域审查根 1.0.1，BR2 只读 `evidence-report` 作者／单叶根。逐字冻结两源的 tracked diff、全部 untracked 文件、字节数、SHA256 与执行属性，再合并 `presets.json` 与 `WORKFLOW_DEFINITIONS.md` 的两方更新；其余候选文件照原字节导入。

继续使用 `DefinitionLibrary`、完整资源／manifest、原 composition 编译和输入／结果读取 owner；不新增调度器、报告服务、状态、模板权限或 CI 矩阵，不修改既有已发布包。源码和测试只在本隔离 worktree 中整合；不修改主工作树或其他工作树，不提交／推送。模型不重复调用，浏览器读取必须来自 BR2 原真实结果导出的 HTML。

## 步骤和验收

|步骤|可核完成条件|状态|
|---|---|---|
|1 冻结／整合|核基线与新分支；两源完整 snapshot；双方 catalog／文档更新保留；旧资源字节／身份保持|两源各 13 文件已冻结；两共享文件无冲突合并；216 旧文件及原 manifest／输入保持|
|2 新安装|新非 editable wheel 和隔离 venv；实际导入 site-packages；source／wheel／site 文件集合与字节同一；reference 283 和依赖检查|663 三方逐字同一，reference PASS／283，pip check 通过|
|3 原接缝|沿既有 preset／资源检查覆盖 pretraining-review、posttraining-review、evidence-report 及原参数化 profile；核旧 manifest／输入与新叶完整祖先资源|原 invariant 通过；安装 r1 为 49 通过／1 冻结 data fixture 缺失，补齐后 r2 精准 1 通过，产品／测试字节保持|
|4 原 HTML|如现有 Playwright／浏览器可用，直接读取原 BR2 HTML，保留桌面／窄屏和控制台／请求观察；无法运行须记录实际限制|原 HTML 字节保持；已有 headless-shell 渲染两宽度，桌面适配；390px 窄屏有 70px 表格横向溢出，原失败与此限制均保留|
|5 审查交接|更新本计划／交付／隔离总计划；冻结 full diff、untracked manifest、验证原件，交主控另配新的独立组合审查|27 文件候选可审；完整 patch／22 untracked／SHA manifest 与实际原件交主控，新的组合独立审查待分配|

两源独立 approve 只属于各自原范围；本组合尚待新的独立需求／维护性审查。安装、源码、真实报告及浏览器观察分别记账，未验的厂商托管／异后端／准确率／训练／性能与发布不移标。
