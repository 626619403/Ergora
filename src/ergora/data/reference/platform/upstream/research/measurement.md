# 计量、端到端 profile、实验设计与正确性分级

核验日：2026-10-26。已读本地《从WAM优化实践到多Agent协作：工作流程与经验.md》及 wam-report-reading.txt 的计量、JVP、通信、FP8、GAS 与组合记录。没有打开其中的私有外链，没有复现 WAM 结果。以下流程、数据契约与默认统计门槛是本方案的工程建议；官方文档和论文用于核实工具语义与适用范围。

## 1. 给计量方向 agent 的职责

计量 agent 不以“跑出最高 MFU”为目标。它维护可比较的工作负载、识别决定完整训练进度的关键路径、给候选提供可重放输入，并交付独立性能证据。方向 agent 可以申请实验，不能自行修改验收阈值、宣布质量等价或替换共享基线。

输入：基线 commit/镜像、最终配置、启动命令、固定 checkpoint 与 optimizer/RNG/sampler 状态、数据清单、硬件拓扑、允许变更分类、性能与质量约束。

输出：`measurement_contract.json`、`run_manifest.json`、每 rank 原始完成窗口、`completion_windows.jsonl`、样本 replay/hash、profile 及采集配置、`bottleneck.json`、配对比较输入/输出、正确性分级结果、失败/停止原因。主报告必须能回到这些原始文件。

## 2. 先定义“完成了什么”，再定义 step

| 字段 | 定义与规则 |
|---|---|
| `source_samples` | 真正消费的源样本数。WAM 可定义为源视频窗口；同一窗口的多视角、多个训练目标、N4 候选不能重复算成新样本。相同样本被有意再次抽样，是另一次消费，并保留 occurrence ID。 |
| `source_samples_by_dataset` | Robot、Ego 等各自计数；不能增加便宜数据占比后只展示更大的总吞吐。模型并行复制不重复计数，只由数据分片的指定 owner 上报。 |
| `microbatch` | 一次物理输入批；记录每 DP replica 的批大小。不要把 TP/PP rank 数当成额外数据并行数。 |
| `target_backward` | 一次目标的反传/累积事件。多目标共享同一源输入时，这个计数通常大于源批计数。 |
| `logical_round` | 一轮业务训练工作，例如同一 Robot/Ego 输入驱动完整 cotrain 工作。它是项目定义，必须写清包括哪些目标。 |
| `optimizer_update` | 某个 optimizer 真正修改状态/参数的更新；分别记录 attempted、completed、skipped。多个 optimizer 分别计数。 |
| `GAS` | 框架以何种事件累积多少次才更新。常见单目标训练与 WAM“目标步”口径不能直接互换。必须从实际调用循环确认。 |

WAM 文档中“一轮包含四个目标，GAS4→16 变成四轮更新一次”是项目特定映射；不是所有框架的 GAS16 都等于四个 batch。这个变化增加有效样本/更新、改变 Adam moments、权重衰减和 scheduler 的作用频率，应进入算法/质量变更轨道。不能将每轮摊销时间标成真实更新延迟。

常规单目标、均匀 DP 场景才可使用 `effective_batch = microbatch_per_replica × DP_size × accumulation_microbatches`。多目标 WAM 应额外记录每种 loss 的权重、归一化分母与样本重用关系，不能用一个乘法掩盖区别。[S9]

### 时间与吞吐

对相同测量边界的窗口，记录各参与 rank 的完整 elapsed，取 `T = max_r(elapsed_r)`；吞吐为 `sum_unique_data_owners(source_samples_r) / T`。每 GPU 吞吐再除实际参与 GPU 数，明确是否包含只做模型并行的 GPU。均匀批量时可同时报告 `T/逻辑轮数` 与 `T/真实更新数`，两者命名不同。

正式性能 run 使用无 profiler 的完整窗口。窗口起点前排空必要 GPU 工作并做一次参与组同步，窗口结束确认该窗口所有必须完成的设备/通信工作；最终 MAX 归约在本地计时结束后执行。窗口内部保留生产异步调度，禁止每次记录额外 `cuda.synchronize()` 或 barrier。初始化、编译、预热、稳态分别记录；另做包含 checkpoint、数据切换和缓存变化的长程运行。

