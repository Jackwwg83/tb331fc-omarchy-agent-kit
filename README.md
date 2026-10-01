# TB331FC 原生 Linux / Omarchy 研究与 Agent 执行包

**给 Jack｜研究基线 2026-09-30｜明天开始：2026-10-01（UTC+8）**

你的设备：照片中的联想小新 Pad 2024，**TB331FC / 骁龙685 / 8GB+128GB / ZUX OS 1.1.10.680**。

## 先看结论

**可以让 Claude Code 与 Codex 开始协作研究，但现有证据还不能批准直接刷机。** 官方解锁入口和 Omarchy 官方 ARM 工作都是值得推进的线索；本机精确版本的解锁结果、恢复材料与 Linux 驱动仍未验证。

这不是一键刷机包。它包含研究结论、后续方法、两个 Agent 的合同与启动任务，以及一个默认不连接设备的只读采集器。当前没有设备写入权限，没有解锁文件，没有厂商镜像，也没有预填的成功记录。

## 明天最短启动顺序

**1．解压到一个新目录。** 建议目录是 `~/Projects/tb331fc-omarchy-agent-kit`。不要覆盖现有项目。

**2．先读主策略，再建立两个工作区。** 主策略是 `docs/01-strategy.zh-CN.md`；Git worktree 的完整命令在 `docs/03-agent-workflow.zh-CN.md`。先有初始 commit，再创建 worktree，不让两个工具同时改主目录。

**3．给 Claude 和 Codex 各自一条启动指令。** 在它们各自的 worktree 打开会话，把以下对应文字交给它们：

```text
Claude Code：读取 CLAUDE.md、README.md 和 prompts/claude-start.md，
按该任务开始。先研究、核对证据并给出计划；不要操作真实设备。
```

```text
Codex：读取 AGENTS.md、README.md 和 prompts/codex-start.md，
先独立审计采集脚本与测试，重点找反例；不要操作真实设备。
```

初始启动参数已写在工作流文档中。先用计划/只读模式，明确可写范围后才允许修改本项目文件；**不要开启跳过审批或完全放权模式**。

**4．验证采集器（不需要连接 Pad）。** Agent 可以替你执行：

```bash
cd ~/Projects/tb331fc-omarchy-agent-kit
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 scripts/collect_readonly.py
```

默认只显示计划。随包 `artifacts/unit-tests.txt` 记录了生成时的模拟测试，但你和Agent仍应检查并在Mac重跑。

**5．脚本经双方审阅后，接上 Pad 读取设备。** 你在平板上启用USB调试、只连接这台平板；命令可由 Agent 执行（执行前会说明）：

```bash
adb devices -l
python3 scripts/collect_readonly.py --collect
```

脚本提示输入USB序列号，不回显。更完整的环境准备与失败处理见 `docs/02-runbook.zh-CN.md`。**不要在这个阶段切换OEM解锁开关、重启到下载模式或执行任何刷写。**

**6．查看报告、检查脱敏。** 私人报告默认在 `~/.local/share/tb331fc-owner-only/`，不在仓库内。只把你审阅过的过滤版复制到 `artifacts/approved-input/`，再交给两个Agent解释。

**7．让两个Agent交付一页决策，而不是自动进入刷机。** 首日任务表在 `docs/05-first-day.zh-CN.md`；用 `templates/day1-decision.md` 汇总。只有证据和恢复条件过关后，才提出单独的实际操作申请。

## 文件导航

| 文件/目录 | 用途 |
|---|---|
| `docs/01-strategy.zh-CN.md` | 完整研究结论、解锁假设、原生路线、阶段门 |
| `docs/02-runbook.zh-CN.md` | 主机准备、采集、脱敏、固件分析、后续实验方法 |
| `docs/03-agent-workflow.zh-CN.md` | Claude/Codex分工、启动模式、worktree、交叉审核 |
| `docs/04-sources.md` | 27项来源及哪些结论不能从来源推导 |
| `docs/05-first-day.zh-CN.md` | 明天的具体安排与停机条件 |
| `CLAUDE.md` / `AGENTS.md` | 两个Agent各自应遵守的项目合同 |
| `prompts/` / `tasks/` | 可直接交给Agent的启动任务与验收标准 |
| `templates/` | 硬件报告、恢复矩阵、固件清单、操作提案、首日决策 |
| `scripts/collect_readonly.py` | 默认计划模式；Owner主动执行后做固定ADB读取 |
| `tests/` / `artifacts/` | 模拟测试与生成时测试记录；不包含本机测试结果 |
| `STATUS.md` | 初始状态：本机未连接、所有设备写入门关闭 |
| `research-guide.html` | 可用浏览器打开的合并阅读版 |

## 这套包已验证什么

生成时在隔离的 Linux 环境运行了32项模拟单元测试；没有启动真实ADB，也没有连接Mac/Pad。测试涵盖默认不执行、目标型号和USB检查、禁止任意查询、多设备/异常状态拒绝、超时、脱敏、文件权限与协作锁。

测试通过**不证明**原厂恢复可行、Bootloader可解锁、内核可启动或Omarchy可用。具体测试环境和边界见 `artifacts/TESTING.md`。

## 最重要的操作规则

Owner 接上 Pad 后，Agent 可以直接执行只读查询；任何会改变设备状态的操作（重启进特殊模式、解锁、刷写、擦除、降级等），Agent 必须先用大白话说明做什么、风险和退路，得到你逐条明确同意才执行，失败不自动重试。同一时间只让一个 Agent 操作设备。未知条件保留为未知，不能为了完成任务自行扩大权限。

没有匹配固件、恢复条件和逐次批准，不进行解锁、降级、重新上锁、临时启动镜像、写分区、进入EDL或上传loader。主策略中的阶段门是研究安排，**不是自动化执行许可**。
