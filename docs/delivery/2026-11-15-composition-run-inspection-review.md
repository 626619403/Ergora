# Q2.3b1：原组合运行读取独立审查

日期：2026-11-15。审查者：fresh-context reviewer `composition_run_inspection_audit`。只读审查源码及必要原件；仅写本记录，未安装、调用模型、重跑全套测试、提交或推送。遵循仓库三处AGENTS、组件协议、maintainable-project-delivery独立brief及ergora-codebase-quality三份参考。

## r1结论

- **需求正确性：request-changes，开放2项P2。** 精确查询、完整结果、搬迁及离线读取的主路径成立；一件材料损坏时保留其它可核证据的合同尚有两个缺口。
- **结构与维护：request-changes，限于下列恢复边界。** owner／薄CLI适当，无须新增模块、ABC、schema或State。未发现其它有证据的结构阻塞项。

检查基线`f1fc4501b8f15060eee7502caf6531c8f44a1b5f`。r1冻结范围为私有`composition-run-inspection/review-scope-r1/`的12路径；已独立逐一核`scope.json`中的字节数／SHA、完整files及author diff（SHA256 `f2498d72eabca197a069833ba50561a57c842e68f2bf4e0bca22afcd6f3f0242`）。检查时12路径与工作树逐字相同。产品仅`agent_runs.py`和`cli.py`；测试仅原`test_composition_invocations.py`。其余为使用／本片合同或前片发布记账，不把前片CI当作本片认证。以下行号均指r1冻结源码。

## Findings

### R1／P2：input故障连带隐藏仍能核身份的原prompt

位置：[agent_runs.py](../../src/ergora/agent_runs.py:407)，`inspect_run`中以`input.available`控制是否读取protocol prompt。

使用r1非editable安装，在临时目录复制原run `efd0fc2581d24d45a42e20d34b475c97`的完整input、protocol prompt及result，原数据库仅以SQLite `mode=ro`读取。完整副本的三项均可用；仅改副本`task.txt`后，input正确不可核，result继续可核，但prompt直接得到`available=false`和“cannot be matched without its verified input”。独立计算的protocol prompt SHA仍等于原record的`prompt_sha256`，字节数仍等于原`input_request.prompt_bytes`。因此另一件损坏导致仍可核的原请求证据被隐藏；缺失input同样可达。

最小修正：prompt先按原record的SHA／字节数独立核验；input可用时再逐字交叉核。缺少原prompt身份应只令prompt明确不可核。沿原fixture补一个input缺失／漂移而prompt和result保持的断言，无须新增框架或后端分派。

### R2／P2：深层持久JSON使整份观察中断

位置：[agent_runs.py](../../src/ergora/agent_runs.py:405)，input观察仅捕`OSError`／`ValueError`；其下`inspect_input`经原`read_json`调用JSON parser。

在同一隔离副本把`request.json`改为15,000层数组（30,001B，低于原10MB树容量），r1安装实际抛`RecursionError: maximum recursion depth exceeded while decoding a JSON array from a unicode string`；`inspect_run`没有返回观察，仍完整的原result因此也无法显示。此处是单个input文件漂移，无须改record或依赖后端。当前Python3.12中1,500层可解析；以上结论采用实际触发异常的15,000层，未依赖模板推断。

最小修正：在本用例的材料观察边界将`RecursionError`转为该项`available=false/error`，继续观察其它材料。result的JSON读取也应沿同一异常边界处理；本次独立复现直接覆盖input路径，未将修改record SHA后的构造结果冒充原writer的业务路径。回归应使用会实际触发异常的深度，保留原run状态与完整可核result。

## 已核范围与测试价值

沿`composition inspect-run`→`agent_runs.inspect_run`→原`inspect_input`／`agents.invoke`保存路径核了完整输入、祖先资源、权限、共同protocol prompt、result SHA及JSON。原backend实际transport差异仍留在各实现；新reader未调用当前backend准入，不将JSON按今天的后端schema重认证，不读取metadata绝对指针、不重发或产生新生命周期。result可用仅表示原字节身份和JSON，后继报告仍须应用可信reviewer合同。

