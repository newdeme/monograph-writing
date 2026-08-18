#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 newdeme
"""
init_project.py —— 专著写作项目初始化脚本（monograph-writing 技能组件）
========================================================================
用途：根据作者已冻结的《专著目录.md》，一键生成整个写作项目的骨架：
    00_管理文件/书稿配置.json            全部项目参数（字数分级/路径/豁免档）
    00_管理文件/写作进度台账.md           跨会话进度与状态锚点（含图表编号指针）
    00_管理文件/术语与符号一致性台账.md    术语表/符号表/新符号流程/一致性待办
    00_管理文件/写作指令清单.md           全书"现在开始写…"批次指令清单
    01_书稿/  03_归档素材/  04_剥离版书稿/  工作目录

目录文件格式（三级结构，每章建议以"X.Y 小结"收尾）：
    ## 第X章 章标题
    **Y.Z 节标题**
    - X.Y.Z 小节标题

用法（在终端里让 AI 助手代跑即可，人不必记命令）：
    python3 init_project.py <项目根目录>                     # 目录已在 项目/00_管理文件/专著目录.md
    python3 init_project.py <项目根目录> --catalog <目录.md>  # 目录在其他位置
    python3 init_project.py <项目根目录> --sample             # 尚无目录：先生成示例目录供作者填写

安全：项目已存在台账时拒绝覆盖（--force 才允许，慎用）。
"""
import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

CATALOG_NAME = "专著目录.md"
CH_RE = re.compile(r"^## (第.+?章 .+)$")
CH_NUM_RE = re.compile(r"^(第.+?章)")
SEC_RE = re.compile(r"^\*\*(\d+\.\d+) (.+?)\*\*$")
ITEM_RE = re.compile(r"^- (\d+\.\d+\.\d+) (.+)$")

SKIP_NAME_KEYWORDS = ["台账", "校核报告", "评估报告", "专著目录", "写作指令清单", "说明"]

CORPUS_NOTE = """# 这里是你的文献资料库（02_语料/）

把你想让 AI 引用的文献资料放进本文件夹即可——**放什么、什么格式，完全由你决定**。

- 支持格式：PDF、Word、Excel、Markdown、TXT 等任何你的 AI 助手能阅读的格式
  （Excel 适合数据表/参数表；Word/Markdown 适合笔记、综述、规范摘编）；
- 建议按主题或类型分子文件夹（如 期刊论文/、规范标准/、数据表格/、读书笔记/）；
- 重复副本建议去重；多篇文章合订的 PDF 建议拆分后放入；
- 写作中 AI 只引用本文件夹（或你登记的其他语料）内的资料，并逐条与原文核对题录。

铁律：语料的边界＝可引用的边界。放进来的每一份资料，都应该是你愿意让它出现在
参考文献表里的资料。更多接入方式（AI 知识库 / Zotero / 降级模式）见技能文档
references/evidence-corpus.md。
"""

SAMPLE_CATALOG = """# 《示例书名》目录（示例版——请作者改写后冻结）

> 使用说明：本文件是全书章节结构与编号的唯一依据。请按下方格式改写为你的目录，
> 经作者确认后即为"冻结版"，此后改动须经作者确认并升版（v2、v3 …）。
> 体例：三级目录，每章建议以"X.Y 小结"收尾。

## 第一章 绪论

**1.1 研究背景与意义**
- 1.1.1 研究背景
- 1.1.2 研究意义

**1.2 国内外研究现状**
- 1.2.1 国外研究现状
- 1.2.2 国内研究现状
- 1.2.3 现状述评

**1.3 小结**
"""

