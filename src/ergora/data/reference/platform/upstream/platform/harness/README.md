# 仓库 harness：先建立反馈，再扩大代理权限

这是可运行的最小检查器和仓库文档起步包。使用 Python 标准库，不安装模型，不调用外部服务。
入口为 `harness.py`；退出码 `0` 表示该检查通过，`2` 表示阻塞。
检查通过只覆盖下面列出的规则，不能替代产品验收、测试、安全审查或人工风险判断。

## 1. 在新目录生成待审查模板

从工具包根目录运行：

```sh
python platform/harness/harness.py init --destination /tmp/repo-harness-staging
```

目标目录必须不存在；没有覆盖已有 `AGENTS.md` 的命令。
把需要的文件合并到仓库的独立 PR，填写负责人、命令、目录与模块映射；不要直接覆盖现有规则。
`harness-policy.json` 中的 `src/app.*` 是示例，必须替换为真实 Python 源码根与层次。
源码根是可导入包的父目录；测试、生成代码、vendored 代码是否纳入应显式决定并记录。
每个源文件使用最长模块前缀匹配一层；未分层文件阻塞。包的 `__init__.py` 也要归属一层。
同层依赖允许；跨层依赖必须出现在 `allowed_edges`。

## 2. 识别旧债务并单独审批基线

在已知基准提交的只读 checkout 扫描。`/trusted` 路径代表受 CI 管理的目录，不能由候选代理写入。

```sh
python platform/harness/harness.py scan \
  --repo /checkouts/base \
  --policy /trusted/harness-policy.json \
  --out /tmp/base-scan.json

python platform/harness/harness.py baseline-proposal \
  --report /tmp/base-scan.json \
  --out /tmp/baseline-proposal.json
```

`scan` 输出完整发现及覆盖范围；已有架构违规、断链和超长文件可形成债务提案。
解析失败、缺失扫描根、未归属模块、动态导入等覆盖缺口属于硬错误，不能加入基线。
`baseline-proposal` **只生成提案**，不批准任何债务。经仓库负责人单独审查后，由 CI 从受保护分支
获取已接受基线、固定其 SHA256，并限制候选执行器写入。CLI 中的哈希不替代平台身份认证。

## 3. 对候选运行质量门禁

```sh
python /trusted/harness.py check \
  --repo /checkouts/candidate \
  --policy /trusted/harness-policy.json \
  --baseline /trusted/baseline.json \
  --baseline-sha256 "$HARNESS_ACCEPTED_BASELINE_SHA256" \
  --out /tmp/harness-gate.json
```

在 CI 受保护环境中设置 `HARNESS_ACCEPTED_BASELINE_SHA256`。不要从候选 PR 的文件或环境定义读取它。
无历史债务的新仓库省略 `--baseline` 和 `--baseline-sha256`，要求零发现。
所有输出文件采用创建模式；重跑用新的输出路径，防止无声覆盖旧证据。

门禁比较稳定发现标识，分别报告新增、仍存、已解决债务。减少一个旧问题不能抵消一个新问题。
已有超长文件允许缩短，继续增长会阻塞；策略或扫描器版本变化必须走独立基线迁移。
持续降低基线时重新扫描、审查并合入新基线，不能让 agent 在功能 PR 中自动“接受当前状态”。

## 4. 核验最终 Git diff 的真实写入范围

`input.allowed_paths` 只是任务声明。最终 `scope` 检查使用 `git_scope.py` 对真实 Git 对象验证：

```sh
python /trusted/platform/harness/git_scope.py \
  --repo /checkouts/final-candidate \
  --candidate "$FINAL_CANDIDATE_SHA" \
  --spec /trusted/tasks/execution-spec.json \
  --policy /trusted/scope-policy.json \
  --out /evidence/scope-result-r1.json
```

`--spec` 是已获准的不可变执行快照，由 `dev_platform.registry.make_spec(request)` 生成；
不是任意代理自填的 JSON。项目策略参考 [scope-policy.example.json](scope-policy.example.json)，
从受保护配置读取，不能让候选 PR 用自己的策略核验自己。

