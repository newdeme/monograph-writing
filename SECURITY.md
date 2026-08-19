# 安全策略 / Security Policy

## 支持范围 / Scope

本项目由四部分组成：SKILL.md（工作流文档）、references/（方法论文档）、scripts/（四个 Python 脚本：init_project / validate_manuscript / generate_stripped_version / merge_to_word）、examples/（示例项目）。安全报告适用于上述脚本与文档中的缺陷，尤其是：

- 脚本对本地文件的非预期读写或删除（本项目脚本仅读写项目目录内的文件，不应有任何网络行为）；
- 路径处理缺陷导致的越界访问；
- 生成的 docx 内容注入类问题。

This skill consists of four Python scripts, workflow documentation, and an example project. Security reports apply to defects in these scripts and docs — especially unexpected file access outside the project directory (the scripts perform no network operations by design), path handling flaws, and content-injection issues in generated docx files.

## 如何报告 / Reporting a Vulnerability

**请勿在公开 Issue 中提交安全漏洞。** 请使用 GitHub 的私密漏洞报告（Private vulnerability reporting）：仓库页 → Security 标签 → Report a vulnerability。

**Please do not open public issues for security vulnerabilities.** Use GitHub's private vulnerability reporting instead: repository page → Security tab → Report a vulnerability.

如该入口未开启，可通过 GitHub Issues 以不含漏洞细节的方式联系维护者，待其开启私密通道后再提交详情。

## 响应预期 / Expectations

- 收到报告后会尽快确认（目标 7 天内）；
- 修复后会在 Release 说明中致谢报告者（除非报告者要求匿名）。

## 隐私说明 / Privacy

本项目四个脚本全部在本地运行，不联网、无遥测、不收集任何数据；如发现任何疑似联网或数据外传行为，请按上述途径立即报告。
