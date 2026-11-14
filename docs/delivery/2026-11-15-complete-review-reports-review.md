# Q2.3b2／b3 完整来源与多分支报告独立评审

日期：2026-11-15。Reviewer：`/root/complete_review_reports_audit`，独立新上下文；仅收到原始要求、固定范围和实际证据，没有继承实现会话。按项目三份AGENTS、组件变更协议，以及`maintainable-project-delivery`独立brief和`ergora-codebase-quality`的维护性／模块／测试接缝参考完成两轴评审。授权写入仅本报告。

**r1需求正确性：request-changes；结构与维护：approve。开放需求finding 2，结构finding 0。** 两项均在Markdown字面渲染边界；以下结论只覆盖冻结r1，不提前关闭尚未复核的修正。

## 精确范围

项目及docs归属Ergora。基线`96b4bb5454714a73e1d5f60b880a479c195e5269`，未提交候选由私有`.ergora/checks/complete-review-reports/review-scope-r1/scope.json`及`files/`固定。已逐份读取／核同14个文件的字节数和SHA256；`author-diff.patch` SHA256为`1bebde8c1368d3a3ffb44d696b4398bbcd73915d93b3068024bd51d11a329047`，实算一致。新增plan／delivery的完整内容在该快照内，未遗漏untracked文件。

14路径为：

- `src/ergora/review_requests.py`、`src/ergora/cli.py`。
- `tests/test_review_packets.py`、`tests/test_review_associations.py`。
- `docs/LOCAL_REVIEW.md`、`docs/TRAINING_REVIEW.md`、`docs/PLAN.md`。
- `docs/plans/2026-11-15-complete-review-reports.md`、`docs/plans/2026-11-15-source-bound-review-inputs.md`。
- `docs/delivery/2026-11-15-complete-review-reports.md`、`docs/delivery/2026-11-15-composition-run-inspection.md`、`docs/delivery/2026-11-15-composition-run-inspection-review.md`、`docs/delivery/2026-11-15-source-bound-review-inputs.md`、`docs/delivery/2026-11-15-source-bound-review-inputs-review.md`。

另沿实际消费者读取原`agent_runs.inspect_run`／run-input、`agents.result_schema`／validate_result、完整manifest／input编译与检查、`require_root_task`、来源reader、严格JSON reader、State及相关既有fixture。后继工作树不在r1认证内。

## 发现

### R1／P2：合法Unicode分隔符使Markdown随附完整JSON失真

位置：冻结r1 [review_requests.py](../../src/ergora/review_requests.py:173)，以及171行的人读回复。

`json.dumps(..., ensure_ascii=False)`会原样保留合法字符串内的U+0085／U+2028／U+2029；`full.splitlines()`却将它们解释为行边界，删除原字符并插入真实LF。完整JSON字符串由此含未转义控制字符，无法反解，Markdown不再携带同一观察。人读回复使用相同分行方式，也会丢失这些字符和原CRLF信息。合法来源正文或模型回复都可触发，不要求损坏原件。

独立复现使用r1非editable安装：在原完整报告的内存副本中把一份合法response设为`"First\u0085Second\u2028Third\u2029Fourth\r\n"`，已有可信`agents.result_schema(["response"], review=True)`接受该结果；渲染后提取末尾缩进JSON并去掉每行四空格，`json.loads`报`JSONDecodeError: Invalid control character at`。原件未改。另一个最小观察中，渲染后上述三Unicode字符及CR的计数均为0。

最小修正：完整JSON只按JSON自身的LF结构分行后缩进，保留字符串内字符；人读代码块可规范CR／LF显示，但完整JSON必须可还原原字符串。扩展原完整报告测试，反解Markdown随附JSON并与同一观察作完整比较，包含Unicode分隔符、CRLF及末尾换行。原测试用`response.splitlines()`推导期望，与实现共享了同一信息丢失，因此现有通过未覆盖这个风险。

### R2／P2：逐叶拒绝后的原run选择仍可注入Markdown结构

位置：冻结r1 [review_requests.py](../../src/ergora/review_requests.py:164)。

`report`允许非空run-ID字符串进入逐叶检查；`inspect_run`会拒绝含换行／HTML的非法ID，报告正确保留该原字符串与错误。但`markdown`将`"Run: " + branch["run_id"]`直接拼入正文，未把该输入作为字面材料渲染。

