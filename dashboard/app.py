import os
import json
import glob
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import streamlit as st

st.set_page_config(page_title="QueryPilot Dashboard", layout="wide")

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")


def load_result_files():
    pattern = os.path.join(RESULTS_DIR, "*.json")
    files = sorted(glob.glob(pattern))
    return files


def load_result(path):
    with open(path) as f:
        return json.load(f)


def no_results_msg():
    st.info(
        "No experiment results yet.  \n"
        "Run: `python experiments/baseline.py --scenario stable --n-queries 100`"
    )


# ── Sidebar navigation ────────────────────────────────────────────────────────
st.sidebar.title("QueryPilot")
page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Query Timeline", "SAGE Decisions", "Experiment Comparison"],
)

result_files = load_result_files()

if not result_files:
    no_results_msg()
    st.stop()

file_labels = [os.path.basename(f) for f in result_files]
selected_label = st.sidebar.selectbox("Result file", file_labels)
selected_path = result_files[file_labels.index(selected_label)]
data = load_result(selected_path)

metrics = data["metrics"]
native_results = data.get("native_results", [])
ml_results = data.get("ml_results", [])
sage_results = data.get("sage_results", [])

CONFIGS = ["native", "ml_only", "sage"]
CONFIG_COLORS = {"native": "#4C72B0", "ml_only": "#DD8452", "sage": "#55A868"}
CONFIG_LABELS = {"native": "Native MySQL", "ml_only": "ML-Only", "sage": "QueryPilot + SAGE"}


# ── Page 1: Overview ──────────────────────────────────────────────────────────
if page == "Overview":
    st.title("Overview")
    st.markdown(f"**Scenario:** `{metrics['scenario']}`  |  **Queries:** {metrics['n_queries']}")

    # Summary table
    rows = []
    for cfg in CONFIGS:
        m = metrics[cfg]
        rows.append({
            "Config": CONFIG_LABELS[cfg],
            "Mean (ms)": f"{m['mean_ms']:.1f}",
            "Median (ms)": f"{m['median_ms']:.1f}",
            "P95 (ms)": f"{m['p95_ms']:.1f}",
            "Total (ms)": f"{m['total_ms']:.0f}",
        })
    st.subheader("Latency Summary")
    st.table(pd.DataFrame(rows).set_index("Config"))

    # Improvement vs native
    native_mean = metrics["native"]["mean_ms"]
    col1, col2 = st.columns(2)
    for cfg, col in zip(["ml_only", "sage"], [col1, col2]):
        diff_pct = (native_mean - metrics[cfg]["mean_ms"]) / native_mean * 100
        label = f"{CONFIG_LABELS[cfg]} vs Native"
        color = "green" if diff_pct >= 0 else "red"
        sign = "+" if diff_pct >= 0 else ""
        col.metric(label, f"{sign}{diff_pct:.1f}% mean latency change",
                   help="Positive = faster than native")

    # Bar chart — mean latency
    st.subheader("Mean Latency by Configuration")
    fig, ax = plt.subplots(figsize=(6, 3.5))
    bars = [metrics[c]["mean_ms"] for c in CONFIGS]
    colors = [CONFIG_COLORS[c] for c in CONFIGS]
    labels = [CONFIG_LABELS[c] for c in CONFIGS]
    ax.bar(labels, bars, color=colors, width=0.5)
    ax.set_ylabel("Mean Latency (ms)")
    ax.set_title("Mean Query Latency")
    for i, v in enumerate(bars):
        ax.text(i, v + max(bars) * 0.01, f"{v:.1f}", ha="center", fontsize=9)
    ax.set_ylim(0, max(bars) * 1.2)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# ── Page 2: Query Timeline ────────────────────────────────────────────────────