这里 max-local-elapsed 需要共同逻辑起点。它不是跨主机原始时间戳直接相减，也不是严格同步时钟的替代。测量边界的额外开销和起点偏差需报告；窗口长度加倍后估计应稳定。连续更新的局部间隔可用于诊断，但 `sum_u(max_r Δt[r,u])` 一般不等于 `max_r(sum_u Δt[r,u])`；整体吞吐必须由完整窗口总量计算。

CUDA 是异步提交；Python 调用返回不表示 GPU 完成。CUDA event 也只覆盖其依赖链，多 stream 结束事件必须等待相关生产者；默认 stream 上一个 event 不能自动证明所有旁路流完成。[S1]

### P99 与吞吐下尾

- `update_latency_p99` 是真实更新完成间隔的上尾，需写清是否用了每 rank 局部间隔的最大值，或基于已对齐的全局完成标记。不要隐藏这个区别。
- 吞吐的差尾是 P1/P5 等下尾，不是 P99 吞吐；后者反映快窗口。仅在固定工作量且同一分布/分位数定义下，才能用 `work/P99(time)` 对应下尾速度。真实实验直接计算固定窗口吞吐的下尾更稳妥。
- 均值、P50、P95、P99、窗口大小、观测数量、运行次数、异常窗口原样保留。短短 20 次更新或 9 个相关窗口不能认证 P99。以 99 分位为例，2,000 个观测也仅有约 20 个名义上尾观测；这是采样规划提示，仍需考虑相关性、独立 run 和置信区间，绝非充分样本的定理。
- 本附带比较器只接收完整 run 汇总，永远返回 `p99_assessment.certified=false`。批准尾延迟需要另一个读取时间序列、分块处理相关性和异常分类的验收器。

### MFU 分子与分母

`MFU = F_useful_global / (T × sum_devices(P_peak_for_reference_precision))`。

PaLM 提出的 MFU 将模型必需前向/反向算量与重算开销分开，不能把额外重复计算算进分子来提高“效率”。WAM 不能照搬 decoder 的 `6N × tokens`：冻结编码只有前向，训练目标、实际候选数、JVP、attention、卷积、参数共享和真实调用次数都要列入 FLOPs ledger；重算、打包和无用重复另外列为实现开销。ledger 改版后必须同时重算旧配置，或明确两代结果不可直接比较。[S5]

H200 SXM 官方表的 BF16 1979、FP8 3958 TFLOP/s 带 sparsity 脚注；稠密口径约为其一半，才对应文档采用的 989.5/1979。NVL、功率和实际频率不能静默共用同一峰值。BF16 等效 MFU 只是统一参照，不能解释为 FP8 设备的实际百分比；它甚至可以超过 100%。`sum_p(F_p/P_p)/(N*T)` 可作为声明清楚的精度加权计算时间指数，但它不是普适硬件占用率，也没有反映带宽、通信与混合资源并发的完整理论下界。[S6]

## 3. Profile 顺序：先全局因果链，再做局部解释

1. **无采集基线**：记录足够长的完成窗口，确认数据计数、更新计数、OOM/skip、时钟、功耗、共享资源和 warm-up 状态；基线不稳定就先诊断，不发“优化已成功”结论。
2. **短窗口 Nsight Systems**：冷启动与稳态分开采集，NVTX 标记 dataloader wait、CPU decode/transform、H2D、冻结编码、各目标 forward/backward/JVP、collective、optimizer、checkpoint。看 CPU/GPU/通信的依赖关系与空档，不把 CPU range 宽度当 GPU 算子时间，不相加重叠阶段。[S2]
3. **定位可缩短的关键路径**：记录暴露通信尾部、等待哪一 rank、host 提交间隙、数据饥饿、实际串行依赖。输出一个可证伪假设：例如“减少 X 阶段的 Y 次拷贝应使完整更新减少约 Z ms；若 Z 被其他阶段覆盖则停止”。潜在收益是有依据的范围，不是把所有 kernel 时间相加。
4. **选择性 Nsight Compute**：只对关键 kernel、真实 shape/stride/layout 做必要 section 采集。记录 replay、cache、clock 配置；默认 replay/序列化可能破坏真实重叠，缓存刷新也会改变测量条件。不得拿 NCU 采集过程当端到端吞吐。[S3]
5. **独立重测**：关闭 profiler，以当前编译/库路径作基线，计入布局变换、量化、分配及 wrapper，先组件、后完整训练。
6. **合入后重新诊断**：旧热点占比与方向优先级会改变。组合性能下降时做小组拆分/消融，不把单项收益相加。

