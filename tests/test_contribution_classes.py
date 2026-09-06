# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 newdeme
"""成果四分类配套测试：genre/discipline/blind_review 配置、学位论文专项文件、
台账 §4b 冻结登记、素材漂移 WARN、未冻结引用 WARN、GB/T 7714—2025 类型标识兼容。"""
import hashlib
import json
import sys
from pathlib import Path

import pytest

from conftest import CATALOG, REPO, SUBSEC_GOOD, run_py, write_subsec

sys.path.insert(0, str(REPO / "scripts"))


def _init(tmp_path, *extra):
    mgmt = tmp_path / "00_管理文件"
    mgmt.mkdir(parents=True, exist_ok=True)
    (mgmt / "专著目录.md").write_text(CATALOG, encoding="utf-8")
    return run_py("init_project.py", str(tmp_path), "--title", "分类测试", *extra)


def _cfg(root):
    return json.loads((root / "00_管理文件" / "书稿配置.json").read_text(encoding="utf-8"))


def test_init_defaults_and_frozen_area(tmp_path):
    r = _init(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    cfg = _cfg(tmp_path)
    assert cfg["genre"] == "monograph"
    assert cfg["discipline"] == "stem"
    assert cfg["blind_review"] is False
    assert (tmp_path / "02_语料" / "定稿数据" / "定稿数据说明.md").is_file()
    ledger = (tmp_path / "00_管理文件" / "写作进度台账.md").read_text(encoding="utf-8")
    assert "## 4b. 素材版本登记" in ledger
    assert "【文体/学科】" in ledger
    assert not (tmp_path / "00_管理文件" / "创新点与成果声明.md").exists()


def test_init_thesis_generates_innovation_ledger(tmp_path):
    r = _init(tmp_path, "--genre", "thesis", "--discipline", "stem", "--blind-review")
    assert r.returncode == 0, r.stdout + r.stderr
    cfg = _cfg(tmp_path)
    assert cfg["genre"] == "thesis"
    assert cfg["discipline"] == "stem"
    assert cfg["blind_review"] is True
    innov = tmp_path / "00_管理文件" / "创新点与成果声明.md"
    assert innov.is_file()
    txt = innov.read_text(encoding="utf-8")
    assert "创新点登记表" in txt and "隐名版处理" in txt


def test_init_genre_choices_rejected(tmp_path):
    mgmt = tmp_path / "00_管理文件"
    mgmt.mkdir(parents=True, exist_ok=True)
    (mgmt / "专著目录.md").write_text(CATALOG, encoding="utf-8")
    r = run_py("init_project.py", str(tmp_path), "--genre", "novel")
    assert r.returncode == 2          # argparse 拒绝非法取值


def _freeze_and_register(root, content="v1 数据\n"):
    """造一份 C-数据素材、快照并登记台账 §4b，返回 (原文件相对名, sha8)。"""
    corpus = root / "02_语料"
    src = corpus / "数据表格" / "试验数据.md"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text(content, encoding="utf-8")
    snap = "试验数据_冻结.md"
    (corpus / "定稿数据" / snap).write_text(content, encoding="utf-8")
    sha8 = hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]
    row = f"- 数据表格/试验数据.md｜{snap}｜{sha8}｜2026-09-04｜1.1.1｜试验参数\n"
    ledger = root / "00_管理文件" / "写作进度台账.md"
    t = ledger.read_text(encoding="utf-8")
    i = t.index("## 4c.")          # §4b 段止于 §4c
    head, tail = t[:i], t[i:]
    j = head.rfind("- （暂无）")
    assert j != -1, "台账 §4b 占位行缺失"
    ledger.write_text(head[:j] + row + head[j + len("- （暂无）"):] + tail,
                      encoding="utf-8")
    return "数据表格/试验数据.md", sha8


def _validate(root):
    return run_py("validate_manuscript.py", "--root", str(root))


def test_drift_warn_when_source_modified(project):
    write_subsec(project, SUBSEC_GOOD)
    _freeze_and_register(project)
    (project / "02_语料" / "数据表格" / "试验数据.md").write_text("v2 改动\n", encoding="utf-8")
    r = _validate(project)
    assert r.returncode == 0            # WARN 不挡收批
    assert "素材漂移" in r.stdout
    assert "试验数据.md" in r.stdout


def test_no_drift_when_untouched(project):
    write_subsec(project, SUBSEC_GOOD)
    _freeze_and_register(project)
    r = _validate(project)
    assert "素材漂移" not in r.stdout
    assert "C-数据证据未冻结" not in r.stdout


def test_unfrozen_author_data_warn(project):
    text = SUBSEC_GOOD.replace("两处引用按首次出现顺序编号。",
                               "两处引用按首次出现顺序编号。试验结果见作者试验数据。")
    write_subsec(project, text)
    r = _validate(project)
    assert r.returncode == 0
    assert "C-数据证据未冻结" in r.stdout
    assert "1.1.1 测试小节.md" in r.stdout
    # 冻结登记后 WARN 消除
    _freeze_and_register(project)
    r = _validate(project)
    assert "C-数据证据未冻结" not in r.stdout


def test_snapshot_missing_warn(project):
    write_subsec(project, SUBSEC_GOOD)
    _freeze_and_register(project)
    (project / "02_语料" / "定稿数据" / "试验数据_冻结.md").unlink()
    r = _validate(project)
    assert "冻结快照缺失" in r.stdout


def test_gbtype_accepts_2025_identifiers():
    from validate_manuscript import check_gb_types
    reflines = [
        "[1] 张三. 某数据集: V1.0[DS/OL]. 国家数据中心 (2026-01-01)[2026-09-01]. http://example.org/ds.",
        "[2] 李四. 某预印本[PP/OL]. arXiv (2026-02-02)[2026-09-01]. http://arxiv.org/abs/x.",
        "[3] 王五. 某奏折: 档号-001[A]. 北京: 中国第一历史档案馆, 1887.",
    ]
    assert check_gb_types(reflines) == []
