"""PDIG-D-26-00980 R1: learning coding agent in a closed documentation loop.

Replaces the deterministic per-cycle transformation of the submitted Box 2.

Finite MDP, one decision per coded diagnosis instance
  state   s = true code k (fixed). Instances: the hospital discharge codes of
          97,737 MIMIC-IV ED-to-admission episodes, restricted to 3-character
          ICD-10-CM categories whose member codes differ in reimbursement tier.
  action  a = recorded code, any member of the same 3-character category as k
  reward  r(k, a) = w_admin * v(a) + w_clin * rho * 1[a == ref(k)],  w_clin = 1 - w_admin
          v(a)  reimbursement tier from CMS MS-DRG v41.1 (none 0, CC 0.5, MCC 1);
                external list, not set by the authors
          rho   probability that clinical correctness is observed (partial,
                delayed observability of R_clin)
          ref   ANCHORED: the true code k (external clinical reference retained)
                REIFIED : the code recorded for the instance in the previous
                          cycle (the coded record serves as the clinical label)
  policy  softmax pi(a | k) per category, initialised as a coder with accuracy acc0
  cycle   the agent is retrained for S policy-gradient steps (exact expected
          gradient, REINFORCE with baseline) on the reward of the current
          cycle; its output becomes the record that the next cycle sees
  metrics JSD (bits) between recorded and true code distribution; share of
          instances recorded at MCC tier vs true MCC share; coding accuracy

Analytic threshold (anchored, eta -> converged): the agent leaves the true
code for a higher-tier code with tier step dv iff w_admin * dv > w_clin * rho,
i.e. w_admin > rho / (dv + rho).

Output: ../results/learning_agent_loop.json
"""
import ast
import json
import os
import math
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path(os.environ.get("MIMIC_ECG_ICD_CSV", "records_w_diag_icd10.csv"))  # PhysioNet credentialed file, not distributed
HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "results" / "learning_agent_loop.json"
TIERS = {"default": {"CC": 0.5, "MCC": 1.0}, "binary": {"CC": 1.0, "MCC": 1.0},
         "cc_low": {"CC": 0.25, "MCC": 1.0}}
BLOCKS = {}


def load_blocks(tier="default"):
    lv = pd.read_csv(HERE / "cms" / "cc_mcc_v41_1.csv")
    level = dict(zip(lv.code, lv.level))
    df = pd.read_csv(SRC, usecols=["ed_stay_id", "ed_hadm_id", "ed_diag_ed", "ed_diag_hosp"])
    df = df.dropna(subset=["ed_stay_id", "ed_hadm_id"]).drop_duplicates("ed_stay_id")
    df = df[(df.ed_diag_ed.str.len() > 2) & (df.ed_diag_hosp.str.len() > 2)]
    counts = Counter(c for cell in df.ed_diag_hosp for c in set(ast.literal_eval(cell)))
    cats = defaultdict(dict)
    for code, n in counts.items():
        cats[code[:3]][code] = n
    blocks = []
    for cat, codes in sorted(cats.items()):
        vals = {c: TIERS[tier].get(level.get(c), 0.0) for c in codes}
        if len(codes) >= 2 and len(set(vals.values())) >= 2:
            names = sorted(codes)
            blocks.append({"cat": cat, "codes": names,
                           "n": np.array([codes[c] for c in names], float),
                           "v": np.array([vals[c] for c in names], float)})
    return blocks, sum(counts.values())


def init_policy(m, acc):
    th = np.full((m, m), math.log((1 - acc) / (m - 1)))
    np.fill_diagonal(th, math.log(acc))
    return th


def softmax(th):
    e = np.exp(th - th.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)


def jsd_bits(p, q):
    m = (p + q) / 2
    def kl(x):
        nz = x > 0
        return (x[nz] * np.log2(x[nz] / m[nz])).sum()
    return 0.5 * (kl(p) + kl(q))