LEDGER_TMPL = """# 写作进度台账

> 用途：跨会话的进度与状态锚点。每批次收尾时由写作助手更新；人工请勿随意改动
> "进度状态"与"编号指针"，其余部分可批注。
> 冲突裁决顺序：本台账 > 其他管理文件 > 技能说明。

## 1. 项目与全局约定（固定，不得中途更改）

- 书名：《{title}》（初始化日期：{today}）
- 目录：`00_管理文件/{catalog_name}` 为全书章节结构与编号的**唯一依据**（冻结版）
- 引用格式：{cite}，按正文首次出现顺序编号（含表格阅读序）
- 文献语料（红线：引用仅限此来源；接入方式四选一，详见技能 references/evidence-corpus.md）：
  - 【接入方式】（①AI 客户端知识库 / ②Zotero 等文献管理器 / ③02_语料/ 文件夹 / ④暂不接入-降级模式）：【待访谈后填写】
  - 【名称/位置】（如：AI 助手内知识库"书稿文献"；或 Zotero 集合名；或 02_语料/）：【待填写】
  - 【检索方式】（如：知识库搜索；或条目检索；或 AI 直接读文件）：【待填写】
  - 【核对方式】新文献题录须读原文首页核对后写入，核对过即登记 §4 缓存；降级模式下只可引用作者手工核实过的文献
- 图表编号：`图X-Y` / `表X-Y`（X=章号，Y 章内连续），图表须有中文标题且正文有解读
- 术语/符号一致性：登记于《术语与符号一致性台账.md》；符号体系锚点：【填写：全书符号在哪一小节统一确立】
- 文件命名：小节 `X.Y.Z 小节标题.md`；节级总结 `第X章 Y.Z节 节标题 章节总结.md`；章末小结 `X.Y 小结.md`（与目录逐字一致，分隔符用空格）
- 字数分级：见 `00_管理文件/书稿配置.json`（以校验脚本实测为准）
- 小节文件三段式：`## 一、写作准备`（成书时统一剥离）→ `## 二、正文` → `## 参考文献`
- 批次单位：一个二级目录（含其节级总结）；"X.Y 小结"单独成批；不跳节、不跳章

## 2. 进度状态

（每批次收尾在此追加一行：`X.Y 节标题（N 小节＋节级总结）✅ 日期｜字数实测 …`；
批次中途收束的写"进行中"断点：写到哪个小节、证据是否已核、下一步。）

- （暂无）

## 3. 图表编号指针（各章下一个可用编号）

| 章 | 下一个表号 | 下一个图号 |
|---|---|---|
{pointer_rows}

## 4. 已核实文献缓存（题录核对通过，可直接引用）

（格式：`- 作者. 题名[J]. 刊名, 年, 卷(期): 页码. ｜ 已核：日期＋核对位置`；新核实的当日登记，节省后续批次重查。）

- （暂无）

## 5. 待裁定事项（发现矛盾只登记，不改历史章节）

- （暂无）

## 6. 遗留 WARN 与已知事项（可接受的校验警告＋理由）

- （暂无）
"""

TERM_LEDGER_TMPL = """# 术语与符号一致性台账

> 用途：全书术语、符号与概念一致性的唯一登记台账。
> 维护规则：
> 1. 专业术语首次出现的小节须给出简明定义，并于该小节完成当日登记本表；
> 2. 符号体系以【填写锚点小节，如 3.1.5】为确立点，此前先行使用的基础符号由该小节写作时终审锁定，此后全书沿用、不得重新定义同一物理量；
> 3. 引入新符号前先查本表：无冲突→随小节完成登记；有冲突→登记 §4 待办并附改名建议，待作者裁定后方可使用；
> 4. 每章章末检查点核对本表一次；发现历史文件与新裁决不一致时只登记、不擅自改写。

## 1. 术语表

| 术语 | 英文对照 | 缩写 | 定义（简明） | 首次出现 | 状态 |
|---|---|---|---|---|---|
| （示例）某某方法 | xxx method | XX | 一句话定义 | 1.1.1 | 已登记 |

## 2. 符号表

| 符号 | 含义 | 单位 | 首次出现/确立点 | 状态 |
|---|---|---|---|---|
| （示例）$x$ | 某物理量 | m | 【锚点小节】 | 已锁定 |

## 3. 新符号引入流程

拟用符号 → 查 §2 符号表：无冲突 → 随小节完成登记；有冲突 → 登记 §4 并附改名建议 → 作者裁定后方可使用。

## 4. 一致性待办（冲突/历史不一致，只登记不改历史）

- （暂无）
"""

