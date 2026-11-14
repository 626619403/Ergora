# G1a：不可变记忆复盘模板补丁

固定基线 `593da960f9eb4039518cfae9119ddafc1f7a847b`，分支 `refactor/architecture-foundations`，承接[G1交接计划](2026-11-14-integrated-handoff.md)。立项时前继F9d1已普通固定发布，其自己的CI和原发布补核在途，因此本片先本地工作；现其八job／30必要步骤和原reviewer终态两轴均已通过，前继精确交付闭合后才推送本片。

## 变更合同

原1.0.0 author／reviewer首行各有一个尾空格。保留所有已发布定义及其材料完整字节，新增相同Agent ID的1.0.1包，各仅删除该一个空格；新增同ID的1.0.1 root，精确引用两新Agent。root的其他材料、权限、限制、边、后端和输出协议保持。沿原preset注册，`memory-retrospective`选择新根并导入旧／新依赖，28个preset不新增别名。不修改Python、状态schema、运行时、测试或CI。

已有1.0.0定义、manifest与已准备输入保持原样，不能借新目录改变旧身份或静默迁移在途执行。新版本只影响下一次明确安装／选择；保留用户原来的后端选择和显式采用。

## 可验收节点

- [x] 记录原七份文件及原catalog，生成新Agent／root并由原owner计算摘要，完整差异仅预期内容。
- [x] 非editable wheel核源／包／安装与两RECORD、283参考；运行原preset／memory suites，不为机械空白变化增加产品测试。
- [x] 实际CLI创建旧库／旧manifest／旧叶输入，安装新preset；旧文件和原输入逐字保持、新根可编译、两个新叶完整继承原根Skill和上下文。
- [x] Ergora原structure-review完整输入；新fresh-context需求／维护性两轴，处理实证finding并更新进度。
- [ ] 前继自己的CI和原reviewer闭合后普通固定发布、完整Ref、本片自己的必要CI及原reviewer补核。

本地原件在`.ergora/checks/memory-preset-patch/`。该片不验模型生成、训练、记忆采用／恢复算法或Windows本机运行；原行为未变化的部分不无理由重复完整旅程。后继G1b沿现有安装器补首次安装、日常升级与旧项目状态回退。

当前最终本地两轴approve／开放0／0，416固定引用直接全核；前继自己的CI43585798832及原reviewer终态两轴现已闭合，普通固定发布及本片自己的CI待。
