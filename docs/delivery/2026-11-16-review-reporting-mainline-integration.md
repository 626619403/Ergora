# BR 主线联合整合交付

日期：2026-11-16。固定基线 `d5b58912e4f20c96a52f7c0138b8c7c3d1a97b50`，当前分支 `refactor/architecture-foundations`。范围／验收见[计划](../plans/2026-11-16-review-reporting-mainline-integration.md)。实施及验证进行中，自身模板和 fresh 联合独立审查由主控安排，本记录不替代其门禁。

## 导入范围与原身份

从隔离 review-reporting-integration 工作树导入 28 个精确文件：原 27 项排除隔离总计划，再加入 README 与原组合独立审查。所有导入文件与该树逐字／执行属性相同，原审查报告不改写。catalog 共 33 项，两个新领域根 1.0.1、独立 evidence-report 1.0.0；保留发布旧资源。未复制旧 training.py／worker 或其他未变源码，未改主线 docs/PLAN.md、c1 文档、训练测试／fixture 或 CI。主控另行导入的 CI fixture 修正单独记账。

新 ignored 验证根为 `.ergora/checks/review-reporting-mainline/`。`imported-files.json`／`imported-files/` 保存 28 文件字节、SHA、mode 和正文；`imported-complete.patch` 为相对 d5b 的完整含新增文件 binary patch，SHA256 `cd81df3d5003a77e38af8b6b3cff0f28b959f471ff0da516e208056dca34d0fb`。使用独立临时 index 冻结，没有暂存主线改动。原历史材料仍在隔离树 ignored `.ergora/checks/review-reporting-integration/`，本次不复制大缓存或重做 1,024 原件全面审计。

## 联合安装与不变式

新 wheel SHA256 `4c938c8fbddfa9f2e7c27a25b4b811e435807d24d128dd90d05717ebe507f079`。新建 core 与 SDK 两个 venv，非 editable 安装同一 wheel，实际隔离导入 site-packages。两方均核 **663 产品文件** source／wheel／site 集合、全部字节及执行位相同，283 reference PASS，依赖 check 通过；core 无 temporalio，SDK 使用原 temporal extra。相对 d5b 产品仅 11 新资源及 catalog 修改，主线五个 c1b1 产品完全保留。构建／安装原命令、日志、逐产品 hash 与执行位在 `build-install-r1.py`、`build-install-r1.json`、`package-r1-{core,sdk}.json`、`package-executable-{core,sdk}.json` 和 `reference-r1-{core,sdk}.json`。

复用隔离原不变式脚本，仅换固定基线与输出位置，不硬锁旧产品摘要。安装 owner 检查 **41.500 秒通过**：216 个旧 preset 文件逐字／执行位不变，30 个无关 catalog 条目不变；每领域旧 24 object 文件及旧 index 映射保持，旧 manifest／八份旧输入保持，按原 manifest 再准备 digest／字节相同；八个新只读叶保留引用、backend、权限并继承根 Skill。原件见 `check-invariants.py`、`invariants-r1.json` 及 `invariants-r1/result.json`。

## 回归与剩余门禁

主控确认 CI fixture 落定后冻结 178 tests／examples，包含其新 fixture SHA256 `80aa81202217ac3d6c9ab43c75a4d6641132d20482cb39582d897d45e2ef1311`。事先附带 228 个原 preset data fixture，避免隔离 r1 已知缺数据问题；两份输入清单分别为 `test-inputs-inputs.json`、`test-preset-data-inputs.json`。原 BR 同一 50 项适用测试以新 SDK 安装一次运行 **50 passed／208.52 秒**（外层 209.734 秒），完整命令、stdout／stderr／JUnit 为 `installed-regression-r1.{json,stdout,stderr,xml}`，入口为 `run-validation.py`。不沿用隔离树的 49＋1 结果；本次预先带齐 fixture，没有该缺数据失败。

