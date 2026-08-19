# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 newdeme
"""共享测试夹具：临时项目初始化＋脚本调用助手。"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

CATALOG = """# 《冒烟测试》目录

## 第一章 测试

**1.1 测试节**
- 1.1.1 测试小节

**1.2 小结**
"""

# 合规小节样例：三段式完整、引用按首现顺序、文献带类型标识、字数落在测试档内
SUBSEC_GOOD = """# 1.1.1 测试小节
> （测试文档定位说明）
## 一、写作准备
- 核心论点：测试论点
- 证据清单：见正文引用
## 二、正文
**观点句领起。**这是用于自动化测试的正文段落，长度控制在测试字数档区间之内，
第一处引用挂期刊文献[1]，随后补充专著类论据[2]，两处引用按首次出现顺序编号。
收束段完成本节论述并与下一小节衔接。
## 参考文献
[1] 作者一. 测试文献一[J]. 测试期刊, 2024, 1(1): 1-9.
[2] 作者二. 测试文献二[M]. 北京: 测试出版社, 2023.
"""

SECTION_SUMMARY = """# 第一章 1.1节 测试节 章节总结
> （测试）
## 一、章节总结（正文）
本节总结正文，归纳小节核心结论并衔接下一节，引用本节已引文献[1]。
## 二、参考文献
[1] 作者一. 测试文献一[J]. 测试期刊, 2024, 1(1): 1-9.
"""


def run_py(script: str, *args) -> subprocess.CompletedProcess:
    """以当前解释器运行仓库脚本，捕获输出。"""
    return subprocess.run(
        [sys.executable, str(REPO / "scripts" / script), *args],
        capture_output=True, text=True)


@pytest.fixture
def project(tmp_path) -> Path:
    """初始化最小项目并把字数档调小（小节 30~120／总结 20~100），返回项目根。"""
    mgmt = tmp_path / "00_管理文件"
    mgmt.mkdir(parents=True)
    (mgmt / "专著目录.md").write_text(CATALOG, encoding="utf-8")
    r = run_py("init_project.py", str(tmp_path), "--title", "冒烟测试")
    assert r.returncode == 0, r.stdout + r.stderr
    cfg_path = tmp_path / "00_管理文件" / "书稿配置.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg["word_targets"] = {"default": [30, 120], "by_chapter": {},
                           "section_summary": [20, 100], "chapter_summary": [15, 100]}
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return tmp_path


def write_subsec(root: Path, text: str) -> Path:
    """把小节文件写入 1.1 节目录（不存在则创建），返回文件路径。"""
    d = root / "01_书稿" / "第一章 测试" / "1.1 测试节"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "1.1.1 测试小节.md"
    p.write_text(text, encoding="utf-8")
    return p
