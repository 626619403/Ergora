# c1a1：控制器意图准备独立产品审查

日期：2026-11-15。审查者：独立 fresh-context agent `training_controller_intent_product_audit`。项目与文档均归 Ergora；仅写本报告，未修改产品、依赖或测试，未安装、提交、推送或运行昂贵检查。

## 范围与结论

先读原始需求、[原合同](../plans/2026-11-15-training-cycle-controller-contracts.md)、[已批准父计划](../plans/2026-11-15-training-cycle-workflow.md)及[本片验收](../plans/2026-11-15-training-controller-intent.md)，再查实际 diff、完整 owner 与邻近 caller，最后读作者[交付说明](2026-11-15-training-controller-intent.md)。遵循根／源码／测试 AGENTS、组件协议，以及 `maintainable-project-delivery` 的 independent-review 和 `ergora-codebase-quality` 的 repository-style／module-design／test-seams references。

基线为 `fbafd8d7fc442acb8c52e0646ada327cdfb49fa3`。初审时提供的 `review-scope-r1.json` 中七文件 SHA 均与当前文件相同；后续计划／交付的证据状态更新另计，不继承旧文档 SHA。被审产品／测试身份如下：

|文件|初审 SHA256|
|---|---|
|`src/ergora/training_cycles.py`|`e2a719c6b5fb062c11459ff4f87af25aa10edc0821e40f2608a78d369178da6b`|
|`src/ergora/training_execution_protocol.py`|`1b15c7bcb75770894adfcf1cd161878dbc5536dd6cdb457b767487e0f6b4dff0`|
|`tests/test_training_submission.py`|`bf6932d8cd6b74e9b75be52f31afa652e58534dca8cbbc32b22e6410e4327a65`|

另四文件为 `docs/PLAN.md`、`docs/architecture/current.md`、本片计划与交付；完整七文件原快照及 tracked diff 位于私有证据根 `.ergora/checks/training-controller-intent/` 的 `review-scope-r1.json`、`review-scope-r1/`、`review-tracked-r1.diff`。

- **修后本地终核：需求正确性 approve／结构维护性 approve，开放 0／0。** 最终 `review-scope-r2.json` 七文件与现场／冻结副本逐字一致，R1 已关闭；修后源码、新安装、原失败回归和收尾证据已分别核实。
- **初审历史：需求 needs changes，P2 R1 一项；结构 approve，0 项。** 下文保留原 SHA、原失败与修正记录，不改写旧验收范围。
- 两个原 owner、调用方向和共享字段生成合适；无新增模块、SDK、持久 schema、source key、公共入口、第二运行状态或不必要抽象。本地结论不转授 SDK 总投递、真实 Workflow、双服务、CPU 两轮、GPU／业务训练或发布 CI 的验收；固定提交／普通发布仍沿原门禁。

## R1（P2，已关闭）：最后同步读取耗尽窗口后仍可能返回 ready

位置：初审 r1 快照的 `training_cycles.py:424`，邻接 [CycleAdmission.check](../../src/ergora/training_execution_protocol.py:391) 与 [_status](../../src/ergora/training_cycles.py:310)。初审顺序为最终 `status` 计算剩余时间，随后 `admission.check()` 再读取完整原 authorization 并 `lstat` stop。该同步文件读取可以阻塞并耗尽计算窗口，之后仍返回此前的 `ready`／正剩余时间。初审 `_status` 内部也先算 clock，再执行 schema2 stop 观察；仅交换末尾两行不能覆盖所有这类读取。

这违反本片“最终重新观察耗时后的原计算窗口；exhausted 不能返回 ready”。准备本身未派发候选，后继仍有实际动作 gate，因此本项不声称已经绕过训练执行期限。

最小修正：保留最后 stop veto，并让最终原 `budget_clock.remaining` 观察晚于这些业务文件／项目读取；维持原 stop 对其他状态的覆盖优先级与原 clock／policy，不新建计时器或重复 validator。作者提出在原 `_status` 将 schema2 stop 读取移到 clock 前、末尾显式 check 移到最终 status 前，符合该最小方向。修正后在原耗尽测试增加 final-check 接缝，保留目录同步接缝，核原件／clock不变；受影响的源码与新安装证据须重验。

