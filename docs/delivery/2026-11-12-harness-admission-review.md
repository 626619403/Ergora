# F8-H0 Harness 准入独立审查

状态：**H0 本地出口独立通过，Spec／Standards 开放 finding 0／0。** 本结论限于研究、隔离安装身份与已明确纳入的分段探针；提交、远端精确身份和本片自身 CI 尚待后续核验。

## 身份与范围

审查者为 fresh-context 协调者 `f8_harness_admission_review`；Spec 与 Standards 分别由两个 `fork_turns: none` 的独立上下文审查，并由各自原审查者复核本片新增原件和最终文档。依据为原始用户要求、`AGENTS.md`、本片计划、总计划 F8／DS5，以及 `code-review`、`maintainable-project-delivery`（含 independent-review）与 `codebase-design`。

固定基线和检查时 HEAD 均为 `784da65da89bdd2fed4742e57e3f904c0f295216`，提交区间为空。检查命令为 `git diff 784da65da89bdd2fed4742e57e3f904c0f295216 -- docs/PLAN.md docs/plans/2026-11-01-all-in-one.md`，并逐字读取以下三份新增全文：

- `docs/research/2026-11-12-harness-admission.md`
- `docs/plans/2026-11-12-harness-admission.md`
- `docs/delivery/2026-11-12-harness-admission.md`

`src/`、`tests/`、`pyproject.toml`、`.github/` 对基线无差异。两份 tracked 文档内 D3c 的 CI 收口属于前片原审查记账，未递归重审，未转授给 F8。

本次两轴终核的精确文档身份如下；本审查报告另计为交付文件。

|受审文件|字节数|SHA256|
|---|---:|---|
|`docs/research/2026-11-12-harness-admission.md`|42,459|`4c38037460ba16fcb50946bff9183ddf5b39b4608471f2affe78f334f4e9e00f`|
|`docs/plans/2026-11-12-harness-admission.md`|3,496|`33ce437d248b881fdb5fe85fba6227db3caafe52707075c59916108bf8989f40`|
|`docs/delivery/2026-11-12-harness-admission.md`|7,182|`4ab410a9c7ce2485fddaf3b6000c75869780528ae7578b9161c7d541f9432ece`|
|`docs/PLAN.md`|25,746|`29dbfd4988c0ebc070f26f2adaedba93e9bc5493d47aa8f1063b46d8437c87a3`|
|`docs/plans/2026-11-01-all-in-one.md`|78,373|`67fea08abe982a9d09ab5de7f8cb9c830cb68548df0d758679bec17dd9be4fb7`|

## Spec

最终范围内 **no findings**。H0 文档研究、隔离安装身份及分段探针的本地出口满足；未发现缺失要求、范围扩张或错误满足。OpenHands 暂缓受限准入的选择、DSH 仅进入有界 SDK 评估、最小 owner 映射、未知恢复及后续门槛均有原件支持。上游 ambient／工具和生命周期限制与本项目缺陷分开。

直接复核自身原生回执：11 份完整附件共 333,323 字节、哈希一致；五 scope 均连续 UTF-8 读取至 null，candidate 正文 16 页、base64 原位重试 2 次。冻结输入、manifest、实际 prompt 及原结构化 approve 一致；234.64 秒对应外层 CLI 计时。判词未覆盖第三段或后续文档。

第三段原件支持 9.54 秒、一次 loopback、空工具、严格 JSON 及三个采样进程清理；MCP 夹具原 JSON 末尾确为字面反斜杠 n，错误发生于服务／runtime 启动前。结论不含 H1a 准入、产品适配、完整停止／恢复、全框架或提交远端通过。

## Standards

最终 **no findings**；明文规范违规 0、判断性 smell 0。已重读最终五文档；原件确认 234.64 秒 approve、11 附件 333,323 字节及五 scope 连续全文读取，模型判词仅覆盖冻结候选。第三段及启动前夹具错误的范围与归属准确。

沿用 `AgentBackend`／`Invocation`／原结果验证和进程 owner，基础 Python >=3.11 与可选 SDK 环境分开；未见推测性抽象、重复 guard、冗余验证分支、test 或 CI 扩张。性能与用量按实际区间和来源记账，未用分段耗时推导速度提升，未把缓存 token 重复累加或换算账单。H0 本地出口满足，正式 MCP、取消后代、恢复、平台与真实模型仍未验。

