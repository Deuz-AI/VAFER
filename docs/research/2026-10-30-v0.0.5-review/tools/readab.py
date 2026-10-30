"""Rough readability stats of a Markdown report: prose sentences, words per sentence, share of long sentences, tables, citations."""
import re, sys
sys.stdout.reconfigure(encoding="utf-8")
for path in sys.argv[1:]:
    text = open(path, encoding="utf-8").read()
    m = re.search(r"^#+\s*(Kaynaklar|Sources|Kaynakça)\s*$", text, re.M | re.I)
    body = text[:m.start()] if m else text
    prose = [l for l in body.splitlines() if l.strip() and not l.lstrip().startswith(("|", "#", "```"))]
    joined = " ".join(re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", l) for l in prose)
    joined = re.sub(r"\[\d+(?:[,\s–-]+\d+)*\]", "", joined)
    sents = [s for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ0-9\"“(])", joined) if len(s.split()) >= 3]
    lens = [len(s.split()) for s in sents]
    tables = sum(1 for l in body.splitlines() if l.lstrip().startswith("|"))
    eng = len(re.findall(r"\b(the|and|of|which|was|were)\b", body))
    heads = len(re.findall(r"^#{2,3} ", body, re.M))
    print(f"{path.split('scratchpad')[-1]}: words {len(text.split())}; prose sentences {len(sents)}; "
          f"mean words/sentence {sum(lens)/max(1,len(lens)):.1f}; >25 words {sum(l>25 for l in lens)}; "
          f"table rows {tables}; headings {heads}; English function words {eng}; citation markers {len(re.findall(r'\[\d+', body))}")
