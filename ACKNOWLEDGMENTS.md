# Acknowledgments ｜ 致谢

> This project is built on ideas explored by the Agent Skills community. We studied five prior academic-writing skills as a **design-space survey** (v1.6.0), adopted the ideas compatible with this project's philosophy, re-implemented them from scratch for Chinese academic manuscripts, and explicitly rejected the mechanisms that conflict with it — no code or text was copied from any upstream project.
>
> 本项目在 Agent Skills 社区已有探索的基础上构建。我们以**设计空间调研**的方式研究了五个先行的学术写作技能（v1.6.0），采纳其中与本技能哲学相容的思想并按中文学术书稿场景从零重新实现，与哲学冲突的机制则明确拒绝——未复制任何上游项目的代码或文本。

## Skills · 五步法调研（v1.6.0）

调研起点为微信文章《五步写作 SCI 论文》推荐的五个辅助 skill，逐个实地核查原文后取其精华、去其糟粕。每条均为「来源思想 → 本技能转化」：

- **paper-polish-workflow**：润色工作流思想 → 转化为中文场景的润色批次（三轮润色法：论证完整 → 图表方法细节 → 术语语言统一）、保守修改原则（可能改变科学含义的改动保留原句、列建议交作者裁定）与中文去 AI 腔清单
- **nature-academic-search**：字段级核验思想 → 转化为引用核验四态与检索留痕（台账 §4/§4c）；其开放网络检索路由与本技能「只查作者语料」哲学冲突，**不采纳**
- **K-Dense scientific-writing**：数字对账思想 → 轻量化为关键数值跨章一致性校验（台账 §3c）
- **venue-templates**：强制时效规则 → 转化为交稿规范时效核验（盲审导出登记格式手册版本与获取渠道）
- **academic-paper-strategist**：同批调研；其样章风格学习方向列为 Roadmap 候选（Issue #4），未纳入现行实现

同批明确不采纳的机制（与本技能「判断与执行分离、轻依赖」哲学冲突）：开放网络检索路由、伪精确打分、逐句交互、LaTeX 模板体系、多脚本重体系。

## Methodology · 方法论

- **skill-creator**：本技能发版闸门的评估闭环（新旧双配置对照＋程序化评分，已运行六轮 iteration）以其基准测试方法论为来源
- **editing-proofreading-expert v1.0.0**：写时校对专项调研对象——采纳其分层校对思想（写时轻校＋全书终校，v1.8.0 排期），排除其云端工具依赖与纸质编校符号流程

## Inspiration · 灵感源

- 微信文章《五步写作 SCI 论文》—— v1.6.0 五 skill 调研的触发源

## Standards · 规范

- Agent Skills 开放规范 —— 本技能遵循的打包格式（SKILL.md ＋ references ＋ scripts）
