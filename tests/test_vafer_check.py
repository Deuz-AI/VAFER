"""Offline tests for skills/vafer-research/scripts/vafer_check.py."""

from __future__ import annotations

import collections
import contextlib
import email.message
import hashlib
import http.server
import io
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
from decimal import Decimal
from unittest import mock
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY / "skills" / "vafer-research" / "scripts" / "vafer_check.py"
sys.path.insert(0, str(SCRIPT.parent))
import vafer_check as vc  # noqa: E402

URL1 = "https://www.epdk.gov.tr/tarifeler"
URL2 = "https://example.org/report/"
PROSE = "".join(f"<p>Paragraph {i}: the regulator published the full tariff table and the explanatory notes today.</p>"
                for i in range(5))


def values(text):
    """First reading of every number in text."""
    return [n.cands[0][0] for n in vc.numbers(text)]


class RunCase(unittest.TestCase):
    """Builds a throwaway run folder."""

    def setUp(self):
        self.run = Path(tempfile.mkdtemp(prefix="vafer-run-"))
        (self.run / "notes").mkdir()
        (self.run / "pages").mkdir()

    def tearDown(self):
        shutil.rmtree(self.run, ignore_errors=True)

    def note(self, text, name="a.md", encoding="utf-8"):
        (self.run / "notes" / name).write_bytes(text.encode(encoding))

    def page(self, url, text):
        name = f"p{len(list((self.run / 'pages').glob('*.txt')))}.txt"
        (self.run / "pages" / name).write_text(f"URL: {url}\nFetched: x\nCharset: utf-8\nSHA256: 0\n\n{text}",
                                               encoding="utf-8")
        with open(self.run / "pages" / "index.tsv", "a", encoding="utf-8") as fh:
            fh.write(f"{url}\t{name}\tok\t2026-10-28\n")

    def report(self, body, sources=((1, URL1),), heading="## Sources"):
        entries = "\n".join(f"[{n}] Title {n}. {u}" for n, u in sources)
        (self.run / "report.md").write_text(f"# Report\n\n{body}\n\n{heading}\n\n{entries}\n", encoding="utf-8")

    def kinds(self):
        return [f["kind"] for f in self.result["flags"]]

    def check(self):
        self.result = vc.check(self.run)
        return self.result


class NumberTests(unittest.TestCase):
    def test_uppercase_turkish_scale_words_and_huge_numbers(self):
        self.assertEqual(values("4 BİN 472"), [Decimal(4472)])
        self.assertEqual(values("12,3 MİLYON"), [Decimal(12300000)])
        self.assertFalse(vc.rounds_to(Decimal("1e40"), Decimal(3), 30))

    def test_turkish_and_english_formats(self):
        self.assertEqual(values("1.234,5"), [Decimal("1234.5")])
        self.assertEqual(values("1,234.5"), [Decimal("1234.5")])
        self.assertEqual(values("1 234,5 лв"), [Decimal("1234.5")])
        self.assertEqual(values("1 234,5 €"), [Decimal("1234.5")])
        self.assertEqual(values("%5 and 5% and % 5"), [Decimal(5)] * 3)
        self.assertEqual(values("₺2,61 and −3,2"), [Decimal("2.61"), Decimal("-3.2")])
        self.assertEqual(values("12.500.000 TL"), [Decimal(12500000)])

    def test_citation_marker_is_not_a_number(self):
        self.assertEqual(values("started in 2012 [12] and [3–5]"), [Decimal(2012)])

    def test_written_out_numbers(self):
        self.assertEqual(values("4 bin 472 ve bin 550"), [Decimal(4472), Decimal(1550)])
        self.assertEqual(values("12,3 milyon; 2,5 milyar; yüz bin"),
                         [Decimal(12300000), Decimal(2500000000), Decimal(100000)])
        self.assertEqual(values("1.2 million and 3 thousand"), [Decimal(1200000), Decimal(3000)])
        self.assertEqual(values("5 bina, the bin"), [Decimal(5)])

    def test_ranges_are_one_token_with_a_key_per_end(self):
        for text, keys in (("16.–19. yüzyıllarda", ["century 16", "century 19"]),
                           ("XVI-XVII. yüzyıl", ["century 16", "century 17"]),
                           ("16th–19th centuries", ["century 16", "century 19"]),
                           ("17–18 Ağustos 1999", ["date 1999-08-17", "date 1999-08-18"]),
                           ("4-11 Eylül 1919", ["date 1919-09-04", "date 1919-09-11"])):
            with self.subTest(text=text):
                self.assertEqual([[k for k, _ in n.cands] for n in vc.numbers(text)], [keys])

    def test_cardinals_are_not_centuries(self):
        self.assertEqual(values("3 yüzyıl boyunca, for 2 centuries"), [Decimal(3), Decimal(2)])
        self.assertEqual(values("16. yüzyıl, XVI. yüzyıl, the sixteenth century"), ["century 16"] * 3)

    def test_dotted_time_needs_saat_a_suffix_or_am_pm(self):
        self.assertEqual(values("stood at 3.45 percent; traded at 18.50 per dollar; faiz %3.45'te"),
                         [Decimal("3.45"), Decimal("18.50"), Decimal("3.45")])
        self.assertEqual(values("peaked at 1.25 million"), [Decimal(1250000)])
        self.assertEqual(values("saat 03.02'de, 03.02'de, 3.45 pm, at 3:45"),
                         ["time 3:02", "time 3:02", "time 3:45", "time 3:45"])

    def test_mixed_separators_have_no_reading(self):
        self.assertEqual(values("1,234.567,8 and 1.234,567.8 and 7"), [Decimal(7)])

    def test_abbreviated_and_foreign_months_and_centuries(self):
        for text, key in (("Oct. 29, 1923", "date 1923-10-29"), ("29 Oct 1923", "date 1923-10-29"),
                          ("Aug. 17, 1999", "date 1999-08-17"), ("Sept. 4th", "date --09-04"),
                          ("29 de octubre de 1923", "date 1923-10-29"), ("29. Oktober 1923", "date 1923-10-29"),
                          ("le 1er mai 1923", "date 1923-05-01"), ("29 ottobre 1923", "date 1923-10-29"),
                          ("1º de maio de 1923", "date 1923-05-01"), ("MAYIS 5th", "date --05-05"),
                          ("16. Jahrhundert", "century 16"), ("XVIe siècle", "century 16"), ("16e siècle", "century 16"),
                          ("siglo XVI", "century 16"), ("no século XVI", "century 16"), ("nel XVI secolo", "century 16"),
                          ("16. asırda", "century 16"), ("im 16. Jh.", "century 16")):
            with self.subTest(text=text):
                self.assertEqual(values(text), [key])

    def test_month_day_needs_a_year_or_suffix_and_a_rate_is_not_a_time(self):
        self.assertEqual(values("In May 5 people died; in March 15 villages; Kasım 3 kişi; Ocak 5 kişi"),
                         [Decimal(5), Decimal(15), Decimal(3), Decimal(5)])
        self.assertEqual(values("May 5th; May 5, 1921"), ["date --05-05", "date 1921-05-05"])
        self.assertEqual(values("yüzde 3.45'te; dolar 12.50'de; % 3.45'te; faiz yüzde yaklaşık 3.45'te; saat 3.45'te"),
                         [Decimal("3.45"), Decimal("12.50"), Decimal("3.45"), Decimal("3.45"), "time 3:45"])


    def test_numbers_time_grows_linearly_with_dates(self):
        # review round 3: every date rebuilt the whole text; a 1 MB page with 6,000 dates and times took 27 s
        text = ("Kayıt 29 Ekim 1923 günü, saat 14:30'da; 12 kişi, 345 ev, 6.789 TL. " + "metin " * 20 + "\n") * 4000
        start = time.time()
        found = vc.numbers(text)
        self.assertLess(time.time() - start, 2.5)
        self.assertEqual([n.cands for n in found[:3]], [[("date 1923-10-29", 0)], [("time 14:30", 0)], [(12, 0)]])
        self.assertEqual(len(found), 20000)


class SentenceTests(unittest.TestCase):
    def test_abbreviations_and_roman_numerals_do_not_split(self):
        line = ("II. Abdülhamid tahta çıktı. I. Mahmud, I. Derece, S. Sayısı, Dr. Ahmet, vb. Diğer, bkz. Ek, "
                "yy. Sonu, M.Ö. 300 ve s. 45 dahil. Son cümle.")
        self.assertEqual(len(vc.sentences([line])), 3, vc.sentences([line]))

    def test_period_before_digit_never_splits(self):
        line = "See Cmd. 1478 and No. 7596, s. 45. Ayrıca Prof. Ahmet, Doç. Ali, çev. Veli, vol. 2 geldi. Son."
        self.assertEqual(len(vc.sentences([line])), 3, vc.sentences([line]))

    def test_accented_capitals_and_spanish_openers_start_a_sentence(self):
        # review round 3: "Él", "¿Por qué" and "Ñandú" did not open a new sentence
        self.assertEqual(vc.sentences(["El precio subió [1]. Él dijo que no [2]. Ésta es otra [3]."]),
                         ["El precio subió [1].", "Él dijo que no [2].", "Ésta es otra [3]."])
        self.assertEqual(vc.sentences(["Subió [1]. ¿Por qué subió? ¡Nadie lo sabe! Ñandú [2]."]),
                         ["Subió [1].", "¿Por qué subió?", "¡Nadie lo sabe!", "Ñandú [2]."])

    def test_footnote_markers_end_sentence(self):
        line = "First ends here.³ Second ends.¹² Third ends.[^3] Fourth."
        self.assertEqual(vc.sentences([line]), ["First ends here.³", "Second ends.¹²", "Third ends.[^3]", "Fourth."])

    def test_marker_lines_are_not_sentences(self):
        lines = [vc.END_MARK, "Text one. Text two.", vc.SOURCES_MARK, "  <!-- any comment -->"]
        self.assertEqual(vc.sentences(lines), ["Text one.", "Text two."])

    def test_a_figure_is_never_split_or_read_as_a_list_mark(self):
        line = "Die Stadt wurde im 16. Jahrhundert gegründet [1]. Am 29. Oktober 1923 wurde sie Hauptstadt."
        self.assertEqual(vc.sentences([line]), ["Die Stadt wurde im 16. Jahrhundert gegründet [1].",
                                                "Am 29. Oktober 1923 wurde sie Hauptstadt."])
        self.assertEqual(vc.sentences(["16. yüzyılda kent büyüdü [1].", "1. Uno.", "2) Dos.", "- 3. Ekim yazısı."]),
                         ["16. yüzyılda kent büyüdü [1].", "Uno.", "Dos.", "3. Ekim yazısı."])


