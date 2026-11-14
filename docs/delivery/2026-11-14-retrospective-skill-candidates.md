# F10c2a：Skill复盘候选交付

日期：2026-11-14；基线`396e9d175cbbcd120dac29b45a2665002984a53b`。[合同](../plans/2026-11-14-retrospective-skill-candidates.md)。已盘点原owner并固定Skill先行范围，产品与验收待。

F10c1已普通发布396e9d1，原独立固定补核／自己的CI待。本片先本地推进，不借此前CI证明自身成功。复盘准备／检查不触及活动head或新增权威；候选导入／评价／采用与其他目标类型另验。

已实现原prepare／离线check、26项catalog中的新retrospective preset及共享祖先Skill；标准Skill元数据解析和目录manifest身份留在原owner复用，未复制parser或执行生命周期。首定向fixture漏建独立Git根，6 setup errors／0.66秒，产品行为未执行；已仅修fixture初始化并另起r2。

r2定向6失败／3.99秒，产品新模块request schema字面量漏闭合导致SyntaxError；已展开字典改善可读性并静态解析后另起r3，保留失败，未宣称行为通过。

r3定向 **6通过／6.13秒**（最终安装另验）；完整资料／源丢失后的离线检查、来源或基线或引用误绑／越界路径无部分CLI输出、当前head冲突与null候选已沿原suite覆盖。其后补Frozen evidence内部规范SHA核对，最终包将包含该门禁；尚未最终安装／实际模型调用／独立审查。

独立初审确认两个Medium：R1原合法CRLF在内联元数据解析被拒；R2文件／目录冲突及大小写目录拼写会给出不可落盘的目录身份。已局部修parse_metadata的解析换行（冻结原文件字节不改）及完整文件集的便携前缀检查。首修3case通过／3.22秒；独立指出仍漏目录前缀大小写，补排序邻接的共同folded前缀原拼写核对，四定向case **4通过／4.24秒**；无trie／逐层join或新格式，待独立复核。

修前r1 wheel `c7432f290d424c0553bd042d0ba69aa5b7c4e8e843c741bf3ab7d0afba83150e`，586产品／两RECORD594／599／283核过；原八suite **286通过／7跳过／213.21秒**，monitor214.708秒。真实原CLI八步Codex作者21.003秒→Claude审查122.529秒，两run成功且完整prompt=实际stdin、原祖先与完整前驱均保持；作者合理返回candidate:null，审查approve，只证明这条只读无改进旅程，不冒称已生成或采用正候选。此包／旅程早于R1/R2修正，最终r2另验。

R1／R2新四case在原修前安装件实红 **4失败／4.06秒**；原源码最终四case **4通过／4.24秒**，独立进一步核六个纯函数案例关闭源码finding。修后r2 wheel为`f5426384529d887bf115e51f8cdae886c933eca6eee1ee1c4fbbc1556710793e`，586产品／两RECORD594／599／283已核，原八suite／实际作者与Claude审查／自身原结构模板均在途，最终独立补核待。

r2原八suite **290通过／7跳过／215.12秒**（monitor216.710秒）；真实八CLI再次通过，Codex作者24.369秒→Claude审查72.901秒，仍为合理null候选的完整只读旅程。自身原结构模板以真实Claude审查116.934秒返回request-changes；独立对照完整相邻owner后确认其M2为新R3：可准入的560,000B JSON参考资料，其完整等量候选在原response嵌套后超过原1 MiB结果限制。已将基线与结果改为本用例的1 MiB／8 MiB分别有界读取，补完整大候选回归，并让七个拒绝实例核自身stderr原因；最终r3包及复审另验。M1关于自有reviewer-role提案叶不可达的判断不成立；CLI／手册已澄清preset的文字review走原composition。保留末尾原Skill完整get以检出新增／删除／执行位变化；不为一行固定canonical编码或fixture新建公共抽象。原审查回复及独立处置均保留。

R3新大候选在原未改r2安装件实红 **1失败／1.48秒**，错误明确为原1 MiB结果门禁；当前源码完整复盘用例 **11通过／11.27秒**。未截断任何文件，最终r3非editable安装与实际调用另验。

