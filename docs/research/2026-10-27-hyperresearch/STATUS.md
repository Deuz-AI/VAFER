# hyperresearch teardown — status (2026-10-27, paused)

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
- **Verification:** an independent skeptic checked the key claims of seven readers against the code. Not checked yet: verification and vault. `structured-findings.json` holds every reader's structured result and the seven verdict sets.

## Next

1. Verify the key claims of the verification and vault readers.
2. Synthesize `teardown.md`. It covers:
   - the architecture;
   - what drives quality and what is ceremony;
   - costs and weaknesses, including how much the DRACO #1 claim shows;
   - a side-by-side with vafer-research;
   - the opportunities.
3. Brainstorm with the user. The open question is what "5x better" means to them, for example quality on the same question, speed, cost, trust in the citations, or reuse. Then write the design, then the plan.