独立复现沿r1实际四run报告、只读SQLite连接：将结构叶的选择替换为`"unknown-run\n\n## Forged approval\n\n<div>untrusted</div>"`。该叶为`verified=false`，总体`incomplete`，其余三条已核反对均保留；Markdown却出现列0的`## Forged approval`与`<div>untrusted</div>`。因此缺失／错误分支仍能伪造人读结构；JSON本身没有该问题。自身原模板也报告了此项，本结论来自独立可达复现。

最小修正：将完整run选择逐行作为缩进代码输出，并在同一renderer内一致处理人读不可信字符串。显示分行须考虑Markdown认可的CR／LF，避免仅改为LF分割后让bare-CR逃出代码块；末尾完整JSON继续保留原字符串。保留当前逐叶错误语义，不需要收紧映射后把整份报告提前拒绝。用已有错误选择接缝覆盖多行HTML及bare-CR即可。

## 所有权、guard和测试价值

`review_requests.report`的生产消费者是薄CLI；它负责已有来源绑定用例的覆盖／意见语义，作为公开应用入口留在原owner合理。`markdown`仅由同一CLI消费，与报告同模块即可，没有需要抽成新框架的复用证据。新增代码没有复制SQL、猜run文件路径、按具体后端分派，或建立第二调度／账本／批准；Kernel／v3及原执行owner不变。

来源／manifest显式身份、未知实例、重复run与只读reviewer／直接根task／读取上限由该边界拒绝；逐叶原input实例、完整composition、来源task、三项原件与可信结果schema则在原观察取得后核验。Agent定义摘要的再次比较保护检查manifest后读取展示定义的漂移。异常隔离限定在原件读取和验证错误，未吞掉普通编程错误。`completed`只能在证据核验后且原status为succeeded时成立；failed／running／preparing／unknown不会被合法意见变成完成，已核反对也不会被多数或不完整覆盖抹去。

现有新增接缝保护了真实静默风险：两域定义／三通用叶、少数反对与全赞同、漏叶／未知run／错实例、有效异源和有效异manifest、缺input、可信schema与保存远端schema的区别、结果容量、只读重读。原invocation接缝已有prompt／result漂移、递归与缺件及历史迁移覆盖。四状态在同一原run循环、先验错误不重建四run，以及复用原外部平台fixture，都有具体成本理由。R1／R2应在这些现有接缝补充，不需要新测试框架／CI job。

## 直接核验的证据与限制

- **包原件**：从固定Git基线读取其余产品、以冻结两产品文件覆盖，逐项与r1wheel和真实`site-packages`比较643文件的完整字节／SHA；无缺件或额外件。283参考包含于同一核验，保持基线。wheel实算SHA256为`b9ac2c8877ae9ad0b921be94106a2ecbaa38e447a05ef24134be8785ea62e8d5`。不是只采信`package-r1.json`布尔。
- **原测试记录**：直接解析XML，源码首轮46通过／66.761秒，追加有效异源2通过／7.422秒、fixture相关5通过／6.820秒；原外部两项均因Git不在PATH失败。安装原三suite为143项：45 packet／64 association／34 invocation，141通过、同两fixture失败／119.045秒。修后外部源码2通过／3.410秒、安装2通过／4.706秒。原三测试快照及SHA已核；packet与冻结r1相同，association的前移项目登记修正已对照。没有将原失败改记为全绿，也未重跑未变141项。
- **15实际CLI**：逐项读`commands.json`与15份stdout／stderr，全部SHA及exit0核同；显式模型调用仅第5／8／11条三通用叶，报告为独立调用观察。用r1安装和只读SQLite连接重新生成第12条报告，完整对象与保存stdout相同，第14条重复对象也相同；没有重新调用模型。
- **四原run**：`efd0fc2581d24d45a42e20d34b475c97`、`66c8bc21bf6f42288f93d0f200363c63`、`4ca178ad5fbe4975b63e40f995a54b3e`、`2be4fce425724e70a0516bc28487a948`的完整input均重新编译核同；result原字节／SHA／JSON与报告逐字匹配，input prompt／protocol prompt／实际stdin相同，原status均succeeded、四条request-changes全文保留。仅原领域叶时为1／4且incomplete，完整时为4／4且request-changes；容量1时四结果均显式不可核。保存的本例Markdown完整JSON可反解；本例未含R1分隔符，不能据此推广。
- **原件保持**：直接重算前片source／manifest／runs全部文件清单，并用只读SQL比较原DB行，与`original-inventories.json`原记录相同；本片copy恰四行，原领域行逐字保留。
- **自身原结构模板**：直接核run `469b5582c6344fd2a7a43ef787875207`、23份完整材料401,815B／3资源、全部文件摘要及其在实际task／prompt中的完整内容；与冻结r1或原基线一致。input digest为`dd009e30fe6160e4b52a8eeb499ac2a6f5a6dd9bac953b0351831aaa7be027ce`，prompt／protocol／stdin相同，原result及保存副本SHA为`6c95edfa19eac8159fa737e9faef51602a258ee2568f45397019ecbee99ac05d`，decision为request-changes。其76.293秒意见仅是supplied-text模型审查，不能认证私有原件或代替本评审。