elif page == "Query Timeline":
    st.title("Query Timeline")

    show_native = st.checkbox("Native MySQL", value=True)
    show_ml = st.checkbox("ML-Only", value=True)
    show_sage = st.checkbox("QueryPilot + SAGE", value=True)

    fig, ax = plt.subplots(figsize=(12, 4))

    if show_native and native_results:
        times = [r["time_ms"] for r in native_results]
        ax.plot(times, color=CONFIG_COLORS["native"], label=CONFIG_LABELS["native"], alpha=0.8, linewidth=1)

    if show_ml and ml_results:
        times = [r["time_ms"] for r in ml_results]
        ax.plot(times, color=CONFIG_COLORS["ml_only"], label=CONFIG_LABELS["ml_only"], alpha=0.8, linewidth=1)

    if show_sage and sage_results:
        times = [r["time_ms"] for r in sage_results]
        ax.plot(times, color=CONFIG_COLORS["sage"], label=CONFIG_LABELS["sage"], alpha=0.8, linewidth=1)

        # Mark drift events
        drift_indices = [i for i, r in enumerate(sage_results) if r.get("drift_detected")]
        if drift_indices:
            drift_times = [sage_results[i]["time_ms"] for i in drift_indices]
            ax.scatter(drift_indices, drift_times, color="red", zorder=5, s=40,
                       label="Drift detected", marker="^")

    ax.set_xlabel("Query Index")
    ax.set_ylabel("Execution Time (ms)")
    ax.set_title("Query Execution Time Over Time")
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# ── Page 3: SAGE Decisions ────────────────────────────────────────────────────
elif page == "SAGE Decisions":
    st.title("SAGE Decisions")

    if not sage_results:
        st.warning("No SAGE results in this file.")
        st.stop()

    decisions = [r["decision"] for r in sage_results]
    decision_counts = pd.Series(decisions).value_counts()

    col1, col2 = st.columns([1, 2])

    # Pie chart
    with col1:
        st.subheader("Decision Breakdown")
        DECISION_COLORS = {
            "adapt": "#55A868",
            "gather_evidence": "#4C72B0",
            "fallback": "#DD8452",
        }
        pie_labels = decision_counts.index.tolist()
        pie_values = decision_counts.values.tolist()
        pie_colors = [DECISION_COLORS.get(l, "#999999") for l in pie_labels]
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(pie_values, labels=pie_labels, colors=pie_colors, autopct="%1.1f%%", startangle=90)
        ax.set_title("SAGE Decision Types")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # Decision frequency over time (bins of 10)
    with col2:
        st.subheader("Decision Frequency Over Time")
        bin_size = 10
        n = len(sage_results)
        bins = range(0, n, bin_size)
        bin_data = []
        for b in bins:
            chunk = sage_results[b: b + bin_size]
            counts = {"bin_start": b}
            for d in ["adapt", "gather_evidence", "fallback"]:
                counts[d] = sum(1 for r in chunk if r["decision"] == d)
            bin_data.append(counts)
        bin_df = pd.DataFrame(bin_data).set_index("bin_start")

        fig, ax = plt.subplots(figsize=(8, 3.5))
        bottom = [0] * len(bin_df)
        for d, color in DECISION_COLORS.items():
            if d in bin_df.columns:
                vals = bin_df[d].tolist()
                ax.bar(bin_df.index, vals, bottom=bottom, color=color, label=d, width=bin_size * 0.8)
                bottom = [b + v for b, v in zip(bottom, vals)]
        ax.set_xlabel("Query Index")
        ax.set_ylabel("Count")
        ax.set_title(f"SAGE Decisions per {bin_size}-Query Window")
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # Last 20 decisions table
    st.subheader("Last 20 SAGE Decisions")
    recent = sage_results[-20:]
    table_rows = [
        {
            "Index": len(sage_results) - len(recent) + i,
            "Query": r["sql"][:55] + "..." if len(r["sql"]) > 55 else r["sql"],
            "Decision": r["decision"],
            "Reason": r.get("reason", ""),
            "Time (ms)": f"{r['time_ms']:.1f}",
        }
        for i, r in enumerate(recent)
    ]
    st.dataframe(pd.DataFrame(table_rows).set_index("Index"), use_container_width=True)


# ── Page 4: Experiment Comparison ────────────────────────────────────────────
elif page == "Experiment Comparison":
    st.title("Experiment Comparison")

    if len(result_files) < 2:
        st.info("Load more result files by running experiments with different scenarios.  \n"
                "Example: `python experiments/baseline.py --scenario sudden_shift --n-queries 100`")

    all_metrics = []
    for path in result_files:
        d = load_result(path)
        m = d["metrics"]
        for cfg in CONFIGS:
            all_metrics.append({
                "File": os.path.basename(path),
                "Scenario": m["scenario"],
                "Config": CONFIG_LABELS[cfg],
                "Mean (ms)": m[cfg]["mean_ms"],
                "Median (ms)": m[cfg]["median_ms"],
                "P95 (ms)": m[cfg]["p95_ms"],
                "Total (ms)": m[cfg]["total_ms"],
            })

    df_all = pd.DataFrame(all_metrics)

    # Grouped bar chart — mean latency by scenario + config
    st.subheader("Mean Latency Across Scenarios")
    scenarios = df_all["Scenario"].unique().tolist()
    x = range(len(scenarios))
    width = 0.25
    fig, ax = plt.subplots(figsize=(max(8, len(scenarios) * 3), 4))
    for i, cfg in enumerate(CONFIGS):
        vals = [
            df_all[(df_all["Scenario"] == s) & (df_all["Config"] == CONFIG_LABELS[cfg])]["Mean (ms)"].mean()
            for s in scenarios
        ]
        offset = (i - 1) * width
        ax.bar([xi + offset for xi in x], vals, width=width,
               color=CONFIG_COLORS[cfg], label=CONFIG_LABELS[cfg])
    ax.set_xticks(list(x))
    ax.set_xticklabels(scenarios)
    ax.set_ylabel("Mean Latency (ms)")
    ax.set_title("Mean Query Latency by Scenario and Configuration")
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Summary table
    st.subheader("All Results")
    pivot = df_all.pivot_table(
        index=["Scenario", "File"], columns="Config",
        values="Mean (ms)", aggfunc="first"
    ).reset_index()
    st.dataframe(pivot, use_container_width=True)