`_record`将原output与新读取的精确SQL和持久project／ID核验留在原owner；`_artifact`局部集中普通文件／容量读取，调用者无需持有存储检查。二者没有独立新模块或假想后端扩展。run ID、显式正整数容量、普通目录／文件和SHA guard各保护外部输入、持久身份或有界读取，未见无关配置限制。超大合法容量未被锁成默认值。

七个新参数化接缝复用原fixture／原保存路径，覆盖最近100条之外、跨项目、控制目录搬迁、无当前backend、完整长回复、原状态／其它材料保留，具有实际静默串身份或丢证据风险。缺少的正是R1的prompt独立核验及R2的parser异常隔离。原output stdout／stderr分支未改，沿web原消费者及DeepSeek归档／续接的共享读取接缝检查，没有要求重复测试或新增CI job。

直接核验的现有证据如下；未把汇总布尔值当作原件验证：

- r1wheel SHA256 `7eeee20d3e757476b87b7509bf05ea26071096d853d22ab63fd0cb61f0323510`；独立逐一比较643份源码／wheel／安装字节与package清单，全部相同，仅两产品文件变化，无新增／删除。安装路径确为site-packages。283参考文件包含于该逐字范围，原reference记录保持。
- 原XML及stdout：源码invocation 32通过／4.18秒；安装四suite 72通过、23可选跳过／14.55秒；MCP extra补测原DeepSeek suite 35通过、0跳过／21.96秒。后者包含原native-history／continuation及unknown不重发接缝，不把它们称为新的真实SDK／模型调用。
- 五条已保存CLI的stdout／stderr SHA、原数据库行和原result字节／SHA／JSON直接相符。两前片真实run分别保留1,679B request-changes及1,150B approve；容量不足后明确完整读取、完整控制目录搬迁读回成立。前后清单的38／19原run文件及全部原记录仍相同。新入口只读验收，无新模型业务验收。
- 自身原结构模板run `51be70035a54488399a4a981866b1c8c`的DB行／native stdout、21份完整scope文件（434,085B）、完整task及3份继承resource均直接核；冻结prompt／protocol prompt／实际stdin逐字相同。原input digest为`265c3bfa7cb03a9666ca0898a8f9f10fa05cc57d0f36d261c2e3169c35783dce`，原result SHA为`2679ceebee29b70dbab5486ff65e0e36642f4752b223bfea951cd1ccded37739`，decision为request-changes。其两项理由已以上述独立源码检查及隔离复现核实；模型结论本身不是本审查证据。该调用使用有记录的授权Codex回退，不称异后端成功。

## 剩余门禁

R1／R2修复、适用接缝和新包身份需给本reviewer复核；r1原结果保持。未验Windows实际读取、真实异后端、本片固定发布／自己的CI及终核。未执行训练、GPU、质量或性能验收；不认证后继报告／全图调度／批准／平台写入，也不把前片CI或本片旧包认证到后继工作树。

## r2复核：本地两轴approve，R1／R2关闭

同一reviewer继续复核原片，未预设关闭。baseline不变；新冻结`review-scope-r2`含13完整路径及r1审查记录，所有字节数／SHA、author diff SHA256 `d3506b691a68a97bcb13001e5b8635b2b9bad1e855e6917403091fcc06ee95ae`已独立核对。检查开始时13路径与工作树相同；后续计划／交付仅记录新结果，产品、测试及手册仍由本r2身份约束。

**需求正确性approve；结构与维护approve；开放finding为0／0。** 以下结论只覆盖本地精确候选，固定发布、本片自己的CI及原reviewer终核仍待完成。

