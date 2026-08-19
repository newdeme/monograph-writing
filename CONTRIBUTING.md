# 贡献指引

感谢你愿意改进这个项目！它很小，但对正在写书的人来说很实用。以下是参与方式。

## 反馈问题（最欢迎）

用 GitHub Issue 描述：

1. 你在写什么类型的书（专著/教材/技术书）、使用哪个 AI 平台；
2. 遇到的问题：脚本报错（附完整输出）、流程不顺、校验误报/漏报；
3. 期望的行为。

## 分享实战经验

方法论的价值来自真实使用。欢迎提交 Issue 分享：

- 新的"常见坑"（会被收录进 `references/batch-workflow.md` 的坑清单）；
- 其他引用格式（如 APA / Chicago）的适配经验；
- 多人协作的实际编排方式。

## 代码/文档改进（Pull Request）

1. Fork 并建分支：`git checkout -b fix-xxx` 或 `feat-xxx`；
2. 保持脚本的既有约束：**纯 Python 标准库**（merge_to_word.py 的 python-docx 除外）、中文输出、面向非计算机用户的错误提示；
3. 改动脚本请附最小复现用例（初始化→校验的临时目录即可）；
4. 新增文件顶部加 SPDX 标识（`# SPDX-License-Identifier: Apache-2.0`）；
5. 提交 PR 并简述动机与验证方式。

## 贡献授权（Contribution License Agreement）

**中文**：当你向本项目提交 Pull Request 时，即表示你同意：你拥有所提交内容的相应权利，并授予项目维护者（newdeme）以 Apache License 2.0 及未来可能采用的其他许可方式使用、复制、修改、再许可（sublicense）你的贡献内容的权利。这一约定用于保持项目未来调整许可协议与商业化的灵活性；本项目当前不设单独的 CLA 签署流程，提交 PR 即视为同意本条款。

**English**: By submitting a Pull Request to this project, you agree that you have the necessary rights to your contribution and that you grant the project maintainer (newdeme) a right to use, copy, modify, and sublicense your contribution under Apache License 2.0 and under any other license that may be adopted by the project in the future. This keeps the project flexible for future relicensing and commercialization. There is currently no separate CLA sign-off process; submitting a PR indicates your acceptance of these terms.

## 行为约定

保持善意与专业讨论；不贬低任何提问；引用他人工作时如实署名——这也是本项目方法论本身的要求。
