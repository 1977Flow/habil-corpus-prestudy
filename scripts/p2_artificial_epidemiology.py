"""
P2 - Artificial Epidemiology: D(C) Divergence Pre-Study
========================================================
Measures the gap between administrative prevalence P_admin(C)
(coded conditions) and clinical prevalence P_clinical(C)
(derived from observations/labs) for sentinel conditions.

Dataset: Synthea synthetic EHR, 11,475 patients, SNOMED-CT coded
Design: Pre-study on synthetic data (Walonoski et al., JAMIA 2018)

Output: D(C) values, temporal drift plots, upcoding simulation
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(r"C:\Users\Flori\Documents\neo4j-medical-graph\neo4j-community-5.26.3\import")
OUTPUT_DIR = Path(r"C:\Users\Flori\Documents\neo4j-medical-graph\experiments\results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# SENTINEL CONDITIONS with clinical thresholds
# ============================================================
SENTINEL_CONDITIONS = {
    "Diabetes": {
        "snomed_patterns": ["Diabetes", "diabetes mellitus"],
        "lab_code": "4548-4",  # HbA1c
        "lab_description": "Hemoglobin A1c",
        "threshold": 6.5,
        "operator": ">=",
        "units": "%"
    },
    "Hypertension": {
        "snomed_patterns": ["Hypertension", "hypertensive"],
        "lab_code": "8480-6",  # Systolic BP
        "lab_description": "Systolic Blood Pressure",
        "threshold": 140,
        "operator": ">=",
        "units": "mm[Hg]"
    },
    "Obesity": {
        "snomed_patterns": ["Obesity", "Body mass index 30+"],
        "lab_code": "39156-5",  # BMI
        "lab_description": "Body Mass Index",
        "threshold": 30,
        "operator": ">=",
        "units": "kg/m2"
    },
    "Hyperlipidemia": {
        "snomed_patterns": ["Hyperlipidemia", "Hypercholesterolemia"],
        "lab_code": "2093-3",  # Total Cholesterol
        "lab_description": "Total Cholesterol",
        "threshold": 240,
        "operator": ">=",
        "units": "mg/dL"
    },
    "Prediabetes": {
        "snomed_patterns": ["Prediabetes"],
        "lab_code": "4548-4",  # HbA1c
        "lab_description": "Hemoglobin A1c",
        "threshold": 5.7,
        "operator": ">=",
        "threshold_upper": 6.5,
        "operator_upper": "<",
        "units": "%"
    }
}

print("=" * 70)
print("P2 ARTIFICIAL EPIDEMIOLOGY: D(C) DIVERGENCE PRE-STUDY")
print("=" * 70)
print(f"Timestamp: {datetime.now().isoformat()}")
print(f"Data source: Synthea v3.x, {DATA_DIR}")
print()

# ============================================================
# 1. LOAD DATA
# ============================================================
print("[1/6] Loading data...")
patients = pd.read_csv(DATA_DIR / "patients.csv", usecols=["Id", "BIRTHDATE", "DEATHDATE", "GENDER", "RACE"])
conditions = pd.read_csv(DATA_DIR / "conditions.csv", usecols=["START", "STOP", "PATIENT", "ENCOUNTER", "SYSTEM", "CODE", "DESCRIPTION"])
observations = pd.read_csv(DATA_DIR / "observations.csv", usecols=["DATE", "PATIENT", "ENCOUNTER", "CATEGORY", "CODE", "DESCRIPTION", "VALUE", "UNITS", "TYPE"])
encounters = pd.read_csv(DATA_DIR / "encounters.csv", usecols=["Id", "START", "PATIENT", "ENCOUNTERCLASS", "CODE", "DESCRIPTION", "TOTAL_CLAIM_COST", "PAYER_COVERAGE"])

n_patients = len(patients)
print(f"  Patients: {n_patients:,}")
print(f"  Conditions: {len(conditions):,}")
print(f"  Observations: {len(observations):,}")
print(f"  Encounters: {len(encounters):,}")
print()

# ============================================================
# 2. COMPUTE D(C) FOR EACH SENTINEL CONDITION
# ============================================================
print("[2/6] Computing D(C) divergence for sentinel conditions...")
print()

results = {}

for cond_name, config in SENTINEL_CONDITIONS.items():
    print(f"  --- {cond_name} ---")

    # P_admin: patients with coded condition
    mask_admin = conditions["DESCRIPTION"].str.contains(
        "|".join(config["snomed_patterns"]), case=False, na=False
    )
    patients_admin = conditions[mask_admin]["PATIENT"].unique()
    p_admin = len(patients_admin) / n_patients

    # P_clinical: patients with lab values exceeding threshold
    obs_filtered = observations[observations["CODE"] == config["lab_code"]]
    obs_filtered = obs_filtered[obs_filtered["TYPE"] == "numeric"]
    obs_filtered = obs_filtered.copy()
    obs_filtered["VALUE_NUM"] = pd.to_numeric(obs_filtered["VALUE"], errors="coerce")
    obs_filtered = obs_filtered.dropna(subset=["VALUE_NUM"])

    if "threshold_upper" in config:
        # Range condition (e.g., Prediabetes: 5.7 <= HbA1c < 6.5)
        patients_clinical_mask = (
            (obs_filtered["VALUE_NUM"] >= config["threshold"]) &
            (obs_filtered["VALUE_NUM"] < config["threshold_upper"])
        )
    else:
        patients_clinical_mask = obs_filtered["VALUE_NUM"] >= config["threshold"]

    patients_clinical = obs_filtered[patients_clinical_mask]["PATIENT"].unique()
    p_clinical = len(patients_clinical) / n_patients

    # D(C) = P_admin - P_clinical
    d_c = p_admin - p_clinical

    # Overlap analysis
    admin_set = set(patients_admin)
    clinical_set = set(patients_clinical)
    coded_only = admin_set - clinical_set  # coded but no lab evidence
    uncoded = clinical_set - admin_set     # lab evidence but no code
    overlap = admin_set & clinical_set

    results[cond_name] = {
        "n_admin": len(patients_admin),
        "n_clinical": len(patients_clinical),
        "p_admin": round(p_admin, 4),
        "p_clinical": round(p_clinical, 4),
        "D_C": round(d_c, 4),
        "D_C_abs": round(abs(d_c), 4),
        "n_coded_only": len(coded_only),
        "n_uncoded": len(uncoded),
        "n_overlap": len(overlap),
        "lab_code": config["lab_code"],
        "threshold": config["threshold"],
        "n_lab_measurements": len(obs_filtered)
    }

    print(f"    P_admin  = {p_admin:.4f} ({len(patients_admin):,} patients)")
    print(f"    P_clinical = {p_clinical:.4f} ({len(patients_clinical):,} patients)")
    print(f"    D(C) = {d_c:+.4f}")
    print(f"    Coded-only (no lab evidence): {len(coded_only):,}")
    print(f"    Uncoded (lab evidence, no code): {len(uncoded):,}")
    print(f"    Overlap: {len(overlap):,}")
    print()

# ============================================================
# 3. UPCODING SIMULATION
# ============================================================
print("[3/6] Upcoding simulation (10%, 20%, 30% shift)...")
print()

upcoding_results = {}
for cond_name, res in results.items():
    upcoding_results[cond_name] = {"baseline_D_C": res["D_C"]}
    for shift_pct in [0.10, 0.20, 0.30]:
        # Simulate: shift X% of uncoded patients to coded
        n_shifted = int(res["n_uncoded"] * shift_pct)
        new_n_admin = res["n_admin"] + n_shifted
        new_p_admin = new_n_admin / n_patients
        new_d_c = new_p_admin - res["p_clinical"]
        upcoding_results[cond_name][f"shift_{int(shift_pct*100)}pct"] = {
            "n_shifted": n_shifted,
            "new_p_admin": round(new_p_admin, 4),
            "new_D_C": round(new_d_c, 4),
            "D_C_amplification": round(abs(new_d_c) / max(abs(res["D_C"]), 0.0001), 2)
        }
    print(f"  {cond_name}: D(C) baseline={res['D_C']:+.4f} | "
          f"+10%={upcoding_results[cond_name]['shift_10pct']['new_D_C']:+.4f} | "
          f"+20%={upcoding_results[cond_name]['shift_20pct']['new_D_C']:+.4f} | "
          f"+30%={upcoding_results[cond_name]['shift_30pct']['new_D_C']:+.4f}")

print()

# ============================================================
# 4. TEMPORAL DRIFT ANALYSIS
# ============================================================
print("[4/6] Temporal drift analysis (yearly D(C) trajectory)...")
print()

conditions["START_YEAR"] = pd.to_datetime(conditions["START"], errors="coerce").dt.year
observations["OBS_YEAR"] = pd.to_datetime(observations["DATE"], errors="coerce").dt.year

temporal_drift = {}
for cond_name, config in SENTINEL_CONDITIONS.items():
    yearly_dc = {}

    mask_admin = conditions["DESCRIPTION"].str.contains(
        "|".join(config["snomed_patterns"]), case=False, na=False
    )
    cond_subset = conditions[mask_admin]

    obs_subset = observations[observations["CODE"] == config["lab_code"]]
    obs_subset = obs_subset[obs_subset["TYPE"] == "numeric"].copy()
    obs_subset["VALUE_NUM"] = pd.to_numeric(obs_subset["VALUE"], errors="coerce")
    obs_subset = obs_subset.dropna(subset=["VALUE_NUM"])

    years = sorted(set(cond_subset["START_YEAR"].dropna().unique().astype(int)) &
                   set(obs_subset["OBS_YEAR"].dropna().unique().astype(int)))

    # Use cumulative counts up to each year
    for year in years:
        if year < 2000:
            continue
        patients_admin_y = cond_subset[cond_subset["START_YEAR"] <= year]["PATIENT"].unique()

        if "threshold_upper" in config:
            obs_mask = (obs_subset["VALUE_NUM"] >= config["threshold"]) & (obs_subset["VALUE_NUM"] < config["threshold_upper"])
        else:
            obs_mask = obs_subset["VALUE_NUM"] >= config["threshold"]

        patients_clinical_y = obs_subset[obs_mask & (obs_subset["OBS_YEAR"] <= year)]["PATIENT"].unique()

        p_admin_y = len(patients_admin_y) / n_patients
        p_clinical_y = len(patients_clinical_y) / n_patients
        d_c_y = p_admin_y - p_clinical_y

        yearly_dc[int(year)] = {
            "p_admin": round(p_admin_y, 4),
            "p_clinical": round(p_clinical_y, 4),
            "D_C": round(d_c_y, 4)
        }

    temporal_drift[cond_name] = yearly_dc
    if yearly_dc:
        first_year = min(yearly_dc.keys())
        last_year = max(yearly_dc.keys())
        print(f"  {cond_name}: D(C) {first_year}={yearly_dc[first_year]['D_C']:+.4f} -> "
              f"{last_year}={yearly_dc[last_year]['D_C']:+.4f}")

print()

# ============================================================
# 5. COMORBIDITY INFLATION CHECK (P2 Marker #2)
# ============================================================
print("[5/6] Comorbidity inflation analysis...")
print()

patient_condition_counts = conditions.groupby("PATIENT")["DESCRIPTION"].nunique()
comorbidity_stats = {
    "mean_conditions_per_patient": round(patient_condition_counts.mean(), 2),
    "median_conditions_per_patient": round(patient_condition_counts.median(), 2),
    "pct_5plus_conditions": round((patient_condition_counts >= 5).mean() * 100, 1),
    "pct_10plus_conditions": round((patient_condition_counts >= 10).mean() * 100, 1),
    "max_conditions": int(patient_condition_counts.max()),
}

# Check for co-occurrence patterns in sentinel conditions
sentinel_patients = {}
for cond_name, config in SENTINEL_CONDITIONS.items():
    mask = conditions["DESCRIPTION"].str.contains(
        "|".join(config["snomed_patterns"]), case=False, na=False
    )
    sentinel_patients[cond_name] = set(conditions[mask]["PATIENT"].unique())

co_occurrence = {}
sentinel_names = list(SENTINEL_CONDITIONS.keys())
for i, name_a in enumerate(sentinel_names):
    for name_b in sentinel_names[i+1:]:
        overlap = len(sentinel_patients[name_a] & sentinel_patients[name_b])
        expected = (len(sentinel_patients[name_a]) / n_patients) * (len(sentinel_patients[name_b]) / n_patients) * n_patients
        ratio = overlap / max(expected, 1)
        co_occurrence[f"{name_a}+{name_b}"] = {
            "observed": overlap,
            "expected": round(expected, 1),
            "ratio": round(ratio, 2)
        }
        if ratio > 1.5:
            print(f"  INFLATION SIGNAL: {name_a}+{name_b}: observed={overlap}, expected={expected:.0f}, ratio={ratio:.2f}")

print(f"  Mean conditions per patient: {comorbidity_stats['mean_conditions_per_patient']}")
print(f"  Patients with 5+ conditions: {comorbidity_stats['pct_5plus_conditions']}%")
print(f"  Patients with 10+ conditions: {comorbidity_stats['pct_10plus_conditions']}%")
print()

# ============================================================
# 6. DOCUMENTATION-ACTION GAP (P2 Marker #3)
# ============================================================
print("[6/6] Documentation-action gap analysis...")
print()

# For each sentinel condition: is there a corresponding treatment?
medications = pd.read_csv(DATA_DIR / "medications.csv", usecols=["PATIENT", "DESCRIPTION", "REASONCODE", "REASONDESCRIPTION"])

doc_action_gap = {}
treatment_patterns = {
    "Diabetes": ["Metformin", "Insulin", "Glipizide", "Sitagliptin"],
    "Hypertension": ["Lisinopril", "Amlodipine", "Hydrochlorothiazide", "Losartan", "Valsartan"],
    "Obesity": ["Orlistat", "Liraglutide", "bariatric"],
    "Hyperlipidemia": ["Simvastatin", "Atorvastatin", "Rosuvastatin", "Pravastatin"],
}

for cond_name, treatments in treatment_patterns.items():
    if cond_name not in sentinel_patients:
        continue
    coded_patients = sentinel_patients[cond_name]

    treatment_mask = medications["DESCRIPTION"].str.contains(
        "|".join(treatments), case=False, na=False
    )
    treated_patients = set(medications[treatment_mask]["PATIENT"].unique())

    coded_and_treated = coded_patients & treated_patients
    coded_not_treated = coded_patients - treated_patients

    gap_rate = len(coded_not_treated) / max(len(coded_patients), 1)
    doc_action_gap[cond_name] = {
        "n_coded": len(coded_patients),
        "n_treated": len(coded_and_treated),
        "n_gap": len(coded_not_treated),
        "gap_rate": round(gap_rate, 4)
    }
    print(f"  {cond_name}: coded={len(coded_patients):,}, treated={len(coded_and_treated):,}, "
          f"gap={len(coded_not_treated):,} ({gap_rate:.1%})")

print()

# ============================================================
# SAVE RESULTS
# ============================================================
print("=" * 70)
print("SAVING RESULTS")
print("=" * 70)

full_results = {
    "metadata": {
        "study": "P2 Artificial Epidemiology D(C) Divergence Pre-Study",
        "dataset": "Synthea v3.x synthetic EHR",
        "n_patients": n_patients,
        "n_conditions": len(conditions),
        "n_observations": len(observations),
        "timestamp": datetime.now().isoformat(),
        "citation": "Walonoski J et al. Synthea: An approach, method, and software mechanism for generating synthetic patients and the synthetic electronic health care record. JAMIA 2018;25(3):230-238."
    },
    "dc_divergence": results,
    "upcoding_simulation": upcoding_results,
    "temporal_drift": temporal_drift,
    "comorbidity_analysis": {
        "stats": comorbidity_stats,
        "co_occurrence": co_occurrence
    },
    "documentation_action_gap": doc_action_gap
}

output_file = OUTPUT_DIR / "p2_dc_divergence_results.json"
with open(output_file, "w") as f:
    json.dump(full_results, f, indent=2, default=str)

print(f"Results saved to: {output_file}")
print()

# ============================================================
# SUMMARY TABLE (for paper insertion)
# ============================================================
print("=" * 70)
print("TABLE 1: D(C) Divergence for Sentinel Conditions")
print("=" * 70)
print(f"{'Condition':<20} {'P_admin':>10} {'P_clinical':>12} {'D(C)':>8} {'Coded-only':>12} {'Uncoded':>10}")
print("-" * 72)
for cond_name, res in results.items():
    print(f"{cond_name:<20} {res['p_admin']:>10.4f} {res['p_clinical']:>12.4f} {res['D_C']:>+8.4f} "
          f"{res['n_coded_only']:>12,} {res['n_uncoded']:>10,}")
print()
print("D(C) > 0: Administrative over-representation (potential upcoding)")
print("D(C) < 0: Administrative under-representation (potential undercoding)")
print()
print("DONE.")
