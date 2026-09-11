"""Recompute per-sol series from the submitted 14-sol Meal Plan workbooks.

Inputs (read-only, the files uploaded to the NASA Mars to Table portal on 2026-08-11):
  2.1_MealPlan_Schedule_2026-08-06.xlsx   (sheet 'Daily Meal Schedule')
  2.2_MealPlan_Lifecycle_2026-08-06.xlsx  (sheets 'Meal Lifecycle Plan', 'Ingredient Energy Audit')

Outputs: results.json + per-sol CSV tables in this folder.
Every number in the paper's Results tables that is labelled 'recomputed' comes from here.
"""
import json, re, sys, os
from collections import defaultdict
import openpyxl

_HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(_HERE, "..", "data")   # copies of the submitted workbooks (MD5 in data/README.md)
F21 = os.path.join(D, "2.1_MealPlan_Schedule_2026-08-06.xlsx")
F22 = os.path.join(D, "2.2_MealPlan_Lifecycle_2026-08-06.xlsx")
OUT = os.path.dirname(os.path.abspath(__file__))
NSOL = 14
BUDGET_H = 90.0          # two specialists x 45 h per 5-sol week (Rules, Appendix B)
NONGALLEY_H = 49.0       # specialist non-galley duties per 5-sol cycle (Deliverable 3.2, Sec. 5)
ROTA_H = 48.9            # galley share carried by the all-crew cooking rotation per cycle (Deliverable 3.2)

def parse_sols(v):
    s = str(v)
    out = set()
    for part in re.split(r"[,;/&]|and", s):
        part = part.strip()
        m = re.match(r"^(\d+)\s*[-–]\s*(\d+)$", part)
        if m:
            out.update(range(int(m.group(1)), int(m.group(2)) + 1))
        else:
            m = re.search(r"\d+", part)
            if m:
                out.add(int(m.group(0)))
    return sorted(x for x in out if 1 <= x <= NSOL)

def num(v):
    if v is None: return 0.0
    if isinstance(v, (int, float)): return float(v)
    m = re.search(r"[-+]?\d*\.?\d+", str(v).replace(",", ""))
    return float(m.group(0)) if m else 0.0

def parse_amount(v):
    """Return (value, unit) with unit in {'g','ml',None}."""
    s = str(v).strip().lower()
    m = re.search(r"([-+]?\d*\.?\d+)\s*(g|ml|l|kg)?", s)
    if not m: return 0.0, None
    val = float(m.group(1)); u = m.group(2)
    if u == "kg": return val * 1000, "g"
    if u == "l": return val * 1000, "ml"
    return val, u

# ---------------------------------------------------------------- 2.1 schedule
wb = openpyxl.load_workbook(F21, data_only=True)
ws = wb["Daily Meal Schedule"]
rows = list(ws.iter_rows(values_only=True))
hi = next(i for i, r in enumerate(rows[:15]) if r and any(str(c).strip() == "Meal ID" for c in r if c))
hdr = [str(c).strip() if c else "" for c in rows[hi]]; rows = rows[hi:]
ci = {h: i for i, h in enumerate(hdr)}
kcal_sol = defaultdict(float); meals_sol = defaultdict(int); meal_ids = set()
prot = defaultdict(float); fibre = defaultdict(float); sodium = defaultdict(float)
for r in rows[1:]:
    if r[ci["Sol"]] is None or r[ci["Meal ID"]] is None: continue
    try: sol = int(num(r[ci["Sol"]]))
    except: continue
    if not (1 <= sol <= NSOL): continue
    kcal_sol[sol] += num(r[ci["Calories per Serving"]])
    prot[sol] += num(r[ci["Protein (g)"]]); fibre[sol] += num(r[ci["Fiber (g)"]]); sodium[sol] += num(r[ci["Sodium (mg)"]])
    meals_sol[sol] += 1; meal_ids.add(str(r[ci["Meal ID"]]).strip())

