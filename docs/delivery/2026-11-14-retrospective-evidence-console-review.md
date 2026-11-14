# F10d3a 复盘证据选择页面独立评审

日期：2026-11-14。Reviewer 为本片新建的 fresh-context agent，并按 `code-review` 启动两个 fresh-context 子轴分别审查 Spec 与 Standards；未复用前片结论。已读 `AGENTS.md`、[当前计划](../PLAN.md)、[本片合同](../plans/2026-11-14-retrospective-evidence-console.md)、[交付记录](2026-11-14-retrospective-evidence-console.md)、AIHERO 索引及 codebase-design／maintainable-project-delivery 独立评审 brief。

固定基线与初审 HEAD 均为 `6b7ebcc83f18c9b5d203eb47735bf3867f73b44d`；分支 `refactor/architecture-foundations`。三点 diff／新增 commit 为空，本次实际审查为 `git diff` 此基线的五份产品文件，含未跟踪的新 `retrospectives.js` 完整正文。前片 task-context-console 的报告／发布／CI 记账不属本片产品，也不作为本片运行验收。

## 初审与源码修复

初审确认一项 P1、一项 P2；以下保留原失败，不把修后结果覆盖到旧包。原始五文件和修后五文件分别留存于本片独立原件目录的 `initial-r1`／`source-after-r1-r2`，均有完整 SHA256 与 Git blob 清单。

|问题|位置、可达场景及影响|最小修复与当前状态|
|---|---|---|
|R1／P1|初始 `retrospectives.js:2` 从 `ui.js` 命名导入未导出的 `facts`／`disclosure`。实际 ESM import exit 1，报 `does not provide an export named 'disclosure'`；`app.js:10` 静态导入使整个控制台模块图无法启动，违反合同的既有 view 入口要求。|复用原 `table`；披露正文为本 view 私有格式函数，不扩大共享 UI。修后 ESM import exit 0，两子轴已重读，源码关闭；最终安装／浏览器仍待。|
|R2／P2|初始 `retrospectives.js:27` 展示 `ergora handoff evidence ...`；原 `cli.py:57` 只注册 `verify`／`read`。实际非 editable r1 CLI exit 2／`invalid choice: 'evidence'`，用户无法照页面复用下载选择，违反 CLI 兼容要求。|第 28 行改为 `ergora handoff read ...`。原 CLI `read --help` exit 0，两个子轴均重读正确命令；源码关闭，最终实际下载清单复读待验。|

R1 初始 view SHA256 为 `6e90b55665ea01b2017a2ba942d0f5ad47d62625b3d5b77e9eba6e5c6db3be6a`。R1／R2 修后 view 为 `16d660793f436fba1010697b426ac4a3a77ee1687a4d22bdf5923448192357d8`，Git blob `889c34966a9a147f81d6778c11b21feb7cfef514`。其余四个产品 blob 保持：web `0ee6acc992c7328865bdcff171693a6b3c353f0c`、app `bcffe122740f13fef2999f14aa5dab6660949057`、index `38490e63a0027cd5f9def95196b3571e35e1cd15`、style `8504e1db73083018f54350f84524706f4baa8b82`。

## Spec

修后静态范围 **approve，开放 finding 0**。新路由先核当前项目，直调原 `handoff.evidence`，再拒绝跨项目结果；没有接管原整包、内部引用、32 项／1 MiB、UTF-8／NUL／二进制校验。空选择仅返回完整目录，明确选择读取完整文本；没有写 State／原包、提取 archive、调用模型或生成／采用候选。

页面目录与选择各有代际；输入变化、重读和选项变化分别使旧观察失效，catch／finally 也检查 active 与代际。原输入／失败勾选保留，成功重读清空选择；下载只由明确点击触发并核当前代际，内容为精确数组或完整原 evidence，明确区分 canonical 身份和下载 JSON 字节摘要。原 index／原 evidence 的取消、outcome、成本缺失与 null 没有重写。上述交错／页面切换／控制目录切换仍是静态核，不代称动态验证。

## Standards

