# Symphony 连接模块验证记录

日期：2026-10-26（新加坡）。版本1.1。

## 真实运行过的部分

- 官方 Symphony 源码已读取并固定到 `be10a1b79df723d6d7612b5651c8522704dafb2e`。
- 官方 Linux x86_64 Burrito 二进制 SHA256：`08d7aac26747fdc14022ade870cf7e530a6343ab92a040f39a4294b27a0cd5af`，与其发布校验文件相符。
- 实际启动原生 Symphony，并通过HTTP读取 `/api/v1/state`；空 memory tracker、0个agent、0个模型token。测试结束已停止该进程。
- 生成的WORKFLOW前置配置经过原生加载：仅将tracker换为空memory并将目录/端口换为临时值，不接真实GitLab/GitHub。
- 新增25项自动化测试全部通过：24项协议/逻辑测试；1项真实Temporal ephemeral test server集成测试。
- 集成测试使用SDK `temporalio==1.34.0`、现有 `ExperimentWorkflow`，验证start、重复start找回、同ID不同URI拒绝、人工release、最终review路由。GPU/审批adapter为测试替身。
- Python编译检查通过。文档与部署包已加入新模块；HTML下载、筛选、复制与移动端检查另由主文档验证流程执行。

## 覆盖的故障

未准入、准入过期、基线改变、issue关闭/失去ready、重复请求、改写同ID请求、start回执丢失、bridge重启、已记录提交意图但执行查不到、同issue并发候选、tracker失败后恢复、门禁通过但未release、失败路由、旧结果更新新head、路径符号链接、issue/workspace身份冲突、终态Rework与收据绑定、GitLab增删标签、GitHub部分标签更新重试、控制面环境变量隔离。

## 未完成且不能声称完成

没有访问用户真实GitLab/GitHub、项目仓库、Codex登录会话、Temporal Cloud、GPU集群或SSO。没有模型调用，没有发布issue评论，没有提交真实实验，也没有合并代码。生产挂载权限、服务身份、commit/push入口、真实API行为和资源准入由README的试点工单验收。

测试服务会报告heartbeat能力告警；本流程使用短activity，不依赖该能力保存进度。此测试不替代真实Cloud兼容性验证。

## 重现

```bash
python -m pip install -r requirements.txt PyYAML==6.0.3
RUN_TEMPORAL_INTEGRATION=1 python -m unittest discover -s tests -v
python native_smoke.py --binary /path/to/symphony
```

bridge采用单主机持久SQLite台账，不提供分布式exactly-once证明。正式实验副作用仍由Temporal和现有runner幂等registry共同约束。
