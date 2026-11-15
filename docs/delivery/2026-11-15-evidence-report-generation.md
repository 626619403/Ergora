# 证据报告生成交付

日期：2026-11-15。基线 `f00bfdfd15173ceb0e961681679d6d3d62254bed`；范围及验收见[计划](../plans/2026-11-15-evidence-report-generation.md)，一手来源与现有能力见[研究](../research/2026-11-15-evidence-report-generation.md)。本独立 worktree 不修改统一 `docs/PLAN.md`。

## 实际进度

- 已读取根／src／tests 协作规则、组件协议、原定义／资源／preset／组合调用 owner，以及 maintainable-project-delivery、research、writing-for-agents；新项目随包 Skill 使用 skill-creator，不修改全局 Skill。
- 已精确盘点基线 31 Agent 包、49 Workflow 包（包含旧版本）；未发现专用通用报告作者。已向主协调者区分领域分析／复盘 Agent 与程序报告导出路径，并获继续这个小范围的授权。
- 指定文章 HTML 全文 HTTP 200、111,233B、SHA256 `8649db23e654ee394f94bacb4310d8d6e032272580aa5635becadc52217a6ec3`。同站 Markdown 链接 HTTP 403；官方 gallery 的 GitHub API 请求为 rate-limit 403，Git 只读 ref 成功取得 `58c305be97f47b26b678f2c07dec01d4242268ec`。失败与成功原件分开保留。
- 新 Agent／单叶 Workflow／自包含 Skill、catalog 新条目、操作页与发现入口已实现；全部正文／资源沿原 owner。Skill-creator `quick_validate.py` 通过。
- 既有冻结测试扩展第二参数后，首次为 1 通过／1 失败、4.90 秒：测试末尾仍固定期待 `root/map`，实际新叶正确为 `root/author`。仅修正测试跟随 `leaf_path`，不修改产品迁就断言；原 XML／stdout／stderr 保留为 r1，后继另存 r2。
- 真实 Codex 报告调用与只读原件复查已完成，实际范围见下文；新的独立审查仍待分配，没有 Claude 或异后端成功主张。

私有原始网页／HTTP 响应／源码与运行证据保存于本 worktree ignored `.ergora/checks/evidence-report-generation/`。公开文档只记录相对位置、身份与真实范围；不包含密钥、私人机器路径或业务代码。

## 定义、资源与发行包

新增包身份：

|资源|原 owner 计算的完整身份|
|---|---|
|Agent `ergora-evidence-report-author@1.0.0`|`f82e5acec681e9f23506fad1289c179bca83d2253450d8ee7de85c92fbc37008`|
|Workflow `ergora-evidence-report@1.0.0`|`67541349b69458a58be8ee9e5fc7fccbe405aba4e0f106bac29342972022c441`|
|Skill 完整目录|`42968e4a057ce46801f45105b1b122bb3e2640540c846360da915ef3955d292f`|
|`ergora-0.2.0-py3-none-any.whl` 原字节 SHA256|`3a95563aa38b1a6bdb79357bec630112718f705a3843995531319c911c833429`|

新包沿 `agent_definitions.inspect_bundle`／`workflow_definitions.inspect_bundle`、原目录 digest 与静态编译器通过；Skill-creator validator 为 `Skill is valid!`。精确对比固定基线，32 个旧 catalog 条目语义与 216 个旧 preset 文件原字节保持。没有修改旧 Agent／Workflow 包。

运行 `python -m build --wheel --no-isolation`；657 个实际包文件源码／wheel 逐字一致，`reference.verify()` 为 PASS／283。首版临时检查器把根 `AGENTS.md` 也视为包文件而失败；修正检查器按既有 root Python／data 包边界选取，不修改产品迁就检查。原观察保留在 `package-check-r1-failure.txt`，最终脚本、stdout／stderr、`source-manifest.json`、完整新包材料与 `package-check.json` 均保留。额外用 `python -I` 从解包 wheel 的独立路径导入并列出新 preset，根 digest 与源码相同；这是发行内容检查，未创建应用／依赖／全局 Skill 安装，不能称 site-packages 新安装验收。

## 既有冻结接缝与公开 CLI

既有 flow-map 冻结测试只扩展一个 `evidence-report` 参数，检查幂等导入、原 training v1/v2 身份、唯一叶 role／权限、完整祖先来源、删除源定义库后仍从完整 manifest 准备输入。首轮 r1 1 通过／1 失败、4.90 秒；末尾遗留 `root/map` 的测试断言修为配置的 `leaf_path` 后，r2 为 2 通过、38 deselected、4.62 秒。没有新增测试文件或 CI。失败不是报告包／继承错误，产品未因该修正变化。

