# 测试记录与边界

日期：2026-09-30。环境：Linux / x86_64 / Python 3.13.5。

## 已实际执行

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/collect_readonly.py
```

单元测试：**32项，通过**。详细stdout/stderr在`unit-tests.txt`。默认计划输出在`plan-only-example.json`，共有38项固定查询；这份文件只是计划，不是设备观测。

Python源文件另经AST解析检查。没有真实ADB调用，没有USB设备访问，没有下载或运行厂商固件。

本次测试对应采集器SHA-256：

```text
debba7c3af50fc505dcc935cae5994139a40ab66586a9a2ae7aea9f3b7650991
```

## 覆盖

默认零执行、固定查询与非shell子进程、序列号格式/明确目标/型号校验、USB标志、多设备与授权状态拒绝、连接变化中止、超时无重试、未知字段保留、报告过滤与原始信息隔离、目录/文件权限、协作锁互斥。

## 不代表什么

没有在macOS实测，也没有在TB331FC上运行。Python 3.9是代码目标，不等于已经对每个3.9+版本做兼容矩阵。必须在Owner的Mac重跑并审核，再由Owner单独做第一次设备采集。

测试不证明Bootloader可解锁、恢复包匹配、数据已备份、EDL可用、Linux启动或GPU正常。

协作锁可被其他程序绕过；过滤器可能漏掉隐私字段；USB标志/型号异常可能产生保守拒绝；报告未知项不提供解锁许可。这些都是待实际环境确认的边界。

## 版本变更

修改脚本后应重新运行测试、计算哈希并接受另一Agent及Owner审阅。旧哈希/测试记录不自动适用于新代码。