class CheckTests(RunCase):
    def test_percent_does_not_match_larger_percent(self):
        self.note(f'- Rate — "the rate is 25%" {URL1} (opened 2026-10-28; primary)\n')
        self.report("The rate is 5% [1].")
        self.check()
        self.assertEqual(self.kinds(), ["number-mismatch"])

    def test_cited_12_does_not_match_2012(self):
        self.page(URL1, "The program began in 2012.")
        self.report("It reached 12 cities [1].")
        self.check()
        self.assertIn("number-mismatch", self.kinds())

    def test_table_row_receipt_and_rounding(self):
        self.note(f'- Tariff — "Mesken | 2,61 TL/kWh | 2026-10" {URL1}/ (opened 2026-10-28; primary)\n')
        self.report("Mesken tarifesi 2,61 TL/kWh [1]. Yaklaşık 2,6 TL [1].\n\nSource check: pending")
        result = self.check()
        self.assertEqual(self.kinds(), [])
        self.assertEqual((result["matched"], result["figures"]), (2, 2))

    def test_equation_correct_and_wrong(self):
        self.page(URL1, "Mesken | 2,61 TL/kWh | 2026-10")
        self.report("Fatura: 230 kWh × 2,61 TL/kWh [1] = 600,3 TL.\n\nYanlış: 230 kWh × 2,61 TL/kWh [1] = 650 TL.")
        result = self.check()
        self.assertEqual((result["eq_ok"], result["eq_bad"]), (1, 1))
        self.assertEqual(self.kinds(), ["equation-wrong"])
        self.assertEqual(result["matched"], 2)
        self.assertIn("; 1 equations correct, 1 wrong; 1 open high/medium flags of 1 (check.md)", result["summary"])

    def test_quotes_exact_near_missing(self):
        self.page(URL1, "Kurul, İSTANBUL bölgesinde tarifeyi değiştirdi ve yeni dönem başladı.")
        self.report('Kurul “tarifeyi değiştirdi ve yeni dönem” dedi [1]. '
                    'Metin: "İstanbul bölgesinde tarifeyi değiştirdi" [1]. '
                    'Ayrıca "fiyatlar hiç değişmeyecek dedi" [1].')
        self.check()
        self.assertEqual(self.kinds(), ["quote-near", "quote-missing"])
        self.assertEqual([f["severity"] for f in self.result["flags"]], ["low", "high"])

    def test_dangling_and_unused(self):
        self.page(URL1, "nothing numeric")
        self.page(URL2, "nothing numeric")
        self.report("See the tariff [1; 7].", sources=((1, URL1), (2, URL2)))
        self.check()
        self.assertEqual(sorted(self.kinds()), ["dangling", "unused"])

    def test_marker_heading_and_url_normalization(self):
        self.page("http://epdk.gov.tr/tarifeler?utm_source=x#top", "Fiyat 2,61 TL")
        self.report("Fiyat 2,61 TL [1].", heading=f"{vc.END_MARK}\n{vc.SOURCES_MARK}\n### Kaynakça")
        result = self.check()
        self.assertEqual(self.kinds(), [])
        self.assertEqual(result["matched"], 1)

    def test_label_leak(self):
        self.page(URL1, "x")
        self.report("This part is PARTIAL [GAP] per notes/s1.md [1].")
        self.check()
        self.assertEqual(self.kinds().count("label-leak"), 3)

    def test_leak_only_internal_tokens(self):
        self.page(URL1, "Values 0 and 1.")
        self.report("The researcher found a wave of new records in wave 1 of the gap wave [1].")
        self.check()
        self.assertEqual(self.kinds(), [])
        for token in ("[prior]", "NOT-FOUND", "notes/s1.md", "[brainstorm]", "NOT SEARCHED", "COVERED",
                      "sections/g2.md", "pages/0a1b2c3d4e5f.txt"):
            with self.subTest(token=token):
                self.report(f"The record is here {token} [1].")
                self.check()
                self.assertEqual(self.kinds(), ["label-leak"])
                self.assertIn(token, self.result["flags"][0]["detail"])

    def test_spanish_report_end_to_end(self):
        cases = {"es": ("El precio es 2,61 € por kWh [1].", "## Lo que no se sabe\n\nNo se sabe la fecha.",
                        "## Fuentes\n[1] Título del informe 2023, 45 páginas https://a.es/x"),
                 "en": ("The researcher reports a price of 2,61 € per kWh [1].",
                        "## What is not known\n\nThe date is unknown.",
                        "## Sources\n[1] Report title 2023, 45 pages https://a.es/x")}
        for lang, (body, end, sources) in cases.items():
            with self.subTest(lang=lang):
                for path in self.run.joinpath("pages").glob("*"):
                    path.unlink()
                self.page("https://a.es/x", "Precio | 2,61 € | kWh")
                text = f"# Informe\n\n{body}\n\n{vc.END_MARK}\n{end}\n\n{vc.SOURCES_MARK}\n{sources}\n"
                (self.run / "report.md").write_text(text, encoding="utf-8")
                (self.run / "evidence.md").write_text("# Evidence\n\nSource check: pending\nSource mix: pending\n",
                                                      encoding="utf-8")
                parsed_body, parsed_sources, parsed_end = vc.parse_report(text)
                self.assertEqual(parsed_sources, {1: "https://a.es/x"})
                self.assertEqual(parsed_body[-1], "")
                self.assertIn(body, parsed_body)
                self.assertEqual(parsed_end[0], end.splitlines()[0])
                self.assertFalse(any("45" in line for line in parsed_body + parsed_end))
                result = self.check()
                self.assertEqual(self.kinds(), [])
                self.assertEqual((result["matched"], result["figures"]), (1, 1))
                evidence = (self.run / "evidence.md").read_text(encoding="utf-8")
                self.assertIn(f"Source check: {result['summary']}", evidence)
                self.assertIn(f"Source mix: {result['mix']}", evidence)
                self.assertNotIn("pending", evidence)

    def test_sources_fallback_without_marker(self):
        text = ("# R\n\n## Pasos\n\n1. Uno.\n2. Dos.\n\nPrecio 2,61 € [1].\n\n## Referencias\n\n"
                "[1] A https://a.org/1\n[2] B https://b.org/2\n[3] C https://c.org/3\n\n## Notas\n\nUna nota.\n")
        body, sources, end = vc.parse_report(text)
        self.assertEqual(sources, {1: "https://a.org/1", 2: "https://b.org/2", 3: "https://c.org/3"})
        self.assertEqual(body[-1], "")
        self.assertIn("2. Dos.", body)
        self.assertFalse(any("a.org" in line or "Referencias" in line for line in body))
        self.assertEqual(end, [])
        three = {1: "https://a.org/1", 2: "https://b.org/2", 3: "https://c.org/3"}
        nested = ("# R\n\nPrecio 2,61 € [1].\n\n## Kaynaklar\n\n### Birincil\n\n[1] A https://a.org/1\n[2] B https://b.org/2"
                  "\n\n### İkincil\n\n[3] C https://c.org/3\n")
        body, sources, _ = vc.parse_report(nested)
        self.assertEqual((sources, body[-2]), (three, "Precio 2,61 € [1]."))
        notes = ("# R\n\nPrecio 2,61 € [1].\n\n## Sources\n\n[1] A https://a.org/1\n[2] B https://b.org/2\n\n## Notes\n\n"
                 + "".join(f"Note line {i} about the method.\n" for i in range(6)))
        self.assertEqual(vc.parse_report(notes)[1], {1: "https://a.org/1", 2: "https://b.org/2"})

    def test_uncited_number(self):
        self.page(URL1, "Fiyat 2,61 TL")
        self.report("Fiyat 2,61 TL [1].\n\nHane sayısı 4.500 oldu. In 2024 there were 3 plans.")
        self.check()
        self.assertEqual(self.kinds(), ["uncited"])
        self.assertIn("4.500", self.result["flags"][0]["detail"])

    def test_unverifiable_source(self):
        self.report("Nothing [1].")
        self.check()
        self.assertEqual(self.kinds(), ["unverifiable"])

    def test_summary_line_replaced_and_check_md(self):
        self.page(URL1, "Fiyat 2,61 TL")
        self.report("Fiyat 2,61 TL [1].\n\n**Source check:** pending")
        result = self.check()
        text = (self.run / "report.md").read_text(encoding="utf-8")
        self.assertIn("**Source check:** script — 1 figures: 0 in a quoted receipt, 1 elsewhere on the cited page, "
                      "0 not found, 0 without evidence; 0 equations correct; 0 open high/medium flags of 0 (check.md)",
                      text)
        self.assertNotIn("pending", text)
        check_md = (self.run / "check.md").read_text(encoding="utf-8")
        self.assertIn(result["summary"], check_md)
        self.assertIn("Receipts: 0 parsed, 0 not in their snapshot (dropped), 0 unverified, 0 unparsed", check_md)
        self.assertIn("| id | severity | kind | report excerpt | cited | expected / found | disposition |", check_md)
        self.assertIn("Low (no answer needed)", check_md)

    def test_evidence_md_gets_check_line_and_report_untouched(self):
        self.page(URL1, "Fiyat 2,61 TL")
        self.report("Fiyat 2,61 TL [1].\n\nSource check: pending")
        (self.run / "evidence.md").write_text("Source check: pending\n", encoding="utf-8")
        before = (self.run / "report.md").read_text(encoding="utf-8")
        result = self.check()
        self.assertEqual((self.run / "report.md").read_text(encoding="utf-8"), before)
        self.assertIn(f"Source check: {result['summary']}", (self.run / "evidence.md").read_text(encoding="utf-8"))

    def test_open_count_excludes_dispositioned_flags(self):
        self.page(URL1, "Fiyat 2,61 TL")
        self.report("Fiyat 2,61 TL [1].\n\nHane sayısı 4.500 oldu.")
        result = self.check()
        self.assertTrue(result["summary"].endswith("; 1 open high/medium flags of 1 (check.md)"), result["summary"])
        self.assertEqual(result["open"], 1)
        path = self.run / "check.md"
        path.write_text(path.read_text(encoding="utf-8").replace("| disposition: |", "| fixed |"), encoding="utf-8")
        result = self.check()
        self.assertTrue(result["summary"].endswith("; 0 open high/medium flags of 1 (check.md)"), result["summary"])
        self.assertEqual(result["open"], 0)

    def test_no_summary_line_added(self):
        self.page(URL1, "Fiyat 2,61 TL")
        self.report("Fiyat 2,61 TL [1].")
        before = (self.run / "report.md").read_text(encoding="utf-8")
        self.check()
        self.assertEqual((self.run / "report.md").read_text(encoding="utf-8"), before)

    def test_windows_bom_note(self):
        self.note(f'- Rate — “oran yüzde 2,5 oldu” {URL1} (opened 2026-10-28; primary)\r\n', encoding="utf-8-sig")
        self.note(f'- Other — "fee 7,25 TL" {URL2} (opened 2026-10-28; secondary)\r\n', "b.md", "utf-16")
        self.report("Oran %2,5 [1]; ücret 7,25 TL [2].", sources=((1, URL1), (2, URL2)))
        result = self.check()
        self.assertEqual(self.kinds(), [])
        self.assertEqual(result["matched"], 2)

    def test_written_out_numbers_match_both_ways(self):
        self.page(URL1, "Katılımcı bin 550 kişi. Toplam 4472 kayıt. Nüfus 12.345.678 kişi.")
        self.report("1550 kişi katıldı [1]. Kayıt 4 bin 472 [1]. Nüfus 12,3 milyon [1].")
        result = self.check()
        self.assertEqual(self.kinds(), [])
        self.assertEqual(result["matched"], 3)

    def test_uncited_table_row_is_low_severity(self):
        self.page(URL1, "Fiyat 2,61 TL")
        self.report("Fiyat 2,61 TL [1].\n\n| İl | Nüfus |\n|---|---|\n| Ankara | 5.800.000 |")
        self.check()
        self.assertEqual(self.kinds(), ["uncited-table"])
        self.assertEqual(self.result["flags"][0]["severity"], "low")

    def test_mid_line_check_label_and_date_lines(self):
        self.page(URL1, "Fiyat 2,61 TL")
        self.report("Tarih: 2026-10-29 · Source check: pending\n\nAs of: 29 October 2026\n\n"
                    "Güncel: 2026-10-01\n\nFiyat 2,61 TL [1].")
        self.check()
        self.assertEqual(self.kinds(), [])
        text = (self.run / "report.md").read_text(encoding="utf-8")
        self.assertIn("Tarih: 2026-10-29 · Source check: script — 1 figures: ", text)
        self.assertNotIn("pending", text)

    def test_dispositions_survive_rerun(self):
        self.page(URL1, "Fiyat 2,61 TL")
        self.report("Fiyat 2,61 TL [1]. Hane sayısı 4.500 | 7 oldu.")
        self.check()
        path = self.run / "check.md"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "| disposition: |", "| false alarm: from census | table |"), encoding="utf-8")
        self.check()
        self.assertIn("| false alarm: from census | table |", path.read_text(encoding="utf-8"))

    def test_missing_report_exits_2(self):
        self.assertEqual(vc.main(["check", str(self.run)]), 2)
        self.assertEqual(vc.main(["check", str(self.run / "nope")]), 2)


WIKI = "https://tr.wikipedia.org/wiki/Elektrik"


class LabelTests(RunCase):
    def test_receipt_labels_parsed(self):
        self.note(f'- A — "span one here" {URL1} (opened 2026-10-28; official)\n'
                  f'- B — "span two here" {URL2} (opened 2026-10-28; secondary)\n'
                  f'- C — "span three" {WIKI} (opened 2026-10-28; lead; unverified)\n'
                  f'- D — "span four" https://x.org/a (opened 2026-10-28; derived)\n'
                  f'- E — "span five" https://x.org/b (opened 2026-10-28)\n')
        spans, labels, stats = vc.load_receipts(self.run)
        self.assertEqual(labels[vc.norm_url(URL1)], [("official", False)])
        self.assertEqual(labels[vc.norm_url(URL2)], [("press", False)])
        self.assertEqual(labels[vc.norm_url(WIKI)], [("lead", True)])
        self.assertEqual(labels["x.org/a"], [("derived", False)])
        self.assertEqual(labels["x.org/b"], [(None, False)])
        self.assertEqual(spans["x.org/b"], ["span five"])
        self.assertNotIn(vc.norm_url(WIKI), spans)
        self.assertEqual((stats["parsed"], stats["unverified"]), (5, 1))

    def test_lead_only_severity_by_section(self):
        self.page(URL1, "nothing numeric")
        self.report("## Summary\n\nElectricity is regulated [2].\n\n## Details\n\nIt is old [2]. "
                    "It is regulated [1; 2].", sources=((1, URL1), (2, WIKI)))
        self.check()
        lead = [f for f in self.result["flags"] if f["kind"] == "lead-only"]
        self.assertEqual(len(lead), 2)
        self.assertEqual([f["severity"] for f in lead], ["high", "medium"])

    def test_lead_by_receipt_label_and_domain_overridden(self):
        self.note(f'- A — "rate went up" {URL2} (opened 2026-10-28; lead)\n'
                  f'- B — "rate went up" {WIKI} (opened 2026-10-28; scholarly)\n')
        self.report("Rate went up [1]. Rate went up [2].", sources=((1, URL2), (2, WIKI)))
        self.check()
        lead = [f for f in self.result["flags"] if f["kind"] == "lead-only"]
        self.assertEqual([f["urls"] for f in lead], [[URL2]])

    def test_source_mix_and_evidence_md(self):
        self.note(f'- A — "x y z" {URL1} (opened 2026-10-28; primary)\n'
                  f'- A2 — "x y z" {URL1} (opened 2026-10-28; press)\n'
                  f'- B — "x y z" {URL2} (opened 2026-10-28; secondary)\n'
                  f'- B2 — "x y z" {URL2} (opened 2026-10-28; press unverified)\n')
        self.report("A [1]. B [2]. C [3]. D [4].",
                    sources=((1, URL1), (2, URL2), (3, WIKI), (4, "https://x.org/c"), (5, "https://x.org/d")))
        (self.run / "evidence.md").write_text("# Evidence\n\n**Source check:** pending\n"
                                              "Source mix: pending\n", encoding="utf-8")
        result = self.check()
        mix = "1 primary, 0 official, 0 scholarly, 1 press, 1 lead, 1 unlabelled"
        self.assertEqual(result["mix"], mix)
        self.assertIn(f"Source mix: {mix}", (self.run / "check.md").read_text(encoding="utf-8"))
        evidence = (self.run / "evidence.md").read_text(encoding="utf-8")
        self.assertIn(f"**Source check:** {result['summary']}", evidence)
        self.assertIn(f"Source mix: {mix}", evidence)
        self.assertNotIn("pending", evidence)


