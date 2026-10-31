# Readability gate for script assembly (PLAN.md Task 1)

Date: 2026-10-31. Inputs: the frozen v0.0.4 Yalova run (`work/v004-yalova-run/`, not committed).

GATE: rewrite

## Versions

| Code | Version | Words (body) | Headings (body) | Mean words/sentence | Sentences >25 words |
|---|---|---|---|---|---|
| a | Script concatenation: `_top` + s1–s5 + g1–g3 + `_end`, by `tools/assemble_proto.py` | 4,060 | 31 | 10.9 | 3 |
| b | `report.before-edit.md` (the lead's assembly, before the editor) | 2,572 | 13 | 12.3 | 6 |
| c | `report.md` (delivered, after the editor) | 2,527 | 13 | 11.0 | 3 |

`_top.md` is report.md lines 1–26 (title, date line, answer, "Bir bakışta" table). `_end.md` is lines 167–190 (the disagreement table and the unknowns). Their `[n]` citations were turned back into URLs so the prototype numbered everything in one pass.

## Blind ranking

Three fresh judges each saw the three texts as X, Y and Z, in different orders. They had no other context. Each one scored readability for "a Turkish general reader with five minutes".

| Judge | a (assembled) | b (before edit) | c (delivered) |
|---|---|---|---|
| 1 | 4.0 | 7.3 | 7.6 |
| 2 | 4.5 | 7.3 | 7.6 |
| 3 | 4.0 | 7.2 | 7.4 |
| **Median** | **4.0** | **7.3** | **7.6** |

The rule was fixed before the ranking: if (a) scores at least 1.0 below (c), the lead rewrites. It did, by 3.6, so **GATE: rewrite**. In v0.0.5 the lead runs `assemble`, rewrites report.md for flow without an editor, and checks the rewrite with `vafer_check.py diff`.

## Why the assembly lost

All three judges named the same faults:
- **Order:** the gap sections came last, so the Crusades section followed the 1999 earthquake.
- **Repetition:** the prehistory, the present-day population and the 1921 departure each appear twice. The sections were drafted independently, and the gap drafts overlapped the main ones.
- **Length and headings:** 61% longer than the delivered report, with 31 headings against 13.
- **Garbled source titles:** the prototype took each snapshot's first body line as the title, and 32 of 50 were page chrome ("Skip to main content", "Jump to content", a bare page number).

## Caveats

- **The order fault overstates the gap.** It comes from v0.0.4's gap wave. v0.0.5 folds gap items into plan rows (REPORT #2), so a v0.0.5 assembly keeps plan order.
- **Repetition and length do not depend on v0.0.4.** Independent drafts overlap whatever the order, so a rewrite pass is still needed.
- **Follow-up:** the title fault carries over to `vafer_check.py assemble`, which also uses the first body line. It is queued as a script fix: take the HTML `<title>` at fetch time.
- **Before-edit vs delivered:** they differ by 0.3, inside judge noise. The editor's gain was small, which supports dropping it.
