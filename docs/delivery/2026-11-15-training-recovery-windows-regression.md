# Q4.2b2：Windows回归范围修正

日期：2026-11-15。基线`9c9ffeee517deff2ec8cd2ffe572744e3c2cd682`，同一原登记恢复产品片的小修正，不包含后继B3.1产品。

自己的Portability`43655794070`／attempt1／固定head终态failure：plan和六Linux成功，Windows应用回归失败、PowerShell5.1安装／升级成功，合计八job中七成功、30必要步骤中29成功。匿名官方check-run／annotations／job HTML／artifacts metadata均200；annotations给出唯一失败`test_original_registration_is_rechecked_in_the_selected_training_process`，`ValueError: Native training submission requires Linux; use the registered runtime in WSL2`。Windows原结果为1 failed、1176 passed、819 skipped及16 subtests passed，1253.82秒；原失败保持，不能宣布精确交付门禁通过。

该测试第一个调用是原`reference.training_submission(...,'prepare',...)`，原公开实现明确仅Linux／WSL2；测试覆盖之后在所选子进程重新核原发布来源，漏了与邻接原生准备／preflight测试相同的平台条件。最小修正只为这个原测试加`skipif(sys.platform != 'linux')`，保留完整测试体、原断言／fixture、产品权限边界和CI选择。没有新增测试、矩阵、job或产品fallback；283参考及b2最终645产品／原wheel保持。

固定baseline/fixed测试、唯一一行diff与35原测试／fixture快照在本片ignored `ci/windows-fix-r1/`；新本地检查直接使用原b2非editable最终r3 SDK安装。Linux原场景1通过，pytest3.62秒／外层4.423秒，原stdout／XML保持；静态求值平台条件Linux=false、win32=true、darwin=true，仅说明标记，不冒称真实Windows已验。原b2 reviewer已按同片限定范围独立核原完整测试、单行修正、35文件scope和实际Linux原件，需求与维护两轴approve／开放0／0；去新增decorator后完整AST与原测试相等。最终仍须普通单独推送、核完整Ref和该新SHA自己的CI；后继B3.1源码不纳入此小修复。

已单独普通发布`82ea3f163e0c29759eb6ebef93fb2e58d87e983a`，parent为原`9c9ffeee517deff2ec8cd2ffe572744e3c2cd682`，tree`0b8b5312d557642bd5257105561e76fbd01ee976`。四个commit blob与staged逐字相同，完整SSH远端Ref同一；测试blob为`c0df7165f0a019d6ad0c27144cd02e1a00f4ed41`，产品没有变更。发布原件保存于同片ignored `ci/windows-fix-r1/publication-local.json`；原reviewer继续核固定发布和该SHA自己的CI，终态未认证，不提前关闭前置门禁。

该修复自己的[Portability43658729462](https://github.com/626619403/Ergora/actions/runs/43658729462)／attempt1于`2026-11-15T00:54:43Z`终态success，八job／30必要步骤全部通过。原reviewer已独立核API／全部八job HTML／完整Ref，需求与维护两轴approve／开放0／0、violations为空；终态索引107件／3,669,064B、SHA `59f5d07b69cbbeb21c98e1308a11412b8b4570dbde3e4ee0bfe003ef4cc8cc1d`。本修正精确交付门禁闭合，原9c失败及其120件索引保持；不转授后继B3.1。