本评审只写本报告，未安装、执行模型／训练、重复全量测试、commit／push或写平台；独立复现仅使用已安装r1、内存文档副本及原状态的只读连接。未做浏览器渲染、Windows实际运行、异后端、正式串行图／all-join、训练／GPU／质量／性能验收。前两片CI记账只按原记录及边界审阅，未独立认证前片CI；本片自己的发布／CI／终核仍另验。R1／R2修正及受影响验证须取得新精确范围后复核，r1结论不能提前转授后继。

## r3同片复核：R1／R2关闭，新增R3待修

仍为同一独立reviewer。r1原报告9,737B前缀完整保留，SHA256仍为`af92b62f64f6a7cf5945a47d76f778476cc3a81e222ded71a04f76b258ed27f9`。本次核验新冻结`review-scope-r3`的16路径、完整字节／摘要和diff，实算diff SHA256为`dd93946e4b4934d365d62a61093f2a5ea17f73d39d16a221e5e6813087e7e9a1`。在原14路径基础上新增本报告r1原文及`docs/plans/2026-11-15-source-review-reports.md`进度同步；相对r1，产品仅改变`markdown`及其局部显示算法，测试只在原fixture补充，其他变化为本片状态记录。

R1已独立关闭：完整JSON改为仅按LF分行；原合法Unicode分隔符／CRLF复现现在可反解成与原内存观察完全相同的对象，原response字符串逐字符保持。R2已独立关闭：run选择、错误和回复统一经局部`_literal_lines`按CommonMark的CR／LF显示行缩进，原非法选择的伪标题／HTML和bare-CR均没有逃出代码块。helper的实际调用仅在同一renderer内三个显示点；它隐藏了真实重复的字面显示义务，无须增加模块或框架。报告核验／覆盖／调用路径、CLI、其他产品保持r1字节与语义。

实际证据已直接核对：

- 两原红测试分别在JSON反解处真实失败（stdout记1失败／4.75秒），以及原非法run-ID字面缩进处真实失败（1失败／3.52秒）；修后源码四相关用例4通过／15.90秒，r3安装同四用例4通过／19.54秒。XML／原stdout均已读取，不重跑未变的原141项。
- r3固定源码／wheel／真实非editable安装643份完整字节和SHA全部相同，无额外或缺失文件；283参考仍与原基线一致。wheel实算SHA为`b27ae2364fac8c88ee0401260708c1cb55a02205fe44be3959d3b0aeb46d79e9`。中间r2的643份wheel／安装亦与其原清单相同，wheel SHA为`d1e2b8bbd7c42fabbff72b60c38792a621911722563a4bd9539644f166ca0fdc`，未把中间包当最终验收。
- 四新只读CLI的argv、exit0及stdout／stderr SHA全部核同，均使用r3安装；完整JSON与r1原四run观察相同，两份Markdown的末尾JSON分别还原完整／非法选择观察，后一报告保留其余三份原反对。按CR／LF逻辑行另核伪标题及HTML均缩进；显示中没有剩余裸CR，完整JSON仍保留原run选择。用只读连接重新生成完整报告也相同。原152文件及四DB行与新CLI前清单／原行逐字相同；这四CLI没有模型调用。
- r3自身原模板run `cfc8d9d67d84413585c8e71c3b1ac4b8`：23完整文件405,348B及3资源与冻结r3／原基线相同，全部完整进入task和实际prompt；input digest `80a9c43254dd4158d911f3db6e76ed432326e6cd5f70c29dd9e7c75936684de4`，prompt／protocol／stdin相同，原result与保存副本SHA为`f14f85fded29046825b8fcf163a237b08820b77d08d2b6a4b64873803b67c111`，82.355秒、request-changes。原driver因配置源路径不存在而停止的stderr已读，停止位置在admission和模型调用之前；resume沿同一已冻结input只修配置源，状态中只有一条实际run，没有重建资料或模型重发。该模型提出下面的新问题；结论另由独立复现确认。

