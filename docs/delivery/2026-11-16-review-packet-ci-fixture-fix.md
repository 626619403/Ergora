# Review packet CI fixture 版本修复

## 范围与基线

测试源码基线为 `6725e62511aa4a5b68baf684ec3cbc1f0470d3e6`，隔离分支 `fix/review-packet-preset-version`。仅修 `tests/test_review_packets.py` 的 `review_manifest` fixture；产品、资源、冻结旧版本及 CI 配置未改，不新增常数测试。

官方 run `43735663360` 的 group3 annotation 指向原测试 `test_source_bound_input_does_not_skip_unexecuted_ancestor_dependencies`：`Workflow ergora-pretraining-review@1.0.1 already exists with different content; choose a new version`。完整远端日志不可读的原限制保持，未把 annotation 当成本地运行结果。

本地使用既有 `training-cycle-service-acceptance/package-r1/venv-r1-sdk` 非 editable 安装，wheel SHA256 `b7e282af7a9e154a6b61525ca36cbc9d834ef0d2c92fb701dae5bea69685fcfd`，Temporal SDK `1.34.0`。此包来自另一个服务候选，包含该候选的四个产品文件变更；并非本片从基线重新构建的 wheel，身份不混同。实际 import 路径已确认位于该环境 `site-packages/ergora`。

## 最小修复

`after_general` 分支原把派生 workflow 固定为 `1.0.1`，与已安装 preset root 冲突，导致祖先依赖断言尚未执行即失败。现在从当前 root 的三段版本读取 major/minor/patch，再发布下一 patch revision；保持原依赖修改和原行为断言。

## 实际验证

所有 pytest 命令均使用上述同一安装环境的 Python，添加 `-I -B`，移除 `PYTHONPATH`，不重新安装产品。运行参数、工作目录、退出码、stdout/stderr 与 JUnit 分别留存在项目 ignored 检查目录 `review-packet-ci-fixture-fix/`；前后运行分别命名。

- `before-single`：原单 test **1 failed，1.13 秒**，准确复现同一版本冲突。
- `collection`：原文件 **49 tests collected**。
- `after-single`：原单 test **1 passed，1.21 秒**。
- `after-file`：原文件 **49 passed，83.27 秒**。另已通过 `git diff --check`。

新的fresh-context reviewer已按实际两行fixture差异、原回归与对应owner／preset身份给出[需求／维护性两轴approve，开放0／0](2026-11-16-review-packet-ci-fixture-review.md)。修正与原交付已逐字接入主开发树，保留主线产品和其他在途文档。

已固定`478c98891522930817fa7005a8ac96e408f37230`；原reviewer核固定测试字节与所审一致，无额外产品／CI改动。已普通推送当前开发分支，精确远端同一。官方一次观察：自己的push／attempt1 run [43737570677](https://github.com/626619403/Ergora/actions/runs/43737570677)为in_progress，plan成功／另七job运行；最终结果待实际观察。原6725 run终态completed／cancelled：5成功、group3失败、Windows与group5取消，未改写为成功。

发布与官方请求原件在ignored `review-packet-ci-fixture-fix/publication-r1/`。未重跑完整 group3／其他 suite，不据本地结果宣称远端通过。

### 公开页面后续观察

同一run／完整SHA／push／attempt1的一次普通HTTPS公开页读取返回200；页面仍是`In progress`、矩阵`6/7 jobs completed`，尚不能确认全8 job最终状态。页面新增group5的明确annotation：`The job has exceeded the maximum execution time of 20m0s`与`The operation was canceled.`。这是远端超时记录，不能写成全CI成功，也不能据此推断某个训练用例断言失败。

完整headers／HTML／摘要在同一publication目录`public-page-r2/`。既有API403／配额0和完整日志不可用的边界保持；未重试、未使用Cookie／认证或其他页面片段。已单独安排对现有分组与本地JUnit成本的只读归因，先查证据再决定最小分组调整，不删生命周期保护或直接加超时。
