# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 newdeme
"""validate_manuscript.py 的正反用例：干净书稿通过，各类违规被逐一检出。"""
from conftest import SUBSEC_GOOD, run_py, write_subsec


def _validate(root):
    return run_py("validate_manuscript.py", "--root", str(root))


def test_validate_clean_passes(project):
    write_subsec(project, SUBSEC_GOOD)
    r = _validate(project)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "全部通过" in r.stdout
    assert "1.1.1 测试小节.md" in r.stdout


def test_validate_citation_order(project):
    text = SUBSEC_GOOD.replace(
        "第一处引用挂期刊文献[1]，随后补充专著类论据[2]",
        "先出现的引用挂专著文献[2]，随后才是期刊文献[1]")
    write_subsec(project, text)
    r = _validate(project)
    assert r.returncode == 1
    assert "引用编号非按首次出现顺序递增" in r.stdout


def test_validate_missing_heading(project):
    write_subsec(project, SUBSEC_GOOD.replace("## 一、写作准备\n", ""))
    r = _validate(project)
    assert r.returncode == 1
    assert "缺少必需章节标题: ## 一、写作准备" in r.stdout


def test_validate_refcount_mismatch(project):
    # 正文只引 [1]，但文献表多列一条 → 条目数与最大引用号不一致
    text = SUBSEC_GOOD.replace("，随后补充专著类论据[2]", "")
    write_subsec(project, text)
    r = _validate(project)
    assert r.returncode == 1
    assert "参考文献条目数(" in r.stdout and "与正文最大引用号" in r.stdout


def test_validate_wordcount_low(project):
    text = SUBSEC_GOOD.replace(
        "**观点句领起。**这是用于自动化测试的正文段落，长度控制在测试字数档区间之内，\n"
        "第一处引用挂期刊文献[1]，随后补充专著类论据[2]，两处引用按首次出现顺序编号。\n"
        "收束段完成本节论述并与下一小节衔接。",
        "**过短。**正文仅一句[1]。")
    write_subsec(project, text)
    r = _validate(project)
    assert r.returncode == 1
    assert "远低于目标" in r.stdout


def test_validate_table_numbering(project):
    text = SUBSEC_GOOD.replace(
        "收束段完成本节论述并与下一小节衔接。",
        "收束段引用两张表：如表1-1与表1-3所示。\n\n**表1-1 测试表一（本节归纳）**\n"
        "| a | b |\n|---|---|\n| 1 | 2 |\n\n**表1-3 测试表三（本节归纳）**\n"
        "| a | b |\n|---|---|\n| 3 | 4 |")
    write_subsec(project, text)
    r = _validate(project)
    assert r.returncode == 1
    assert "表编号跳号" in r.stdout
