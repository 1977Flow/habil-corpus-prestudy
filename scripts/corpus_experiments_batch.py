"""
Habilitation Corpus: Empirical Pre-Studies (Batch)
===================================================
P1:  SNOMED->ICD Information Loss Rate
P11: Drift Sentinel Pattern Validation
P12: Cost of Drift
S1:  Terminology Coverage Gap
S2:  Semantic Entropy Metric
S3:  Cross-Organization Coding Variance
PRAXIS-AI: Framework Domain Operationalization

Dataset: Synthea v3.x, 11,475 patients, SNOMED-CT coded
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from collections import Counter
import re

DATA_DIR = Path(r"C:\Users\Flori\Documents\neo4j-medical-graph\neo4j-community-5.26.3\import")
OUTPUT_DIR = Path(r"C:\Users\Flori\Documents\neo4j-medical-graph\experiments\results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("HABILITATION CORPUS: BATCH EMPIRICAL PRE-STUDIES")
print("=" * 70)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# ============================================================
# LOAD ALL DATA ONCE
# ============================================================
print("[LOAD] Loading datasets...")
patients = pd.read_csv(DATA_DIR / "patients.csv")
conditions = pd.read_csv(DATA_DIR / "conditions.csv")
encounters = pd.read_csv(DATA_DIR / "encounters.csv")
medications = pd.read_csv(DATA_DIR / "medications.csv")
observations = pd.read_csv(DATA_DIR / "observations.csv",
    usecols=["DATE", "PATIENT", "ENCOUNTER", "CATEGORY", "CODE", "DESCRIPTION", "VALUE", "UNITS", "TYPE"])
procedures = pd.read_csv(DATA_DIR / "procedures.csv",
    usecols=["START", "PATIENT", "ENCOUNTER", "CODE", "DESCRIPTION", "BASE_COST", "REASONCODE", "REASONDESCRIPTION"])
organizations = pd.read_csv(DATA_DIR / "organizations.csv")

n_patients = len(patients)
print(f"  Loaded: {n_patients:,} patients, {len(conditions):,} conditions, "
      f"{len(encounters):,} encounters, {len(observations):,} observations")
print()

all_results = {}

# ============================================================
# P1: SNOMED -> ICD INFORMATION LOSS RATE
# ============================================================
print("=" * 70)
print("P1: SNOMED -> ICD INFORMATION LOSS ANALYSIS")
print("=" * 70)
print()

# Core argument of P1: clinical nuance is lost when SNOMED concepts
# are mapped to ICD billing codes. We measure this by analyzing
# the granularity compression in the Synthea dataset.

# SNOMED codes are 6-9 digit numeric codes with hierarchical structure
# ICD-10 codes are alphanumeric with 3-7 character structure

# Analysis 1: SNOMED granularity -- how many distinct SNOMED codes
# map to similar clinical descriptions?
condition_codes = conditions[["CODE", "DESCRIPTION", "SYSTEM"]].drop_duplicates()
snomed_conditions = condition_codes[condition_codes["SYSTEM"] == "SNOMED-CT"]

# Group by first word of description (rough clinical domain)
snomed_conditions = snomed_conditions.copy()
snomed_conditions["domain"] = snomed_conditions["DESCRIPTION"].str.split().str[0]

# Analysis 2: Description clustering -- conditions that differ only
# in specificity (e.g., "Diabetes" vs "Diabetes mellitus type 2")
description_groups = {}
for _, row in snomed_conditions.iterrows():
    base = row["DESCRIPTION"].split("(")[0].strip().lower()[:30]
    if base not in description_groups:
        description_groups[base] = []
    description_groups[base].append({
        "code": str(row["CODE"]),
        "full_description": row["DESCRIPTION"]
    })

# Find groups with multiple SNOMED codes -> information compression risk
multi_code_groups = {k: v for k, v in description_groups.items() if len(v) > 1}

# Analysis 3: Encounter-level information density
# How many distinct condition codes per encounter?
encounter_conditions = conditions.groupby("ENCOUNTER").agg(
    n_conditions=("CODE", "nunique"),
    n_descriptions=("DESCRIPTION", "nunique")
).reset_index()

# Information loss proxy: encounters where n_conditions > n_descriptions
# (multiple SNOMED codes collapse to same description)
info_loss_encounters = encounter_conditions[
    encounter_conditions["n_conditions"] > encounter_conditions["n_descriptions"]
]

# Analysis 4: Temporal specificity loss
# Conditions with START but no STOP (ongoing) vs. resolved
conditions_temporal = conditions.copy()
conditions_temporal["has_stop"] = conditions_temporal["STOP"].notna()
temporal_stats = conditions_temporal.groupby("has_stop").size()

p1_results = {
    "n_unique_snomed_codes": int(snomed_conditions["CODE"].nunique()),
    "n_unique_descriptions": int(snomed_conditions["DESCRIPTION"].nunique()),
    "code_to_description_ratio": round(
        snomed_conditions["CODE"].nunique() / max(snomed_conditions["DESCRIPTION"].nunique(), 1), 2),
    "n_multi_code_groups": len(multi_code_groups),
    "examples_multi_code": {k: v for k, v in list(multi_code_groups.items())[:5]},
    "encounter_info_loss": {
        "total_encounters_with_conditions": len(encounter_conditions),
        "encounters_with_code_compression": len(info_loss_encounters),
        "compression_rate": round(len(info_loss_encounters) / max(len(encounter_conditions), 1), 4)
    },
    "temporal_resolution": {
        "conditions_with_stop_date": int(temporal_stats.get(True, 0)),
        "conditions_without_stop": int(temporal_stats.get(False, 0)),
        "pct_unresolved": round(temporal_stats.get(False, 0) / len(conditions) * 100, 1)
    },
    "clinical_domains": dict(snomed_conditions["domain"].value_counts().head(15))
}

print(f"  Unique SNOMED codes: {p1_results['n_unique_snomed_codes']}")
print(f"  Unique descriptions: {p1_results['n_unique_descriptions']}")
print(f"  Code:Description ratio: {p1_results['code_to_description_ratio']}:1")
print(f"  Multi-code groups (compression risk): {p1_results['n_multi_code_groups']}")
print(f"  Encounters with code compression: {p1_results['encounter_info_loss']['encounters_with_code_compression']:,} "
      f"({p1_results['encounter_info_loss']['compression_rate']:.2%})")
print(f"  Conditions without resolution date: {p1_results['temporal_resolution']['pct_unresolved']:.1f}%")
print()

all_results["P1_information_loss"] = p1_results

# ============================================================
# P11: DRIFT SENTINEL PATTERN VALIDATION
# ============================================================
print("=" * 70)
print("P11: DRIFT SENTINEL PATTERN VALIDATION")
print("=" * 70)
print()

# Implements a simplified Drift Sentinel (Pattern #3 from P11)
# Measures semantic fingerprint changes over time

conditions["START_DT"] = pd.to_datetime(conditions["START"], errors="coerce")
conditions["YEAR"] = conditions["START_DT"].dt.year

# Semantic fingerprint: distribution of condition codes per year
yearly_fingerprints = {}
years = sorted(conditions["YEAR"].dropna().unique().astype(int))
years = [y for y in years if 2005 <= y <= 2026]

for year in years:
    year_conditions = conditions[conditions["YEAR"] == year]
    code_dist = year_conditions["CODE"].value_counts(normalize=True)
    yearly_fingerprints[year] = code_dist

# Measure drift: Jensen-Shannon divergence between consecutive years
def js_divergence(p, q):
    """Jensen-Shannon divergence between two distributions."""
    all_keys = set(p.index) | set(q.index)
    p_aligned = pd.Series({k: p.get(k, 0) for k in all_keys})
    q_aligned = pd.Series({k: q.get(k, 0) for k in all_keys})
    p_aligned = p_aligned / p_aligned.sum()
    q_aligned = q_aligned / q_aligned.sum()
    m = (p_aligned + q_aligned) / 2
    # Avoid log(0)
    p_safe = p_aligned.replace(0, 1e-10)
    q_safe = q_aligned.replace(0, 1e-10)
    m_safe = m.replace(0, 1e-10)
    kl_pm = (p_aligned * np.log(p_safe / m_safe)).sum()
    kl_qm = (q_aligned * np.log(q_safe / m_safe)).sum()
    return float((kl_pm + kl_qm) / 2)

drift_trajectory = {}
for i in range(1, len(years)):
    y_prev, y_curr = years[i-1], years[i]
    if y_prev in yearly_fingerprints and y_curr in yearly_fingerprints:
        jsd = js_divergence(yearly_fingerprints[y_prev], yearly_fingerprints[y_curr])
        drift_trajectory[f"{y_prev}->{y_curr}"] = round(jsd, 6)

# Cumulative drift from baseline (first year)
baseline_year = years[0]
cumulative_drift = {}
for year in years[1:]:
    if baseline_year in yearly_fingerprints and year in yearly_fingerprints:
        jsd = js_divergence(yearly_fingerprints[baseline_year], yearly_fingerprints[year])
        cumulative_drift[str(year)] = round(jsd, 6)

# New condition emergence rate
new_conditions_per_year = {}
seen_codes = set()
for year in years:
    year_codes = set(conditions[conditions["YEAR"] == year]["CODE"].unique())
    new_codes = year_codes - seen_codes
    new_conditions_per_year[str(year)] = len(new_codes)
    seen_codes |= year_codes

# Drift alert threshold: flag years with JSD > 2x median
jsd_values = list(drift_trajectory.values())
median_jsd = np.median(jsd_values) if jsd_values else 0
alerts = {k: v for k, v in drift_trajectory.items() if v > 2 * median_jsd}

p11_results = {
    "yearly_drift_jsd": drift_trajectory,
    "cumulative_drift_from_baseline": cumulative_drift,
    "new_conditions_per_year": new_conditions_per_year,
    "drift_statistics": {
        "mean_yearly_jsd": round(np.mean(jsd_values), 6) if jsd_values else 0,
        "median_yearly_jsd": round(median_jsd, 6),
        "max_yearly_jsd": round(max(jsd_values), 6) if jsd_values else 0,
        "n_drift_alerts": len(alerts),
        "alert_threshold": round(2 * median_jsd, 6)
    },
    "drift_alerts": alerts,
    "vocabulary_growth": {
        "initial_vocabulary": int(new_conditions_per_year.get(str(years[0]), 0)),
        "final_vocabulary": len(seen_codes),
        "total_new_conditions_added": sum(new_conditions_per_year.values())
    }
}

print(f"  Yearly drift (JSD):")
for period, jsd in list(drift_trajectory.items())[-5:]:
    flag = " << ALERT" if period in alerts else ""
    print(f"    {period}: {jsd:.6f}{flag}")
print(f"  Mean yearly JSD: {p11_results['drift_statistics']['mean_yearly_jsd']:.6f}")
print(f"  Drift alerts (>2x median): {len(alerts)}")
print(f"  Cumulative drift {years[0]}->{years[-1]}: {list(cumulative_drift.values())[-1]:.6f}")
print(f"  New conditions added over period: {sum(new_conditions_per_year.values())}")
print()

all_results["P11_drift_sentinel"] = p11_results

# ============================================================
# P12: COST OF DRIFT
# ============================================================
print("=" * 70)
print("P12: COST OF ONTOLOGICAL DRIFT")
print("=" * 70)
print()

# Link coding patterns to costs
encounters_with_cost = encounters[["Id", "PATIENT", "TOTAL_CLAIM_COST", "PAYER_COVERAGE", "ENCOUNTERCLASS"]].copy()
encounters_with_cost["TOTAL_CLAIM_COST"] = pd.to_numeric(encounters_with_cost["TOTAL_CLAIM_COST"], errors="coerce")
encounters_with_cost["PAYER_COVERAGE"] = pd.to_numeric(encounters_with_cost["PAYER_COVERAGE"], errors="coerce")

# Join conditions to encounter costs
cond_costs = conditions.merge(
    encounters_with_cost, left_on="ENCOUNTER", right_on="Id", how="left", suffixes=("", "_enc")
)

# Cost per condition category
condition_prevalence = conditions.groupby("DESCRIPTION")["PATIENT"].nunique()
condition_prevalence_pct = condition_prevalence / n_patients

# Split into "stable" (common, well-coded) and "drifting" (rare, potentially miscoded)
stable_conditions = condition_prevalence_pct[condition_prevalence_pct >= 0.05].index
drifting_conditions = condition_prevalence_pct[condition_prevalence_pct < 0.01].index

stable_costs = cond_costs[cond_costs["DESCRIPTION"].isin(stable_conditions)]
drifting_costs = cond_costs[cond_costs["DESCRIPTION"].isin(drifting_conditions)]

# Cost comparison
cost_per_encounter_stable = stable_costs["TOTAL_CLAIM_COST"].mean()
cost_per_encounter_drifting = drifting_costs["TOTAL_CLAIM_COST"].mean()

# Total cost burden
total_cost_stable = stable_costs["TOTAL_CLAIM_COST"].sum()
total_cost_drifting = drifting_costs["TOTAL_CLAIM_COST"].sum()

# Payer coverage gap
payer_gap_stable = (stable_costs["TOTAL_CLAIM_COST"] - stable_costs["PAYER_COVERAGE"]).mean()
payer_gap_drifting = (drifting_costs["TOTAL_CLAIM_COST"] - drifting_costs["PAYER_COVERAGE"]).mean()

# Cost variance (proxy for coding uncertainty)
cost_cv_stable = stable_costs.groupby("DESCRIPTION")["TOTAL_CLAIM_COST"].std().mean()
cost_cv_drifting = drifting_costs.groupby("DESCRIPTION")["TOTAL_CLAIM_COST"].std().mean()

p12_results = {
    "cost_comparison": {
        "mean_cost_stable_conditions": round(cost_per_encounter_stable, 2),
        "mean_cost_drifting_conditions": round(cost_per_encounter_drifting, 2),
        "cost_ratio": round(cost_per_encounter_drifting / max(cost_per_encounter_stable, 1), 2),
        "total_cost_stable": round(total_cost_stable, 2),
        "total_cost_drifting": round(total_cost_drifting, 2),
    },
    "payer_coverage_gap": {
        "mean_gap_stable": round(payer_gap_stable, 2),
        "mean_gap_drifting": round(payer_gap_drifting, 2),
        "gap_ratio": round(payer_gap_drifting / max(payer_gap_stable, 1), 2)
    },
    "cost_variance": {
        "mean_std_stable": round(cost_cv_stable, 2) if not np.isnan(cost_cv_stable) else 0,
        "mean_std_drifting": round(cost_cv_drifting, 2) if not np.isnan(cost_cv_drifting) else 0,
    },
    "n_stable_conditions": len(stable_conditions),
    "n_drifting_conditions": len(drifting_conditions),
    "encounter_class_distribution": {
        "stable": dict(stable_costs["ENCOUNTERCLASS"].value_counts().head(5)),
        "drifting": dict(drifting_costs["ENCOUNTERCLASS"].value_counts().head(5))
    }
}

print(f"  Stable conditions (>5% prev): {len(stable_conditions)}")
print(f"  Drifting conditions (<1% prev): {len(drifting_conditions)}")
print(f"  Mean cost/encounter - stable: ${cost_per_encounter_stable:,.2f}")
print(f"  Mean cost/encounter - drifting: ${cost_per_encounter_drifting:,.2f}")
print(f"  Cost ratio (drifting/stable): {p12_results['cost_comparison']['cost_ratio']}x")
print(f"  Payer gap - stable: ${payer_gap_stable:,.2f}")
print(f"  Payer gap - drifting: ${payer_gap_drifting:,.2f}")
print()

all_results["P12_cost_of_drift"] = p12_results

# ============================================================
# S1: TERMINOLOGY COVERAGE GAP
# ============================================================
print("=" * 70)
print("S1: TERMINOLOGY COVERAGE GAP ANALYSIS")
print("=" * 70)
print()

# Analyze how well the condition vocabulary maps to standard ontologies
# Using the SNOMED-CT codes in the dataset as reference

unique_conditions = conditions[["CODE", "DESCRIPTION"]].drop_duplicates()

# Check for digital health / AI-specific terms
ai_health_terms = [
    "telemedicine", "telehealth", "remote monitoring", "wearable",
    "digital", "AI", "artificial intelligence", "machine learning",
    "clinical decision support", "algorithm", "chatbot", "virtual care",
    "mHealth", "eHealth", "remote patient", "sensor", "app-based",
    "automated", "predictive", "screening tool"
]

# Search in condition descriptions
ai_term_hits = {}
for term in ai_health_terms:
    matches = unique_conditions[unique_conditions["DESCRIPTION"].str.contains(
        term, case=False, na=False
    )]
    if len(matches) > 0:
        ai_term_hits[term] = list(matches["DESCRIPTION"].unique())

# Terminology structure analysis
# How many conditions have standardized (numeric) codes vs. text-only?
unique_conditions = unique_conditions.copy()
unique_conditions["code_type"] = unique_conditions["CODE"].apply(
    lambda x: "numeric_snomed" if str(x).isdigit() else "alphanumeric"
)

# Description complexity (proxy for ontological expressiveness)
unique_conditions["desc_word_count"] = unique_conditions["DESCRIPTION"].str.split().str.len()
unique_conditions["has_qualifier"] = unique_conditions["DESCRIPTION"].str.contains(
    r"\(disorder\)|\(finding\)|\(situation\)|\(procedure\)", case=False, na=False
)

# Coverage analysis: what percentage of conditions have proper SNOMED qualifiers?
qualified = unique_conditions["has_qualifier"].sum()
unqualified = len(unique_conditions) - qualified

s1_results = {
    "total_unique_conditions": len(unique_conditions),
    "ai_health_terms_found": len(ai_term_hits),
    "ai_health_terms_searched": len(ai_health_terms),
    "ai_coverage_gap": round((1 - len(ai_term_hits) / len(ai_health_terms)) * 100, 1),
    "ai_terms_with_matches": ai_term_hits,
    "ai_terms_without_matches": [t for t in ai_health_terms if t not in ai_term_hits],
    "ontological_quality": {
        "with_snomed_qualifier": int(qualified),
        "without_qualifier": int(unqualified),
        "qualifier_rate": round(qualified / len(unique_conditions) * 100, 1)
    },
    "description_complexity": {
        "mean_word_count": round(unique_conditions["desc_word_count"].mean(), 1),
        "max_word_count": int(unique_conditions["desc_word_count"].max()),
        "single_word_conditions": int((unique_conditions["desc_word_count"] == 1).sum())
    },
    "code_types": dict(unique_conditions["code_type"].value_counts())
}

print(f"  Unique conditions in dataset: {len(unique_conditions)}")
print(f"  AI/digital health terms searched: {len(ai_health_terms)}")
print(f"  AI terms with SNOMED matches: {len(ai_term_hits)}")
print(f"  AI terminology coverage gap: {s1_results['ai_coverage_gap']}%")
print(f"  Terms WITHOUT SNOMED representation:")
for term in s1_results["ai_terms_without_matches"]:
    print(f"    - {term}")
print(f"  SNOMED qualifier rate: {s1_results['ontological_quality']['qualifier_rate']}%")
print()

all_results["S1_terminology_coverage"] = s1_results

# ============================================================
# S2: SEMANTIC ENTROPY METRIC
# ============================================================
print("=" * 70)
print("S2: SEMANTIC ENTROPY IN CLINICAL CODING")
print("=" * 70)
print()

# Formal semantic entropy: H_sem = -sum(p_i * log(p_i))
# Applied to the distribution of condition codes within clinical domains

# Group conditions by clinical domain (first significant word)
conditions_unique = conditions[["CODE", "DESCRIPTION"]].drop_duplicates()
conditions_unique = conditions_unique.copy()

def extract_domain(desc):
    """Extract clinical domain from SNOMED description."""
    desc = str(desc).lower()
    if "diabetes" in desc: return "Metabolic-Diabetes"
    if "hypertens" in desc: return "Cardiovascular-Hypertension"
    if "neoplasm" in desc or "carcinoma" in desc or "cancer" in desc: return "Oncology"
    if "fracture" in desc: return "Musculoskeletal-Fracture"
    if "infection" in desc or "viral" in desc or "bacterial" in desc: return "Infectious"
    if "asthma" in desc or "bronchit" in desc or "pneumonia" in desc: return "Respiratory"
    if "depress" in desc or "anxiety" in desc or "stress" in desc: return "Mental-Health"
    if "obesity" in desc or "body mass" in desc: return "Metabolic-Obesity"
    if "pain" in desc: return "Pain"
    if "kidney" in desc or "renal" in desc: return "Renal"
    return "Other"

conditions_unique["domain"] = conditions_unique["DESCRIPTION"].apply(extract_domain)

# Compute Shannon entropy per domain
domain_entropy = {}
for domain in conditions_unique["domain"].unique():
    domain_codes = conditions[conditions["CODE"].isin(
        conditions_unique[conditions_unique["domain"] == domain]["CODE"]
    )]
    code_dist = domain_codes["CODE"].value_counts(normalize=True)

    if len(code_dist) > 1:
        entropy = -sum(p * np.log2(p) for p in code_dist if p > 0)
        max_entropy = np.log2(len(code_dist))
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
    else:
        entropy = 0
        normalized_entropy = 0

    domain_entropy[domain] = {
        "n_codes": len(code_dist),
        "n_instances": len(domain_codes),
        "entropy_bits": round(entropy, 4),
        "max_entropy": round(max_entropy, 4) if len(code_dist) > 1 else 0,
        "normalized_entropy": round(normalized_entropy, 4)
    }

# Overall semantic entropy
all_code_dist = conditions["CODE"].value_counts(normalize=True)
overall_entropy = -sum(p * np.log2(p) for p in all_code_dist if p > 0)
max_overall = np.log2(len(all_code_dist))

# Sort domains by entropy
sorted_domains = sorted(domain_entropy.items(), key=lambda x: x[1]["entropy_bits"], reverse=True)

s2_results = {
    "overall_entropy": {
        "H_sem_bits": round(overall_entropy, 4),
        "H_max_bits": round(max_overall, 4),
        "normalized": round(overall_entropy / max_overall, 4),
        "n_codes": len(all_code_dist)
    },
    "domain_entropy": dict(sorted_domains),
    "high_entropy_domains": [d for d, v in sorted_domains if v["normalized_entropy"] > 0.8],
    "low_entropy_domains": [d for d, v in sorted_domains if v["normalized_entropy"] < 0.5 and v["n_codes"] > 1],
}

print(f"  Overall semantic entropy: {overall_entropy:.4f} bits (max: {max_overall:.4f})")
print(f"  Normalized entropy: {overall_entropy/max_overall:.4f}")
print(f"  Domain entropy (top 5):")
for domain, vals in sorted_domains[:5]:
    print(f"    {domain:<35} H={vals['entropy_bits']:.4f} bits, "
          f"norm={vals['normalized_entropy']:.4f}, n={vals['n_codes']} codes")
print(f"  High entropy domains (>0.8): {len(s2_results['high_entropy_domains'])}")
print(f"  Low entropy domains (<0.5): {len(s2_results['low_entropy_domains'])}")
print()

all_results["S2_semantic_entropy"] = s2_results

# ============================================================
# S3: CROSS-ORGANIZATION CODING VARIANCE
# ============================================================
print("=" * 70)
print("S3: CROSS-ORGANIZATION CODING VARIANCE (LOCK-IN PROXY)")
print("=" * 70)
print()

# Measure coding variation across organizations for the same conditions
# High variance = potential vendor lock-in / coding practice divergence

# Join encounters with organizations
enc_org = encounters[["Id", "ORGANIZATION", "ENCOUNTERCLASS"]].copy()
cond_org = conditions.merge(enc_org, left_on="ENCOUNTER", right_on="Id", how="left", suffixes=("", "_enc"))

# For top 20 conditions: measure coding variance across organizations
top_20_conditions = conditions["DESCRIPTION"].value_counts().head(20).index.tolist()

coding_variance = {}
for cond in top_20_conditions:
    cond_data = cond_org[cond_org["DESCRIPTION"] == cond]
    org_counts = cond_data.groupby("ORGANIZATION").size()

    if len(org_counts) < 3:
        continue

    # Coding rate per organization (normalized by org total encounters)
    org_total_encounters = enc_org.groupby("ORGANIZATION").size()
    coding_rates = (org_counts / org_total_encounters).dropna()

    if len(coding_rates) < 3:
        continue

    cv = coding_rates.std() / coding_rates.mean() if coding_rates.mean() > 0 else 0

    # HHI of coding concentration
    shares = org_counts / org_counts.sum()
    hhi = (shares ** 2).sum()

    coding_variance[cond[:50]] = {
        "n_organizations": len(org_counts),
        "mean_coding_rate": round(coding_rates.mean(), 6),
        "std_coding_rate": round(coding_rates.std(), 6),
        "cv": round(cv, 4),
        "hhi": round(hhi, 6),
        "max_rate": round(coding_rates.max(), 6),
        "min_rate": round(coding_rates.min(), 6),
        "rate_ratio_max_min": round(coding_rates.max() / max(coding_rates.min(), 1e-10), 1)
    }

# Sort by CV
sorted_variance = sorted(coding_variance.items(), key=lambda x: x[1]["cv"], reverse=True)

s3_results = {
    "n_organizations": int(organizations["Id"].nunique()),
    "coding_variance_by_condition": dict(sorted_variance),
    "summary": {
        "mean_cv_across_conditions": round(np.mean([v["cv"] for v in coding_variance.values()]), 4),
        "max_cv_condition": sorted_variance[0][0] if sorted_variance else "",
        "max_cv_value": sorted_variance[0][1]["cv"] if sorted_variance else 0,
        "mean_hhi": round(np.mean([v["hhi"] for v in coding_variance.values()]), 6),
        "conditions_with_high_variance": len([v for v in coding_variance.values() if v["cv"] > 0.5])
    }
}

print(f"  Organizations: {s3_results['n_organizations']}")
print(f"  Mean CV across conditions: {s3_results['summary']['mean_cv_across_conditions']:.4f}")
print(f"  Highest variance condition: {s3_results['summary']['max_cv_condition'][:40]}")
print(f"  Conditions with high variance (CV>0.5): {s3_results['summary']['conditions_with_high_variance']}")
print(f"  Mean HHI: {s3_results['summary']['mean_hhi']:.6f}")
print()
print("  Top 5 by coding variance:")
for cond, vals in sorted_variance[:5]:
    print(f"    {cond[:45]:<45} CV={vals['cv']:.4f}, HHI={vals['hhi']:.6f}, "
          f"ratio={vals['rate_ratio_max_min']:.1f}x")
print()

all_results["S3_coding_variance"] = s3_results

# ============================================================
# PRAXIS-AI: FRAMEWORK DOMAIN OPERATIONALIZATION
# ============================================================
print("=" * 70)
print("PRAXIS-AI: FRAMEWORK DOMAIN OPERATIONALIZATION")
print("=" * 70)
print()

# Operationalize PRAXIS-AI's 7 domains against measurable metrics
# from the Synthea dataset

# Domain 1: Clinical Workflow Integration
encounter_classes = encounters["ENCOUNTERCLASS"].value_counts()
workflow_diversity = len(encounter_classes)
ambulatory_share = encounter_classes.get("ambulatory", 0) / len(encounters)

# Domain 2: Data Quality & Ontological Integrity
conditions_with_code = conditions["CODE"].notna().sum()
data_completeness = conditions_with_code / len(conditions)

# Domain 3: Patient Safety & Diagnostic Accuracy
# Proxy: patients with contradictory conditions
# (e.g., both "Diabetes" and "Prediabetes" simultaneously)
diabetes_patients = set(conditions[conditions["DESCRIPTION"].str.contains("Diabetes mellitus", na=False)]["PATIENT"])
prediabetes_patients = set(conditions[conditions["DESCRIPTION"].str.contains("Prediabetes", na=False)]["PATIENT"])
contradictory = diabetes_patients & prediabetes_patients

# Domain 4: Regulatory Compliance Readiness
# Proxy: percentage of encounters with complete cost/payer documentation
encounters_cost = encounters.copy()
encounters_cost["TOTAL_CLAIM_COST"] = pd.to_numeric(encounters_cost["TOTAL_CLAIM_COST"], errors="coerce")
complete_billing = encounters_cost["TOTAL_CLAIM_COST"].notna().sum() / len(encounters_cost)

# Domain 5: Health Equity
patient_demographics = patients.copy()
gender_dist = patient_demographics["GENDER"].value_counts(normalize=True)
race_dist = patient_demographics["RACE"].value_counts(normalize=True)
race_entropy = -sum(p * np.log2(p) for p in race_dist if p > 0)

# Domain 6: Provider-Technology Interaction
provider_encounter_load = encounters.groupby("PROVIDER")["Id"].count()
provider_load_cv = provider_encounter_load.std() / provider_encounter_load.mean()

# Domain 7: Scalability & Sustainability
yearly_encounters = encounters.copy()
yearly_encounters["YEAR"] = pd.to_datetime(yearly_encounters["START"], errors="coerce").dt.year
encounter_growth = yearly_encounters.groupby("YEAR").size()
recent_years = encounter_growth[encounter_growth.index >= 2020]
if len(recent_years) >= 2:
    growth_rate = (recent_years.iloc[-1] / recent_years.iloc[0]) ** (1 / len(recent_years)) - 1
else:
    growth_rate = 0

praxis_results = {
    "domain_metrics": {
        "D1_workflow_integration": {
            "encounter_class_diversity": int(workflow_diversity),
            "ambulatory_share": round(ambulatory_share, 4),
            "primary_care_relevant": round((encounter_classes.get("ambulatory", 0) + encounter_classes.get("wellness", 0)) / len(encounters), 4)
        },
        "D2_data_quality": {
            "snomed_coding_completeness": round(data_completeness, 4),
            "unique_condition_codes": int(conditions["CODE"].nunique()),
            "code_description_ratio": round(conditions["CODE"].nunique() / max(conditions["DESCRIPTION"].nunique(), 1), 4)
        },
        "D3_patient_safety": {
            "contradictory_diagnoses": len(contradictory),
            "pct_contradictory": round(len(contradictory) / n_patients * 100, 2),
        },
        "D4_regulatory_compliance": {
            "billing_completeness": round(complete_billing, 4),
        },
        "D5_health_equity": {
            "gender_balance": dict(gender_dist.round(4)),
            "race_diversity_entropy": round(race_entropy, 4),
            "n_race_categories": len(race_dist),
        },
        "D6_provider_interaction": {
            "mean_encounters_per_provider": round(provider_encounter_load.mean(), 1),
            "provider_load_cv": round(provider_load_cv, 4),
        },
        "D7_scalability": {
            "total_encounters": len(encounters),
            "annual_growth_rate": round(growth_rate, 4),
        }
    }
}

print("  PRAXIS-AI Domain Operationalization:")
for domain, metrics in praxis_results["domain_metrics"].items():
    print(f"    {domain}:")
    for k, v in metrics.items():
        if isinstance(v, dict):
            print(f"      {k}: {v}")
        else:
            print(f"      {k}: {v}")
print()

all_results["PRAXIS_AI_operationalization"] = praxis_results

# ============================================================
# SAVE ALL RESULTS
# ============================================================
print("=" * 70)
print("SAVING ALL RESULTS")
print("=" * 70)

all_results["metadata"] = {
    "studies": ["P1", "P11", "P12", "S1", "S2", "S3", "PRAXIS-AI"],
    "dataset": "Synthea v3.x synthetic EHR",
    "n_patients": n_patients,
    "timestamp": datetime.now().isoformat(),
    "citation": "Walonoski J et al. Synthea: An approach, method, and software mechanism for generating synthetic patients and the synthetic electronic health care record. JAMIA 2018;25(3):230-238."
}

output_file = OUTPUT_DIR / "corpus_batch_results.json"
with open(output_file, "w") as f:
    json.dump(all_results, f, indent=2, default=str)

print(f"All results saved to: {output_file}")
print()
print("DONE. All 7 experiments completed.")
