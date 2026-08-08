# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository nature

This is **not a software codebase** — there is no source code, build system, linter, or test suite. The repository contains a single working directory, [Story_paper/](Story_paper/), holding a series of academic research proposal documents (Markdown, written in Vietnamese) for a Q1-journal paper series on container yard/port logistics optimization. There are no commands to build, lint, or test; work here consists of reading, drafting, and revising these Markdown documents.

Note: `git rev-parse --show-toplevel` resolves to the user's home directory (`C:/Users/X1`), not this folder — this project folder is a subdirectory of a much larger git repository that also tracks unrelated personal/system files. Treat `Research_Story/` as the effective project scope; don't assume sibling directories seen in `git status` are part of this project.

## Paper series roadmap

The documents in `Story_paper/` form a **sequential, dependent roadmap** — each paper builds on the previous one's assumptions and explicitly defers certain concerns to later papers. When editing or extending any one paper, check the others for consistency (shared terminology, the trigger/replan/repair vocabulary, and the "what belongs in which paper" boundaries below).

| File | Paper | Core question |
|---|---|---|
| `SAR_CRP_v2_FINAL_READY_With_Implementation_Appendix_VI (1).md` | Paper 1 — SAR-CRP v2 | When retrieval information changes, should the relocation plan be repaired, and how, while staying stable? |
| `SAR_CRP_Paper2_EA_SAR_CRP_ULTRA_FINAL_Implementation_Ready_VI.md` | Paper 2 — EA-SAR-CRP | How does replanning stay robust under imperfect execution (delays, failures, stale/unreliable state, rollback/fallback)? |
| `SAR_CRP_Paper3_MISR_Yard_ABSOLUTE_FINAL_Code_Ready_VI.md` | Paper 3 — MISR-Yard | Multi-intervention / multi-crane stable replanning for yard operations. |
| `SAR_CRP_Paper4_Port_GSAR_ULTRA_FINAL_Code_Ready_VI.md` | Paper 4 — Port-GSAR | Making the Paper 1–3 decision framework port-configurable and generalizable across yards. |
| `SAR_CRP_Paper5_HITL_DT_Yard_ULTRA_FINAL_Code_Ready_VI.md` | Paper 5 — HITL-DT-Yard | Human-in-the-loop learning from operator feedback/overrides inside a digital-twin replay environment before deploying policy updates to production. |

Key shared concepts across the series: **event impact estimation, replanning trigger, freeze horizon, stability-aware objective, local-search repair vs. full reoptimization, and fallback (keep-old-plan / safe-hold)**. Paper *N* generally assumes Paper *N-1*'s mechanisms as a given baseline and only introduces its own delta (e.g., Paper 2 does not revisit retrieval-information triggers, and explicitly pushes multi-crane scheduling to Paper 3 rather than scope-creeping).

Each document also cites external base papers (e.g., Shin et al. 2026 for a CRP RL solver, Zhou & Zhang 2024 for real-time stochastic CRP, Zhang et al. 2025 for retrieval-probability prediction) that are marked as **unverified placeholders** pending DOI/venue confirmation — several files contain an explicit checklist for this. Do not treat these citations as confirmed without checking the verification checklist in the relevant file.

## File naming convention

Filenames encode revision status, not just topic — e.g. `_ULTRA_FINAL_`, `_ABSOLUTE_FINAL_`, `_FINAL_READY_`, `_Code_Ready_`, `_Implementation_Ready_`, with a trailing `_VI` marking Vietnamese-language content. When asked to revise a paper, prefer editing the existing (latest-tagged) file in place rather than creating a new versioned filename, unless the user asks for a new revision snapshot.

## Working in this repo

- Content is in Vietnamese with embedded English technical terms (e.g., "freeze horizon", "stability-aware objective") — preserve this bilingual convention when editing rather than translating wholesale, unless asked to.
- Each document mixes narrative proposal text with `text` code fences used for structured pseudo-formal definitions (inputs/outputs, decision cases) and Markdown tables for cross-paper comparisons — match this existing style for consistency when adding new sections.
- Several of the ARS (academic-research-skills) slash commands available in this environment (`/ars-plan`, `/ars-outline`, `/ars-revision`, `/ars-citation-check`, `/ars-lit-review`, etc.) are directly applicable to this kind of paper-proposal work — prefer them over ad hoc editing when the task matches (e.g., use `/ars-citation-check` before treating the placeholder base-paper citations as final).