修后结构／维护成本范围 **approve，开放 finding 0**。原 `handoff` 仍是资料准入 owner；新 payload／route 是既有 HTTP 框架要求的接口，未增加平行规则或透传库。`app.js` 是新 view 唯一生产 caller，其框架接口和页面私有状态足以支持独立文件；本 view 内的失效、目录读取、选择读取函数将生命周期规则集中，没有为假想调用者增加通用接缝。

新增 guards 分别保护可达的外部项目错绑、请求重入、来源变化、选项变化和已销毁 view；未发现重复原容量／格式 owner 的断言、锁默认配置的检查或低收益新增测试。样式只作用于本页长来源换行与 fieldset 最小宽。

性能静态核：每次明确读取继续由原 owner 核整包，保持原有界读取，没有新增轮询、缓存或重复持久化。页面直接正文与完整结果披露会复制所选文本的展示，但原完整结果仍受 1 MiB 上限约束；当前没有可证的性能 finding，也没有实测大目录延迟／浏览器内存或真实性能成功的结论。

## 已执行检查与待验范围

Reviewer 已读完整五文件／邻接 handoff、CLI、UI、app 生命周期及原 handoff suite；独立执行模块链接失败／修后通过、旧包错误命令拒绝／原 `read --help` 通过。原件在本片 `independent/` 的 `module-import-r2.json`、`module-import-r3.json`、`displayed-cli-r2.json`、`displayed-cli-r3.json`，Spec 子轴另留修后链接记录。两个 r1 探针分别因不支持的 Node flag 与误解引用 venv 解释器失败，仅属 reviewer 调用器记录，不算产品失败。

本节仅给修后静态双轴结论，**不预批本片完成或发布**。最终非 editable 包／两 RECORD／283 reference、原 suite、同包 CLI／HTTP／真实页面、错 SHA／跨项目／二进制／NUL／容量反例、完整下载与代际交错、三宽／键盘、自身原模板、全部引用及服务收尾尚待同片终核；普通发布／完整 Ref／本片自己的 CI 另核。后续三类候选 prepare／check／export、原单叶调用与原评价／明确采用／回退、F9d／G1 和真实 GPU／业务验收继续开放。

## 最终 r3 包身份补核

同一 reviewer 已独立只读逐份核最终 r3：**603 产品文件的当前源码＝source snapshot＝wheel＝installed**；wheel 无重复成员。wheel SHA256 为 `fdb886245ce886464b42cf722fb6834cc545e218814b5fb1163ce0d942fbb95f`。wheel／安装 RECORD 的 **611／616 行**逐行核大小与 SHA256，包含安装生成文件；不是只读取作者 package-identity 摘要。

从固定基线 `git ls-tree` 取得 **283 个 reference 原 Git blob**，逐份重算上述四处 bytes 的 Git blob，并核四处执行位，全部相同。原件为本片 `independent/final-package-audit-r1.json` 与对应脚本。此补核关闭最终包身份待项，不代替安装 suite、实际页面、模板或收尾；本地终核与发布仍待。

## 最终本地终核

同一 reviewer 在本片继续核最终原件；HEAD 仍为固定基线，产品仍是上述五个精确 blob，没有把前片发布／CI 记账算作本片产品。**需求／行为轴 approve；结构／维护成本轴 approve；R1、R2 在最终 r3 页面及真实 CLI 中闭合，开放 finding 0／0。** 本结论为本地终核，普通发布、完整远端 Ref、本片自己的必要 CI 与相应补核仍待；不以此前或前片 CI 预批。

直接读最终 r3 suite 的命令／原 stdout／stderr：非 editable 安装解释器 `-I -m pytest` 运行原 `test_web.py`，**9 passed／13.00 秒**，monitor 14.875857 秒，exit 0。原 r1 两 suite **65 passed／14.25 秒**继续保持旧包身份；没有把其后端测试说成旧页面可启动。产品、原 handoff 与测试 owner 未因 R1／R2 修正发生旁改。