def run(args):
    key, blocks_key, w_admin, rho, mode, cycles, steps, eta, acc0, cat_idx = args
    blocks = BLOCKS[blocks_key]
    if cat_idx is not None:
        blocks = [blocks[i] for i in cat_idx]
    w_clin = 1 - w_admin
    th = [init_policy(len(b["codes"]), acc0) for b in blocks]
    recs = [np.eye(len(b["codes"])) for b in blocks]
    true = np.concatenate([b["n"] for b in blocks]); true /= true.sum()
    v = np.concatenate([b["v"] for b in blocks])
    ntot = sum(b["n"].sum() for b in blocks)
    traj = []
    for _ in range(cycles):
        parts, acc_num = [], 0.0
        for i, b in enumerate(blocks):
            ref = np.eye(len(b["codes"])) if mode == "anchored" else recs[i]
            q = w_admin * b["v"][None, :] + w_clin * rho * ref
            for _ in range(steps):
                pi = softmax(th[i])
                th[i] = th[i] + eta * pi * (q - (pi * q).sum(axis=1, keepdims=True))
            pi = softmax(th[i])
            recs[i] = pi
            parts.append((b["n"][:, None] * pi).sum(0))
            acc_num += (b["n"] * np.diag(pi)).sum()
        coded = np.concatenate(parts); coded /= coded.sum()
        traj.append([round(float(jsd_bits(true, coded)), 5), round(float(coded[v == 1].sum()), 5),
                     round(float(acc_num / ntot), 5)])
    return key, {"true_mcc_share": round(float(true[v == 1].sum()), 5), "traj": traj}


CACHE = HERE / "results" / "blocks_cache.pkl"


def build_cache():
    import pickle
    data = {t: load_blocks(t) for t in TIERS}
    CACHE.write_bytes(pickle.dumps(data))
    return data


def init_worker():
    import pickle
    for t, (b, _) in pickle.loads(CACHE.read_bytes()).items():
        BLOCKS[t] = b


def main():
    data = build_cache()
    init_worker()
    blocks = BLOCKS["default"]
    n_codes_total = data["default"][1]
    n_inst = int(sum(b["n"].sum() for b in blocks))
    meta = {"categories": len(blocks), "instances": n_inst,
            "share_of_hospital_codes": round(n_inst / n_codes_total, 4),
            "codes_in_model": sum(len(b["codes"]) for b in blocks),
            "defaults": {"cycles": 20, "steps": 50, "eta": 1.0, "acc0": 0.95}}
    print(meta, flush=True)
    jobs = []
    W = [round(x, 2) for x in np.arange(0, 1.0001, 0.05)]
    for mode in ("anchored", "reified"):
        for rho in (0.1, 0.25, 0.5, 1.0):
            for w in W:
                jobs.append((f"grid|{mode}|{rho}|{w}", "default", w, rho, mode, 20, 50, 1.0, 0.95, None))
    sens = {"steps10": dict(steps=10), "steps200": dict(steps=200), "acc0.90": dict(acc0=0.90),
            "acc0.99": dict(acc0=0.99), "cycles50": dict(cycles=50),
            "tier_binary": dict(tier="binary"), "tier_cc_low": dict(tier="cc_low")}
    for name, kw in sens.items():
        for mode in ("anchored", "reified"):
            for w in (0.2, 0.5, 0.8):
                jobs.append((f"sens|{name}|{mode}|0.5|{w}", kw.get("tier", "default"), w, 0.5, mode,
                             kw.get("cycles", 20), kw.get("steps", 50), 1.0, kw.get("acc0", 0.95), None))
    rng = np.random.default_rng(20261026)
    for b in range(30):
        idx = sorted(rng.integers(0, len(blocks), len(blocks)).tolist())
        for mode in ("anchored", "reified"):
            for w in (0.2, 0.5, 0.8):
                jobs.append((f"boot|{b}|{mode}|0.5|{w}", "default", w, 0.5, mode, 20, 50, 1.0, 0.95, idx))
    print(len(jobs), "jobs", flush=True)
    res = {}
    with Pool(processes=int(sys.argv[1]) if len(sys.argv) > 1 else 6, initializer=init_worker) as pool:
        for i, (k, r) in enumerate(pool.imap_unordered(run, jobs)):
            res[k] = r
            if i % 25 == 0:
                print(i, k, flush=True)
    OUT.write_text(json.dumps({"meta": meta, "runs": res}))
    print("saved", OUT)


if __name__ == "__main__":
    main()
