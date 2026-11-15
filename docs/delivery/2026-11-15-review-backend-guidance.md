# BR1：审查后端说明交付记录

日期：2026-11-15。需求和验收见[具体计划](../plans/2026-11-15-review-backend-guidance.md)。固定基线 `f00bfdfd15173ceb0e961681679d6d3d62254bed`，分支 `docs/review-backend-guidance`；开始时独立 worktree 干净。

## 当前状态

实现及适用源码检查完成，fresh-context 独立审查待主控安排。未提交、推送、安装或运行厂商审查；当前检查不认证模型效果或发布安装。

初始已读本 worktree 根／src／tests 协作规则、组件协议、当前计划、领域审查实现与 G1a 不可变 catalog 补丁。采用 maintainable-project-delivery、writing-for-agents、skill-creator、research 和 OpenAI Docs；本片是主控明确委派的独立研究／实现工作，额外并发槽已占满，fresh-context 产品审查由主控安排。

真实消费者为两个领域根下的通用结构／正确性／测试价值三叶及领域叶。现有 `CodexBackend.command` 是 `exec` 结构化调用，`ClaudeCodeBackend.command` 是 print／JSON 调用；两者均未封装原生 review 命令、插件或托管产品。没有独立名为 quality-reviewer 的 PR preset，优化 measurement reviewer 不纳入本片。

已直接读取用户指定的官方页面和 OpenAI GitHub／CLI 页面。网页工具返回不可调用，改用无认证的公开 HTTPS 获取；OpenAI 旧路径重定向到 `learn.chatgpt.com`。Anthropic 三月文章仍保留 preview 与当时成本／耗时叙述，不能由文章推断今日可用性；现已核当前服务、安装、认证、费用、原生命令、公开插件与 CI。[完整研究](../research/2026-11-15-review-backend-guidance.md)区分当前 Codex GitLab beta、Claude 会话 MR 发评与 Anthropic GitHub 托管服务。

## 后续验证

本记录接续保留来源、旧新包身份、实际命令／结果和未验范围。只运行原本适用的静态与源码检查，不安装，不执行厂商模型或对外发表意见。主控统一维护 `docs/PLAN.md`，本 worktree 不改该文件。

## 首轮检查

两份窄 Skill 的原 `quick_validate.py` 均通过；原领域 preset 冻结／祖先材料测试 **2 passed／8.73 秒**。临时旧新包验收 r1 错把可追加的 library `index.json` 也当作不可变 object，安装新版本后在该断言失败；已确认 index 合法新增 1.0.1 映射，旧对象仍在。保留 r1 脚本／失败输出，r2 改为核全部旧 object 字节和全部旧 index 映射，使用新的隔离目录；产品未因该脚本失败变更。

## 新旧身份与最终源码验证

新增 `ergora-pretraining-review@1.0.1`／`ergora-posttraining-review@1.0.1` 两个完整根，原 instructions 字节、全部节点／叶引用、图、permissions、limits 和后端保持。唯一新增资源是四叶继承的同名 `ergora-review-backends` Skill，两个可分享包中的资源内容逐字相同；没有在五个叶中分别增加矩阵。

|定义 ID|旧 1.0.0 digest|新 1.0.1 digest|
|---|---|---|
|`ergora-pretraining-review`|`d482a88fd372d0e8fd862841249f1821ee08de874e20190e7811346b0fde4be7`|`654b5c49875556a31e6982e33a066623106980d9bbc73366d5a45f4eaf4a118a`|
|`ergora-posttraining-review`|`7206e155114560e55beb54e2d62528c7d18e11cf3d8a77e9687588d614e328e3`|`7023d0de86de0c61811b644bea6cd782057e3ee538ceba52c3c98f173b04bbca`|

原 owner 计算两份 Skill 的完整目录 digest 均为 `05cf4cbad8ec9a6971b0695c7c48611566bd17e4581e164a8bce5647092cd6f3`；单个 `SKILL.md` 为 5,097B，文件 SHA256 `56ef96fcecc5ec1e3ba1dbb66721085bb5e733f95e76f0c4aa7dc29ab654092b`。

实际检查及原件保存在 `.ergora/checks/review-backend-guidance/`：

- `PYTHONPATH=src python -m pytest -q tests/test_presets.py::test_domain_reviews_keep_general_identities_and_frozen_ancestor_material`：**2 passed／8.73 秒**；核当前 preset 幂等安装、旧通用身份、required／all-join、冻结包脱离源库及所有叶的完整祖先提示。
- 两份 Skill 各由原 `skill-creator/scripts/quick_validate.py` 检查通过；原 workflow inspector 接受两个完整新包。
- 临时 `check-invariants.py` r2 成功：全部 **216 个原 preset 文件**的字节／执行属性与固定基线相同；32 个 preset 名称不变，**30 个无关条目保持**；两个相关条目仅切换 root 并追加新依赖。
- r2 用原 owner 分别建立旧库／旧 manifest／四份旧叶输入，再重复安装当前 preset：每领域 **24 个旧 object 文件**和旧 index 全映射保持；旧 manifest／八份旧输入字节不变，从同一旧 manifest 再准备的八份输入摘要与字节亦相同。新根八个实际叶保留原引用／默认 backend／只读权限，每叶完整 prompt 含一次来自根的共享 Skill。
- 完整变更范围的 9 份 Markdown、80 条本地链接路径、24 个引用定义及行尾空白扫描通过；12 个研究来源快照摘要与实际原件匹配，八份新 prompt 均直接核到共享 Skill 正文恰好出现一次。50 处外链不是该静态扫描的联网验收，事实来自研究的已读原文。`git diff --check` 通过。

## 审查交接与未验范围

范围共 **12 个文件**：三处 tracked 修改为 `presets.json`、`TRAINING_REVIEW.md` 与 `WORKFLOW_DEFINITIONS.md`；九个 untracked 为本片 plan／delivery／research，以及两个新根各自的 workflow／instructions／Skill。完整含新增文件的 patch、scope／untracked 清单与原件可由主控直接检查；本片未操作其他 worktree 或 index。

本地实现可审，独立审查仍待安排，不能把实现者检查记作独立通过。没有增加产品测试、CI、runtime 或依赖；未构建／安装 wheel、运行真实 Codex／Claude Code 或任何厂商托管／插件／CI 审查，未核用户认证／套餐／组织设置，未发表意见／approve／merge，未修改业务仓库。安装包交付、后端可用性和任何质量／数值／分布式／训练／性能声明均未由本片验收。
