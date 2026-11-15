# Review packet CI fixture 独立审查

日期：2026-11-16。审查者：fresh-context reviewer `review_packet_ci_fixture_review`，未继承实施对话。先读实际 diff／新增文件，再核作者交付与原件；按根及 tests AGENTS、测试协议、independent-review／test-seams 审查。仅写本报告，未改源码、安装依赖或重跑测试。

需求符合性：**approve**。维护性：**approve**。本次范围内无阻塞或非阻塞 finding，开放 finding 0／0。

## 检查身份与范围

基线 `6725e62511aa4a5b68baf684ec3cbc1f0470d3e6`；候选分支 `fix/review-packet-preset-version` 的未提交树 `.ergora/worktrees/review-packet-ci-fix`。实际差异为 `tests/test_review_packets.py` 两行修正、`docs/PLAN.md` 新状态段及新增 [交付](2026-11-16-review-packet-ci-fixture-fix.md)。检查完整 tracked diff、新交付正文与邻近调用；产品、preset、immutable 发布 owner 和 CI 配置均无变更。

`tests/test_review_packets.py:72–73` 从已安装 root 派生下一 patch，消除把当前 published `1.0.1` 改内容再发布的冲突。当前 preset catalog 选择 `ergora-pretraining-review-v1.0.1`，且安装同时包含旧 root；fixture 的临时 State 尚未包含下一 patch。修改保持依赖串行化、真实 import 和 manifest 编译（同文件 74–80 行）。原测试 164–174 行仍要求祖先未执行时抛出 `direct root task` 并且不发布 destination；不是只检查版本字符串。`review_requests._reviewer` 调用 `review_dags.require_root_task`，而 immutable 冲突仍由 `definition_bundles.py:291` 拒绝。

两行逻辑位于单一 fixture，无新接口、控制流或依赖；派生有效配置优于固定 patch。现有真实接缝已覆盖该故障，不要求引入 SemVer 库或新增镜像测试。

## 证据与边界

核读 ignored 检查目录 `review-packet-ci-fixture-fix/` 的 argv／cwd／returncode、stdout、安装身份和 JUnit：原单测 1 failed／1.13 秒，错误与官方 annotation 一致；修后原单测 1 passed／1.21 秒；原文件 49 passed／83.27 秒，collection 49。独立执行 `git diff --check` 通过，未重新运行已有行为检查。

安装身份为既有服务候选的非 editable SDK 环境，wheel SHA256 `b7e282af7a9e154a6b61525ca36cbc9d834ef0d2c92fb701dae5bea69685fcfd`，Python 3.12；argv 使用 `-I -B`，PYTHONPATH unset，实际 ergora 位于 site-packages。逐文件只读比较候选 `src/ergora` 与该安装：产品差异恰为 `reference.py`、`reference_training_worker.py`、`training_execution_protocol.py`、`services.py`，另有未打包 `AGENTS.md`。fixture／原失败路径的 workflow、definition_bundles、review_packets、review_requests、review_dags 及全部 preset 资源一致。CLI 间接导入 services、agent_runs 使用 reference，不能据此把全文件通过称为精确基线新包验收；四 owner 的新增服务路径不参与此次原单测的 install→import→manifest→祖先拒绝链路。当前证据足以支持此局部 fixture 修正。

核读 `review-reporting-mainline/publication-r2/` 官方原件：run `43735663360` 对应准确基线，group3 官方 annotation 为该版本冲突（1 failed／349 passed／27 skipped）；完整日志请求 403，原因是需要 Repository admin 权限。保存快照中整体 run 仍 in_progress／conclusion null，group5 与 Windows 仍在途。原失败、不可读日志和未完终态均保留，本报告不推断后续远端状态。

## 后续验收

无源码修正请求。提交／普通推送、精确新候选自己的官方 CI 及远端终态仍属后续发布验收；本地文件回归不替代这些证据。未跑完整 group3、其他 suite 或准确基线重建 wheel；交付已如实注明，本次不据其宣称全源或远端成功。
