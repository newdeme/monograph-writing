# monograph-writing — Academic Monograph Batch-Writing Assistant

**English** · [简体中文](README.zh-CN.md)

[![Tests](https://github.com/newdeme/monograph-writing/actions/workflows/python-package.yml/badge.svg)](https://github.com/newdeme/monograph-writing/actions/workflows/python-package.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)](#quick-start-3-steps)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
[![Release](https://img.shields.io/github/v/release/newdeme/monograph-writing?include_prereleases)](https://github.com/newdeme/monograph-writing/releases)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> Turn "writing a 12-chapter book" into an AI-assisted, script-validated, multi-author pipeline — with a hard no-fabrication guarantee for every citation.

**Want to see it in action first?** Browse the complete example project: [examples/demo-project](examples/README.md) — every artifact from project initialization, section writing, and validation through stripped-clean-copy generation.

---

## 1. Who is this for?

Anyone writing a **long-form academic manuscript**: professors writing academic monographs, researchers writing technical books, engineers writing industry handbooks, graduate teams co-writing textbooks, and **doctoral/master's students writing theses (blind review included, and thesis-to-book conversion)** — especially if:

- the book has a dozen chapters and hundreds of thousands of words, and **cannot be written in a single AI conversation**;
- you use AI to write but **fear it fabricating references and data**;
- multiple people / multiple sessions work in relay, and you **fear inconsistency and lost progress**.
- you are writing a **thesis** and fear the AI can't tell *your own contributions* from *citable references* — misattributed innovation points, blind-review anonymization, and plagiarism-check pitfalls.

If any of these sound familiar, this skill was designed for you. **No programming knowledge is required at any point** — your AI assistant runs every script for you.

## 2. What problems does it solve?

| Pain point | What this skill does |
|---|---|
| AI "forgets" over long documents | Progress ledger persisted to files; seamless continuation across sessions and co-authors |
| AI fabricates references | Academic red lines + every citation verified against the source + nothing citable outside your approved corpus |
| Your references are scattered; the AI can't reach them | Bring-your-own corpus: the AI only searches materials you provide (see Section 4) |
| Citation & figure numbering drift into chaos | Validator script checks first-appearance order, continuity, and figure/table numbering — a batch isn't "done" until errors reach zero |
| Fear of manuscript data leakage | All scripts run locally — no network, no telemetry, no data collection (see Section 6) |
| Word count spirals out of control | Per-chapter word-count tiers, measured automatically (prose only) |
| Final assembly is painful | One command generates the stripped clean copy and a fully-styled merged Word manuscript |
| Can't tell "my own work" from "citable references" | Contribution classification: your published work is cited with a relation note; unpublished data stays as material (freezable into a citable dataset); unpublished drafts never masquerade as references |
| Writing a thesis (blind review, innovation points) | Thesis mode: innovation-point register, publications-to-chapters relations, blind-review anonymization checklist, plagiarism-check discipline |
| AI invents data in figures | Figure red line: statistical charts are generated only from registered data files (evidence cards + checksums + drift detection); concept diagrams get Mermaid drafts for you to redraw |
| Multi-author relay descends into chaos | Collaboration protocol: the progress ledger + a handover note travel with the workspace; successors continue from the ledger cache with an identical workflow (**theses excluded** — same-author multi-session relay and advisor comments only; see the ethics note in Section 9) |

## 3. Quick Start (3 steps)

**Step 1: Install**

If you use a command line (requires Node.js):

```bash
npx skills add newdeme/monograph-writing
```

No command line? Copy this sentence and paste it into your AI assistant — it will do everything:

> Please install the monograph-writing skill from GitHub for me: clone the repository https://github.com/newdeme/monograph-writing, then copy only the three items the skill needs — SKILL.md, references/, and scripts/ — into a monograph-writing/ folder in your skill library (skip tests/, examples/, docs/ and .github/ — they are repository development files), confirm the skill is recognized, and tell me how to get started.

Works with any AI assistant that supports the Agent Skills open specification (Claude Code, Claude Agent SDK, Cherry Studio, …). Start a new conversation after installing.

**Step 2: Prepare your table of contents**

Put your book outline into one Markdown file (your AI can format it for you; see a complete example in [examples/demo-project](examples/demo-project/00_管理文件/专著目录.md)):

```markdown
# Your Book Title — Table of Contents

## Chapter 1 Title

**1.1 Section Title**
- 1.1.1 Subsection Title
- 1.1.2 Subsection Title

**1.2 Section Title**
…

**1.N Summary**
```

**Step 3: Say one sentence to your AI assistant**

> "Initialize my monograph project with the monograph-writing skill; the outline is at xxx.md"

The AI runs `init_project.py` to scaffold the project, then confirms word-count tiers and your evidence-corpus setup with you. After that, every time you say "**continue**", it advances to the next batch according to the ledger. You get a report after each batch: files written, validation results, and a preview of the next batch.

## 4. Bring-Your-Own Evidence Corpus (signature feature)

The two biggest fears when writing with AI: **fabricated references**, and **your materials being out of the AI's reach**. This skill solves both: you put your literature into a corpus beforehand, and the AI only searches what you gave it, verifying every citation against the original before it enters the manuscript.

At initialization, the "corpus onboarding interview" offers four choices (upgradeable at any time):

| Option | One-line description | Best for |
|---|---|---|
| ① AI-assistant knowledge base | Build a knowledge base inside your AI assistant app and upload your literature (any app with knowledge-base features) | Large collections, semantic search |
| ② Zotero or another reference manager | Designate an existing collection | Researchers already using one |
| ③ In-project `02_语料/` folder | Created automatically at init — just drag files in. **Any format: PDF, Word, Excel, Markdown, TXT; you decide what goes in and how it's organized** (a usage note ships inside the folder) | Anyone; the simplest start |
| ④ Not yet | Write the argument skeleton first, connect a corpus later (degraded mode: the AI cites only references you have personally verified) | Authors still collecting literature |

The laziest path: send the files to your AI assistant and say "**organize these into the project's 02_语料 folder, grouped by theme**".

The boundary of your corpus = the boundary of **evidence**: every document you put in should support your argument. What may enter the **reference list** is further governed by contribution classification — published work by others and your own published work are citable (the latter with a relation note), while your own unpublished data/drafts stay as writing material by default (see the FAQ below and `references/evidence-corpus.md` §8). Setup steps for each option and upgrade paths: [`references/evidence-corpus.md`](references/evidence-corpus.md).

## 5. The five automation scripts (your AI runs them; humans can read them)

| Script | What it does | When |
|---|---|---|
| `scripts/init_project.py` | Scaffolds the project from the frozen outline (config + two ledgers + instruction list) | Once, at the start |
| `scripts/validate_manuscript.py` | Validates naming / structure / word counts / citation numbering / figure-table numbering | After every batch |
| `scripts/generate_stripped_version.py` | Strips the "preparation" sections; generates clean-copy mirror tree + per-chapter merged files | After a chapter is finalized |
| `scripts/generate_figures.py` | Generates statistical charts from registered data files per ledger §3b evidence cards (no invented data points) | When you need data figures (requires `pip3 install matplotlib`) |
| `scripts/merge_to_word.py` | Produces a single, fully-styled Word manuscript with TOC field | When you need to deliver (requires `pip3 install python-docx`) |

All project parameters live in one file — `00_管理文件/书稿配置.json`. Change word-count targets or add exemption tiers there; the scripts never need editing.

Note: script output and generated ledger templates are currently in Chinese (functionality is language-independent; internationalization is on the roadmap).

## 6. Data privacy & technical facts

- **Your data never leaves your computer**: all four scripts run locally — **no network, no telemetry, no data collection**. Your manuscript, outline, and ledgers stay on your own disk. Literature search goes through your own AI assistant and knowledge base, under your control.
- **Minimal dependencies**: pure Python standard library (any Python 3 ≥ 3.9); two optional dependencies as needed — `python-docx` for Word merging, `matplotlib` for data figures (your AI can install and run them).
- **Platform compatibility**: follows the Agent Skills open specification; works with any compliant AI assistant.
- **Reporting issues**: script bugs and security concerns go to GitHub Issues.

## 7. Core design principles

1. **The ledger is the state**: progress, conventions, numbering pointers, verified references — all recorded in project files on disk, not in conversations. Switch sessions, co-authors, or computers without losing anything.
2. **Batch-by-batch progress**: one section directory = one batch (all subsections + a section summary). Small deliveries; validation must reach zero errors before a batch closes, so errors never accumulate into disasters.
3. **Judgment separated from execution**: the author is the academic authority (arguments, evidence selection, final calls); the AI is the writing partner and process executor — it never replaces the author's judgment and never fabricates evidence.
4. **Layered summaries against forgetting**: section summaries (600–800 words) → chapter summaries written *only* from the section summaries, avoiding the context loss of re-reading entire chapters.
5. **Preparation kept with the prose**: every subsection file carries its argument tree and evidence list (three-part structure) for auditability during review; stripped automatically at book assembly.

## 8. Project structure

```
your-book/
├── 00_管理文件/            outline, config, progress ledger, terminology ledger, instruction list
├── 01_书稿/第X章 章标题/Y.Z 节标题/   the whole manuscript (grows batch by batch)
├── 02_语料/                your evidence corpus (PDF/Word/Excel/Markdown — you decide)
├── 03_归档素材/            external drafts (go through the repair workflow; never used directly)
├── 04_剥离版书稿/          clean copies + merged Word manuscript (script-generated)
└── 05_图表/                figures: data plots (script) / drafts (Mermaid) / finals (author)
```

## 9. Multi-author collaboration

> **An academic-ethics red line first**: multi-author collaboration applies to **monographs, textbooks, technical books, collected reports** — works that can bear multiple authors. **A thesis must never be co-written.** In thesis projects, "multiple people" means only: (1) the same author relaying across sessions/devices via the ledger; (2) an advisor's review comments flowing through annotations. Chapter content must be the degree candidate's own; using the relay machinery to ghostwrite a thesis is academic misconduct.

- Each co-author owns several chapters; everyone follows the same method (this skill *is* the standard).
- Handover: the progress ledger + a handover note travel with the workspace.
- When the corpus can't travel with the files, the incoming author uses only the ledger's "verified references cache" (§4 of the ledger); new references go through the corpus owner — **better to cite less than to cite wrong**.

## 10. FAQ

**Q: I have a pile of references (mixed PDF/Word/Excel/Markdown). How do I let the AI use them?**
Simplest: put them all into the `02_语料/` folder created at initialization (a usage note is inside). Any format, your call on content. Then tell the AI: "the corpus is in 02_语料/ — search and verify against it when writing." For large collections or semantic search, upgrade to an AI knowledge base or Zotero (see Section 4). In every mode the AI cites only corpus materials, verified one by one against the originals.

**Q: Will my manuscript be uploaded or collected?**
No. All four scripts run locally on your computer — no network, no telemetry, no data collection. Manuscripts and ledgers stay on your disk. Literature search goes through your own AI assistant and knowledge base (see Section 6).

**Q: I can't use a command line at all. Can I still use this?**
Yes. Installation is one copy-pasted sentence to your AI assistant; after that, all scripts are run by the assistant — you just talk ("continue", "next chapter", "set chapter 2 to 1200–1800 words").

**Q: Can I use a citation style other than GB/T 7714?**
Yes. GB/T 7714 (the Chinese national standard, sequential numbering) is the default. Change `citation_style` in `书稿配置.json` and set `check_citation_style` to `false` (that check is tailored to GB/T 7714 type identifiers).

**Q: Why is citation checking so strict?**
In real monograph writing, out-of-order citation numbers and reference lists that don't match the text are the most frequent errors — manually auditing a 300,000-word book is nearly impossible. Script-enforced checks on every batch are what make the final manuscript trustworthy.

**Q: My platform isn't Claude — will it work?**
The skill follows the Agent Skills open specification (SKILL.md + scripts + reference docs), so any compliant AI assistant can use it. The scripts are pure Python standard library (except `python-docx` for Word merging) and can also be used standalone.

**Q: What if I need to change the outline mid-writing?**
The frozen outline is a serious contract: changes require author approval and a version bump (v2, v3…), recorded in the ledger. Completed chapters are never silently rewritten — contradictions are logged for adjudication. See the `references/` docs.

**Q: A script printed an error I don't understand. What now?**
You don't need to understand it. Every script error follows the format *what happened → common causes → how to fix*; do what the "how to fix" line says and re-run. Common errors (broken config JSON, wrong file encoding, filename drift, missing python-docx) have a symptom→cause→fix lookup table in `references/troubleshooting.md`. The easiest route: paste the full output to your AI assistant and say "fix this for me".

**Q: My "book" is really a training handbook / collected report — does it still apply?**
Yes. Any multi-chapter long manuscript fits. Word-count tiers live in `书稿配置.json` and are fully adjustable — global tiers, per-chapter overrides, and special-case exemptions are all supported, so defaults never box you in. For single papers or short documents the batch machinery adds little value and isn't recommended.

**Q: Does it work on Windows? What about non-Chinese manuscripts?**
The scripts are pure Python standard library (only Word merging needs `python-docx`) and run on macOS/Linux/Windows; quote paths containing spaces or CJK characters. Chinese-language writing is the best supported (word counts are measured in Chinese characters; GB/T 7714 type-identifier checking included). Other languages run, but counting and punctuation rules may be imprecise — multilingual support is on the roadmap.

**Q: Will the AI cite my own unpublished data or drafts as references?**
No — that is the "contribution classification" red line: published work by others is cited normally; **your own published** work is cited with a relation note ("this chapter extends the author's published work [n]"); **your own unpublished data** stays as writing material (labeled "author's experimental data" in text and figures; freeze it into a registered snapshot to cite it formally as [DS/OL]); **unpublished drafts never enter the reference list** — they are rewritten, not cited. Discipline differences are explicit too (unpublished archives in the humanities are cited per disciplinary convention, e.g. [A]). See `references/evidence-corpus.md` §8.

**Q: Does it work for a thesis going to blind review?**
Yes, with a dedicated guide: declaring the thesis genre creates an innovations-and-outputs register (innovation ↔ supporting chapters ↔ published papers), ready-made relation-note phrasing for your own published work, and a blind-review anonymization checklist (acknowledgements removed, self-citations de-identified or removed per your university's rule, full name-sweep before export). Citation renumbering after anonymization still goes through the validator until it passes. Plagiarism-check handling and the dual-submission risk of concurrently-submitted drafts are flagged in the ledger. See `references/thesis-guide.md`.

**Q: Can the AI draw figures for me?**
Two kinds: **data figures (statistical charts) — yes.** Put your data files (CSV/JSON) in the corpus, register an evidence card in ledger §3b (figure number + data file + checksum + chart recipe), and `generate_figures.py` renders bar/line/scatter/box/histogram charts from the data; re-run after data changes; data-file drift is flagged by the validator. **Concept diagrams (schematics/architecture) — drafts only.** The AI produces a Mermaid text draft (version-controlled under 05_图表/草稿/) for you to redraw; the manuscript keeps a "Figure X-Y (to be finalized)" placeholder, and the publication-grade artwork is yours — conceptual structure is your scholarly judgment. See `references/figure-guide.md`.

**Q: GB/T 7714 got a 2025 revision — does the skill follow it?**
Yes. The new standard (effective July 2026) adds preprint [PP], dataset [DS], and archive [A] rules — the type-identifier check accepts both old and new codes, and frozen datasets are cited as [DS/OL] per the new standard. If your institution or journal pins a specific version, theirs wins.

## 11. Citing this project

If this skill helps your research, teaching, or work, a citation is the best way to support it. Click the **"Cite this repository"** button on the repository homepage (driven by [`CITATION.cff`](CITATION.cff)) to get a ready-to-use citation, or use the BibTeX entry below:

```bibtex
@software{chang2026monograph,
  author  = {Chang, Sheng},
  title   = {monograph-writing: Academic Monograph Batch-Writing Assistant},
  year    = {2026},
  url     = {https://github.com/newdeme/monograph-writing},
  version = {1.5.0},
  license = {Apache-2.0}
}
```

## 12. Contributing & license

- This skill distills the complete writing practice of a real academic monograph — the methodology is battle-tested over 200+ section batches.
- Feedback and improvements welcome via Issues / Pull Requests (batch experiences, new validation rules, adaptations to other citation styles). For commercial cooperation, private-deployment guidance, or custom development, please reach the maintainer via GitHub Issues.
- Released under the [Apache License 2.0](LICENSE), © 2026 newdeme — includes patent grant, safe for academic and commercial use.

---

*Co-developed by an AI writing assistant and a monograph author. Methodology details: `SKILL.md` and the `references/` directory.*
