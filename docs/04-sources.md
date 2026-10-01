# 研究来源与可验证边界

**读取日期：2026-09-30。共27个来源条目，其中1项正文访问受限、1项仅部分读取。** 原始网页未整页打包；不转存论坛个人标识、厂商固件或第三方签名材料。

“官方”只描述发布者身份，不自动提升到本机实测证据；第一人称报告只证明有人报告了该结果。本次没有任何本机解锁、恢复或驱动测试。代码链接指向可变分支，下一轮必须记录实际commit；清单中的空哈希表示尚未取得文件，不能由Agent猜填。

研究中的官方技术事实与案例陈述在主文中用 `[Sxx]` 标记；其余时间盒、验收和分工是本项目设计。机器可读清单见 `../evidence/sources.json`。

## S01 · 联想/ZUI 官方解锁入口
来源：[打开原始资料](https://www.zui.com/iunlock)  
性质：官方｜状态：已读取。  
本次读取：入口、风险说明、标识说明及条件性服务提示可读；未登录、未提交本机申请。  
边界：页面可达不证明本机获批；示例命令不是已验证的TB331FC步骤。

## S02 · 联想社区：Pad 2024 官方SN.img解锁失败
来源：[打开原始资料](https://club.lenovo.com.cn/thread-7926480-1-1.html)  
性质：同型号第一人称报告｜状态：已读取。  
本次读取：2024-05-27 的 TB331FC 失败案例。  
边界：不能代表当前固件，也不是厂商根因报告。

## S03 · lenovoubl Issue #1：Lenovo Xiaoxin Pad 2024
来源：[打开原始资料](https://github.com/MlgmXyysd/lenovoubl/issues/1)  
性质：上游问题跟踪/第一人称报告｜状态：已读取。  
本次读取：2026-03-12，TB331FC/ZUI 15.1.328：写入成功但OEM解锁失败。  
边界：与用户当前版本不同；未作实机复现，不保留帖主序列号。

## S04 · lenovoubl 上游仓库
来源：[打开原始资料](https://github.com/MlgmXyysd/lenovoubl)  
性质：项目原始资料｜状态：已读取。  
本次读取：确认项目入口与公开代码；下一步需固定提交。  
边界：未取得完整离线副本，也未证明支持本机。

## S05 · lenovoubl index.html
来源：[打开原始资料](https://raw.githubusercontent.com/MlgmXyysd/lenovoubl/master/index.html)  
性质：上游源码｜状态：已读取。  
本次读取：检查前端对初始系统分支与标识输入的要求。  
边界：只看UI不能验证引导程序接受条件；页面操作示例不得直接套用。

## S06 · lenovoubl js/main.js
来源：[打开原始资料](https://raw.githubusercontent.com/MlgmXyysd/lenovoubl/master/js/main.js)  
性质：上游源码｜状态：已读取。  
本次读取：静态阅读固定块、标识和填充的拼接逻辑。  
边界：没有分析完整验证端；未固定commit，不构成密码学绕过证明。

## S07 · AOSP：Lock and unlock the bootloader
来源：[打开原始资料](https://source.android.com/docs/core/architecture/bootloader/locking_unlocking)  
性质：官方技术文档｜状态：已读取。  
本次读取：通用状态、解锁开关、数据清除和critical保护语义。  
边界：不是联想特定版本的操作配方。

## S08 · Android Verified Boot README
来源：[打开原始资料](https://android.googlesource.com/platform/external/avb/+/master/README.md)  
性质：官方源码文档｜状态：已读取。  
本次读取：AVB验证与回滚保护概念。  
边界：只分析镜像元数据不足以知道设备全部防回滚策略。

## S09 · AOSP：Fastbootd
来源：[打开原始资料](https://source.android.com/docs/core/architecture/bootloader/fastbootd)  
性质：官方技术文档｜状态：已读取。  
本次读取：区分bootloader和userspace fastboot。  
边界：具体设备支持的查询仍须核对。

## S10 · AOSP：Boot image header
来源：[打开原始资料](https://source.android.com/docs/core/architecture/bootloader/boot-image-header)  
性质：官方技术文档｜状态：已读取。  
本次读取：启动头版本及结构分析入口。  
边界：没有本机镜像就不能替本机填启动布局。

## S11 · Lenovo Software Fix / Rescue and Smart Assistant
来源：[打开原始资料](https://support.lenovo.com/us/en/downloads/ds101291-rescue-and-smart-assistant-lmsa)  
性质：官方支持入口｜状态：部分读取。  
本次读取：确认产品支持入口；本次返回正文信息不足。  
边界：本机型号、地区、版本及执行平台支持均未核实。

## S12 · bkerler/edl
来源：[打开原始资料](https://github.com/bkerler/edl)  
性质：工具上游文档｜状态：已读取。  
本次读取：loader、设备标识与平台/厂商限制的研究入口。  
边界：没有取得经验证的TB331FC恢复链；不保证工具能救本机。

## S13 · Introducing Omarchy Dragon
来源：[打开原始资料](https://omarchy.org/news/2026/09/introducing-omarchy-dragon/)  
性质：项目官方公告｜状态：已读取。  
本次读取：2026-09-18：官方Snapdragon团队，当前公开工作聚焦X/X2系列电脑。  
边界：不能迁移成TB331FC支持承诺。

## S14 · omacom/try-omarchy
来源：[打开原始资料](https://github.com/omacom/try-omarchy)  
性质：项目官方仓库｜状态：已读取。  
本次读取：Apple Silicon Mac上的ARM虚拟机路径；USB直通为实验功能。  
边界：虚拟GPU和启动环境不验证平板硬件。

## S15 · omacom/omarchy-pkgs
来源：[打开原始资料](https://github.com/omacom/omarchy-pkgs)  
性质：项目官方仓库｜状态：已读取。  
本次读取：存在aarch64构建逻辑与架构选择。  
边界：选定版本所有依赖是否发布，需逐包验证。

## S16 · Omarchy manual：Getting started
来源：[打开原始资料](https://omarchy.org/manual/getting-started/)  
性质：项目官方手册｜状态：已读取。  
本次读取：普通安装的磁盘影响及早期输入要求。  
边界：不是Android平板刷机教程。

## S17 · Mesa：Freedreno
来源：[打开原始资料](https://docs.mesa3d.org/drivers/freedreno.html)  
性质：驱动上游文档｜状态：已读取。  
本次读取：Adreno用户空间驱动与设备表入口。  
边界：不证明本机kernel/display/touch完整支持。

## S18 · Linux qcom/sm6115.dtsi
来源：[打开原始资料](https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/qcom/sm6115.dtsi)  
性质：内核上游源码｜状态：已读取。  
本次读取：相邻平台设备树参考入口。  
边界：未证明与TB331FC兼容；不能替换本机设备树。

## S19 · postmarketOS：TB128FU 页面（待复核）
来源：[打开原始资料](https://wiki.postmarketos.org/wiki/Lenovo_Xiaoxin_Pad_2022_(lenovo-tb128fu))  
性质：社区设备Wiki｜状态：访问受限。  
本次读取：此次访问未成功取得可核验正文。  
边界：不引用其中功能表；不能据访问失败断言不存在移植。

## S20 · Android SDK Platform-Tools
来源：[打开原始资料](https://developer.android.com/tools/releases/platform-tools)  
性质：官方工具文档｜状态：已读取。  
本次读取：Google提供macOS ADB/Fastboot。  
边界：不证明OEM命令与任何特定固件兼容。

## S21 · Homebrew：android-platform-tools
来源：[打开原始资料](https://formulae.brew.sh/cask/android-platform-tools)  
性质：软件分发项目官方条目｜状态：已读取。  
本次读取：核对cask安装方式。  
边界：安装由Owner批准；实际版本另行记录。

## S22 · Claude Code：Permissions
来源：[打开原始资料](https://code.claude.com/docs/en/permissions)  
性质：产品官方文档｜状态：已读取。  
本次读取：权限与审批模式。  
边界：提示词和文档不是硬件隔离。

## S23 · Claude Code：Common workflows
来源：[打开原始资料](https://code.claude.com/docs/en/common-workflows)  
性质：产品官方文档｜状态：已读取。  
本次读取：Plan Mode与worktree工作流。  
边界：本地版本的CLI帮助仍需核对。

## S24 · Codex：Agent approvals & security
来源：[打开原始资料](https://learn.chatgpt.com/docs/agent-approvals-security)  
性质：产品官方文档｜状态：已读取。  
本次读取：核对read-only/workspace-write、on-request及旧策略退役。  
边界：沙盒模式不是Android写保护；不授予高风险全权执行。

## S25 · Codex：AGENTS.md
来源：[打开原始资料](https://learn.chatgpt.com/docs/agent-configuration/agents-md)  
性质：产品官方文档｜状态：已读取。  
本次读取：项目指导文件及层级发现机制。  
边界：不改用户全局配置；指令文件不是不可绕过的权限。

## S26 · Termux：proot-distro
来源：[打开原始资料](https://github.com/termux/proot-distro)  
性质：工具上游文档｜状态：已读取。  
本次读取：PRoot用户空间与权限/内核/服务管理边界。  
边界：不能称为原生Omarchy。

## S27 · Termux：termux-x11
来源：[打开原始资料](https://github.com/termux/termux-x11)  
性质：工具上游文档｜状态：已读取。  
本次读取：Android图形入口的参考路径。  
边界：不代表Wayland与本机完整驱动已解决。

## 尚未完成的证据获取

尚未登录官方渠道查询本机资格；尚未取得并校验匹配恢复包；尚未取得本机boot/vendor_boot/设备树/引导组件；尚未确认TB331FC的内核源码与可复现Linux移植；尚未验证任何EDL loader与授权；尚未连接Mac或Pad。

对postmarketOS相关页面和软件支持动态页面的访问限制，意味着本次无法核实部分内容，不意味着内容或支持不存在。下一轮可由Owner与Agent在正常浏览器中重试，并将来源与访问结果补入清单。

此前对话中的未附可复核证据的说法不计入来源等级。网上的“已解锁出售”不能证明从用户当前版本能复现；未匹配版本的成功截图只保留为线索。
