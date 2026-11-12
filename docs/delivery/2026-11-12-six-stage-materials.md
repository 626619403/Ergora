# B1 完整材料输入交付记录

基线 `210f58d46c3332f4d192ee8cb13e8c149dd2173f`，产品基线 `5ab6d350024de8515487d0bedb3b950be60ac867`。范围及验收见[B1计划](../plans/2026-11-12-six-stage-materials.md)。B1实现、受影响源码／隔离安装行为验证、实际自身模板及完整36文件fresh-context独立两轴同片补核均通过，本地出口完成；普通交付／该提交CI待做。B2 总预算、C 单实例调用、D 完整生命周期均待做。

## 开工核对

已核总计划、D1设计、既有交付及 Git：分支 `refactor/architecture-foundations`，开工工作树干净，HEAD 与已核远端为上述文档基线。冻结参考文件保持原件。

源码确认 inventory/plan 尚不消费完整结构材料，旧依赖读取存在 60k 字符截断；旧 WorkDelivery 要求 work/review 覆盖全部叶，不能直接把准备叶塞入原投影。新片以显式新版本解决，保留旧合同。现有 composition 原生夹具能覆盖原 stage 所有者，但手工提交活动不是完整 CLI／Temporal 生命周期；后者另用隔离旅程验收。

已委派只读验证路径调查，输出限定私有持久目录；调查不是独立实现审查。产品变更、测试、安装、模型审查与独立评审尚未完成。

## B1.1／B1.2 实现与首轮证据

已增加definition4／input8、显式两个准备叶和repository_paths、全部Agent覆盖、原创建／恢复及版本队列。v4可选沿用来源快照。前两阶段使用原Executor／stage_driver／run_input；原writer、unit、批准及检查保持。Git对象批量完整读取由原Executor共享，plan核原inventory请求、receipt、claim、实际选择与调用后交付全部声明产物／可信baseline。新输入的text-only拒绝未内联附件，task-mcp成功响应附实际范围，原阶段接受前核连续覆盖。

新增三个静态示例包：多职能development-preparer、preparation-guide、prepared-delivery；旧包不改。示例不是新的内置preset，不宣称原生嵌套可执行。两手册、合同表及架构入口补当前使用方式与限制；页面向导仍生成v6。

开发环境已有Python3.11及editable安装；未以其冒称非editable安装验收。原有受影响129项通过（80.03秒），架构／工作／task-mcp原70项通过（161.92秒）；这两组先于本片后续小幅共同行为整理，不覆盖最终候选。新静态／创建7项首轮通过。新增完整组件首轮4失败／8通过：MCP中间件误以为成功dict返回有structuredContent，实际固定SDK是content文本；已改用真实返回正文，保留首轮日志。新13项复核通过（85.09秒），含完整原阶段进程、75k字符inventory尾部、超过64KiB附件连续读取、容量整份拒绝、未读附件拒绝、原产物篡改拒绝、可选完整工单来源及有重叠但缺字节的真实MCP响应。

上述新旅程经过原preview/create、Executor进程、stage_driver、固定CLI协议及收据，非真实模型／Temporal服务或完整任务CLI生命周期。随后整理共用member冻结、选中依赖准入及首inventory context所有者，最终受影响检查、隔离wheel安装／283原件、自身真实审查及fresh-context独立评审仍在进行。私有原件位于持久`six-stage-materials`检查目录；旧失败不覆盖为成功。

## B1.3 最终候选的行为与安装身份

共同行为整理后的受影响九组源码suite共295项通过，pytest报告338.10秒、驱动墙钟338.87秒。新Python3.12非editable wheel的完整材料／task-mcp／架构三组58项通过，pytest报告200.58秒、驱动202.03秒。两者不是全量回归或真实模型／Temporal验收，不把早期129／70项结果扩为最终全量。

wheel共458文件，其中453件产品文件逐字等于当前源码和隔离安装；wheel及安装的两个RECORD逐项核hash／size，283冻结参考文件按原manifest核身份。wheel SHA-256为`dffc1232c60a4a0a883420f4f0bc4f01bf15fb6ac9e940d13443029f4f246c21`。源码和安装路径之外的真实服务可用性不由这些检查证明。

## B1.4 实际模板与独立审查进行中

34份完整公开候选已冻结，独立协调者启动fresh-context Spec与Standards两轴，分别读取原要求、固定基线、tracked差异、新文件及实际证据；当前尚无完整判词。实际自身审查使用隔离wheel随包结构模板，仅追加冻结候选材料Skill及限额修订。首选Claude Code调用8.01秒失败，原API返回400（system content为空的网关校验），没有审查结果；八个采样所属进程无存活。该失败不是代码审查意见，也不是双后端通过。

按用户已有授权回退Codex，继续使用相同34份冻结候选及明确的新运行身份。实际输入、manifest、prompt、MCP完整读取与原结果须在返回后核准；当前不提前记approve、独立评审通过或本地出口完成。后续最终文档会交原独立评审同片复核，再普通提交／推送并核该提交必要CI。

## 实际模板返回与原34文件独立判词

上述Codex调用已完成：`gpt-6.1-sol`／high，377.86秒succeeded／approve，CLI退出0。没有代码修改意见。随包结构模板本身保持，仅追加本片证据Skill、版本1.0.121及材料限额。34份完整候选形成629,091字节附件，全部五scope通过实际原stream重建连续UTF-8读取至`next_offset:null`；manifest→prepared→实际input→prompt／scope→原结果身份一致，没有失败list／read调用。四个采样所属进程无存活。模型只读所提供源码／规格／证据叙述，没有自行运行测试、安装或网络检查；冻结后的状态文档不借它的判词。公开[身份与读取投影](evidence/2026-11-12-six-stage-materials-self-review.json)保留原文件摘要、范围、结果和原生用量计数，不将缓存重复计为额外输入或推导账单。

新的fresh-context协调者及两个子轴[完成原34文件审查](2026-11-12-six-stage-materials-review.md)：Spec finding0，Standards硬违规0／判断性smell0，产品、测试与示例没有待修finding。其另从实际原件核源码295／安装58、453产品与两RECORD／283身份；不只读取作者passed字段。此判词不替代最终文档补核、精确Git／远端与必要CI。

当前34文件静态初核212个本地链接目标／六个已加载秘密值issue0，JSON及diff空白通过。范围不含远端链接、Markdown锚点或渲染；最后公开清单增加独立报告与上述读取投影后还需补核，未提前称精确交付完成。

原独立协调者已同片核完整36文件、最新四份状态文档及实际模型原件，开放Spec／Standards finding0／0，本地出口通过。从原stream独立重建五scope（含base64边界重读），34份附件内容逐SHA回原冻结副本；公开投影逐字段与原件核对，Claude失败／无结果及两轮进程采样保持。D1总设计已明确哪些是历史源码事实、哪些是B1当前实现，未把过期注册表当当前状态。最终文档状态更新不构成新产品候选，不重复已过测试或模型；普通提交／推送与该提交必要CI继续。