`bottleneck.json` 建议至少包含：baseline hash、capture hash、rank、阶段、critical-path evidence、受影响调用次数、估计可回收时间范围、所需 correctness level、微测是否保留真实 layout/derivatives、反证条件、额外显存与复杂度预算。

### 命令模板（需映射项目实际入口，不声称已跑 GPU）

```bash
# 先检查远端安装工具版本与支持的选项；不需 root 改频率。
nsys --version
ncu --version
ncu --list-sections

# train_entry.py 是项目适配入口；--config 也由项目实现。
# 入口在所选窗口调用 torch.cuda.profiler.start()/stop()。
nsys profile --trace=cuda,nvtx,osrt --sample=none --cpuctxsw=none \
  --capture-range=cudaProfilerApi --capture-range-end=stop \
  --output=artifacts/timeline \
  torchrun --standalone --nproc_per_node=8 train_entry.py --config experiment.json

# 单个复现 kernel；正则名须来自上一步实际 trace。
# 应用重放要求每次选择相同 kernel/输入路径；不要原样用于随机分布式全训。
ncu --set=basic --kernel-name='regex:REPLACE_WITH_REAL_KERNEL' \
  --launch-count=1 --replay-mode=application --cache-control=none \
  --export=artifacts/hotspot python3 kernel_probe.py --case case.json

# 无采集器的正式对照；各臂由 runner 恢复相同状态并换序执行。
torchrun --standalone --nproc_per_node=8 train_entry.py --config experiment.json
```

多节点应由集群 launcher 在各节点启动 nsys，并用 node/rank/run ID 命名，不能用本机 `--standalone` 命令假装跨节点采集。kernel 的 clock/cache 选择是诊断配置；它们不代表正式验收应锁同样的频率。保持两臂设备政策一致即可。

## 4. 实验设计：筛选、确认与长程验收分开

### 同一比较必须匹配的内容

同硬件组/拓扑/资源独占政策、最终输入形状与数据混合、同数据 replay 与 augmentation/noise/mask、相同初始完整训练状态、编译缓存政策、预热准则、测量边界、samples/updates定义。相同 seed 不保证相同实际输入：worker 调度和数据读取改动会改变 RNG 消费，需保存 sample occurrence ID、字幕/文本 token hash、增强参数、真实张量摘要或可重放输入。

`workload_fingerprint` 对这些不可改语义做 hash；`config_hash` 仍分别记录两臂实际配置。精度/模型/GAS 改动可以作为已声明处理变量，但必须标为 approximate 或 algorithmic，不能用相同 workload 标签暗示数值等价。

### 配对运行

- 探索可用一对短 run 找明显机制；不能由此生成确定收益或 P99 承诺。
- 确认集提前登记预算与顺序。每一个 pair 是从同 checkpoint、同 replay 重启的一次 baseline 和 candidate；按随机化/平衡的 AB、BA 顺序，在邻近资源条件下运行，独立重复。不要在同一不断训练的状态上交替实现，却称为相同初始状态。
- 同一训练 run 内多个连续窗口通常相关；先汇总成一个 run，或交给明确分层/分块统计方法。不能把 20 步当 20 个独立重复。不能用一个 baseline run 与八个 candidate 配对，伪造八个独立 pair。
- 温度/时钟/缓存、存储抖动、网络干扰应记录。异常值不因不利而删除；预先定义污染规则，污染整个 pair 则重跑并保留原始证据。基线本身的波动应参与不确定性评估。
- 候选很多时，用独立确认集消除“挑中最快噪声”的偏差。普通固定样本 bootstrap CI 不支持不断偷看、直到显著为止；若必须连续决策，需要另行设计顺序方法与多重比较控制。

### 判定与停止

计量产出只分 `PASS`（性能证据满足筛选门槛）、`FAIL`（已有证据不满足）、`INCONCLUSIVE`（证据不足）。晋级还要独立通过对应正确性级别、显存/尾部/维护性条件，由 owner 完成。数值失败、数据变动未解释、实际路径未启用、出现非预期跳过更新时直接停止晋级。

