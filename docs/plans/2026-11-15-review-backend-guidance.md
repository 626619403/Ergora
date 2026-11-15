# BR1：审查后端说明与不可变根补丁

日期：2026-11-15。固定基线 `f00bfdfd15173ceb0e961681679d6d3d62254bed`，分支 `docs/review-backend-guidance`。本片在独立 worktree 完成；主计划由主控统一排期，本片不修改 `docs/PLAN.md`。逐步证据见[交付记录](../delivery/2026-11-15-review-backend-guidance.md)。

## 需求与实际入口

核对用户指定的 [Anthropic Code Review 文档](https://code.claude.com/docs/en/code-review)与[产品文章](https://claude.com/resources/articles/code-review)，并沿 OpenAI 官方来源核实 Codex 对应能力。说明不同后端的原生 PR／MR 审查方式、安装／认证／可用范围、结果与副作用，区分托管产品、公开命令／插件、自建 CI 与 Ergora 后端调用。

现有 `pretraining-review`／`posttraining-review` 均选择 1.0.0 根；每根包含通用结构／正确性／测试价值三叶和一个领域叶，required／all-join。没有独立名为 quality-reviewer 的 PR 模板；measurement reviewer 的质量证据检查属于优化流程。实际 Codex／Claude Code driver 使用原结构化 Agent 调用，没有封装厂商原生 review、插件或托管审查。

## 小范围实现

- 保留全部旧 Agent、Workflow、manifest 与已准备输入的身份和字节。按 [G1a catalog 惯例](2026-11-14-memory-preset-patch.md)新增同 ID 的两个 1.0.1 根，原 preset 名称选择新根并导入旧／新依赖，不增加版本别名。
- 新根各封装同名、同摘要的窄 `ergora-review-backends` Skill，使通用三叶和领域叶通过原祖先链读取。完整包须可独立分享，因此两根保存相同资源字节；长产品比较只在一份研究维护，不写进五个叶或另建调度。
- 原图、叶引用、默认后端、权限、限制、输出和人工发布边界保持。模板仍按实际 backend-neutral 合同工作；来源链接不授予网络、安装、shell、平台写入或订阅能力。
- 在领域审查手册说明新默认根与该资料的继承范围；旧独立通用根和优化 reviewer 仍按其原包读取。

## 验收与边界

- [x] 核实官方页面，记录日期、来源身份、历史文章与当前文档的差异及未验范围。
- [x] 由原 Skill／bundle owner 计算新摘要，检查旧包与无关 catalog 条目保持；新／旧根均可编译。
- [x] 运行适用的既有 preset／资源检查；检查两个新根的四叶继承和旧 manifest／input 字节保持，不增加措辞测试或 CI 矩阵。
- [x] 检查完整 diff、untracked、文档链接路径及空白，准备交主控的审查材料。
- [ ] 主控安排 fresh-context 独立审查并处理实证 finding；通过前状态保持待审，不提交／推送。

不安装第三方工具或本项目，不运行真实厂商审查／平台写入，不发表评论、approve、merge，不改业务仓库、runtime、CI、依赖、全局 Skill 或其他 worktree，不提交／推送。源码检查不认证认证状态、订阅、托管服务访问、模型效果、训练质量、GPU 或性能。
