# c1b2a 服务管理接线

2026-11-16；实施基线 `b7193530f12363aeb0f68daddfa1a6f5774bc86d`，分支 `feat/training-cycle-service`。仅本片接线结果，整体业务／安装／独立审查由主交付汇总。

`reference.training_cycle_worker_command` 沿原 budget bootstrap，使用应用解释器和选定 native installation，直接调用同 owner 的 `cycle_main(installation)`。`services` 增加独立 program，从原 `program:training-worker` 复制配置，关闭 autostart，分离 stdout／stderr 日志，并显式设置 70 秒停止观察期限。原 budget command、原配置存在时的配置选择、283 参考资源和 Worker 配额未改。

启动 cycle 服务时检查可选 Temporal SDK，缺项明确提示 `ergora[temporal]`；离线服务状态读取及其他服务控制保持可用。已有运行 daemon 缺少新 program 时，拒绝请求并提示显式 stop／shutdown／restart，不改运行配置、不 reload。服务 `task_readiness` 保持 `not_checked`；stop／shutdown 的 confirmed 仍只根据 Supervisor 的 OS 服务状态，不证明业务子树停止。70 秒后强杀也不能证明业务停止。

本树源码检查使用已有 SDK 检查环境，显式 `PYTHONPATH` 指向本树 `src`；不是新安装验收：

- `python -m pytest tests/test_services.py -q`：19 passed、1 skipped（Linux 上跳过原 Windows 平台反例），57.28 秒。真实 Supervisor fixture 验证继承原配置、独立日志且未自动启动；旧 daemon 缺项拒绝且配置不变，显式 shutdown 后新启动才出现新 program。SDK 缺项通过替换发现函数验证服务入口拒绝及离线状态仍可读，未冒充真实无 SDK 安装。
- `python -m pytest tests/test_reference.py -q -k 'worker_command or budget_worker'`：1 passed、17 deselected，4.28 秒，原 budget bootstrap 接缝保持。
- `git diff --check` 通过。

未验证：真实 cycle 进程启动／两 Worker queue 路由／PID 与 loop 隔离、业务 H 消费者、真实无 SDK 非 editable 安装、SIGTERM／SIGINT／70 秒强杀的业务结果。这些属于整体 worker 与安装验收；本片未以空函数或服务 RUNNING 代替这些结果。未提交或推送。