### R3／P2：非有限结果值使坏叶越过读取边界并阻断整份报告

位置：r3 [review_requests.py](../../src/ergora/review_requests.py:177)，上游原[结果读取](../../src/ergora/agent_runs.py:430)及[JSON parser](../../src/ergora/definition_bundles.py:39)。

原`parse_json`使用Python默认`json.loads`，允许NaN／Infinity／-Infinity，且`1e9999`／`-1e9999`等数字会溢出为非有限float。匹配原SHA的这种结果被`inspect_run`标为available。`report`虽按可信reviewer schema正确拒绝该叶，却保留了含非有限对象的原观察：Markdown的`allow_nan=False`随后抛错并丢掉整份输出；JSON CLI默认序列化则成功输出不属于标准JSON的NaN／Infinity。

独立复现只在自动清理的小隔离副本修改原结构叶result及其原记录SHA，保留另三份完整input／result。使用`{"summary":"Saved custom result","artifacts":{"response":"Original invalid result"},"decision":"approve","extra":NaN}`：reader返回result.available=true，此叶verified=false、总体incomplete，另三反对仍在内存观察中；`markdown`抛`ValueError: Out of range float values are not JSON compliant: nan`。实际JSON CLI exit0且正文含`: NaN`；Markdown CLI exit2、stdout为0B。原控制目录未改。另直接确认三常量及正负溢出指数均产生相同非有限值和序列化失败。

这也有实际producer路径：`run_input`可显式传入宽松自定义结果schema，`agents.invoke`先按该schema验证，再用默认`json.dumps`保存并记录SHA。报告要求使用自身可信schema，不能因原自定义结果宽松就让错误污染其他叶。

最小修正：在原run记录／结果读取边界显式要求可用于标准JSON观察的有限数值，错误继续沿已有逐叶不可核路径报告，不修改原件或把整份报告改成失败。若复用共享parser，限定新读取消费者的opt-in合同，保留其他旧JSON消费者的默认语义；处理命名常量也要处理`parse_float`溢出，避免只拒绝NaN字面量。原report／reader fixture补同一错误叶仍能输出完整JSON／Markdown、保留其余原意见的回归；无需重发模型或新增调度／账本。

**r3需求正确性仍为request-changes；结构与维护approve。R1／R2关闭，新增R3开放，需求开放1／结构开放0。** r3包与显示修正的验收不认证后续尚未冻结的数值读取修正；前片CI终核、本片发布和自己的CI仍由各原记录分别负责。

## r4同片复核：R3关闭，新增结构容量R4待修

已核`review-scope-r4`全部19路径及9份证据的完整字节／SHA，diff实算SHA256为`12a054cf3ace9ec851d3314571087be2677b9289815017bbea40c2a659908680`。新增产品范围为原`agent_runs`和`definition_bundles`，新增测试范围为原`test_composition_invocations.py`；其他新增内容是本片／前片结果记账。共享`parse_json`的`finite`选项默认关闭，仅原run记录／结果读取采用；其他消费者默认行为保持，没有重写结果协议或改变writer。

R3已独立关闭：NaN、正负Infinity、`1e309`及`-1e9999`在原观察读取处明确拒绝。隔离副本沿实际报告验证，坏result仅该项unavailable，坏record仅该叶显式错误；另三份原反对与Markdown完整JSON反解保持。有限`1e308`的原结果仍available，有限大数、subnormal、负零与整数保持原parser语义；默认调用仍保留原行为。重复key仍由原reader拒绝，没有因数值修正放宽结构校验。

已直接核r4源码／wheel／独立安装643文件逐字相同、283参考保持，实算wheel SHA为`408ec00029d63aad172a53e39ca0377edbec33fbd06edf6b5e5da1c808f162d1`。原数值红XML为3失败、修后3通过，原record故障在旧r3安装实红1项；r4四suite安装XML为183通过、0失败／0跳过，stdout154.01秒，覆盖报告／外部来源／原invocation及DeepSeek归档续接的实际消费者。四份只读CLI流摘要／argv／exit0核同，原JSON与r1相同、两种Markdown可还原相同完整观察，非法标题／HTML按CR／LF行核为字面代码；原152文件及四DB行保持。

