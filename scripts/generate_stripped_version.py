#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 newdeme
"""
generate_stripped_version.py —— 书稿剥离版生成器（monograph-writing 技能组件）
========================================================================
用途：把书稿目录（缺省 01_书稿/，章节→节两级文件夹）下的三段式小节文件
（## 一、写作准备 → ## 二、正文 → ## 参考文献）与二段式节级总结
（## 一、章节总结 → ## 二、参考文献）剥离为"纯正文版"：
仅保留 小节标题（H1）＋ 正文 ＋ 参考文献。

规则：
  - 类型A（含"## 一、写作准备"）：丢弃写作准备区，保留正文与参考文献；
  - 类型B（节级总结）：保留章节总结与参考文献两部分；
  - 参考文献标题统一为 "## 参考文献"；正文内容一字不改；
  - 源文件不做任何改动；重复运行安全（先清空对应章旧剥离版再重建）。

输出（写入配置 stripped_dir，缺省 04_剥离版书稿/）：
  1. 镜像树：与书稿目录同构的逐篇剥离文件（1:1 可溯源）；
  2. 章合并稿：每章一份（Y.Z 节 → 节内小节 → 节级总结 → 章末小结），可直接整章复制进 Word。

用法（在项目根目录运行）：
    python3 generate_stripped_version.py --root .            # 全部章节
    python3 generate_stripped_version.py --root . 第一章 第三章  # 仅指定章节（目录名前缀匹配）
"""
import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

REF_HEADING_OUT = "## 参考文献"


def load_config(root: Path):
    cfg = {"manuscript_dir": "01_书稿", "stripped_dir": "04_剥离版书稿"}
    cfile = root / "00_管理文件" / "书稿配置.json"
    if cfile.is_file():
        user = json.loads(cfile.read_text(encoding="utf-8"))
        cfg.update({k: user[k] for k in cfg if k in user})
    return cfg


def parse_and_strip(text, relpath):
    """解析单篇书稿文件，返回剥离后的文本；结构异常时抛 ValueError。"""
    lines = text.splitlines()
    h2 = [(i, l.strip()) for i, l in enumerate(lines) if l.startswith("## ")]
    heads = [h[1] for h in h2]

    has_prep = any(h.startswith("## 一、写作准备") for h in heads)
    body_pat = re.compile(r"^## 二、正文\s*$")
    ref_pat = re.compile(r"^## (?:二、)?参考文献")
    sum_pat = re.compile(r"^## 一、章节总结")

    if has_prep:
        body_i = next((i for i, h in h2 if body_pat.match(h)), None)
        ref_i = next((i for i, h in h2 if ref_pat.match(h)), None)
        if body_i is None or ref_i is None or ref_i <= body_i:
            raise ValueError(f"类型A结构不完整：正文或参考文献标题缺失/顺序异常，H2={heads}")
        body = lines[body_i + 1: ref_i]
    else:
        sum_i = next((i for i, h in h2 if sum_pat.match(h)), None)
        ref_i = next((i for i, h in h2 if ref_pat.match(h)), None)
        if sum_i is None or ref_i is None or ref_i <= sum_i:
            raise ValueError(f"无法识别结构：既非三段式也非节级总结二段式，H2={heads}")
        body = lines[sum_i + 1: ref_i]

    refs = lines[ref_i + 1:]
    title = lines[0].strip()  # H1 标题

    out = [title, ""]
    out.extend(trim_edges(body))
    out += ["", REF_HEADING_OUT, ""]
    out.extend(trim_edges(refs))
    return "\n".join(out).rstrip() + "\n"


def trim_edges(ls):
    """去除列表首尾的空行与孤立分隔线（---），中间内容原样保留。"""
    ls = list(ls)
    while ls and ls[0].strip() in ("", "---"):
        ls.pop(0)
    while ls and ls[-1].strip() in ("", "---"):
        ls.pop()
    return ls


def section_key(name):
    m = re.match(r"^(\d+)\.(\d+)", name)
    return (int(m.group(1)), int(m.group(2))) if m else (999, 999)


def subsection_key(name):
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", name)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (999, 999, 999)


