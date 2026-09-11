"""Publication figures for the ESPERANZA II paper. Reads results.json (from 01_recompute_from_deliverables.py)
and the design-document constants stated in Deliverable 3.2 (ConOps Appendix) for the lighting and EVA panels."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)
R = json.load(open(os.path.join(HERE, "results.json")))

# palette (validated with the dataviz validator; categorical, fixed order)
BLUE, RED, TEAL, AMBER = PALETTE = ["#2f6db5", "#d1495b", "#1a9c8a", "#b8791a"]  # validated order
C1, C2, C3, C4 = BLUE, RED, TEAL, AMBER
INK, MUTED, GRID = "#1f1f1f", "#5f5f5f", "#e3e3e3"
plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "legend.frameon": False, "figure.dpi": 200, "savefig.dpi": 300})

def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"), bbox_inches="tight")
    plt.close(fig)

# ------------------------------------------------------------------ Figure 1: LED load over one sol
# Zone table from Deliverable 3.2 Sec. 1.1 (instantaneous kW when lit; photoperiod hours on / off; sol = 24.66 h)
SOL_H = 24.66
zones = [("Wheat (150 m2, 24/0)", 13.52, (0.0, SOL_H)),
         ("Soybean (80 m2, 12.33/12.33)", 13.22, (0.0, 12.33)),
         ("Potato (80 m2, opposite window)", 12.02, (12.33, 24.66)),
         ("Tomato, pepper, greens (63 m2, 16/8)", 6.55, (4.0, 20.0))]
t = np.linspace(0, SOL_H, 2467)
load = np.zeros((len(zones), t.size))
for i, (_, kw, (a, b)) in enumerate(zones):
    load[i] = np.where((t >= a) & (t < b), kw, 0.0)
tot = load.sum(0)
fig, ax = plt.subplots(figsize=(6.4, 3.0))
ax.stackplot(t, load, colors=[C1, C2, C3, C4], labels=[z[0] for z in zones], alpha=0.9, linewidth=0)
ax.axhline(tot.mean(), color=INK, lw=1.0, ls="--")
ax.text(SOL_H - 0.2, tot.mean() + 0.6, f"mean {tot.mean():.1f} kW", ha="right", va="bottom", fontsize=8, color=INK)
ax.text(SOL_H - 0.2, tot.max() + 0.6, f"peak {tot.max():.1f} kW", ha="right", va="bottom", fontsize=8, color=INK)
ax.set_xlim(0, SOL_H); ax.set_ylim(0, 40); ax.set_xlabel("Time in sol (h)"); ax.set_ylabel("Canopy LED electrical load (kW)")
ax.legend(loc="lower left", fontsize=7.5, ncol=2)
save(fig, "fig1_led_photoperiod")
print("fig1: mean %.2f peak %.2f" % (tot.mean(), tot.max()))

# ------------------------------------------------------------------ Figure 2: galley hours per sol + rolling windows
sols = np.arange(1, 15)
g = np.array([R["galley_h_per_sol"][str(s)] for s in sols])
comp = R["galley_components_h"]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw={"width_ratios": [1.35, 1]})
a1.bar(sols, g, color=C1, width=0.72, linewidth=0)
a1.axhline(g.mean(), color=INK, ls="--", lw=1.0)
a1.text(14.4, g.mean() + 0.25, f"mean {g.mean():.2f} h/sol", ha="right", fontsize=8)
for s in (3, 6, 13):
    a1.text(s, g[s - 1] + 0.25, f"{g[s-1]:.2f}", ha="center", fontsize=7.5, color=INK)
a1.set_xticks(sols); a1.set_xlabel("Sol of the 14-sol rotation"); a1.set_ylabel("Galley labour, all crew (h/sol)")
a1.set_ylim(0, 21)
w = R["windows"]; starts = [x["start"] for x in w]; tot5 = [x["galley_all_crew_h"] for x in w]
a2.bar(starts, tot5, color=TEAL, width=0.72, linewidth=0)
a2.axhline(90, color=C2, lw=1.2); a2.text(10.4, 90.8, "budget 90 h (2 x 45 h)", ha="right", fontsize=8, color=C2)
a2.set_xticks(starts); a2.set_xlabel("First sol of 5-sol window"); a2.set_ylabel("Galley labour per window (h)")
a2.set_ylim(0, 100)
save(fig, "fig2_crew_time")

# ------------------------------------------------------------------ Figure 3: Earth-provisioned fraction per sol + EVA sensitivity
ep = np.array([R["earth_provisioned_fraction_per_sol"][str(s)] for s in sols]) * 100
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.9))
a1.bar(sols, ep, color=AMBER, width=0.72, linewidth=0)
a1.axhline(50, color=C2, lw=1.2); a1.text(14.4, 50.8, "Rules cap 50 %", ha="right", fontsize=8, color=C2)
a1.axhline(R["earth_provisioned_fraction_menu"] * 100, color=INK, ls="--", lw=1.0)
a1.text(0.6, 56.5, f"dashed: 14-sol mean {R['earth_provisioned_fraction_menu']*100:.1f} %", fontsize=8)
a1.set_xticks(sols); a1.set_xlabel("Sol of the 14-sol rotation"); a1.set_ylabel("Earth-provisioned energy (% of kcal)")
a1.set_ylim(0, 60)
# EVA sensitivity: Deliverable 3.2 Sec. 9 (baseline 47.0 % nameplate basis; 200 kcal per crew-EVA-hour)
eva = np.array([0, 4, 8, 12, 13.8, 16, 24]); base_e, base_tot = 21384.0, 45525.0
sup = eva * 200
from_earth = (base_e + sup) / (base_tot + sup) * 100
in_situ = base_e / (base_tot + sup) * 100
a2.plot(eva, from_earth, color=C2, lw=2, marker="o", ms=4, label="Supplement shipped from Earth")
a2.plot(eva, in_situ, color=TEAL, lw=2, marker="o", ms=4, label="Supplement produced in situ")
a2.axhline(50, color=C2, lw=1.0, ls=":")
a2.axvline(8, color=MUTED, lw=0.8, ls=":"); a2.text(8.2, 41.2, "nominal 8 h", fontsize=7.5, color=MUTED)
a2.set_xlabel("Crew EVA hours per sol"); a2.set_ylabel("Earth-provisioned energy (% of kcal)")
a2.set_ylim(40, 54); a2.legend(fontsize=7.5, loc="upper left")
save(fig, "fig3_earth_fraction")
print("fig3 eva rows:", [(float(e), round(a, 2), round(b, 2)) for e, a, b in zip(eva, from_earth, in_situ)])

# ------------------------------------------------------------------ Figure 4: carbon and oxygen ledger (kg/sol), Deliverable 3.2 Sec. 3
fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.7), gridspec_kw={"wspace": 0.75})
src = [("Crew respiration", 15.4), ("Fermentation, compost,\nheterotrophs", 2.8), ("Martian atmosphere\n(net of buffer)", 2.5)]
snk = [("Crops, 373 m2", 13.5), ("Spirulina PBR, 40 m2", 7.2)]
a1.barh([s[0] for s in src], [s[1] for s in src], color=C1, height=0.6, linewidth=0)
a1.barh([s[0] for s in snk], [s[1] for s in snk], color=TEAL, height=0.6, linewidth=0)
for lab, v in src + snk:
    a1.text(v + 0.2, lab, f"{v:.1f}", va="center", fontsize=8)
a1.set_xlabel("CO$_2$ (kg/sol)"); a1.set_xlim(0, 19); a1.invert_yaxis()
a1.set_title("CO$_2$: sources (blue), sinks (teal); 20.7 kg/sol fixed", fontsize=8, loc="left")
o2 = [("Crops", 9.82), ("Spirulina PBR", 5.20), ("Crew demand", -12.95)]
a2.barh([o[0] for o in o2], [abs(o[1]) for o in o2], color=[TEAL, TEAL, BLUE], height=0.6, linewidth=0)
for lab, v in o2:
    a2.text(abs(v) + 0.2, lab, f"{abs(v):.2f}", va="center", fontsize=8)
a2.set_xlabel("O$_2$ (kg/sol)"); a2.set_xlim(0, 16); a2.invert_yaxis()
a2.set_title("O$_2$: 15.02 released vs 12.95 demand (116 %)", fontsize=8, loc="left")
save(fig, "fig4_gas_ledger")
print("done")
