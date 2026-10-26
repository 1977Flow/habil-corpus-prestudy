"""PDIG R1: retention of ED-assigned codes in the subsequent hospital claim, by ICD-10-CM chapter.
Same episode set as mimic_coding_context.py. Output: ../results/mimic_retention.json"""
import ast
import json
import os
from collections import Counter
from pathlib import Path

import pandas as pd

SRC = Path(os.environ.get("MIMIC_ECG_ICD_CSV", "records_w_diag_icd10.csv"))  # PhysioNet credentialed file, not distributed
OUT = Path(__file__).resolve().parent.parent / "results" / "mimic_retention.json"
CHAPTERS = {"R": "R symptoms, signs, abnormal findings", "Z": "Z factors influencing health status",
            "S": "S-T injury, poisoning", "T": "S-T injury, poisoning", "I": "I circulatory",
            "E": "E endocrine, metabolic", "J": "J respiratory", "F": "F mental, behavioural",
            "N": "N genitourinary", "K": "K digestive"}


def chap(c):
    return CHAPTERS.get(c[0], "other")


def main():
    df = pd.read_csv(SRC, usecols=["ed_stay_id", "ed_hadm_id", "ed_diag_ed", "ed_diag_hosp"])
    df = df.dropna(subset=["ed_stay_id", "ed_hadm_id"]).drop_duplicates("ed_stay_id")
    ed = df.ed_diag_ed.map(lambda s: list(dict.fromkeys(ast.literal_eval(s))) if isinstance(s, str) else [])
    hosp = df.ed_diag_hosp.map(lambda s: set(ast.literal_eval(s)) if isinstance(s, str) else set())
    keep = (ed.str.len() > 0) & (hosp.str.len() > 0)
    ed, hosp = ed[keep], hosp[keep]
    tot, ret, hosp_ch = Counter(), Counter(), Counter()
    for e, h in zip(ed, hosp):
        for c in e:
            tot[chap(c)] += 1
            ret[chap(c)] += c in h
        for c in h:
            hosp_ch[chap(c)] += 1
    T, H = sum(tot.values()), sum(hosp_ch.values())
    res = {"episodes": int(keep.sum()), "ed_codes": T, "hosp_codes": H,
           "ed_codes_retained": sum(ret.values()), "retention_overall": round(sum(ret.values()) / T, 4),
           "by_chapter": {k: {"ed_share": round(tot[k] / T, 4), "retained": round(ret[k] / tot[k], 4),
                              "hosp_share": round(hosp_ch[k] / H, 4)}
                          for k in sorted(tot, key=lambda x: -tot[x])}}
    OUT.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
