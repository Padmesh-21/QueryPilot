import numpy as np
from workload.queries import QUERIES, instantiate

_SCAN_HEAVY_IDS = {"q1", "q6"}
_JOIN_HEAVY_IDS = {"q3", "q5", "q10"}

_SCAN_HEAVY = [q for q in QUERIES if q["id"] in _SCAN_HEAVY_IDS]
_JOIN_HEAVY = [q for q in QUERIES if q["id"] in _JOIN_HEAVY_IDS]


class WorkloadGenerator:
    def __init__(self, scenario="stable", seed=42):
        self.scenario = scenario
        self.rng = np.random.default_rng(seed)
        self._py_rng = __import__("random").Random(seed)

    def _pick(self, pool):
        idx = self.rng.integers(0, len(pool))
        q = pool[idx]
        param_idx = self.rng.integers(0, len(q["params"]))
        return instantiate(q, param_override=q["params"][param_idx], rng=self._py_rng)

    def generate(self, n_queries=500):
        if self.scenario == "stable":
            return self._stable(n_queries)
        elif self.scenario == "sudden_shift":
            return self._sudden_shift(n_queries)
        elif self.scenario == "gradual_shift":
            return self._gradual_shift(n_queries)
        elif self.scenario == "data_skew":
            return self._data_skew(n_queries)
        else:
            raise ValueError(f"Unknown scenario: {self.scenario}")

    def _stable(self, n):
        return [self._pick(QUERIES) for _ in range(n)]

    def _sudden_shift(self, n):
        cutoff = int(n * 0.6)
        queries = []
        for i in range(n):
            pool = _SCAN_HEAVY if i < cutoff else _JOIN_HEAVY
            queries.append(self._pick(pool))
        return queries

    def _gradual_shift(self, n):
        queries = []
        for i in range(n):
            p_join = i / max(n - 1, 1)  # 0.0 → 1.0
            pool = _JOIN_HEAVY if self.rng.random() < p_join else _SCAN_HEAVY
            queries.append(self._pick(pool))
        return queries

    def _data_skew(self, n):
        cutoff = int(n * 0.7)
        q3 = next(q for q in QUERIES if q["id"] == "q3")
        building_params = [p for p in q3["params"] if p["segment"] == "BUILDING"]
        auto_params = [p for p in q3["params"] if p["segment"] == "AUTOMOBILE"]
        queries = []
        for i in range(n):
            params_pool = building_params if i < cutoff else auto_params
            idx = self.rng.integers(0, len(params_pool))
            queries.append(instantiate(q3, param_override=params_pool[idx], rng=self._py_rng))
        return queries
