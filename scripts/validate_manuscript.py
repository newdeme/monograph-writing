#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 newdeme
"""
validate_manuscript.py —— 专著书稿校验脚本（monograph-writing 技能组件）
========================================================================
每批次收尾必跑。零参数即可运行：在项目根目录（含 00_管理文件/书稿配置.json）执行
    python3 validate_manuscript.py
也可显式指定：
    python3 validate_manuscript.py --root <项目根目录>
    python3 validate_manuscript.py --root <项目根目录> --manuscript <书稿目录>

检查项（全部由《书稿配置.json》驱动）：
  1. 文件命名与分类（小节 X.Y.Z / 二级条目 X.Y / 节级总结 / 章末小结）
  2. 文件结构完整性（三段式：写作准备 / 正文 / 参考文献）
  3. 正文字数 vs 分级目标（默认/按章/特殊档；区间外 ±tolerance 为 WARN，再往外为 ERROR）
  4. 引用编号：正文（含表格阅读序）须覆盖 1..N 且按首次出现顺序递增；
     参考文献列表编号连续、条目数与正文最大引用号一致
  5. 参考文献条目含文献类型标识（[J]/[M]/[C]/[R]/[D]/[S]/[EB/OL] 等，WARN 级，可关）
  6. 表/图编号：章内序号从 1 开始、无跳号（按小节顺序合并检查）
  7. 未匹配任何命名规则的文件提示人工确认
  8. 成果四分类配套（WARN 级）：台账 §4b 登记素材的漂移检查（原文件 hash 与冻结时不符）；
     正文使用"作者试验数据/本文数据"类标注而 §4b 无任何冻结登记时的提醒
  9. 关键数值一致性（WARN 级，台账 §3c）：登记数值首现可溯、关联数据图的数据文件核对、
     同一数据多口径冲突——语义级变体（7.5 h vs 7小时30分）须人工终检

输出：逐文件结果（OK / WARN / ERROR）＋末尾汇总；存在 ERROR 时退出码 1。
字数口径：中文字符（含中文标点）逐字计，连续西文/数字串计 1；
        仅统计叙述文字（正文部分，不含写作准备、参考文献及 Markdown 表格行）。
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

CN_RE = re.compile(r"[一-鿿　-〿＀-￯]")
WEST_RE = re.compile(r"[A-Za-z0-9]+(?:[.\-][A-Za-z0-9]+)*")
SUBSEC_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+) .+\.md$")
SEC_RE = re.compile(r"^(\d+)\.(\d+) .+\.md$")
SUMMARY_RE = re.compile(r"^第[一二三四五六七八九十百]+章 (\d+)\.(\d+)\s*节 .+ 章节总结\.md$")
CITE_RE = re.compile(r"\[([\d,\s\-]+)\]")
GBTYPE_RE = re.compile(r"\[[A-Z]{1,2}(?:/[A-Z]{1,2})?\]")
TABLE_RE = re.compile(r"表\s*(\d+)\s*[-–—]\s*(\d+)")
FIG_RE = re.compile(r"图\s*(\d+)\s*[-–—]\s*(\d+)")

DEFAULT_CONFIG = {
    "manuscript_dir": "01_书稿",
    "excluded_dirs": ["00_管理文件", "02_语料", "03_归档素材", "04_剥离版书稿", ".claude", ".git"],
    "skip_name_keywords": ["台账", "校核报告", "评估报告", "专著目录", "写作指令清单", "说明"],
    "word_targets": {"default": [1500, 2000], "by_chapter": {},
                     "section_summary": [600, 800], "chapter_summary": [300, 500]},
    "special_tiers": [],      # [{"pattern": "…", "target": [lo, hi], "reason": "…"}]
    "exempt_patterns": [],    # 完全跳过校验（待修复外部文件）
    "tolerance": 0.15,
    "check_citation_style": True,
}


def load_config(root: Path) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    cfile = root / "00_管理文件" / "书稿配置.json"
    if cfile.is_file():
        try:
            user = json.loads(cfile.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"[配置文件语法错误] {cfile}")
            print(f"  出了什么：第 {e.lineno} 行第 {e.colno} 列附近 JSON 语法有误（{e.msg}）。")
            print("  常见原因：上一行行尾漏了逗号／多写了逗号；字符串两端误用了中文引号；多余的换行。")
            print("  怎么改：用编辑器打开该文件定位到该行补上逗号（或改回英文双引号 \"），")
            print(f"          改完先自检：python3 -m json.tool \"{cfile}\" ——无报错再重跑本脚本。")
            sys.exit(1)
        except UnicodeDecodeError:
            print(f"[配置文件编码错误] {cfile} 不是 UTF-8 编码，无法读取。")
            print("  怎么改：用编辑器打开该文件，另存为 UTF-8 编码后重跑本脚本。")
            sys.exit(1)
        cfg.update({k: v for k, v in user.items() if v is not None})
        wt = cfg.get("word_targets") or {}
        merged = dict(DEFAULT_CONFIG["word_targets"])
        merged.update(wt)
        for k in ("by_chapter",):
            merged[k] = {**DEFAULT_CONFIG["word_targets"][k], **(wt.get(k) or {})}
        cfg["word_targets"] = merged
    return cfg


def count_words(text: str) -> int:
    prose = "\n".join(l for l in text.splitlines()
                      if not l.lstrip().startswith("|"))
    return len(CN_RE.findall(prose)) + len(WEST_RE.findall(prose))


def extract_body(text: str, kind: str):
    """返回 (正文, 错误列表)；正文不含参考文献与写作准备部分。"""
    errs = []
    if kind == "summary":
        starts = ["## 一、章节总结（正文）", "## 一、章节总结"]
        ends = ["## 二、参考文献", "## 参考文献"]
        need = ["## 一、章节总结"]
    else:
        starts = ["## 二、正文"]
        ends = ["## 参考文献"]
        need = ["## 一、写作准备", "## 二、正文", "## 参考文献"]
    for h in need:
        if h not in text:
            errs.append(f"缺少必需章节标题: {h}")
    if kind != "summary" and "## 一、写作准备" not in text and not errs:
        pass  # 已由 need 覆盖
    if errs:
        return text, errs
    s = next((text.index(x) for x in starts if x in text), None)
    e = next((text.index(x) for x in ends if x in text), None)
    if s is None or e is None or e <= s:
        return text, ["正文/参考文献分段无法解析"]
    return text[s:e], []


def check_citations(body: str, reflines: list):
    """引用编号连续性检查。返回 (错误, 警告)。"""
    errs, warns = [], []
    cited_order = []
    for m in CITE_RE.finditer(body):
        for part in m.group(1).split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                a, b = part.split("-")[:2]
                try:
                    nums = range(int(a), int(b) + 1)
                except ValueError:
                    continue
            else:
                nums = [int(part)]
            for n in nums:
                if n not in cited_order:
                    cited_order.append(n)
    ref_nums = []
    for line in reflines:
        m = re.match(r"^\s*[\[［](\d+)[\]］]", line)
        if m:
            ref_nums.append(int(m.group(1)))
    if not cited_order:
        errs.append("正文未检出任何 [n] 形式引用")
        return errs, warns
    n_max = max(cited_order)
    if sorted(cited_order) != list(range(1, n_max + 1)):
        missing = sorted(set(range(1, n_max + 1)) - set(cited_order))
        errs.append(f"引用编号未连续覆盖 1..{n_max}，缺失: {missing}")
    if cited_order != sorted(cited_order):
        first_bad = next(
            cited_order[i] for i in range(1, len(cited_order))
            if cited_order[i] < max(cited_order[:i + 1])
            and cited_order[i] not in cited_order[:i])
        errs.append(f"引用编号非按首次出现顺序递增（首个乱序号: [{first_bad}]）")
    if not ref_nums:
        errs.append("参考文献列表为空或无法解析编号")
    else:
        if ref_nums != list(range(1, len(ref_nums) + 1)):
            errs.append(f"参考文献列表编号不连续: {ref_nums}")
        if len(ref_nums) != n_max:
            errs.append(f"参考文献条目数({len(ref_nums)})与正文最大引用号({n_max})不一致")
    return errs, warns


def check_gb_types(reflines: list):
    warns = []
    for line in reflines:
        m = re.match(r"^\s*[\[［](\d+)[\]］]\s*(.+)$", line.strip())
        if m and not GBTYPE_RE.search(m.group(2)):
            warns.append(
                f"参考文献 [{m.group(1)}] 未检出文献类型标识"
                f"（GB/T 7714 的 [J]/[M]/[C]/[R]/[D]/[S] 等）")
    return warns


def word_verdict(n: int, lo: int, hi: int, tol: float):
    if n < lo * (1 - tol):
        return "ERROR", f"字数 {n}，远低于目标 {lo}~{hi}"
    if n > hi * (1 + tol):
        return "ERROR", f"字数 {n}，远高于目标 {lo}~{hi}"
    if n < lo or n > hi:
        return "WARN", f"字数 {n}，目标 {lo}~{hi}（区间外但容差内）"
    return "OK", f"字数 {n}（目标 {lo}~{hi}）"


FROZEN_ROW_RE = re.compile(r"^- (.+?)｜(.+?)｜([0-9a-fA-F]{8})｜(.+?)｜(.+)$")
FIG_ROW_RE = re.compile(
    r"^- (图\d+-\d+)｜(数据图|概念草图|作者供图)｜(.+?)｜([0-9a-fA-F]{8}|-)｜(.+?)｜(\S+)$")


def parse_fig_ledger(root: Path):
    """解析台账 §3b 图表证据登记 → {图号: (类型, 来源, sha8, 日期)}。"""
    ledger = root / "00_管理文件" / "写作进度台账.md"
    if not ledger.is_file():
        return {}
    figs, in3b = {}, False
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if line.startswith("## 3b"):
            in3b = True
            continue
        if in3b and line.startswith("## "):
            break
        if not in3b:
            continue
        m = FIG_ROW_RE.match(line)
        if m and not m.group(1).startswith("（"):
            figs[m.group(1)] = (m.group(2), m.group(3), m.group(4), m.group(6))
    return figs


def parse_frozen_ledger(root: Path):
    """解析台账 §4b 素材版本登记 → [(原文件, 快照名, sha8, 日期, 章节)]；无登记返回 []。"""
    ledger = root / "00_管理文件" / "写作进度台账.md"
    if not ledger.is_file():
        return []
    rows, in4b = [], False
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if line.startswith("## 4b"):
            in4b = True
            continue
        if in4b and line.startswith("## "):
            break
        if not in4b:
            continue
        m = FROZEN_ROW_RE.match(line)
        if m and not m.group(1).startswith("（"):
            rows.append((m.group(1).strip(), m.group(2).strip(),
                         m.group(3).lower(), m.group(4).strip(), m.group(5).strip()))
    return rows


NUM_ROW_RE = re.compile(r"^- (.+?)｜(.+?)｜(.+?)｜(.+)$")


def parse_number_ledger(root: Path):
    """解析台账 §3c 关键数值登记 → [(数值串, 含义, 首现小节, 关联图表)]；无登记返回 []。"""
    ledger = root / "00_管理文件" / "写作进度台账.md"
    if not ledger.is_file():
        return []
    rows, in3c = [], False
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if line.startswith("## 3c"):
            in3c = True
            continue
        if in3c and line.startswith("## "):
            break
        if not in3c:
            continue
        m = NUM_ROW_RE.match(line)
        if m and not m.group(1).startswith("（"):
            rows.append((m.group(1).strip(), m.group(2).strip(),
                         m.group(3).strip(), m.group(4).strip()))
    return rows


def check_key_numbers(root: Path, num_rows, fig_rows, ms_dir: Path):
    """关键数值一致性检查（references/polish-workflow.md §3/§7；字符串级）。

    检查三件事：①登记可溯——首现小节文件存在且正文含该数值串；
    ②图表核对——登记关联图表（数据图）时，其数据文件内容含该数值的数字部分；
    ③登记冲突——同一首现小节+同一含义出现两条不同数值串。
    语义级变体（如「7.5 h」vs「7小时30分」）脚本查不了，终检时人工过一遍。"""
    warns = []
    # 收集全部书稿正文文本（含表格行——数字常出现在表里）
    body_cache = {}
    for p in sorted(ms_dir.rglob("*.md")):
        try:
            body_cache[p.name] = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            body_cache[p.name] = ""
    seen = {}
    for value, meaning, subsec, figs in num_rows:
        # ① 首现可溯
        hit = next((fn for fn, txt in body_cache.items()
                    if fn.startswith(subsec) and value in txt), None)
        if hit is None:
            any_hit = next((fn for fn, txt in body_cache.items() if value in txt), None)
            if any_hit:
                warns.append(f"关键数值登记可溯性：数值「{value}」在书稿中见于「{any_hit}」，"
                             f"但登记的首现小节「{subsec}」未检出——更正 §3c 首现列，或把该处写法统一为登记串")
            else:
                warns.append(f"关键数值登记可溯性：「{value}」（{meaning}）在全部书稿中未检出"
                             f"——数值已改则同步更新 §3c 登记串（先改台账再改正文）")
        # ② 图表数据核对
        for fig_id in [f.strip() for f in figs.split("、")] if figs and figs != "-" else []:
            info = fig_rows.get(fig_id)
            if not info:
                continue  # 图未登记 §3b 已由图表证据卡检查报过，不重复
            _kind, src, _sha, _d = info
            src_path = root / src
            if not src_path.is_file():
                continue  # 来源缺失已由证据卡检查报过
            num_core = next((s for s in re.findall(r"\d+(?:\.\d+)?", value)), None)
            if num_core and num_core not in src_path.read_text(encoding="utf-8", errors="ignore"):
                warns.append(f"关键数值不一致：§3c 登记「{value}」（{meaning}）关联 {fig_id}，"
                             f"但其数据文件 {src} 中未检出数字 {num_core}——正文与图各说各话，须复核")
        # ③ 登记冲突
        key = (subsec, meaning)
        if key in seen and seen[key] != value:
            warns.append(f"关键数值登记冲突：「{meaning}」（{subsec}）登记了两个数值"
                         f"「{seen[key]}」与「{value}」——同一数据全书只能有一个口径")
        seen[key] = value
    return warns


def check_frozen_materials(root: Path, rows):
    """成果四分类配套检查（references/evidence-corpus.md §8）。返回 WARN 列表。"""
    warns = []
    corpus = root / "02_语料"
    for orig, snap, sha8, _date, _chapters in rows:
        src = corpus / orig
        if not src.is_file():
            warns.append(
                f"素材漂移：台账 §4b 登记的原文件不存在：{orig}"
                f"（快照在 02_语料/定稿数据/{snap}，误删可从快照恢复）")
            continue
        cur = hashlib.sha256(src.read_bytes()).hexdigest()[:8]
        if cur != sha8:
            warns.append(
                f"素材漂移：{orig} 当前内容与冻结时（{sha8}）不一致——依赖它的章节须复核；"
                f"数据确已更新则把新版快照到 02_语料/定稿数据/ 并在 §4b 追加一行登记")
        if not (corpus / "定稿数据" / snap).is_file():
            warns.append(
                f"冻结快照缺失：02_语料/定稿数据/{snap} 不存在（台账 §4b 登记 {orig}）——"
                f"请补放快照或更正 §4b 登记")
    return warns


def main():
    ap = argparse.ArgumentParser(
        description="专著书稿校验（详细说明见文件头注释）",
        epilog="示例：在项目根目录直接跑 python3 validate_manuscript.py；"
               "在别处跑时加 --root <项目根目录>。报错看不懂时，把完整输出复制给 AI 助手代修。")
    ap.add_argument("--root", default=".", help="项目根目录（含 00_管理文件/书稿配置.json）")
    ap.add_argument("--manuscript", default=None,
                    help="书稿目录（缺省取配置 manuscript_dir）")
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    cfg = load_config(root)
    root_ms = root / cfg["manuscript_dir"]
    ms_dir = Path(args.manuscript).expanduser().resolve() if args.manuscript else root_ms
    if not ms_dir.is_dir():
        print(f"[目录不存在] {ms_dir}")
        print(f"  请确认在项目根目录运行，或用 --manuscript 指定书稿目录。")
        return 1

    wt = cfg["word_targets"]
    default_tier = tuple(wt.get("default", [1500, 2000]))
    by_chapter = {int(k): tuple(v) for k, v in (wt.get("by_chapter") or {}).items()}
    sum_tier = tuple(wt.get("section_summary", [600, 800]))
    end_tier = tuple(wt.get("chapter_summary", [300, 500]))
    special_tiers = [(re.compile(t["pattern"]), tuple(t["target"]), t.get("reason", ""))
                     for t in cfg.get("special_tiers") or []]
    exempt = [re.compile(p) for p in cfg.get("exempt_patterns") or []]
    tol = float(cfg.get("tolerance", 0.15))
    skip_kw = cfg.get("skip_name_keywords") or []
    excl_dirs = set(cfg.get("excluded_dirs") or [])

    files = sorted(ms_dir.rglob("*.md"))
    if not files:
        print(f"未发现 Markdown 文件: {ms_dir}")
        return 1

    total_err = total_warn = 0
    n_ok = n_exempt = 0
    chapter_tabs, chapter_figs = {}, {}
    author_data_files = []      # 正文使用"作者试验数据/本文数据"标注的文件（成果四分类检查用）
    print(f"== 专著书稿校验：{ms_dir} ==\n")
    for p in files:
        if any(k in p.name for k in skip_kw):
            continue
        if excl_dirs.intersection(p.parts):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            print(f"[ERROR] {p.name}（编码错误）")
            print(f"    - 出了什么：文件不是 UTF-8 编码（位置 {e.start} 附近无法解码）。")
            print(f"    - 怎么改：用编辑器打开「{p}」另存为/转换为 UTF-8 编码后重跑本脚本。")
            total_err += 1
            continue
        errs, warns, kind, chap = [], [], None, None

        if m := SUBSEC_RE.match(p.name):
            kind, chap = "subsec", int(m.group(1))
            lo, hi = end_tier if "小结" in p.name else by_chapter.get(chap, default_tier)
        elif m := SUMMARY_RE.match(p.name):
            kind = "summary"
            lo, hi = sum_tier
        elif m := SEC_RE.match(p.name):
            kind, chap = "secend", int(m.group(1))
            lo, hi = end_tier if "小结" in p.name else by_chapter.get(chap, default_tier)
        else:
            print(f"[SKIP] {p.name} —— 未匹配任何命名规则（请人工确认）")
            continue

        if any(rx.match(p.name) for rx in exempt):
            n_exempt += 1
            print(f"[豁免] {p.name} —— 命中 exempt_patterns（如为修复完成的文件，请从配置移出）")
            continue

        body, berrs = extract_body(text, kind)
        errs += berrs
        if re.search(r"作者试验数据|作者实测|本文数据", body or ""):
            author_data_files.append(p.name)
        for pat, tier, _r in special_tiers:      # 特殊档优先于章档
            if pat.match(p.name):
                lo, hi = tier
                break
        n = count_words(body)
        lvl, msg = word_verdict(n, lo, hi, tol)
        if lvl == "ERROR":
            errs.append(msg)
        elif lvl == "WARN":
            warns.append(msg)

        mref = re.search(r"^##\s*(?:[一二]、\s*)?参考文献.*$", text, re.M)
        ref_part = text[mref.start():] if mref else ""
        reflines = [l for l in ref_part.splitlines()
                    if re.match(r"^\s*[\[［]\d+[\]］]", l)]
        cerrs, cwarns = check_citations(body, reflines)
        errs += cerrs
        warns += cwarns
        if cfg.get("check_citation_style", True):
            warns += check_gb_types(reflines)

        if kind in ("subsec", "secend") and chap:
            for _t, d in TABLE_RE.findall(body):
                chapter_tabs.setdefault(chap, []).append(int(d))
            for _t, d in FIG_RE.findall(body):
                chapter_figs.setdefault(chap, []).append(int(d))

        tag = {"subsec": "小节", "summary": "节级总结", "secend": "二级条目"}[kind]
        if "小结" in p.name:
            tag = "章末小结"
        if errs:
            total_err += len(errs)
            print(f"[ERROR] {p.name} ({tag})")
            for e in errs:
                print(f"    - {e}")
        elif warns:
            total_warn += len(warns)
            print(f"[WARN ] {p.name} ({tag})")
            for w in warns:
                print(f"    - {w}")
        else:
            n_ok += 1
            print(f"[OK   ] {p.name} ({tag})，字数 {n}，引用 {len(reflines)} 条")

    for chap, ds in sorted(chapter_tabs.items()):
        if sorted(set(ds)) != list(range(1, max(ds) + 1)):
            missing = sorted(set(range(1, max(ds) + 1)) - set(ds))
            print(f"[ERROR] 第{chap}章 表编号跳号: 已出现 {sorted(set(ds))}，缺失 {missing}")
            total_err += 1
    for chap, ds in sorted(chapter_figs.items()):
        if ds and sorted(set(ds)) != list(range(1, max(ds) + 1)):
            missing = sorted(set(range(1, max(ds) + 1)) - set(ds))
            print(f"[ERROR] 第{chap}章 图编号跳号: 已出现 {sorted(set(ds))}，缺失 {missing}")
            total_err += 1

    # ---- 图表证据卡检查（references/figure-guide.md）----
    fig_rows = parse_fig_ledger(root)
    referenced = {f"图{c}-{d}" for c, ds in chapter_figs.items() for d in ds}
    for fig_id in sorted(referenced - set(fig_rows)):
        print(f"[WARN] 图无证据卡登记：正文引用了 {fig_id}，但台账 §3b 未登记该图"
              f"（数据图须登记数据文件+校验和，概念图登记 .mmd 草稿；格式见 references/figure-guide.md）")
        total_warn += 1
    for fig_id, (kind, src, sha8, _date) in sorted(fig_rows.items()):
        src_path = (root / src)
        if not src_path.is_file():
            print(f"[WARN] 图表证据卡来源缺失：{fig_id} 的 {src} 不存在（核对 §3b 来源列）")
            total_warn += 1
            continue
        if kind == "数据图" and sha8 != "-":
            cur = hashlib.sha256(src_path.read_bytes()).hexdigest()[:8]
            if cur != sha8.lower():
                print(f"[WARN] 图数据漂移：{fig_id} 的数据文件 {src} 当前（{cur}）与登记（{sha8}）不一致"
                      f"——依赖该图的章节须复核后重生成")
                total_warn += 1

    # ---- 成果四分类配套检查（references/evidence-corpus.md §8）----
    frozen_rows = parse_frozen_ledger(root)
    for w in check_frozen_materials(root, frozen_rows):
        print(f"[WARN] {w}")
        total_warn += 1

    # ---- 关键数值一致性检查（references/polish-workflow.md；台账 §3c）----
    num_rows = parse_number_ledger(root)
    for w in check_key_numbers(root, num_rows, fig_rows, ms_dir):
        print(f"[WARN] {w}")
        total_warn += 1
    if author_data_files and not frozen_rows:
        print("[WARN] C-数据证据未冻结：以下文件正文标注了「作者试验数据/本文数据」，"
              "但台账 §4b 无任何冻结登记：")
        for name in author_data_files:
            print(f"    - {name}")
        print("    怎么处理：数据已定稿 → 快照复制到 02_语料/定稿数据/ 并在台账 §4b 登记一行；"
              "仍在迭代 → 属正常在研状态，本 WARN 记入台账 §6（说明理由）即可收批；"
              "确需著录进参考文献表 → 冻结后按 [DS/OL] 著录（见 evidence-corpus.md §8）。")
        total_warn += len(author_data_files)

    print(f"\n== 汇总：OK {n_ok} 个文件，ERROR {total_err} 项，WARN {total_warn} 项，"
          f"豁免 {n_exempt} 个 ==")
    if total_err:
        print("存在 ERROR：请修复后复跑本脚本，直到 ERROR 清零再收批。")
    elif total_warn:
        print("无 ERROR。WARN 逐条判断：可接受的记入台账 §6 并说明理由，不可接受的修复。")
    else:
        print("全部通过 ✅")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())
