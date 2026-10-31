# Offline replays of check and fetch (PLAN.md Task 8)

Date: 2026-10-31. Script: `vafer_check.py` at fc72fa7.

Inputs, copied under `work/` and not committed:
- the frozen v0.0.4 Yalova run, `work/v004-yalova-run/` (left unchanged);
- the review's concatenation probe, `v005-review/asm_probe/run`.

Step 4, the follow-up agent on C12 and C15, runs separately.

## Results

| Step | Expected | Result |
|---|---|---|
| 2. `check` on the frozen report | exactly 4 `b-unopened`; at most 5 other open high or medium flags; each one real or in a named class | 4 `b-unopened` and 3 others. 5 of the 7 are real. The 2 false ones fall in named classes. |
| 3. `check` on asm_probe | the open count against the old check's 55 | 26 open, against 55. With snapshots from the new `fetch`: 23. |
| 5. Re-fetch the 12 URLs that failed in v0.0.4 | longest call ≤ 30 s | One call for all 12 took 2.5 s. 6 of the 12 are now ok. |
| 6. Checker bugs | a failing test and a fix for each | One. The check dropped 8 receipts that were on their pages. Fixed in fc72fa7. |

## Step 1: markers

`work/v004-yalova-run-marked/` is a copy of the frozen run with two lines added to report.md:
- `<!-- vafer:end -->` before `## Ayrışan kaynaklar` (now line 167);
- `<!-- vafer:sources -->` before `## Kaynaklar` (now line 193).

evidence.md already used the key `Source check:`, so nothing was renamed. The old check.md has 6 columns, and the new check reads dispositions only from its own 7-column table. So every flag starts open.

## Step 2: the frozen report

```
script — 236 figures: 138 in a quoted receipt, 91 elsewhere on the cited page, 7 not found, 0 without evidence; 0 equations correct; 7 open high/medium flags of 7 (check.md)
Receipts: 162 parsed, 10 not in their snapshot (dropped), 8 unverified, 4 unparsed
```

The v0.0.4 check gave 13 flags. All 13 needed an answer, and 1 was real (run-evidence F10). The new check gives 12 flags: 7 high or medium that need an answer, and 5 low.

| id | severity | kind | report text | label | reason |
|---|---|---|---|---|---|
| F1 | medium | number-mismatch | "Bazı kaynaklardaki 318 yılını doğrulayan bir antik metin bulunamadı." | false | A rejected value in prose. The sentence has no citation, so it borrows its paragraph's [8] Procopius and [2] Socrates. Neither page has 318, which is what the sentence says. The page that gives 318 (catholic.com, opened, C1) is not cited. |
| F2 | medium | lead-only | "… yaygın kabul gören tarih 21 Ekim 1096'dır† [20]." | real | The only citation is Wikipedia. The report already marks the date † with a footnote, so the answer is †. |
| F3 | medium | number-mismatch | "… yer 4. yüzyıldan 1207'ye kadar kullanıldı [22]." | false | A two-column PDF read with `-layout`. Gündüz 2023 says "between the 4th century AD and 1207 AD", but the frozen snapshot has the other column's text between "the 4th" and "century AD". With the new fetch's text the flag goes away (see below). |
| F4 | high | b-unopened | B cell "27 köy (derlemeler)" | real | No [n] and no †. This is the judge's error C12: the opened Wikipedia page says "27 villages burned" and cites Gingeras (2009) for it. |
| F5 | high | b-unopened | B cell "4,80 metre (yaygın anlatı)" | real | No [n] and no †. This is the judge's error C15: conflicts.md says "not opened". |
| F6 | high | b-unopened | B cell "Bir kanun (bazı derlemeler)" | real | No [n] and no †. C16's B value ("Law 4114", from the gap-finder) is in no snapshot and no note. |
| F7 | high | b-unopened | B cell "2.501 ölü, 4.472 yaralı (yabancı derlemeler)" | real | No [n] and no †. C17 says "lead, not opened". |