绝对门槛与相对门槛都可以配置，例如“每固定全局逻辑轮至少省 10ms”与“吞吐至少 +0.5%”。二者是 AND 还是 OR 必须显式写。10ms 是项目的成本/噪声选择，不是通用定律。达到实验预算仍无法区分就记为不确定/暂存，不自动接受。合并多个候选后对实际组合重跑；局部胜出而端到端无收益时停止或转到容量价值评估。

## 5. 正确性级别与证据

| 级别 | 验收对象 | 不足以支持什么 |
|---|---|---|
| C0 语义/数据 | 样本及 augmentation/RNG、mask、loss 权重/归一化、候选选择、缓存键与参数版本、GAS/更新映射 | 输入不一致的对照不能证明保真加速。 |
| C1 实际输出 | 真实 shape/stride/dtype、零/极值/边界；max abs、相对 L2/NRMSE、尾部、nonfinite、低精度饱和/下溢；预登记阈值 | 一次均值误差或有限值不能代表任务质量。数值非逐位一致本身也不等于错误。[S8] |
| C2 所需导数 | dX/dW，JVP 的 primal/tangent；合适小用例 FP64 gradcheck，实际低精度 kernel 独立差分；仅需要高阶导时做更高阶检查 | `gradcheck` 默认不查 forward AD；必须显式 `check_forward_ad=True`。双精度数学路径不能替代真实 kernel。[S7] |
| C3 更新与恢复 | 多次真实 optimizer 更新，参数 delta、moments、计数、scaler/scheduler、梯度裁剪、跨 rank 一致、恢复后下一更新 | AMP 可跳过更新，调用 step 不等于完成更新。不是所有 BF16/FP8 都用 GradScaler，应记录实际路径。[S9] |
| C4 长程质量 | 预登记验证指标/容忍边界，代表任务/种子，固定数据预算及 time-to-quality，失败/未达标 run 保留 | finite、20 次更新和短 loss 对齐不能证明收敛；GAS、8bit optimizer、FP8/fast accumulation、结构变化必须单独评估。[S10] |

默认建议：保持数学任务的调度/缓存/编译优化需 C0–C3 和代表性回归；任何会改变数值轨迹的方案先受控试验，再按风险完成 C4 才声称质量不劣。C4 质量由领域 owner 定义，不使用统一 NRMSE 阈值代替。对含候选选择的 WAM，连续值误差还需检查离散排序/选中候选变化及其下游效应。

## 6. 比较器接口：`compare_runs.py`

这是纯 Python 标准库程序，不依赖 GPU。接口：

```bash
python3 compare_runs.py --self-test
python3 compare_runs.py --example > synthetic-comparison.json
python3 compare_runs.py synthetic-comparison.json --output synthetic-result.json
```

`--example` 生成的数字明确是合成测试，不能加入真实实验榜单。实际集成固定使用 `python3 compare_runs.py INPUT.json --output OUTPUT.json`。成功计算的退出码是 0，不论 PASS/FAIL/INCONCLUSIVE；调用方必须读 `status`。输入/文件错误退出 2。自测失败退出 1。

### 输入 schema 与 manifest 责任

```json
{
  "schema_version": 1,
  "experiment_id": "exp-unique-id",
  "comparison_id": "confirm-001",
  "manifest_sha256": "64个小写十六进制字符：实验manifest原字节hash",
  "workload_fingerprint": "不可变工作负载契约的hash或ID",
  "independent_unit": "paired_run",
  "normalization_source_samples": 128,
  "statistics": {"min_pairs": 8, "bootstrap_resamples": 10000, "confidence": 0.95, "seed": 20261026},
  "thresholds": {
    "min_saved_seconds_at_normalization": 0.010,
    "min_speedup_percent": 0.5,
    "mode": "any"
  },
  "pairs": [{
    "pair_id": "pair-001", "order": "AB",
    "baseline": {
      "run_id": "run-b001", "code_sha": "完整40位Git SHA或64位源码bundle SHA256",
      "matched_input_fingerprint": "输入replay清单原字节SHA256，64位小写十六进制",
      "environment_fingerprint": "不含处理变量的环境契约SHA256，64位小写十六进制",
      "initial_checkpoint_sha256": "完整初始状态或其manifest的SHA256，64位小写十六进制",
      "measurement_mode": "unprofiled", "aggregation": "global_completion_window",
      "elapsed_seconds": 100.0, "source_samples": 4096
    },
    "candidate": {
      "run_id": "run-c001", "code_sha": "完整40位Git SHA或64位源码bundle SHA256",
      "matched_input_fingerprint": "必须与此pair的baseline相同",
      "environment_fingerprint": "必须与此pair的baseline相同",
      "initial_checkpoint_sha256": "必须与此pair的baseline相同",
      "measurement_mode": "unprofiled", "aggregation": "global_completion_window",
      "elapsed_seconds": 97.0, "source_samples": 4096
    }
  }]
}
```

