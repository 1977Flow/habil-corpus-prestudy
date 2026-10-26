# Habilitation Corpus: Computational Pre-Studies on Synthetic EHR Data

Reproducible analysis scripts and results for the computational pre-studies reported across the habilitation corpus on ontological distortion and terminology governance in clinical AI systems.

## Dataset

All analyses use **Synthea v3.x** (Walonoski et al., JAMIA 2018), an open-source synthetic patient generator producing realistic but entirely fictional electronic health records.

- **Patients:** 11,475 (10,000 alive, 1,475 deceased)
- **Conditions:** 415,464 (SNOMED-CT coded, 309 unique)
- **Observations:** 8,750,706 (vital signs, laboratory values)
- **Encounters:** 677,938 across 1,146 provider organisations
- **Medications:** 592,721 records
- **Geographic context:** Massachusetts, USA
- **All data are synthetic. No real patient information was used.**

The dataset is deterministically reproducible. To regenerate:

```bash
git clone https://github.com/synthetichealth/synthea.git
cd synthea
./run_synthea -p 11475 -s 42 Massachusetts
```

## Experiments

### P2: Artificial Epidemiology (D(C) Divergence)

**Script:** `scripts/p2_artificial_epidemiology.py`
**Results:** `results/p2_dc_divergence_results.json`

Operationalises the artificial epidemiology divergence D(C) = P_a(C) - P_c(C) for five sentinel conditions, simulates upcoding amplification, and validates three of the five proposed markers (comorbidity inflation, documentation-action gap, temporal drift).

**Key findings:**
- D(C) = +0.378 for diabetes (administrative over-representation)
- D(C) = -0.024 for hypertension (clinical under-coding)
- Comorbidity co-occurrence ratios 1.5x to 2.4x across sentinel condition pairs
- Documentation-action gap: 75.7% for coded diabetes

### P3: Preserve, Don't Prune (Dormancy vs. Pruning)

**Script:** `scripts/p3_dormancy_pruning.py`
**Results:** `results/p3_dormancy_pruning_results.json`

Simulates frequency-based pruning at multiple prevalence thresholds, measuring vocabulary loss, patient impact, and clinically significant conditions at risk.

**Key findings:**
- At 1% threshold: 46.9% vocabulary lost, 24.4% patients affected
- 34 clinically actionable conditions in the pruning zone (heart failure, asthma, atrial fibrillation)
- 80% of rare conditions have diagnostic bridges to common conditions

### Corpus Batch (P1, P11, P12, S1, S2, S3, PRAXIS-AI)

**Script:** `scripts/corpus_experiments_batch.py`
**Results:** `results/corpus_batch_results.json`

Seven additional experiments across the habilitation corpus:

| Paper | Experiment | Key Finding |
|---|---|---|
| P1 | SNOMED information structure | 25.4% conditions without resolution date |
| P11 | Drift Sentinel validation | 5 drift alerts, cumulative JSD 0.113 over 21 years |
| P12 | Cost of drift | Drifting conditions 4.32x more expensive per encounter |
| S1 | Terminology coverage gap | 95% of AI/digital health terms absent from SNOMED |
| S2 | Semantic entropy | Overall H = 5.35 bits, Oncology highest entropy (0.903) |
| S3 | Coding variance | Mean CV 0.666 across organisations, 17/20 conditions high variance |
| PRAXIS-AI | Domain operationalisation | 5.3% contradictory diagnoses, provider load CV 2.41 |

### Governing the Loop, revision 1 (real coding data and learning agent)

**Folder:** `pdig_r1/`

Code and aggregate results for the revised manuscript "Governing the Loop: Three Architectures for AI Systems That Co-Produce Clinical and Administrative Reality" (Stummer, Schumacher, Thulesius, Müller, Frese). This analysis does not use Synthea.

- `scripts/fetch_cms_cc_mcc.py` downloads the CMS MS-DRG v41.1 lists of complications or comorbidities (Appendix G) and major complications or comorbidities (Appendix H part 1) to `cms/cc_mcc_v41_1.csv`.
- `scripts/mimic_coding_context.py` and `scripts/mimic_retention.py` compare, for the same emergency-department-to-admission episodes, the ICD-10-CM codes assigned in the emergency department and on the hospital discharge claim.
- `scripts/learning_agent_loop.py` simulates a policy-gradient coding agent on the real code structure of these episodes (full grid of administrative weight, observability and reference regime, sensitivity and bootstrap analyses).
- `scripts/summarise_and_plot.py` produces the summary, the supporting tables S1 to S3 and Fig 2; `scripts/draw_fig1_fig3.py` draws Figs 1 and 3.

**Data:** MIMIC-IV-ECG-Ext-ICD v1.0.1 (Strodthoff N, Lopez Alcaraz JM, Haverkamp W; PhysioNet 2024; doi:10.13026/ypt5-9d58). The dataset is available to credentialed PhysioNet users and is not distributed here. Set the environment variable `MIMIC_ECG_ICD_CSV` to the path of `records_w_diag_icd10.csv`. Only aggregate results are included in `pdig_r1/results/`.

### Figures

**Scripts:** `figures/generate_p2_figures.py`, `figures/generate_p3_figures.py`

Publication-ready figures (300 DPI, PDF + PNG) for P2 and P3.

## Reproducibility

All scripts require Python 3.10+ with:

```
pandas>=2.0
numpy>=1.24
matplotlib>=3.7
scipy>=1.11   # pdig_r1 only
```

To reproduce all results:

```bash
# 1. Generate Synthea data (or use pre-generated CSVs)
# 2. Place CSVs in data/ directory
# 3. Run experiments
python scripts/p2_artificial_epidemiology.py
python scripts/p3_dormancy_pruning.py
python scripts/corpus_experiments_batch.py
python figures/generate_p2_figures.py
python figures/generate_p3_figures.py
```

## Citation

If you use these scripts or results, please cite the relevant paper(s) from the habilitation corpus. See individual paper preprints for full citation information.

## Associated Papers

- **P1:** Stummer FO. The symptom and the billing code. SSRN [preprint]. 2026. doi:10.2139/ssrn.6475038
- **P2:** Stummer FO. Artificial epidemiology. Cambridge Open Engage [preprint]. 2026. doi:10.33774/coe-2026-ssm1q
- **P3:** Stummer FO. Preserve, don't prune. Research Square [preprint]. 2026. doi:10.21203/rs.3.rs-9321746/v1
- **EMoT:** Stummer FO. Enhanced Mycelium of Thought. arXiv [preprint]. 2026. arXiv:2603.24065

The preprint venues for P2 and P3 were listed incorrectly as medRxiv in the initial release; corrected on 26 October 2026.

## License

MIT License. See LICENSE file.

## Data Source

Walonoski J, Kramer M, Nichols J, et al. Synthea: an approach, method, and software mechanism for generating synthetic patients and the synthetic electronic health care record. J Am Med Inform Assoc. 2018;25(3):230-238. doi:10.1093/jamia/ocx079
