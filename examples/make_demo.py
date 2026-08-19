#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 newdeme
"""make_demo.py —— 示例项目再生成脚本

复跑示例项目的"校验＋剥离版生成"两步（不跑 init_project.py——示例已含管理文件，
init 会因台账已存在而拒绝执行）。修改 examples/demo-project/01_书稿/ 内容后运行
本脚本，可重新生成 04_剥离版书稿/ 并确认校验通过；若 04_ 有变化，请一并提交，
保持"提交的剥离版＝脚本产物"（CI 的确定性测试据此比对）。

用法（在仓库根目录）：
    python3 examples/make_demo.py
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEMO = REPO / "examples" / "demo-project"


def run(label, *cmd):
    print(f"\n== {label} ==")
    r = subprocess.run([sys.executable, *cmd], cwd=REPO)
    if r.returncode != 0:
        sys.exit(f"[失败] {label} 退出码 {r.returncode}；请修复后重跑本脚本。")


def main():
    if not DEMO.is_dir():
        sys.exit(f"[目录缺失] {DEMO}")
    run("① 校验示例书稿（ERROR 须清零）",
        str(REPO / "scripts" / "validate_manuscript.py"), "--root", str(DEMO))
    run("② 重新生成剥离版（04_剥离版书稿/）",
        str(REPO / "scripts" / "generate_stripped_version.py"), "--root", str(DEMO))
    print("\n完成。若 04_剥离版书稿/ 有改动，请一并提交（保持与脚本产物一致）。")
    print("如需示例合并 Word 稿（不入库，仅供本地预览/Release 附件）：")
    print(f"    python3 scripts/merge_to_word.py --root \"{DEMO}\"")


if __name__ == "__main__":
    main()
