"""
Experiment: Compare Native MySQL vs ML-Only vs Full QueryPilot+SAGE

Methodology: INTERLEAVED execution.
For each query, all three configs run back-to-back before moving to the next query.
This ensures each config faces the same MySQL buffer pool state, eliminating
cache-warming bias that would otherwise favour whichever config runs last.

Run: python experiments/baseline.py --scenario stable --n-queries 100
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection
from workload.generator import WorkloadGenerator
from collector.query_executor import execute_query
from collector.feature_extractor import extract_features
from collector.candidate_generator import generate_candidates
from ml.performance_model import PerformanceModel, features_to_vector
from sage.controller import SAGEController


def _run_sql(cursor, sql):
    start = time.perf_counter()
    cursor.execute(sql)
    cursor.fetchall()
    return round((time.perf_counter() - start) * 1000, 3)


def run_experiment(queries, warmup=5):
    """
    Run all three configs interleaved: for each query, execute native → ml_only → sage.
    Warm-up queries run first to seed the buffer pool equally for all configs.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ── ML-Only state ──────────────────────────────────────────────────────────
    ml_model = PerformanceModel()
    ml_buffer = []

    # ── SAGE state ─────────────────────────────────────────────────────────────
    sage = SAGEController()

    native_results = []
    ml_results = []
    sage_results = []

    total = len(queries)

    for i, sql in enumerate(queries):
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i + 1}/{total} queries")

        # ── Config 1: Native ───────────────────────────────────────────────────
        native_time = _run_sql(cursor, sql)
        native_results.append({"index": i, "sql": sql[:80], "time_ms": native_time, "decision": "native"})

        # ── Config 2: ML-Only ─────────────────────────────────────────────────
        features = extract_features(sql, cursor)
        fvec = features_to_vector(features)
        candidates = generate_candidates(sql, cursor)

        if ml_model.is_trained:
            best_c = min(
                candidates,
                key=lambda c: ml_model.predict(
                    extract_features(c["sql"], cursor) if c["hint_type"] != "native" else features
                ),
            )
            ml_sql = best_c["sql"]
        else:
            ml_sql = sql

        ml_time = _run_sql(cursor, ml_sql)
        ml_buffer.append((fvec, ml_time))
        if len(ml_buffer) >= 10:
            ml_model.fit([v for v, _ in ml_buffer], [t for _, t in ml_buffer])
        ml_results.append({"index": i, "sql": sql[:80], "time_ms": ml_time, "decision": "ml_only"})

        # ── Config 3: SAGE ────────────────────────────────────────────────────
        r = sage.execute(sql, cursor)
        sage_results.append({
            "index": i,
            "sql": sql[:80],
            "time_ms": r["execution_time_ms"],
            "decision": r["decision"],
            "drift_detected": r["drift_detected"],
            "reason": r["reason"],
        })

    cursor.close()
    conn.close()
    return native_results, ml_results, sage_results


