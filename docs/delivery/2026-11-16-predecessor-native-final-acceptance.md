# M5 r7 与 native source-v2 r5 联合终核

2026-11-16。最终实现与各自安装证据已齐，**新 fresh 联合终审待完成**。未导入、推送或认证自己的 CI。这里集中接续依赖，不覆盖两片原始失败和模型判定。

|范围|准确候选／证据|
|---|---|
|M5 最终源|`5bcecf37b615e3708ceb08acc329ba3dd0470f4a`，父f672214，完整11文件patch61e1e11f；[逐轮交付](2026-11-16-training-cycle-predecessor-native-gates.md)|
|native 最终源|`bc58be6781d35e7e4fbd54ad997df8a4743428a8`，唯一父5bcecf3，native-only11文件patch3524d80f；[交付](2026-11-16-native-admission-dependency-isolation.md)|
|M5 新安装|core／SDK663产品逐字节／执行位相同、283／依赖过；5 passed／148.89秒；原模板67.198秒仅已知R1，R2–R6源审关闭|
|native 新安装|core／SDK665产品相同、283／依赖过；25 passed／161.78秒；正常选定解释器真实禁SDK whole-hook，在原完整容量边界到达原schema3关闭；原模板28.602秒approve|
|CI 配置|[四完整文件再平衡](2026-11-16-predecessor-native-ci-balance.md)，最终实际collector2335／原selector444、359；仅收集，官方执行另验|

## 安装输入及捕获身份终核

私有 `.ergora/checks/native-admission-dependency-v2/final-installed-r7-r5-audit.{py,json}` 在两轮已终态后运行。逐项重新读取 M5 的853／native的855源码输入、各自 core／SDK 完整产品和 wheel 内容／执行位，以及各179份测试／示例副本，全部仍匹配冻结身份。

只在两轮根自有安装 test roots 的原 request／owner／attempt／ack／started／stopped／result／identity／marker 记录和两个模型 original-result 内提取身份结构；247份指定 JSON 可解析。初次记录4条均absent，但新reviewer指出其中2条是 `synthetic_execution` 明示的pid2/start1与pid3/start2、boot全零；**不能把它们计作真实Linux进程**。原记录保留SHA256 `6ed78128dc3ea1a344274ded4af26ca6dd850c17d02129c3d80f992db99549ad`，不改写历史。

按原fixture精确合成三元组分开后的新 `final-installed-r7-r5-audit-r2.{py,json}` 再核相同源码／安装／wheel／副本，全部保持。**2个实际pytest父身份均absent，live match=0、unknown=0；另2个合成supervisor／executor单列**，合成pid1的出现数亦单列。不发信号，不称全局清点或已捕获所有业务子进程。r2 JSON SHA256 `c9ef8c705ec82fe3678d5af1f9b2b4b0c955c0901fd4ea6d0f07c9ea0b318576`。

同样只读分类原前期记录：r4／r6的31条结构含29实际＋2同一合成三元组，原JSON SHA256 `8177b158ce78961801555a9604bfddc70a2f8f7350084b4d3903671de0351665`；实施者r7的191条含189实际＋2合成，原SHA256 `af1975ea795492244481b4095291158f40514367844d427daa350206a828cdcf`。此处只纠正计数口径，没有重跑那些现场或把旧候选收尾转授最终组合。

## 待独立判断与边界

新 reviewer 应从原要求、准确源与真实入口检查 M5 R1 是否由最终 native whole-hook 证据关闭，而非把 pure `-S`、package identity 或模型 approve 当成替代。M5 原模型 request-changes 的已知依赖保留原判定，不通过重调用改写历史。其他时序 finding 必须沿各自红例／最小修正／受影响绿例核对。

本片只允许完整前驱认证与最后gate接线／依赖隔离。原 permits、attempt-before-send、锁、完成结果早读、全部原 H archive／phase 门、source／ROOT／measurement／interpreter／完整 clock 及当前 intent 语义必须保留。无旧owner升级、改pin、预算扩窗或新调度器。所有 schema3／ordinal1 执行效果仍关闭；M6正式producer／完整M1c／实际两轮、真实GPU／训练与质量不在本次验收。
