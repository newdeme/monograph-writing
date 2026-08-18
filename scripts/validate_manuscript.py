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

输出：逐文件结果（OK / WARN / ERROR）＋末尾汇总；存在 ERROR 时退出码 1。
字数口径：中文字符（含中文标点）逐字计，连续西文/数字串计 1；
        仅统计叙述文字（正文部分，不含写作准备、参考文献及 Markdown 表格行）。
"""
import argparse
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
    "excluded_dirs": ["00_管理文件", "03_归档素材", "04_剥离版书稿", ".claude", ".git"],
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
        user = json.loads(cfile.read_text(encoding="utf-8"))
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


def main():
    ap = argparse.ArgumentParser(description="专著书稿校验（详细说明见文件头注释）")
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
    print(f"== 专著书稿校验：{ms_dir} ==\n")
    for p in files:
        if any(k in p.name for k in skip_kw):
            continue
        if excl_dirs.intersection(p.parts):
            continue
        text = p.read_text(encoding="utf-8")
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