独立只读确定性探针终态如下；实际执行生产 `prepare_controller`、`_status`、`CycleAdmission.check` 和共享字段生成，SQLite／flock／文件发布和剩余时间使用内存替身。它证明读取顺序缺口，不是实际文件系统阻塞或真实 Workflow 的验收：

```json
{"actual_final_clock_status":"exhausted","actual_final_work_remaining_seconds":-4.0,"authorization_reads":2,"returned_status":"ready","returned_work_remaining_seconds":2.0}
```

## 所有权、guard 与测试价值

|变更／检查|实际 caller 或可达失败／所保护的行为|判断|
|---|---|---|
|`prepare_controller`|本片明确应用用例；当前尚无生产入口 caller，后继 SDK 片消费。它内聚持有 State reservation、原 status、父共享许可与原 publisher，不是单次调用的转发包装|位置正确；不要求虚构 caller 或增加公共入口|
|`intent_record`|生产文件 `training_cycles` 的 producer 与 protocol 原 `controller_intent` reader；原 reader 又被 budget／worker／native binding 消费|字段生成归已被 pin 的 stdlib owner；与原 inline mapping 一致，未改变缺文件返回 None 或完整 SHA 拒绝语义|
|revision 类型／正值、精确 SHA 相等、当前 revision|应用调用可以传 bool／无效 revision、None／错误 SHA，或持过期项目修订|入口拥有明确原身份，必要；没有重复 regex 验证|
|原 status 必须 ready|真实 publisher 仍持锁、ready 持久性未知、clock／项目漂移或 stop 已可见|复用已有状态语义，不凭 ready 路径存在授予准备|
|父 `permission` 与最终 `check`|stop writer 独立于父共享锁发布，可能在 intent link 之前或同步期间出现|最后 veto 必要；null-intent stop 不被补写或修复；R1 的 clock 观察顺序修正已核|
|首次 `_record`／已有 intent 分支|首次必须 file-fsync→无覆盖 link→directory-fsync；丢回复或同步失败后已有原件|重试只同步、完整验证并重读，保留 bytes／inode；原 SQLite reservation 序列化正常应用准备，不跨 RPC|
|三个新增原 fixture 接缝|publisher 持锁／恢复同原件，publication 中 null-intent stop，同步消耗 compute|均保护可达持久性／并发／期限问题；未增加新测试框架或重复 CI。R1 已在同一耗尽测试扩展 final-check／stop-observation，旧安装实红、修后实绿|

核过 `State.connect/project`、原 `training._setup/_submission` 的 reservation，`BudgetedStart.source/permission/check_controller_history`、worker `_cycle_target/_cycle_operation` 与 protocol `bind/_stop_record/observe`。原 start／launch slots、唯一 reaper、冻结参考、证据归档／比较权威、六阶段和人工 release 未在本片改动。未发现目标业务仓库修改或 kernel 专家 v3 移除。

## 初审身份的已核证据与边界

私有证据根均为 `.ergora/checks/training-controller-intent/`。

- `source-r1.json/xml`：23 通过，pytest 34.533 秒，外层 35.964 秒；其 cycles／测试 SHA 属于 None 接缝修正前，保留原范围。`source-r2.json/xml`：23 通过，pytest 34.064 秒，外层 34.863 秒，产品／测试为上述初审 SHA；两轮各自运行前后完整 source SHA 相同。
- `build-install-r1.json`、两 `package-r1-*.json`、`reference-r1-*.json`、依赖原结果：新非 editable core／SDK 各 652 产品文件与同一 wheel／source 逐字；原 283 参考 PASS，core 无 temporalio。安装路径确为 site-packages。
- `installed-r1.json/xml/stdout`：`-I -B` 使用新的 SDK 安装及冻结测试副本，33 通过／124.703 秒，外层 125.772 秒，errors／failures／skipped 均 0。包含三新接缝、原授权／父锁发布恢复、完整父 binding／固定 history／单 start、stop 与 ready 恢复、SDK-free 旧历史及全部架构检查；不称为全仓库或真实服务验收。
- `core-preparation-r1.py/json`：真实无 SDK core 安装对已有完整 schema2 原件幂等准备，0.091 秒，created=false／ready，5 原 cycle 文件逐字、DB rows 和原 clock 不变；无 attempt／receipt 或执行。
- `self-review-r1.json`：Ergora 自身原结构模板真实 Codex 33.545 秒 approve；16 完整文件／484,867B 与 3 原资源完整进入 stdin。它是所供文本审查，不能替代本独立审查或私有原件核验，也不构成异后端／真实 Workflow 结论。
- `integrity-cleanup-r1.json`：两安装／source 652 文件和 178 冻结输入保持；5 个已知 actor 身份的活匹配 0，其中含历史合成身份。只认证已列身份，不宣称扫描全主机或完成后继服务收尾。
- 远端 b2a 的 403／remaining 0／reset 是查询受限事实，无 CI 终态。本片未推送，不借其他候选 CI。最终固定提交、普通发布及自己的 CI 仍由原逐片门禁处理。