class QuietCheckTests(RunCase):
    """Task 3: one-token dates and centuries, B-cell rule, borrowing, severities, honest counts, receipts."""

    def flags(self):
        return [(f["kind"], f["severity"]) for f in self.result["flags"]]

    def fresh_page(self, url, text):
        for path in self.run.joinpath("pages").glob("*"):
            path.unlink()
        self.page(url, text)

    def test_roman_and_ordinal_centuries(self):
        for report, page in (("XVI. yüzyılda kuruldu [1].", "Kent 16. yüzyıl başında kuruldu."),
                             ("It was founded in the 16th century [1].", "Kent XVI. yüzyıl başında kuruldu."),
                             ("Kale 11. yüzyılda yapıldı [1].", "Built by Alexios in the eleventh century.")):
            with self.subTest(report=report):
                self.fresh_page(URL1, page)
                self.report(report)
                self.check()
                self.assertNotIn("number-mismatch", self.kinds())
                self.assertEqual(self.result["counts"]["page"], 1)

    def test_full_date_is_one_token(self):
        self.page(URL1, "Cumhuriyet 29 Ekim 1923 günü ilan edildi.")
        self.report("İlan 29.10.1923 [1] tarihindedir. ISO biçimi 1923-10-29 [1].")
        self.check()
        self.assertEqual(self.kinds(), [])
        self.assertEqual(self.result["counts"]["page"], 2)
        self.fresh_page(URL1, "Toplantıya 29 kişi geldi. 10 köy katıldı. Yıl 1923 idi.")
        self.report("İlan 29.10.1923 [1] tarihindedir.")
        self.check()
        self.assertEqual(self.flags(), [("number-mismatch", "medium")])
        self.assertIn("29.10.1923", self.result["flags"][0]["detail"])

    def test_yearless_and_comma_dates_are_one_token(self):
        text = "29 Ekim'de, October 29th, the 18th October, 1912, 5 Marching; of these 5 may close"
        self.assertEqual([n.cands for n in vc.numbers(text)],
                         [[("date --10-29", 0)], [("date --10-29", 0)], [("date 1912-10-18", 0)], [(Decimal(5), 0)],
                          [(Decimal(5), 0)]])

    def test_date_parts_count_as_evidence(self):
        self.page(URL1, "Cumhuriyet 29 Ekim 1923 günü ilan edildi.")
        self.report("Cumhuriyet 1923'te ilan edildi [1]. Bayram her yıl 29 Ekim'de kutlanır [1].")
        self.check()
        self.assertEqual(self.kinds(), [])
        self.assertEqual(self.result["counts"]["page"], 2)
        self.fresh_page(URL1, "The Commission returned on the 22nd May, having finished. Signed May 23, 1921.")
        self.report("Komisyon 22 Mayıs 1921'de döndü [1]. Rapor 25 Mayıs'ta yazıldı [1].")
        self.check()
        self.assertEqual(self.flags(), [("number-mismatch", "medium")])
        self.assertIn("25 Mayıs not found", self.result["flags"][0]["detail"])

    def test_full_date_year_conflict_on_the_cited_page(self):
        # review round 3: a year miscopied from the cited page passed through the date's parts
        for report, page, flagged in (
                ("Yunanlar 7 Ağustos 1921'de girdi [1].", "Yunanlar 7 Ağustos 1920'de girdi. 1921 yılında köyler yakıldı.",
                 True),
                ("Cumhuriyet 29 Ekim 1924'te ilan edildi [1].", "Cumhuriyet 29 Ekim 1923'te ilan edildi. 1924 Anayasası "
                 "kabul edildi.", True),
                ("Komisyon 22 Mayıs 1921'de döndü [1].", "The Commission returned on the 22nd May, having finished. "
                 "Signed May 23, 1921.", False),
                ("Yunanlar 7 Ağustos 1921'de girdi [1].", "Tarihler 7 Ağustos 1920 ve 7 Ağustos 1921.", False)):
            with self.subTest(report=report, page=page):
                self.fresh_page(URL1, page)
                self.report(report)
                self.check()
                self.assertEqual(self.flags(), [("number-mismatch", "medium")] if flagged else [])

    def test_fallback_needs_an_ordinal_century_or_a_day_before_a_word(self):
        # review round 3: on a page without a century or date token, any equal plain number passed
        for report, page, flagged in (
                ("Kale 12. yüzyılda yapıldı [1].", "Kale çok eskidir; 12 kule vardır.", True),
                ("Kale 12. yüzyılda yapıldı [1].", "Zamek zbudowano w 12. wieku.", False),
                ("Kale 12. yüzyılda yapıldı [1].", "Il castello è del 12º secolo circa.", False),
                ("Bayram 29 Ekim'de kutlanır [1].", "Kale çok eskidir; bkz. sayfa 29.", True),
                ("Bayram 29 Ekim'de kutlanır [1].", "Święto obchodzone 29 października.", False)):
            with self.subTest(report=report, page=page):
                self.fresh_page(URL1, page)
                self.report(report)
                self.check()
                self.assertEqual(self.kinds(), ["number-mismatch"] if flagged else [])

    def test_time_suffix_den_and_capital_roman_numerals(self):
        # review round 3: 'den/'dan was not a time suffix; under (?i) Italian "il" read as a Roman numeral
        self.assertEqual([n.cands for n in vc.numbers("Tren 03.02'den kalktı, 14.30'dan önce.")],
                         [[("time 3:02", 0)], [("time 14:30", 0)]])
        self.assertEqual([n.cands for n in vc.numbers("Fu costruito nel il secolo XVI.")], [[("century 16", 0)]])
        self.assertEqual([n.cands for n in vc.numbers("XVI secolo; xvi. madde")], [[("century 16", 0)]])

    def test_dates_and_centuries_across_languages(self):
        for report, page in (("Cumhuriyet 29 Ekim 1923'te ilan edildi [1].", "Proclaimed on Oct. 29, 1923."),
                             ("Deprem 17 Ağustos 1999'da oldu [1].", "The quake struck on Aug. 17, 1999."),
                             ("Cumhuriyet 29 Ekim 1923'te ilan edildi [1].", "Proclaimed 29 Oct 1923 in Ankara."),
                             ("Se proclamó el 29 de octubre de 1923 [1].", "Proclaimed on 29 October 1923."),
                             ("Die Stadt wurde im 16. Jahrhundert gegründet [1].", "The town was founded in the 16th century."),
                             ("Am 29. Oktober 1923 wurde sie Hauptstadt [1].", "It became the capital on October 29, 1923."),
                             ("La ville date du XVIe siècle [1].", "Kent 16. yüzyılda kuruldu."),
                             ("La ciudad es del siglo XVI [1].", "The town dates from the 16th century.")):
            with self.subTest(report=report):
                self.fresh_page(URL1, page)
                self.report(report)
                self.check()
                self.assertEqual(self.kinds(), [])
                self.assertEqual(self.result["counts"]["page"], 1)

    def test_token_falls_back_to_plain_parts_on_a_page_without_one(self):
        for report, page, flagged in (
                ("İlan 29 Ekim 1923'te yapıldı [1].", "Ogłoszono 29 października 1923 roku.", False),
                ("Bayram 29 Ekim'de kutlanır [1].", "Święto obchodzone 29 października.", False),
                ("Kent 16. yüzyılda kuruldu [1].", "De stad werd in de 16e eeuw gesticht.", False),
                ("İlan 29 Ekim 1923'te yapıldı [1].", "Toplantıya 29 kişi geldi. 10 köy katıldı. Yıl 1923 idi.", True),
                ("İlan 29 Ekim 1923'te yapıldı [1].", "Signed May 23, 1921. Ogłoszono 29 października 1923.", True)):
            with self.subTest(report=report, page=page):
                self.fresh_page(URL1, page)
                self.report(report)
                self.check()
                self.assertEqual(self.kinds(), ["number-mismatch"] if flagged else [])

    def test_paragraph_opening_with_a_century_is_checked(self):
        self.page(URL1, "Kent XVI. yüzyıl başında büyüdü.")
        self.report("16. yüzyılda kent büyüdü [1].")
        self.check()
        self.assertEqual((self.kinds(), self.result["counts"]["page"]), ([], 1))

    def test_clock_time(self):
        self.assertEqual([n.cands for n in vc.numbers("saat 03.02'de")], [[("time 3:02", 0)]])
        self.page(URL1, "Deprem 3:02 sularında oldu.")
        self.report("Deprem saat 03.02'de oldu [1].")
        self.check()
        self.assertEqual(self.kinds(), [])

    def test_decades(self):
        for report, page in (("1930'larda göç arttı [1].", "1930'lu yıllarda göç arttı."),
                             ("Migration rose in the 1930s [1].", "Migration rose in the 1930s.")):
            with self.subTest(report=report):
                self.fresh_page(URL1, page)
                self.report(report)
                self.check()
                self.assertEqual(self.kinds(), [])

    def test_ranges_match_either_end(self):
        for report, page, flagged in (
                ("16.–19. yüzyıllarda kaza idi [1].", "16. yüzyılda köydü. 19. yüzyılda kaza oldu.", False),
                ("Kent 16. yüzyılda köydü [1].", "16.-19. yüzyıllarda kaza idi.", False),
                ("Deprem 17–18 Ağustos 1999 gecesi oldu [1].", "Deprem 17 Ağustos 1999 günü oldu.", False),
                ("Kongre 4 Eylül 1919'da toplandı [1].", "Kongre 4-11 Eylül 1919 arasında toplandı.", False),
                ("It began in the 16th century [1].", "XVI-XVII. yüzyıl boyunca sürdü.", False),
                ("16.–19. yüzyıllarda kaza idi [1].", "12. yüzyılda kuruldu.", True)):
            with self.subTest(report=report, page=page):
                self.fresh_page(URL1, page)
                self.report(report)
                self.check()
                self.assertEqual(self.kinds(), ["number-mismatch"] if flagged else [])

    def test_date_line_in_any_language(self):
        self.page(URL1, "Fiyat 2,61 TL")
        for line in ("Fecha: 31 de octubre de 2026", "Fecha: 2026-10-31", "Datum: 31.10.2026",
                     "**Data:** 31 ottobre 2026", "Tarih: 29 Ekim 2026"):
            with self.subTest(line=line):
                self.report(f"{line}\n\nFiyat 2,61 TL [1].")
                self.check()
                self.assertEqual(self.kinds(), [])
        self.report("Not: 25 köy etkilendi.\n\n## Bölüm\n\nKayıt: 31 il, 2026 yılı.\n\nFiyat 2,61 TL [1].")
        self.check()
        self.assertEqual([f["detail"] for f in self.result["flags"]],
                         ["numbers without citation: 25", "numbers without citation: 31"])

    def test_historical_year_mismatch_is_low(self):
        self.page(URL1, "Hamam onarıldı. Kale MÖ 300 dolayında kuruldu.")
        self.report("Onarım Hicrî 1316, yani 1899 yılında [1]. Kent MÖ 280'de kuruldu [1]. It fell in 280 BC [1]. "
                    "Toplam 1.500 kişi [1].")
        self.check()
        self.assertEqual(sorted(self.flags()), [("number-mismatch", "low")] * 4 + [("number-mismatch", "medium")])

    def end_report(self, table_rows, prose="", sources=((1, URL1), (2, URL2))):
        table = "| topic | A | B | verdict | why |\n|---|---|---|---|---|\n" + "\n".join(table_rows)
        entries = "\n".join(f"[{n}] Title {n}. {u}" for n, u in sources)
        (self.run / "report.md").write_text(f"# R\n\nFiyat 2,61 TL [1].\n\n{vc.END_MARK}\n## Disagreements\n\n"
                                            f"{table}\n\n{prose}\n\n{vc.SOURCES_MARK}\n## Sources\n\n{entries}\n",
                                            encoding="utf-8")

    def test_b_column_not_matched_and_b_cell_rule(self):
        self.page(URL1, "Fiyat 2,61 TL. Köy sayısı 30. Kıyı 5 m.")
        self.page(URL2, "Kaynak sayfası, rakam yok.")
        self.end_report(["| köy sayısı | 30 köy [1] | 1.200 köy | A | açık |",
                         "| kıyı | 5 m [1] | 4,80 m † | A | açılmadı |",
                         "| köy | 30 köy [1] | 27 köy [2] | A | eski |"])
        self.check()
        self.assertEqual(self.flags(), [("b-unopened", "high")])
        self.assertIn("1.200 köy", self.result["flags"][0]["excerpt"])
        self.assertIn("neither [n] nor †: open its page and cite it, or mark it †", self.result["flags"][0]["detail"])

    def test_b_rule_needs_a_five_column_table_and_flags_keep_the_row(self):
        self.page(URL1, "Fiyat 2,61 TL. Köy sayısı 30.")
        self.page(URL2, "Kaynak sayfası, rakam yok.")
        entries = f"[1] Title 1. {URL1}\n[2] Title 2. {URL2}"
        (self.run / "report.md").write_text(
            f"# R\n\nFiyat 2,61 TL [1]. Kaynak [2].\n\n{vc.END_MARK}\n## Bilinmeyenler\n\n| konu | bilinen | neden |\n"
            f"|---|---|---|\n| nüfus | 2030 tahmini | kaynak yok |\n\n{vc.SOURCES_MARK}\n## Sources\n\n{entries}\n",
            encoding="utf-8")
        self.check()
        self.assertEqual(self.kinds(), [])
        self.end_report(["| köy sayısı | 31 köy [1] | 27 köy [2] | A | eski |"])
        self.check()
        self.assertEqual(self.flags(), [("number-mismatch", "medium")])
        self.assertIn("27 köy [2]", self.result["flags"][0]["excerpt"])

    def test_b_unopened_cannot_be_closed_as_a_false_alarm(self):
        self.page(URL1, "Fiyat 2,61 TL. Köy sayısı 30.")
        self.page(URL2, "Kaynak sayfası, rakam yok.")
        self.end_report(["| köy sayısı | 30 köy [1] | 1.200 köy | A | açık |", "| köy | 30 köy [1] | 27 köy [2] | A | eski |"])
        self.check()
        path, old = self.run / "check.md", "disposition:"
        for disp, still_open in (("false alarm: B is wrong anyway", 1), ("† marked unverified", 0), ("Fixed", 0)):
            with self.subTest(disp=disp):
                path.write_text(path.read_text(encoding="utf-8").replace(f"| {old} |", f"| {disp} |"), encoding="utf-8")
                self.assertEqual(self.check()["open"], still_open)
                old = disp

    def test_end_table_cells_keep_escaped_pipes(self):
        # review round 3: an escaped \| shifted the columns, so the B rule read the A cell
        self.page(URL1, "Fiyat 2,61 TL. Değerler 450 ve 451.")
        self.page(URL2, "Kaynak sayfası, rakam yok.")
        self.end_report(["| a \\| b | 450 \\| 451 [1] | 300 [2] | A | açık |", "| c | 450 [1] | 451 \\| 300 | A | açık |"])
        self.check()
        self.assertEqual(self.flags(), [("b-unopened", "high")])
        self.assertRegex(self.result["flags"][0]["detail"], r"^B value `451 \\+\| 300`")

    def test_b_cell_citations_count_for_the_row(self):
        self.page(URL1, "Fiyat 2,61 TL. Eski ölçüm alanı 4.200 m² verir.")
        self.page(URL2, "Kazı ekibi alanı yaklaşık 3.000 m² olarak verdi.")
        self.end_report(["| alan | 4.200 m² [1] | 3.000 m² [2] | Yaklaşık 3.000 m² | Kazı ekibinin son yayını |"])
        self.check()
        self.assertEqual(self.kinds(), [])

    def test_marker_missing_is_a_high_flag(self):
        self.page(URL1, "Fiyat 2,61 TL. Köy sayısı 30.")
        self.page(URL2, "Kaynak sayfası, rakam yok.")
        self.end_report(["| köy sayısı | 30 köy [1] | 1.200 köy | A | açık |"])
        path = self.run / "report.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace(vc.END_MARK + "\n", ""), encoding="utf-8")
        self.check()
        marks = [f for f in self.result["flags"] if f["kind"] == "marker-missing"]
        self.assertEqual([(f["severity"], vc.END_MARK in f["excerpt"]) for f in marks], [("high", True)])
        (self.run / "report.assembled.md").write_text(text, encoding="utf-8")
        path.write_text(text.replace(vc.END_MARK + "\n", "").replace(vc.SOURCES_MARK + "\n", ""), encoding="utf-8")
        self.check()
        self.assertEqual([f for f in self.flags() if f[0] == "marker-missing"], [("marker-missing", "high")] * 2)

    def test_unknowns_block_not_matched(self):
        self.page(URL1, "Fiyat 2,61 TL.")
        self.page(URL2, "Kaynak sayfası, rakam yok.")
        self.end_report([], "Nüfusun 2030'da 400.000 olacağı bilinmiyor [2]. Oran 7,5 kadar olabilir.")
        self.check()
        self.assertEqual(self.kinds(), [])

    def test_citation_borrowing(self):
        self.page(URL1, "Kent 1995'te il oldu. Nüfusu 270.976 kişidir.")
        self.report("Kent 1995'te il oldu [1]. Nüfusu 270.976'dır.")
        self.check()
        self.assertEqual(self.kinds(), [])
        self.assertEqual(self.result["counts"]["page"], 2)
        self.report("Kent 1995'te il oldu [1].\n\nNüfusu 270.976'dır.")
        self.check()
        self.assertEqual(self.flags(), [("uncited", "medium")])
        self.report("| İl | Nüfus |\n|---|---|\n| Yalnız | 1995 [1] |\n| Kent | 270.976 |")
        self.check()
        self.assertEqual(self.kinds(), [])

    def test_open_count_only_high_and_medium(self):
        self.page(URL1, "Fiyat 2,61 TL")
        self.page(URL2, "nothing numeric")
        self.report("Fiyat 2,61 TL [1]. Kuruluş 1950 [1].\n\nHane sayısı 4.500 oldu.",
                    sources=((1, URL1), (2, URL2)))
        result = self.check()
        self.assertEqual(sorted(self.flags()), [("number-mismatch", "low"), ("uncited", "medium"), ("unused", "low")])
        self.assertEqual(result["open"], 1)
        self.assertTrue(result["summary"].endswith("; 1 open high/medium flags of 1 (check.md)"), result["summary"])
        check_md = (self.run / "check.md").read_text(encoding="utf-8")
        low = check_md.split("Low (no answer needed)")[1]
        self.assertIn("unused", low)
        self.assertNotIn("disposition:", low)

    def test_honest_counts_line(self):
        self.note(f'- Fee — "the fee is 7,25 TL" {URL1} (opened 2026-10-31; primary)\n')
        self.page(URL1, "Tarife: the fee is 7,25 TL. Abone sayısı 1.200.")
        self.report("Ücret 7,25 TL [1]. Abone 1.200 [1]. Hane 4.500 [1].\n\nSource check: pending")
        result = self.check()
        self.assertIn("3 figures: 1 in a quoted receipt, 1 elsewhere on the cited page, 1 not found, "
                      "0 without evidence", result["summary"])
        self.assertTrue(result["summary"].startswith("script — 3 figures"))
        self.assertEqual(result["counts"], {"quoted": 1, "page": 1, "missing": 1, "none": 0})

    def test_uncited_figures_count_as_without_evidence(self):
        # review round 3: flagged uncited figures were left out of the honest counts
        self.page(URL1, "Fiyat 2,61 TL")
        self.report("Fiyat 2,61 TL [1].\n\nHane sayısı 4.500 oldu, köy sayısı 31.\n\nAlan 2,5 × 4 = 10 hektar.")
        result = self.check()
        self.assertEqual(sorted(self.kinds()), ["uncited", "uncited"])
        self.assertEqual(result["counts"], {"quoted": 0, "page": 1, "missing": 0, "none": 3})
        self.assertIn("4 figures: 0 in a quoted receipt, 1 elsewhere on the cited page, 0 not found, 3 without evidence",
                      result["summary"])

    def test_html_comments_over_several_lines_are_skipped(self):
        # review round 3: the inner lines of a multi-line comment were checked as sentences
        self.page(URL1, "Fiyat 2,61 TL")
        self.report("Fiyat 2,61 TL [1].\n\n<!--\nTaslak notu: 4.500 hane\nve 31 köy\n-->\n\nSon cümle <!-- 77 --> burada.")
        self.check()
        self.assertEqual(self.kinds(), [])

    def test_body_word_count_on_stdout_and_in_check_md(self):
        self.page(URL1, "Fiyat 2,61 TL")
        self.report("Tarih: 31 Ekim 2026\n\nFiyat 2,61 TL oldu [1].\n\n| a | b |\n|---|---|\n| 1 2 3 | 4 [1] |\n\n"
                    "## Bölüm\n\n- İki — kelime [1].\n\n**Source check:** pending")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(vc.main(["check", str(self.run)]), 0)
        self.assertEqual(out.getvalue().splitlines()[2], "Body: 6 words")
        self.assertIn("\nBody: 6 words\n", (self.run / "check.md").read_text(encoding="utf-8"))
        self.assertRegex((self.run / "report.md").read_text(encoding="utf-8"),
                         r"\*\*Source check:\*\* script — \d+ figures: [^\n]*\(check\.md\)\n")

    def test_receipts_autolink_inner_quotes_and_span_validation(self):
        self.page("https://x.org/p", "Intro text a ‘b’ c and more. Tari-\nfeleri GÜNCELLENDİ  bugün.")
        self.note('- fact — "a \'b\' c" <https://x.org/p> (opened 2026-10-31; primary)\n'
                  '- other — "tarifeleri güncellendi bugün" https://x.org/p (opened 2026-10-31; primary)\n'
                  '- gone — "this text is not on the page" https://x.org/p (opened 2026-10-31; primary)\n'
                  '- unv — "fee 9 TL" https://y.org/q (opened 2026-10-31; press; unverified)\n'
                  '- broken — "no url after the quote" (opened 2026-10-31) see https://z.org\n')
        spans, labels, stats = vc.load_receipts(self.run, vc.load_snapshots(self.run))
        self.assertEqual(spans["x.org/p"], ["a 'b' c", "tarifeleri güncellendi bugün"])
        self.assertNotIn("y.org/q", spans)
        self.assertEqual((stats["parsed"], stats["dropped"], stats["unverified"], len(stats["unparsed"])),
                         (4, 1, 1, 1))
        self.report("Ücret 9 TL [1].", sources=((1, "https://y.org/q"),))
        result = self.check()
        self.assertEqual(result["counts"]["quoted"], 0)
        self.assertIn("Receipts: 4 parsed, 1 not in their snapshot (dropped), 1 unverified, 1 unparsed",
                      (self.run / "check.md").read_text(encoding="utf-8"))

    def test_receipt_passages_and_quoted_fact_words(self):
        # Task 8 replay: receipts quoting several passages, or with a quoted word in the fact, were dropped
        self.page("https://x.org/p", "Report of May 23, 1921. Signed: G. M. FRANKS, E. ROLLETTO, G. VIEG.\n"
                                     "The hotel opened on 22 January 1938. Its first guests were the ministers.\n"
                                     "A ship named «Evangelos» carried about 1,800 people from Port Kato.")
        self.note('- signers — "G. M. FRANKS … E. ROLLETTO … G. VIEG" / "May 23, 1921." https://x.org/p '
                  '(opened 2026-10-31; primary)\n'
                  '- opening — "The hotel opened on 22 January 1938" … "Its first guests were" https://x.org/p '
                  '(opened 2026-10-31; scholarly)\n'
                  '- two — "about 1,800 people", "first guests" https://x.org/p (opened 2026-10-31; press)\n'
                  '- ship from "Port Kato" — "a ship named «Evangelos» carried about 1,800 people" https://x.org/p '
                  '(opened 2026-10-31; press)\n'
                  '- made up — "first guests" / "were the kings" https://x.org/p (opened 2026-10-31; press)\n')
        spans, _, stats = vc.load_receipts(self.run, vc.load_snapshots(self.run))
        self.assertEqual((stats["parsed"], stats["dropped"]), (5, 1))
        self.assertIn("a ship named «Evangelos» carried about 1,800 people", spans["x.org/p"])
        self.report("The ship carried about 1,800 people [1].", sources=((1, "https://x.org/p"),))
        self.assertEqual(self.check()["counts"], {"quoted": 1, "page": 0, "missing": 0, "none": 0})

    def test_section_check(self):
        (self.run / "sections").mkdir()
        self.page("https://a.org/x", "Fiyat 2,61 TL ve 300 abone.")
        (self.run / "sections" / "s1.md").write_text(
            "## Fiyat\n\nFiyat 2,61 TL [https://a.org/x]. Abone sayısı 450 [https://a.org/x].\n", encoding="utf-8")
        self.report("Nothing.\n\nSource check: pending", sources=())
        (self.run / "evidence.md").write_text("Source check: pending\n", encoding="utf-8")
        flags = vc.check_section(self.run, "s1")
        self.assertEqual([(f["kind"], f["severity"]) for f in flags], [("number-mismatch", "medium")])
        out = io.StringIO()
        stdout, sys.stdout = sys.stdout, out
        try:
            code = vc.main(["check", str(self.run), "--section", "s1"])
        finally:
            sys.stdout = stdout
        self.assertEqual(code, 0)
        lines = out.getvalue().splitlines()
        self.assertEqual(lines[0], "section s1: 1 flags (0 high, 1 medium, 0 low)")
        self.assertTrue(lines[1].startswith("medium number-mismatch: Abone sayısı 450"), lines)
        self.assertIn(" — 450 not found", lines[1])
        self.assertTrue(lines[1].endswith(" — https://a.org/x"), lines)
        self.assertFalse((self.run / "check.md").exists())
        self.assertEqual((self.run / "evidence.md").read_text(encoding="utf-8"), "Source check: pending\n")

    def test_section_draft_name_in_any_case(self):
        # review round 3: --section opened sections/<id>.md exactly; Linux file systems are case-sensitive
        (self.run / "sections").mkdir()
        self.page("https://a.org/x", "Fiyat 2,61 TL ve 300 abone.")
        (self.run / "sections" / "S1.md").write_text("Abone sayısı 450 [https://a.org/x].\n", encoding="utf-8")
        real = vc.read_text

        def case_sensitive(path):
            if Path(path).name not in os.listdir(Path(path).parent):
                raise FileNotFoundError(path)
            return real(path)

        out = io.StringIO()
        with mock.patch.object(vc, "read_text", case_sensitive), contextlib.redirect_stdout(out):
            self.assertEqual(vc.main(["check", str(self.run), "--section", "s1"]), 0)
        self.assertTrue(out.getvalue().startswith("section s1: 1 flags (0 high, 1 medium, 0 low)"), out.getvalue())

    def test_numbered_citation_in_a_draft_is_flagged_not_mapped(self):
        # review round 3: a [n] copied back from report.md was read as the draft's n-th URL
        (self.run / "sections").mkdir()
        self.page("https://a.org/x", "Fiyat 2,61 TL ve 300 abone.")
        self.page("https://b.org/y", "Nüfus 270.976.")
        (self.run / "sections" / "s1.md").write_text(
            "Fiyat 2,61 TL [https://a.org/x]. Nüfus 270.976 [https://b.org/y]. Abone 300 [2].\n", encoding="utf-8")
        flags = vc.check_section(self.run, "s1")
        self.assertEqual([(f["kind"], f["severity"], f["detail"]) for f in flags],
                         [("dangling", "high", "numbered citation [2]; write [URL]")])
        self.assertIn("Abone 300 [2].", flags[0]["excerpt"])

    def test_section_lines_show_table_rows_unescaped(self):
        (self.run / "sections").mkdir()
        self.page("https://a.org/x", "Fiyat 2,61 TL ve 300 abone.")
        (self.run / "sections" / "s1.md").write_text("| Abone | 450 [https://a.org/x] |\n", encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            vc.main(["check", str(self.run), "--section", "s1"])
        self.assertIn("\nmedium number-mismatch: | Abone | 450 [1] | — 450 not found", out.getvalue())


class AssembleTests(RunCase):
    """`assemble` builds report.md from sections/ drafts."""

    def setUp(self):
        super().setUp()
        (self.run / "sections").mkdir()
        self.page("https://a.org/x", "\n\nAlpha Agency Annual Report\nFiyat 2,61 TL ve 300 abone.")
        self.page("https://b.org/y", "Beta Page " + "z" * 200 + "\nNüfus 270.976.")
        (self.run / "plan.md").write_text("# Plan\n\n## S2 — second\n\n### g1 gap\n\n## S1 first\n\n## S9 missing\n",
                                          encoding="utf-8")
        self.section("_top", "# Rapor\n\nKısa cevap [https://b.org/y].")
        self.section("s1", "## Bir\n\nFiyat 2,61 TL [https://a.org/x].")
        self.section("s2", "## İki\n\nNüfus 270.976 [https://b.org/y/]. Yine [https://b.org/y#p3].")
        self.section("g1", "## Boşluk\n\nAbone 300 [https://a.org/x, https://b.org/y].")
        self.section("x1", "## Ek\n\nEk bilgi.")
        self.section("_end", "## Belirsizlikler\n\nBilinmiyor.")

    def section(self, sid, text):
        (self.run / "sections" / f"{sid}.md").write_text(text + "\n", encoding="utf-8")

    def assemble(self, *extra):
        out, err = io.StringIO(), io.StringIO()
        streams, (sys.stdout, sys.stderr) = (sys.stdout, sys.stderr), (out, err)
        try:
            self.code = vc.main(["assemble", str(self.run), *extra])
        finally:
            sys.stdout, sys.stderr = streams
        self.out, self.err = out.getvalue(), err.getvalue()
        path = self.run / "report.md"
        return path.read_text(encoding="utf-8") if path.exists() else None

    def test_assemble_order_and_markers(self):
        self.assertEqual(vc.section_order(self.run), ["s2", "g1", "s1", "s9", "x1"])
        text = self.assemble()
        self.assertEqual(self.code, 0)
        order = [text.index(h) for h in ("# Rapor", "## İki", "## Boşluk", "## Bir", "## Ek", vc.END_MARK,
                                         "## Belirsizlikler", vc.SOURCES_MARK, "## Sources")]
        self.assertEqual(order, sorted(order))
        self.assertEqual((text.count(vc.END_MARK), text.count(vc.SOURCES_MARK)), (1, 1))
        self.assertNotIn("https://a.org/x]", text)
        self.assertRegex(self.out, r"report\.md: 4 sections, \d+ body words, 2 sources")
        self.assertIn("s9", self.err)

    def test_assemble_numbering_dedup_normalized_urls(self):
        text = self.assemble()
        body = text.split(vc.END_MARK)[0]
        self.assertIn("Kısa cevap [1]", body)
        self.assertIn("Nüfus 270.976 [1]. Yine [1]", body)
        self.assertIn("Abone 300 [2, 1]", body)
        self.assertIn("Fiyat 2,61 TL [2]", body)
        self.assertEqual(len(vc.parse_report(text)[1]), 2)

    def test_assemble_sources_titles_and_title_arg(self):
        text = self.assemble("--title", "Fuentes")
        tail = text.split(vc.SOURCES_MARK)[1].strip().splitlines()
        self.assertEqual(tail[0], "## Fuentes")
        self.assertEqual(tail[2], "[1] " + ("Beta Page " + "z" * 200)[:120] + " https://b.org/y")
        self.assertEqual(tail[3], "[2] Alpha Agency Annual Report https://a.org/x")
        _, sources, _ = vc.parse_report(text)
        self.assertEqual(sources, {1: "https://b.org/y", 2: "https://a.org/x"})

    def test_assemble_rerun_idempotent(self):
        first = self.assemble()
        self.section("s1", "## Bir\n\nFiyat 2,61 TL [https://a.org/x]. Takip sonucu eklendi.")
        folded = self.assemble()  # a follow-up verdict folded into a section
        self.assertIn("Takip sonucu eklendi.", folded)
        self.assertEqual((folded.count(vc.END_MARK), folded.count(vc.SOURCES_MARK)), (1, 1))
        self.assertEqual(vc.parse_report(folded)[1], vc.parse_report(first)[1])
        self.section("s1", "## Bir\n\nFiyat 2,61 TL [https://a.org/x].")
        self.assertEqual(self.assemble(), first)
        self.assertEqual((first.count(vc.END_MARK), first.count(vc.SOURCES_MARK)), (1, 1))

    def test_assemble_drops_marker_lines_from_drafts(self):
        self.section("_end", vc.END_MARK + "\n## Belirsizlikler\n\nBilinmiyor.")
        self.section("s1", "## Bir\n\nFiyat 2,61 TL [https://a.org/x].\n\n" + vc.SOURCES_MARK)
        text = self.assemble()
        self.assertEqual((text.count(vc.END_MARK), text.count(vc.SOURCES_MARK)), (1, 1))
        self.assertIn(vc.END_MARK + "\n## Belirsizlikler", text)

    def test_assemble_section_file_name_in_any_case(self):
        (self.run / "sections" / "s1.md").unlink()
        self.section("S1", "## Bir\n\nFiyat 2,61 TL [https://a.org/x].")
        self.assertEqual(vc.section_order(self.run), ["s2", "g1", "s1", "s9", "x1"])
        text = self.assemble()
        self.assertEqual(text.count("## Bir"), 1)
        self.assertLess(text.index("## Boşluk"), text.index("## Bir"))
        self.assertNotIn("s1.md", self.err)
        self.assertRegex(self.out, r"report\.md: 4 sections")

    def test_assemble_title_never_holds_a_url(self):
        self.page("https://c.org/z", "https://doi.org/10.1/abc\nGamma Survey of Coastal Towns 2019\nDeğer 7,5 ölçüldü.")
        self.section("s9", "## Dokuz\n\nDeğer 7,5 [https://c.org/z].")
        text = self.assemble()
        self.assertIn("\n[3] Gamma Survey of Coastal Towns 2019 https://c.org/z\n", text)
        self.assertEqual(vc.parse_report(text)[1][3], "https://c.org/z")
        kinds = [f["kind"] for f in vc.check(self.run)["flags"]]
        self.assertNotIn("unverifiable", kinds)
        self.assertNotIn("number-mismatch", kinds)

    def test_title_with_a_link_keys_the_right_url(self):
        url, html = "https://x.com/vali/status/1", "<html><head><title>Vali açıkladı https://t.co/x</title></head><body>"
        with mock.patch.object(vc, "urlopen", lambda req, timeout: FakeResponse((html + PROSE).encode(), "text/html")), \
                contextlib.redirect_stdout(io.StringIO()):
            vc.cmd_fetch(self.run, [url])
        self.section("s9", f"## Dokuz\n\nVali açıkladı [{url}].")
        text = self.assemble()
        self.assertIn(f"\n[3] Vali açıkladı {url}\n", text)
        self.assertEqual(vc.parse_report(text)[1][3], url)
        self.assertEqual(vc.parse_report("## S\n\n[1] A https://t.co/x https://a.org/real\n")[1], {1: "https://a.org/real"})

    def test_assemble_always_writes_the_assembled_copy(self):
        first = self.assemble()
        self.assertEqual((self.run / "report.assembled.md").read_text(encoding="utf-8"), first)
        vc.write_text(self.run / "report.md", first.replace("Kısa cevap", "Akıcı kısa cevap"))  # rewritten, no copy step
        self.section("s1", "## Bir\n\nFiyat 2,61 TL [https://a.org/x]. Takip.")
        self.assertIn("Akıcı kısa cevap", self.assemble())
        self.assertIn("Takip.", (self.run / "report.assembled.md").read_text(encoding="utf-8"))
        (self.run / "report.assembled.md").unlink()  # a report.md with no assembled copy is kept too
        self.assertIn("Akıcı kısa cevap", self.assemble())

    def test_url_with_parentheses_keeps_its_evidence(self):
        url = "https://tr.wikipedia.org/wiki/Mudanya_(ilçe)"
        self.page(url, "Mudanya (ilçe)\nNüfus 66.000 kişi.")
        self.section("s9", f"## Dokuz\n\nNüfus 66.000 [{url}].")
        text = self.assemble()
        self.assertEqual(vc.parse_report(text)[1][3], url)
        kinds = [f["kind"] for f in vc.check(self.run)["flags"]]
        self.assertNotIn("unverifiable", kinds)
        self.assertNotIn("number-mismatch", kinds)
        self.assertEqual(vc.URL_RX.search("(bkz. https://a.org/x).").group(0), "https://a.org/x")

    def test_assemble_titles_prefer_header_and_skip_navigation(self):
        (self.run / "pages" / "h.txt").write_text("URL: https://h.org/t\nStatus: ok\nTitle: Yalova Kaplıcaları Raporu\n\n"
                                                  "Skip to main content\n" + "Uzun metin satırı burada. " * 20,
                                                  encoding="utf-8")
        self.page("https://n.org/u", "Skip to main content\nJump to content\n| Search: Submit Search\n"
                                     "| Home | Encyclopedia | Summa | Fathers | Bible | Library |\n"
                                     "Short URL for this page:\nISSN: 0041-4255 · e-ISSN: 2791-7584\n2019 2020 2021 2022 2023\n"
                                     "Haber ara...\nYalova'nın İdari Tarihi Üzerine Bir İnceleme\nMetin.")
        self.section("s9", "## Dokuz\n\nBilgi [https://h.org/t]. Ek [https://n.org/u].")
        text = self.assemble()
        self.assertIn("\n[3] Yalova Kaplıcaları Raporu https://h.org/t\n", text)
        self.assertIn("\n[4] Yalova'nın İdari Tarihi Üzerine Bir İnceleme https://n.org/u\n", text)

    def test_assemble_keeps_a_rewritten_report(self):
        vc.write_text(self.run / "report.assembled.md", self.assemble())
        self.section("s1", "## Bir\n\nFiyat 2,61 TL [https://a.org/x]. Takip bir.")
        second = self.assemble()  # report.md not rewritten yet: both files take the new assembly
        self.assertIn("Takip bir.", second)
        self.assertEqual((self.run / "report.assembled.md").read_text(encoding="utf-8"), second)
        rewrite = second.replace("Kısa cevap", "Akıcı kısa cevap")
        vc.write_text(self.run / "report.md", rewrite)
        self.section("s1", "## Bir\n\nFiyat 2,61 TL [https://a.org/x]. Takip iki.")
        self.assertEqual(self.assemble(), rewrite)
        self.assertIn("Takip iki.", (self.run / "report.assembled.md").read_text(encoding="utf-8"))
        self.assertTrue(self.out.startswith("report.assembled.md: ") and "report.md was edited" in self.out, self.out)

    def test_urls_with_apostrophe_comma_or_escapes_roundtrip(self):
        apos, comma = "https://tr.wikipedia.org/wiki/Türkiye'nin_illeri", "https://en.wikipedia.org/wiki/Washington,_D.C."
        self.page(apos, "Türkiye'nin 81 ili vardır.")
        self.page(comma, "Population 689,545 in the 2020 census.")
        self.page("https://tr.wikipedia.org/wiki/%C3%87%C4%B1narc%C4%B1k", "Nüfus 30.000 kişi.")
        self.section("s9", f"## Dokuz\n\nİl sayısı 81 [{apos}]. Nüfus 689,545 [{comma}; https://tr.wikipedia.org/wiki/"
                           "Çınarcık]. Kasaba 30.000 [https://tr.wikipedia.org/wiki/Çınarcık].")
        text = self.assemble()
        self.assertNotIn("[http", text + self.err)
        self.assertEqual(vc.parse_report(text)[1][3], apos)
        self.assertEqual(len(vc.parse_report(text)[1]), 5)
        kinds = [f["kind"] for f in vc.check(self.run)["flags"]]
        self.assertNotIn("unverifiable", kinds)
        self.assertNotIn("number-mismatch", kinds)
        self.section("x1", "## Ek\n\nEk bilgi [https://x.org/a b].")
        self.assemble()
        self.assertIn("[https://x.org/a b]", self.err)

    def test_assemble_warns_about_numbered_citations_in_drafts(self):
        # review round 3: a [n] copied back from report.md passed through unchanged and pointed at another source
        (self.run / "sections" / "s1.md").unlink()
        self.section("S1", "## Bir\n\nFiyat 2,61 TL [https://a.org/x]. Eski metin [3; 4].")
        self.section("_top", "# Rapor\n\nKısa cevap [https://b.org/y] [1].")
        self.assemble()
        self.assertIn("warning: sections/S1.md: numbered citation [3; 4]; write [URL]\n", self.err)
        self.assertIn("warning: sections/_top.md: numbered citation [1]; write [URL]\n", self.err)
        self.assertEqual(self.err.count("numbered citation"), 2, self.err)

    def test_assemble_warns_without_top_and_end(self):
        for sid in ("_top", "_end"):
            (self.run / "sections" / f"{sid}.md").unlink()
        text = self.assemble()
        self.assertEqual(self.code, 0)
        self.assertIn("_top.md", self.err)
        self.assertIn("_end.md", self.err)
        self.assertIn(vc.END_MARK + "\n\n" + vc.SOURCES_MARK, text)

    def test_assemble_then_check_roundtrip(self):
        self.assemble()
        kinds = [f["kind"] for f in vc.check(self.run)["flags"]]
        self.assertNotIn("dangling", kinds)
        self.assertNotIn("unused", kinds)

    def test_assemble_missing_sections_exits_2(self):
        shutil.rmtree(self.run / "sections")
        self.assertIsNone(self.assemble())
        self.assertEqual(self.code, 2)
        self.assertIn("sections", self.err)


OLD = ('# R\n\n## Özet\n\nKayıt 4.472 oldu [1]. Kurul "tarifeyi değiştirdi ve yeni dönem başladı" dedi [2-3].\n\n'
       'Source check: x 1 of 2\n\n<!-- vafer:sources -->\n## Kaynaklar\n\n[1] A. https://a.org/1\n[2] B. https://b.org/2\n'
       '[3] C. https://c.org/3\n')


class DiffTests(unittest.TestCase):
    def test_rephrase_with_written_numbers_is_clean(self):
        new = OLD.replace("Kayıt 4.472 oldu [1].", "Toplam kayıt sayısı 4 bin 472 olarak gerçekleşti [1].")
        new = new.replace("[2-3]", "[2, 3]").replace("x 1 of 2", "y 5 of 9")
        self.assertEqual(vc.diff(OLD, new), [])

    def test_lost_and_changed_items(self):
        new = (OLD.replace("4.472", "4.500").replace(" [1].", ".").replace("yeni dönem", "yeni bir dönem")
               .replace("https://c.org/3", "https://c.org/9"))
        out = vc.diff(OLD, new)
        text = "\n".join(out)
        self.assertIn("number missing: 4.472 (was in: Kayıt 4.472 oldu [1].)", text)
        self.assertIn("number added: 4.500", text)
        self.assertIn("citation missing: [1]", text)
        self.assertIn("quote missing or altered: “tarifeyi değiştirdi ve yeni dönem başladı”", text)
        self.assertIn("source [3] changed: https://c.org/3 -> https://c.org/9", text)

    def test_cli_exit_codes(self):
        tmp = Path(tempfile.mkdtemp(prefix="vafer-diff-"))
        try:
            (tmp / "old.md").write_text(OLD, encoding="utf-8")
            (tmp / "same.md").write_text(OLD.replace("oldu", "olarak kaydedildi"), encoding="utf-8")
            (tmp / "bad.md").write_text(OLD.replace("[2-3]", "[2]"), encoding="utf-8")
            out = io.StringIO()
            stdout, sys.stdout = sys.stdout, out
            try:
                codes = [vc.main(["diff", str(tmp / "old.md"), str(tmp / n)]) for n in ("same.md", "bad.md", "no.md")]
            finally:
                sys.stdout = stdout
            self.assertEqual(codes, [0, 1, 2])
            self.assertIn("citation missing: [3]", out.getvalue())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_added_citations_and_sources_pass(self):
        new = OLD.replace("oldu [1].", "oldu [1; 4].") + "[4] D. https://d.org/4\n"
        out = vc.diff(OLD, new)
        self.assertEqual([c for c in out if "(ok)" not in c], [], out)
        self.assertIn("citation added (ok): [4]", "\n".join(out))
        self.assertIn("source [4] added (ok): https://d.org/4", out)

    def test_lost_marker_is_a_problem(self):
        old = OLD.replace(vc.SOURCES_MARK, f"{vc.END_MARK}\n\n{vc.SOURCES_MARK}")
        tmp = Path(tempfile.mkdtemp(prefix="vafer-diff-"))
        try:
            (tmp / "old.md").write_text(old, encoding="utf-8")
            for mark in (vc.END_MARK, vc.SOURCES_MARK):
                with self.subTest(mark=mark):
                    new = old.replace(mark + "\n", "")
                    self.assertEqual(vc.diff(old, new), [f"marker missing: {mark}"])
                    (tmp / "new.md").write_text(new, encoding="utf-8")
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(vc.main(["diff", str(tmp / "old.md"), str(tmp / "new.md")]), 1)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_citation_detached(self):
        new = OLD.replace("Kayıt 4.472 oldu [1].", "Kayıt 4.472 oldu. Bu veri resmidir [1].")
        out = [c for c in vc.diff(OLD, new) if "(ok)" not in c]
        self.assertEqual(len(out), 1, out)
        self.assertTrue(out[0].startswith("citation detached: Kayıt 4.472 oldu [1]. -> now: Kayıt 4.472 oldu."), out)


class FakeResponse(io.BytesIO):
    def __init__(self, body, ctype):
        super().__init__(body)
        self.headers = email.message.Message()
        self.headers["Content-Type"] = ctype


def http_error(url, code, retry_after=None):
    headers = email.message.Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return urllib.error.HTTPError(url, code, "busy", headers, None)


class FetchTests(RunCase):
    def fetch(self, urls, opener=None, find=None):
        """Run cmd_fetch with a fake urlopen; return the printed lines."""
        out = io.StringIO()
        with contextlib.ExitStack() as stack:
            if opener:
                stack.enter_context(mock.patch.object(vc, "urlopen", opener))
            stack.enter_context(contextlib.redirect_stdout(out))
            vc.cmd_fetch(self.run, urls, find)
        return out.getvalue().splitlines()

    def test_file_url_windows_1254_and_table_rows(self):
        html = ('<html><head><meta charset="windows-1254"><title>t</title><script>var a=1;</script></head>'
                '<body><nav>menu</nav><p>Elektrik tarifeleri güncellendi.</p>'
                '<table><tr><th>Abone</th><th>Fiyat</th></tr><tr><td>Mesken</td><td>2,61 TL/kWh</td></tr>'
                '</table><p>Şubat dönemi</p>' + PROSE + '</body></html>')
        src = self.run / "page.html"
        src.write_bytes(html.encode("cp1254"))
        url = src.as_uri()
        self.assertEqual(vc.cmd_fetch(self.run, [url]), 0)
        snaps = vc.load_snapshots(self.run)
        text = snaps[vc.norm_url(url)]
        self.assertIn("Elektrik tarifeleri güncellendi.", text)
        self.assertIn("Abone | Fiyat\nMesken | 2,61 TL/kWh", text)
        self.assertIn("Şubat dönemi", text)
        self.assertNotIn("menu", text)
        self.assertNotIn("var a", text)
        raw = next((self.run / "pages").glob("*.txt")).read_text(encoding="utf-8")
        self.assertTrue(raw.startswith(f"URL: {url}\nFetched: "))
        self.assertIn("Charset: windows-1254", raw)

    def test_retry_on_403_header_charset_and_bad_url(self):
        calls = []

        def fake_urlopen(req, timeout):
            if req.full_url.endswith("/bad"):
                raise urllib.error.URLError("no route")
            calls.append(req.get_header("User-agent"))
            if len(calls) == 1:
                raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", None, None)
            return FakeResponse(("<p>Çalışma ücreti 7,25 TL</p>" + PROSE).encode("iso-8859-9"),
                                "text/html; charset=iso-8859-9")

        lines = self.fetch(["https://example.org/ok", "https://example.org/bad"], fake_urlopen)
        self.assertTrue(lines[0].startswith("ok ") and lines[1].startswith("URLError"), lines)
        self.assertNotEqual(calls[0], calls[1])
        self.assertIn("Çalışma ücreti 7,25 TL", vc.load_snapshots(self.run)["example.org/ok"])
        self.assertFalse((self.run / "pages" / "index.tsv").exists())

    def test_empty_boilerplate_doc_binary_and_utf16(self):
        bodies = {"empty": (b"<p>Loading...</p>", "text/html"),
                  "nav": ("".join(f"<li>Menu item {i}</li>" for i in range(40)).encode(), "text/html"),
                  "doc": (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 64, "application/octet-stream"),
                  "u16": (("Çalışma ücreti 7,25 TL\n" + PROSE).encode("utf-16"), "text/html; charset=iso-8859-9")}
        lines = self.fetch([f"https://example.org/{k}" for k in bodies],
                           lambda req, timeout: FakeResponse(*bodies[req.full_url.rsplit("/", 1)[1]]))
        self.assertTrue(lines[0].startswith("empty ") and ".txt" in lines[0], lines)
        self.assertTrue(lines[1].startswith("boilerplate ") and ".txt" in lines[1], lines)
        self.assertEqual(lines[2], "doc-binary - 0")
        self.assertTrue(lines[3].startswith("ok "), lines)
        self.assertEqual(len(list((self.run / "pages").glob("*.txt"))), 3)
        snaps = vc.load_snapshots(self.run)
        self.assertEqual(list(snaps), ["example.org/u16"])
        self.assertIn("Çalışma ücreti 7,25 TL", snaps["example.org/u16"])

    def test_fetch_status_header_and_skip_existing_ok(self):
        calls = []

        def opener(req, timeout):
            calls.append((req.full_url, timeout))
            return FakeResponse(("<html><head><title>Tarife duyurusu</title></head><body><h1>Duyuru</h1>" + PROSE
                                 + "</body></html>").encode(), "text/html")

        lines = self.fetch(["https://example.org/t"], opener)
        status, name, chars, title = lines[0].split(" ", 3)
        self.assertEqual((status, title), ("ok", "Tarife duyurusu"))
        self.assertGreater(int(chars), 400)
        raw = (self.run / "pages" / name).read_text(encoding="utf-8")
        self.assertRegex(raw, r"^URL: https://example.org/t\nFetched: .+\nStatus: ok\nCharset: .+\nSHA256: \w+\n"
                              r"Title: Tarife duyurusu\n\n")
        self.assertEqual(calls, [("https://example.org/t", 20)])
        again = self.fetch(["https://example.org/t/", "https://www.example.org/t#p3"], opener)
        fetched = vc.snap_head(self.run / "pages" / name)[0]["Fetched"][:10]
        self.assertEqual(again, [f"{lines[0]} (cached {fetched})"] * 2)
        self.assertEqual(len(calls), 1)
        self.assertFalse((self.run / "pages" / "index.tsv").exists())
        self.assertEqual(list(vc.load_snapshots(self.run)), ["example.org/t"])

    def test_concurrent_fetch_no_lost_snapshots(self):
        counts, lock = collections.Counter(), threading.Lock()

        def opener(req, timeout):
            with lock:
                counts[req.full_url] += 1
            time.sleep(0.02)
            return FakeResponse((f"<p>Page {req.full_url}</p>" + PROSE).encode(), "text/html")

        first = [f"https://h{i % 3}.org/p{i}" for i in range(12)]
        second = [f"https://h{i % 3}.org/p{i}" for i in range(6, 18)]
        out = io.StringIO()
        with mock.patch.object(vc, "urlopen", opener), contextlib.redirect_stdout(out):
            workers = [threading.Thread(target=vc.cmd_fetch, args=(self.run, urls)) for urls in (first, second)]
            for w in workers:
                w.start()
            for w in workers:
                w.join()
        self.assertEqual(sorted(counts), sorted(set(first + second)))
        self.assertEqual(set(counts.values()), {1})
        self.assertEqual(len(vc.load_snapshots(self.run)), 18)
        self.assertEqual(out.getvalue().count("ok "), 24)
        leftovers = [p.name for p in (self.run / "pages").iterdir() if not p.name.endswith(".txt")]
        self.assertEqual(leftovers, [])

    def test_stale_lock_is_broken_and_a_live_one_kept(self):
        url = "https://example.org/locked"
        lock = self.run / "pages" / (hashlib.sha1(vc.norm_url(url).encode("utf-8")).hexdigest()[:12] + ".lock")
        lock.touch()
        os.utime(lock, (time.time() - 3600,) * 2)  # left by a fetch that was killed an hour ago
        start = time.time()
        lines = self.fetch([url], lambda req, timeout: FakeResponse(PROSE.encode(), "text/html"))
        self.assertLess(time.time() - start, 5)
        self.assertTrue(lines[0].startswith("ok "), lines)
        self.assertFalse(lock.exists())
        lock.touch()  # a live fetch holds it: the ok snapshot is read at once and the lock is left alone
        start = time.time()
        fetched = vc.snap_head(next((self.run / "pages").glob("*.txt")))[0]["Fetched"][:10]
        self.assertEqual(self.fetch([url], mock.Mock(side_effect=AssertionError("downloaded again"))),
                         [f"{lines[0]} (cached {fetched})"])
        self.assertLess(time.time() - start, 5)
        self.assertTrue(lock.exists())

    def test_fresh_lock_without_a_holder_delays_only_up_to_the_cap(self):
        url = "https://example.org/held"
        lock = self.run / "pages" / (hashlib.sha1(vc.norm_url(url).encode("utf-8")).hexdigest()[:12] + ".lock")
        lock.touch()  # left a moment ago by a fetch that was killed
        start = time.time()
        with mock.patch.object(vc, "LOCK_WAIT", 0.5), mock.patch.object(vc, "LOCK_STALE", 3600):
            lines = self.fetch([url], lambda req, timeout: FakeResponse(PROSE.encode(), "text/html"))
        self.assertTrue(0.5 <= time.time() - start < 5, time.time() - start)
        self.assertTrue(lines[0].startswith("ok "), lines)
        self.assertTrue(lock.exists())  # not this fetch's lock, so it is left alone
        self.assertEqual((vc.LOCK_WAIT, vc.LOCK_STALE), (30, 60))

    def test_download_deadline_spans_retries_and_slow_bodies(self):
        calls, sleeps = [], []

        def busy(req, timeout):
            calls.append(timeout)
            raise http_error(req.full_url, 503)

        class Trickle(FakeResponse):
            def read(self, size=-1):
                time.sleep(0.05)
                return b"x" * 100

            read1 = read

        with mock.patch.object(vc, "DEADLINE", 1), mock.patch.object(vc, "sleep", sleeps.append):
            lines = self.fetch(["https://a.org/busy"], busy)
        self.assertTrue(lines[0].startswith("http-503 "), lines)
        self.assertEqual((len(calls), sleeps), (1, []))  # a 2 s retry wait would pass the deadline
        start = time.time()
        with mock.patch.object(vc, "DEADLINE", 0.3):
            lines = self.fetch(["https://a.org/slow"], lambda req, timeout: Trickle(b"", "text/html"))
        self.assertLess(time.time() - start, 3)
        self.assertTrue(lines[0].startswith("TimeoutError"), lines)
        self.assertEqual(vc.DEADLINE, 30)

    def test_download_reads_one_network_chunk_at_a_time(self):
        # review round 3: a buffered read(64 KB) waits for 64 KB, so a trickling server outlived the deadline
        class Buffered(FakeResponse):
            def read(self, size=-1):
                time.sleep(2)
                return b"x" * 100

            def read1(self, size=-1):
                time.sleep(0.05)
                return b"x" * 100

        start = time.time()
        with mock.patch.object(vc, "DEADLINE", 0.3):
            lines = self.fetch(["https://a.org/trickle"], lambda req, timeout: Buffered(b"", "text/html"))
        self.assertLess(time.time() - start, 1.5)
        self.assertTrue(lines[0].startswith("TimeoutError"), lines)

    def test_fetch_refresh_downloads_again_and_cached_lines_say_so(self):
        calls, page = [], {"html": "<p>Tarife 2,61 TL olarak açıklandı.</p>" + PROSE}

        def opener(req, timeout):
            calls.append(req.full_url)
            return FakeResponse(page["html"].encode(), "text/html")

        first = self.fetch(["https://example.org/t"], opener)
        fetched = vc.snap_head(self.run / "pages" / first[0].split()[1])[0]["Fetched"][:10]
        self.assertRegex(fetched, r"^\d{4}-\d\d-\d\d$")
        self.assertEqual(self.fetch(["https://example.org/t"], opener), [f"{first[0]} (cached {fetched})"])
        page["html"] = "<p>Tarife 2,75 TL olarak açıklandı.</p>" + PROSE
        out = io.StringIO()
        with mock.patch.object(vc, "urlopen", opener), contextlib.redirect_stdout(out):
            self.assertEqual(vc.main(["fetch", str(self.run), "--refresh", "https://example.org/t"]), 0)
        self.assertEqual((len(calls), out.getvalue().startswith("ok "), "cached" in out.getvalue()), (2, True, False))
        self.assertIn("2,75 TL", vc.load_snapshots(self.run)["example.org/t"])
        page["html"] = "".join(f"<li>Menu item {i}</li>" for i in range(40))  # blocked now: the ok page is kept
        out = io.StringIO()
        with mock.patch.object(vc, "urlopen", opener), contextlib.redirect_stdout(out):
            vc.main(["fetch", str(self.run), "--refresh", "https://example.org/t"])
        self.assertTrue(out.getvalue().startswith("boilerplate - "), out.getvalue())
        self.assertIn("kept", out.getvalue())
        self.assertIn("2,75 TL", vc.load_snapshots(self.run)["example.org/t"])
        self.assertEqual([p.suffix for p in (self.run / "pages").iterdir()], [".txt"])

    def test_find_prints_the_snapshot_file_line_numbers(self):
        # follow-up test: find's line 13 was line 20 of pages/<file>.txt
        def opener(req, timeout):
            return FakeResponse(("<html><head><title>İSKİ</title></head><body><p>Giriş paragrafı burada.</p>"
                                 "<p>İSKİ baraj doluluk oranı yüzde 41 olarak açıklandı.</p>" + PROSE).encode(),
                                "text/html")

        self.page(URL2, "Satır bir.\nSatır iki.\nBaraj hattı burada da geçer.")  # a v0.0.4 header of four lines
        out = self.fetch(["https://iski.istanbul/baraj"], opener, find="baraj")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            vc.cmd_find(self.run, "baraj")
        shown = [(n, t) for n, _, t in (line.strip().partition(": ") for line in out[1:] + buf.getvalue().splitlines())
                 if n.isdigit() and "araj" in t]
        self.assertEqual(len(shown), 3, shown)
        files = [p.read_text(encoding="utf-8").split("\n") for p in (self.run / "pages").glob("*.txt")]
        for number, text in shown:
            self.assertTrue(any(f[int(number) - 1:int(number)] == [text] for f in files), (number, text))

    def test_save_leaves_no_temp_file_when_the_move_fails(self):
        def stuck(src, dst):
            raise PermissionError("in use")

        with mock.patch.object(vc.os, "replace", stuck), mock.patch.object(vc.time, "sleep", lambda s: None), \
                self.assertRaises(PermissionError):
            vc.save(self.run / "pages" / "a.txt", "body")
        self.assertEqual(list((self.run / "pages").iterdir()), [])

    def test_unreadable_snapshot_is_skipped(self):
        self.page(URL1, "Fiyat 2,61 TL")
        self.page(URL2, "Nüfus 300")
        real = vc.snap_head

        def flaky(path):
            if path.name == "p0.txt":
                raise PermissionError("being replaced by another fetch")
            return real(path)

        with mock.patch.object(vc, "snap_head", flaky):
            self.assertEqual(list(vc.load_snapshots(self.run)), [vc.norm_url(URL2)])

    def test_status_header_wins_over_a_legacy_index_row(self):
        # review round 3: a URL that failed in a v0.0.4 folder stayed excluded after an ok fetch there
        self.page(URL1, "Fiyat 2,61 TL")  # a v0.0.4 snapshot: no Status header, so its index row counts
        (self.run / "pages" / "p1.txt").write_text(f"URL: {URL2}\nFetched: 2026-10-31T10:00:00+00:00\nStatus: ok\n"
                                                   "Title: T\n\nNüfus 300", encoding="utf-8")
        (self.run / "pages" / "index.tsv").write_text(f"{URL1}\tp0.txt\thttp-503\t2026-10-28\n"
                                                      f"{URL2}\tp1.txt\thttp-503\t2026-10-28\n", encoding="utf-8")
        self.assertEqual(list(vc.load_snapshots(self.run)), [vc.norm_url(URL2)])

    def test_find_reads_the_body_not_the_layout_copy(self):
        self.page("https://x.org/doc.pdf", "Baraj doluluk oranı yüzde 41 oldu.")
        stem = next((self.run / "pages").glob("*.txt")).stem
        (self.run / "pages" / f"{stem}.layout.txt").write_text("Baraj   doluluk   oranı   yüzde 41", encoding="utf-8")
        self.assertIn("Baraj   doluluk", vc.load_snapshots(self.run)["x.org/doc.pdf"])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            vc.cmd_find(self.run, "baraj")
        self.assertEqual(buf.getvalue().count("araj"), 1, buf.getvalue())

    def test_save_uses_a_private_temp_name_and_retries_permission_errors(self):
        calls, real, target = [], os.replace, self.run / "pages" / "a.txt"

        def flaky(src, dst):
            calls.append(Path(src).name)
            if len(calls) < 3:
                raise PermissionError("in use")
            real(src, dst)

        with mock.patch.object(vc.os, "replace", flaky), mock.patch.object(vc.time, "sleep", lambda s: None):
            vc.save(target, "body")
        self.assertEqual(target.read_text(encoding="utf-8"), "body")
        self.assertEqual(len(calls), 3)
        self.assertIn(str(os.getpid()), calls[0])

    def test_unexpected_error_stays_on_its_line(self):
        real = vc.save

        def save(path, data):
            if "boom" in str(data)[:100]:
                raise PermissionError("in use")
            real(path, data)

        with mock.patch.object(vc, "save", save):
            lines = self.fetch(["https://x.org/boom", "https://x.org/fine"],
                               lambda req, timeout: FakeResponse(PROSE.encode(), "text/html"))
        self.assertEqual(lines[0], "error:PermissionError - 0")
        self.assertTrue(lines[1].startswith("ok "), lines)

    def test_non_ascii_url_is_quoted_for_the_request(self):
        seen, url = [], "https://tr.wikipedia.org/wiki/Çınarcık"

        def opener(req, timeout):
            seen.append(req.full_url)
            return FakeResponse(PROSE.encode(), "text/html")

        lines = self.fetch([url], opener)
        self.assertEqual(seen, ["https://tr.wikipedia.org/wiki/%C3%87%C4%B1narc%C4%B1k"])
        self.assertTrue(lines[0].startswith("ok "), lines)
        raw = next((self.run / "pages").glob("*.txt")).read_text(encoding="utf-8")
        self.assertTrue(raw.startswith(f"URL: {url}\n"), raw[:80])
        self.assertIn(vc.norm_url(url), vc.load_snapshots(self.run))

    def test_title_header_from_meta_title_or_body(self):
        pages = {"cite": '<html><head><title>Site | Home</title><meta name="citation_title" content="Kaplıcalar &amp; '
                         'Tarih"><meta property="og:title" content="OG"></head><body>' + PROSE + '</body></html>',
                 "og": '<html><head><meta content="Open Graph Başlığı" property="og:title"><title>Yedek</title></head>'
                       '<body>' + PROSE + '</body></html>',
                 "plain": '<html><head><title> Çınarcık\n İlçesi </title></head><body><svg><title>ikon</title></svg>'
                          + PROSE + '</body></html>',
                 "none": '<body><p>Skip to main content</p><p>Menü</p><p>| Search: Submit Search</p>' + PROSE + '</body>'}
        lines = self.fetch([f"https://t.org/{k}" for k in pages],
                           lambda req, timeout: FakeResponse(pages[req.full_url.rsplit("/", 1)[1]].encode(), "text/html"))
        self.assertEqual([line.split(" ", 3)[3] for line in lines],
                         ["Kaplıcalar & Tarih", "Open Graph Başlığı", "Çınarcık İlçesi",
                          "Paragraph 0: the regulator published the full tariff table and the explanatory notes today."])
        raws = [p.read_text(encoding="utf-8") for p in (self.run / "pages").glob("*.txt")]
        self.assertTrue(any("\nTitle: Kaplıcalar & Tarih\n\n" in raw for raw in raws))

    def test_find_prints_only_hits_under_their_url(self):
        self.page("https://www.iski.istanbul/baraj", "İSKİ baraj doluluk oranı yüzde 41.")
        self.page("https://a.org/other", "Başka bir sayfa.")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            vc.cmd_find(self.run, "baraj", ["https://www.iski.istanbul/baraj", "https://a.org/other", "https://none.org/z"])
        out = buf.getvalue().splitlines()
        self.assertEqual(out[0], "https://www.iski.istanbul/baraj")
        self.assertIn("İSKİ baraj", out[1])
        self.assertEqual(out[-1], "1 page without hits; 1 URL without a snapshot: https://none.org/z")
        self.assertNotIn("(no hit)", buf.getvalue())

    def test_host_limit_two_at_a_time(self):
        state, lock = {"now": 0, "peak": 0}, threading.Lock()

        def opener(req, timeout):
            with lock:
                state["now"] += 1
                state["peak"] = max(state["peak"], state["now"])
            time.sleep(0.03)
            with lock:
                state["now"] -= 1
            return FakeResponse(PROSE.encode(), "text/html")

        self.fetch([f"https://one.org/p{i}" for i in range(6)], opener)
        self.assertEqual(state["peak"], 2)

    def test_find_passages_turkish_folding_and_limits(self):
        lines = [f"Satır {i}: genel bilgi ve duyurular burada yer alır." for i in range(60)]
        for i in (5, 20, 35, 50):
            lines[i] = f"İSKİ baraj doluluk oranı {i} yüzde olarak açıklandı. " * 8
        text = "\n".join(lines)
        found = vc.passages(text, ["iski", "baraj"])
        self.assertEqual(len(found), 3)
        self.assertLessEqual(sum(map(len, found)), 1500)
        self.assertRegex(found[0], r"^\d+: ")
        self.assertIn("İSKİ", found[0])
        self.assertEqual(vc.passages(text, ["yok-böyle-bir-şey"]), [])
        short = vc.passages("a\nb\nİski raporu\nc\nd\ne\nf", ["ISKI"])
        self.assertEqual(short, ["1: a\n2: b\n3: İski raporu\n4: c\n5: d"])

        def opener(req, timeout):
            return FakeResponse(("<p>İSKİ baraj doluluk oranı yüzde 41 olarak açıklandı.</p>" + PROSE).encode(),
                                "text/html")

        out = self.fetch(["https://iski.istanbul/baraj"], opener, find="iski|baraj")
        self.assertTrue(out[0].startswith("ok "), out)
        self.assertTrue(any("İSKİ baraj doluluk" in line for line in out[1:]), out)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(vc.main(["find", str(self.run), "BARAJ"]), 0)
        self.assertIn("İSKİ baraj doluluk", buf.getvalue())
        self.assertIn("iski.istanbul/baraj", buf.getvalue())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            vc.cmd_find(self.run, "baraj", ["https://other.org/x"])
        self.assertNotIn("İSKİ", buf.getvalue())

    def test_retry_after_on_429_and_503(self):
        calls, sleeps = collections.Counter(), []

        def opener(req, timeout):
            calls[req.full_url] += 1
            if req.full_url.endswith("/busy"):
                raise http_error(req.full_url, 503)
            if calls[req.full_url] == 1:
                raise http_error(req.full_url, 429, "30")
            if calls[req.full_url] == 2:
                raise http_error(req.full_url, 503)
            return FakeResponse(PROSE.encode(), "text/html")

        with mock.patch.object(vc, "sleep", sleeps.append):
            lines = self.fetch(["https://a.org/slow"], opener)
            self.assertTrue(lines[0].startswith("ok "), lines)
            self.assertEqual(sleeps, [10, 5])
            sleeps.clear()
            lines = self.fetch(["https://a.org/busy"], opener)
        self.assertTrue(lines[0].startswith("http-503 "), lines)
        self.assertEqual(sleeps, [2, 5])
        self.assertEqual(calls["https://a.org/busy"], 3)

    def test_table_rows_count_as_content(self):
        table = "<table>" + "".join(f"<tr><td>İlçe {i}</td><td>{i * 37}</td><td>2,{i:02} TL</td></tr>"
                                    for i in range(30)) + "</table>"
        menu = "<ul>" + "".join(f'<li><a href="/m{i}">Menü {i}</a></li>' for i in range(50)) + "</ul>"
        bodies = {"table": table, "menu": menu}
        lines = self.fetch(["https://x.org/table", "https://x.org/menu"],
                           lambda req, timeout: FakeResponse(bodies[req.full_url.rsplit("/", 1)[1]].encode(),
                                                             "text/html"))
        self.assertTrue(lines[0].startswith("ok "), lines)
        self.assertTrue(lines[1].startswith("boilerplate "), lines)

    def pdf_fetch(self, which, body="Reading order paragraph about water tariffs in the city. " * 12, hook=None,
                  layout=None):
        raw, runs = b"%PDF-1.4 fake", []

        def fake_run(args, **kwargs):
            runs.append(args)
            if hook:
                hook(args, kwargs)
            text = "LAYOUT col1     col2\n" + (layout or body) if "-layout" in args else body
            Path(args[-1]).write_text(text, encoding="utf-8")

        with mock.patch.object(vc.shutil, "which", lambda name: which), \
                mock.patch.object(vc.subprocess, "run", fake_run):
            lines = self.fetch(["https://x.org/doc.pdf"], lambda req, timeout: FakeResponse(raw, "application/pdf"))
        return lines, runs, raw

    def test_pdf_runs_have_short_timeouts_and_keep_the_lock_fresh(self):
        lock = self.run / "pages" / (hashlib.sha1(b"x.org/doc.pdf").hexdigest()[:12] + ".lock")
        seen = []

        def hook(args, kwargs):
            seen.append((kwargs["timeout"], time.time() - lock.stat().st_mtime))
            os.utime(lock, (time.time() - 3600,) * 2)  # as if this conversion had run for an hour
            if "-layout" in args:
                raise subprocess.TimeoutExpired(args, kwargs["timeout"])

        lines, runs, _ = self.pdf_fetch("pdftotext", hook=hook)
        self.assertTrue(lines[0].startswith("ok "), lines)
        self.assertEqual([t for t, _ in seen], [50, 30])
        self.assertTrue(all(age < 5 for _, age in seen), seen)  # touched before each run
        self.assertEqual(list((self.run / "pages").glob("*.layout.txt")), [])  # a timed-out layout run is skipped
        self.assertFalse(lock.exists())

    def test_pdf_reading_order_and_layout_copy(self):
        lines, runs, _ = self.pdf_fetch("pdftotext")
        self.assertTrue(lines[0].startswith("ok "), lines)
        self.assertNotIn("-layout", runs[0])
        self.assertIn("-layout", runs[1])
        self.assertEqual(len(list((self.run / "pages").glob("*.layout.txt"))), 1)
        snaps = vc.load_snapshots(self.run)
        self.assertEqual(list(snaps), ["x.org/doc.pdf"])
        self.assertIn("Reading order paragraph", snaps["x.org/doc.pdf"])
        self.assertIn("LAYOUT col1", snaps["x.org/doc.pdf"])

    def test_pdf_title_skips_numbers_labels_and_issn(self):
        body = ("87\nISSN: 0041-4255 · e-ISSN: 2791-7584\nS a y f a | 75\nYalova Kaplıcalarının Osmanlı Dönemi\n"
                + "Reading order paragraph about water tariffs in the city. " * 12)
        lines, _, _ = self.pdf_fetch("pdftotext", body)
        self.assertTrue(lines[0].startswith("ok ") and lines[0].endswith(" Yalova Kaplıcalarının Osmanlı Dönemi"), lines)

    def test_pdf_title_skips_the_masthead(self):
        # title check 2026-10-31: DergiPark PDFs were titled by their journal masthead, not the article
        for head, title in (
                ("UNIMUSEUM\nInternational University Museums Association Platform\nARAŞTIRMA MAKALESİ / RESEARCH "
                 "ARTICLE\n", "THE MOVING HOUSE OR ATATÜRK HOUSE MUSEUM"),
                ("İNSAN VE TOPLUM BİLİMLERİ ARAŞTIRMALARI DERGİSİ Cilt: 5, Sayı: 8, 2016 Sayfa: 2782-2816\n",
                 "Çerkes Göçleri ve Çerkeslerin Anadolu’da Yurt Edinme Arayışları"),
                ("KUJES 7(1):27-53, 2021\nInternational Journal of Social and Educational Sciences, 2017\n",
                 "Population Change in a Province"),
                ("Millî Saraylar, Yıl: 2022, S: 23, s. 66-85\nMakale Gönderim Tarihi: 16.07.2018\nAraştırma Makalesi "
                 "DOI: 10.54078/savsad.1626262\nE-mail: yazar@example.org\n", "Nüfus Coğrafyası Açısından Bir İnceleme")):
            with self.subTest(title=title):
                for path in (self.run / "pages").iterdir():
                    path.unlink()
                lines, _, _ = self.pdf_fetch("pdftotext", f"{head}{title}\n" + "Reading order paragraph. " * 30)
                self.assertTrue(lines[0].endswith(f" {title}"), lines)

    def test_pdf_table_only_uses_layout(self):
        # review round 3: reading order put each table cell on its own line, so the page read as boilerplate
        cells = "".join(f"İlçe {i}\n{1000 + i * 37}\n2,{i:02} TL\n" for i in range(30))
        rows = "".join(f"İlçe {i}       {1000 + i * 37} abone       2,{i:02} TL/kWh       2026\n" for i in range(30))
        self.assertEqual((vc.page_status(cells), vc.page_status(rows)), ("boilerplate", "ok"))
        lines, runs, _ = self.pdf_fetch("pdftotext", cells, layout=rows)
        self.assertTrue(lines[0].startswith("ok ") and ".txt" in lines[0], lines)
        raw = (self.run / "pages" / lines[0].split()[1]).read_text(encoding="utf-8")
        self.assertIn("\nCharset: pdf-layout\n", raw)
        self.assertIn("İlçe 7       1259 abone", vc.load_snapshots(self.run)["x.org/doc.pdf"])
        self.assertEqual([p.name.split(".", 1)[1] for p in (self.run / "pages").iterdir()], ["txt"])  # no layout copy

    def test_scanned_pdf_is_saved_for_the_pdf_reader(self):
        lines, runs, raw = self.pdf_fetch("pdftotext", "\f\n  \n")
        self.assertTrue(lines[0].startswith("pdf-saved ") and ".pdf" in lines[0], lines)
        self.assertEqual([p.read_bytes() for p in (self.run / "pages").glob("*.pdf")], [raw])
        self.assertEqual(vc.load_snapshots(self.run), {})

    def test_pdf_saved_without_pdftotext(self):
        lines, runs, raw = self.pdf_fetch(None)
        self.assertEqual(runs, [])
        self.assertTrue(lines[0].startswith("pdf-saved ") and ".pdf" in lines[0], lines)
        self.assertEqual([p.read_bytes() for p in (self.run / "pages").glob("*.pdf")], [raw])
        self.assertEqual(vc.load_snapshots(self.run), {})


class LocalServer:
    """An HTTP server on 127.0.0.1 that counts GETs per path; a path in `hold` waits until `release` is set."""

    def __init__(self):
        self.counts, self.lock, self.hold = collections.Counter(), threading.Lock(), set()
        self.seen, self.release, server = threading.Event(), threading.Event(), self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                with server.lock:
                    server.counts[self.path] += 1
                if self.path in server.hold:
                    server.seen.set()
                    server.release.wait(60)
                body = (f"<p>Page {self.path}</p>" + PROSE).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                with contextlib.suppress(OSError):
                    self.wfile.write(body)

            def log_message(self, *args):
                pass

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.release.set()
        self.httpd.shutdown()
        self.httpd.server_close()


class ProcessTests(RunCase):
    """Real `fetch` processes against a local server: Review Focus 3 across processes, and a killed fetch."""

    def setUp(self):
        super().setUp()
        self.server = LocalServer()
        self.env = {**os.environ, "NO_PROXY": "*", "no_proxy": "*"}

    def tearDown(self):
        self.server.close()
        super().tearDown()

    def spawn(self, *urls):
        return subprocess.Popen([sys.executable, str(SCRIPT), "fetch", str(self.run), *urls], env=self.env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_two_processes_fetch_overlapping_urls(self):
        urls = [f"{self.server.url}/p{i}" for i in range(18)]
        procs = [self.spawn(*urls[:12]), self.spawn(*urls[6:])]
        outs, errs = zip(*[(b.decode("utf-8") for b in proc.communicate(timeout=120)) for proc in procs])
        self.assertEqual([proc.returncode for proc in procs], [0, 0], errs)
        self.assertEqual(dict(self.server.counts), {f"/p{i}": 1 for i in range(18)})
        self.assertEqual([line[:3] for out in outs for line in out.splitlines()], ["ok "] * 24, outs)
        self.assertEqual(len(vc.load_snapshots(self.run)), 18)
        self.assertEqual([p.name for p in (self.run / "pages").iterdir() if not p.name.endswith(".txt")], [])

    def test_killed_fetch_delays_a_retry_only_up_to_the_cap(self):
        url = f"{self.server.url}/slow"
        self.server.hold.add("/slow")
        proc = self.spawn(url)
        self.assertTrue(self.server.seen.wait(60))  # the fetch holds the URL's lock and waits for the body
        proc.kill()
        proc.communicate(timeout=60)
        self.assertEqual(len(list((self.run / "pages").glob("*.lock"))), 1)
        self.server.hold.clear()
        self.server.release.set()
        out, start = io.StringIO(), time.time()
        with mock.patch.object(vc, "LOCK_WAIT", 1), mock.patch.dict(os.environ, {"no_proxy": "*"}), \
                contextlib.redirect_stdout(out):
            vc.cmd_fetch(self.run, [url])
        self.assertLess(time.time() - start, 15)
        self.assertTrue(out.getvalue().startswith("ok "), out.getvalue())
        self.assertIn(vc.norm_url(url), vc.load_snapshots(self.run))


if __name__ == "__main__":
    unittest.main()
