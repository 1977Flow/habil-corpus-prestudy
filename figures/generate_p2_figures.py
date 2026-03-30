"""
P2 Figures: Artificial Epidemiology
====================================
Figure 1: POMDP State Diagram (conceptual)
Figure 2: D(C) Divergence Bar Chart (from Synthea data)
Figure 3: Reification Feedback Loop Amplification (governance simulation)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import numpy as np
from pathlib import Path

OUTPUT_DIR = Path(r"C:\Users\Flori\Documents\8daw\MMDS_ontology\docs\figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Publication style
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

# Color palette
C_CLINICAL = '#2E86AB'     # blue - clinical
C_ADMIN = '#A23B72'        # purple - administrative
C_NEUTRAL = '#555555'      # grey
C_ALERT = '#E63946'        # red - alert/danger
C_SAFE = '#2A9D8F'         # teal - safe/dormancy
C_WARN = '#E9C46A'         # yellow - warning
C_BG = '#FAFAFA'

# ============================================================
# FIGURE 1: POMDP Conceptual Diagram
# ============================================================
print("Generating Figure 1: POMDP State Diagram...")

fig, ax = plt.subplots(figsize=(8, 5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 7)
ax.axis('off')
fig.patch.set_facecolor('white')

# State boxes
clinical_box = mpatches.FancyBboxPatch((0.5, 4.2), 3.5, 1.8, boxstyle="round,pad=0.15",
    facecolor='#E8F4FD', edgecolor=C_CLINICAL, linewidth=2)
admin_box = mpatches.FancyBboxPatch((6, 4.2), 3.5, 1.8, boxstyle="round,pad=0.15",
    facecolor='#F5E6F0', edgecolor=C_ADMIN, linewidth=2)
agent_box = mpatches.FancyBboxPatch((3.25, 0.5), 3.5, 1.8, boxstyle="round,pad=0.15",
    facecolor='#F0F0F0', edgecolor=C_NEUTRAL, linewidth=2)

ax.add_patch(clinical_box)
ax.add_patch(admin_box)
ax.add_patch(agent_box)

# Labels
ax.text(2.25, 5.5, r'$s_{clin}$', fontsize=16, ha='center', va='center', fontweight='bold', color=C_CLINICAL)
ax.text(2.25, 4.8, 'Clinical State\n(hidden)', fontsize=9, ha='center', va='center', color=C_CLINICAL, style='italic')

ax.text(7.75, 5.5, r'$s_{admin}$', fontsize=16, ha='center', va='center', fontweight='bold', color=C_ADMIN)
ax.text(7.75, 4.8, 'Administrative State\n(observed)', fontsize=9, ha='center', va='center', color=C_ADMIN, style='italic')

ax.text(5.0, 1.8, 'AI Agent', fontsize=14, ha='center', va='center', fontweight='bold', color=C_NEUTRAL)
ax.text(5.0, 1.1, r'$\pi_{t+1} = f(\pi_t, R_t)$', fontsize=11, ha='center', va='center', color=C_NEUTRAL)

# Arrows
arrow_style = dict(arrowstyle='->', lw=2, connectionstyle='arc3,rad=0.15')

# Agent observes s_admin (solid, thick)
ax.annotate('', xy=(7.75, 4.2), xytext=(6.0, 2.3),
    arrowprops=dict(arrowstyle='->', lw=2.5, color=C_ADMIN, connectionstyle='arc3,rad=-0.2'))
ax.text(7.8, 3.2, 'Observes\n(immediate)', fontsize=8, ha='center', color=C_ADMIN, fontweight='bold')

# Agent cannot observe s_clin (dashed, thin)
ax.annotate('', xy=(2.25, 4.2), xytext=(4.0, 2.3),
    arrowprops=dict(arrowstyle='->', lw=1.5, color=C_CLINICAL, linestyle='dashed', connectionstyle='arc3,rad=0.2'))
ax.text(2.0, 3.2, 'Hidden\n(delayed, noisy)', fontsize=8, ha='center', color=C_CLINICAL, style='italic')

# Reward labels
reward_box_admin = mpatches.FancyBboxPatch((7.5, 3.4), 2.2, 0.6, boxstyle="round,pad=0.1",
    facecolor='#F5E6F0', edgecolor=C_ADMIN, linewidth=1.5, linestyle='-')
ax.add_patch(reward_box_admin)
ax.text(8.6, 3.7, r'$R_{admin}$: immediate', fontsize=8, ha='center', va='center', color=C_ADMIN, fontweight='bold')

reward_box_clin = mpatches.FancyBboxPatch((0.3, 3.4), 2.2, 0.6, boxstyle="round,pad=0.1",
    facecolor='#E8F4FD', edgecolor=C_CLINICAL, linewidth=1.5, linestyle='dashed')
ax.add_patch(reward_box_clin)
ax.text(1.4, 3.7, r'$R_{clin}$: delayed', fontsize=8, ha='center', va='center', color=C_CLINICAL)

# Meta-loop arrow (self-referential)
ax.annotate('', xy=(3.25, 1.0), xytext=(6.75, 1.0),
    arrowprops=dict(arrowstyle='->', lw=2, color=C_ALERT, connectionstyle='arc3,rad=-0.5'))
ax.text(5.0, -0.15, 'Meta-loop: outputs become training data\nfor next policy iteration',
    fontsize=8, ha='center', color=C_ALERT, style='italic')

# Title
ax.text(5.0, 6.7, 'Figure 1. POMDP sketch of the self-evolving AI feedback loop',
    fontsize=10, ha='center', fontweight='bold')
ax.text(5.0, 6.3, 'The agent observes only administrative state; clinical state remains hidden.\n'
    'The reward asymmetry creates a structural gradient toward administrative optimisation.',
    fontsize=8, ha='center', color=C_NEUTRAL)

plt.savefig(OUTPUT_DIR / "P2_Figure1_POMDP.png", facecolor='white')
plt.savefig(OUTPUT_DIR / "P2_Figure1_POMDP.pdf", facecolor='white')
plt.close()
print("  Saved P2_Figure1_POMDP.png/pdf")


# ============================================================
# FIGURE 2: D(C) Divergence Bar Chart
# ============================================================
print("Generating Figure 2: D(C) Divergence...")

conditions = ['Diabetes', 'Hypertension', 'Obesity', 'Hyperlipidemia', 'Prediabetes']
p_admin = [0.4211, 0.2267, 0.4729, 0.0986, 0.3735]
p_clinical = [0.0434, 0.2505, 0.3715, 0.1391, 0.3320]
d_c = [0.3777, -0.0238, 0.1014, -0.0404, 0.0415]

fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), gridspec_kw={'width_ratios': [3, 2]})

# Panel A: Paired bar chart
ax = axes[0]
x = np.arange(len(conditions))
width = 0.35
bars_admin = ax.bar(x - width/2, p_admin, width, label=r'$P_a(C)$ Administrative', color=C_ADMIN, alpha=0.85, edgecolor='white', linewidth=0.5)
bars_clin = ax.bar(x + width/2, p_clinical, width, label=r'$P_c(C)$ Clinical', color=C_CLINICAL, alpha=0.85, edgecolor='white', linewidth=0.5)
ax.set_ylabel('Prevalence', fontsize=11)
ax.set_xticks(x)
ax.set_xticklabels(conditions, fontsize=9, rotation=25, ha='right')
ax.legend(fontsize=9, frameon=False)
ax.set_title('A. Administrative vs. clinical prevalence', fontsize=10, fontweight='bold', loc='left')
ax.set_ylim(0, 0.55)

# Panel B: D(C) waterfall
ax2 = axes[1]
colors = [C_ADMIN if d > 0 else C_CLINICAL for d in d_c]
bars = ax2.barh(conditions, d_c, color=colors, alpha=0.85, edgecolor='white', linewidth=0.5)
ax2.axvline(0, color='black', linewidth=0.8)
ax2.set_xlabel('D(C) = $P_a(C)$ - $P_c(C)$', fontsize=10)
ax2.set_title('B. Artificial epidemiology divergence', fontsize=10, fontweight='bold', loc='left')

# Annotate values
for i, (bar, val) in enumerate(zip(bars, d_c)):
    x_pos = val + 0.01 if val > 0 else val - 0.01
    ha = 'left' if val > 0 else 'right'
    ax2.text(x_pos, i, f'{val:+.3f}', va='center', ha=ha, fontsize=9, fontweight='bold')

# Labels
ax2.text(0.25, -0.8, 'Over-coded', fontsize=8, ha='center', color=C_ADMIN, style='italic')
ax2.text(-0.03, -0.8, 'Under-coded', fontsize=8, ha='center', color=C_CLINICAL, style='italic')

plt.tight_layout()
fig.text(0.5, -0.04,
    'Figure 2. D(C) divergence for five sentinel conditions (Synthea synthetic EHR, n = 11,475).\n'
    'Positive D(C) indicates administrative over-representation; negative indicates under-coding.',
    fontsize=8, ha='center', color=C_NEUTRAL)

plt.savefig(OUTPUT_DIR / "P2_Figure2_DC_Divergence.png", facecolor='white')
plt.savefig(OUTPUT_DIR / "P2_Figure2_DC_Divergence.pdf", facecolor='white')
plt.close()
print("  Saved P2_Figure2_DC_Divergence.png/pdf")


# ============================================================
# FIGURE 3: Reification Feedback Loop Amplification
# ============================================================
print("Generating Figure 3: Feedback Loop Amplification...")

cycles = [1, 2, 3, 4, 5]

# From Tier 2 governance simulation results
clinical_first = [0.022, 0.028, 0.033, 0.038, 0.043]
equilibrium = [0.002, 0.008, 0.018, 0.030, 0.040]
business_first = [0.005, 0.020, 0.042, 0.068, 0.093]

fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), gridspec_kw={'width_ratios': [3, 2]})

# Panel A: JSD trajectory
ax = axes[0]
ax.plot(cycles, clinical_first, 'o-', color=C_SAFE, linewidth=2.5, markersize=7, label='Clinical-first (0.8/0.2)')
ax.plot(cycles, equilibrium, 's-', color=C_WARN, linewidth=2.5, markersize=7, label='Equilibrium (0.5/0.5)')
ax.plot(cycles, business_first, '^-', color=C_ALERT, linewidth=2.5, markersize=7, label='Business-first (0.2/0.8)')
ax.set_xlabel('Feedback cycle', fontsize=11)
ax.set_ylabel('Jensen-Shannon divergence', fontsize=11)
ax.set_title('A. Coding distortion over iterative cycles', fontsize=10, fontweight='bold', loc='left')
ax.legend(fontsize=9, frameon=False, loc='upper left')
ax.set_xticks(cycles)
ax.set_ylim(0, 0.105)

# Shaded danger zone
ax.axhspan(0.05, 0.105, alpha=0.08, color=C_ALERT)
ax.text(1.1, 0.095, 'High distortion zone', fontsize=7, color=C_ALERT, style='italic')

# Panel B: Amplification factor
ax2 = axes[1]
amplifications = {
    'Clinical-first': 0.043 / 0.022,
    'Equilibrium': 0.040 / 0.002,
    'Business-first': 0.093 / 0.005,
}
names = list(amplifications.keys())
values = list(amplifications.values())
colors = [C_SAFE, C_WARN, C_ALERT]

bars = ax2.barh(names, values, color=colors, alpha=0.85, edgecolor='white', linewidth=0.5)
ax2.set_xlabel('Amplification factor (Cycle 5 / Cycle 1)', fontsize=10)
ax2.set_title('B. Cumulative amplification', fontsize=10, fontweight='bold', loc='left')

for bar, val in zip(bars, values):
    ax2.text(val + 0.3, bar.get_y() + bar.get_height()/2, f'{val:.1f}x',
        va='center', fontsize=10, fontweight='bold')

ax2.set_xlim(0, 25)

plt.tight_layout()
fig.text(0.5, -0.06,
    'Figure 3. Reification feedback loop amplification under three governance scenarios.\n'
    'Equilibrium governance (0.5/0.5) shows 21x amplification despite low initial distortion,\n'
    'demonstrating that apparent single-cycle stability does not predict long-term trajectory.',
    fontsize=8, ha='center', color=C_NEUTRAL)

plt.savefig(OUTPUT_DIR / "P2_Figure3_Amplification.png", facecolor='white')
plt.savefig(OUTPUT_DIR / "P2_Figure3_Amplification.pdf", facecolor='white')
plt.close()
print("  Saved P2_Figure3_Amplification.png/pdf")

print("\nP2 figures complete.")
