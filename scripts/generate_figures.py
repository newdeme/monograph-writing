#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Sheng Chang
"""
generate_figures.py —— 数据图生成器（monograph-writing 技能组件）
========================================================================
用途：按台账 §3b「图表证据登记」中的**数据图**行，从作者的数据文件生成统计图。
红线：**图只能从登记的数据文件生成，禁止自编数据点**——图内编造数字比正文更
隐蔽且难校验。每图在台账 §3b 有一张「图表证据卡」（图号/数据文件+校验和/
生成配方/日期），改数据后重跑本脚本即可重生成。

支持的图类型（配方见下）：柱状图 bar / 折线图 line / 散点图 scatter /
箱线图 box / 直方图 hist。概念示意图/架构图**不归本脚本**——AI 只产
Mermaid 文本草稿放 05_图表/草稿/，成稿由作者重绘（见 references/figure-guide.md）。

依赖：matplotlib 为可选依赖（`pip3 install matplotlib` 或让 AI 用
`uv run --with matplotlib` 代跑）。中文字体自动探测（PingFang/思源/黑体等），
探测失败仍出图但中文可能显示为方框——按提示安装字体。

用法（在项目根目录运行）：
    python3 generate_figures.py --root .                # 生成 §3b 全部数据图
    python3 generate_figures.py --root . 图1-1 图2-3    # 只生成指定图
    python3 generate_figures.py --root . --force        # 覆盖已有图（慎用，见 §9 变更单规则）

台账 §3b 数据图行的「生成配方」列写 JSON，例如：
    {"chart":"bar","x":"方法","y":"精度","title":"各方法精度对比"}
    {"chart":"line","x":"轮次","y":"损失","hue":"模型"}     # hue 可选：分组列
覆盖保护：已存在的图默认跳过并提示走变更单；确要覆盖加 --force。
"""
import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROW_RE = re.compile(
    r"^- (图\d+-\d+)｜(数据图|概念草图|作者供图)｜(.+?)｜([0-9a-fA-F]{8}|-)｜(.+?)｜(\S+)$")
CHARTS = ("bar", "line", "scatter", "box", "hist")
FONT_CANDIDATES = ("PingFang SC", "Songti SC", "Hiragino Sans GB", "Noto Sans CJK SC",
                   "Source Han Sans SC", "Source Han Sans", "SimHei", "Microsoft YaHei")


def parse_fig_rows(root: Path):
    """解析台账 §3b 图表证据登记 → [（图号, 类型, 来源, sha8, 配方文本, 日期）]。"""
    ledger = root / "00_管理文件" / "写作进度台账.md"
    if not ledger.is_file():
        return []
    rows, in3b = [], False
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if line.startswith("## 3b"):
            in3b = True
            continue
        if in3b and line.startswith("## "):
            break
        if not in3b:
            continue
        m = ROW_RE.match(line)
        if m and not m.group(1).startswith("（"):
            rows.append(m.groups())
    return rows


def sha8_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:8]


