"""Offline tests for skills/vafer-research/scripts/vafer_check.py."""

from __future__ import annotations

import collections
import contextlib
import email.message
import io
import shutil
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
sys.path.insert(0, str(REPOSITORY / "skills" / "vafer-research" / "scripts"))
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


class SentenceTests(unittest.TestCase):
    def test_abbreviations_and_roman_numerals_do_not_split(self):
        line = ("II. Abdülhamid tahta çıktı. I. Mahmud, I. Derece, S. Sayısı, Dr. Ahmet, vb. Diğer, bkz. Ek, "
                "yy. Sonu, M.Ö. 300 ve s. 45 dahil. Son cümle.")
        self.assertEqual(len(vc.sentences([line])), 3, vc.sentences([line]))

    def test_period_before_digit_never_splits(self):
        line = "See Cmd. 1478 and No. 7596, s. 45. Ayrıca Prof. Ahmet, Doç. Ali, çev. Veli, vol. 2 geldi. Son."
        self.assertEqual(len(vc.sentences([line])), 3, vc.sentences([line]))

    def test_footnote_markers_end_sentence(self):
        line = "First ends here.³ Second ends.¹² Third ends.[^3] Fourth."
        self.assertEqual(vc.sentences([line]), ["First ends here.³", "Second ends.¹²", "Third ends.[^3]", "Fourth."])

    def test_marker_lines_are_not_sentences(self):
        lines = [vc.END_MARK, "Text one. Text two.", vc.SOURCES_MARK, "  <!-- any comment -->"]
        self.assertEqual(vc.sentences(lines), ["Text one.", "Text two."])


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
        self.report("Fiyat 2,61 TL [1].", heading=f"{vc.SOURCES_MARK}\n### Kaynakça")
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
        self.assertIn("**Source check:** script — 1 figure: 0 in a quoted receipt, 1 elsewhere on the cited page, "
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
        self.assertTrue(result["summary"].endswith("; 1 open high/medium flag of 1 (check.md)"), result["summary"])
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
        self.assertIn("Tarih: 2026-10-29 · Source check: script — 1 figure: ", text)
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
        self.assertFalse((self.run / "check.md").exists())
        self.assertEqual((self.run / "evidence.md").read_text(encoding="utf-8"), "Source check: pending\n")


class AssembleTests(RunCase):
    """`assemble` builds report.md from sections/ drafts."""

    def setUp(self):
        super().setUp()
        (self.run / "sections").mkdir()
        self.page("https://a.org/x", "\n\nAlpha Agency Report\nFiyat 2,61 TL ve 300 abone.")
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
        self.assertEqual(tail[3], "[2] Alpha Agency Report https://a.org/x")
        _, sources, _ = vc.parse_report(text)
        self.assertEqual(sources, {1: "https://b.org/y", 2: "https://a.org/x"})

    def test_assemble_rerun_idempotent(self):
        first = self.assemble()
        self.section("s1", "## Bir\n\nFiyat 2,61 TL [https://a.org/x]. Takip sonucu eklendi.")
        self.assemble()
        self.section("s1", "## Bir\n\nFiyat 2,61 TL [https://a.org/x].")
        self.assertEqual(self.assemble(), first)
        self.assertEqual((first.count(vc.END_MARK), first.count(vc.SOURCES_MARK)), (1, 1))

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
            return FakeResponse(("<h1>Tarife duyurusu</h1>" + PROSE).encode(), "text/html")

        lines = self.fetch(["https://example.org/t"], opener)
        status, name, chars, title = lines[0].split(" ", 3)
        self.assertEqual((status, title), ("ok", "Tarife duyurusu"))
        self.assertGreater(int(chars), 400)
        raw = (self.run / "pages" / name).read_text(encoding="utf-8")
        self.assertRegex(raw, r"^URL: https://example.org/t\nFetched: .+\nStatus: ok\nCharset: .+\nSHA256: \w+\n\n")
        self.assertEqual(calls, [("https://example.org/t", 20)])
        again = self.fetch(["https://example.org/t/", "https://www.example.org/t#p3"], opener)
        self.assertEqual(again, [lines[0], lines[0]])
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

    def pdf_fetch(self, which):
        raw, runs = b"%PDF-1.4 fake", []

        def fake_run(args, **kwargs):
            runs.append(args)
            text = "LAYOUT col1     col2\n" if "-layout" in args else ""
            Path(args[-1]).write_text(text + "Reading order paragraph about water tariffs in the city. " * 12,
                                      encoding="utf-8")

        with mock.patch.object(vc.shutil, "which", lambda name: which), \
                mock.patch.object(vc.subprocess, "run", fake_run):
            lines = self.fetch(["https://x.org/doc.pdf"], lambda req, timeout: FakeResponse(raw, "application/pdf"))
        return lines, runs, raw

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

    def test_pdf_saved_without_pdftotext(self):
        lines, runs, raw = self.pdf_fetch(None)
        self.assertEqual(runs, [])
        self.assertTrue(lines[0].startswith("pdf-saved ") and ".pdf" in lines[0], lines)
        self.assertEqual([p.read_bytes() for p in (self.run / "pages").glob("*.pdf")], [raw])
        self.assertEqual(vc.load_snapshots(self.run), {})


if __name__ == "__main__":
    unittest.main()
