# PUB1：Apache-2.0 许可落实

维护者已明确选择Apache-2.0。本片落实该选择及发行包许可元数据；公共发行、GitHub精确远端身份和必要CI仍分别验收。产品基线为`5af9882367bbe5708f1a86ddabc16b2b665e9a49`，不包含同时进行的D2数据包改动。

## 改动与归属

- 根`LICENSE`采用完整Apache License 2.0文本，`NOTICE`标明Ergora贡献者与第三方边界。
- `pyproject.toml`声明PEP 639的`license = "Apache-2.0"`及`LICENSE`、`NOTICE`、`THIRD_PARTY_NOTICES.md`三个许可文件；已有setuptools最低版本78支持该元数据，不增加依赖。
- README和第三方说明同步项目许可；第三方组件及冻结参考发行保留原有许可，原许可尚未建立的资料不被根许可重新授权。
- [总计划PUB1](../plans/2026-11-01-all-in-one.md)将“等待维护者选择”改为已选择，完整公共发行仍开放。

未改动任何产品Python、已有第三方许可正文、283个冻结参考文件、运行配置、测试或CI。没有引入许可证扫描服务或外部发布。

## 验证

从固定基线导出隔离源码，仅叠加上述五个发行文件，通过已有本地构建环境执行`python -m build --no-isolation`，源码包与wheel构建exit0，用时6.256秒。wheel与sdist均声明`License-Expression: Apache-2.0`及三个`License-File`；wheel元数据版本2.4，打包的许可正文与源码逐字相等。

正常隔离venv离线安装exit0，458产品文件与固定源码／wheel／安装位置逐一相等；wheel的465个带摘要RECORD项和已安装包的469项均核过，三个已安装许可文件保持相等。`LICENSE`完整11,358B／SHA256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`与系统保存的标准文本逐字一致。wheel SHA256为`cc0c71df3e99efdda9b003a13110a68ac621959ff65ade5390412eaa74194401`，sdist为`6181bf2c582b2e761cdbdc3370c4ba60e235c178242e7f65b2ccd009ad4b3abc`。完整源码身份、构建／安装原命令及输出、两RECORD和元数据核验记录留在持久私有验收目录。

首轮验收驱动在`pip --target`布局下按普通site-packages相对路径解析入口脚本的RECORD，出现FileNotFoundError；构建与安装本身均exit0。保留该目标安装和失败记录，改在独立正常venv中核验实际安装布局；没有为适应验收驱动而修改产品或许可内容。

新的[fresh-context独立审查](2026-11-13-apache-license-review.md)分别核验Spec与Standards，开放finding0／0；独立离线重算七文件、标准许可正文、wheel／sdist／正常venv、458产品、两RECORD及283冻结身份。首轮验收驱动失败保留，未用后轮通过覆盖。

本片本地出口通过，将普通提交；远端Ref／自己的必要CI及完整公共发行仍开放。它是行政元数据与文档改动，不重复模型、Temporal或产品回归；它们已有结果仅归属原精确候选。许可决定及本片打包检查不替代完整公共发行或全仓第三方许可审计。
