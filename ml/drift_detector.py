class PageHinkley:
    def __init__(self, delta=0.005, lambda_=50, alpha=0.9999):
        self.delta = delta
        self.lambda_ = lambda_
        self.alpha = alpha
        self.reset()

    def reset(self):
        self._n = 0
        self._mean = 0.0
        self._sum = 0.0
        self._min_sum = 0.0

    @property
    def n(self):
        return self._n

    @property
    def mean(self):
        return self._mean

    def update(self, value):
        self._n += 1
        self._mean = self._mean * self.alpha + value * (1 - self.alpha)
        self._sum += value - self._mean - self.delta
        self._min_sum = min(self._min_sum, self._sum)
        return (self._sum - self._min_sum) > self.lambda_


class WorkloadDriftDetector:
    def __init__(self, delta=0.005, lambda_=50):
        self._delta = delta
        self._lambda = lambda_
        self._global = PageHinkley(delta=delta, lambda_=lambda_)
        self._per_query = {}

    def _signature(self, sql):
        return sql.strip().replace(" ", "")[:60]

    def update(self, sql, execution_time_ms):
        sig = self._signature(sql)
        if sig not in self._per_query:
            self._per_query[sig] = PageHinkley(delta=self._delta, lambda_=self._lambda)
        self._per_query[sig].update(execution_time_ms)
        return self._global.update(execution_time_ms)

    def reset_all(self):
        self._global.reset()
        self._per_query.clear()
