# B2a 精确交付与必要CI终核

2026-11-13。新的独立上下文只核已完成B2a的提交 `c46f3834df08927f7d266757c0f7d3fae8308fb8` 与其自己的 [CI 43226350116](https://github.com/626619403/Ergora/actions/runs/43226350116)。已读AGENTS、[交付记录](2026-11-12-six-stage-budget.md)、[原实现评审](2026-11-12-six-stage-budget-preparation-review.md)及原身份补核；原评审的本地两轴通过与失败史保持。本次未审未提交B2b／c，未安装、运行测试／模型、提交或请求网络；只新增本报告。

## Spec

**此次发布终核通过，开放finding 0。** 官方run原件指向完整c46提交，两个job的七个必要步骤均completed／success；没有借B1或其他候选CI关闭B2a。

私有原件根为 `.ergora/checks/six-stage-budget/b2a-closure/`。以下四对 `page.html`／`receipt.json` 均逐份重新计数和计算SHA256，body与receipt所载值相等；每份receipt的请求URL与final URL均等于下表官方链接，HTTP均为200。

|原件目录／官方URL|page.html：字节；SHA256|receipt.json：字节；SHA256|
|---|---|---|
|`ci-run-html-r1`／[run](https://github.com/626619403/Ergora/actions/runs/43226350116)|150669；`42ca0120e9ee787f3356365f098626f68b0c7d1dd217fb4d7a832cd1e64be51f`|5953；`5bf42fbc56a8195b55fd48f2cf770bb867372d524283aa377bc7b67804b3fe3a`|
|`ci-run-html-r2`／[run](https://github.com/626619403/Ergora/actions/runs/43226350116)|157206；`e6e72dae562d69e0e6d04bd8f58a30b238708ffae9b0ae901f0b5dc08b212f19`|5970；`1f2c0102aad65f97933b7846d8836c8a539f3cc151404cffe385493964d21f38`|
|`ci-job-131210421168-html-r1`／[Windows job](https://github.com/626619403/Ergora/actions/runs/43226350116/job/131210421168)|159844；`3614971f3557a8e55e1d4c4bf7d56c91cc048913628b826bc81c980299c550cf`|5986；`2b83ff58eb3373b27bfb38858fc3892f368c2a3042173cc3b9f42e08c00e0459`|
|`ci-job-131210421450-html-r1`／[Linux job](https://github.com/626619403/Ergora/actions/runs/43226350116/job/131210421450)|161757；`a4c3b7dd1825215d83ff40770961a0638a1f3d76a336c0d12a1d119990e8748d`|5996；`3b86063ddc7faef797974607e5a080dc0d5be55049d8aa68a74b4ea02707e325`|

直接解析原HTML：r1的Status为In progress；r2为Success，唯一完整commit链接是c46，job链接对应Windows／Python3.12的131210421168及Ubuntu／Python3.11的131210421450。提交内 `.github/workflows/portability.yml` 与e37基线逐字相同；原checkout未指定其他ref，必要步骤为构建安装、包身份、原生回归，另有仅Windows安装升级。

下表七个原 `check-step` 均有 `data-job-completed` 属性、`data-conclusion="success"` 及非空开始／完成时间；时间与 `ci-terminal-r3.json` 逐项相等。原 `data-log-url` 逐项等于完整前缀 `/626619403/Ergora/commit/c46f3834df08927f7d266757c0f7d3fae8308fb8/checks/` 加表中后缀。两job的全部非空步骤日志路径也只含该候选，Complete job均success。

|job／步骤|原步骤名|日志路径后缀|完成时间（2026-11-12 UTC）|
|---|---|---|---|
|Linux 4|Build and install wheel|`131210421450/logs/4`|13:20:49Z|
|Linux 5|Packaged reference identity|`131210421450/logs/5`|13:20:50Z|
|Linux 6|Native application regression|`131210421450/logs/6`|13:40:26Z|
|Windows 4|Build and install wheel|`131210421168/logs/4`|13:21:21Z|
|Windows 5|Packaged reference identity|`131210421168/logs/5`|13:21:22Z|
|Windows 6|Native application regression|`131210421168/logs/6`|13:34:19Z|
|Windows 7|Windows PowerShell 5.1 installer and upgrade|`131210421168/logs/7`|13:35:13Z|

三个状态摘要也重新核过字节与SHA256，并与原HTML交叉核对，未以摘要代替原件：

|摘要|字节；SHA256|保留的实际范围|
|---|---|---|
|`ci-terminal-r1.json`|590；`7ab52599ebd508c279a06e861abf996ec743b3045c694775c7b2bd7e04245b43`|In progress，无job，必要步骤尚未确认|
|`ci-terminal-r2.json`|693；`0d21e818b780f44f02abca934d8d6823283f4bf50b50cdb77fc77bebc9b9722b`|run Success，已识别双job，尚未核必要步骤|
|`ci-terminal-r3.json`|3065；`ae4d8ca6f7dfa14d6d8a732a7ee8f6f5143864ac6f4f42c79469ae904203b884`|同一run／候选，双job七必要步骤通过；body／receipt引用相等|

## Standards

**此次发布终核通过，开放finding 0。** 按AGENTS的候选绑定和证据准确性要求，独立核实际Git对象及作者原发布回执，未用后续工作树代替已审对象，也未更改原证据或原评审报告。

c46唯一父为 `e37f617f9aca566d862175de5a1e6b25a08ba2de`。实际changed-path集合正好21文件，与 `ready-r1/manifest.json` 完全相同；清单4272字节、SHA256 `5ce90d1a0fd7fd94bafe64febeb2b1d9ae48e97ea59b63c2dd53b28b702deef4`。逐份重算21份冻结文件的尺寸／SHA256，并核提交blob逐字、mode及Git SHA1对象身份，全部相等；12份源码／测试与已审r3快照逐字相同。提交中原评审报告22020字节、SHA256 `51fb5fa8ff817190607c4f9248a4851a9da6a5facd3ded3574c7171aad409ce2`；`commit-identity.json`与独立结果一致。

另直接读取原 `b2a-delivery-identity-review-r1.md`（2237字节，SHA256 `f5a34595e004e9b80cd503b8fdf9d677085af4413944fa50acf846d1ad85b962`）及commit／push／ref的JSON、stdout、stderr。commit与普通SSH push均exit0，原push无force参数；原SSH ls-remote为完整c46及 `refs/heads/refactor/architecture-foundations`。这是作者当时保存的远端回执，本次未自行查询远端。

匿名REST限流403保留：`ci-api-r1/runs.json` 为280字节、SHA256 `cab107d310af6137d3ca21f7de123c972a91cb1cbd91e2f58f61fe192ba31735`，与错误回执相等。本次是保存的官方HTML终核，不称REST成功、完整日志下载或评审者直接网络成功；原In progress不改写。结论只关闭已审B2a此次精确交付，B2b／c及新预算六阶段全生命周期仍按各自出口验收。