r4自身原模板`facb6a826a6c4f37a1a3efb2776daa25`的24文件429,227B／3资源、完整task／prompt／protocol／stdin和原result已直接核同。input digest为`e59f51735d596e2549b09b1b71e949600ecec9fa20ba276fed0e0dd956965ef9`，result SHA为`ec183326a8675161323ce3bd1f6e2fddf14a47177ea56b7046eda159f74b3618`，64.635秒、approve。产品／测试与冻结r4一致；三份plan／delivery／PLAN在模型启动后只补已验183项／四CLI／自身结果的状态，该差异已另读。模型approve不能替代下面的独立反例。

### R4／P2：原writer可保存的深嵌套坏结果阻断两种完整导出

位置：r4 [结果读取](../../src/ergora/agent_runs.py:430)、[JSON parser](../../src/ergora/definition_bundles.py:29)与[完整报告序列化](../../src/ergora/review_requests.py:177)。

有限数值检查未限制可解析JSON的结构容量。约990层的深嵌套结果可以由原writer成功保存，也能由reader解析；report按可信schema正确拒绝该叶，保留的深嵌套观察却使最终缩进JSON编码触发递归错误。JSON CLI同样使用`indent=2`，因此JSON和Markdown均不返回其他已核意见。

独立实证使用自动清理的隔离控制目录，调用原`agent_runs.run_input`、原输入与显式宽松schema `{"type":"object"}`；唯一替身是`processes.run`写入原native结果槽位，实际模型调用0。结果在正常summary／response／decision外加990层数组的`extra`字段。原run状态succeeded且记录SHA，reader result.available=true，报告将此叶verified=false／总体incomplete且内存中保留另三反对；冻结r4实际`cli.main`的JSON和Markdown均exit2、stdout0B，stderr为`ERROR: maximum recursion depth exceeded`。此前985／988层同一路径可导出，990／992层原writer都能保存而导出失败，证明存在真实producer与consumer容量差，并非只手改原件或把模型失败当原成功。

最小修正可复用同一`definition_bundles`内已有结构容量算法：`convert_document`已迭代检查64层／100000值。把该算法留在原owner供原convert和run观察的显式opt-in读取共同使用，保持既有convert计数／错误及其他JSON消费者默认行为；原run记录／结果超限按既有不可核路径隔离，其余叶完整导出，原件不截断。公开说明该观察容量，勿在report重复编码整份观察或另建JSON词法parser。回归须覆盖“可解析且原writer成功保存、但可信reviewer schema不接受”的深层结果，不能只用远超Python解析极限的旧递归故障替代此风险。

另检查未配对Unicode surrogate只在手工构造的匹配SHA材料中触发输出问题；原writer的UTF-8编码会先拒绝，当前没有实证支持的正常producer路径，因此不将它列为新增blocking，也不要求泛化guard。

**r4需求正确性request-changes，结构与维护approve；R1–R3已关闭，新增R4开放，需求开放1／结构开放0。** 结构容量的后继修正须由新的精确范围及相关证据复核。本评审没有重跑上述183项或任何模型；新的producer复现全部在临时副本使用原协议替身，未更动原run或平台。

## r5最终本地复核：R1–R4关闭，两轴approve

**冻结r5需求正确性approve；结构与维护approve。需求开放0／结构开放0。** 本次仅认证下面的本地精确候选及直接核验的原证据；不将该结论转授后继提交、发布、CI或完整B3／Forge验收。

原报告20,275B前缀完整保留，SHA256仍为`b1fff11589e3ba1fed26c80ac1ef9b9e5b4b097b2854046308338d1a672b7e21`；r1的9,737B、r3的15,427B前缀摘要也分别保持原值。已逐份核`review-scope-r5/scope.json`、`files/`的19路径完整字节／SHA及11份证据身份，基线仍为`96b4bb5454714a73e1d5f60b880a479c195e5269`；`author-diff.patch`实算SHA256为`a3b4573187510015c33986a50879e40d0680ffc72955eb25360ccbbf37e62049`。19路径是原r1的14路径，加本报告、`docs/plans/2026-11-15-source-review-reports.md`、`src/ergora/agent_runs.py`、`src/ergora/definition_bundles.py`和`tests/test_composition_invocations.py`；本报告在快照中为追加本段之前的20,275B版本。相对固定基线，产品改变仅原四模块cli／review_requests／agent_runs／definition_bundles。等待期间另建的Q4.2计划／交付两文件不属于这19路径，也未纳入本结论。

