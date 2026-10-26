"""PDIG-D-26-00980 R1, real-data component.

Same clinical episode, two coding contexts (MIMIC-IV-ECG-Ext-ICD v1.0.1):
  ed_diag_ed   = ICD-10-CM codes assigned during the emergency-department stay
  ed_diag_hosp = ICD-10-CM codes assigned at discharge from the hospital admission
                 that followed that ED stay (the DRG-relevant claim)
Reimbursement relevance is taken from an external, independent list:
CMS MS-DRG v41.1 Appendix G (CC) and H Part 1 (MCC), see fetch_cms_cc_mcc.py.

Data are credentialed (PhysioNet) and stay local; only aggregates are written.
Output: ../results/mimic_coding_context.json
"""
import ast
import json
import os
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

SRC = Path(os.environ.get("MIMIC_ECG_ICD_CSV", "records_w_diag_icd10.csv"))  # PhysioNet credentialed file, not distributed
HERE = Path(__file__).resolve().parent.parent
CCMCC = HERE / "cms" / "cc_mcc_v41_1.csv"
OUT = HERE / "results" / "mimic_coding_context.json"
RNG = np.random.default_rng(20261026)

# Sentinel condition families, ICD-10-CM prefixes (chosen before analysis,
# mirroring the five Box 2 clusters plus two classic CDI targets).
SENTINELS = {
    "diabetes": ("E08", "E09", "E10", "E11", "E13"),
    "hypertension": ("I10", "I11", "I12", "I13", "I15", "I16"),
    "depression": ("F32", "F33"),
    "heart_failure": ("I50",),
    "chronic_kidney_disease": ("N18",),
    "hyponatraemia": ("E871",),
    "malnutrition": ("E40", "E41", "E42", "E43", "E44", "E45", "E46"),
}


def parse(cell):
    if not isinstance(cell, str) or cell in ("", "[]"):
        return []
    return list(dict.fromkeys(ast.literal_eval(cell)))


def jsd_bits(p: Counter, q: Counter) -> float:
    keys = set(p) | set(q)
    ps, qs = sum(p.values()), sum(q.values())
    out = 0.0
    for k in keys:
        a, b = p.get(k, 0) / ps, q.get(k, 0) / qs
        m = (a + b) / 2
        if a:
            out += 0.5 * a * math.log2(a / m)
        if b:
            out += 0.5 * b * math.log2(b / m)
    return out


def main():
    cc = pd.read_csv(CCMCC)
    level = dict(zip(cc.code, cc.level))

    df = pd.read_csv(SRC, usecols=["ed_stay_id", "ed_hadm_id", "subject_id",
                                   "ed_diag_ed", "ed_diag_hosp"])
    df = df.dropna(subset=["ed_stay_id", "ed_hadm_id"]).drop_duplicates("ed_stay_id")
    df["ed"] = df.ed_diag_ed.map(parse)
    df["hosp"] = df.ed_diag_hosp.map(parse)
    df = df[(df.ed.str.len() > 0) & (df.hosp.str.len() > 0)].copy()
    n_ep, n_pat = len(df), df.subject_id.nunique()

    def share(codes, lv):
        return np.mean([level.get(c) in lv for c in codes]) if codes else np.nan

    df["n_ed"], df["n_hosp"] = df.ed.str.len(), df.hosp.str.len()
    df["ccmcc_ed"] = df.ed.map(lambda c: share(c, ("CC", "MCC")))
    df["ccmcc_hosp"] = df.hosp.map(lambda c: share(c, ("CC", "MCC")))
    df["any_mcc_ed"] = df.ed.map(lambda c: any(level.get(x) == "MCC" for x in c))
    df["any_mcc_hosp"] = df.hosp.map(lambda c: any(level.get(x) == "MCC" for x in c))
    df["any_ccmcc_ed"] = df.ed.map(lambda c: any(level.get(x) in ("CC", "MCC") for x in c))
    df["any_ccmcc_hosp"] = df.hosp.map(lambda c: any(level.get(x) in ("CC", "MCC") for x in c))

    # Codes present only in the hospital claim vs present in both contexts
    added, kept = Counter(), Counter()
    for ed, hosp in zip(df.ed, df.hosp):
        s = set(ed)
        for c in hosp:
            (kept if c in s else added)[level.get(c, "none")] += 1
    def frac(cnt):
        t = sum(cnt.values())
        return {k: round(v / t, 4) for k, v in cnt.items()} | {"n": t}

    # Sentinel prevalence in the two contexts, paired (McNemar, exact)
    sentinel = {}
    for name, pref in SENTINELS.items():
        e = df.ed.map(lambda c: any(x.startswith(pref) for x in c)).to_numpy()
        h = df.hosp.map(lambda c: any(x.startswith(pref) for x in c)).to_numpy()
        b, c_ = int((e & ~h).sum()), int((~e & h).sum())
        p = stats.binomtest(min(b, c_), b + c_, 0.5).pvalue if b + c_ else 1.0
        sentinel[name] = {"prev_ed": round(e.mean(), 4), "prev_hosp": round(h.mean(), 4),
                          "ratio_hosp_to_ed": round(h.mean() / e.mean(), 2) if e.mean() else None,
                          "ed_only": b, "hosp_only": c_, "mcnemar_p": float(f"{p:.3g}")}

    # Distribution-level divergence, 3-character categories, with bootstrap CI
    def dist(series):
        return Counter(x[:3] for codes in series for x in codes)
    j = jsd_bits(dist(df.ed), dist(df.hosp))
    boots = []
    idx = np.arange(n_ep)
    for _ in range(200):
        s = df.iloc[RNG.choice(idx, n_ep)]
        boots.append(jsd_bits(dist(s.ed), dist(s.hosp)))

    w = stats.wilcoxon(df.ccmcc_hosp, df.ccmcc_ed)
    res = {
        "source": "MIMIC-IV-ECG-Ext-ICD v1.0.1 (PhysioNet, credentialed); CMS MS-DRG v41.1 App. G/H",
        "episodes": n_ep, "patients": n_pat,
        "codes_per_episode": {"ed_median": float(df.n_ed.median()), "hosp_median": float(df.n_hosp.median()),
                              "ed_mean": round(df.n_ed.mean(), 2), "hosp_mean": round(df.n_hosp.mean(), 2)},
        "ccmcc_share_per_episode": {"ed_mean": round(df.ccmcc_ed.mean(), 4), "hosp_mean": round(df.ccmcc_hosp.mean(), 4),
                                    "wilcoxon_p": float(f"{w.pvalue:.3g}")},
        "episodes_with_any_ccmcc": {"ed": round(df.any_ccmcc_ed.mean(), 4), "hosp": round(df.any_ccmcc_hosp.mean(), 4)},
        "episodes_with_any_mcc": {"ed": round(df.any_mcc_ed.mean(), 4), "hosp": round(df.any_mcc_hosp.mean(), 4)},
        "hosp_codes_by_level": {"added_in_hospital_claim": frac(added), "also_coded_in_ed": frac(kept)},
        "sentinels": sentinel,
        "jsd_3char_ed_vs_hosp_bits": round(j, 4),
        "jsd_bootstrap_95ci": [round(float(np.percentile(boots, 2.5)), 4), round(float(np.percentile(boots, 97.5)), 4)],
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
