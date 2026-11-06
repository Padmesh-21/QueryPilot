import csv
import os
import time
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "results", "sage_decisions.csv")

FIELDS = [
    "timestamp", "query_index", "scenario", "sql_preview",
    "decision", "reason", "hint_type",
    "execution_time_ms", "prediction_mean_ms", "prediction_uncertainty_ms",
    "drift_detected",
]


class MetricsLogger:
    def __init__(self, scenario="unknown"):
        self.scenario = scenario
        self.query_index = 0
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        self._file = open(LOG_FILE, "a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=FIELDS)
        # Write header only if file is empty
        if os.path.getsize(LOG_FILE) == 0:
            self._writer.writeheader()

    def log(self, sql, sage_result):
        self._writer.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "query_index": self.query_index,
            "scenario": self.scenario,
            "sql_preview": sql[:80].replace("\n", " "),
            "decision": sage_result.get("decision", ""),
            "reason": sage_result.get("reason", ""),
            "hint_type": sage_result.get("selected_candidate", {}).get("hint_type", ""),
            "execution_time_ms": sage_result.get("execution_time_ms", ""),
            "prediction_mean_ms": round(sage_result["prediction_mean"], 3)
                if sage_result.get("prediction_mean") is not None else "",
            "prediction_uncertainty_ms": round(sage_result["prediction_uncertainty"], 3)
                if sage_result.get("prediction_uncertainty") is not None else "",
            "drift_detected": sage_result.get("drift_detected", False),
        })
        self._file.flush()
        self.query_index += 1

    def close(self):
        self._file.close()