r1 的原 XML／stdout／stderr 未覆盖。r1 测试源码是在失败后按唯一修正反向重建，并和原 traceback 对照，保存在 `preset-regression-r1-test_presets.reconstructed.py`；这不是运行前冻结副本，`preset-test-source-identities.json` 明确记录此局限。r2 当前测试文件 SHA 与重建 r1 SHA 分别记录，不将后来的源码冒充 r1 原件。

真实独立 State 已沿公开 CLI 成功完成 preset 导入、project add、show、prepare-manifest、prepare-from-manifest、verify-input --material、check-input。每步真实 argv／退出码／时长和完整 stdout／stderr 分别保存；根与叶均 read=[definitions]、write=[]、shell=false、network=[]，提示包含三份 root／author／Skill 完整正文。输入只有实际提供的摘要及清楚标明的合成显示探针；没有赋予 workspace、网络、shell 或 MCP 权限。

## 真实报告作者与派生视图

沿原 `composition run-input` 明确选择 Codex text-only，后端原因为 `Explicit authorized Codex report author; Claude not attempted`。复用原已授权的私有推理配置，副本只在 ignored 目录、0600，凭据沿环境变量引用；值不进入公开文档或报告。没有尝试 Claude，不以 CLI 存在冒充其成功。

|原件／派生物|实际身份与范围|
|---|---|
|原 run|`3a08dd0bb80448269cfe222f79ef6d15`；succeeded，实际 CLI 用时 89.084 秒|
|完整输入 digest|`bc26f668b7ad71c23fbe7e0b6bb49d39e6ff9283a6af2556b4f07e0645569abd`|
|原 prompt|12,496B，SHA256 `a7ddda17e473b38e2008a0fe01dd521604dfc9a01056c41a4c4b23743dce129b`；prepared／saved input／protocol／实际 stdin 逐字相同|
|原 result|12,098B，SHA256 `6c9b22e1486fe60758827ade6c15bcf17cbf3fd07bff1dae1debbeda3546b662`；原 input／prompt／result 均 available|
|response 原字符串 `views/report.json`|11,670B，SHA256 `140f61fd910fb3eba5878e5ca30cf84c8cd264f1f6c9c4416fc0067e7e279e11`|
|`views/report.md`|3,890B，SHA256 `1feb15884bfe36d50fc8505b58e7cdcbb8de57d5bda1646389e3823587933db5`|
|`views/report.html`|6,181B，SHA256 `fc0d9bd7cf225cfa0969c0035de9fefa56920b8a673c907d6cff2d0b6a557adc`|

三份视图只从原 result 的 `artifacts.response` 解码写出，没有手写、替换或修饰 HTML 冒充 Agent 输出。原 run 保存实际 argv／stdout／stderr／result 和全部冻结资料；`real-call.py`／每步 command JSON／`observation.json`／`report-check.json` 保留了完整调用与读取事实。

实现者对照两视图读过相同的结论、包身份／检查值、首次失败与测试修正、来源摘要的边界和所有未验证项。作者没有把“收到 SHA”说成自行重算，也没有把 657 文件观察扩大为训练、性能或报告准确率证明。XML suite 秒数 4.353／4.115 按原摘要保留，不和 pytest CLI 总时长 4.90／4.62 混为同一口径，更不作性能比较。没有测量图；合成 `<script>` 显示探针在 Markdown 与 HTML 中均保留原换行和字面文本。

HTMLParser 与源内容检查未发现 script／事件处理／iframe／form／外部资源或 CSS import／URL，存在限制性 meta CSP，探针解析为文本。此检查只针对本次产物，不是通用 HTML sanitizer 或浏览器安全／布局认证。没有安装浏览器或渲染框架，没有加载 CDN；浏览器视觉／打印／可访问性交互仍未测。

清除已知推理凭据变量并把 PATH 设为不可用工具目录后，再执行同一精确 `inspect-run`，exit 0／0.306 秒、完整观察与首次相同，19 个原 run 文件 SHA 保持，模型新调用 0；`formal_execution_authorized` 仍为 false。原状态和执行／批准 owner 未被派生报告改变。

## 完整范围、检查与未交付项

范围为 12 个公开文件：现有工作流手册／catalog／preset 测试三处修改，新操作页／plan／delivery／research 四份文档，Agent 三文件与 Workflow 两文件。Python 产品 owner、已发布包、原报告命令、全局 Skill、业务仓库与统一 `docs/PLAN.md` 均未修改。70 个本地 Markdown 链接目标存在，已手工核主要章节锚点；`git diff --check` 通过。完整 tracked diff、untracked 清单／正文和 SHA manifest 保存在私有 `review/`，供 fresh reviewer 直接核对。

本片只有实现者的上述静态、冻结／包和一次真实小报告验收。尚未做新的独立审查、新应用安装、Claude／异后端验证、浏览器布局、系统性报告事实准确率评测或真实 GPU／训练／质量／收益验证。未提交、推送、发表评论或发布报告。已向主协调者交完整可审范围，等待其分配 fresh-context 独立需求／维护性审查；未以自身检查标记完整交付。
