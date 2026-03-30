"""
P3 Figures: Preserve, Don't Prune
===================================
Figure 1: Pruning Impact Curve (vocabulary loss vs. patients affected)
Figure 2: Clinically Actionable Rare Conditions at Pruning Risk
Figure 3: Diagnostic Bridge Network (simplified)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

OUTPUT_DIR = Path(r"C:\Users\Flori\Documents\8daw\MMDS_ontology\docs\figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    'font.family': 'Arial',
    'font.size': 10,
    'axes.linewidth': 1.2,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.15,
})

C_CLINICAL = '#2E86AB'
C_ADMIN = '#A23B72'
C_ALERT = '#E63946'
C_SAFE = '#2A9D8F'
C_WARN = '#E9C46A'
C_NEUTRAL = '#555555'

# ============================================================
# FIGURE 1: Pruning Impact Dual-Axis
# ============================================================
print("Generating P3 Figure 1: Pruning Impact...")

thresholds = [0.1, 0.5, 1.0, 2.0, 5.0]
vocab_lost = [17.5, 35.9, 46.9, 58.9, 76.4]
patients_affected = [1.7, 10.8, 24.4, 47.9, 78.3]
actionable = [8, 18, 34, None, None]  # only measured for first 3

fig, ax1 = plt.subplots(figsize=(7, 4.5))

# Vocabulary loss
line1 = ax1.plot(thresholds, vocab_lost, 'o-', color=C_ALERT, linewidth=2.5, markersize=8,
    label='Diagnostic vocabulary lost (%)', zorder=3)
ax1.set_xlabel('Pruning threshold (% prevalence)', fontsize=11)
ax1.set_ylabel('Vocabulary lost (%)', fontsize=11, color=C_ALERT)
ax1.tick_params(axis='y', labelcolor=C_ALERT)
ax1.set_ylim(0, 85)

# Patients affected on second axis
ax2 = ax1.twinx()
line2 = ax2.plot(thresholds, patients_affected, 's--', color=C_CLINICAL, linewidth=2.5, markersize=8,
    label='Patients affected (%)', zorder=3)
ax2.set_ylabel('Patients affected (%)', fontsize=11, color=C_CLINICAL)
ax2.tick_params(axis='y', labelcolor=C_CLINICAL)
ax2.set_ylim(0, 85)
ax2.spines['right'].set_visible(True)

# Highlight the 1% threshold (most clinically relevant)
ax1.axvline(1.0, color=C_NEUTRAL, linewidth=1, linestyle=':', alpha=0.7)
ax1.annotate('Clinical threshold\n(1% prevalence)',
    xy=(1.0, 50), fontsize=8, ha='center', color=C_NEUTRAL, style='italic')

# Annotate key data points at 1%
ax1.annotate('46.9% vocabulary', xy=(1.0, 46.9), xytext=(2.2, 55),
    fontsize=8, color=C_ALERT, fontweight='bold',
    arrowprops=dict(arrowstyle='->', color=C_ALERT, lw=1.5))
ax2.annotate('24.4% patients', xy=(1.0, 24.4), xytext=(2.5, 35),
    fontsize=8, color=C_CLINICAL, fontweight='bold',
    arrowprops=dict(arrowstyle='->', color=C_CLINICAL, lw=1.5))

# Combined legend
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left', fontsize=9, frameon=False)

ax1.set_title('A. Pruning impact on diagnostic vocabulary and patient coverage',
    fontsize=10, fontweight='bold', loc='left')

fig.text(0.5, -0.06,
    'Figure 1. Frequency-based pruning eliminates nearly half the diagnostic vocabulary\n'
    'at a 1% prevalence threshold, affecting one quarter of the patient population.\n'
    'Synthea synthetic EHR, n = 11,475 patients, 309 unique SNOMED-CT conditions.',
    fontsize=8, ha='center', color=C_NEUTRAL)

plt.savefig(OUTPUT_DIR / "P3_Figure1_Pruning_Impact.png", facecolor='white')
plt.savefig(OUTPUT_DIR / "P3_Figure1_Pruning_Impact.pdf", facecolor='white')
plt.close()
print("  Saved P3_Figure1_Pruning_Impact.png/pdf")


# ============================================================
# FIGURE 2: Clinically Actionable Rare Conditions
# ============================================================
print("Generating P3 Figure 2: Actionable Rare Conditions...")

conditions = [
    'Non-small cell lung carcinoma',
    'Asthma',
    'Heart failure',
    'Atrial fibrillation',
    'Small cell lung neoplasm',
    'Malignant neoplasm of colon',
    'Opioid abuse',
    'HIV infection',
    'Deep venous thrombosis',
    'Septic shock',
]
prevalences = [0.0095, 0.0012, 0.0010, 0.0091, 0.0016, 0.0065, 0.0083, 0.0032, 0.0056, 0.0077]
prescriptions = [43688, 19478, 12089, 10843, 9678, 1116, 800, 704, 380, 355]

fig, axes = plt.subplots(1, 2, figsize=(10, 5), gridspec_kw={'width_ratios': [1, 1.2]})

# Panel A: Prevalence (below 1% threshold)
ax = axes[0]
y_pos = np.arange(len(conditions))
bars = ax.barh(y_pos, [p * 100 for p in prevalences], color=C_ALERT, alpha=0.8, edgecolor='white')
ax.axvline(1.0, color=C_NEUTRAL, linewidth=2, linestyle='--', alpha=0.7)
ax.text(1.05, 9.5, '1% pruning\nthreshold', fontsize=8, color=C_NEUTRAL, va='top')
ax.set_yticks(y_pos)
ax.set_yticklabels(conditions, fontsize=8.5)
ax.set_xlabel('Prevalence (%)', fontsize=10)
ax.set_title('A. Prevalence (all below pruning threshold)', fontsize=10, fontweight='bold', loc='left')
ax.invert_yaxis()

# Panel B: Associated prescriptions (clinical significance)
ax2 = axes[1]
bars2 = ax2.barh(y_pos, prescriptions, color=C_SAFE, alpha=0.8, edgecolor='white')
ax2.set_yticks(y_pos)
ax2.set_yticklabels([''] * len(conditions))
ax2.set_xlabel('Associated prescriptions in dataset', fontsize=10)
ax2.set_title('B. Clinical significance (active treatment)', fontsize=10, fontweight='bold', loc='left')
ax2.invert_yaxis()

# Annotate top 3
for i in range(3):
    ax2.text(prescriptions[i] + 500, i, f'{prescriptions[i]:,}', va='center', fontsize=8, fontweight='bold')

plt.tight_layout()
fig.text(0.5, -0.06,
    'Figure 2. Ten clinically actionable conditions that fall below the 1% pruning threshold.\n'
    'These conditions are rare by prevalence but clinically significant: heart failure alone\n'
    'accounts for 12,089 linked prescriptions. Pruning removes them from the AI training set.',
    fontsize=8, ha='center', color=C_NEUTRAL)

plt.savefig(OUTPUT_DIR / "P3_Figure2_Actionable_Rare.png", facecolor='white')
plt.savefig(OUTPUT_DIR / "P3_Figure2_Actionable_Rare.pdf", facecolor='white')
plt.close()
print("  Saved P3_Figure2_Actionable_Rare.png/pdf")


# ============================================================
# FIGURE 3: Diagnostic Bridge Concept
# ============================================================
print("Generating P3 Figure 3: Diagnostic Bridges...")

fig, axes = plt.subplots(1, 2, figsize=(10, 5))

for ax_idx, (ax, title, show_bridges) in enumerate(zip(axes,
    ['A. With dormancy (bridges preserved)', 'B. After pruning (bridges severed)'],
    [True, False])):

    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.axis('off')
    ax.set_title(title, fontsize=10, fontweight='bold', loc='left')

    # Common conditions (center, large)
    common_conditions = [
        ('Diabetes', 0, 0.3, 0.35),
        ('Hypertension', -0.5, -0.4, 0.3),
        ('Obesity', 0.5, -0.4, 0.3),
    ]

    for name, cx, cy, radius in common_conditions:
        circle = plt.Circle((cx, cy), radius, facecolor='#E8F4FD', edgecolor=C_CLINICAL, linewidth=2)
        ax.add_patch(circle)
        ax.text(cx, cy, name, ha='center', va='center', fontsize=8, fontweight='bold', color=C_CLINICAL)

    # Rare conditions (periphery, small)
    rare_conditions = [
        ('Heart\nfailure', -1.1, 0.8, 0.2),
        ('Asthma', 1.1, 0.8, 0.2),
        ('Atrial\nfib.', -1.1, -0.2, 0.2),
        ('HIV', 1.1, -0.2, 0.2),
        ('DVT', 0, -1.1, 0.2),
    ]

    for name, cx, cy, radius in rare_conditions:
        if show_bridges:
            fc = '#FFF3E0'
            ec = C_WARN
            alpha = 1.0
        else:
            fc = '#F5F5F5'
            ec = '#CCCCCC'
            alpha = 0.3

        circle = plt.Circle((cx, cy), radius, facecolor=fc, edgecolor=ec, linewidth=1.5, alpha=alpha)
        ax.add_patch(circle)
        ax.text(cx, cy, name, ha='center', va='center', fontsize=7,
            color=C_WARN if show_bridges else '#CCCCCC', alpha=alpha)

    # Draw bridges (connections between rare and common)
    if show_bridges:
        bridges = [
            ((-1.1, 0.8), (0, 0.3)),      # Heart failure -> Diabetes
            ((-1.1, 0.8), (-0.5, -0.4)),   # Heart failure -> Hypertension
            ((1.1, 0.8), (0, 0.3)),         # Asthma -> Diabetes
            ((1.1, 0.8), (0.5, -0.4)),      # Asthma -> Obesity
            ((-1.1, -0.2), (-0.5, -0.4)),   # Atrial fib -> Hypertension
            ((1.1, -0.2), (0.5, -0.4)),     # HIV -> Obesity
            ((0, -1.1), (-0.5, -0.4)),      # DVT -> Hypertension
        ]
        for (x1, y1), (x2, y2) in bridges:
            ax.plot([x1, x2], [y1, y2], '-', color=C_WARN, linewidth=1.5, alpha=0.6, zorder=0)
    else:
        # Show severed connections (red X marks)
        for name, cx, cy, radius in rare_conditions:
            ax.plot(cx, cy, 'x', color=C_ALERT, markersize=15, markeredgewidth=2.5, zorder=5)

    # Legend elements
    if ax_idx == 0:
        ax.text(-1.4, -1.4, 'Common (>5%)', fontsize=7, color=C_CLINICAL, fontweight='bold')
        ax.text(0.2, -1.4, 'Rare (<1%)', fontsize=7, color=C_WARN, fontweight='bold')
    else:
        ax.text(-1.4, -1.4, 'Diagnostic context lost', fontsize=7, color=C_ALERT, fontweight='bold')

fig.text(0.5, -0.04,
    'Figure 3. Diagnostic bridges between rare and common conditions.\n'
    'Dormancy preserves the co-occurrence context (A); pruning severs it (B),\n'
    'reducing common conditions to context-free codes. 80% of rare conditions\n'
    'have at least one diagnostic bridge to a common condition.',
    fontsize=8, ha='center', color=C_NEUTRAL)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "P3_Figure3_Diagnostic_Bridges.png", facecolor='white')
plt.savefig(OUTPUT_DIR / "P3_Figure3_Diagnostic_Bridges.pdf", facecolor='white')
plt.close()
print("  Saved P3_Figure3_Diagnostic_Bridges.png/pdf")

print("\nP3 figures complete.")
