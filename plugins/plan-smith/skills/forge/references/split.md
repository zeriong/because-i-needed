# Split protocol — large plans become an index plus ordered parts

Used by **Stage 2d** of the forge skill. The main agent reads this file; the section
**"Split protocol (copy verbatim to the writer)"** goes into the split-mode prompt word for word.

## When to split (main agent)

- Measure the final plan: `wc -m < plans/<slug>/plan.md`. Split only when it is **over 20,000
  characters** — (c) declared arbitrary; the first retrospectives that record `split` / `unsplit`
  outcomes replace it. Characters, not words or lines: the plan is written in the user's language, and
  word and line counts mean different things from one language to the next.
- Split the **final** plan only — after Stage 2 and, for build-outs, after the Stage 2c wiring audit and
  its additions. Every quality gate and the wiring audit judge the whole plan; the split only moves text.
- Never split `draft.md` (relay pass 1) or divergence variants (`plan-<variant>.md`). If the user adopts a
  variant that is over the threshold, copy it to `plan.md` and split that.
- Why split at all: two **hypotheses, not yet measured** — a reader, human or agent, is less likely to skip
  part of a long plan that arrives in ordered pieces, and pointer-ordered files are easier for an agent to
  work through. Treat them as hypotheses until a retrospective or an experiment says otherwise.

## Procedure (main agent)

1. `mv plans/<slug>/plan.md plans/<slug>/plan.unsplit.md`
2. Invoke a **fresh** `plan-writer` in split mode. The prompt contains: the absolute path of
   `plan.unsplit.md` (read-only input), the absolute index output path `plans/<slug>/plan.md`, the
   absolute parts directory `plans/<slug>/parts/`, and the section below, verbatim.
3. Check the result with the checker command in SKILL.md's Stage 2d. There `${CLAUDE_PLUGIN_ROOT}` is
   replaced with the plugin's path when the skill loads; in this file it is not, and the shell does not set
   it, so don't copy the variable from here. Outside Claude Code the script is
   `<plugin>/scripts/split-check.py`. Exit 0 means the split is lossless and well-formed; otherwise it
   prints what is wrong.
4. **Pass** → delete `plan.unsplit.md`: the parts are now the plan, and a second full copy would drift
   from them at the first edit. **Fail** → re-invoke split mode once, adding the checker's output to the
   prompt. If it fails again, restore (`rm -r plans/<slug>/parts` and
   `mv plans/<slug>/plan.unsplit.md plans/<slug>/plan.md`), relay the unsplit plan, and tell the user
   the split failed and why.

## Split protocol (copy verbatim to the writer)

You are moving an existing plan into an index and ordered parts. You are the **mover, not the author**:
the plan was already written and checked, and your job is to cut it, not to improve it.

**Output**

- `plan.md` — the index. It starts with the unsplit plan's header lines, moved verbatim (the `#` title,
  the frame/style line, the one-line summary — everything before the first `##` heading), followed by
  this block and nothing after it:

  ```markdown
  <!-- plan-smith:index -->
  > This file is an index — it holds no implementation. Read every part below in order; each one ends
  > with a pointer to the next. Do not start the work from this file alone.

  | order | part | covers | read after |
  |---|---|---|---|
  | A0 | [overview_A0.md](parts/overview_A0.md) | <the sections or steps it holds> | — |
  | B0 | [schema_B0.md](parts/schema_B0.md) | <…> | A0 |
  <!-- /plan-smith:index -->
  ```

  In the "covers" cells, also name the parts that hold the load-bearing path, the definition of done,
  and the implementer contract, when the plan has them.
- `parts/<category>_<code>.md` — one file per part.
  - `<category>`: ASCII kebab-case naming what the part holds (`overview`, `schema`, `api`, `risks`,
    `contract`), even when the plan is written in another language.
  - `<code>`: a letter `A`–`Z` for the phase, then a number `0`–`99` for the order within that phase
    (`A0`, `B0`, `B1`, `C0`). Codes ascend in reading order. The index, not the file listing, defines the
    order — a listing puts `A10` before `A2`.
  - The first line of every part: `> plan-smith · part <k>/<n> · <code> · index: [plan.md](../plan.md)`.
  - The last line: `> plan-smith · next: [<next file>](<next file>)`, or `> plan-smith · next: end of plan`
    on the last part.

**Rules**

1. **Move, never write.** Every non-empty line of the unsplit plan appears exactly once in the output,
   unchanged. The only new lines allowed are the index block and the two `> plan-smith ·` lines of each
   part. No summaries, no bridging sentences, no renamed headings, no fixes — if you notice a defect,
   report it in your return message and leave the text as it is.
2. **Keep the order.** The index header followed by the parts in index order reproduces the unsplit plan
   from top to bottom. Every part is one contiguous slice.
3. **Cut at boundaries.** Cut only before a heading or between the items of a list of steps — never inside
   a table, a code block, a list item, or a paragraph.
4. **Size.** Aim for each part to stay under 10,000 characters — (c) declared arbitrary, half the split
   threshold — but never break rule 3 to get there; a single oversized section stays whole.
5. **Context first, contract last.** Because the order is kept, the first part holds the plan's opening
   (the frame's starting point, the goal, the assumptions) and the last part holds "done" and the
   implementer contract. Name them so it shows (`overview_A0`, `contract_<last code>`).

Return only: the index path, the part paths in order, and any defects you noticed but did not fix.
