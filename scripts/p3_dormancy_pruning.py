"""
P3 - Preserve Don't Prune: Dormancy vs. Pruning Pre-Study
==========================================================
Tests the impact of removing low-frequency conditions (pruning)
vs. preserving them (dormancy) on comorbidity network integrity
and downstream diagnostic accuracy.

Dataset: Synthea synthetic EHR, 11,475 patients, SNOMED-CT coded
Design: Pre-study on synthetic data (Walonoski et al., JAMIA 2018)

Output: Pruning impact metrics, comorbidity network degradation,
        rare condition analysis
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from collections import Counter

DATA_DIR = Path(r"C:\Users\Flori\Documents\neo4j-medical-graph\neo4j-community-5.26.3\import")
OUTPUT_DIR = Path(r"C:\Users\Flori\Documents\neo4j-medical-graph\experiments\results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("P3 PRESERVE DON'T PRUNE: DORMANCY vs. PRUNING PRE-STUDY")
print("=" * 70)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================
# 1. LOAD DATA
# ============================================================
print("[1/7] Loading data...")
patients = pd.read_csv(DATA_DIR / "patients.csv", usecols=["Id", "BIRTHDATE", "GENDER"])
conditions = pd.read_csv(DATA_DIR / "conditions.csv")
medications = pd.read_csv(DATA_DIR / "medications.csv", usecols=["PATIENT", "ENCOUNTER", "CODE", "DESCRIPTION", "REASONCODE", "REASONDESCRIPTION"])

n_patients = len(patients)
print(f"  Patients: {n_patients:,}")
print(f"  Conditions: {len(conditions):,}")
print()

# ============================================================
# 2. CONDITION FREQUENCY DISTRIBUTION
# ============================================================
print("[2/7] Condition frequency distribution...")
print()

condition_counts = conditions.groupby("DESCRIPTION")["PATIENT"].nunique().reset_index()
condition_counts.columns = ["condition", "n_patients"]
condition_counts["prevalence"] = condition_counts["n_patients"] / n_patients
condition_counts = condition_counts.sort_values("prevalence", ascending=False).reset_index(drop=True)

n_unique_conditions = len(condition_counts)

# Frequency tiers
tiers = {
    "ultra_rare": condition_counts[condition_counts["prevalence"] < 0.001],   # < 0.1%
    "rare": condition_counts[(condition_counts["prevalence"] >= 0.001) & (condition_counts["prevalence"] < 0.01)],  # 0.1-1%
    "uncommon": condition_counts[(condition_counts["prevalence"] >= 0.01) & (condition_counts["prevalence"] < 0.05)],  # 1-5%
    "common": condition_counts[(condition_counts["prevalence"] >= 0.05) & (condition_counts["prevalence"] < 0.20)],  # 5-20%
    "very_common": condition_counts[condition_counts["prevalence"] >= 0.20],  # >20%
}

print(f"  Unique conditions: {n_unique_conditions}")
for tier_name, tier_df in tiers.items():
    pct = len(tier_df) / n_unique_conditions * 100
    print(f"  {tier_name:<15}: {len(tier_df):>4} conditions ({pct:.1f}% of vocabulary)")

print()

# ============================================================
# 3. PRUNING SIMULATION
# ============================================================
print("[3/7] Pruning simulation at multiple thresholds...")
print()

PRUNING_THRESHOLDS = [0.001, 0.005, 0.01, 0.02, 0.05]

pruning_results = {}
for threshold in PRUNING_THRESHOLDS:
    pruned = condition_counts[condition_counts["prevalence"] < threshold]
    retained = condition_counts[condition_counts["prevalence"] >= threshold]

    # Patients affected: have at least one pruned condition
    pruned_conditions_set = set(pruned["condition"])
    affected_patients = conditions[conditions["DESCRIPTION"].isin(pruned_conditions_set)]["PATIENT"].unique()

    # Conditions lost per affected patient
    patient_pruned_counts = conditions[
        conditions["DESCRIPTION"].isin(pruned_conditions_set)
    ].groupby("PATIENT")["DESCRIPTION"].nunique()

    pruning_results[f"threshold_{threshold}"] = {
        "threshold_pct": threshold * 100,
        "n_conditions_pruned": len(pruned),
        "n_conditions_retained": len(retained),
        "pct_vocabulary_lost": round(len(pruned) / n_unique_conditions * 100, 1),
        "n_patients_affected": len(affected_patients),
        "pct_patients_affected": round(len(affected_patients) / n_patients * 100, 1),
        "mean_conditions_lost_per_affected": round(patient_pruned_counts.mean(), 2) if len(patient_pruned_counts) > 0 else 0,
        "max_conditions_lost": int(patient_pruned_counts.max()) if len(patient_pruned_counts) > 0 else 0,
    }

    print(f"  Threshold <{threshold*100:.1f}%: "
          f"pruned {len(pruned)} conditions ({len(pruned)/n_unique_conditions*100:.1f}% vocabulary), "
          f"affects {len(affected_patients):,} patients ({len(affected_patients)/n_patients*100:.1f}%)")

print()

# ============================================================
# 4. COMORBIDITY NETWORK IMPACT
# ============================================================
print("[4/7] Comorbidity network degradation analysis...")
print()

# Build comorbidity co-occurrence matrix (patient-level)
# Use top 50 conditions for tractability
top_conditions = condition_counts.head(50)["condition"].tolist()

# Build patient-condition matrix for top 50
patient_conditions = conditions[conditions["DESCRIPTION"].isin(top_conditions)]
patient_cond_matrix = patient_conditions.groupby(["PATIENT", "DESCRIPTION"]).size().unstack(fill_value=0)
patient_cond_matrix = (patient_cond_matrix > 0).astype(int)

# Compute co-occurrence matrix
cooccurrence_full = patient_cond_matrix.T.dot(patient_cond_matrix)
n_edges_full = (cooccurrence_full > 0).sum().sum() // 2  # undirected

# Now simulate pruning rare conditions and measure network loss
network_degradation = {}
for threshold in PRUNING_THRESHOLDS:
    retained_conds = condition_counts[condition_counts["prevalence"] >= threshold]["condition"].tolist()
    retained_top = [c for c in top_conditions if c in retained_conds]

    if len(retained_top) < 2:
        continue

    pruned_matrix = patient_cond_matrix[[c for c in retained_top if c in patient_cond_matrix.columns]]
    cooccurrence_pruned = pruned_matrix.T.dot(pruned_matrix)
    n_edges_pruned = (cooccurrence_pruned > 0).sum().sum() // 2

    edge_loss = 1 - (n_edges_pruned / max(n_edges_full, 1))

    network_degradation[f"threshold_{threshold}"] = {
        "n_nodes_full": len(top_conditions),
        "n_nodes_retained": len(retained_top),
        "n_edges_full": int(n_edges_full),
        "n_edges_retained": int(n_edges_pruned),
        "edge_loss_pct": round(edge_loss * 100, 1),
        "node_loss_pct": round((1 - len(retained_top) / len(top_conditions)) * 100, 1)
    }

    print(f"  Threshold <{threshold*100:.1f}%: "
          f"nodes {len(top_conditions)}->{len(retained_top)}, "
          f"edges {n_edges_full}->{n_edges_pruned} "
          f"({edge_loss*100:.1f}% loss)")

print()

# ============================================================
# 5. CLINICALLY SIGNIFICANT RARE CONDITIONS
# ============================================================
print("[5/7] Clinically significant rare conditions at risk of pruning...")
print()

# Find rare conditions that have associated medications (clinically actionable)
rare_conditions = condition_counts[condition_counts["prevalence"] < 0.01]
rare_cond_set = set(rare_conditions["condition"])

# Check which rare conditions trigger medication prescriptions
rare_with_treatment = []
for _, row in rare_conditions.iterrows():
    cond_name = row["condition"]
    # Check if this condition appears as a reason for medication
    import re
    safe_name = re.escape(cond_name[:30])
    med_match = medications[medications["REASONDESCRIPTION"].str.contains(
        safe_name, case=False, na=False
    )] if len(cond_name) > 5 else pd.DataFrame()

    if len(med_match) > 0:
        rare_with_treatment.append({
            "condition": cond_name,
            "prevalence": round(row["prevalence"], 5),
            "n_patients": int(row["n_patients"]),
            "n_prescriptions": len(med_match),
            "medications": list(med_match["DESCRIPTION"].unique()[:3])
        })

print(f"  Rare conditions (<1% prevalence): {len(rare_conditions)}")
print(f"  Rare conditions with active treatment: {len(rare_with_treatment)}")
print()

# Show top 10 most clinically significant rare conditions
rare_with_treatment.sort(key=lambda x: x["n_prescriptions"], reverse=True)
print("  Top 10 clinically actionable rare conditions at pruning risk:")
for i, item in enumerate(rare_with_treatment[:10]):
    print(f"    {i+1}. {item['condition'][:50]:<50} "
          f"prev={item['prevalence']:.4f} "
          f"scripts={item['n_prescriptions']:>5}")

print()

# ============================================================
# 6. CATASTROPHIC COLLAPSE METRIC
# ============================================================
print("[6/7] Catastrophic collapse analysis...")
print()

# Define: a patient experiences "catastrophic information loss" when
# pruning removes ALL their rare conditions, leaving only common ones
# This simulates the collapse pattern from EMoT ablation (4.2 -> 1.0)

collapse_results = {}
for threshold in PRUNING_THRESHOLDS:
    pruned_conds = set(condition_counts[condition_counts["prevalence"] < threshold]["condition"])

    if not pruned_conds:
        continue

    # For each patient with rare conditions, measure what fraction is lost
    patient_total = conditions.groupby("PATIENT")["DESCRIPTION"].nunique()
    patient_rare = conditions[conditions["DESCRIPTION"].isin(pruned_conds)].groupby("PATIENT")["DESCRIPTION"].nunique()

    # Patients who have rare conditions
    patients_with_rare = set(patient_rare.index)
    if not patients_with_rare:
        continue

    # Information loss ratio per patient
    loss_ratios = []
    for pat_id in patients_with_rare:
        total = patient_total.get(pat_id, 0)
        rare = patient_rare.get(pat_id, 0)
        if total > 0:
            loss_ratios.append(rare / total)

    loss_ratios = np.array(loss_ratios)

    # Catastrophic = patients losing >50% of their condition profile
    n_catastrophic = (loss_ratios > 0.5).sum()
    # Severe = losing >30%
    n_severe = (loss_ratios > 0.3).sum()

    collapse_results[f"threshold_{threshold}"] = {
        "n_patients_with_rare": len(patients_with_rare),
        "mean_info_loss": round(loss_ratios.mean(), 4),
        "median_info_loss": round(np.median(loss_ratios), 4),
        "max_info_loss": round(loss_ratios.max(), 4),
        "n_catastrophic_gt50pct": int(n_catastrophic),
        "n_severe_gt30pct": int(n_severe),
        "pct_catastrophic": round(n_catastrophic / len(patients_with_rare) * 100, 1)
    }

    print(f"  Threshold <{threshold*100:.1f}%: "
          f"mean loss={loss_ratios.mean():.1%}, "
          f"catastrophic(>50% loss)={n_catastrophic} patients ({n_catastrophic/len(patients_with_rare)*100:.1f}%), "
          f"severe(>30%)={n_severe}")

print()

# ============================================================
# 7. DORMANCY BENEFIT QUANTIFICATION
# ============================================================
print("[7/7] Dormancy benefit quantification...")
print()

# Key metric: what is preserved by dormancy that pruning destroys?
# For the 1% threshold (the most relevant clinical scenario):

threshold_key = 0.01
pruned_at_1pct = set(condition_counts[condition_counts["prevalence"] < threshold_key]["condition"])
retained_at_1pct = set(condition_counts[condition_counts["prevalence"] >= threshold_key]["condition"])

# Unique diagnostic pathways preserved by dormancy
# = rare conditions that co-occur with common conditions
# (these create diagnostic CONTEXT that pruning removes)

rare_common_bridges = []
for rare_cond in list(pruned_at_1pct)[:200]:  # sample for speed
    patients_with_rare = set(conditions[conditions["DESCRIPTION"] == rare_cond]["PATIENT"].unique())
    if len(patients_with_rare) < 5:
        continue

    # What common conditions do these patients also have?
    common_comorbidities = conditions[
        (conditions["PATIENT"].isin(patients_with_rare)) &
        (conditions["DESCRIPTION"].isin(retained_at_1pct))
    ]["DESCRIPTION"].value_counts().head(3)

    if len(common_comorbidities) > 0:
        rare_common_bridges.append({
            "rare_condition": rare_cond,
            "n_patients": len(patients_with_rare),
            "common_comorbidities": dict(common_comorbidities)
        })

dormancy_benefit = {
    "threshold": threshold_key,
    "n_conditions_preserved_by_dormancy": len(pruned_at_1pct),
    "n_diagnostic_bridges": len(rare_common_bridges),
    "pct_rare_with_common_bridge": round(len(rare_common_bridges) / max(len(pruned_at_1pct), 1) * 100, 1),
    "examples": rare_common_bridges[:5]
}

print(f"  At 1% threshold:")
print(f"    Conditions preserved by dormancy: {len(pruned_at_1pct)}")
print(f"    Diagnostic bridges (rare<->common): {len(rare_common_bridges)}")
print(f"    % of rare conditions with diagnostic context: {dormancy_benefit['pct_rare_with_common_bridge']}%")
print()
if rare_common_bridges:
    print("  Example diagnostic bridges preserved by dormancy:")
    for bridge in rare_common_bridges[:5]:
        comorbids = list(bridge["common_comorbidities"].keys())[:2]
        print(f"    {bridge['rare_condition'][:45]:<45} -> {', '.join(c[:30] for c in comorbids)}")

print()

# ============================================================
# SAVE RESULTS
# ============================================================
print("=" * 70)
print("SAVING RESULTS")
print("=" * 70)

full_results = {
    "metadata": {
        "study": "P3 Preserve Don't Prune: Dormancy vs. Pruning Pre-Study",
        "dataset": "Synthea v3.x synthetic EHR",
        "n_patients": n_patients,
        "n_unique_conditions": n_unique_conditions,
        "timestamp": datetime.now().isoformat(),
        "citation": "Walonoski J et al. Synthea: An approach, method, and software mechanism for generating synthetic patients and the synthetic electronic health care record. JAMIA 2018;25(3):230-238."
    },
    "frequency_distribution": {
        tier_name: {
            "n_conditions": len(tier_df),
            "pct_of_vocabulary": round(len(tier_df) / n_unique_conditions * 100, 1)
        } for tier_name, tier_df in tiers.items()
    },
    "pruning_simulation": pruning_results,
    "network_degradation": network_degradation,
    "clinically_significant_rare": rare_with_treatment[:20],
    "catastrophic_collapse": collapse_results,
    "dormancy_benefit": dormancy_benefit
}

output_file = OUTPUT_DIR / "p3_dormancy_pruning_results.json"
with open(output_file, "w") as f:
    json.dump(full_results, f, indent=2, default=str)

print(f"Results saved to: {output_file}")
print()

# ============================================================
# SUMMARY TABLE
# ============================================================
print("=" * 70)
print("TABLE 2: Pruning Impact at Multiple Thresholds")
print("=" * 70)
print(f"{'Threshold':<12} {'Vocab Lost':>12} {'Patients Hit':>14} {'Edge Loss':>12} {'Catastrophic':>14}")
print("-" * 64)
for threshold in PRUNING_THRESHOLDS:
    key = f"threshold_{threshold}"
    pr = pruning_results.get(key, {})
    nd = network_degradation.get(key, {})
    cc = collapse_results.get(key, {})
    print(f"<{threshold*100:>5.1f}%     "
          f"{pr.get('pct_vocabulary_lost', 0):>10.1f}%  "
          f"{pr.get('pct_patients_affected', 0):>12.1f}%  "
          f"{nd.get('edge_loss_pct', 0):>10.1f}%  "
          f"{cc.get('n_catastrophic_gt50pct', 0):>14,}")

print()
print("DONE.")
