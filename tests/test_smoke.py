# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 newdeme
"""最小冒烟测试：脚本可编译、初始化流程可跑通（供 CI 与本地自检）。"""
import compileall
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_scripts_compile():
    """全部脚本可被当前 Python 编译（语法级检查）。"""
    ok = compileall.compile_dir(str(REPO / "scripts"), quiet=1)
    assert ok, "存在无法编译的脚本"


def test_init_project_smoke():
    """init_project.py 全流程冒烟：生成骨架、双台账、02_语料/ 说明文件。"""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        mgmt = root / "00_管理文件"
        mgmt.mkdir(parents=True)
        (mgmt / "专著目录.md").write_text(
            "# 《冒烟测试》目录\n\n## 第一章 测试\n\n**1.1 测试节**\n"
            "- 1.1.1 测试小节\n\n**1.2 小结**\n", encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "init_project.py"),
             str(root), "--title", "冒烟测试"],
            capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        assert (root / "00_管理文件" / "写作进度台账.md").is_file()
        assert (root / "00_管理文件" / "术语与符号一致性台账.md").is_file()
        assert (root / "00_管理文件" / "写作指令清单.md").is_file()
        assert (root / "02_语料" / "把文献放这里.md").is_file()
