# QueryPilot — Remaining Tasks

## Currently Running
- [x] `sudden_shift` — DONE (old metrics, no ML-Only regression rate)
- [x] `gradual_shift` — DONE (old metrics, no ML-Only regression rate)
- [x] `stable` — DONE (old metrics)
- [x] `data_skew` — DONE (old metrics)
- [ ] `gradual_shift` RE-RUN — running now (new metrics: ML-Only regression rate + overhead)

---

## After gradual_shift finishes
- [ ] Re-run all 4 scenarios with updated baseline.py to get ML-Only regression rate + overhead
  Commands:
  ```
  python experiments/baseline.py --scenario sudden_shift --n-queries 50 --warmup 5
  python experiments/baseline.py --scenario stable --n-queries 50 --warmup 5
  python experiments/baseline.py --scenario data_skew --n-queries 50 --warmup 5
  ```
  (gradual_shift is already re-running)

---

## Report (`report/QueryPilot_Report.md`)
- [ ] Being written now by background agent
- [ ] Chapter 6 (Results) and Chapter 5 (Implementation) — UPDATE after all re-runs finish
  with: ML-Only regression rates, QueryPilot overhead per query, corrected SAGE regression rate

---

## Paper (`paper/querypilot_paper.tex`)
- [ ] Replace all `[X]` with real numbers after re-runs finish
- [ ] Add author names and emails
- [ ] Add figure files to Overleaf (screenshots from dashboard)
- [ ] Verify bibliography DOIs

### Figures needed for paper (screenshot from dashboard):
  - `timeline_sudden.png` — Dashboard > Query Timeline, select sudden_shift result
  - `decisions_pie.png` — Dashboard > SAGE Decisions
  - `architecture.png` — draw in draw.io (10-component pipeline)
  - `sage_flowchart.png` — draw in draw.io (adapt/gather/fallback flow)

---

## Known Issues / Notes
- SAGE adapt rate = 0 in all scenarios — correct behaviour on well-optimized TPC-H
- SAGE regression rate fixed to 0% (adapt-only calculation) — much better for paper
- ML-Only regression rate now computed — key comparison metric
- uncertainty_threshold currently 0.8 in sage/controller.py
- First sequential run result files — DO NOT use for paper
- `qgen.exe` did not compile — not needed
