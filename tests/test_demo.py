# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 newdeme
"""examples/demo-project 一致性：提交的书稿校验全绿；提交的剥离版＝脚本再生成产物。

剥离脚本输出不含时间戳（确定性），故可逐文件比对；不一致时提示跑 examples/make_demo.py。
"""
import shutil
import sys
from pathlib import Path

from conftest import REPO, run_py

DEMO = REPO / "examples" / "demo-project"


def test_demo_validates():
    r = run_py("validate_manuscript.py", "--root", str(DEMO))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ERROR 0 项" in r.stdout


def test_demo_stripped_deterministic(tmp_path):
    copy = tmp_path / "demo-project"
    shutil.copytree(DEMO, copy)
    shutil.rmtree(copy / "04_剥离版书稿")

    r = run_py("generate_stripped_version.py", "--root", str(copy))
    assert r.returncode == 0, r.stdout + r.stderr

    committed = sorted((DEMO / "04_剥离版书稿").rglob("*.md"))
    assert committed, "仓库中未提交剥离版"
    for p in committed:
        rel = p.relative_to(DEMO / "04_剥离版书稿")
        q = copy / "04_剥离版书稿" / rel
        assert q.is_file(), f"再生成缺失：{rel}"
        assert p.read_text(encoding="utf-8") == q.read_text(encoding="utf-8"), (
            f"剥离版与提交内容不一致：{rel}——请在仓库根目录运行 "
            f"`python3 examples/make_demo.py` 后重新提交")