# ---------------------------------------------------------------- 2.2 lifecycle
wb2 = openpyxl.load_workbook(F22, data_only=True)
# energy audit: label -> (kcal/g, source, confidence)
wa = wb2["Ingredient Energy Audit"]
audit = {}
for r in wa.iter_rows(values_only=True):
    if r and r[0] and r[1] in ("In-situ", "Earth-provisioned") and isinstance(r[4], (int, float)):
        audit[str(r[0]).strip().lower()] = (float(r[4]), r[1], r[7])
wl = wb2["Meal Lifecycle Plan"]
rows = list(wl.iter_rows(values_only=True))
hi = next(i for i, r in enumerate(rows[:15]) if r and any(str(c).strip() == "Meal ID" for c in r if c))
hdr = [str(c).strip() if c else "" for c in rows[hi]]; rows = rows[hi:]
ci = {h: i for i, h in enumerate(hdr)}
prep_sol = defaultdict(float); cook_sol = defaultdict(float); clean_sol = defaultdict(float)
kcal_src_sol = defaultdict(lambda: defaultdict(float))
n_lines = 0; unmatched = defaultdict(float); lines_per_sol = defaultdict(int)
class_sol = {"insitu_processing": defaultdict(float), "crop_preparation": defaultdict(float), "earth_stock": defaultdict(float)}
mass_src = defaultdict(float)
for r in rows[1:]:
    if not r[ci["Meal ID"]] or not r[ci["Ingredient Name"]]: continue
    n_lines += 1
    sols = parse_sols(r[ci["Sol Day(s) Served"]])
    p, c, k = num(r[ci["Prep Time (min)"]]), num(r[ci["Cook Time (min)"]]), num(r[ci["Cleaning Time (min)"]])
    name = str(r[ci["Ingredient Name"]]).strip().lower()
    src_raw = str(r[ci["Ingredient Source"]] or "")
    src = "Earth-provisioned" if "earth" in src_raw.lower() else ("In-situ" if "in-situ" in src_raw.lower() or "in situ" in src_raw.lower() else "Other")
    val, unit = parse_amount(r[ci["Amount Required (g or mL)"]])
    grams = val * (0.92 if (unit == "ml" and "oil" in name) else 1.0)
    dens = audit.get(name)
    # M2: classify the line by production method (in-situ processing modules vs crop preparation vs Earth stock)
    method = str(r[ci["Production Method"]] or "").lower()
    if any(w in method for w in ("fermentlab", "insect", "mushroom", "soy processing", "photobioreactor")):
        cls = "insitu_processing"
    elif src == "Earth-provisioned" or "pre-packaged" in method:
        cls = "earth_stock"
    else:
        cls = "crop_preparation"
    for s in sols:
        lines_per_sol[s] += 1
        prep_sol[s] += p; cook_sol[s] += c; clean_sol[s] += k
        class_sol[cls][s] += (p + c + k) / 60.0
        if dens:
            kcal_src_sol[s][dens[1]] += grams * dens[0]
        else:
            unmatched[name] += grams
    mass_src[src] += grams * len(sols)

sols = list(range(1, NSOL + 1))
galley_h = {s: (prep_sol[s] + cook_sol[s] + clean_sol[s]) / 60.0 for s in sols}
mean_galley = sum(galley_h.values()) / NSOL
peak_sol = max(sols, key=lambda s: galley_h[s]); min_sol = min(sols, key=lambda s: galley_h[s])

# rolling 5-sol windows on the cyclic 14-sol rotation (10 distinct windows: starts 1..10)
windows = []
for start in range(1, 11):
    w = [galley_h[s] for s in range(start, start + 5)]
    tot = sum(w)
    spec = tot - ROTA_H * (tot / (mean_galley * 5)) + NONGALLEY_H  # rota share scaled to window load
    windows.append({"start": start, "galley_all_crew_h": round(tot, 2), "specialist_h_est": round(spec, 2)})
worst = max(windows, key=lambda w: w["galley_all_crew_h"])

