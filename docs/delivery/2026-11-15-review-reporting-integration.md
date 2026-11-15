# BR1／BR2 隔离整合逐步记录

日期：2026-11-15。整合基线 `a4371c8e19ddf32d5dbe1d57cf88f9e638baf373`，分支 `integrate/review-reporting`。原始要求、范围和验收见[计划](../plans/2026-11-15-review-reporting-integration.md)。组合实现与本地验证已形成可审候选；新的组合独立审查待主控另配，无提交／推送／完成结论。

## 1. 恢复与边界

已读根／src／tests 合作规则、组件协议、总计划、并行 BR 计划／交付，以及两源各自的具体 plan／delivery／research／独立审查报告。采用 maintainable-project-delivery 保存逐步证据。主工作树固定 HEAD 为 `a4371c8`，两个源分支均为 `f00bfdfd`；新建独立持久 worktree／分支前核实不存在同名分支。

BR1／BR2 原独立需求／维护性审查均 approve／开放 0／0，仍只归其原范围。两源均改 catalog 与工作流手册，需组合验收；其余改动没有路径冲突。主工作树 c1b1 正在运行，未复制或修改其未提交源码／测试。下一步冻结两个完整候选，然后整合并验证新包。

私有验证原件位于本 worktree ignored `.ergora/checks/review-reporting-integration/`。两源历史原件仍由其各自 worktree 下的 `.ergora/checks/review-backend-guidance/` 和 `.ergora/checks/evidence-report-generation/` 保存；原报告中的历史验收不改写为本次运行结果。

## 2. 完整冻结与组合

两源均冻结 13 个候选文件（各 3 tracked、10 untracked，含各自独立审查报告）。`sources/br1/`、`sources/br2/` 保留完整二进制 patch、tracked patch、untracked 清单、文件正文以及字节数／SHA256／执行属性清单；读取前后身份相同。完整 patch SHA256 分别为 `e2a6b21713140d304f0c16db48648d7b84589a419a43420a88e9829486e9d006`、`3b79a5e2090dca52fda0e8b39d8d852210eaac917387d77841f5d60542eb003c`。

两个共享文件按原 `f00bfdfd` 正文三方合并，无冲突。原 32 个 preset 名称全部保留，30 个无关条目不变，两个领域默认根选择 1.0.1，追加 `evidence-report` 后共 33 个；工作流手册同时保留两方说明。其余 22 个导入文件均与源 snapshot 逐字相同。组合没有 Python 产品 owner、既有资源包、权限、limits、图或 CI 修改。

## 3. 新非 editable 安装与原身份

`python -m build --wheel --no-isolation` 构建新 wheel，并在本片全新 venv 安装该 wheel 与 pytest。wheel 原字节 SHA256 为 `bd5352e7edd0e85d8c93fa9d958200757b13f385e355f92a8e4d04abed205276`。实际 `python -I` 从该 venv 的 site-packages 导入；源码／wheel／site 的 **663 个产品文件**集合、全部字节和执行位相同，`reference.verify()` 为 **PASS／283**，`pip check` 为 `No broken requirements found.`。命令、安装日志、完整文件 SHA／执行位清单与结果在 `validation-commands.json`、`package-files.json`、`package-executable-bits.json`、`package-check.json`。

复用 BR1 原 `check-invariants.py`，仅改整合基线／输出目录和允许 BR2 catalog 新条目，保留原脚本来源 SHA 与改动说明。对新安装 owner 的实际检查 **43.564 秒通过**：216 个旧 preset 文件字节／执行位保持；两领域各 24 个原 object 文件及旧 index 全映射保持；两份旧 manifest、八份旧叶输入字节不变，按旧 manifest 再准备的八份输入 digest／字节相同；八个新叶保留原引用／backend／只读权限，并完整继承根 Skill。原两新根及共享 Skill digest 与 BR1 独立审查身份相同。结果见 `invariants-r1/result.json`。

## 4. 安装回归首轮与准确归属

把当前 tests／examples 冻结到私有目录，以新安装 `python -I -m pytest` 运行完整 preset suite 及既有 resource／manifest／export／restore 接缝。r1 为 **49 passed／1 failed／70.84 秒**（外层命令 71.197 秒）。唯一失败在旧 training-v2 测试直接按 `__file__` 查源码 data 时，冻结 fixture 尚未复制 `src/ergora/data/presets`；实际安装、manifest 和此前断言已通过。原 stdout／stderr／JUnit 与首轮输入清单保留，不修改产品或测试迁就失败。接续只补原 preset 数据 fixture，并单独重跑该测试；其余 49 项不重复运行。

