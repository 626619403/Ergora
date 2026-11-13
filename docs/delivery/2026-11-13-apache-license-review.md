# PUB1：Apache-2.0 许可落实独立审查

审查者：`/root/apache_license_review`，2026-11-13，fresh-context 独立上下文。按仓库 `AGENTS.md` 及 `maintainable-project-delivery` 的 independent-review brief，只读检查固定作者快照、邻接许可材料与已有离线发行物；本次唯一写入为本报告。

**Spec：通过；Standards：通过。** 在本片行政许可、打包元数据与文档边界范围内，开放 finding 为 **0 / 0**，无阻塞项。维护者已选择 Apache-2.0，落实该选择不再需要重复授权。该判词不关闭 PUB1 的完整公共发行，也不代表法律意见或全仓第三方许可审计。

审查基线为 `5af9882367bbe5708f1a86ddabc16b2b665e9a49`；检查时分支 `refactor/architecture-foundations` 的 HEAD 与其相同。作者范围由私有 `.ergora/checks/apache-license-r1/review-r1/manifest.json` 固定，SHA-256 为 `ca0d7913c49e9c8e57410e259db72409bae9ea2e1d011a5324d2a5a12742cd7d`。逐一复算其 `files/` 内七份完整文件的长度与摘要，并确认当时工作树中的对应字节相同；其他 D 旅程和 D2 专家配方改动未纳入本片。

|固定作者文件|字节|SHA-256|
|---|---:|---|
|`LICENSE`|11358|`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`|
|`NOTICE`|397|`8f4e28c59f27fa16369c947cfddbd70acf2d0735125b32fc44a4b4e807af9520`|
|`pyproject.toml`|1054|`3769bbcddad5b513e8290d3fb302fd4c68c4a1aa96dc01b35664da66f5799f27`|
|`README.md`|42747|`27dcb17a9f18f8ede97eb6d80e58fe23796f8664a3309d31dd447a2513f73719`|
|`THIRD_PARTY_NOTICES.md`|2049|`f35e7be22a95ce319f42ed8b86b3130bcd7ccc1462600153b8063cb4f5f87fb8`|
|`docs/plans/2026-11-01-all-in-one.md`|78933|`9a38f4a2d7f80472b49c255eddc25c7545a598940f8294f7dc3ce63e1a21c944`|
|`docs/delivery/2026-11-13-apache-license.md`|2652|`09538875588bdbb4cb4f1e897d11e2babb5169e9db404eb522b4e27a30fb6b25`|

实际检查支持以下结论：

- 完整读取根 `LICENSE`，包含条款 1–9 及标准附录；与本机 `/usr/share/common-licenses/Apache-2.0` 的 11,358 字节逐字一致。标准附录中的示例占位符属于原文。`NOTICE:4–8`、`README.md:434` 与 `THIRD_PARTY_NOTICES.md:3–6,18–30` 一致限定 Ergora 自有材料与第三方、原许可尚未建立的参考资料边界，没有新增对后者的授权。
- 对照基线 diff，`pyproject.toml:10–11` 仅新增 SPDX 表达式与三个 `license-files`；TOML 结构比较确认构建依赖、运行依赖、可选依赖及其他配置均未改变。复用既有 setuptools 接口，无新依赖、运行代码或测试框架。
- 对隔离 `source/` 的全部 1,309 个基线受控路径复算 Git blob 身份：除三个已受控发行文件覆盖外，其余 1,306 个路径保持基线；新增 `LICENSE`、`NOTICE` 连同三个覆盖文件均与作者快照相同。额外文件仅为构建生成的六份 `src/ergora.egg-info/` 文件。未混入 D2 产品数据，也未修改产品 Python、测试、CI 或既有第三方许可正文。
- 独立用标准库 `zipfile`、`tarfile`、`email`、`csv` 和摘要运算读取现有发行物及正常 venv，未执行安装包代码。wheel、sdist 根及 egg-info 的 `PKG-INFO`、已安装 `METADATA` 均为元数据 2.4，声明 `License-Expression: Apache-2.0` 和恰好 `LICENSE`、`NOTICE`、`THIRD_PARTY_NOTICES.md` 三个 `License-File`。实际许可文件位于 sdist 根和 wheel／安装位置的 `ergora-0.2.0.dist-info/licenses/`，逐字等于固定源码；已安装 `METADATA` 也与 wheel 相同。未发现重复 archive 成员。
- 全部 458 个产品文件在固定源码、wheel、sdist、正常 venv 之间逐字一致。wheel 的 466 行 RECORD 中 465 个带摘要项、正常 venv 的 470 行中 469 个带摘要项均重新核对摘要及长度；两者唯一无摘要项为各自 RECORD。wheel RECORD 覆盖全部实际文件。
- `reference-manifest.json` 保持基线身份；其 283 个冻结文件分别在隔离源码、wheel、sdist、正常 venv 及当前工作树逐项核对 SHA-256，全部相同。Cytoscape 原 MIT 许可亦保持基线并随产品内容进入包。这里证明文件身份及本次许可边界，未重新裁定参考资料的原始权利状态。
- `docs/plans/2026-11-01-all-in-one.md:175–177` 将维护者选择落实与公共发行分别记录，没有把本地元数据验收当作完整发行。新增许可入口及第三方说明、本片记录的相关本地链接均存在；限定七路径的 `git diff --check` 退出 0。