审查者另行只读重算同一 wheel SHA、两安装 652 项及 wheel 内完整文件集合／SHA、178 个冻结输入 SHA，均与各自 manifest 一致；直接核自身模板 `original-result.json` 的 approve 与文本范围。`git diff --check` 及本报告文件链接检查通过。未重复上述耗时测试、安装或模板调用。

以上为初审产品身份的证据；不转授修后版本。

## R1 修正源码复审

实查修正只将 `prepare_controller` 的最后显式 `admission.check` 移到最终 `status` 前，将原 `_status` 的同一次 schema2 stop 读取移到 clock 前；原 stop 的状态覆盖仍在原位置。没有新 helper、clock、policy、重复读取或 validator。原耗尽测试在同一 fixture 扩展 directory／final-check／stop-observation 三个边界，延迟按实际配置和原 `budget_clock` 余量计算；原预算／完整原件保持断言继续存在。

从本报告直接提取同一原失败探针，在修后生产源码重新执行：返回 `exhausted`／work=-4.0，与探针最后同一 clock 的观察相同；authorization 读取仍为两次。R1 的源码缺口已关闭，实际旧／新安装验证与最终 identity 另见下段。

`source-r3.json/xml` 实际 25 通过／54.937 秒，外层 55.786 秒，运行前后及审查时当前 source／测试 SHA 同一。修后 cycles SHA 为 `3c5127edb5938e803e4302a5dd775708b33ff4be2ddeea2e579391231fecd0b0`，测试为 `f3537278d3fed096261ad46979aaa2d537799e8d93b79d1563519cbc7dc162e9`，protocol SHA 保持。审查者另独立重算 r2 同一 wheel、当前源码及两非 editable 安装各 652 产品文件逐字相同；wheel SHA 为 `b7567dfad206bbfc671ac81cf96840d8b66d31c88e379e22f16e4634de49d2c3`。

## 修后安装与最终本地终核

最终 `review-scope-r2.json`／`review-scope-r2/`／`review-tracked-r2.diff` 固定上述七文件；审查者逐项比较现场和冻结 bytes／长度／SHA，均一致。报告按约定排除以免递归。产品仍仅原 cycles／protocol 两文件，测试仍原文件；计划／交付正确保留初审、原失败、修后验收与未验范围。审查时标记“独立终核待完成”与当时进度一致，作者随后只需记录本结论。

|实际原件|终核结果与范围|
|---|---|
|`original-r1-regression-r2.json/xml/stdout`|`-I -B` 使用冻结旧 r1 SDK 安装运行新 r2 冻结 final-check／stop-observation 两节点；两项均因 `ready != exhausted` 实红，23.327 秒／外 24.046 秒，无 setup error。确认新增测试能暴露原问题；原 r1 调用器参数 ID 错误为 exit4／零测试，单独保留，不算产品失败|
|`build-install-r2.json`、两 `package-r2-*`、`reference-r2-*`、依赖原件|两新非 editable 安装各 652 产品文件与当前 source／同一 wheel 逐字，完整集合无增删；仅两原产品 owner 不同于基线。两原 283 参考 PASS／依赖 exit0，core 无 temporalio，SDK 1.34.0|
|`installed-r2.json/xml/stdout`|新 SDK 安装与 r2 冻结输入，35 通过／stdout 145.43 秒／JUnit 145.420 秒，外 146.497 秒；errors／failures／skipped 均 0。含三实际 clock 耗尽边界与原授权／binding／history／stop／恢复／架构回归；无真实自动循环主张|
|`core-preparation-r2.json`|真实无 SDK 安装幂等准备 0.070 秒通过，created=false／ready，5 原 cycle 文件、DB rows 与原 clock 保持；无 attempt／receipt／执行|
|`self-review-r2.json` 及 `self-review-r2-codex/original-result.json`|原结构模板真实 Codex 31.493 秒 approve，16 完整文件／488,529B／3 资源进入同一 stdin。独立核原结果 SHA；保留原输出中“运行尚在途”的生成时点，终态运行另由本审查核验；仍限所供文本|
|`integrity-cleanup-r2.json`|652 两安装／source 与 178 冻结输入保持。审查者另重算两安装／wheel／source 及 178 frozen／current SHA；对列出的 7 完整已知 actor 身份另用原 identity reader 复核，当前活匹配 0；其中 3 为合成历史身份，不扩大为全机清理|
|`document-links-r2.json` 与最终轻量检查|所有变更 Markdown 的文件链接通过；本报告更新后另核自身链接与 `git diff --check`|

