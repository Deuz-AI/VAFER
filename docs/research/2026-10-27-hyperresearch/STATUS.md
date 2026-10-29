# hyperresearch teardown — status (2026-10-28, done)

The goal is to understand how hyperresearch (github.com/jordan-gibbs/hyperresearch, MIT, v0.12.0) produces its reports, what drives their quality, what it costs and where it is weak, and then to brainstorm how vafer-research can beat it by a wide margin (the user's target is "5x better").

## Done

- **Clone:** the repository is cloned at `C:\Users\VECTOR\Documents\GitHub\hyperresearch` (commit 327498b).
- **Install:** it is installed in `hyperresearch\.venv`. Run `.venv\Scripts\hyperresearch --version`.
- **Sandbox:** a sandbox project at `C:\Users\VECTOR\Documents\GitHub\hyperresearch-sandbox` holds a fresh `hyperresearch install . --target all`. It contains:
  - 17 step skills plus the entry skill;
  - 16 Claude subagents and 15 Codex agents;
  - hooks and a SQLite vault.
- **Readers:** nine parallel readers each covered one subsystem, and their notes are in `read-*.md`:
  - pipeline-front, pipeline-middle and pipeline-back (the 16 steps);
  - enforcement (hooks and gates);
  - runs-lint;
  - verification (cite-check and the independence audit);
  - acquisition (search, fetch and scholarly APIs);
  - vault;
  - claims-history (README, benchmark, changelog, issues).
- **Verification:** an independent skeptic checked the key claims of all nine readers against the code: 85 claims, 57 confirmed, 28 partly, none refuted.
  - `verified-claims.md` digests the first seven verdict sets, which are stored in `structured-findings.json`.
  - `verify-verification.md` and `verify-vault.md` hold the last two.
- **Teardown:** `teardown.md` covers:
  - the architecture;
  - what drives quality and what is ceremony;
  - costs and weaknesses, including what the DRACO #1 claim shows;
  - a side-by-side with vafer-research;
  - eleven opportunities.

  Three critics reviewed the first draft (`critique-accuracy.md`, `critique-completeness.md`, `critique-redteam.md`), and the draft was revised against their findings.

## Next

1. Brainstorm with the user. The open question is what "5x better" means to them. The teardown's view (§5) is that against the bare model we should expect 0–5 points of quality, so 5x is plausible only on rates:
   - unsupported load-bearing claims per report;
   - searches and minutes per follow-up on an INDEX hit;
   - run-to-run spread in checklist coverage.
2. Write the design, then the plan.
