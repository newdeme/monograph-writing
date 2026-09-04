# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Sheng Chang
"""绘图功能测试：05_图表 骨架、台账 §3b 证据卡、validate 图登记与漂移检查、
generate_figures.py 生成与覆盖保护（matplotlib 缺失时生成类用例自动跳过）。"""
import hashlib
import json
from pathlib import Path

import pytest

from conftest import SUBSEC_GOOD, run_py, write_subsec


def _validate(root):
    return run_py("validate_manuscript.py", "--root", str(root))


def test_init_creates_figure_scaffold(project):
    for sub in ("数据图", "草稿", "定稿"):
        assert (project / "05_图表" / sub).is_dir()
    ledger = (project / "00_管理文件" / "写作进度台账.md").read_text(encoding="utf-8")
    assert "## 3b. 图表证据登记" in ledger
    cfg = json.loads((project / "00_管理文件" / "书稿配置.json").read_text(encoding="utf-8"))
    assert cfg["figure"]["dpi"] == 300 and cfg["figure"]["format"] == "png"


def _register_3b(root, row):
    p = root / "00_管理文件" / "写作进度台账.md"
    t = p.read_text(encoding="utf-8")
    i = t.index("## 4.")           # §3b 段止于 §4
    head, tail = t[:i], t[i:]
    j = head.rfind("- （暂无）")
    assert j != -1
    p.write_text(head[:j] + row + head[j + len("- （暂无）"):] + tail, encoding="utf-8")


def test_validate_warns_unregistered_figure(project):
    text = SUBSEC_GOOD.replace("收束段完成本节论述并与下一小节衔接。",
                               "收束段完成本节论述并与下一小节衔接，结果如图1-1所示。")
    write_subsec(project, text)
    r = _validate(project)
    assert r.returncode == 0
    assert "图无证据卡登记" in r.stdout and "图1-1" in r.stdout
    # 登记后 WARN 消除（作者供图形态）
    _register_3b(project, "- 图1-1｜作者供图｜05_图表/定稿/图1-1 示意.tif｜-｜作者提供｜2026-09-04\n")
    (project / "05_图表" / "定稿" / "图1-1 示意.tif").write_bytes(b"x")
    r = _validate(project)
    assert "图无证据卡登记" not in r.stdout


def test_validate_warns_figure_data_drift(project):
    text = SUBSEC_GOOD.replace("收束段完成本节论述并与下一小节衔接。",
                               "收束段完成本节论述并与下一小节衔接，结果如图1-1所示。")
    write_subsec(project, text)
    data = project / "02_语料" / "结果.csv"
    data.parent.mkdir(parents=True, exist_ok=True)
    data.write_text("方法,精度\nA,0.9\nB,0.85\n", encoding="utf-8")
    sha = hashlib.sha256(data.read_bytes()).hexdigest()[:8]
    _register_3b(
        project,
        f'- 图1-1｜数据图｜02_语料/结果.csv｜{sha}｜{{"chart":"bar","x":"方法","y":"精度","title":"精度对比"}}｜2026-09-04\n')
    assert "图数据漂移" not in _validate(project).stdout
    data.write_text("方法,精度\nA,0.95\nB,0.8\n", encoding="utf-8")   # 篡改
    r = _validate(project)
    assert "图数据漂移" in r.stdout and "图1-1" in r.stdout


def test_validate_warns_missing_figure_source(project):
    write_subsec(project, SUBSEC_GOOD)
    _register_3b(project, "- 图1-2｜概念草图｜05_图表/草稿/图1-2 机制.mmd｜-｜Mermaid 草稿｜2026-09-04\n")
    r = _validate(project)
    assert "图表证据卡来源缺失" in r.stdout


def test_generate_figures_end_to_end(project):
    pytest.importorskip("matplotlib")
    data = project / "02_语料" / "结果.csv"
    data.parent.mkdir(parents=True, exist_ok=True)
    data.write_text("方法,精度\nA,0.92\nB,0.85\nC,0.88\n", encoding="utf-8")
    sha = hashlib.sha256(data.read_bytes()).hexdigest()[:8]
    _register_3b(
        project,
        f'- 图1-1｜数据图｜02_语料/结果.csv｜{sha}｜{{"chart":"bar","x":"方法","y":"精度","title":"精度对比"}}｜2026-09-04\n')
    r = run_py("generate_figures.py", "--root", str(project))
    assert r.returncode == 0, r.stdout + r.stderr
    out = project / "05_图表" / "数据图" / "图1-1.png"
    assert out.is_file() and out.stat().st_size > 1000
    # 覆盖保护：再次运行默认跳过
    r = run_py("generate_figures.py", "--root", str(project))
    assert "已存在" in r.stdout and "--force" in r.stdout
    # 数据漂移后拒绝生成
    data.write_text("方法,精度\nA,0.99\n", encoding="utf-8")
    r = run_py("generate_figures.py", "--root", str(project), "--force")
    assert "数据漂移" in r.stdout


def test_generate_figures_no_registration(project):
    r = run_py("generate_figures.py", "--root", str(project))
    assert r.returncode == 1
    assert "[无可生成]" in r.stdout and "§3b" in r.stdout