r3包已构建并核586产品／两RECORD594／599／283，wheel `0db77316516597ee4b1fd12b544d493146a38d559b35138da65b0ec400cd52a3`，尚未运行最终suite／模型。独立复核发现R4为测试自身的Windows文本换行假设：write_text可写CRLF而read_text会正规化，不能与产品冻结的原字节比较。已将fixture的LF样本显式写bytes、完整性断言比原bytes，CRLF专例仍另验原CRLF；产品冻结合同不改。保留r3初始安装身份，最终r4快照另起，避免改写旧证据。

最终r4 wheel `377cee68ab99b94136d32ca38b07625d3d397d9e98d20a981a72b2e5881cc8bc`：586产品／两RECORD594／599／283已核，安装八suite **291通过／7平台跳过／219.22秒**（monitor220.744秒）。实际八CLI均按预期退出，Codex作者23.263秒、Claude审查42.110秒成功；仍为null候选／approve的只读旅程，完整prompt＝stdin、全部祖先资料及完整checked前驱保持，Skill版本／head／历史、原包和Git未改，错结果SHA无部分输出且离线不创建State。原结构模板最终Claude复审在途，独立最终证据另核。

原结构模板r4 Claude复审23完整文件303,397B，完整prompt／实际stdin一致，原run `a8c8749c37084bb7b838a239d89ed374` 在360.552秒终态timed_out、无review结果；失败原件保留。按用户授权对同一精确input另建Codex调用，明确fallback reason，不重写原run，也不当作异后端审查通过；当前等待新调用终态。

同一原input的Codex结构复审45.359秒成功、decision approve；23完整文件303,397B、prompt SHA `d2016ca8b22c18e160b83a19e0d2b9d0e262094cc35e37faac0bda36e0e68f07`、input digest `10b4e93a376dff1bb0047540f4e1ee4bae690dec13de09fc5aa642d5356cd0df`与Claude超时原件相同。原reply SHA `56649e900dba67998a838b061e33d0bd7838bd5c273058280979a7d8d4922c38`；没有用自身静态approve替代独立最终验收。全部本片harness／调用已终态，可访问/proc中无cwd归本片的在途进程（10个进程不可读，范围据实保留），未启动服务／端口／浏览器。公开[最终证据](evidence/2026-11-14-retrospective-skill-candidates.json)含236原引用、完整产品／快照／wheel／安装及两RECORD／283身份，最终fresh-context补核待，尚未发布。

原fresh-context reviewer最终本地两轴 **approve／开放0／0**，R1–R4全部关闭；直接核最终r4产品／快照／wheel／安装、两RECORD／283、291／7、实际双后端和236原引用。保持真实null候选与自身Claude超时／同input Codex回退边界，不继承为效果或采用成功。现在普通提交／推送本分支，固定发布与自己的CI随后另核，不合main。

已普通发布 `a60a8f68513a46ef7e6c18add0832f8bcee3eccc`，28个Git blob与完整远端Ref已逐字核同。固定提交的236原引用保持，工作树另补四份静态／commit／push／Ref回执共240；原fixed发布补核和自己的CI待，未合main。

原fresh-context固定发布补核两轴approve／开放0／0：28blob、15源码／测试与固定236／发布后240引用及完整Ref分别一致。自己的CI43551217945已从官方列表及完整SHA绑定到此候选，八job在途；CI原件另列，未借前片CI。

自己的固定候选a60a8f6的CI43551217945最终官方run HTML r4为Success，八job／30必要步骤全部success且完成，Windows r3及其余七job r2的完整SHA日志路径已离线核。新增CI引用58份，与固定236／发布后240原引用分列；原独立reviewer正在作同片终核，尚未以作者观察代替独立结论。

原fresh-context reviewer已追加自己的CI终核：8job／30必要步骤、完整SHA及时间、58独立CI引用和固定236／发布后240全部核对，approve／开放0／0。F10c2a精确交付闭合，R1–R4仍全部关闭；后续片保持独立身份。
