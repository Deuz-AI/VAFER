# Spike: can WebFetch supply verbatim quotes on Claude Code? (2026-10-28)

**Question.** The design wants researchers to capture the exact sentence behind each citable fact (a receipt) and a later check to match the report against those receipts. Does Claude Code's WebFetch return page text verbatim?

**Status: predicted, not measured.** WebFetch was never called. The user-level `~/.claude/settings.json` denies `WebSearch` and `WebFetch`, and the deny was already present in the 2026-10-27 backup. The conclusions come from reading the installed Claude Code 2.1.312 binary and from rebuilding its page processing locally on six downloaded pages. Pages, targets, prompts and scripts are in the session scratchpad under `spike-webfetch/`.

## Findings from the binary

- **WebFetch returns a small model's answer, never the page text.** For sites outside a short list of developer-docs domains, every prompt is extended with a rule that caps quotes at 125 characters and forbids word-for-word text outside the quotation. 5 of the 12 target sentences are longer than 125 characters.
- **Depth.** The converted page is cut at 100,000 characters, so later text is never seen.
- **Charset.** Pages are decoded as UTF-8 whatever their declared charset. The windows-1254 Resmî Gazete page arrives with all 1,245 Turkish letters replaced by "�". UTF-8 Turkish pages are fine.
- **PDF.** The model receives compressed bytes, with no readable text.
- **Tables.** Each cell becomes its own paragraph, so no row survives as a quotable unit.

## What the WebFetch model could see, per target (12 targets on 6 pages)

| Outcome | Targets |
|---|---|
| Intact and 125 characters or shorter | Turkish Wikipedia, early; ABS labour force, early |
| Intact but over the cap | Turkish Wikipedia, late; ONS labour market, early and late |
| Only as separate table cells | Federal Reserve H.15, first and last row |
| Turkish letters replaced by "�" | Resmî Gazete 2026-10-27, early and late |
| Past the 100k cut | ABS labour force, late |
| Not visible at all (PDF) | EIA STEO PDF, early and late |

At most 2 of the 12 receipts could come back exact and complete.

## Consequences for the design

- WebFetch is for finding and skimming pages, not for receipts.
- Receipts come from a page snapshot. A small stdlib script downloads the page, decodes it with the page's own charset, extracts text (pdftotext for PDFs when installed) and saves the snapshot in the run folder. The check matches quotes and numbers against the snapshot.
- A download can fail. For example, bls.gov answered 403 to curl with a browser user agent but 200 to WebFetch's user agent. The fetcher should try a second user agent. A page that cannot be downloaded is marked unverified, not dropped.
- Statistics pages labelled "latest" roll over (ABS, ONS, H.15), so a snapshot also keeps the access date and a content hash.
