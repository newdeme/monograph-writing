# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 newdeme
"""generate_stripped_version.py：剥离"写作准备"、保留正文与参考文献、生成章合并稿。"""
from conftest import SECTION_SUMMARY, SUBSEC_GOOD, run_py, write_subsec

ANCHOR = "两处引用按首次出现顺序编号"


def test_strip_removes_prep_keeps_body(project):
    write_subsec(project, SUBSEC_GOOD)
    sec_dir = project / "01_书稿" / "第一章 测试" / "1.1 测试节"
    (sec_dir / "第一章 1.1节 测试节 章节总结.md").write_text(SECTION_SUMMARY, encoding="utf-8")

    r = run_py("generate_stripped_version.py", "--root", str(project))
    assert r.returncode == 0, r.stdout + r.stderr

    mirror = project / "04_剥离版书稿" / "第一章 测试" / "1.1 测试节" / "1.1.1 测试小节.md"
    assert mirror.is_file(), "剥离镜像未生成"
    stripped = mirror.read_text(encoding="utf-8")
    assert "写作准备" not in stripped, "剥离版仍含写作准备区"
    assert "论点树" not in stripped
    assert ANCHOR in stripped, "正文内容缺失"
    assert "## 参考文献" in stripped
    assert "[1] 作者一. 测试文献一[J]" in stripped

    merged = project / "04_剥离版书稿" / "第一章 测试.md"
    assert merged.is_file(), "章合并稿未生成"
    merged_text = merged.read_text(encoding="utf-8")
    assert "1.1.1 测试小节" in merged_text
    assert "写作准备" not in merged_text
