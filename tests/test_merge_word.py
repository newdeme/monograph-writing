# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 newdeme
"""merge_to_word.py：合并 Word 稿生成（需 python-docx，无依赖时自动跳过）。

docx 生成只写入字体名等 XML 属性、不渲染字体，故无中文字体的 Linux CI 亦可运行。
"""
import pytest

docx = pytest.importorskip("docx")

from conftest import SUBSEC_GOOD, run_py, write_subsec

TABLE_VARIANT = SUBSEC_GOOD.replace(
    "收束段完成本节论述并与下一小节衔接。",
    "收束段附一张归纳表。\n\n**表1-1 测试表（本节归纳）**\n| 列A | 列B |\n|---|---|\n| 甲 | 乙 |")


def test_merge_word_generates_docx(project):
    write_subsec(project, TABLE_VARIANT)
    assert run_py("generate_stripped_version.py", "--root", str(project)).returncode == 0
    r = run_py("merge_to_word.py", "--root", str(project))
    assert r.returncode == 0, r.stdout + r.stderr

    out = project / "04_剥离版书稿" / "冒烟测试（合并稿）.docx"
    assert out.is_file(), "合并 Word 稿未生成"

    document = docx.Document(str(out))
    assert document.core_properties.title == "冒烟测试"
    headings = [p.text for p in document.paragraphs if p.style.name.startswith("Heading")]
    assert any(h.startswith("1.1.1") for h in headings), headings
    assert any(h.startswith("第一章") for h in headings)
    assert len(document.tables) >= 1, "Markdown 表未转换为 Word 表格"