这段是带字符串占位符的 schema 示例，不能直接运行；`--example` 才输出合法输入。绝对节省单位为处理 `normalization_source_samples` 个全局源样本的秒数。若 128 个源窗口就是一个固定逻辑轮，则 `estimated_saving_ms` 表示该轮节省毫秒；如果改变工作量/目标映射，不能继续把它解释成同一逻辑轮。

两臂同 pair 必须有相同 source_samples，且 `matched_input_fingerprint`、`environment_fingerprint`、`initial_checkpoint_sha256` 三个64位SHA256分别一致；不同 pair 的数量可以不同，结果用总样本/总耗时形成 workload-weighted 速率。每臂跨 pair 的 code hash 固定；run_id 不可复用；每对顺序必须为 AB/BA，达到样本门槛后仍只出现一种顺序则返回 INCONCLUSIVE。默认 8 个独立 pair 是保守起点策略，非充分样本定理；可配置但程序最低接受 4。低于配置数量时只输出描述结果、不出 CI。

三个指纹必须能沿 manifest 找到对应内容：输入指纹包括样本序列、实际token/augmentation/mask/noise及shape；环境契约固定硬件组/拓扑/依赖/资源政策，显式处理变量另存，不能偷换环境；初始状态指纹应覆盖模型、optimizer、scheduler/scaler、RNG与sampler状态（可hash它们的完整manifest）。仅有模型权重不能称为完整训练状态。程序核对一致性和格式，不宣称验证文件存在或内容真实。

比较器不读取 manifest 本体，也不能证明调用方声明独立、无 profiler、数据匹配就是真实；这些由 runner/独立验收器核验，manifest 应保存：每臂最终配置/hash、容器/依赖/driver/CUDA/PyTorch版本、硬件GPU UUID/拓扑/功率政策、完整数据 replay/shape/dtype、初始 checkpoint/optimizer/RNG/sampler hash、每 rank 时间和计数、窗口边界、warm-up/compile 状态、原始输出文件hash、异常/失败、真实更新计数、允许变更类别、C0–C4要求、资源租约与实验顺序。代码有未提交改动时用源码 bundle hash，不得只记 HEAD。

### 统计算法与输出

一次 bootstrap 抽取完整 pair 索引，使其 baseline/candidate 始终一起重采样；不抽单步、不拆相关窗口。对重采样集合计算：

`speedup = sum(baseline_seconds)/sum(candidate_seconds)`；`time_reduction = 1 - sum(candidate_seconds)/sum(baseline_seconds)`；`saved_seconds_at_normalization = normalization_samples × sum(baseline_seconds-candidate_seconds)/sum(source_samples)`。

输出 percentile paired-bootstrap 区间，并用区间下界严格超过配置的实际门槛作为性能 PASS；区间上界也不能满足门槛为 FAIL；否则 INCONCLUSIVE。abs/relative 都启用时 `thresholds.mode` 必须显式为 `all`（AND）或 `any`（OR）。设置某门槛为 null 可禁用该门槛。两个同时禁用会拒绝输入。方法是便于审计的近似筛选器，不是小样本精确推断，不修正反复偷看或多候选搜索。SciPy 的 paired 模式同样使用共同索引，但本程序不依赖 SciPy，也不宣称实现它的 BCa 算法。[S4]

主要输出字段：`status`、`input_sha256`（CLI 输入原字节）、`manifest_sha256`、两臂 code hashes、`matched_pair_fingerprints`、`n_pairs`、`reason`、`normalization_source_samples`、`estimated_saving_ms`、`saving_ms_ci`、`estimated_speedup_percent`、`speedup_percent_ci`、点估计与完整 CI、逐 pair 节省、`quality_assessment=NOT_EVALUATED`、`promotion_approved=false`。`p99_assessment=INSUFFICIENT_EVIDENCE` 永远不认证尾部。