上述离线重算对应的原件均保留在私有 `.ergora/checks/apache-license-r1/`。本次核过的主要原件身份如下，摘要为 SHA-256：

|原件|摘要|
|---|---|
|`source-manifest.json`|`5af9b4f54cf2f051459b7fd616a89da6d70ac87e4eb1d34a376d4d33bdcbd741`|
|`build.json`|`2c798839adb1ce81dd59e48af541d8893d1f2055a1257fa2ec1129119e21d15e`|
|`build.stdout`|`99f6704ebf72ac044730fb4d80813e958521ade0776dd1acd6d849e828214494`|
|`build.stderr`|`807e97125a07cf58c76bef6d9db88eabace05a8d396c6082665436b821e3923f`|
|`venv-install.json`|`39e3728b6191c602e5aa27951e0283aeb3a62e3aae9ec079264558a0a3b4f4ed`|
|`verification-r1-error.json`|`3a7150e607727da20e290c7d38de0bf4742ff1e4a9d885001117e22475af61a5`|
|`verification-r2.json`|`085ebcc8dd0b7a24a4a51d79b2f6890693a85d0ff6fccc2db958a613970bf62f`|
|`dist/ergora-0.2.0-py3-none-any.whl`（1,718,838B）|`cc0c71df3e99efdda9b003a13110a68ac621959ff65ade5390412eaa74194401`|
|`dist/ergora-0.2.0.tar.gz`（1,724,298B）|`6181bf2c582b2e761cdbdc3370c4ba60e235c178242e7f65b2ccd009ad4b3abc`|

构建／安装的退出状态与耗时来自已有原件，本次没有重跑：`build.json` 记录 `/usr/bin/python -m build --no-isolation`、退出 0／6.2556 秒；读取构建输出的许可文件追加记录、成功末尾及完整 stderr，与现有两个 archive 一致。wheel 自报构建器为 setuptools 78.1.1。正常 venv 的 `pyvenv.cfg` 记录 Python 3.12.3、禁用系统 site-packages；`venv-install.json` 及原 stdout／stderr 记录 `pip install --no-index --no-deps --no-compile`、退出 0／1.7587 秒。这是本地许可打包验收，不是依赖齐全的产品运行验收。

首轮 `pip --target` 目标目录、`install.json`／输出与 `verification-r1-error.json` 均仍存在。离线读其 RECORD 确认记录脚本为 `../../bin/ergora`，直接以目标根解析时不存在，而保留的脚本实际在 `installed/bin/ergora`；正常 venv 的 RECORD 为 `../../../bin/ergora`，以真实 site-packages 解析可找到文件且摘要通过。该修正属于验收布局选择，没有改变本片产品字节；首轮失败未被改写为通过。

本次未构建、安装、运行模型、Temporal 或产品回归，未安装依赖、访问网络、检查远端 Ref／CI、提交或推送。既有产品行为结果继续只归属原候选。未评估所有第三方原始授权、再分发义务或未知参考内容能否公开发行；本报告不将元数据表达式的存在提升为这些问题已解决。后续公共发行、精确提交／远端与必要 CI 仍应按各自范围验收；本片实现与本次本地离线审查可记录为通过。报告及状态记录无需递归独立审查。
