# training-optimization

本地操作说明：~/multi-agent-platform/docs/TRAINING.md。
先按项目填写 workload-contract.md、baseline.json、experiment.json 和 runner-template.example.json；人工审阅合同后再批准，示例中的提交、指标和 PASS 不能作为真实实验依据。
每次只手动启动一个精确实验：training prepare → worker-start → start → run-local（确认 manifest SHA）→ status/result。没有常驻训练队列消费者。
固定 perfctl 证据门禁通过后才等待人工放行；放行只创建该项目的集成/复验任务。
真实训练使用项目自己的环境；模板不安装 CUDA/PyTorch，也未测量任何 GPU 性能。

开发与集成复验使用 Codex 实现及独立新会话审查；实验的独立审查证据由项目可信流程提供。
