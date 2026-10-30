# large-change

复制 input.json 到具体项目，填写真实目标、路径、验收标准和 work_units。
每个项目独立注册；本地任务使用 --tracker local --project local/项目名，接入 GitLab 后绑定真实项目。
盘点 → 计划 → 人工批准 → 分单元实现 → 集成 → 命令验证 → Codex 独立新会话审查 → REVIEW_READY。
平台不自动合并。命令验证读取项目注册时的 checks.json；本模板不提供默认 PASS。
当前 Docker 是外层安全边界，Git worktree 只负责工作目录管理。