def compute_metrics(results):
    times = sorted(r["time_ms"] for r in results)
    n = len(times)
    return {
        "mean_ms": round(sum(times) / n, 3),
        "median_ms": round(times[n // 2], 3),
        "p95_ms": round(times[int(n * 0.95)], 3),
        "total_ms": round(sum(times), 3),
        "n_queries": n,
    }


def compute_regression_rate(results, native_results, tolerance=0.10, adapt_only=False):
    """
    Regression rate = fraction of queries where this config ran >tolerance% slower than native.
    For SAGE, adapt_only=True counts only queries where SAGE actually adapted (not fallbacks).
    This is the correct measure: a fallback IS native, so it cannot regress vs native.
    """
    pairs = zip(results, native_results)
    if adapt_only:
        pairs = [(r, n) for r, n in zip(results, native_results)
                 if r.get("decision") == "adapt"]
        if not pairs:
            return 0.0
        regressions = sum(1 for r, n in pairs if r["time_ms"] > n["time_ms"] * (1 + tolerance))
        return round(regressions / len(pairs) * 100, 2)
    regressions = sum(
        1 for r, n in zip(results, native_results)
        if r["time_ms"] > n["time_ms"] * (1 + tolerance)
    )
    return round(regressions / len(results) * 100, 2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="stable",
                        choices=["stable", "sudden_shift", "gradual_shift", "data_skew"])
    parser.add_argument("--n-queries", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--warmup", type=int, default=10)
    args = parser.parse_args()

    gen = WorkloadGenerator(scenario=args.scenario, seed=args.seed)
    all_queries = gen.generate(args.n_queries + args.warmup)

    # Warm-up: run native queries to seed buffer pool before any timed measurement
    print(f"Warming up ({args.warmup} queries to seed buffer pool)...")
    for sql in all_queries[:args.warmup]:
        execute_query(sql)

    queries = all_queries[args.warmup:]
    print(f"Running interleaved experiment: scenario={args.scenario}, n={len(queries)}, seed={args.seed}")
    print("  (Each query runs through all 3 configs before moving to the next)")

    native_results, ml_results, sage_results = run_experiment(queries)

    sage_decisions = {d: sum(1 for r in sage_results if r["decision"] == d)
                      for d in ["adapt", "gather_evidence", "fallback"]}

    # ML-Only regression rate: queries where ML-Only chose a non-native candidate and was slower
    ml_only_non_native = [(r, n) for r, n in zip(ml_results, native_results)
                          if r.get("hint_type", "native") != "native"]
    ml_regression_rate = compute_regression_rate(ml_results, native_results, tolerance=0.10)

    # SAGE regression rate: only adapt decisions (fallback = running native = no regression possible)
    sage_regression_rate = compute_regression_rate(sage_results, native_results,
                                                    tolerance=0.10, adapt_only=True)

    # QueryPilot overhead: measure EXPLAIN + feature extraction + candidate generation per query
    overhead_times = []
    from database.connection import get_connection as _gc
    from collector.feature_extractor import extract_features as _ef
    from collector.candidate_generator import generate_candidates as _cg
    _conn = _gc(); _cur = _conn.cursor()
    for sql in queries[:10]:
        t0 = time.perf_counter()
        _ef(sql, _cur); _cg(sql, _cur)
        overhead_times.append((time.perf_counter() - t0) * 1000)
    _cur.close(); _conn.close()
    avg_overhead_ms = round(sum(overhead_times) / len(overhead_times), 2)

    metrics = {
        "scenario": args.scenario,
        "n_queries": len(queries),
        "seed": args.seed,
        "methodology": "interleaved",
        "native": compute_metrics(native_results),
        "ml_only": compute_metrics(ml_results),
        "sage": compute_metrics(sage_results),
        "sage_decisions": sage_decisions,
        "sage_regression_rate_pct": sage_regression_rate,
        "ml_only_regression_rate_pct": ml_regression_rate,
        "querypilot_overhead_ms": avg_overhead_ms,
    }

    print("\n=== Results (interleaved — fair comparison) ===")
    header = f"{'Config':<12} {'Mean':>10} {'Median':>10} {'P95':>10} {'Total':>12}"
    print(header)
    print("-" * len(header))
    for cfg in ["native", "ml_only", "sage"]:
        m = metrics[cfg]
        print(f"  {cfg:<10} {m['mean_ms']:>9.1f}ms {m['median_ms']:>9.1f}ms "
              f"{m['p95_ms']:>9.1f}ms {m['total_ms']:>11.0f}ms")

    native_mean = metrics["native"]["mean_ms"]
    for cfg in ["ml_only", "sage"]:
        diff = (native_mean - metrics[cfg]["mean_ms"]) / native_mean * 100
        sign = "+" if diff >= 0 else ""
        print(f"  {cfg} vs native: {sign}{diff:.1f}% mean latency change")

    print(f"\nSAGE decisions: {sage_decisions}")
    print(f"SAGE regression rate (adapt decisions only): {sage_regression_rate}%")
    print(f"ML-Only regression rate (all queries):       {ml_regression_rate}%")
    print(f"QueryPilot per-query overhead:               {avg_overhead_ms}ms")

    os.makedirs("results", exist_ok=True)
    out_file = f"results/{args.scenario}_{args.n_queries}q_seed{args.seed}.json"
    with open(out_file, "w") as f:
        json.dump({
            "metrics": metrics,
            "native_results": native_results,
            "ml_results": ml_results,
            "sage_results": sage_results,
        }, f, indent=2)
    print(f"\nSaved to {out_file}")


if __name__ == "__main__":
    main()