此检查要求：完整提交 SHA、实际 checkout 的 HEAD 等于候选、工作区干净、候选由固定基准派生。
验证 checkout 必须完整且无子模块；拒绝 partial / promisor / sparse 配置、
`assume-unchanged` / `skip-worktree` 索引标记，以及配置了可执行 clean / process filter 的仓库。
Git LFS 等依赖 filter 的项目需要单独批准的验证适配器，不能把此检查器的拒绝改成 PASS。
runner 应使用专用、已冻结的验证 checkout；检查期间代理不得并发改写文件、索引或 Git 配置。
逐文件检查允许目录及模板 / 项目保护目录，重命名作为旧路径删除和新路径增加分别核验。
可配置文件数和文本增删行数上限；开启行数上限时，二进制改动无法计数，直接阻塞。
异常路径、非 UTF-8 路径、变更的符号链接和含子模块的基准 / 候选也阻塞，需额外批准的专用校验。
报告绑定基准 / 候选 SHA、任务 / 模板 / 策略哈希。违反范围输出 `FAIL`，退出码 `2`；通过为 `PASS` / `0`。
输出文件必须新建且位于 checkout 之外；重跑换一个证据路径。

读取 Git 对象前先检查生效配置（含 include / worktree 配置），拒绝可能触发转换或延迟拉取的仓库。
只运行 Git 内建配置、索引、对象与 diff 命令，禁用 hooks、外部 diff、textconv 和传输协议；
不递归运行子模块 status，不执行仓库脚本，不修改用户 Git 配置。
适配器仍须证明仓库远端身份、任务授权和最终集成提交的来源；本检查不验证运行时行为，
也不把工作区声明当作 OS 沙箱。忽略文件与工具安装目录的隔离由受信任 runner 保证。

## 已实现与明确边界

| 检查 | 实际覆盖 | 不覆盖 / 接入建议 |
| --- | --- | --- |
| 仓库地图 | 必须存在的文档、普通 Markdown 行内及引用式本地文件链接 | 不检查远程 URL、标题锚点、HTML/MDX 链接、文档语义与更新日期；另接文档构建器和独立审查 |
| 架构 | Python AST 的静态 `import` / `from`，包括相对导入；内部模块的已配置层间依赖 | 不证明运行时调用图；动态导入直接阻塞；自定义导入器、alias 后调用、反射等必须另行检查 |
| 覆盖完整性 | 缺失 / 空根、未归属模块、语法错误、重复模块、符号链接 | 不扫描 `.git`、虚拟环境、`node_modules`、`__pycache__`；不自动发现未配置的源码根 |
| 大小规则 | 配置范围内 UTF-8 Python / Markdown 文件行数及已有超长文件增长 | 不等价于复杂度、可维护性或质量评分 |
| 旧债务质量门禁 | 精确发现对比、固定策略哈希、可信基线内容哈希 | 不认证批准者身份；必须由 Git / CI 权限实现 |

其他语言用项目已有的语言工具生成独立门禁，例如 TypeScript 的 [dependency-cruiser](https://github.com/sverweij/dependency-cruiser)、
Java 的 [ArchUnit](https://www.archunit.org/)、Python 更完整的契约可用 [Import Linter](https://import-linter.readthedocs.io/)。
这里只提供链接，不把未安装工具算作已运行验证；CI 适配层将这些检查结果绑定到最终候选 SHA。
保留“未运行 / 不支持 / 不适用（附理由）”状态，不能统一转成 PASS。

## 两类任务怎样使用

**仓库治理**：先记录现状与失败 → 选择一个可验证、可回退的小改动 → 检查行为与质量门禁 →
独立审查 → 待合并。优先治理变更频繁且缺少反馈的区域，不做全仓库重写。

**大型变更**：先写入执行计划、接口契约和依赖图 → 锁定每个单元的独占路径 →
并行实现互不依赖的单元 → 集成后重跑所有验收 → 兼容 / 迁移 / 回滚演练 → 独立审查。
单元通过不能沿用为集成提交的通过证据。

相同的检查器对两类任务共用；任务模板决定需要哪些检查与人类决策，不复制一套独立平台。
审查结果应包含任务、提交、检查命令、原始输出、尚未覆盖的风险和责任人。

## 对文章的取舍

依据 [OpenAI《Harness engineering》](https://openai.com/index/harness-engineering/)（2026-02-11），采用短入口文档、
仓库内版本化知识、可执行架构约束与持续的小步治理。该文章描述特定团队的实践，不是所有仓库的保证；
这里保留独立验收、受保护的规则更新和人工发布边界。示例层次由项目配置，不要求照搬文章的层名。

测试：`python -m unittest discover -s platform/tests -p 'test_*scope.py' -v`；
文档 / 架构 / 债务测试：`python -m unittest discover -s platform/tests -p test_harness.py -v`。