def main():
    ap = argparse.ArgumentParser(
        description="数据图生成器（详细说明见文件头注释）",
        epilog="示例：python3 generate_figures.py --root . 图1-1；配方与红线见 references/figure-guide.md。")
    ap.add_argument("--root", default=".", help="项目根目录")
    ap.add_argument("figures", nargs="*", help="可选：只生成指定图号（如 图1-1）")
    ap.add_argument("--force", action="store_true",
                    help="覆盖已存在的图（默认跳过并提示走变更单）")
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    rows = parse_fig_rows(root)
    data_rows = [r for r in rows if r[1] == "数据图"]
    if args.figures:
        data_rows = [r for r in data_rows if r[0] in set(args.figures)]
    if not data_rows:
        print("[无可生成] 台账 §3b 未登记任何数据图（或未命中指定的图号）。")
        print("  怎么做：把数据文件放 02_语料/，在台账 §3b 登记一行（格式见 references/figure-guide.md），"
              "再跑本脚本；概念示意图走 05_图表/草稿/ 的 Mermaid 草稿流程。")
        return 1

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
    except ImportError:
        print("[缺依赖] 生成数据图需要安装 matplotlib，请在终端执行：")
        print("    pip3 install matplotlib")
        print("  （或让 AI 助手用 `uv run --with matplotlib` 代跑；装好后重新运行本脚本即可。）")
        return 1

    font = next((f.name for f in font_manager.fontManager.ttflist
                 if f.name in FONT_CANDIDATES), "")
    if font:
        plt.rcParams["font.family"] = font
        plt.rcParams["axes.unicode_minus"] = False
    else:
        print("[字体提示] 未探测到中文字体（PingFang/思源/黑体等），图中中文可能显示为方框。")
        print("  怎么改：安装任一候选字体，或在《书稿配置.json》figure.font 指定已装字体名后重跑。")

    cfg = {}
    cfg_file = root / "00_管理文件" / "书稿配置.json"
    if cfg_file.is_file():
        try:
            cfg = json.loads(cfg_file.read_text(encoding="utf-8")).get("figure") or {}
        except Exception as e:
            print(f"[配置文件语法错误] {cfg_file}：{e}——修复后重跑（自检：python3 -m json.tool 该文件）。")
            return 1
    fmt = cfg.get("format", "png")
    dpi = int(cfg.get("dpi", 300))
    if cfg.get("font"):
        plt.rcParams["font.family"] = cfg["font"]

    out_dir = root / "05_图表" / "数据图"
    out_dir.mkdir(parents=True, exist_ok=True)
    made = skipped = drifted = bad = 0
    for fig_id, _kind, src, reg_sha, recipe_txt, _date in data_rows:
        src_path = (root / src).resolve()
        if not src_path.is_file():
            print(f"[跳过] {fig_id}：数据文件不存在 {src_path}（核对台账 §3b 的来源列）")
            bad += 1
            continue
        cur = sha8_of(src_path)
        if cur != reg_sha.lower():
            print(f"[跳过] {fig_id}：数据漂移——{src} 当前（{cur}）与登记（{reg_sha}）不一致。")
            print("  怎么改：数据确已更新 → 用新校验和在 §3b 更新该行后重跑；误改 → 从 02_语料/定稿数据/ 快照恢复。")
            drifted += 1
            continue
        try:
            recipe = json.loads(recipe_txt)
        except Exception as e:
            print(f"[跳过] {fig_id}：生成配方不是合法 JSON（{e}）——§3b 配方列格式见 references/figure-guide.md。")
            bad += 1
            continue
        chart = recipe.get("chart")
        if chart not in CHARTS:
            print(f"[跳过] {fig_id}：不支持的图类型 {chart!r}（可选：{'/'.join(CHARTS)}；概念图走 Mermaid 草稿流程）。")
            bad += 1
            continue
        try:
            if src_path.suffix.lower() == ".json":
                records = json.loads(src_path.read_text(encoding="utf-8"))
                if isinstance(records, dict):
                    records = [dict(zip(records.keys(), v)) for v in zip(*records.values())]
            else:
                with open(src_path, encoding="utf-8-sig", newline="") as f:
                    records = list(csv.DictReader(f))
        except Exception as e:
            print(f"[跳过] {fig_id}：数据文件读取失败（{e}）——仅支持 CSV（含表头）与 JSON（对象数组/按列）。")
            bad += 1
            continue

        out = out_dir / f"{fig_id}.{fmt}"
        if out.exists() and not args.force:
            print(f"[跳过] {fig_id}：{out.name} 已存在——覆盖需走变更单或加 --force（防静默覆盖人工后处理过的图）。")
            skipped += 1
            continue

        xk, yk, hue = recipe.get("x"), recipe.get("y"), recipe.get("hue")
        fig, ax = plt.subplots(figsize=recipe.get("figsize", (6, 4)))
        try:
            if chart == "hist":
                ax.hist([float(r[yk]) for r in records], bins=int(recipe.get("bins", 20)))
            else:
                series = {}
                for r in records:
                    key = str(r.get(hue, "")) if hue else ""
                    series.setdefault(key, ([], []))
                    series[key][0].append(r[xk])
                    series[key][1].append(float(r[yk]) if chart != "bar" else float(r[yk]))
                for key, (xs, ys) in series.items():
                    getattr(ax, chart)(xs, ys, label=key or None)
                if hue:
                    ax.legend()
            ax.set_xlabel(str(xk or ""))
            if chart != "hist":
                ax.set_ylabel(str(yk or ""))
            ax.set_title(recipe.get("title", fig_id))
            fig.tight_layout()
            fig.savefig(out, dpi=dpi)
        finally:
            plt.close(fig)
        print(f"[生成] {fig_id} ← {src}（{chart}，校验和 {cur}）→ {out}")
        made += 1

    print(f"\n== 汇总：生成 {made}，跳过 {skipped + drifted + bad}（已存在 {skipped}／数据漂移 {drifted}／配置问题 {bad}）==")
    if drifted:
        print("存在数据漂移：依赖这些图的章节须复核后再重生成（红线见 references/figure-guide.md）。")
    return 0 if (made or skipped) and not bad else (1 if not made else 0)


if __name__ == "__main__":
    sys.exit(main())