真实浏览器主旅程 **39 项**、生命周期 **31 项**原脚本与结果已逐项读取；原服务确实运行最终 r3 安装件。Reviewer 另独立核 **31 个 HTTP** 原请求／响应的大小与摘要，其中 **25 个 evidence 响应**，并将全部 **21 个浏览器 sample**逐个匹配原 HTTP；两次夹具 503 明确区分原应用 200 与实际交付 503。全部成功结果的 canonical／index SHA、原 manifest、job／receipt、artifact metadata 和 UTF-8 正文均交叉核同一原包；两份别名各 **6,432B** 完整原文保持。错误整包 SHA、跨项目、非 UTF-8、NUL、完整超容量与目录后明确变包均拒绝，没有部分下载。

四个真实延后响应覆盖旧目录后改 SHA、旧正文后换选择、正文跨 view 与跨 project；全部释放，旧回复与 finally 没有恢复材料或覆盖新结果。重读清空、原目录／正文失败后的禁旧观察／保留选项、明确重读及零自动下载／零 pageerror 均有实际检查。1440／960／390 三张截图已由 reviewer 逐张查看，表单／来源／正文与按钮布局可用，没有横向溢出；键盘实际覆盖路径→SHA→目录按钮两次 Tab。

浏览器真实下载的 **115B** 精确选择数组与原请求相同；**21,018B** 完整 evidence JSON 与原响应相同。原最终安装 CLI `handoff read` 使用这份实际下载数组、同包和明确整包 SHA，**exit 0／0.364254 秒**；reviewer 直接读取其 stdout，逐对象核与下载相同，stderr 空。选择 canonical 身份 `bee43337cc8560e31fdf069b4ee1d33f852f265143bdb75aee4cc71e88a872d9` 与下载字节 SHA `0f6ea06a2b8f82f24cf397b9eb6116e05e9e688d4c155a672ba3d9ff42ab34f2` 分别重算，没有混称。

自身原结构模板的 run `44959477dc0f4a79b512c6ff18bfc694` 为 **succeeded／exit 0／approve，58.062485 秒**。实际是授权 Codex 回退，原 requested Claude 与理由保留。Reviewer 逐块核九份完整文件 **114,399B** 的原字节／SHA；它们与三份完整继承资源全部进入 **118,864B** prompt，prompt＝实际 stdin，原 result SHA 与保存原回复逐字相同。grant→root→leaf 的 read／write／shell／network 权限没有扩大。这是自身模板检查，不替代本次独立评审或任何产品效果评价。

收尾已由 reviewer 实地复核：r2／r3 原 PID 消失、两个端口关闭，原独享浏览器 close exit 0 且 daemon 不在。两组 demo／other 原包的实际 bytes／mode＝before＝cleanup，fixture Git 均干净；mutable 只在 r3 增加夹具明确写入的 30B。另以 SQLite `mode=ro` 直接重算两组实际数据库逻辑摘要，均与 before／cleanup 相同；没有仅相信清理摘要。相关独立原件为 `browser-evidence-audit-r1.json`、`self-template-audit-r1.json`、`cleanup-audit-r1.json`、`database-readonly-audit-r1.json`。

[公开证据清单](evidence/2026-11-14-retrospective-evidence-console.json)的 **266 个原引用／20,095,366B**已全部直接读取：路径唯一，每项实际大小与 SHA256 相同，无缺失或差异；五份最终产品的清单身份亦与当前 bytes 相同。已重读最终 PLAN／具体合同／交付、USAGE 与当前架构新增说明：历史 r1／r2／r3、实际检查与未验范围分开，后续三类候选与原调用／评价／明确采用／回退范围没有关闭。跟踪 diff 的 `git diff --check` exit 0；最终暂存／发布检查由发布步骤继续完成。

本地结论仍不覆盖控制目录 Home 切换、全部键盘／生命周期／平台矩阵、大目录浏览器内存或性能基准；取消／其他 outcome 的逐字展示也未另做浏览器全矩阵，沿原 owner／完整 JSON 静态核。没有执行实际业务候选生成／评价／采用、真实 GPU 或质量／性能验收。F10d3b、原单叶调用与完整评价采用回退、F9d、G1、完整 Forge C2 继续开放。
