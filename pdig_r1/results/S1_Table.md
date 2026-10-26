# S1 Table. Observational analysis: same episodes, two coding contexts (MIMIC-IV-ECG-Ext-ICD v1.0.1)

Episodes: 97,737; patients: 57,304. Reimbursement relevance: CMS MS-DRG v41.1 Appendix G (CC) and H part 1 (MCC).

## A. Sentinel condition families

| Family | ICD-10-CM prefixes | ED prevalence | Hospital-claim prevalence | ED only (n) | Hospital only (n) | Exact McNemar P |
|---|---|---|---|---|---|---|
| diabetes | E08, E09, E10, E11, E13 | 0.0796 | 0.3047 | 310 | 22,315 | <0.001 |
| hypertension | I10, I11, I12, I13, I15, I16 | 0.1323 | 0.6299 | 946 | 49,580 | <0.001 |
| depression | F32, F33 | 0.0154 | 0.1911 | 238 | 17,410 | <0.001 |
| heart failure | I50 | 0.0479 | 0.2242 | 321 | 17,547 | <0.001 |
| chronic kidney disease | N18 | 0.0178 | 0.2088 | 55 | 18,728 | <0.001 |
| hyponatraemia | E87.1 | 0.0093 | 0.0736 | 231 | 6,522 | <0.001 |
| malnutrition | E40-E46 | 0.0003 | 0.0406 | <11 | 3,947 | <0.001 |

Counts below 11 are suppressed.

## B. Codes on the hospital claim by reimbursement tier

| Code group | n | none | CC | MCC |
|---|---|---|---|---|
| Added in hospital claim | 1,225,799 | 0.7987 | 0.1441 | 0.0572 |
| Also coded in ED | 98,857 | 0.7045 | 0.1904 | 0.1052 |

## C. Retention of ED codes on the hospital claim, by ICD-10-CM chapter

ED codes: 210,575; retained: 98,857 (0.4695); hospital codes: 1,324,656.

| Chapter | Share of ED codes | Retained on hospital claim | Share of hospital codes |
|---|---|---|---|
| R symptoms, signs, abnormal findings | 0.3107 | 0.3194 | 0.0916 |
| I circulatory | 0.1701 | 0.6069 | 0.1706 |
| other | 0.1303 | 0.3985 | 0.2180 |
| E endocrine, metabolic | 0.0954 | 0.5575 | 0.1273 |
| S-T injury, poisoning | 0.0614 | 0.5318 | 0.0286 |
| J respiratory | 0.0572 | 0.4936 | 0.0418 |
| N genitourinary | 0.0491 | 0.6801 | 0.0506 |
| K digestive | 0.0490 | 0.3750 | 0.0607 |
| Z factors influencing health status | 0.0402 | 0.6673 | 0.1496 |
| F mental, behavioural | 0.0367 | 0.6119 | 0.0611 |

JSD between three-character category distributions: 0.2647 bits (95% bootstrap interval 0.2642 to 0.2671, 200 resamples).