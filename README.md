# QueryPilot

An uncertainty-aware, self-adaptive query optimization framework for MySQL. QueryPilot intercepts SQL queries, learns from observed execution performance, detects workload drift, and uses SAGE (Stability-Aware Guarded Execution) to make bounded-risk optimization decisions.

## What it does

- Extracts query features using MySQL's EXPLAIN output
- Generates candidate query variants using optimizer hints (NO_INDEX, HASH_JOIN, NO_BKA)
- Predicts candidate performance using a 3-model ensemble (Linear Regression, Random Forest, Gradient Boosting)
- Estimates prediction uncertainty via ensemble disagreement
- Detects workload drift using the Page-Hinkley sequential change-point test
- Uses SAGE to decide: **adapt** (apply a hint), **gather_evidence** (collect more data), or **fallback** (use MySQL's native optimizer)
- Logs every decision to CSV and visualizes results in a Streamlit dashboard

---

## Requirements

- Python 3.8+
- MySQL 8.0.18+ (EXPLAIN ANALYZE support required)
- Windows / macOS / Linux

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd QueryPilot
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure database connection

Copy `.env.example` to `.env` and fill in your MySQL credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=querypilot
```

### 5. Create the database

In MySQL Workbench or the MySQL shell:

```sql
CREATE DATABASE IF NOT EXISTS querypilot;
```

### 6. Test the connection

```bash
python main.py
```

Expected output:
```
Connected to MySQL successfully.
MySQL version: 8.0.x
```

---

## Loading TPC-H Data

QueryPilot is evaluated on the TPC-H benchmark (scale factor 1).

### Step 1 — Build the data generator

```bash
cd tpch-dbgen
mingw32-make dbgen.exe    # Windows with MinGW
# or: make dbgen          # macOS / Linux
```

### Step 2 — Generate data (scale factor 1 ≈ 1 GB, ~6M rows in lineitem)

```bash
./dbgen -s 1
cd ..
```

### Step 3 — Create schema and load data

```bash
python database/load_tpch.py
```

This creates all 8 TPC-H tables and loads data. Takes 5–10 minutes.

### Step 4 — Create indexes

Run `database/indexes.sql` in MySQL Workbench:

```sql
source database/indexes.sql
```

---

## Running Experiments

Experiments compare three configurations on the same query workload:
1. **Native MySQL** — queries execute without QueryPilot
2. **ML-Only** — QueryPilot's ML model selects candidates without safety filters
3. **QueryPilot + SAGE** — full system with uncertainty estimation, drift detection, and guarded fallback

### Available scenarios

| Scenario | Description |
|---|---|
| `stable` | Uniform random mix of all query types |
| `sudden_shift` | First 60% scan-heavy, last 40% join-heavy |
| `gradual_shift` | Join-heavy probability increases linearly 0→1 |
| `data_skew` | All Q3 queries, parameter distribution shifts mid-run |

### Run an experiment

```bash
python experiments/baseline.py --scenario stable --n-queries 50 --warmup 5
```

Options:
- `--scenario` — one of `stable`, `sudden_shift`, `gradual_shift`, `data_skew`
- `--n-queries` — number of queries to run (default: 100)
- `--warmup` — warm-up queries to seed buffer pool (default: 10)
- `--seed` — random seed for reproducibility (default: 42)

Results are saved to `results/<scenario>_<n>q_seed<seed>.json`.

### Run all 4 scenarios (sequentially — do NOT run in parallel)

```bash
python experiments/baseline.py --scenario stable --n-queries 50 --warmup 5
python experiments/baseline.py --scenario sudden_shift --n-queries 50 --warmup 5
python experiments/baseline.py --scenario gradual_shift --n-queries 50 --warmup 5
python experiments/baseline.py --scenario data_skew --n-queries 50 --warmup 5
```

> **Important:** Run scenarios one at a time. Parallel runs share the same MySQL instance and corrupt timing measurements.

---

## Dashboard

```bash
streamlit run dashboard/app.py
```

Open `http://localhost:8501` in your browser. The dashboard has 4 pages:

- **Overview** — latency summary table and bar chart per scenario
- **Query Timeline** — execution time over query index, drift events marked
- **SAGE Decisions** — decision distribution pie chart and per-decision table
- **Experiment Comparison** — grouped bar chart across all scenarios

Select a result file from the sidebar to switch between experiments.

---

## Project Structure

```
QueryPilot/
├── database/
│   ├── connection.py          # MySQL connection using .env
│   ├── schema.sql             # TPC-H table definitions
│   ├── indexes.sql            # Index creation
│   └── load_tpch.py           # TPC-H data loader
├── collector/
│   ├── query_executor.py      # Times query execution
│   ├── feature_extractor.py   # EXPLAIN-based feature extraction
│   ├── candidate_generator.py # Optimizer hint injection
│   └── metrics_logger.py      # Logs SAGE decisions to CSV
├── ml/
│   ├── performance_model.py   # 3-model ensemble predictor
│   └── drift_detector.py      # Page-Hinkley drift detection
├── sage/
│   └── controller.py          # SAGE decision controller
├── workload/
│   ├── queries.py             # TPC-H query templates (Q1,Q3,Q5,Q6,Q10)
│   └── generator.py           # 4 workload scenario generators
├── experiments/
│   └── baseline.py            # Interleaved 3-config experiment runner
├── dashboard/
│   └── app.py                 # Streamlit dashboard
├── results/                   # Experiment output JSON files
├── paper/
│   └── querypilot_paper.tex   # IEEE conference paper draft
├── report/
│   └── QueryPilot_Report.md   # Project report
├── tpch-dbgen/                # TPC-H data generator source
├── main.py                    # Connection test + SAGE demo
├── requirements.txt
└── .env                       # Database credentials (not committed)
```

---

## Key Design Decisions

**Why an external Python SDK and not a database proxy?**
A transparent proxy requires implementing MySQL's wire protocol — significant engineering complexity that adds nothing to the research contribution. The SDK approach lets us focus on SAGE's decision logic.

**Why ensemble disagreement for uncertainty?**
It requires no Bayesian inference, adds negligible overhead (~4ms per query), and generalizes to any ensemble of sklearn models.

**Why Page-Hinkley for drift detection?**
Computationally lightweight (O(1) per update, no window storage), suitable for high-frequency query streams, and sensitive to sustained upward shifts in mean execution time.

**Why TPC-H?**
Industry-standard analytical benchmark, widely used in database research, queries involve multi-table joins where optimizer hint choices can matter.

---

## Experimental Methodology Note

Experiments use **interleaved execution**: for each query, all three configurations execute back-to-back before moving to the next query. This controls for MySQL buffer pool warm-up bias — a confound where sequential execution would give later configurations an unfair advantage from cached pages.

---

## Citation

If you use QueryPilot in your research, please cite:

```
[Author 1], [Author 2]. "QueryPilot: An Uncertainty-Aware, Self-Adaptive Query
Optimization Framework for Dynamic Database Workloads." [Conference], [Year].
```
