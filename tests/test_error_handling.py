# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 newdeme
"""异常路径用例：坏输入必须得到中文三段式提示（出了什么/怎么改），不得裸 traceback。

对应 TRACE 评测报告 R 维度（异常处理 4.3 / 运行稳定性 4.3）的修复：
  - 配置 JSON 写坏 → 中文提示＋行号＋自检命令
  - 非 UTF-8 书稿 → 中文提示＋转码指引
  - init 把目录文件当根目录 → 用法纠正
  - strip 全部失败 → 报失败并退出码 1
  - merge 遇坏文件 → 跳过保盘（Word 稿仍生成）；节目录漂移 → 编号前缀回退
"""
import json

import pytest

from conftest import CATALOG, SUBSEC_GOOD, run_py, write_subsec

try:
    import docx  # noqa: F401
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


def _break_config(project):
    """在配置第 manuscript_dir 行制造"漏行尾逗号"——最常见的手改事故。"""
    cfg = project / "00_管理文件" / "书稿配置.json"
    good = json.loads(cfg.read_text(encoding="utf-8"))
    broken = json.dumps(good, ensure_ascii=False, indent=2).replace(
        '"manuscript_dir": "01_书稿",', '"manuscript_dir": "01_书稿"')
    assert broken != json.dumps(good, ensure_ascii=False, indent=2)
    cfg.write_text(broken, encoding="utf-8")


def test_broken_config_chinese_hint(project):
    _break_config(project)
    r = run_py("validate_manuscript.py", "--root", str(project))
    assert r.returncode == 1
    assert "[配置文件语法错误]" in r.stdout
    assert "怎么改" in r.stdout and "json.tool" in r.stdout
    assert "Traceback" not in r.stdout + r.stderr


def test_non_utf8_manuscript_hint(project):
    d = project / "01_书稿" / "第一章 测试" / "1.1 测试节"
    d.mkdir(parents=True, exist_ok=True)
    (d / "1.1.1 测试小节.md").write_bytes(
        "# 1.1.1 测试小节\n\n## 二、正文\n中文正文\n\n## 参考文献\n".encode("gbk"))
    r = run_py("validate_manuscript.py", "--root", str(project))
    assert r.returncode == 1
    assert "编码错误" in r.stdout and "UTF-8" in r.stdout
    assert "Traceback" not in r.stdout + r.stderr


def test_init_root_is_file_hint(tmp_path):
    cat = tmp_path / "目录.md"
    cat.write_text(CATALOG, encoding="utf-8")
    r = run_py("init_project.py", str(cat))
    assert r.returncode == 1
    assert "[参数错误]" in r.stdout and "--catalog" in r.stdout
    assert "Traceback" not in r.stdout + r.stderr


def test_strip_all_failed_reports_and_exits_1(project):
    d = project / "01_书稿" / "第一章 测试" / "1.1 测试节"
    d.mkdir(parents=True, exist_ok=True)
    (d / "1.1.1 测试小节.md").write_bytes(
        "# 1.1.1 测试小节\n\n## 二、正文\n中文\n\n## 参考文献\n".encode("gbk"))
    r = run_py("generate_stripped_version.py", "--root", str(project))
    assert r.returncode == 1
    assert "未生成任何剥离版" in r.stdout
    assert "UTF-8" in r.stdout


@pytest.mark.skipif(not HAS_DOCX, reason="需要 python-docx")
def test_merge_skips_bad_unit_and_still_saves(project):
    write_subsec(project, SUBSEC_GOOD)
    assert run_py("generate_stripped_version.py", "--root", str(project)).returncode == 0
    bad = (project / "04_剥离版书稿" / "第一章 测试" / "1.1 测试节"
           / "1.1.1 测试小节.md")
    bad.write_text(bad.read_text(encoding="utf-8").replace(
        "## 参考文献\n", "参考文献如下\n", 1), encoding="utf-8")
    r = run_py("merge_to_word.py", "--root", str(project))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "未能并入" in r.stdout and "生成完成" in r.stdout
    assert "Traceback" not in r.stdout + r.stderr
    assert list((project / "04_剥离版书稿").glob("*.docx"))  # Word 稿仍已落盘


@pytest.mark.skipif(not HAS_DOCX, reason="需要 python-docx")
def test_merge_section_dir_drift_recovers(project):
    write_subsec(project, SUBSEC_GOOD)
    assert run_py("generate_stripped_version.py", "--root", str(project)).returncode == 0
    sd = project / "04_剥离版书稿" / "第一章 测试" / "1.1 测试节"
    sd.rename(sd.parent / "1.1 测试")  # 目录名漂移：去掉"节"字
    r = run_py("merge_to_word.py", "--root", str(project))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "节目录 1.1" in r.stdout          # 编号前缀回退匹配记录
    assert "已并入小节: 1" in r.stdout
