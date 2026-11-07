# QueryPilot — Remaining Tasks

## Code & Experiments — COMPLETE ✅
All 4 scenarios run with final metrics (ML-Only regression rate + overhead):

| Scenario | SAGE Regression | ML-Only Regression | Overhead |
|---|---|---|---|
| stable | 0.0% | 14.0% | 3.21ms |
| sudden_shift | 0.0% | 10.0% | 5.86ms |
| gradual_shift | 0.0% | 14.0% | 4.07ms |
| data_skew | 0.0% | 0.0% | 3.88ms |

---

## Paper (`paper/querypilot_paper.tex`) — CONTENT COMPLETE ✅
- [x] All real numbers filled in
- [x] Author names added (Nitish M, Padmesh V A, Dr. V. Sabaresan, Mohamed Hussain)
- [x] Tables split/resized — no more layout clashes
- [x] Citations verified (all 9 references checked)
- [x] Code/paper alignment verified (n_min=10, τ_u=0.8, λ=25, δ=0.005)

### Still needed (manual — Overleaf):
- [ ] Upload `timeline_sudden.png` — screenshot already taken
- [ ] Upload `decisions_pie.png` — screenshot already taken
- [ ] Draw `architecture.png` in draw.io → upload
- [ ] Draw `sage_flowchart.png` in draw.io → upload
- [ ] Final compile check in Overleaf

---

## Report (`report/QueryPilot_Report.md`) — CONTENT COMPLETE ✅
All 7 chapters written (~5,800 words), abbreviations list added.

### Still needed (manual — Word):
- [ ] Copy markdown content into Word document
- [ ] Format per spec: Times New Roman 14, top 30-35mm, bottom 25-30mm, left 35-40mm, right 20-25mm, 1.5 line spacing
- [ ] Insert figures at placeholder spots (Figure 3.1, 4.1, 6.1, 6.2, 6.3, 6.4)

---

## Git
- [ ] Commit everything to GitHub

---

## Draw.io Diagrams — Quick Reference

**architecture.png** — 10-box pipeline (left to right):
SQL Input → Workload Collector → Feature Extractor → Candidate Generator → Performance Model → Uncertainty Estimator → Drift Detector → SAGE Controller → Execution Layer → MySQL → Feedback Collector → Dashboard

**sage_flowchart.png** — decision flow (top to bottom):
Receive Query → [Model trained AND queries≥10?] NO→Gather Evidence / YES↓ → [Drift detected?] YES→Fallback / NO↓ → [Candidate passes uncertainty+regression filters?] NO→Fallback / YES→Adapt → Record time, update detector, retrain model
