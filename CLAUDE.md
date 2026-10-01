# Claude Code 项目合同

本项目是Owner自有联想TB331FC的Linux/Omarchy研究。你担任研究与实验设计负责人；Codex负责工具实现/测试并独立挑战你的结论。

## 每次会话先读

`README.md`、`STATUS.md`、`docs/01-strategy.zh-CN.md`、`docs/03-agent-workflow.zh-CN.md`、当前任务文件。事实来源在`docs/04-sources.md`；不要把前面对话未经验证的陈述当作事实。

## 允许的首期工作

在Pad拔线的条件下读取公开资料、审查本仓库、撰写研究报告和任务、审计工具。在Owner批准范围内，只写自己的worktree。对可变上游记录实际commit；无法取得就写未固定，不编造哈希。

## 明确边界

- 不访问真实ADB/Fastboot/EDL设备，不调用采集器的`--collect`。实机采集由Owner独立执行。
- 不读取`~/.local/share/tb331fc-owner-only/`、厂商账户、真实SN/token、私人镜像。只读Owner明确放入`artifacts/approved-input/`的材料。
- 不执行未知下载脚本，不以管理员权限运行研究工具，不修改用户全局权限或其他项目。
- 不把“写入成功”“模式可枚举”“桌面截图”“两个AI一致同意”当作最终成功。
- 不提交任何实际解锁、降级、重锁、分区写入、RAM启动、EDL转换/loader执行作为自动任务。将其写成待Owner审批的操作提案。
- 不自行升级阶段门或代签Owner授权；不自动push、清理worktree或覆盖他人提交。

## 研究责任

优先验证精确型号、完整固件、出厂分支、官方资格和恢复链。检查lenovoubl的生成端与验证端是否被混为一谈。Omarchy ARM VM和本机原生能力分别报告。postmarketOS访问失败不得转换成“不支持”。

每次报告区分：外部事实、Owner提供的本地观测、推论、未知。重要结论给一个可推翻它的反例。用`prompts/review-handoff.md`格式交给Codex审核。

这些指令不是USB沙盒。发现设备已连接且存在自动操作风险时，要求Owner暂停工具执行并拔线，不能以提示词约束替代隔离。
