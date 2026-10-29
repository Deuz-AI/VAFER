"""Offline tests for skills/vafer-research/scripts/vafer_check.py."""

from __future__ import annotations

import email.message
import io
import shutil
import sys
import tempfile
import unittest
import urllib.error
from decimal import Decimal
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "skills" / "vafer-research" / "scripts"))
import vafer_check as vc  # noqa: E402

URL1 = "https://www.epdk.gov.tr/tarifeler"
URL2 = "https://example.org/report/"
PROSE = "".join(f"<p>Paragraph {i}: the regulator published the full tariff table and the explanatory notes today.</p>"
                for i in range(3))


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
        self.assertEqual(self.kinds(), ["quote-near", "quote-mismatch"])

    def test_dangling_and_unused(self):
        self.page(URL1, "nothing numeric")
        self.page(URL2, "nothing numeric")
        self.report("See the tariff [1; 7].", sources=((1, URL1), (2, URL2)))
        self.check()
        self.assertEqual(sorted(self.kinds()), ["dangling", "unused"])

    def test_kaynaklar_heading_and_url_normalization(self):
        self.page("http://epdk.gov.tr/tarifeler?utm_source=x#top", "Fiyat 2,61 TL")
        self.report("Fiyat 2,61 TL [1].", heading="### Kaynakça")
        result = self.check()
        self.assertEqual(self.kinds(), [])
        self.assertEqual(result["matched"], 1)

    def test_label_leak(self):
        self.page(URL1, "x")
        self.report("This part is PARTIAL [GAP] per the researcher [1].")
        self.check()
        self.assertEqual(self.kinds().count("label-leak"), 3)

    def test_uncited_number(self):
        self.page(URL1, "Fiyat 2,61 TL")
        self.report("Fiyat 2,61 TL [1]. Hane sayısı 4.500 oldu. In 2024 there were 3 plans.")
        self.check()
        self.assertEqual(self.kinds(), ["uncited"])
        self.assertIn("4.500", self.result["flags"][0]["detail"])

    def test_unverifiable_source(self):
        self.report("Nothing [1].")
        self.check()
        self.assertEqual(self.kinds(), ["unverifiable"])

    def test_summary_line_replaced_and_check_md(self):
        self.page(URL1, "Fiyat 2,61 TL")
        self.report("Fiyat 2,61 TL [1].\n\n**Kaynak kontrolü:** pending")
        result = self.check()
        text = (self.run / "report.md").read_text(encoding="utf-8")
        self.assertIn("**Kaynak kontrolü:** script, page snapshots — 1 of 1 figures matched", text)
        self.assertNotIn("pending", text)
        self.assertIn(result["summary"], (self.run / "check.md").read_text(encoding="utf-8"))

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
        self.assertIn("low severity", self.result["flags"][0]["detail"])

    def test_mid_line_check_label_and_date_lines(self):
        self.page(URL1, "Fiyat 2,61 TL")
        self.report("Tarih: 2026-10-29 · Source check: pending\n\nAs of: 29 October 2026\n\n"
                    "Güncel: 2026-10-01\n\nFiyat 2,61 TL [1].")
        self.check()
        self.assertEqual(self.kinds(), [])
        text = (self.run / "report.md").read_text(encoding="utf-8")
        self.assertIn("Tarih: 2026-10-29 · Source check: script, page snapshots", text)
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


class FakeResponse(io.BytesIO):
    def __init__(self, body, ctype):
        super().__init__(body)
        self.headers = email.message.Message()
        self.headers["Content-Type"] = ctype


class FetchTests(RunCase):
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
            calls.append(req.get_header("User-agent"))
            if req.full_url.endswith("/bad"):
                raise urllib.error.URLError("no route")
            if len(calls) == 1:
                raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", None, None)
            return FakeResponse(("<p>Çalışma ücreti 7,25 TL</p>" + PROSE).encode("iso-8859-9"),
                                "text/html; charset=iso-8859-9")

        original = vc.urlopen
        vc.urlopen = fake_urlopen
        out = io.StringIO()
        try:
            stdout, sys.stdout = sys.stdout, out
            vc.cmd_fetch(self.run, ["https://example.org/ok", "https://example.org/bad"])
        finally:
            sys.stdout = stdout
            vc.urlopen = original
        lines = out.getvalue().splitlines()
        self.assertTrue(lines[0].startswith("ok ") and lines[1].startswith("failed "), lines)
        self.assertNotEqual(calls[0], calls[1])
        self.assertIn("Çalışma ücreti 7,25 TL", vc.load_snapshots(self.run)["example.org/ok"])
        index = (self.run / "pages" / "index.tsv").read_text(encoding="utf-8")
        self.assertIn("https://example.org/bad\t\t", index)

    def test_empty_boilerplate_doc_binary_and_utf16(self):
        bodies = {"empty": (b"<p>Loading...</p>", "text/html"),
                  "nav": ("".join(f"<li>Menu item {i}</li>" for i in range(40)).encode(), "text/html"),
                  "doc": (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 64, "application/octet-stream"),
                  "u16": (("Çalışma ücreti 7,25 TL\n" + PROSE).encode("utf-16"), "text/html; charset=iso-8859-9")}
        original = vc.urlopen
        vc.urlopen = lambda req, timeout: FakeResponse(*bodies[req.full_url.rsplit("/", 1)[1]])
        out = io.StringIO()
        try:
            stdout, sys.stdout = sys.stdout, out
            vc.cmd_fetch(self.run, [f"https://example.org/{k}" for k in bodies])
        finally:
            sys.stdout = stdout
            vc.urlopen = original
        lines = out.getvalue().splitlines()
        self.assertTrue(lines[0].startswith("failed empty (saved "), lines)
        self.assertTrue(lines[1].startswith("failed boilerplate (saved "), lines)
        self.assertEqual(lines[2], "failed doc-binary")
        self.assertTrue(lines[3].startswith("ok "), lines)
        self.assertEqual(len(list((self.run / "pages").glob("*.txt"))), 3)
        snaps = vc.load_snapshots(self.run)
        self.assertEqual(list(snaps), ["example.org/u16"])
        self.assertIn("Çalışma ücreti 7,25 TL", snaps["example.org/u16"])


if __name__ == "__main__":
    unittest.main()