### R4关闭及默认兼容性

原`convert_document`已有的迭代树检查提为同owner私有`_check_document_tree`，64层／100000值的遍历、dict键值计数、错误文本和顺序保持；原转换和`parse_json(..., bounded=True)`共享实际算法。原run记录／结果观察同时显式启用`finite=True, bounded=True`，两个选项默认均关闭，其他JSON消费者没有全局收紧。没有新增词法parser、报告整包试编码、第二观察协议或容量框架；两个真实消费者由原定义文档owner持有局部算法合理。手册明确结构容量与读取字节上限是两项约束，提高字节容量不会放大结构容量。

独立载入r4原模块，与r5比较9项JSON／YAML转换的实际值或错误，结果逐字相同。另验总值数100000接受／100001拒绝，默认parser仍接受两者；有限`1e308`、`5e-324`、负零与整数保持原值，重复key仍拒绝。原数值修正对NaN、正负Infinity及正负指数溢出继续拒绝，默认调用保持原语义。此轮没有引入没有已证producer路径的surrogate guard。

最强复核沿R4同一实际producer：用r5真实非editable安装，在自动清理的控制目录副本调用原`agent_runs.run_input`、原结构input和宽松schema `{"type":"object"}`；唯一替身是`processes.run`写入native结果槽位，实际模型调用0。正常summary／response／decision外的`extra`仍为990层数组。原writer成功、原run状态succeeded、保存SHA与原结果字节相同；reader仅将该result标为unavailable，错误为`Agent result exceeds 64 levels / 100000 values`。总体incomplete，另三叶均completed、完整result与原观察相同，三份原request-changes及全文保持。

实际`cli.main`两种格式均exit0、stderr空：JSON输出528,663B并反解等于同一观察；Markdown输出565,118B、末尾完整JSON反解也等于同一观察。读前／读后原result字节不变。因此原writer可成功保存的深坏结果现在在原观察边界逐件隔离，其他意见仍完整返回；没有截断原件或仅用不可解析的递归fixture替代该可达风险。R4独立关闭，R1–R3保持关闭。

### 冻结包、测试、原CLI及模板原件

- **包**：重建固定基线并覆盖冻结四产品文件后，与r5wheel和真实非editable `site-packages/ergora`逐份比较643文件的完整字节／长度／SHA，无缺件或额外件；283参考与基线相同。wheel实算SHA为`feef8ab41d0547a4c1eb7410b8bb1129829ba910b1282468410c494e6f2423cf`。不是仅采用`package-r5.json`的成功字段。
- **原测试记录**：直接读取XML／stdout。r4新深结果集成实红1失败，XML9.937秒／stdout9.96秒；r5源码3通过，XML4.720秒／stdout4.73秒，含报告深结果、原custom-schema writer深度62可读及深度80不可读。r5安装五suite共207通过、0失败／0跳过，XML180.180秒／stdout180.75秒：packet49、association64、invocation38、DeepSeek35、definition-console21。原定义编辑接缝包含JSON／YAML、重复key、alias、非有限值、object根、64层／100000值拒绝及不发布；共享算法的真实旧消费者也已覆盖。这里读取原记录，没有重复跑这些suite，也没有改写各轮原失败。
- **四原run只读CLI**：逐项核r5 argv、exit0及stdout／stderr摘要；完整JSON原字节仍等于r1第12条输出。使用r5与只读SQLite连接另行生成，观察完全相同；完整／非法选择的Markdown末尾JSON分别还原同一观察。LF、bare-CR、HTML及伪标题选择按CommonMark逻辑行保持缩进，错误叶未抹掉另三原反对。152原run文件及四DB行与CLI前清单逐字一致；原来源／manifest／先前runs及原source-state行也与最初`original-inventories.json`一致。四原Codex run的succeeded／四request-changes及完整回复保持，未重发模型。
- **自身原结构模板**：直接核run `a716f8f3095a43c09e607df8b521d8c5`的24完整文件433,329B／3资源、全部摘要及在task／实际prompt内的完整内容，prompt／protocol prompt／实际stdin相同；input digest为`1469471f56ecf9967df11421d23a021fa3429921e5e770196fb983b8a9697a0a`。原result与保存副本／解析观察相同，SHA为`7b11905aad6215dceaae7e105cae6aef6a302e8b43652d52e8421480d66cb774`，46.1608815秒、succeeded、approve。产品／测试／用户手册与冻结r5一致；plan／delivery／PLAN三文档在模型启动后补入最终207项、四CLI、自身意见及待独立结论记账，已逐段另读这些差异。模型没有认证后补状态或私有原件；本独立审查分别核验原记录。

