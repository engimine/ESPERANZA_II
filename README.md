# ESPERANZA II — crew-time-constrained bioregenerative food system for a 15-crew, 500-sol Mars surface mission

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22713680.svg)](https://doi.org/10.5281/zenodo.22713680)
[![Preprint](https://img.shields.io/badge/preprint-v1%20(PDF)-c1440e)](https://esperanzaresearch.com/paper.pdf)
[![Project site](https://img.shields.io/badge/project-esperanzaresearch.com-222)](https://esperanzaresearch.com)
[![License: CC BY 4.0](https://img.shields.io/badge/docs%20%26%20data-CC%20BY%204.0-lightgrey)](LICENSE-CC-BY-4.0.md)
[![License: MIT](https://img.shields.io/badge/scripts-MIT-lightgrey)](LICENSE)

Open post-challenge release of the ESPERANZA II design (NASA Mars to Table Challenge 2026, solo entry, submitted 11 August 2026, not selected as finalist). Everything needed to check the numbers is here: the delivered meal-plan workbooks, the scripts that recompute crew time and Earth-provisioned energy from them, and the preprint.

**Paper (preprint v1, 18 pp.):** *Crew time as the binding constraint of a bioregenerative food system for a fifteen-person, 500-sol Mars surface mission: design reconciliation and a 14-sol meal plan* — [PDF](paper/Puerta_Angulo_2026_ESPERANZA_II_crew_time_preprint_v1.pdf) · [web](https://esperanzaresearch.com/paper.pdf) · 89-second [trailer](https://esperanzaresearch.com/#trailer).

**Open to collaboration** — space agencies, universities, labs, chefs, engineers: mariajesuspuertaangulo@gmail.com · https://www.mariajesuspuertaangulo.com

## Layout
```
paper/                   preprint PDF + LaTeX source + references.bib
data/                    2.1 meal schedule, 2.2 meal lifecycle (as submitted), results.json, per_sol.csv
scripts/                 01_recompute_from_deliverables.py, 02_figures.py
figures/                 paper figures (PDF)
submitted_deliverables/  Solution Summary, ConOps + appendix, Design Layout (as submitted)
```

**Author:** María Jesús Puerta Angulo (independent researcher, Tarragona, Spain) · **Version:** v1, September 2026

## Contents
| File | What it is |
|---|---|
| `Puerta_Angulo_2026_ESPERANZA_II_crew_time_preprint_v1.pdf` | Paper, preprint v1 |
| `2.1_MealPlan_Schedule_2026-08-06.xlsx` | 14-sol meal schedule (78 meals, per-meal nutrition) as submitted |
| `2.2_MealPlan_Lifecycle_2026-08-06.xlsx` | Meal lifecycle plan (1,004 ingredient lines with source, mass, prep/cook/clean times) + per-ingredient energy audit + crew-time basis of estimate, as submitted |
| `01_recompute_from_deliverables.py` | Recomputes per-sol galley hours, rolling 5-sol windows, partition by production method and Earth-provisioned energy fraction from the two workbooks. Output: `results.json`, `per_sol.csv` |
| `02_figures.py` | Generates the paper figures from `results.json` and stated design constants |
| `results.json`, `per_sol.csv` | Outputs of the above (deterministic) |
| `1.2_SolutionSummary_FINAL_2026-08-08d.pdf` | Solution Summary as submitted |
| `3.1_ConOps_FINAL_2026-08-07.pdf`, `3.2_ConOps_Appendix_2026-08-08c.pdf` | Concept of Operations and its basis-of-estimate appendix as submitted |
| `4_DesignLayout_2026-08-07h.pdf` | Design layout as submitted |

## Reproduce
```
pip install openpyxl matplotlib numpy
python 01_recompute_from_deliverables.py   # reads ../data/*.xlsx
python 02_figures.py
```
Expected: galley mean 15.40 h/sol (peak 19.03 sol 3, minimum 13.35 sol 6), 76.98 h per 5-sol cycle, worst window 80.27 h (sols 10–14); Earth-provisioned 41.21 % of menu energy (per-sol 32.96–47.14 %).

## Known errata in the submitted documents
- Solution Summary §4 cites "NASA-STD-3001 Vol.2 Sec. 6.4" for fire safety; the correct section is 9.8.2 (6.4 covers environmental hazards).
- The iron content of the delivered rotation (20 mg/sol) exceeds the NASA-STD-3001 spaceflight ceiling (8–10 mg/sol); this is declared as an open non-conformance in the paper.

## Citation
Puerta Angulo, M.J. (2026). ESPERANZA II: crew-time-constrained bioregenerative food system for a 500-sol Mars surface mission — design package, 14-sol meal plan workbooks and reconciliation scripts. Zenodo. DOI: https://doi.org/10.5281/zenodo.22713680