5 of the 7 are real (71%), against 1 of 13 (8%) in v0.0.4.

The 4 `b-unopened` flags are exactly the four B cells without a citation. 2 of them sit on the judge's errors, which is the 50% the critique expected from this rule. In v0.0.4 the lead closed the flags on those two claims as false alarms. A `b-unopened` flag now closes only as fixed or †.

The 5 low flags need no answer. All five are years:
- L1: "MÖ 8000", a value the report rejects.
- L2–L5: the calendar bounds 1899 and 1901, in the restoration sentence and in its table row. The lead computed them.

What became of the 13 v0.0.4 flags:
- **Gone (4):**
  - "16. yüzyıl" against TDV's "XVI.": centuries are now one token.
  - The sentence split at "Cmd.".
  - "16.–19. yüzyıllarda" in the unknowns: the END block is not number-matched.
  - "27 köy" in prose: the sentence now borrows [27]. Toynbee's OCR book has 929,736 characters and "27" in 22 places, so the number counts as "elsewhere on the cited page".
- **Became low (4 flags, now 5):** "MÖ 8000" and the calendar bounds.
- **Kept (2):**
  - the lead-only 21 Ekim 1096;
  - "318", now a number-mismatch, because the sentence borrows its paragraph's citations.
- **Became `b-unopened` (3 flags, now 2):** the B-column mismatches 4,80, 2.501 and 4.472. Each cell gets one flag.
- **New (3):**
  - "4. yüzyıl" (F3);
  - the B cells "27 köy" and "Bir kanun". v0.0.4 did not flag them: it matched 27 against the row's Toynbee citation, and "Bir kanun" has no number.

### Receipts: the one checker bug

Before the fix, 18 of the 154 verified receipts that have a snapshot were "not in their snapshot". 8 of the 18 were on their pages:
- 7 quoted two or more passages in one line, as `"a" … "b"`, `"a" / "b"` or `"a", "b"`. The check split spans only at bare elisions. So the quote marks between passages stayed in the pieces, and the pieces never matched.
- 1 had a quoted word in its fact: `- Ship with ~1,800 refugees from "Gialova" to Volos, summer 1921 — "ένα άλλο …"`. The span opened at "Gialova".

The fix (fc72fa7) opens the span at the quote after the fact's dash. It also splits spans at quote-delimited separators. The test is `test_receipt_passages_and_quoted_fact_words`. All 159 tests pass, and the script stays at 899 lines. The flags do not change. 6 figures move from "elsewhere on the cited page" to "in a quoted receipt" (132 → 138).

The other 10 drops are real misses:
- 7 come from two-column PDFs read with `-layout`: Gündüz 2023 three times and Erbay four times. One of them is the "moved 5 meters" receipt behind C15.
- 1 comes from the TDV print PDF, whose font turns ı, ş and ğ into ý, þ and ð.
- 1 comes from Kaya (DergiPark 20471), whose PDF prints İ as Đ.
- 1 comes from Procopius. The page has a section number inside the sentence ("Helen, 4 mother"), and the receipt leaves it out.

| Snapshots and checker | Dropped | Kept |
|---|---|---|
| frozen, before the fix | 18 | 88.3% |
| frozen, after the fix | 10 | 93.5% |
| new fetch's PDF text, after the fix | 3 | 98.1% |

REPORT #12 asks for at least 97% kept.

### With the new fetch's PDF text

`work/v004-yalova-run-marked-newpdf/` replaces four PDF snapshots with fresh ones from the new `fetch`, which writes reading order and keeps the `-layout` copy beside it. The four are Gündüz 2023, Erbay, the TDV print PDF and Kaya.

The check then gives 6 open flags. F3 is gone, and nothing new appears. The figures are 148 in a quoted receipt, 82 elsewhere on the cited page and 6 not found.

