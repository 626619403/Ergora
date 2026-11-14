# G1d-CI：纯交付记录的检查范围

承接用户要求的冗余测试／CI审计和[G1交接](2026-11-14-integrated-handoff.md)。固定基线`6c7c45f79e499dde83d9880043342710a28d7809`，其自己的CI43589988699在途，闭合前不推送后继。该候选只改九个文档／交付摘要路径，仍按原规则触发八job／30必要步骤；这次原运行保留，不取消或追溯更改门禁。

## 依据与最小变更

原`portability.yml`已忽略Markdown、README和AGENTS，未忽略交付JSON。静态搜索`src / tests / scripts / .github / pyproject.toml`未发现对`docs/delivery/evidence`的读取；这些文件是验证摘要／原件指纹，不是随包合同、原生输入或测试fixture。只在push的`paths-ignore`增加`docs/delivery/evidence/*.json`，仅覆盖该目录直接子级JSON；其他文档资源、嵌套路径、产品、schema、例子、测试、依赖、安装器和CI配置仍按原规则触发。

不增加另一套过滤脚本、独立test/CI job或手写GitHub glob解释器。JSON语法、引用身份和范围沿各片原发布检查与独立审查；本次不把它们变成运行时输入。PR和workflow_dispatch保持原触发，job矩阵、时限、必要步骤、artifact及concurrency不改。

## 可验收节点

- [x] 独立审计指出实际纯记录候选触发完整CI成本，核现有消费者与原触发配置，固定范围。
- [x] 改一个push过滤项，核实际完整diff及产品／installer／测试／依赖不变；使用已有解析工具做必要静态检查，不新增产品测试。
- [x] 新fresh-context需求／维护性两轴审查，处理实证finding，保存报告与原件；两轴本地approve／开放0／0，R1旧状态措辞关闭。
- [x] G1b自己的精确CI和原reviewer闭合后，与已独立审查的G1c手册共同普通发布77d1736；此候选自己的CI43591668528八job／30步骤成功，原reviewer固定发布与CI终核两轴approve／开放0／0。不借前片成功，不合main。
- [x] 最后纯记录同步5cc463b的11路径／普通推送／完整Ref已获原reviewer最终两轴approve／开放0／0；7同步原件和3观察件身份匹配。官方捕获25条中该SHA的Portability为0，原77／43591668528仍在，结论限捕获时点／范围，不凭无新run宣称产品通过。后续报告完成记账按AGENTS不递归审查。

本片属于记录成本优化，不是削减产品回归；如果未来生产／测试确需读取该目录，接入时必须同步修订此触发边界。
