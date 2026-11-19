# 安装与日常使用

简体中文 · [English](../../install/linux.md) · [文档目录](../../README.zh-CN.md)

Ergora 提供 Linux / Windows 本地 CLI 与图形控制面，并保留 v2.2 的完整六阶段 Linux 参考发行。控制面可以先独立使用；项目工具、工单、服务和实验环境按需接入。Windows 的 PowerShell 安装、Agent 与 WSL2 范围见 [Windows 手册](../../install/windows.md)。已实现的能力和实际验收范围见 [计划与进度](../../PLAN.md)。

第一次选择模板时，可沿[三模板入门旅程](../../development/templates.md)完成专家组合、逐实例后端、页面v6创建、原ID恢复与训练提案，再回到本手册查具体命令。

已有本地候选可先使用[精确 PR／MR 审查材料包](../../review/materials.md)：无需项目登记或模型登录，直接冻结完整 Git 对象、原需求、显式调用者与祖先规范；也可用`review collect`只读绑定明确的GitHub／GitLab来源，再离线核包。自动领域审查与远端发表意见分别实施。

## 从空环境安装

基础环境为 Linux、Git、Python 3.11+、venv / pip。Ubuntu 24.04 可以先安装系统基础包：

本文使用包含当前组合／执行功能的 `main` 分支。已有clone先选择 `main`，或固定所需验收记录的完整提交，再运行该源码中的安装器；仅凭相同包版本号不能确认源码身份。

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git python3 python3-venv
git clone --branch main https://github.com/626619403/Ergora.git
cd Ergora
bash scripts/install.sh
export PATH="$HOME/.local/bin:$PATH"
ergora serve
```

在服务所在机器打开 `http://127.0.0.1:8977`。网页资源和图组件随 Python 包安装，不需要 Node、运行时 CDN 或前端构建。安装脚本把应用放在 `~/.local/share/ergora-app/venv`，命令放在 `~/.local/bin/ergora`；运行数据默认放在独立的 `~/.local/share/ergora/`，可用 `ERGORA_HOME` 或全局 `--home` 指定持久目录。容器应持久化这些目录及业务仓库。

已经有 Python 时也可以在自己的环境安装：

```bash
python3 -m venv .venv
.venv/bin/pip install '.[web]'
.venv/bin/ergora serve
```

### 选择安装组合

默认组合为`control`。可在源码目录运行`bash scripts/install.sh --profile development`或`--profile research`；Windows使用`-Profile`，见[Windows手册](../../install/windows.md)。

|组合|安装的SDK|另需配置|
|---|---|---|
|`control`|Web控制台|所选Agent CLI及认证；本地项目可先用SQLite与手动操作|
|`development`|Web、Temporal|完整六阶段需Linux/WSL2参考运行时、服务及Agent|
|`research`|Web、Temporal、GEPA|评价器、提案器、所选资料/实验服务；GPU工具按任务安装|

安装后运行`ergora tools profiles`查看同源配方；本地API为`GET /api/installation-profiles`。该描述是安装配方，实际状态另看`ergora tools doctor PROJECT`及任务验收。安装组合不启动服务、登录模型或执行训练。SDK存在不代表服务可连接、工具已认证或效果已经验证。

原有`--with-gepa`、`--with-temporal`仍可使用，按集合添加到所选组合，例如`bash scripts/install.sh --profile development --with-gepa`。在同一目录重跑安装器可升级或补装；改回较小组合不会自动卸载已装SDK。源码特性尚未发布时，先切换到维护者提供的功能分支。

### 准备离线依赖

在联网环境为目标OS、Python版本和架构准备全部构建/运行wheel，再在同类环境安装。以下命令在源码目录执行，缓存目录可自行指定：

```bash
mkdir -p "$HOME/.local/share/ergora-tools/wheels"
python3 -m pip wheel --wheel-dir "$HOME/.local/share/ergora-tools/wheels" \
  '.[web,temporal,gepa]' setuptools wheel
PIP_NO_INDEX=1 PIP_FIND_LINKS="$HOME/.local/share/ergora-tools/wheels" \
  bash scripts/install.sh --profile research
```

安装器继续通过pip读取本地源码和缓存。缺少兼容wheel或构建依赖时，pip会明确失败，补齐缓存后重试。离线缓存不包含外部Agent、参考服务二进制、系统包或模型；它们按各自说明另行准备。Windows也使用pip的`PIP_NO_INDEX`/`PIP_FIND_LINKS`环境变量及适合Windows的wheel。

控制平面安装器和 current-native 源码准备不会配置完整原生运行时。冻结发行版保留原范围。当前正式执行前，请阅读[实际源码/依赖/环境配置门禁（英文）](../../install/linux.md#prepare-the-formal-reference-runtime)。