## Step 3: asm_probe

`work/asm-probe-run-marked/` is the review's concatenation of the eight v0.0.4 section drafts. It has no `_top.md` or `_end.md`. So both markers go before `## Kaynaklar`, which is how `assemble` writes them when there is no `_end.md`.

```
script — 219 figures: 129 in a quoted receipt, 73 elsewhere on the cited page, 15 not found, 2 without evidence; 0 equations correct; 26 open high/medium flags of 26 (check.md)
```

| Check | Flags | Need an answer |
|---|---|---|
| v0.0.4 | 55: 26 uncited, 13 uncited table rows, 8 lead-only, 5 number-mismatch, 2 unverifiable, 1 quote | 55 |
| new | 47: 26 high or medium; 21 low (14 uncited table rows, 7 years) | 26 |
| new, with the new fetch's snapshots | 44 | 23 |

For the last row, `work/asm-probe-run-marked-newfetch/` swaps in the new fetch's snapshots for the four PDFs above and for ToposText and KeiBi (Step 5). F8, F25 and F26 go, and nothing new appears.

| id | severity | kind | report text | label | reason |
|---|---|---|---|---|---|
| F1 | high | lead-only | "Bir başka kaynağa göre kazı 1932'deydi … doğrulanamadı [3]." | real | ToposText (a lead) is the only support for a claim the section keeps (C3: two events). |
| F2 | high | lead-only | "Eski bir Katolik ansiklopedisi 318 yılını verir, ancak … bulunamadı [7]." | false | A rejected value. The lead is cited only for what it says, and the sentence doubts it (C1). |
| F3 | medium | number-mismatch | "İmparator I. Justinianus (527-565) …" (527) | real | The sentence borrows [5] Procopius, which has no reign years. TDV [1] has "(527-565)". |
| F4 | medium | number-mismatch | the same sentence (565) | real | The same. |
| F5 | medium | uncited | "Yalova kıyısı, 1096'da Halk Haçlı Seferi'nin yok olduğu yerdir." | real | A three-sentence paragraph with no citation. |
| F6 | medium | lead-only | "Haçlılar 21 Ekim 1096'da … [9]." | real | Wikipedia only. |
| F7 | medium | number-mismatch | "Kale 13. yüzyıldan sonra kaynaklardan kayboldu … [10]." | false | The page says "in the eleventh century before it disappeared … after the thirteenth". The noun "century" is left out, so the page has no century token for 13. |
| F8 | medium | number-mismatch | "… 4. yüzyıldan 1207'ye kadar kullanıldı [11]." | false | The `-layout` PDF, as in frozen F3. It goes away with the new fetch. |
| F9 | medium | lead-only | "Pylai'nin İznik İmparatorluğu'nun önemli limanı olduğu … [18]." | real | Wikipedia only. |
| F10 | medium | lead-only | "Pylai'nin yeri de tartışmalı … [19]." | real | limenproject.net only, labelled lead in the notes. |
| F11 | high | quote-missing | "… "yeniden tamir ve ihya" edildi [1]." | real | An altered quote: TDV has "müceddeden tamir ve ihya". |
| F12 | medium | uncited | "Kaynak kitabedeki 1316'yı 1898 diye çevirir." | real | TDV's "1316 (1898)", with no citation in the paragraph. |
| F13 | medium | uncited | "Ancak 25. yıl dönümü 1900 sonuna düşer; … Rumî 1316, yani 1900'dür." | real | 25 and 1316 are TDV's, uncited. The conclusion is the researcher's calendar reasoning. |
| F14 | medium | lead-only | "Kévorkian, Lalıdere (Laledere) ve Çukur gibi Ermeni köylerini sayıyor … [26]." | real | virtual-genocide-memorial.de only, labelled lead in the notes. |
| F15 | high | quote-missing | "… "hiçbir rakamın doğrulukla verilemeyeceğini" yazdı." | real | A Turkish translation inside quotation marks. House style rule 5 gives translations without quotation marks. |
| F16 | high | quote-missing | "… "Türk köylerinin yok edilmesi ve Müslüman nüfusun …" | real | The same. |
| F17 | high | quote-missing | "Bazı derlemelerde geçen "27 köy" ve "7.000 kişiden 1.500'ü kaldı" rakamlarının birincil kaynağı bulunamadı." | false | Rejected values in prose, checked against the borrowed Toynbee citation. This is the sentence of the judge's error C12. |
| F18 | medium | number-mismatch | "… yaygın anlatılarda ise 4,80 metre geçer." | false | A rejected value in prose, checked against the borrowed Erbay citation. This is the sentence of the judge's error C15. |
| F19 | medium | number-mismatch | "31 Aralık 2025 itibarıyla il nüfusu 311.635'tir [39]." | false | The governor's post says "2025 yılı sonunda" (at the end of 2025), and 311.635 matches. A derived date. |
| F20 | medium | uncited | "… derlemeler 2.501 ölü ve 4.472 yaralı veriyor; bu rakamlar asıl kaynağında doğrulanamadı." | false | Rejected values in prose (C17: "lead, not opened"). |
| F21 | medium | number-mismatch | "… 12 Kasım 1999 Düzce depremi Yalova'yı az etkiledi." | false | The TDV print PDF says "12 Kasým 1999": its font turns ı into ý, so "Kasým" is not read as a month. |
| F22 | medium | number-mismatch | "… (168.593'ten 311.635'e)." (168.593) | real | The 2000 census figure is not on the borrowed haberci.com.tr page. Bostan and Doğan [42] has it. |
| F23 | medium | lead-only | "Bir yıl önce 307.882 idi; artış 3.753 kişidir [47]." | real | tr.wikipedia only, although the governor's post [39] has both figures. |
| F24 | medium | lead-only | "Nüfusun yaklaşık yüzde 89'u kentlerde yaşar [47]." | real | tr.wikipedia only. |
| F25 | medium | unverifiable | [3] topostext.org | real | v0.0.4 saved the page as boilerplate, and its receipt is unverified. The new fetch gets it as ok. |
| F26 | medium | unverifiable | [45] keibi.uni-tuebingen.de | real | The same. |

