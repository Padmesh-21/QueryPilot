import time
import numpy as np
from ml.performance_model import PerformanceModel, features_to_vector
from ml.drift_detector import WorkloadDriftDetector
from collector.candidate_generator import generate_candidates
from collector.feature_extractor import extract_features
from collector.metrics_logger import MetricsLogger


class SAGEController:
    def __init__(
        self,
        uncertainty_threshold=0.8,
        drift_sensitivity=0.5,
        min_evidence=8,
        regression_tolerance=0.15,
    ):
        self.uncertainty_threshold = uncertainty_threshold
        self.regression_tolerance = regression_tolerance
        self.min_evidence = min_evidence

        lambda_ = max(1, int(50 * (1 - drift_sensitivity)))
        self.model = PerformanceModel()
        self.drift_detector = WorkloadDriftDetector(lambda_=lambda_)
        self._training_buffer = []
        self._queries_seen = 0
        self._drift_active = False  # set after execution, checked on next call
        self._logger = MetricsLogger()

    def _run(self, sql, cursor):
        start = time.perf_counter()
        cursor.execute(sql)
        results = cursor.fetchall()
        elapsed_ms = (time.perf_counter() - start) * 1000
        return results, round(elapsed_ms, 3)

    def execute(self, sql, cursor):
        candidates = generate_candidates(sql, cursor)
        native = candidates[0]
        features = extract_features(sql, cursor)
        fvec = features_to_vector(features)

        not_ready = not self.model.is_trained or self._queries_seen < self.min_evidence

        if not_ready:
            selected = native
            decision = "gather_evidence"
            reason = f"Collecting evidence ({self._queries_seen}/{self.min_evidence} queries seen)"
            pred_mean = pred_std = None

        elif self._drift_active:
            selected = native
            decision = "fallback"
            reason = "Workload drift detected — falling back to native optimizer"
            pred_mean = pred_std = None
            self._training_buffer.clear()
            self._drift_active = False

        else:
            native_mean, _ = self.model.predict_with_uncertainty(features)
            best = None
            best_mean = float("inf")

            for c in candidates:
                c_features = extract_features(c["sql"], cursor) if c["hint_type"] != "native" else features
                mean, std = self.model.predict_with_uncertainty(c_features)
                rel_uncertainty = std / mean if mean > 0 else float("inf")

                if rel_uncertainty > self.uncertainty_threshold:
                    continue
                if mean > native_mean * (1 + self.regression_tolerance):
                    continue
                if mean < best_mean:
                    best_mean = mean
                    best = (c, mean, std)

            if best is None or best[0]["hint_type"] == "native":
                selected = native
                decision = "fallback"
                reason = "No candidate beat native within uncertainty and regression bounds"
                pred_mean = pred_std = None
            else:
                selected, pred_mean, pred_std = best
                decision = "adapt"
                reason = (
                    f"Candidate '{selected['hint_type']}' predicted {pred_mean:.1f}ms "
                    f"(uncertainty ±{pred_std:.1f}ms)"
                )

        results, execution_time_ms = self._run(selected["sql"], cursor)

        # Update drift detector with actual execution time AFTER the query runs
        self._drift_active = self.drift_detector.update(sql, execution_time_ms)
        self._queries_seen += 1
        self._training_buffer.append((fvec, execution_time_ms))

        if len(self._training_buffer) >= self.min_evidence:
            X = [v for v, _ in self._training_buffer]
            y = [t for _, t in self._training_buffer]
            self.model.fit(X, y)

        result = {
            "results": results,
            "execution_time_ms": execution_time_ms,
            "decision": decision,
            "selected_candidate": selected,
            "prediction_mean": pred_mean,
            "prediction_uncertainty": pred_std,
            "drift_detected": self._drift_active,
            "reason": reason,
        }
        self._logger.log(sql, result)
        return result