r2 加入 228 个原 preset 数据 fixture 后，原失败用例 **1 passed／2.33 秒**（外层命令 2.577 秒），原 49 项仍归 r1。两轮实际覆盖同一产品的 50 个既有用例，其中包括 pretraining／posttraining 新根、报告／flow-map 两个 profile、独立旧审查根、全部既有 preset profile，以及完整祖先／Skill 冲突／manifest 离线恢复／包 export 与 backup restore。没有增加测试文件或 CI。首轮冻结 tests／examples 共 178 文件；r2 输入目录清单另含 228 个 preset 数据和 5 个可辨别的 pytest cache 文件，`final-validation-check.json` 分别记数，不把缓存称为源码输入。

新安装原 inspectors 同时复核 BR2 Agent／Workflow／Skill，digest 分别保持 `f82e5acec681e9f23506fad1289c179bca83d2253450d8ee7de85c92fbc37008`、`67541349b69458a58be8ee9e5fc7fccbe405aba4e0f106bac29342972022c441`、`42968e4a057ce46801f45105b1b122bb3e2640540c846360da915ef3955d292f`。13 个变更源码／测试文件验证前后 SHA 保持；两源各 13 文件在本次结束检查仍与其 snapshot 相同。

## 5. 原 HTML 浏览器首轮

BR2 原 `artifacts.response` 中的 HTML 与保存视图逐字相同：6,181B，SHA256 `fc0d9bd7cf225cfa0969c0035de9fefa56920b8a673c907d6cff2d0b6a557adc`。复制相同字节到 ignored `output/playwright/review-reporting-integration/original/report.html`，没有修改模型输出或调用模型。现有 Playwright CLI 通过 bash 调用已有 wrapper，独立 session 与仅 loopback 的临时 HTTP server 不接触其他会话。

首轮浏览器使用既有完整 Chromium，启动在系统缺少 `libcups.so.2` 时失败，尚未渲染页面；原 stdout／stderr／命令与 server 关闭观察存于 `browser/`，没有安装系统依赖。现有 headless-shell 的动态库检查没有缺失项，下一轮尝试此已有二进制，另存 `browser-r2/`，不覆盖首轮失败。

r2 使用已有 Chromium headless-shell 1247 成功打开原 HTML，实际截图已视觉检查，DOM 观察如下；原内容仍写它当时的 657 文件与未安装事实，没有改写成此次整合结果。

|观察|1280×900 桌面|390×844 窄屏|
|---|---|---|
|文档尺寸|1280×1974，无横向溢出|460×3079，结果表格造成 70px 横向溢出|
|正文与来源|标题、五节、原失败、来源／限制均可读|同一正文与来源保留，表格需横向滚动|
|静态／锚点／显示探针|script 节点 0；内部目标均存在；探针保留原换行及字面 `<script>`|同左|

控制台实际 0 消息／0 error／0 warning；CLI 请求观察显示 1 个被默认过滤的 static request，loopback server 原记录为唯一 `GET /report.html` 200。没有据此声称所有浏览器网络均获隔离。实际命令／DOM／snapshot／请求／console 原件在 `browser-r2/`，截图在 ignored `output/playwright/review-reporting-integration/{desktop,narrow}.png`。原 HTML、派生副本 SHA 相同；本片模型调用 0。独立 session 与两轮临时 server 均已关闭。

窄屏溢出是本次原产物的实际布局限制，未修饰或替换模型输出；本次观察不认证通用报告准确率、sanitizer、打印或可访问性。新增模板的事实核验仍归调用者与原审查／release owner。

## 6. 冻结交接与剩余门禁

完整可审候选共 27 文件：两源合并后 24 文件，另加本片计划／交付及隔离总计划 checkpoint。tracked diff、完整含新增文件的 binary patch、22 项 untracked 清单、逐文件 SHA／字节／mode 与摘要保存到 `review/`；冻结范围不包含 ignored wheel／venv／运行数据。验证原件及截图另列在 `review/artifacts.json`，供独立 reviewer 复核实际身份。

最终静态检查覆盖 21 份变更 Markdown、275 个本地链接目标，缺失目标 0、行尾空白 0，`git diff --check` 通过；没有把路径存在扩大为全部 anchor 或外链联网认证。源码／测试候选与两源 snapshot 的最终 SHA 复核通过，index 保持未暂存；总计划只改本隔离 worktree 的新增 checkpoint。

两源原 approve 仍只归各自范围；新的组合需求／维护性独立审查待主控另配，未由本实现者替代。主控下一步使用冻结基线／完整 scope／原始要求与实际验证交 fresh reviewer，处理实证 finding 后再按原门禁决定自身模板、固定候选、逐片合入与普通发布。当前没有本组合自身模板新模型调用、厂商原生／托管审查、Claude／异后端、系统准确率、训练／GPU／质量／性能或远端 CI 验收；本片不提交／推送，不将这些缺口移标为通过。
