# 全新 Linux 环境安装

支持 Ubuntu 24.04 / Linux x86_64。目标系统只需预装操作系统自带 Bash、apt 与基础命令。安装 Linux 包需要系统/容器内部 root 或 sudo 权限；模型认证和项目配置在安装后完成。

## 推荐：单文件安装器

从 HTML 下载 install-agentflow.sh，在目标系统执行：

```bash
bash install-agentflow.sh
source ~/multi-agent-platform/env.sh
```

安装器先补齐 Python 与 Linux 支持包，把内嵌源码包解压到 ~/.local/share/agentflow/installers/，再安装 Node.js、uv、Codex、Temporal、Symphony 和版本锁定的 Python 环境。无需预先安装这些工具或配置 ~/.codex。

安装需要联网访问 Ubuntu 软件源、nodejs.org、GitHub、registry.npmjs.org 和 Python 包索引。脚本不会登录模型账号、启用项目执行或开始训练。

## 源码 ZIP 路径

先用系统包管理器安装 unzip，再解压 ZIP 到 home 中的新目录，进入包含 install-from-report.sh、BUNDLE-SHA256SUMS、platform/ 的目录：

```bash
bash install-from-report.sh
# 已有 Python 时，可先做无安装检查
bash install-from-report.sh --check
```

--check 校验源码完整性、目标冲突与运行缓存缺口，不下载和启动服务。实际安装会先安装 Linux 支持包；存在不同内容的源码或 home 脚本时停止，保留用户内容，需人工审阅升级差异。

## 认证与首次使用

```bash
python3 ~/multi-agent-platform/bootstrap/configure-model.py \
  --model YOUR_SUPPORTED_MODEL_ID \
  --base-url https://api.openai.com/v1 --env-key OPENAI_API_KEY
```

通过自己的 Secret 管理方式提供 OPENAI_API_KEY；兼容网关可替换 URL、模型和变量名。实现与独立新会话审查共用同一份 Codex 配置。安装不包含任何使用者的 API key 或登录状态。订阅登录和 adapter 的 API 认证不应混淆。

按部署手册准备可信项目执行容器，检查并明确启用：

```bash
agentflow sandbox probe
agentflow execution enable --trusted-current-container
agentflow services start
agentflow doctor
```

裸 Linux 也可安装控制面与模板；自带执行器仅在检测到支持的容器并明确确认后可用。更多部署选项见 README.zh-CN.md。容器里的 home 必须持久保存。

## 固定版本与缓存

工具版本与摘要见 platform/bootstrap/report/public-release.json、platform/downloads/temporal-cli.json 和 platform/upstream/symphony/upstream.lock.json。Node/uv/Temporal 归档、Symphony 二进制校验 SHA256；Codex 使用 npm 锁定完整性；Python 使用哈希锁。

Symphony 官方 nightly 地址会滚动。摘要变化时安装停止，不接受未审阅的新文件；可以提供已核验的运行缓存，或按锁定 commit 的官方说明构建。--runtime-cache DIR 接受包含 downloads/temporal-cli.tar.gz、bin/symphony，以及可选 downloads/node.tar.xz、downloads/uv.tar.gz 的缓存目录。

运行缓存不包含完整 Python wheel 和 npm 缓存，不是离线镜像。SHA256 提供内容完整性校验，不替代来源认证。

两个完整手册随包提供：platform/README.zh-CN.md（部署与日常使用）、platform/docs/TRAINING.md（训练优化）。还包含 platform/docs/VALIDATION.md、项目接入任务、三个模板与全部可复用协议源码。没有用户配置、任务数据库、项目代码、模型权重或预设验收结论。