新安装实际 CLI 导入 evidence-report／pretraining-review／posttraining-review 以及 report show 全部通过，原命令／日志见 `validation.json` 与 `cli-*`。另以安装 owner 准备完整报告 manifest／input，Agent／Workflow digest 保持 `f82e5acec681e9f23506fad1289c179bca83d2253450d8ee7de85c92fbc37008`／`67541349b69458a58be8ee9e5fc7fccbe405aba4e0f106bac29342972022c441`，9,279B prompt 及 CLI verify-input 通过，无模型调用；见 `check-report-resource.py`、`report-resource-result.json` 和 `cli-verify-report-input.stdout`。

导入 28 文件及 178 tests／examples 在验证结束 SHA 未变；源／wheel／site 同一另独立核字节／执行位。导入 Markdown 的 208 个本地链接目标存在，最终另核本片两文档的本地目标及 `git diff --check`。最终 30 文件（28 导入＋本片计划／交付）完整 patch、正文／SHA／mode 清单位于 `final-review/`；排除主控 docs/PLAN.md、c1 文档及 fixture。自身模板与 fresh 联合审查仍待主控记录，不能把隔离两轴结果移作本片通过。

本片不重跑 c1b1 76 suite、模型、浏览器或训练。原报告 390px 宽下 70px 溢出继续保留，未修 HTML／替换模型输出。未验原生／托管／异后端审查、通用准确率／sanitizer、训练质量、远端 CI 或发布；未提交／推送／安装系统包／发外部消息。

## 主控联合接缝与自身模板

上述30文件为实施子任务原冻结范围；主控另将已独立通过的`7025e15`测试竞态修正适配到本线fixture。c1b1已把marker改为原子发布，直接旧patch的`--check`因上下文不同失败且未修改文件；仅调整原mark以支持完整payload／各PID pending，并在beta真实通知前沿原operation clock等writer与alpha实际阻塞marker，保留所有新candidate fault。产品／原reaper／测试正文和CI未变。完整差异及来源见`ci-fixture/import.json`／`mainline.patch`。

同一663包及178冻结输入下，主控精准运行原CI失败、相邻取消／冷观察／错identity／预算尽和并发Candidate正向：实际**8 passed／106.07秒**，外层107.303秒、exit0、stderr空。此前预计7，原operation取消实际展开spawn／helper／loop三个case，按原JUnit记8；与上文BR50项分开，原件`ci-fixture/installed.{json,xml,stdout,stderr}`，不重跑c1b1的76总suite。

原`ergora-structure-review@1.0.0`经新联合安装真实Codex fallback **29.200秒、approve**。37份完整文件653,196B及三份祖先资源进入809,109B真实stdin，SHA256 `30293705f7de5785fbe8396a82535435cea6f46cb98f74f72c0deb9ed48d84e4`；结果SHA256 `5031b93a28c27a15a4e0b756d099b34934a3f0e7fea6599b8de0c555b5eb7f26`，见`self-review-r1.json`／`self-review-r1-codex/`。该次完整供稿仍写回归在途，未把后来终态倒归给模型；模型只审供稿，私有原件／运行／远端CI仍另验，也无异后端成功声明。

新联合候选即将冻结完整scope并交fresh-context reviewer，两轴门禁仍待；与已批准的后继服务设计和隔离实施分别记账。

收尾观察`cleanup-r2.json`读取本轮cycle接缝与自身模板目录的418份JSON（含无扩展名marker），15个不同完整进程身份当前活匹配0、unknown0、无超限跳读；不是全OS spawn清单，也不把非父身份观察说成wait。原`cleanup-r1.json`只扫描.json后缀，5项身份的较窄范围原样保留。

## 联合独立门禁闭合

新的fresh-context reviewer已对准确33文件scope／168,673B完整patch、663双安装、原216资源／旧图和输入、178＋228输入、50及8两轮终态、自身完整stdin与结果完成核查，需求／可维护性均approve，开放0／0。[原审查报告](2026-11-16-review-reporting-mainline-integration-review.md)9,773B，SHA256 `46911b17f6696e0b9bc8da3e4f5223da49f1199a6b7cd669db180e483c0e5712`。未重跑原suite／模型／浏览器，历史限制保持。本地联合片闭合，进入固定提交；普通推送用于取得该候选自身CI，不自动合main，也不改写前片失败。