自测覆盖已知 10% 时间下降与 11.11% 吞吐提升的区别、单 pair 不确定、回退/无收益、非法非有限输入、profile 污染声明、重复 run、工作量不匹配、归一化、固定 seed、AND/OR 与运行顺序要求。真实集成仍需独立核验计数和输入真实性。

## 7. WAM 记录中不能泛化的结论

- “9/9 窗改善”“5/9 窗改善”保留作短测观察；窗口相关时不能转成独立重复的胜率/置信度。
- “超过10ms”是当时筛选策略；和测量噪声、复杂度、显存代价一起判断。
- GAS16 的每轮提速不是同训练算法的无条件纯加速；真实更新延迟和到质量所需样本必须另报。
- 200 步 loss 有限、20 次 AdamW 更新、NRMSE 1%–3% 等是不同级别证据，不能单独认证质量不劣。字幕/采样不完全相同的短程对照不应标 strict。
- 原结构与宽浅结构、不同视角/帧数/文本长度、不同数据混合的吞吐/MFU不能排成同任务纯加速榜。
- 组合中共用的最终吞吐不能归因给某个没有独立开关对照的单项；通信链提速也不等于完整更新时间同幅提速。
- 不要只展示“最优”窗口；负例、采样长度、未采集项、未测收敛都应在证据卡正文可见。

## 8. 十个一手链接与核验事实

以下链接及事实已核验；实施时固定所用版本。以下简短事实不是对全部工具能力的概括。

| ID | URL | 已核验事实、适用条件 |
|---|---|---|
| S1 | https://docs.pytorch.org/docs/2.14/notes/cuda.html | CUDA 异步，精确时间需同步或 events；非默认 stream 需显式依赖与生命周期管理。用于计时实现，不意味着每步都同步。 |
| S2 | https://docs.nvidia.com/nsight-systems/UserGuide/index.html | 支持集中采集关键窗口、NVTX、cudaProfilerApi；`capture-range-end=stop` 停采集但让应用继续。用于全局时间线；采集本身仍需考虑扰动。 |
| S3 | https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html | 指标采集可能重放/序列化 kernel；默认 replay 刷缓存；application replay + cache-control none 可保留应用缓存准备。用于局部硬件原因，不当整训吞吐。 |
| S4 | https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html | paired=True 用同一索引重采样相关数组；percentile/basic/BCa 为不同区间方法。只借鉴配对语义，不能证明输入 IID，也不能代替顺序/多重比较设计。 |
| S5 | https://arxiv.org/pdf/2204.02311 | PaLM 的 MFU 区分模型必要计算与 rematerialization；附录给 dense decoder 公式。WAM 需自己的多组件 FLOPs ledger。 |
| S6 | https://dam-cdn.nvd.orangelogic.com/AssetLink/5o2qgy5d2835ve2pm11i62kv8mphqta8.pdf | NVIDIA H200 数据表给 SXM/NVL 性能和 sparsity 脚注。分母必须匹配设备/精度/稠密政策，不混用宣传峰值。 |
| S7 | https://docs.pytorch.org/docs/2.14/generated/torch.autograd.gradcheck.gradcheck.html | gradcheck 默认不检查 forward AD，默认数值差分容差面向 double；不可微点/重叠内存需处理。实际 BF16/FP8/JVP 路径另验。 |
| S8 | https://docs.pytorch.org/docs/2.14/notes/numerical_accuracy.html | 数学等价不保证浮点逐位一致；平台、批量/切片计算、有限输入的中间溢出都影响数值。误差预算应按任务与路径制定。 |
| S9 | https://docs.pytorch.org/docs/2.14/notes/amp_examples.html | 梯度累积中 scale 保持一致，按有效batch unscale/step/update；GradScaler 可能跳过 optimizer step。只适用于实际使用AMP/scaler的路径。 |
| S10 | https://mlcommons.org/benchmarks/training/ | MLPerf Training 测指定数据/质量目标的墙钟时间，区分 Closed/Open 灵活度。借鉴time-to-quality思想，不照搬该站噪声比例、删极值或重复次数。 |