# M2: specialist load lower bound = in-situ processing (module lines) + non-galley duties, on rolling windows
proc = [class_sol["insitu_processing"][s] for s in sols]
proc_windows = [sum(proc[st - 1:st + 4]) for st in range(1, 11)]
m2 = {
    "class_h_per_cycle": {k: round(sum(v.values()) / NSOL * 5, 2) for k, v in class_sol.items()},
    "insitu_processing_h_per_sol": {s: round(class_sol["insitu_processing"][s], 2) for s in sols},
    "insitu_processing_worst_window_h": round(max(proc_windows), 2),
    "specialist_worst_window_recomputed_h": round(max(proc_windows) + NONGALLEY_H, 2),
    "specialist_mean_recomputed_h": round(sum(proc) / NSOL * 5 + NONGALLEY_H, 2),
    "note": "module-based classification excludes grain milling (booked under crop preparation in the workbook); design allocation retains 28.1 h/cycle and gives 81.2 h worst window",
}

ep_sol = {}
for s in sols:
    e = kcal_src_sol[s]["Earth-provisioned"]; i = kcal_src_sol[s]["In-situ"]
    ep_sol[s] = e / (e + i) if (e + i) else float("nan")
tot_e = sum(kcal_src_sol[s]["Earth-provisioned"] for s in sols); tot_i = sum(kcal_src_sol[s]["In-situ"] for s in sols)

res = {
    "n_meal_rows_2_1": sum(meals_sol.values()), "unique_meal_ids_2_1": len(meal_ids),
    "n_ingredient_lines_2_2": n_lines, "audit_labels": len(audit),
    "unmatched_labels_mass_g": {k: round(v, 1) for k, v in sorted(unmatched.items(), key=lambda kv: -kv[1])[:15]},
    "unmatched_total_g": round(sum(unmatched.values()), 1),
    "kcal_per_sol": {s: round(kcal_sol[s], 1) for s in sols},
    "kcal_mean": round(sum(kcal_sol.values()) / NSOL, 1), "kcal_min": round(min(kcal_sol.values()), 1), "kcal_max": round(max(kcal_sol.values()), 1),
    "protein_mean_g": round(sum(prot.values()) / NSOL, 1), "fibre_mean_g": round(sum(fibre.values()) / NSOL, 1), "sodium_mean_mg": round(sum(sodium.values()) / NSOL, 1),
    "galley_h_per_sol": {s: round(galley_h[s], 2) for s in sols},
    "galley_components_h": {"prep": round(sum(prep_sol.values()) / 60 / NSOL, 2), "cook": round(sum(cook_sol.values()) / 60 / NSOL, 2), "clean": round(sum(clean_sol.values()) / 60 / NSOL, 2)},
    "galley_mean_h": round(mean_galley, 2), "galley_peak": [peak_sol, round(galley_h[peak_sol], 2)], "galley_min": [min_sol, round(galley_h[min_sol], 2)],
    "galley_per_5sol_cycle_h": round(mean_galley * 5, 2),
    "windows": windows, "worst_window": worst, "m2_specialist_split": m2,
    "earth_provisioned_kcal_14sol": round(tot_e, 0), "insitu_kcal_14sol": round(tot_i, 0),
    "earth_provisioned_fraction_menu": round(tot_e / (tot_e + tot_i), 4),
    "earth_provisioned_fraction_per_sol": {s: round(ep_sol[s], 4) for s in sols},
    "ep_min": round(min(ep_sol.values()), 4), "ep_max": round(max(ep_sol.values()), 4),
    "menu_kcal_per_sol_from_audit": round((tot_e + tot_i) / NSOL, 1),
}
json.dump(res, open(os.path.join(OUT, "results.json"), "w"), indent=1)
with open(os.path.join(OUT, "per_sol.csv"), "w") as f:
    f.write("sol,kcal_2_1,galley_h,prep_h,cook_h,clean_h,earth_fraction\n")
    for s in sols:
        f.write(f"{s},{kcal_sol[s]:.1f},{galley_h[s]:.2f},{prep_sol[s]/60:.2f},{cook_sol[s]/60:.2f},{clean_sol[s]/60:.2f},{ep_sol[s]:.4f}\n")
print(json.dumps({k: v for k, v in res.items() if k not in ("kcal_per_sol", "galley_h_per_sol", "earth_provisioned_fraction_per_sol", "windows")}, indent=1))
print("galley_h_per_sol", res["galley_h_per_sol"]); print("ep_per_sol", res["earth_provisioned_fraction_per_sol"]); print("kcal", res["kcal_per_sol"])