- **R1关闭。** prompt在原owner独立验证原`input_request`合同、原request／record两份SHA和字节数；完整input也可核时再逐字交叉核，并用`input_compared`明确覆盖。该字段没有把独立可核冒称为完整input已核。用r2非editable安装和另一个临时隔离副本，独立重做task漂移及整个input树缺失：两者均保留prompt可用、`input_compared=false`及原完整result。完整副本则标记true。原DB只读备份到临时目录，未改两条历史run。
- **R2关闭。** 各材料边界容纳`RecursionError`，未改公共JSON协议或生命周期。独立重做15,000层／30,001B的request损坏后，只有input不可核，原prompt／result和run不变；恢复input，再对副本result构造同样JSON，并经原State writer同步fixture SHA，只有result解析不可核，input／prompt及原status保持。result构造只说明parser错误边界，不称原writer曾生成该业务结果。上述读取将`for_binding`和`agents.invoke`替换成必失败函数，仍成功返回观察。

新增测试仍在原invocation fixture和原保存／查询接缝。实际红测试原XML和stdout直接证明input漂移、递归input、递归result三条失败，31条未选／0.70秒；前一次7失败中四项只是新字段尚未实现，未混称为四个额外缺陷。修后源码34通过／4.00秒；安装invocation 34＋原DeepSeek 35合计69通过、0跳过／26.50秒，含共享output归档、续接及unknown不重发。新增递归result先更新副本摘要，确实经过JSON parser，未只测到SHA拒绝；新增断言保护独立观察语义，没有新增测试文件或CI job。

r2wheel SHA256 `6a38e336970627e20ca1f6890bce3552166bcf681c5fbd9bea4fee1baff31956`已独立重算；643源码／wheel／新site-packages安装逐份字节及package清单相符。仍只改agent_runs／cli，无产品文件增删；283参考保持原身份。原r1包／结果保留，未借r1包身份认证本次修正。

八条保存CLI的stdout／stderr SHA均直接核过。前七条run仍等于两原DB记录，所有可用result等于原完整文件／SHA／JSON；第3条只报告容量不足，第4条完整读，第5条迁移读，第6／7条仅隔离副本input故障。第8条副本record只有测试所需result摘要变化，原State writer写入后result递归错误被隔离，原status及其它材料保持。两条原run的38／19文件和DB记录仍与r1原前后清单逐字相同。首driver裸SQLite更新副本被writer guard拒绝的原stderr仍在；核了续接driver只修fixture并执行第8次读取，没有改产品绕过保护，也没有重发模型。

新自身模板run `2714f6e314a24c17a5fa17cff88c2bdd`的原DB行／native stdout、21完整scope文件（439,899B）、完整task及3继承资源已直接核；产品／测试／两手册与r2冻结范围一致，冻结prompt／protocol prompt／实际stdin逐字相同。原input digest为`83f3a21f1124ba6a3b0e25ecdc5de08fbe62e2a0c47ed309378a32199297f91d`，result SHA为`fafca90f49a3e4f9183231f6327c59f4548eacdd48f12f0c3c402c881b3e8798`，decision为approve。其意见仅覆盖supplied-text；本reviewer以上述实际原件和独立复现自行得出结论，仍不声称异后端成功、Windows实际验收或训练／GPU／收益通过。

## 本地固定提交复核

固定提交`96b4bb5454714a73e1d5f60b880a479c195e5269`，直接父提交为原baseline `f1fc4501b8f15060eee7502caf6531c8f44a1b5f`。本次仅用`git show`／`git cat-file`读取固定对象及已验r2原件，不将后继工作树纳入认证。

独立核定相对baseline的13路径与r2冻结范围一致，逐一读取13个blob／OID／完整字节：9个与冻结r2逐字相同；另外4个为`docs/PLAN.md`、本片plan、delivery及本review报告，只更新已核自身模板／独立复核和后续门禁状态，没有新增行为。原r1段和r2结论完整保留。13路径→blob OID映射按键排序、紧凑JSON的SHA256为`3583c3b97cf73e63057753f05c7d78e0451cf5f9b679623102b2fde04b692ae8`。

