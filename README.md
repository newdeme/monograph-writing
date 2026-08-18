# monograph-writing ｜ 学术专著批次化写作助手

> Academic Monograph Batch-Writing Assistant —— 把"写一本十几章的书"变成 AI 可接力、可校验、可多人协作的流水线。

**English summary**: A skill for AI-writing-assistant platforms (Claude Code / Claude Agent SDK / Cherry Studio, any environment supporting the Agent Skills spec). It turns monograph writing into a batch pipeline: one section directory per batch, three-step writing method (argument tree → evidence list → draft), layered summaries, a progress ledger as the single source of truth across sessions, and automated validation scripts (citation numbering, word-count tiers, table/figure numbering), plus stripped-version and Word-merge generation. Primarily in Chinese, targeting GB/T 7714 citation style by default (configurable).

---

## 一、这是给谁用的？

给**要写书的人**：高校教师写学术专著、科研人员写技术书、工程师写行业手册、研究生团队合写教材——尤其是：

- 书有十几章、几十万字，**一个人在一段对话里根本写不完**；
- 用 AI 写又**怕它编造文献和数据**；
- 多人/多会话接力写，**怕前后不一致、进度失控**。

如果你符合其中任何一条，这套方法就是为你设计的。**全程不需要编程知识**——脚本由 AI 助手替你运行。

## 二、它解决什么问题？

| 痛点 | 本技能的做法 |
|---|---|
| AI 长文写作会"失忆" | 进度台账落盘为文件，跨会话/跨人无缝续作 |
| AI 会编造文献 | 学术红线＋引用前逐条与原文核对＋禁止引用语料之外的文献 |
| 章节风格漂移 | 固定目录冻结结构＋术语/符号双台账＋每批校验 |
| 引用编号、图表编号混乱 | 校验脚本自动检查（引用首现顺序、连续性、图表跳号），错误清零才能收批 |
| 字数失控 | 分章字数分级配置，脚本按"叙述文字"口径自动实测 |
| 最后拼稿痛苦 | 一键生成剥离版（去写作准备）与合并 Word 稿（自带目录、样式） |

## 三、快速开始（3 步）

**第 1 步：把本文件夹放进你的 AI 助手技能目录**
- Cherry Studio 用户：应用会自动同步技能目录（设置里可查看技能库位置）；
- Claude Code 用户：放入 `~/.claude/skills/` 或项目 `.claude/skills/`。

**第 2 步：准备你的目录**
把全书大纲整理成一个 Markdown 文件（格式如下，让 AI 帮你排版也行）：

```markdown
# 《你的书名》目录

## 第一章 章标题

**1.1 节标题**
- 1.1.1 小节标题
- 1.1.2 小节标题

**1.2 节标题**
…

**1.N 小结**
```

**第 3 步：对 AI 助手说一句话**

> "用 monograph-writing 技能初始化我的专著项目，目录在 xxx.md"

AI 会运行 `init_project.py` 生成项目骨架，然后与你确认字数分级和文献语料来源，之后每次你说"**继续**"，它就按台账推进下一个批次。每批次结束你会收到一份汇报：写了哪些文件、校验结果、下一批预告。

## 四、四个自动化脚本（AI 替你跑，人也看得懂）

| 脚本 | 作用 | 什么时候用 |
|---|---|---|
| `scripts/init_project.py` | 从目录一键生成项目骨架（配置＋双台账＋指令清单） | 开工一次 |
| `scripts/validate_manuscript.py` | 校验命名/结构/字数/引用编号/图表编号 | 每批次收尾必跑 |
| `scripts/generate_stripped_version.py` | 剥离"写作准备"，生成纯正文版＋章合并稿 | 章节定稿后 |
| `scripts/merge_to_word.py` | 生成带目录与排版样式的单个 Word 书稿 | 需要交稿时（需 `pip3 install python-docx`） |

所有项目参数集中在 `00_管理文件/书稿配置.json`——改字数要求、加豁免档，改这一个文件即可，脚本不用动。

## 五、核心理念（为什么这样设计）

1. **台账即状态**：书的进度、约定、编号指针、已核实文献全部登记在项目内文件里。写在磁盘上而不是对话里——换会话、换人、换电脑都无损续作。
2. **批次推进**：一个二级目录 = 一个批次（全部小节＋节级总结）。小步交付，跑校验至零错误才收批，错误不会累积成灾。
3. **判断与执行分离**：作者是学术责任人（论证立场、资料取舍、结论裁定）；AI 是写作搭档与流程执行者，不代替作者作学术判断，更不编造证据。
4. **分层汇总防遗忘**：节级总结（600~800 字）→ 章末小结只依据各节级总结撰写，避免通读全章导致的上下文遗忘。
5. **写作准备随文保留**：每小节文件含论点树与证据清单（三段式），审稿/返修时可溯源，成书时一键剥离。

## 六、项目结构一览

```
你的书/
├── 00_管理文件/            专著目录、书稿配置、进度台账、术语台账、指令清单
├── 01_书稿/第X章 章标题/Y.Z 节标题/   全部书稿（随批次逐节生成）
├── 03_归档素材/            外部旧稿（走修复批次，不直接采用）
└── 04_剥离版书稿/          纯正文版＋合并 Word 稿（脚本生成）
```

## 七、多人协作

- 每人负责若干章，工作方法完全一致（本技能即规范）；
- 交接时：进度台账＋一份交接说明随工作空间移交；
- 文献语料不随文件走时，接手人只用台账 §4"已核实文献缓存"，新文献请语料持有人代查——**宁可少引，不可错引**。

## 八、常见问题

**Q：我完全不会命令行，能用吗？**
能。所有脚本由 AI 助手运行，你只需要用日常语言交流（"继续""下一章""把第二章字数调到 1200~1800"）。

**Q：不用 GB/T 7714 引用格式行吗？**
行。在 `书稿配置.json` 里改 `citation_style`，并把 `check_citation_style` 设为 `false`（该项检查仅适配 GB/T 7714 的类型标识）。

**Q：引用格式为什么查得这么严？**
真实专著写作中，"引用编号未按首现顺序""文献数与正文对不上"是最高发的错误，人工排查一本几十万字的书几乎不可能。让脚本每批把关，成书时才有底气。

**Q：我的 AI 平台不是 Claude，能用吗？**
本技能遵循 Agent Skills 开放规范（SKILL.md＋脚本＋参考文档）。任何支持该规范的 AI 助手平台均可使用；脚本本身是纯 Python 标准库（仅 Word 合并需 `python-docx`），也可独立使用。

**Q：写作中途想改目录怎么办？**
目录冻结是严肃约定：改动须作者确认后升版（v2、v3…），并同步台账。已完成章节不悄悄重写——历史矛盾登记台账 §5 待裁定。详见技能内 `references/` 文档。

## 九、贡献与许可

- 本技能源自一部真实学术专著的完整写作实践，方法论经 200+ 小节批次检验。
- 欢迎通过 Issue / Pull Request 反馈改进（批次经验、新校验规则、其他引用格式适配等）。
- 本项目以 [Apache License 2.0](LICENSE) 发布，版权所有 © 2026 newdeme；含专利授权条款，可放心在学术与商业项目中使用。

---

*本技能由 AI 写作助手与专著作者协作打磨；方法论细节见 `SKILL.md` 与 `references/` 目录。*