18 of the 26 are real (69%):
- 6 are figures cited to the wrong page or not at all (F3, F4, F5, F12, F13, F22);
- 7 are lead-only;
- 3 are quotes: one altered, and two translations in quotation marks;
- 2 are sources without a snapshot.

These drafts never ran `check --section`, which did not exist in v0.0.4. The first group is what that check asks researchers to fix before they reply.

## C12 and C15 follow-up

see the follow-up test below

## Step 5: re-fetch

The 12 URLs whose status in `work/v004-yalova-run/pages/index.tsv` is not ok were fetched again with the new `fetch`, in one call, into `work/refetch-run/`:

`python -I skills/vafer-research/scripts/vafer_check.py fetch work/refetch-run <the 12 URLs>` took **2.5 s** of wall time. So no single URL took longer than 2.5 s.

| Status | v0.0.4 | New fetch |
|---|---|---|
| ok | 0 | 6 |
| empty | 4 | 4 |
| boilerplate | 4 | 0 |
| http-429 | 2 | 0 |
| http-404 | 1 | 1 |
| DNS failure | 1 | 1 |

| URL | v0.0.4 | New | Characters | Note |
|---|---|---|---|---|
| `ataturkansiklopedisi.gov.tr/bilgi/yalova-ataturk-kosku/?pdf=3267` | empty | empty | 0 | a JavaScript page |
| `ataturkansiklopedisi.gov.tr/bilgi/yalova-ataturk-kosku/` | empty | empty | 0 | the same |
| `ataturkansiklopedisi.gov.tr/detay/96/…` | empty | empty | 0 | the same |
| `biruni.tuik.gov.tr/medas/?kn=95&locale=tr` | empty | empty | 180 | TÜİK's query app |
| `dergipark.org.tr/en/download/article-file/254666` | http-429 | ok | 91,159 | PDF, a 2016 article |
| `dergipark.org.tr/en/download/article-file/2713766` | http-429 | ok | 64,279 | PDF, Millî Saraylar 2022 |
| `topostext.org/place/406292UPyT` | boilerplate | ok | 1,224 | a place record, with the "Mansel … 1932" quote behind asm_probe F1 |
| `acikerisim.anadolu.edu.tr/entities/publication/…/full` | boilerplate | ok | 1,385 | a repository record: a metadata table, no article text |
| `gutenberg.org/files/73839/73839-0.txt` | boilerplate | ok | 44,975 | the plain text of Cmd. 1478 |
| `keibi.uni-tuebingen.de/Record/KEI00119699/Details` | boilerplate | ok | 2,618 | the bibliographic record of Fıratlı 1953 |
| `uab.gov.tr/uploads/pages/mega-projeler/uab-megaprojeler.pdf` | http-404 | http-404 | – | not found |
| `media.iskur.gov.tr/94823/yalova.pdf` | DNS failure | DNS failure | – | the host does not resolve |

