# Q4.2a1：只读启动检查交付

日期：2026-11-15。固定基线`5a3e3b2a96c92632a65e60e87bcfc8713eff41e9`，以[具体计划](../plans/2026-11-15-training-start-admission.md)为准。

|步骤|实际状态|
|---|---|
|恢复／合同|已核原preflight、load／status、start双重preflight及原SDK-free进程；列明此入口只观察，不能替代正式准入／恢复／批准。|
|实现|原submission只读check模式、应用check_start与薄CLI已实现；原start双重preflight／attempt及恢复不改。已有意图返回原状态／不可新用，不查服务或补发。|
|源码|源码两新接缝首轮1通过／1测试SQL注入误用不存在revision列失败；改成原JSON document内revision后2通过／1.63秒。原失败保留，产品未为测试改变。|
|新安装|最终r2 wheel SHA为`cbe1c14efbb577810585db94d696a03f14f0c2f6e3c30ebcae135b85203ca495`；独立core与SDK非editable环境均643源／wheel／真实site-packages逐字一致，283参考保持。相对5a3e3b2仅三个产品模块改变；core无Temporal SDK，SDK环境为1.34.0。原training／submission／runtime／cancellation四suite安装54通过／210.12秒，无失败／跳过。|
|实际CLI|用原注册／baseline／runner／experiment owner准备独立合成CPU合同，再在确实无Temporal SDK的安装中运行三条check-start：正确SHA两次exit0且stdout逐字相同，错SHA exit2。42原文件和完整DB dump保持。模型／workflow／runner调用均0，没有实际训练／GPU／质量／收益或自动循环主张。|
|自身审查|原refactoring-quality中的ergora-structure-review 1.0.0，17完整文件354,253B／3完整祖先资源，run `343bb89a50284f6eb6be2b1cdd51fd8b`，43.254秒、succeeded／approve。授权Codex回退，不冒称异后端；只审所给完整资料，不认证私有原件／运行／CI。|
|独立审查／发布|本片新的fresh-context实现评审本地两轴approve／开放0／0；前片自己的CI及原终核已闭合，本片可普通发布。固定提交／完整Ref及自己的CI仍待，不能借前片认证。|

验收原件使用ignored持久目录`.ergora/checks/training-start-admission/`。不改目标业务项目、原参考快照或任何训练运行／批准状态。

## 验收身份和保留范围

- 包／参考：`package-r2-core.json`、`package-r2-sdk.json`、两份`reference-r2-*.json`及相应实际checker；目录名venv-r1沿初次创建，已重新安装上述最终r2 wheel，不能把旧dist-r1的包当最终候选。
- 源码首轮／修正后：`source-tests-r1.xml`和`source-tests-r2.xml`分列。安装四suite记录为`installed-tests-r2.*`，54通过，XML209.514秒／stdout210.12秒；一次原TestClient的Starlette弃用提示，不影响本片准入合同。
- 实际旅程：`native-journey-r2.py`／`.json`及同名目录。manifest SHA为`e8939c8c4fefc2be53835db3b0be6b190b09857b5ac6be18974769dffd3273a4`；两成功stdout SHA均为`040b446d0c571e173e96de23589aee6c661bd812537a5d82d0d6343f8218204f`。before／after原42文件及DB dump可直接比较。
- 自身原件：`self-review-r2-codex.json`及同名目录，input digest `7410a4ffb74719935172a7a8838ef28986a4d41820a7ac69f426819c735cc615`，result SHA `b288266e1697ae3360c4fcc8792a6e142c2c055b9493f13b36f44d2626a9163b`。产品、测试和手册与模型输入一致；此后计划／交付只补实际验收状态，模型未认证后补状态。

初次安装准备曾考虑绕开reference的Linux平台限制，核实原preflight使用`/usr/bin/git`后已撤回，reference.py相对基线保持。因此本入口仅Linux／WSL2，Windows原生历史读取沿原合同，未称新检查在Windows原生可用。提交前停止、跨恢复预算、有限选择和Temporal控制仍属后续Q4.2节点。

## 新独立本地终核

[原报告](2026-11-15-training-start-admission-review.md)为12,584B、SHA `61daea268894558530ecc013a6b53937c742960ec5361c94d85d0531862039a2`：需求／维护性均approve，实证finding及开放0／0。新reviewer直接核13完整快照／16证据、diff SHA `544c3c43b074716f6f5b7d43e61e1ed304cad6a2b861e7e3a3cdd927f22dd96d`、643两安装与完整wheel／源、283参考、原XML／三CLI／42文件和88行DB dump及自身17完整文件／全部3资源／实际stdin／原reply。

独立另跑新两接缝2通过／1.29秒，并在可自动清理的原fixture副本经无SDK安装CLI验证四已有状态：正确SHA均exit1、错SHA均exit2，原状态／文件／DB保持。该八命令使用本地合成checkpoint，不是服务恢复或训练证明。没有产品finding，未为审查扩大测试矩阵。后补计划／交付只记实际状态，下一片a2设计和前片自己的CI仍各归原审查／终核，不改变本片产品范围。
