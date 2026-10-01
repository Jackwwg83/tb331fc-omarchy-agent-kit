# 发给 Codex 的启动任务

你是工具/测试负责人，并担任Claude研究结论的独立审查者。先读AGENTS.md、README.md、STATUS.md、主策略与协作文件。设备操作规则见AGENTS.md：只读查询可执行，状态变更须Owner逐条同意；与Claude不同时操作设备。

首轮执行T001：不要连接设备，不调用任何真实ADB/Fastboot/USB，不读取Owner私人目录。

检查`scripts/collect_readonly.py`与全部测试，重点回答：默认模式是否真的不运行子进程；固定查询是否可能扩展成任意shell；目标序列号/型号/USB/多设备处理是否拒绝不确定情况；超时是否自动重试；未知值是否误判；错误与私人信息是否泄漏；跨worktree协作锁有哪些绕过边界。

先重跑模拟测试，再提出最重要的三个未覆盖风险。若需要改代码，先列变更范围并等Owner允许workspace写入；保持无真实设备，不增加任意命令/自动刷写能力。

随后准备T003的ARM用户空间验证清单，根据Owner确认的Mac架构选择路径。软件安装/下载执行需要另获批准；不传入USB设备，不共享宿主私人目录或ADB服务。VM运行成功不得写成本机驱动成功。

交付`reports/codex-tool-audit.md`、必要的代码/测试提交，以及`reports/codex-arm-userspace.md`。用handoff格式交Claude复核。

再独立审核Claude的T002报告：至少找出型号/版本类比、恢复保证和token成功判据中的潜在漏洞；引用你自己核查过的材料，不只转述Claude。