报告入口继续由原来源绑定owner核明确source kind／SHA、完整manifest／digest、全部声明叶及实例／run映射；原record／input／result身份和可信reviewer schema仍是完成前提。错误原件继续逐叶不完整，已核完整反对不能被覆盖率或其他叶批准抹去。CLI保持薄读取／渲染消费者，没有当前来源再认证、redispatch、调度、正式批准或项目产品编辑。局部容量复用和原fixture的producer／consumer边界回归与此次真实故障对应，未见需要另建框架、模块或CI job的维护性证据。

本次仅追加本报告；未安装、实际调用模型／训练、重跑全量测试、commit／push或写外部平台。独立深结果复现仅在自动清理的隔离副本使用原进程接缝替身，原保存件未改。12份文档／168本地链接的原检查记录已核；本追加再检查旧前缀、链接和空白。原四叶是CPU算术来源的advisory Codex审查，不证明训练／GPU／质量／性能、异后端、正式串行图／all-join或完整B3。前片8job／30步骤CI只属于其原终核，本reviewer未独立认证该CI；本片自己的固定提交、发布／CI和原终核仍须后续分别完成。

## 固定发布与本片自己的CI终核

**固定提交`5a3e3b2a96c92632a65e60e87bcfc8713eff41e9`需求正确性approve；结构与维护approve，需求开放0／结构开放0。本片固定发布、自己的适用CI与原独立终核已闭合。** R1–R4全部保持关闭。本段仅追加原报告；追加前27,365B前缀SHA256仍为`264d43cc9586a4904bf90cd66998c110b5ad3b187d2341f341d774929a39ffa2`，各更早前缀也保持原值。

### 固定Git内容、包与远端身份

独立从Git对象读取提交、父对象、完整tree与19份blob，未用当前工作树替代：父提交恰为原基线`96b4bb5454714a73e1d5f60b880a479c195e5269`，tree为`bf32214c148ab72554bc5ebbd4a4f8b146e6fcdd`。相对该父对象恰19路径，与冻结r5及`publication-local-r5.json`路径集合相同；逐份实算blob对象ID、完整字节长度与SHA256，均与原发布清单一致。清单原件SHA为`263923a1750cd40b10967d54bd5078c840e02555659a469262583dc3fd45f9cf`。提交内本报告为27,365B、blob `fdbb5bcbb41fb0e308e516cf5932e7dc339a1a64`，本终核附记不倒算进该blob。

四产品模块、三原测试和两本用户手册与冻结r5逐字相同；另读plan／delivery／PLAN及上层source-review-reports四状态文档差异，均为R1–R4关闭、两轴approve／开放0／0及发布／CI尚待的记账，没有扩大行为范围。Q4.2两计划／交付新文件不在该提交tree内。等待期间开展的Q4.2a1工作树改变也不属于此固定对象认证。

从该固定提交直接取643份产品完整字节，与原r5wheel和真实非editable安装再次逐份比较，文件集合、长度与SHA均一致，无缺件或额外包文件；Git中的`src/ergora/AGENTS.md`是独立源码指令文件，不计为打包产品。283参考文件同时与原基线逐字一致。r5wheel SHA仍为`feef8ab41d0547a4c1eb7410b8bb1129829ba910b1282468410c494e6f2423cf`。没有为此重新安装或重跑模型／测试。对固定提交12份Markdown另核168本地链接及其中8个片段、尾空白，均无错误。

