# V4：原生回归的即时进度

2026-11-04。范围：CI 日志可定位性；本地wrapper探针、精确两OS CI及[独立最终审查](2026-11-04-ci-regression-progress-review.md)通过，V4完成。

## 原始问题和边界

F4.1 候选 `11e89cf44eb29fe9064bd0015417cf6bc54fdc5e` 的 [CI41662193234](https://github.com/626619403/Ergora/actions/runs/41662193234) Windows 必要步骤成功，Linux 超过原20分钟上限被取消。官方注释及job HTML已保存；Linux回归未完成，不能报告两平台通过。当前wrapper在pytest退出后才一次性输出全部结果，取消时没有可定位的逐例进度。

同Python/测试内容的历史F3.4b2本地完整回归为1723.45秒；其Linux CI为12分08秒。两者仅是各自环境下观察，不能单凭这两个数断言新超时原因。当时另启动原F4.1已安装包的本地同套件诊断，保留`-v`进度；实际完成结果见下文。

## 实现及验收

只改 `.github/workflows/portability.yml` 的回归wrapper：原套件与环境保持，pytest改为`-u/-v`，`Popen`逐行输出并flush；保留最近3500字符作为错误尾部，失败案例继续生成GitHub注释，实际退出码原样传递。构建、冻结身份、Windows安装、矩阵、触发、concurrency及20分钟上限保持。不增加依赖、不修改应用/测试或用跳过隐藏耗时。

实际以 `.venv-dev/bin/python .ergora/checks/ci-regression-progress/probe.py` 提取当前实际YAML脚本，未修改脚本，置入受控pytest模块验证成功/失败/信号退出分别为0/3/241（负信号值经Unix进程退出编码）；失败案例百分号转义和两类注释保留。三种情况下首行在0.063–0.078秒已可见，晚于0.7秒才写的结束标记当时不存在，证明输出在子进程结束前到达。保留原始输出/JSON及workflow SHA；不把受控模块当成完整真实回归或Windows验收。`git diff --check`通过。

独立初审P2指出初版80行deque仍可保留任意长行，未限制字符总量；已改为3500字符字符串尾部并删除deque/import。完整输出仍逐行转发，单次readline和字符编码的瞬时内存不宣称字节恒定。原探针保留原workflow身份，修正后实际YAML的三种探针另存`review-fix/`；独立复核确认P2关闭，当前workflow SHA为`a6274a6415ad9c249a8777d72bc3bf02de75dd05c36fbee9a97f8d7f15820bfb`，无未解决源码finding。

原F4.1非editable安装包的本地完整诊断实际结束：711 passed、19 skipped、36 subtests passed、1个既有warning，pytest报告2550.05秒；命令进程exit0。应用Python/测试未改，工作区另有F4.2a资产，不把本次结果说成已验证其DOM，也不代替远端两OSCI。相比历史1723.45秒，这次只记录环境中的实际运行观察，未测CPU/IO原因，不归因于新页面。

已独立提交推送`2137a95418879d48cce557016caa5c7f0d6a6a1b`，只含workflow及7份文档。精确[CI41679431542](https://github.com/626619403/Ergora/actions/runs/41679431542)两OS及必要步骤全部success；原HTML、选择及身份核查保存在私有`ci/`，独立审查者已核selectedJobId、精确提交日志URL和实时远端完整2137。348应用Git blob与旧3f287e wheel逐项一致，应用/测试树相对11e89cf不变；新有效门禁补齐F4.1，原取消结果保留。独立终结审查无未解决findings。成功不证明旧超时根因或性能提升。每行在换行后转发；长时间未结束的一行不承诺即时展示。

本片和F4.2a生产页面保持独立提交、审查及证据身份；本片提交的应用树仍为F4.1已验证348文件，不携带尚未验收的任务创建页面。