固定产品blob仍为agent_runs `29b44d679f776519a06725f35502e8a0ecb46c74`、cli `d7695d94af8e0e90c38946f04a23caa78b9fd5a2`，原invocation测试为`fc99084a500a201f996b6f51b81d849c448b4e68`。另从固定Git对象逐份重比全部643产品与r2wheel／独立安装及原package字节／SHA清单，全部相符，283参考包含于同一核验；r2wheel SHA仍为`6a38e336970627e20ca1f6890bce3552166bcf681c5fbd9bea4fee1baff31956`。固定diff空白检查通过。新增记账与已核原件相符；链接检查保留首个不识别`:行号`的失败原件及修正后的202项结果，没有更换r1报告或夸大运行验收。

**本地固定提交需求正确性approve、结构与维护approve，开放0／0。** 此时尚未推送，完整远端Ref、本片自己的CI终态及原reviewer终核仍待；前片CI不认证本提交，后续改动也不继承本结论。未新增模型调用、安装或重复既验回归。

## 固定发布与自己的CI终核

2026-11-14 21:00 UTC完成终核。两次独立`git ls-remote`均返回完整`96b4bb5454714a73e1d5f60b880a479c195e5269`对应`refs/heads/refactor/architecture-foundations`，原stdout／stderr及最终命令回执已保存。本次继续只认证该固定Git对象、r2原件和它自己的CI，没有读取后继产品工作树作为验收依据。

按完整head SHA的官方API查询发现唯一[Portability运行43638408686](https://github.com/626619403/Ergora/actions/runs/43638408686)，event为push、attempt为1、workflow为固定`.github/workflows/portability.yml`。独立跟踪并保存过程原件后，最终官方run API为completed／success；精确attempt jobs API的8个job与原发现ID集合完全相同，全部completed／success。主run页面也显示Success和同一完整提交。

直接逐页核8个官方job页面，并与API中的步骤名称／编号／状态交叉核验：plan的1个必要步骤、六个Linux分组各4个、Windows分组5个，共30个必要步骤全部success。各原步骤的开始／结束时间存在，log URL均绑定完整`96b4bb5…`及对应原job ID。Windows原生回归于20:57:30 UTC成功完成，PowerShell 5.1安装／升级于20:58:26 UTC成功完成；本地阶段未验Windows的范围现由该固定提交自己的Windows CI接缝补足，未扩大为真实模型后端或训练验收。

固定workflow、显式分组和runner分别从该提交保存，SHA仍为`be814a956237b8a64258f396fa81a972ff764ceaa3ea16ffefa8e82be89a4353`／`b50d95a1954d6e2612183feccc7b5a764c9109c479997dec7fe628127b55981e`／`cc465950dd63ad1b73b6abe611358b87e756ef011daca18d06894941e503f1d8`。确认包含本片原invocation与共享output的原归档／续接接缝，没有使用前片成功代替它们。

私有`composition-run-inspection/ci/`保存本reviewer的39个匿名GET原body及HTTP元数据，单请求超时30秒、显式容量4,000,000B，原响应合计2,264,827B；109份捕获文件及其清单逐份重算字节／SHA相符。原发现分页也保留，后续显式完整八job观察及最终API无缺页。终核汇总`reviewer-ci-terminal-r1.json`为28,763B，SHA256 `20513735ff01b4a87d29f9416891e12564ed961dcfd39135b669d0d3d696b461`。只作GET及远端Ref读取，未重跑CI、发起平台写入、安装或调用模型。

**固定提交的发布／自己的CI／原独立终核门禁关闭：需求正确性approve、结构与维护approve，开放0／0。** r1失败与r2修正的原记录保持；本结论不认证后继b2工作树，也不增加训练、GPU、质量、性能、异后端或正式批准主张。