The four "empty" pages are JavaScript apps and need a browser. The four former "boilerplate" pages hold real content, so "ok" is right for them. A second call fetched four PDFs again for Step 2's comparison; it took 2.2 s.

## False flags by class

| Class | Frozen run | asm_probe | What removes it |
|---|---|---|---|
| A value the sentence names only to reject or doubt it | F1 | F2, F17, F18, F20 | Nothing in the check, which cannot tell rejection from assertion. See below. |
| A two-column PDF read with `-layout` | F3 | F8 | The new fetch (measured above). |
| A century with the noun left out ("after the thirteenth") | – | F7 | Nothing planned. |
| A PDF font that turns ı ş ğ into ý þ ð | – | F21 | A repair at fetch time (not done). |
| A date the report derives ("2025 yılı sonunda" written as "31 Aralık 2025") | – | F19 | The lead answers "derived". |

## Not fixed

- **Rejected values in prose.** The B-cell rule covers rejected values only in the disagreement table. In prose, a rejected value borrows a neighbour's citation or has none, and the flag then names the wrong problem. Two such sentences (asm_probe F17 and F18) are behind the judge's errors C12 and C15: values rejected without opening the page that states them.
  - A proposed rule for researcher.md: "A value you reject in prose carries the citation of the page that states it, or †". With it, these flags would become real, and the error class would be caught outside the table too.
  - This is skill text in another lane's files, so it is only proposed here.
- **TDV print PDFs.** There is one in this run, but TDV is a common source for Turkish local history. Its broken letters cost one false flag (asm_probe F21) and one dropped receipt, and month names such as "Kasým" never read as dates. A repair would fit in `fetch`: turn ý þ ð Ý Þ Ð into ı ş ğ İ Ş Ğ when a text has those letters and no ı ş ğ. The script is at 899 of its 900 lines, though.
- **Page-only matches in very large snapshots.** Any small number matches the 929,736-character Toynbee book. The check counts these as "elsewhere on the cited page" and does not flag them, as designed. That count says little for a source this size.
- **Snapshot titles of PDFs and plain text.** The Gutenberg text's title is "*** START OF THE PROJECT GUTENBERG EBOOK 73839 ***". The TDV print PDF's title is a sentence fragment in its broken font. `assemble` would print both in the Sources list.

## After the replays

Fixed in d10ff57 and 2168c94. `vafer_check.py` is at 900 of its 900 lines, and `python -m pytest -q tests` passes. Test names are in `tests/test_vafer_check.py`.