CONFIG_TMPL = """{{
  "book_title": "{title}",
  "author": "",
  "citation_style": "{cite}",
  "catalog_file": "00_管理文件/{catalog_name}",
  "manuscript_dir": "01_书稿",
  "stripped_dir": "04_剥离版书稿",
  "excluded_dirs": ["00_管理文件", "02_语料", "03_归档素材", "04_剥离版书稿", ".claude", ".git"],
  "skip_name_keywords": {skip_kw},
  "word_targets": {{
    "default": [1500, 2000],
    "by_chapter": {by_chapter},
    "section_summary": [600, 800],
    "chapter_summary": [300, 500]
  }},
  "special_tiers": [],
  "exempt_patterns": [],
  "tolerance": 0.15,
  "check_citation_style": true
}}
"""


def parse_catalog(path: Path):
    """解析目录 → [ {title, prefix, sections: [ {num, title, items: [(num, title)] } ] } ]"""
    chapters = []
    cur_ch, cur_sec = None, None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        m = CH_RE.match(line)
        if m:
            title = m.group(1).strip()
            pm = CH_NUM_RE.match(title)
            cur_ch = {"title": title,
                      "prefix": pm.group(1) if pm else title,
                      "sections": []}
            chapters.append(cur_ch)
            cur_sec = None
            continue
        m = SEC_RE.match(line)
        if m and cur_ch is not None:
            cur_sec = {"num": m.group(1), "title": m.group(2), "items": []}
            cur_ch["sections"].append(cur_sec)
            continue
        m = ITEM_RE.match(line)
        if m and cur_sec is not None:
            cur_sec["items"].append((m.group(1), m.group(2)))
    return chapters


def gen_instructions(title, chapters):
    body = []
    for ch in chapters:
        for sec in ch["sections"]:
            if sec["title"] == "小结":
                body.append(f"现在开始写「{ch['prefix']}的{sec['num']} 小结」。")
                continue
            for num, item_title in sec["items"]:
                body.append(
                    f"现在开始写「{ch['prefix']}的{sec['num']} {sec['title']}」"
                    f"的「{num} {item_title}」。")
    return f"# 写作指令清单｜《{title}》\n\n" + "\n".join(body) + "\n"