## 已直接核对的证据

- `.ergora/checks/f8-harness-admission/research/manifest.json` 的 18 份缓存全部字节数／SHA256 一致，状态为 17×200、1×404；固定源码定位 77 处及本研究 8 个本地链接可达。45 个被引用的唯一源码文件与相应官方 archive 逐字一致。最终五文档的 188 个本地链接目标存在，`git diff --check` 通过。
- 直接读取持久 home 的安装文件，OpenHands 328 件 RECORD／323 件已分发源码、DSH 25 件 RECORD／6 件 SDK Python 源码均与身份原件一致；两安装步骤退出 0。未将六 SDK 文件比对扩大成 runtime 构建身份；首身份驱动错误及未分发文档清单保留。
- `probe-minimal-r1` 为 45.34 秒整体超时、0 请求、无最终结果；`probe-minimal-r2` 为 23.35 秒诊断 wrapper 成功、一次 loopback、空工具表及本次严格 JSON／原 review 结果形状。请求 body 的字节数／哈希和保存的 document 一致，stdout 与 native 最终文本一致。
- 明确追加纳入 `probe-minimal-r3/{validated,result,native-result,requests}.json` 与 `process/{stdout,stderr}.txt`，并核对原请求 body／直连 helper。第三段 9.54 秒、一次 loopback、空工具表、原结果 schema 形状及三个采样身份无存活与原件吻合。三个分段都只证明其实际采样及服务线程停止；未推广为完整 MCP 后代停止。usage 来自合成 fixture，未视为真实用量。SDK 协议 timeout 与完整 run budget 分开。
- `probe-mcp-r1/fixture-error-audit.json` 与保留的 `agent/agent.json` 字节／SHA256 一致；离线解析得到相同 JSONDecodeError。原 helper 在服务构造和 runtime 启动前调用夹具准备，故该错误不能归给 SDK，也不是 MCP 行为反例。
- 纳入 `self-review-r1.json`、`self-review-r1/{review.md,original-result.json}`、`self-review-r1-read-audit.json` 及其原始输入、manifest、scope、native stream、采样记录和 `model-candidate-r1`。独立重算 prepared／actual 输入树、manifest、prompt／stdin、scope／原生 receipt、原结果身份，并从原生 stream 重建全部五 scope 的连续 UTF-8 正文；22 次 read 包含两次 base64 原位缩页重试，未将 base64 回执单独充当正文读取。
- 自身模板与随包模板相比仅修订、证据资源及材料上限发生所记录变化，权限保持。11 完整附件 SHA256 为 `a1bfbb57fa51ffa2660fe1529cae97ce202a567ab3210d9c5b690c034c3318f5`；原结构化结果 SHA256 为 `15d0605f2746c66b49b92925321e20c1c80bfa21c72e8619cf23e01cfb06716c`，与原 approve 及公开描述一致。四个采样身份无存活；原自报 usage 保留来源及覆盖区间，不解释为独立计费或双后端成功。

审查只执行文件／Git／哈希／原件静态核对；没有安装、运行 suite、浏览器、模型、网络、提交或产品写入。

## 结论边界与后续出口

本次仅追加上述明确冻结清单；其他并行 MCP 行为未纳入判词。自身模型只审其冻结十一文件架构候选，未独立复现安装、探针或未附带的一手实现；本次独立静态核验不扩大该模型覆盖。首身份驱动错误、首段超时、诊断 wrapper 范围及 MCP 启动前夹具失败均保持。

仍未证明正式 task MCP 全资源／越权拒绝、完整取消与未知恢复、真实模型／网关、Windows／WSL2、同模板六阶段或精确候选准入；runtime 的源码构建身份亦未知。下一步先完成 H0 精确提交／远端及本片必要 CI，再按原 owner 继续 H1a，是否进入 H1b 由其实际证据决定。本报告不关闭 F8 整体或其他工作包。

最终：Spec 0；Standards 0；各轴无最严重问题，H0 本地出口独立通过。