**最终本地两轴 approve／开放 0／0，R1 关闭。** 该结论绑定 r2 最终七文件及上述修后产品／测试 SHA；可继续原本地固定与后继计划。普通发布仍等待前片准确 CI／原 reviewer 门禁，本片自己的提交／远端 CI 尚未发生；限额 403 不是成功或失败。SDK attempt／receipt／固定 run 对账、独立 cycle 服务／stop 配额、真实总 Workflow、两轮 CPU、GPU／业务训练均未由本片实现或认证。

## 只读顺序探针复现代码

在仓库根使用已存在 SDK 环境，`PYTHONPATH=src .ergora/checks/training-controller-intent/venv-r1-sdk/bin/python -B -` 执行以下代码；无文件创建或产品修改：

```python
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
import json
from ergora import training_cycles as cycles
from ergora import training_execution_protocol as protocol

root = Path('/tmp/ergora-independent-order-probe-no-files')
directory = root / 'training-cycles/demo/controller'
project = {'id': 'demo', 'revision': 1}
auth = {'schema_version': 2, 'project': 'demo', 'project_revision': 1,
        'control_home': str(root), 'cycle_id': 'controller', 'input_sha256': 'a' * 64,
        'sha256': 'b' * 64, 'clock': {}, 'controller': {
            'protocol': 'ergora-training-cycle-v1', 'workflow_id': 'ergora-training-cycle/fixed',
            'task_queue': 'ergora-training-cycle-v1', 'actor_id': 'unix:1000:reviewer'}}
plan = {'project': project, 'definition': {'budget': {'wall_seconds': 12, 'cleanup_seconds': 3}}}
ready = {'existing': True}
clock = {'remaining': 5.0, 'authorization_reads': 0}
records = {directory / 'authorization.json': json.dumps(auth).encode()}

class Database:
    def execute(self, sql):
        assert sql == 'BEGIN IMMEDIATE'

class State:
    root = root
    @contextmanager
    def connect(self):
        yield Database()
    def project(self, project_id):
        assert project_id == 'demo'
        return project

@contextmanager
def permit(self, *, shared):
    yield

def raw(path):
    if path == directory / 'authorization.json':
        clock['authorization_reads'] += 1
        if clock['authorization_reads'] == 2:
            clock['remaining'] = -1.0
    if path not in records:
        raise FileNotFoundError(path)
    return records[path]

def save(path, value):
    records[path] = json.dumps(value).encode()

def status(state, project_id, cycle_id, *, authorization_sha256=None):
    return cycles._status(state, plan, auth, ready)

with patch.object(cycles, 'status', status), patch.object(cycles, '_record', save), \
     patch.object(protocol, 'read_raw', raw), patch.object(protocol.CycleAdmission, '_locked', permit), \
     patch.object(cycles.budget_clock, 'remaining', lambda *args: clock['remaining']):
    result = cycles.prepare_controller(State(), 'demo', 'controller', auth['sha256'], 1)
    after = cycles._status(State(), plan, auth, ready)
    print(json.dumps({'authorization_reads': clock['authorization_reads'],
                      'returned_status': result['cycle']['status'],
                      'returned_work_remaining_seconds': result['cycle']['work_remaining_seconds'],
                      'actual_final_clock_status': after['status'],
                      'actual_final_work_remaining_seconds': after['work_remaining_seconds']}, sort_keys=True))
```