def main():
    ap = argparse.ArgumentParser(description="专著写作项目初始化（详细说明见文件头注释）")
    ap.add_argument("root", help="项目根目录（将在此创建骨架）")
    ap.add_argument("--catalog", help="专著目录.md 路径（缺省在 root/00_管理文件/ 下寻找）")
    ap.add_argument("--title", help="书名（缺省取目录 H1 标题中的《书名》）")
    ap.add_argument("--sample", action="store_true",
                    help="尚无目录：生成示例目录供作者填写后退出")
    ap.add_argument("--force", action="store_true",
                    help="覆盖已存在的台账（慎用，不动 01_书稿/）")
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    mgmt = root / "00_管理文件"
    mgmt.mkdir(parents=True, exist_ok=True)
    for d in ("01_书稿", "03_归档素材", "04_剥离版书稿"):
        (root / d).mkdir(exist_ok=True)
        (root / d / ".gitkeep").touch()
    # 02_语料/：作者的文献资料库（格式不限、内容自定），附使用说明
    corpus = root / "02_语料"
    corpus.mkdir(exist_ok=True)
    if not (corpus / "把文献放这里.md").is_file():
        (corpus / "把文献放这里.md").write_text(CORPUS_NOTE, encoding="utf-8")

    # 定位/生成目录文件
    catalog = Path(args.catalog).expanduser().resolve() if args.catalog else None
    if catalog is None:
        for cand in (mgmt / CATALOG_NAME, root / CATALOG_NAME):
            if cand.is_file():
                catalog = cand
                break
    if catalog is None:
        if not args.sample:
            print(f"[未找到目录] 请先把《{CATALOG_NAME}》放到 {mgmt}/ 下，"
                  f"或用 --catalog 指定路径；或加 --sample 生成示例目录。")
            return 1
        catalog = mgmt / CATALOG_NAME
        catalog.write_text(SAMPLE_CATALOG, encoding="utf-8")
        print(f"[已生成示例目录] {catalog}")
        print("  → 请作者改写为真实目录并确认冻结后，重新运行本脚本完成初始化。")
        return 0
    if catalog != mgmt / CATALOG_NAME:
        shutil.copyfile(catalog, mgmt / CATALOG_NAME)
        catalog = mgmt / CATALOG_NAME

    # 防覆盖
    ledger = mgmt / "写作进度台账.md"
    if ledger.is_file() and not args.force:
        print(f"[拒绝覆盖] {ledger} 已存在，项目似已初始化。"
              f"确要重来请加 --force（仅覆盖台账/术语台账/指令清单，不动书稿）。")
        return 1

    chapters = parse_catalog(catalog)
    if not chapters:
        print(f"[目录无法解析] {catalog} 未检出任何 '## 第X章 …' 行。请核对格式后重试。")
        return 1
    n_items = sum(len(sec["items"]) for ch in chapters for sec in ch["sections"])
    n_end = sum(1 for ch in chapters for sec in ch["sections"]
                if sec["title"] == "小结")

    # 书名：--title > 目录 H1 中的《…》
    title = args.title
    if not title:
        h1 = next((l.lstrip("# ").strip()
                   for l in catalog.read_text(encoding="utf-8").splitlines()
                   if l.startswith("# ")), "")
        m = re.match(r"^《(.+)》", h1)
        title = m.group(1) if m else (h1 or "未命名书稿")

    today = str(date.today())
    pointer_rows = "\n".join(
        f"| 第{i}章（{ch['prefix']}） | 表{i}-1 | 图{i}-1 |"
        for i, ch in enumerate(chapters, 1))
    config = CONFIG_TMPL.format(
        title=title, cite="GB/T 7714（顺序编码制）",
        catalog_name=CATALOG_NAME,
        skip_kw=json.dumps(SKIP_NAME_KEYWORDS, ensure_ascii=False),
        by_chapter=json.dumps({}, ensure_ascii=False))
    (mgmt / "书稿配置.json").write_text(config, encoding="utf-8")
    ledger.write_text(
        LEDGER_TMPL.format(title=title, today=today, catalog_name=CATALOG_NAME,
                           cite="GB/T 7714（顺序编码制）",
                           pointer_rows=pointer_rows),
        encoding="utf-8")
    (mgmt / "术语与符号一致性台账.md").write_text(TERM_LEDGER_TMPL, encoding="utf-8")
    (mgmt / "写作指令清单.md").write_text(
        gen_instructions(title, chapters), encoding="utf-8")

    print(f"[初始化完成] 项目：{root}")
    print(f"  书名：《{title}》｜章：{len(chapters)}｜小节：{n_items}｜章末小结指令：{n_end}")
    print("  生成文件：00_管理文件/ 下 书稿配置.json、写作进度台账.md、"
          "术语与符号一致性台账.md、写作指令清单.md")
    print("\n下一步（建议由 AI 助手代办）：")
    print("  1. 与作者核对《书稿配置.json》（字数分级），并完成语料接入访谈（四选一，见技能 references/evidence-corpus.md）登记台账 §1；")
    print("  2. 确认第一批次范围后，按技能三步法开工；")
    print(f"  3. 每批次收尾跑：python3 validate_manuscript.py --root \"{root}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