def collect_reading_order(src_ch):
    """按阅读顺序收集一章全部文件：Y.Z 节目录 → 节内小节 → 节级总结 → 章末小结。"""
    ordered = []
    sec_dirs = sorted(
        (d for d in os.listdir(src_ch) if os.path.isdir(os.path.join(src_ch, d))),
        key=section_key)
    for sd in sec_dirs:
        if "小结" in sd:      # 章末小结目录由下方统一处理
            continue
        sd_path = os.path.join(src_ch, sd)
        files = [f for f in os.listdir(sd_path) if f.endswith(".md")]
        subs = sorted((f for f in files if re.match(r"^\d+\.\d+\.\d+", f)),
                      key=subsection_key)
        summaries = sorted(f for f in files if f.startswith("第") and "章节总结" in f)
        others = [f for f in files if f not in subs and f not in summaries]
        if others:
            print(f"    [提示] 节目录 {sd} 含未分类文件（跳过）：{others}")
        for f in subs + summaries:
            ordered.append(os.path.join(sd_path, f))
    # 章末小结：根级 'X.Y 小结.md' 文件或 'X.Y 小结/' 目录
    for entry in sorted(os.listdir(src_ch), key=section_key):
        if "小结" not in entry:
            continue
        p = os.path.join(src_ch, entry)
        if os.path.isfile(p) and p not in ordered:
            ordered.append(p)
        elif os.path.isdir(p):
            for rt, _dirs, fns in os.walk(p):
                for fn in sorted(fns):
                    if fn.endswith(".md"):
                        ordered.append(os.path.join(rt, fn))
    return ordered


def merge_chapter(ch, stripped_texts):
    parts = [f"# {ch}"]
    for _, t in stripped_texts:
        parts.append(t.rstrip())
    return "\n\n---\n\n".join(parts) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(description="书稿剥离版生成（详细说明见文件头注释）")
    ap.add_argument("--root", default=".", help="项目根目录")
    ap.add_argument("chapters", nargs="*", help="可选：仅处理目录名以指定前缀开头的章节")
    args = ap.parse_args(argv)

    root = Path(args.root).expanduser().resolve()
    cfg = load_config(root)
    src = root / cfg["manuscript_dir"]
    dst = root / cfg["stripped_dir"]
    if not src.is_dir():
        print(f"[目录不存在] {src}（请在项目根目录运行，或检查配置 manuscript_dir）")
        return 1
    dst.mkdir(parents=True, exist_ok=True)

    chapters = sorted(
        d for d in os.listdir(src)
        if os.path.isdir(os.path.join(src, d)) and d.startswith("第"))
    if args.chapters:
        chapters = [c for c in chapters
                    if any(c.startswith(f) for f in args.chapters)]
    if not chapters:
        print("未找到匹配的章节目录，退出。")
        return 1

    print(f"待处理章节：{len(chapters)} 个（源：{src} → 输出：{dst}）")
    total = 0
    for ch in chapters:
        ch_total, ch_err = 0, []
        src_ch = os.path.join(src, ch)
        dst_ch = os.path.join(dst, ch)
        if os.path.isdir(dst_ch):
            shutil.rmtree(dst_ch)
        ordered_paths = collect_reading_order(src_ch)
        stripped_texts = []
        for src_path in ordered_paths:
            rel = os.path.relpath(src_path, src)
            try:
                text = open(src_path, encoding="utf-8").read()
                stripped = parse_and_strip(text, rel)
            except ValueError as e:
                ch_err.append(f"  [跳过] {rel}: {e}")
                continue
            out_path = os.path.join(dst, rel)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(stripped)
            stripped_texts.append((rel, stripped))
            ch_total += 1
        if stripped_texts:
            merged = merge_chapter(ch, stripped_texts)
            with open(os.path.join(dst, f"{ch}.md"), "w", encoding="utf-8") as f:
                f.write(merged)
        total += ch_total
        print(f"  {ch}: 剥离 {ch_total} 篇 ＋ 章合并稿 1 份")
        for msg in ch_err:
            print(msg)
        if ch_err:
            print(f"  !! {ch} 有 {len(ch_err)} 篇结构异常未剥离，需人工核查")
    print(f"完成：共生成剥离版 {total} 篇 → {dst}")
    print("下一步可运行 merge_to_word.py 生成合并 Word 稿。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
