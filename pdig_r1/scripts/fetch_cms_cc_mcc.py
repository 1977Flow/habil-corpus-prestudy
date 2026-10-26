"""Fetch CMS MS-DRG v41.1 Appendix G (CC) and H (MCC) diagnosis lists.
Source: https://www.cms.gov/icd10m/FY2024-version41.1-fullcode-cms/fullcode_cms/
Output: ../cms/cc_mcc_v41_1.csv (code,level,appendix_page)"""
import re, html, csv, time, urllib.request
from pathlib import Path
B = "https://www.cms.gov/icd10m/FY2024-version41.1-fullcode-cms/fullcode_cms/"
OUT = Path(__file__).resolve().parent.parent / "cms"
def get(p):
    f = OUT / "pages" / p
    if f.exists():
        return f.read_text(encoding="latin-1")
    req = urllib.request.Request(B + p, headers={"User-Agent": "Mozilla/5.0"})
    t = urllib.request.urlopen(req, timeout=60).read().decode("latin-1")
    f.parent.mkdir(exist_ok=True); f.write_text(t, encoding="latin-1"); time.sleep(0.3)
    return t
def crawl(start, level, heading_key):
    rows, p, seen = [], start, set()
    while p and p not in seen:
        seen.add(p); t = get(p)
        head = re.search(r'class="heading">([^<]+)</td>', t)
        if not head or heading_key not in head.group(1):
            break
        for code in re.findall(r"<td nowrap class=code>([A-Z0-9]+)</td>", t):
            rows.append((code, level, p))
        nxt = re.search(r'id="next_page" href="([^"]+)"', t)
        p = nxt.group(1) if nxt else None
    return rows
rows = crawl("P0392.html", "CC", "Appendix G") + crawl("P0393.html", "MCC", "Appendix H Part 1")
with open(OUT / "cc_mcc_v41_1.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["code", "level", "page"]); w.writerows(rows)
from collections import Counter
print(Counter(r[1] for r in rows), len({r[0] for r in rows}))