已读普通push回执，并在CI前及终态后分别独立执行只读`git ls-remote --refs origin refs/heads/refactor/architecture-foundations`；两次exit0、stderr空，完整输出均为该40位SHA及完整分支Ref。终态观察时间为2026-11-14 21:41:35 UTC；stdout 86B，SHA为`e0e66b61f38732b677a510bd259da1d1128c9b3c7bb25aa7f11ea9547ccc6eb5`。没有借本地remote-tracking ref或推送进行中的状态预设成功。

### 本SHA自己的Portability原件

通过匿名只读GET按完整head SHA发现且核同本片自己的[Portability run 43642459815](https://github.com/626619403/Ergora/actions/runs/43642459815)，attempt 1，event为push，workflow为`.github/workflows/portability.yml`，head branch为`refactor/architecture-foundations`。发现、run API、attempt jobs API、逐轮完整job集合及最终官方run／job页始终对应`5a3e3b2a96c92632a65e60e87bcfc8713eff41e9`。这是本提交自己的运行，没有采用前片`96b4bb5`的CI结果。

从在途观察到终态，job集合始终恰8项、无分页遗漏；最终API和8个官方job页面逐项相符：

|Job|精确job ID|必要步骤|终态|
|---|---|---|---|
|plan|132592797515|1|success|
|Ubuntu／Python 3.11／group 0|132592827199|4|success|
|Ubuntu／Python 3.11／group 1|132592827205|4|success|
|Ubuntu／Python 3.11／group 2|132592827222|4|success|
|Ubuntu／Python 3.11／group 3|132592827194|4|success|
|Ubuntu／Python 3.11／group 4|132592827179|4|success|
|Ubuntu／Python 3.11／group 5|132592827195|4|success|
|Windows／Python 3.12／group all|132592827192|5|success|

必要步骤共30：plan的显式分组读取1项，7个native job各自Python设置／wheel构建安装／打包参考身份／原应用回归28项，加Windows PowerShell 5.1安装升级1项。每项API的status为completed、conclusion为success；官方job页对应名称／步骤编号／success一致、起止时间非空，log URL逐项指向同一完整commit及对应job ID。30项没有以skip或未开始冒充成功。Windows原应用回归与PowerShell安装升级均实际完成，整个Windows job于21:39:58 UTC成功；run API同刻更新为completed／success。没有从中间7／8通过提前推出终核。

所有读取保存于私有`.ergora/checks/complete-review-reports/ci/`。共34次匿名GET，单次30秒／4,000,000B上限，完整原响应和HTTP receipt均保留；实算长度／SHA与receipt逐项一致，均HTTP 200。终核汇总中的95份原件／脚本／校验记录也逐份重算核同。关键原件身份为：

|原件|完整字节数|SHA256|
|---|---|---|
|`reviewer-fixed-contract.json`|6,043|`52034e237207de3eead306751fd7d09a1a4723993256b6a5334da8c9d370f0ad`|
|`reviewer-fixed-docs.json`|36,488|`84d6906813286f67c8b1fd4159f576ebfc8be7a19ec8eb0310028ca28e8cfafb`|
|`reviewer-run-terminal-r1.body`|11,946|`1249fc10e8f7bc1712000c4fcf852e6ee52cbed5119be5b19229a3eb60fe961b`|
|`reviewer-jobs-terminal-r1.body`|21,121|`fe47c5a59be0a327f8d6d8ce6e3d00792315421a638f82cd1998dbfeee1523a6`|
|`reviewer-remote-terminal-r1.json`|564|`9cc36e2be0c64a854c76cfbff726ef0d3f2778f5c14b2923533ae758a991c32c`|
|`reviewer-ci-terminal-r1.json`|26,691|`2384e6a690682f845656f50e3438676e87155e3fc7b704e436d649f4eb45e378`|

最后一项包含8个job、全部30必要步骤的原名称／编号／起止时间／精确log URL及95文件完整摘要。这里的CI结论来自本SHA官方终态和必要步骤核验，没有另行宣称CI测试数量或读取未取得的日志正文。

此次持久化仅原报告追加及本片私有CI原响应／校验记录；本reviewer未修改产品、commit／push、重新安装、运行模型／训练、重复全量测试或写平台。现有advisory来源审查合同和本次Linux／Windows打包、参考身份、回归／安装CI范围内两轴均approve、开放0／0；训练／GPU／质量／性能、异后端、正式串行图／all-join和完整B3／Forge仍不在本终核范围。后继Q4.2a1及其他产品改变须有自己的固定范围和证据，不继承本片认证。