- A full date no longer matches through its parts when the cited page gives that day and month in another year ("7 Ağustos 1921" against "7 Ağustos 1920 … 1921"): `test_full_date_year_conflict_on_the_cited_page`.
- A table-only PDF, whose reading-order text is boilerplate, is saved from its `-layout` text (`Charset: pdf-layout`), not as `pdf-saved`: `test_pdf_table_only_uses_layout`.
- A snapshot's own `Status:` header wins over a v0.0.4 `index.tsv` row: `test_status_header_wins_over_a_legacy_index_row`.
- `check --section` finds `sections/<id>.md` in any case, as `assemble` does: `test_section_draft_name_in_any_case`.
- An escaped `\|` stays inside its END-table cell: `test_end_table_cells_keep_escaped_pipes`.
- `fetch` checks the 30 s deadline after every network read (`read1`): `test_download_reads_one_network_chunk_at_a_time`.
- "03.02'den" reads as a time, and Roman centuries need capitals ("il secolo XVI" is the 16th century): `test_time_suffix_den_and_capital_roman_numerals`.
- A sentence can open with an accented capital, ¿ or ¡: `test_accented_capitals_and_spanish_openers_start_a_sentence`.
- `find` and `fetch --find` number lines as `pages/<file>.txt` does: `test_find_prints_the_snapshot_file_line_numbers`.
- `fetch --refresh` downloads again; a skipped URL's line ends "(cached <date>)"; a refresh that gets a page that is not ok keeps the ok snapshot: `test_fetch_refresh_downloads_again_and_cached_lines_say_so`.
- Source titles: of 8 live pages (Wikipedia, yalova.gov.tr, Sözcü, Smithsonian, Harvard, Küre, two DergiPark PDFs), the 6 HTML titles were right and both PDFs were titled by their journal masthead. JUNK now skips masthead and metadata lines, and both PDFs get their article titles. Over the 25 PDF snapshots in `work/`, titles taken from a masthead, a metadata line or a citation line fall from 17 to 1 (a Resmî Gazete section label): `test_pdf_title_skips_the_masthead`.
- A numbered `[n]` in a draft: `assemble` warns, and `--section` flags it as dangling instead of reading it as the draft's n-th URL: `test_assemble_warns_about_numbered_citations_in_drafts`, `test_numbered_citation_in_a_draft_is_flagged_not_mapped`.
- Figures flagged uncited count as "without evidence" (asm_probe: 2 becomes 50): `test_uncited_figures_count_as_without_evidence`.
- HTML comments over several lines, and inline ones, are skipped: `test_html_comments_over_several_lines_are_skipped`.
- On a page with no century or date token, the fallback takes only an ordinal ("16.", "16e") for a century and a day before a word for a date: `test_fallback_needs_an_ordinal_century_or_a_day_before_a_word`.
- `check` prints "Body: N words" and writes it to check.md (frozen run: 1,521): `test_body_word_count_on_stdout_and_in_check_md`.
- `numbers()` blanks one-token figures in one pass and reads only the 40 characters before a time, so a page of many dates stays fast: `test_numbers_time_grows_linearly_with_dates`.

The frozen run (`work/final-check`, a copy of `v004-yalova-run-marked`) gives the same 4 b-unopened and 3 medium flags as before this pass; its check.md differs only by the Body line.

Deferred:

- "Toplam 12. Ekim 1920'de" still reads as the date 1920-10-12: a known limit, and no lines are left for a rule.
- The TDV print-PDF font repair (ý þ ð for ı ş ğ, proposal 2 above): no lines are left under the 900-line cap.
- Rejected values in prose (proposal 1 above): researcher.md text, in another lane.
- A yearless date still matches a page's day before any word ("29 Ekim" against "29 kule"): the fallback cannot tell an unknown month name from another word.
- The Gutenberg "*** START OF …" line and the TDV fragment remain titles: not among the 8 pages measured, and JUNK has no room for them.
- An escaped `\|` shows as `\\|` in check.md excerpts: cosmetic.
