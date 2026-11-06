import numpy as np
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

FEATURE_ORDER = [
    "query_type_encoded", "num_joins", "num_tables",
    "has_where", "has_group_by", "has_order_by",
    "estimated_rows", "uses_index",
]

MIN_SAMPLES = 10

def features_to_vector(feature_dict):
    return np.array([feature_dict.get(k, 0) for k in FEATURE_ORDER], dtype=float)

class PerformanceModel:
    def __init__(self):
        self._models = [
            LinearRegression(),
            RandomForestRegressor(n_estimators=50, random_state=42),
            GradientBoostingRegressor(n_estimators=50, random_state=42),
        ]
        self._trained = False

    @property
    def is_trained(self):
        return self._trained

    def fit(self, X, y):
        X = np.array(X, dtype=float)
        y = np.array(y, dtype=float)
        if len(X) < MIN_SAMPLES:
            return
        for m in self._models:
            m.fit(X, y)
        self._trained = True

    def _predict_all(self, x):
        x = features_to_vector(x).reshape(1, -1)
        return np.array([m.predict(x)[0] for m in self._models])

    def predict(self, x):
        return float(np.mean(self._predict_all(x)))

    def predict_with_uncertainty(self, x):
        preds = self._predict_all(x)
        return float(np.mean(preds)), float(np.std(preds))

    def save(self, path):
        joblib.dump({"models": self._models, "trained": self._trained}, path)

    def load(self, path):
        data = joblib.load(path)
        self._models = data["models"]
        self._trained = data["trained"]
