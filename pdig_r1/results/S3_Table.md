# S3 Table. Sensitivity (rho = 0.5) and category bootstrap (30 resamples)

| Variant | Reference | w_admin | JSD (cycle end) | MCC share | Accuracy |
|---|---|---|---|---|---|
| acc0.90 | anchored | 0.2 | 0.0001 | 0.085 | 0.998 |
| acc0.90 | anchored | 0.5 | 0.1007 | 0.207 | 0.867 |
| acc0.90 | anchored | 0.8 | 0.5463 | 0.354 | 0.358 |
| acc0.90 | reified | 0.2 | 0.0001 | 0.085 | 0.998 |
| acc0.90 | reified | 0.5 | 0.1525 | 0.220 | 0.807 |
| acc0.90 | reified | 0.8 | 0.5929 | 0.397 | 0.306 |
| acc0.99 | anchored | 0.2 | 0.0001 | 0.085 | 0.998 |
| acc0.99 | anchored | 0.5 | 0.0103 | 0.098 | 0.984 |
| acc0.99 | anchored | 0.8 | 0.3608 | 0.325 | 0.559 |
| acc0.99 | reified | 0.2 | 0.0001 | 0.085 | 0.998 |
| acc0.99 | reified | 0.5 | 0.0106 | 0.098 | 0.983 |
| acc0.99 | reified | 0.8 | 0.3717 | 0.325 | 0.547 |
| cycles50 | anchored | 0.2 | 0.0000 | 0.085 | 0.999 |
| cycles50 | anchored | 0.5 | 0.1063 | 0.212 | 0.868 |
| cycles50 | anchored | 0.8 | 0.6087 | 0.411 | 0.304 |
| cycles50 | reified | 0.2 | 0.0000 | 0.085 | 0.999 |
| cycles50 | reified | 0.5 | 0.1527 | 0.220 | 0.812 |
| cycles50 | reified | 0.8 | 0.6136 | 0.414 | 0.303 |
| steps10 | anchored | 0.2 | 0.0007 | 0.086 | 0.990 |
| steps10 | anchored | 0.5 | 0.0104 | 0.099 | 0.968 |
| steps10 | anchored | 0.8 | 0.2839 | 0.281 | 0.592 |
| steps10 | reified | 0.2 | 0.0007 | 0.086 | 0.990 |
| steps10 | reified | 0.5 | 0.0126 | 0.101 | 0.963 |
| steps10 | reified | 0.8 | 0.3169 | 0.302 | 0.564 |
| steps200 | anchored | 0.2 | 0.0000 | 0.085 | 0.999 |
| steps200 | anchored | 0.5 | 0.1160 | 0.222 | 0.859 |
| steps200 | anchored | 0.8 | 0.6209 | 0.415 | 0.296 |
| steps200 | reified | 0.2 | 0.0000 | 0.085 | 0.999 |
| steps200 | reified | 0.5 | 0.1627 | 0.230 | 0.803 |
| steps200 | reified | 0.8 | 0.6233 | 0.415 | 0.296 |
| tier_binary | anchored | 0.2 | 0.0001 | 0.273 | 0.998 |
| tier_binary | anchored | 0.5 | 0.3910 | 0.740 | 0.525 |
| tier_binary | anchored | 0.8 | 0.5471 | 0.907 | 0.358 |
| tier_binary | reified | 0.2 | 0.0001 | 0.273 | 0.997 |
| tier_binary | reified | 0.5 | 0.3997 | 0.745 | 0.521 |
| tier_binary | reified | 0.8 | 0.5513 | 0.911 | 0.354 |
| tier_cc_low | anchored | 0.2 | 0.0001 | 0.085 | 0.998 |
| tier_cc_low | anchored | 0.5 | 0.0975 | 0.204 | 0.877 |
| tier_cc_low | anchored | 0.8 | 0.3559 | 0.371 | 0.561 |
| tier_cc_low | reified | 0.2 | 0.0001 | 0.085 | 0.998 |
| tier_cc_low | reified | 0.5 | 0.1012 | 0.205 | 0.876 |
| tier_cc_low | reified | 0.8 | 0.3931 | 0.371 | 0.528 |

| Bootstrap | Reference | w_admin | JSD cycle 20 (2.5%, 50%, 97.5%) | Accuracy cycle 20 (2.5%, 50%, 97.5%) |
|---|---|---|---|---|
| categories | anchored | 0.2 | [0.0, 0.0001, 0.0001] | [0.9976, 0.9977, 0.9978] |
| categories | anchored | 0.5 | [0.0351, 0.0735, 0.1281] | [0.8308, 0.8975, 0.9449] |
| categories | anchored | 0.8 | [0.4108, 0.485, 0.5617] | [0.3489, 0.4255, 0.5011] |
| categories | reified | 0.2 | [0.0, 0.0001, 0.0001] | [0.9976, 0.9977, 0.9978] |
| categories | reified | 0.5 | [0.0704, 0.1203, 0.18] | [0.7737, 0.8447, 0.9055] |
| categories | reified | 0.8 | [0.4155, 0.4911, 0.5679] | [0.3454, 0.4194, 0.4969] |