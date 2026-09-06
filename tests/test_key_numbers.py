# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Sheng Chang
"""关键数值一致性测试：台账 §3c 登记解析、首现可溯、关联数据图核对、登记冲突。"""
import hashlib

from conftest import SUBSEC_GOOD, run_py, write_subsec


def _validate(root):
    return run_py("validate_manuscript.py", "--root", str(root))


def _ledger(root):
    return root / "00_管理文件" / "写作进度台账.md"


def _register_3c(root, row):
    p = _ledger(root)
    t = p.read_text(encoding="utf-8")
    i = t.index("## 4.")           # 数值行插到 §3c 段尾（§4 之前），可重复调用
    p.write_text(t[:i] + row + t[i:], encoding="utf-8")


def test_init_creates_3c_and_4c_sections(project):
    t = _ledger(project).read_text(encoding="utf-8")
    assert "## 3c. 关键数值登记" in t
    assert "## 4c. 检索记录" in t
    assert "核验状态" in t                     # §4 缓存行格式含四态列说明
    # 段序：3 < 3b < 3c < 4 < 4b < 4c < 5
    i3, i4, i5 = (t.index(f"## {s}.") for s in ("3", "4", "5"))
    assert i3 < t.index("## 3b.") < t.index("## 3c.") < i4
    assert i4 < t.index("## 4b.") < t.index("## 4c.") < i5


def test_no_registration_no_warning(project):
    write_subsec(project, SUBSEC_GOOD)
    r = _validate(project)
    assert "关键数值" not in r.stdout


def test_traceable_value_passes(project):
    text = SUBSEC_GOOD.replace("收束段完成本节论述并与下一小节衔接。",
                               "收束段完成本节论述，本批平均写作时长 7.5 h。")
    write_subsec(project, text)
    _register_3c(project, "- 7.5 h｜批次平均写作时长｜1.1.1｜-\n")
    r = _validate(project)
    assert "关键数值登记可溯性" not in r.stdout


def test_value_missing_from_manuscript_warns(project):
    write_subsec(project, SUBSEC_GOOD)      # 正文没有 7.5 h
    _register_3c(project, "- 7.5 h｜批次平均写作时长｜1.1.1｜-\n")
    r = _validate(project)
    assert "关键数值登记可溯性" in r.stdout and "7.5 h" in r.stdout


def test_value_in_wrong_subsec_warns(project):
    text = SUBSEC_GOOD.replace("收束段完成本节论述并与下一小节衔接。",
                               "收束段完成本节论述，本批平均写作时长 7.5 h。")
    write_subsec(project, text)
    _register_3c(project, "- 7.5 h｜批次平均写作时长｜1.2.1｜-\n")   # 首现登记错节
    r = _validate(project)
    assert "关键数值登记可溯性" in r.stdout


def test_linked_figure_data_mismatch_warns(project):
    text = SUBSEC_GOOD.replace("收束段完成本节论述并与下一小节衔接。",
                               "收束段完成本节论述，结果如图1-1所示，平均时长 7.5 h。")
    write_subsec(project, text)
    data = project / "02_语料" / "结果.csv"
    data.parent.mkdir(parents=True, exist_ok=True)
    data.write_text("批次,时长\n1,9.9\n2,8.8\n", encoding="utf-8")   # 没有 7.5
    sha = hashlib.sha256(data.read_bytes()).hexdigest()[:8]
    t = _ledger(project).read_text(encoding="utf-8")
    i3c = t.index("## 3c.")                      # 图行插到 §3b 段尾（§3c 之前）
    j = t.rfind("- （暂无）", 0, i3c)
    assert j != -1
    fig_row = (f"- 图1-1｜数据图｜02_语料/结果.csv｜{sha}｜"
               f'{{"chart":"bar","x":"批次","y":"时长","title":"时长"}}｜2026-09-05\n')
    t = t[:j] + fig_row + t[j + len("- （暂无）"):]
    _ledger(project).write_text(t, encoding="utf-8")
    _register_3c(project, "- 7.5 h｜批次平均写作时长｜1.1.1｜图1-1\n")
    r = _validate(project)
    assert "关键数值不一致" in r.stdout and "图1-1" in r.stdout
    data.write_text("批次,时长\n1,7.5\n2,8.8\n", encoding="utf-8")   # 数据对上（sha 变了会另报漂移，属预期）
    r2 = _validate(project)
    assert "关键数值不一致" not in r2.stdout


def test_conflicting_registrations_warn(project):
    text = SUBSEC_GOOD.replace("收束段完成本节论述并与下一小节衔接。",
                               "收束段完成本节论述，本批平均写作时长 7.5 h。")
    write_subsec(project, text)
    _register_3c(project, "- 7.5 h｜批次平均写作时长｜1.1.1｜-\n")
    _register_3c(project, "- 7.8 h｜批次平均写作时长｜1.1.1｜-\n")
    r = _validate(project)
    assert "关键数值登记冲突" in r.stdout
