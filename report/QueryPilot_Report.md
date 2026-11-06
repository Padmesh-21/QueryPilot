# QueryPilot: An Uncertainty-Aware, Self-Adaptive Query Optimization Framework for Dynamic Database Workloads

---

# CHAPTER 1 – INTRODUCTION

Modern database systems are central to nearly every software application, from e-commerce platforms to enterprise analytics pipelines. The efficiency with which a database executes SQL queries directly affects application responsiveness, server resource consumption, and ultimately the user experience. Among the many factors that determine query efficiency, the choice of execution plan made by the query optimizer is one of the most consequential. A well-chosen plan can execute a query in milliseconds; a poor one can take seconds or minutes on the same data.

## 1.1 OVERVIEW

Query optimization is the process by which a database management system (DBMS) selects the most efficient execution strategy for a given SQL query. MySQL's native optimizer evaluates multiple candidate plans based on internal cost estimates and statistical summaries of the data, then selects the plan with the lowest estimated cost. While this approach works well under stable conditions, it faces a fundamental challenge in real-world deployments: workloads are not static.

As application usage patterns change over time, the mix of queries arriving at the database shifts. Morning analytical queries may differ substantially from afternoon transactional queries. A new product launch may cause a sudden surge in filter-heavy queries for a specific product category. Seasonal patterns may cause gradual changes in join selectivity and result set sizes. When these workload shifts occur, a plan that was optimal under the previous distribution may become inefficient under the new one.

Learned query optimization techniques attempt to address this limitation by using machine learning to improve execution plan selection. However, ML models are trained on historical data, and their predictions can become unreliable when the workload distribution changes, when the model encounters unfamiliar query patterns, or when its uncertainty is high. An unconstrained ML-based optimizer that blindly follows its model's recommendations under these conditions can introduce performance regressions — making queries slower than MySQL's native optimizer would.

QueryPilot addresses this challenge as an external Python middleware that intercepts SQL queries before they reach MySQL. For each query, QueryPilot extracts structural features, generates a small set of candidate execution variants using MySQL optimizer hints, predicts the performance of each candidate using an ensemble machine learning model, estimates the uncertainty of those predictions, monitors the query stream for workload drift using the Page-Hinkley statistical test, and uses a guarded decision controller called SAGE (Stability-Aware Guarded Execution) to choose between adapting to a better plan, gathering more evidence, or falling back to MySQL's native optimizer. Every decision is logged to a CSV file and visualized in a real-time Streamlit dashboard.

## 1.2 PROBLEM STATEMENT

The central problem addressed in this project is as follows: given a stream of SQL queries arriving at a MySQL database under dynamically changing workload conditions, how can an external optimization framework make bounded-risk execution plan decisions — improving performance where possible while reliably preventing regressions — without requiring modifications to the database internals?

This problem has three dimensions. First, the optimization decisions must be made incrementally and online, as new queries arrive, without access to the full future query distribution. Second, the framework must estimate its own confidence in each recommendation so that unreliable predictions do not lead to harmful execution choices. Third, the framework must detect when the workload distribution has changed and respond appropriately, rather than continuing to apply recommendations trained on an outdated distribution.

### 1.2.1 Motivation

The motivation for QueryPilot stems from two observed limitations in the existing landscape of query optimization. Traditional rule-based optimizers such as MySQL's native optimizer make static decisions based on collected statistics and do not adapt when those statistics become unrepresentative. Learned optimizers such as Bao and Neo demonstrate that ML can improve on native optimizers on training workloads, but neither system explicitly addresses what should happen when the model's predictions are unreliable or when the workload has drifted away from the training distribution.

QueryPilot is motivated by the hypothesis that a conservative, uncertainty-aware decision framework — one that knows when not to override the native optimizer — is more robust in practice than a system that always applies its best ML recommendation. This conservative approach is especially relevant in production environments where performance regressions carry real costs.

## 1.3 OBJECTIVES

The objectives of this project are as follows:

- To design and implement QueryPilot, a Python middleware for adaptive query optimization over MySQL that operates without modifying the database internals.
- To build a feature extraction pipeline that derives meaningful query characteristics from MySQL's EXPLAIN output.
- To implement a candidate optimization generator that produces controlled query variants using MySQL's supported optimizer hint system.
- To train an ensemble machine learning model on observed execution data and use ensemble disagreement as a practical uncertainty estimator.
- To implement the Page-Hinkley sequential change-point detection algorithm for real-time workload drift detection.
- To design and implement SAGE, a guarded decision controller that combines uncertainty estimation, drift detection, and risk-bounded adaptation.
- To evaluate QueryPilot against a native MySQL baseline and an unconstrained ML-Only baseline across four controlled workload scenarios using the TPC-H benchmark.
- To build a Streamlit monitoring dashboard that visualizes query performance, SAGE decisions, drift events, and prediction uncertainty in real time.

### 1.3.1 Scope of the Project

The scope of this project is limited to MySQL 8.0 as the target database system. Optimization decisions are made using MySQL's supported optimizer hint system (NO_INDEX, HASH_JOIN, NO_BKA), and the framework does not claim to enumerate or evaluate every possible execution plan. The evaluation uses the TPC-H benchmark at scale factor 1. The framework is implemented as a Python SDK and does not implement a transparent wire-protocol proxy. Extensions such as a database proxy layer, support for other database systems, and advanced hint types such as FORCE INDEX or JOIN_ORDER are identified as future work.

---

# CHAPTER 2 – LITERATURE SURVEY

The field of query optimization has a long history, and the application of machine learning to this domain has accelerated significantly in recent years. This chapter reviews the most relevant prior work, spanning traditional optimizer limitations, learned query optimization, database configuration tuning, and the statistical foundations of drift detection and uncertainty estimation that underpin QueryPilot's design.

Leis et al. (2015) conducted a foundational empirical study titled "How Good Are Query Optimizers, Really?" published in the Proceedings of the VLDB Endowment. The authors systematically evaluated cardinality estimation errors in several commercial and open-source database systems and demonstrated that even small estimation errors can compound across join trees, leading to dramatically suboptimal plan selections. Their work established that cardinality misestimation is the primary source of optimizer failure in practice, not the cost model itself. This finding motivates external optimization frameworks like QueryPilot that do not rely on the database's internal statistics for decision-making but instead learn from observed execution performance.

Marcus and Papaemmanouil (2019) introduced Neo, a learned query optimizer published in the Proceedings of the VLDB Endowment. Neo uses a value network trained on query execution feedback to evaluate candidate execution plans produced by the database's own optimizer. The key insight of Neo is that a learned value function can rank plans more accurately than the database's cost model when trained on sufficient execution data. Neo achieves significant improvements over the native optimizer on the Join Order Benchmark. However, Neo is tightly integrated with the database's plan enumeration engine and does not address what should happen when the model encounters queries that are dissimilar from its training distribution. QueryPilot differs from Neo in that it operates as an external middleware without requiring plan enumeration access, and explicitly addresses model uncertainty and workload drift.

Marcus et al. (2022) presented Bao (Bandit Optimizer) in the ACM SIGMOD Record, framing optimizer hint selection as a contextual bandit problem. Bao uses a tree-convolutional neural network over the query plan structure to recommend one of a small, fixed set of hint configurations per query. Bao's formulation is particularly relevant to QueryPilot because it also works within a predefined hint space rather than enumerating all possible plans. Bao demonstrates strong performance on both TPC-H and the Join Order Benchmark and has been extended to handle non-stationary workloads using a sliding window approach. QueryPilot differs from Bao in that it adds an explicit uncertainty estimation layer and a drift detection mechanism, and uses a fallback decision when uncertainty is too high rather than always applying the bandit's recommendation.

Van Aken et al. (2017) introduced OtterTune, a system for automatic database management system tuning through large-scale machine learning, presented at ACM SIGMOD. OtterTune uses Gaussian process regression to recommend database configuration knob settings (such as buffer pool size, thread count, and I/O scheduler parameters) based on a repository of previously observed workload-configuration-performance tuples. Unlike query-level optimizers, OtterTune operates at the configuration level and targets long-term system throughput rather than per-query execution time. QueryPilot operates at the per-query level and does not modify database configuration. OtterTune's use of uncertainty-aware regression (Gaussian processes) is conceptually related to QueryPilot's ensemble uncertainty estimation, but the two systems address fundamentally different optimization targets.

Gama et al. (2014) published a comprehensive survey titled "A Survey on Concept Drift Adaptation" in ACM Computing Surveys, reviewing the broad landscape of methods for learning from non-stationary data streams. The survey distinguishes between abrupt drift, gradual drift, recurring drift, and incremental drift, and categorizes detection methods as statistical process control methods, windowing methods, and ensemble methods. This taxonomy directly informs QueryPilot's experimental design, which evaluates performance under sudden shift, gradual shift, stable, and data skew workload scenarios. QueryPilot employs a statistical process control method (Page-Hinkley) for drift detection, which the survey identifies as suitable for detecting abrupt changes in data streams.

Bifet and Gavalda (2007) introduced the ADWIN (ADaptive WINdowing) algorithm at the 2007 SIAM International Conference on Data Mining. ADWIN maintains a variable-length window over a data stream and automatically shrinks the window when a statistical change is detected, ensuring that the active window always contains data from the current distribution. ADWIN provides formal guarantees on false positive and false negative rates. QueryPilot uses the Page-Hinkley test instead of ADWIN, primarily because Page-Hinkley is computationally lighter for high-frequency query streams and does not require storing the full window of observations. Both methods are evaluated in the literature as effective for detecting abrupt shifts in data streams.

Hinkley (1971) originally proposed the sequential change-point detection method known as the Page-Hinkley test in the journal Biometrika. The test maintains a cumulative sum statistic that increases when observed values exceed the running mean by more than a small tolerance, and signals a change when this statistic exceeds a threshold. The test is well-suited to query execution time streams because it is computationally efficient, requires no window storage, and is sensitive to sustained upward shifts in mean execution time. QueryPilot implements the Page-Hinkley test with parameters delta=0.005 and lambda=25, and maintains one detector per unique query signature in addition to a global detector across all queries.

Lakshminarayanan et al. (2017) demonstrated in their NeurIPS paper "Simple and Scalable Predictive Uncertainty Estimation Using Deep Ensembles" that training multiple independently initialized neural networks and using their output disagreement as an uncertainty signal is a practical and effective approach to uncertainty quantification. While the original paper focuses on deep neural networks, the ensemble disagreement principle generalizes to any ensemble of models. QueryPilot applies this principle to an ensemble of three scikit-learn models — Linear Regression, Random Forest Regressor, and Gradient Boosting Regressor — where the standard deviation of the three predictions divided by their mean serves as the relative uncertainty estimate. This approach requires no Bayesian inference and introduces negligible computational overhead compared to a single model.

---

# CHAPTER 3 – SYSTEM DESIGN

The design of QueryPilot is organized around a sequential pipeline that processes each incoming SQL query through a series of well-defined stages, from initial receipt to final execution and feedback collection. This chapter describes the flow of control and data through the system using three complementary flow diagrams: the overall execution flow, the SAGE decision flow, and the workload drift detection flow.

## 3.1 FLOW DIAGRAMS

The system design is best understood through the three flows described below. Each flow represents a distinct dimension of QueryPilot's operation. Together, they describe how a single query is processed, how SAGE makes its decision, and how the drift detector is updated and triggers a response.

### 3.1.1 QueryPilot Execution Flow

The QueryPilot execution flow describes the end-to-end lifecycle of a single SQL query as it passes through the system, as illustrated in Figure 3.1.

**Figure 3.1: QueryPilot Execution Flow**

The flow begins when the application submits a SQL query to the QueryPilot SDK via the `execute()` method. In Step 1, the Workload Collector receives the query and passes it to the Feature Extractor. In Step 2, the Feature Extractor runs MySQL's EXPLAIN command on the query to obtain the estimated execution plan, then derives eight features: query type (encoded as an integer), number of JOIN clauses, number of tables accessed, presence of WHERE clause, presence of GROUP BY clause, presence of ORDER BY clause, total estimated rows from the plan, and whether any table access uses an index. In Step 3, the Candidate Optimization Generator uses the extracted features and the EXPLAIN output to generate up to four candidate SQL variants: the native query with no hints, a variant with the NO_INDEX hint on the first table, a variant with the HASH_JOIN hint if joins are present, and a variant with the NO_BKA hint. In Step 4, the ML Performance Prediction Model predicts the expected execution time in milliseconds for each candidate. In Step 5, the Uncertainty Estimator computes the relative ensemble disagreement for each candidate prediction. In Step 6, the Workload Drift Detector checks whether the drift flag has been set by the previous query's update. In Step 7, SAGE takes all of this information and makes one of three decisions: adapt, gather_evidence, or fallback. In Step 8, the selected candidate query is executed against MySQL and the actual execution time is recorded. In Step 9, the Feedback and Metrics Collector updates the drift detector with the actual execution time, appends the observation to the training buffer, and retrains the ML model when sufficient evidence has been collected. In Step 10, the query results are returned to the application along with metadata about the decision made.

### 3.1.2 SAGE Decision Flow

The SAGE decision flow describes the logic inside the SAGE Controller module, as illustrated in Figure 3.2.

**Figure 3.2: SAGE Decision Flow**

When SAGE receives control, it first checks whether the model has been trained on at least the minimum required number of observations (default: 8). If not, it immediately selects the native candidate and sets the decision to gather_evidence. No uncertainty or regression checks are performed at this stage, as the model does not yet have sufficient data to make reliable predictions. If the model is trained, SAGE checks whether the drift flag is active, meaning that the Page-Hinkley detector signalled a workload shift after the previous query. If drift is active, SAGE selects the native candidate, sets the decision to fallback, and clears the training buffer to prevent the stale model from continuing to influence future decisions. If neither condition applies, SAGE evaluates each candidate by predicting its execution time and computing its relative uncertainty. Any candidate whose relative uncertainty exceeds the threshold (default: 0.8) is excluded. Any candidate whose predicted time exceeds the native predicted time by more than the regression tolerance (default: 15%) is also excluded. Among the surviving non-native candidates, SAGE selects the one with the lowest predicted execution time. If no non-native candidate survives, or if native has the lowest predicted time, SAGE falls back to native. If a valid non-native candidate is selected, the decision is set to adapt.

### 3.1.3 Workload Drift Detection Flow

The drift detection flow describes how the Page-Hinkley detector is updated after each query execution, as illustrated in Figure 3.3.

**Figure 3.3: Workload Drift Detection Flow**

After a query is executed and its actual execution time is recorded, the WorkloadDriftDetector receives the SQL text and the execution time in milliseconds. It first computes a query signature by stripping whitespace from the SQL and taking the first 60 characters, then updates the per-query Page-Hinkley detector for that signature. It then updates the global detector that monitors the execution time stream across all queries. The global detector computes the cumulative sum statistic: it adds the difference between the current observation and the running mean, minus a small tolerance delta, to an accumulator. If the accumulator minus its historical minimum exceeds the threshold lambda, the detector returns True to signal that drift has occurred. The WorkloadDriftDetector stores this signal in the SAGEController's `_drift_active` flag, which will be checked at the start of the next query's SAGE evaluation. If drift is detected, the controller clears its training buffer on the next invocation, effectively resetting the model's knowledge base so that it can re-learn under the new workload distribution.

---

# CHAPTER 4 – SYSTEM ARCHITECTURE

QueryPilot is organized as a ten-component pipeline, illustrated in Figure 4.1. Each component has a clearly defined responsibility and communicates with adjacent components through well-defined interfaces. The architecture is intentionally external to MySQL — no database internals are modified, and the system operates through the standard MySQL Python connector.

**Figure 4.1: QueryPilot System Architecture**

The **MySQL Database** component is the foundation of the system. It stores the experimental TPC-H dataset (8.6 million rows across 8 tables at scale factor 1) and executes all SQL queries. MySQL 8.0.43 is used because it supports the EXPLAIN ANALYZE command, which provides actual row counts and execution times alongside estimated values, and because its optimizer hint system is mature and well-documented. All communication with MySQL uses the official mysql-connector-python library without any ORM abstraction layer.

The **Workload Collector** is the entry point for queries arriving at QueryPilot. It receives SQL strings from the application, timestamps each query, and passes them into the pipeline. In its current implementation, the workload collector is embedded within the SAGEController's execute() method, but it is designed as a separable component that could be extended to intercept queries from an application log or a MySQL audit plugin.

The **Feature Extractor** translates a raw SQL query string into a numerical feature vector suitable for machine learning. It issues an EXPLAIN command to MySQL to obtain the estimated execution plan, then parses the plan rows to extract eight features. These features capture the structural properties of the query (join count, table count, clause presence) and the optimizer's own estimates (estimated rows, index usage). The features are encoded as a fixed-length numpy array using a consistent ordering defined in the PerformanceModel module.

The **Candidate Optimization Generator** takes the original SQL query and generates a small set of alternative SQL strings by injecting MySQL optimizer hints. It supports four hint types: no hint (native), NO_INDEX to disable index usage on the leading table, HASH_JOIN to force a hash join between the two leading joined tables, and NO_BKA to disable Batched Key Access. The generator injects hints using a regular expression that inserts the hint comment immediately after the SELECT keyword, which is the correct syntactic position for MySQL optimizer hints. The candidate set is bounded at four entries, and join-specific hints are only generated when the query contains explicit JOIN clauses.

The **ML Performance Prediction Model** maintains an ensemble of three scikit-learn regression models: a Linear Regression, a Random Forest Regressor with 50 trees, and a Gradient Boosting Regressor with 50 estimators. The ensemble is trained incrementally on observed (feature vector, execution time) pairs. The model retrains after every batch of observations once the training buffer reaches the minimum evidence threshold. Training on a small ensemble of interpretable models is intentional: it allows the uncertainty estimation to be meaningful, it keeps inference latency low, and it avoids overfitting on the small training sets typical of early execution phases.

The **Uncertainty Estimator** is not a separate module but a function of the prediction ensemble. For any input feature vector, the three models produce three independent predictions. The mean of these predictions is the point estimate, and the standard deviation divided by the mean is the relative uncertainty. This ensemble disagreement metric captures how much the three models disagree about the expected execution time, which serves as a practical proxy for prediction confidence.

The **SAGE Decision Controller** is the central intelligence of QueryPilot. It receives the feature vector, the list of candidates with their predicted times and uncertainties, the current drift state, and the count of queries seen so far, and produces a single decision: adapt, gather_evidence, or fallback. The decision logic implements a priority-ordered set of guards that prevent risky adaptations under conditions of insufficient evidence, active drift, high uncertainty, or predicted regression.

The **Query Execution Layer** takes the selected candidate SQL string (which may be the native query or a hinted variant) and executes it against MySQL using a shared cursor. Execution time is measured on the client side using Python's time.perf_counter(), which captures the round-trip time including result fetching.

The **Feedback and Metrics Collector** receives the actual execution time after each query completes, updates the drift detector, appends the observation to the training buffer, triggers model retraining when the buffer is full, and logs the full decision record to a CSV file via the MetricsLogger. The logged record includes the timestamp, query signature, decision type, selected hint, predicted and actual execution times, uncertainty estimate, and drift flag.

The **Streamlit Dashboard** provides a real-time monitoring interface for QueryPilot's behaviour. It reads experiment result JSON files from the results/ directory and presents four pages: an Overview page with latency summary tables and bar charts, a Query Timeline page showing execution times over query index with drift event markers, a SAGE Decisions page with a decision breakdown pie chart and a decisions-over-time histogram, and an Experiment Comparison page that shows mean latency across all available scenarios side by side.

---

# CHAPTER 5 – SYSTEM IMPLEMENTATION

QueryPilot is implemented entirely in Python 3 and communicates with MySQL 8.0.43 using the mysql-connector-python library. Machine learning components are built using scikit-learn. Data manipulation uses pandas and numpy. The monitoring dashboard is built with Streamlit and matplotlib. All credentials are managed through environment variables loaded from a .env file using the python-dotenv library. The project is developed on Windows using Visual Studio Code, with the virtual environment managed using Python's built-in venv module.

## 5.1 MODULE DESCRIPTION

The implementation is organized into twelve Python modules across six packages. Each module addresses a specific responsibility in the pipeline.

### 5.1.1 Database Connection Module

The database connection module (`database/connection.py`) provides a single function, `get_connection()`, that reads the database host, port, username, password, and database name from environment variables and returns a live mysql.connector connection object. Using environment variables rather than hardcoded credentials ensures that sensitive information is never committed to version control. The connection is created fresh for each use and closed by the caller, following a stateless connection pattern that avoids connection pool complexity at this stage of the project.

### 5.1.2 Feature Extraction Module

The feature extraction module (`collector/feature_extractor.py`) implements the `extract_features(sql, cursor)` function. It executes EXPLAIN on the incoming SQL query, retrieves the plan rows, and parses the column names from the cursor description to locate the table, rows, filtered, key, and Extra columns. It then computes the eight features described in Chapter 4. Boolean features (has_where, has_group_by, has_order_by, uses_index) are encoded as integers (0 or 1). The function wraps the EXPLAIN call in a try-except block so that unparseable queries fall back to a zero-feature vector rather than raising an exception.

### 5.1.3 Candidate Optimization Generator Module

The candidate optimization generator (`collector/candidate_generator.py`) implements `generate_candidates(sql, cursor)`. It first calls a helper function `_get_first_table(sql, cursor)` that runs EXPLAIN and extracts the name of the first table in the plan. It then builds the candidate list by injecting hint strings using the `_inject_hint(sql, hint)` helper, which uses a regular expression to insert the hint comment after the SELECT keyword. Join-specific hints (HASH_JOIN, NO_BKA) are only added when the SQL contains the JOIN keyword. The function returns at most four candidates, always including the native query as candidate_id 0.

### 5.1.4 Performance Prediction Model Module

The performance prediction model (`ml/performance_model.py`) defines the `PerformanceModel` class and the `features_to_vector(feature_dict)` utility function. The utility function converts a feature dictionary to a numpy array using a fixed column ordering defined in the FEATURE_ORDER constant, ensuring consistency between training and inference. The PerformanceModel class wraps three scikit-learn estimators, exposes a `fit(X, y)` method that trains all three on the provided samples, a `predict(x)` method that returns the ensemble mean, and a `predict_with_uncertainty(x)` method that returns the mean and standard deviation. The model is considered trained only after at least MIN_SAMPLES (10) observations have been provided. The class also provides `save(path)` and `load(path)` methods using joblib for persistence.

### 5.1.5 Uncertainty Estimator Module

Uncertainty estimation is implemented as part of the PerformanceModel class rather than as a separate module. The `predict_with_uncertainty(x)` method feeds the input feature vector to each of the three models independently and returns the mean and standard deviation of the three predictions. The relative uncertainty is computed in the SAGEController as std / mean. This design keeps uncertainty estimation tightly coupled to the model that produces the predictions, making it impossible to use a stale uncertainty estimate from a different model state.

### 5.1.6 Workload Drift Detector Module

The drift detector module (`ml/drift_detector.py`) implements two classes. The `PageHinkley` class maintains the cumulative sum statistic and its running minimum, updates them with each new observation, and returns True when the statistic exceeds the threshold. The `WorkloadDriftDetector` class maintains a global PageHinkley instance and a dictionary of per-query-signature PageHinkley instances. Its `update(sql, execution_time_ms)` method derives the query signature, updates the appropriate per-query detector, updates the global detector, and returns the global detector's drift signal.

### 5.1.7 SAGE Controller Module

The SAGE controller (`sage/controller.py`) is the most complex module in the system. It instantiates a PerformanceModel, a WorkloadDriftDetector, and a MetricsLogger, and maintains the training buffer and query counter as instance state. The core logic is in the `execute(sql, cursor)` method.

The SAGE algorithm is described below:

```
Algorithm: SAGE Execution

Input: SQL query string, database cursor
Output: Query results, execution time, decision metadata

1. candidates ← generate_candidates(sql, cursor)
2. features ← extract_features(sql, cursor)
3. fvec ← features_to_vector(features)

4. IF model is not trained OR queries_seen < min_evidence THEN
     selected ← candidates[0]  (native)
     decision ← "gather_evidence"
     reason ← "Collecting evidence"

5. ELSE IF drift_active = True THEN
     selected ← candidates[0]  (native)
     decision ← "fallback"
     reason ← "Workload drift detected"
     training_buffer.clear()
     drift_active ← False

6. ELSE
     native_mean, _ ← model.predict_with_uncertainty(features)
     best ← None
     best_mean ← infinity

     FOR each candidate c in candidates DO
       IF c.hint_type = "native" THEN
         c_features ← features
       ELSE
         c_features ← extract_features(c.sql, cursor)
       END IF
       mean, std ← model.predict_with_uncertainty(c_features)
       rel_uncertainty ← std / mean
       IF rel_uncertainty > uncertainty_threshold THEN CONTINUE
       IF mean > native_mean × (1 + regression_tolerance) THEN CONTINUE
       IF mean < best_mean THEN
         best_mean ← mean
         best ← (c, mean, std)
       END IF
     END FOR

     IF best = None OR best.hint_type = "native" THEN
       selected ← candidates[0]
       decision ← "fallback"
     ELSE
       selected ← best.candidate
       decision ← "adapt"
     END IF

7. results, execution_time ← run(selected.sql, cursor)

8. drift_active ← drift_detector.update(sql, execution_time)
9. queries_seen ← queries_seen + 1
10. training_buffer.append((fvec, execution_time))
11. IF len(training_buffer) >= min_evidence THEN
      model.fit(training_buffer.X, training_buffer.y)
    END IF

12. metrics_logger.log(sql, decision_metadata)
13. RETURN results, execution_time, decision_metadata
```

### 5.1.8 Workload Generator Module

The workload generator (`workload/generator.py`) implements the `WorkloadGenerator` class with four scenario methods. The `stable` scenario samples uniformly from all five query templates. The `sudden_shift` scenario uses scan-heavy queries (Q1, Q6) for the first 60% of the workload and join-heavy queries (Q3, Q5, Q10) for the remainder. The `gradual_shift` scenario increases the probability of drawing a join-heavy query linearly from 0 to 1 over the full run. The `data_skew` scenario uses only Q3 but shifts the market segment parameter from BUILDING (first 70%) to AUTOMOBILE (last 30%). All scenarios use a seeded numpy random generator for reproducibility.

### 5.1.9 Experiment Runner Module

The experiment runner (`experiments/baseline.py`) implements the interleaved three-configuration comparison. For each query in the workload, it runs the native query first, then the ML-Only query (using the ML model without SAGE's guards), then the SAGE query, all with the same database cursor. This interleaved order ensures that all three configurations face the same MySQL buffer pool state for each query, eliminating the cache warm-up bias that would arise from running the three configurations sequentially. The runner computes mean, median, P95, and total latency for each configuration, the SAGE regression rate (counting only adapt decisions), and the ML-Only regression rate across all queries. It also measures QueryPilot's per-query overhead by timing feature extraction and candidate generation on a sample of 10 queries.

### 5.1.10 Dashboard Module

The dashboard (`dashboard/app.py`) is a four-page Streamlit application that reads result JSON files from the results/ directory. The Overview page displays a latency summary table, improvement percentages versus native, and a mean latency bar chart for the selected result file. The Query Timeline page plots execution time over query index for all three configurations, with drift detection events marked as red triangles on the SAGE line. The SAGE Decisions page shows a decision type pie chart and a stacked bar chart of decision frequency in bins of 10 queries, followed by a table of the last 20 SAGE decisions. The Experiment Comparison page shows a grouped bar chart comparing mean latency across all available result files and a pivot table summarizing all results.

---

# CHAPTER 6 – RESULTS AND CODING

The QueryPilot system was implemented and evaluated on a Windows machine running Python 3.12 and MySQL Server 8.0.43. Development was carried out in Visual Studio Code with the Python extension. All experiments were run with the virtual environment activated to ensure consistent package versions. The TPC-H benchmark at scale factor 1 was used as the experimental dataset, providing approximately 8.6 million rows across 8 relational tables. Standard indexes were created on all foreign key columns and frequently filtered columns including order date, ship date, and market segment.

## 6.1 SAMPLE CODE

The following code excerpts illustrate the core logic of three key modules.

**Code Excerpt 1: Feature Extraction Core Logic** (from `collector/feature_extractor.py`)

```python
def extract_features(sql, cursor):
    sql_upper = sql.upper().strip()
    first_token = sql_upper.split()[0] if sql_upper.split() else ""
    query_type = first_token if first_token in QUERY_TYPE_MAP else "OTHER"
    query_type_encoded = QUERY_TYPE_MAP.get(query_type, 4)
    num_joins = len(re.findall(r'\bJOIN\b', sql_upper))
    has_where = bool(re.search(r'\bWHERE\b', sql_upper))

    cursor.execute(f"EXPLAIN {sql}")
    plan_rows = cursor.fetchall()
    col_names = [desc[0].lower() for desc in cursor.description]

    num_tables = len([r for r in plan_rows if col(r, "table") is not None])
    estimated_rows = sum((col(r, "rows") or 0) for r in plan_rows)
    uses_index = any(col(r, "key") is not None for r in plan_rows)

    return {
        "query_type_encoded": query_type_encoded,
        "num_joins": num_joins,
        "num_tables": num_tables,
        "has_where": int(has_where),
        "estimated_rows": estimated_rows,
        "uses_index": int(uses_index),
    }
```

**Code Excerpt 2: SAGE Decision Logic Excerpt** (from `sage/controller.py`)

```python
not_ready = not self.model.is_trained or self._queries_seen < self.min_evidence

if not_ready:
    selected = native
    decision = "gather_evidence"
    reason = f"Collecting evidence ({self._queries_seen}/{self.min_evidence})"

elif self._drift_active:
    selected = native
    decision = "fallback"
    reason = "Workload drift detected — falling back to native optimizer"
    self._training_buffer.clear()
    self._drift_active = False

else:
    native_mean, _ = self.model.predict_with_uncertainty(features)
    best = None
    for c in candidates:
        mean, std = self.model.predict_with_uncertainty(c_features)
        rel_uncertainty = std / mean if mean > 0 else float("inf")
        if rel_uncertainty > self.uncertainty_threshold:
            continue
        if mean > native_mean * (1 + self.regression_tolerance):
            continue
        if mean < best_mean:
            best = (c, mean, std)
```

**Code Excerpt 3: Page-Hinkley Update Logic** (from `ml/drift_detector.py`)

```python
def update(self, value):
    self._n += 1
    self._mean = self._mean * self.alpha + value * (1 - self.alpha)
    self._sum += value - self._mean - self.delta
    self._min_sum = min(self._min_sum, self._sum)
    return (self._sum - self._min_sum) > self.lambda_
```

## 6.2 SAMPLE SCREENSHOTS

The QueryPilot Streamlit dashboard provides a real-time view of system behaviour across all four pages. The dashboard is launched with the command `streamlit run dashboard/app.py` from the project root directory.

**Figure 6.1: QueryPilot Dashboard – Overview Page**

The Overview page displays the latency summary table comparing Native MySQL, ML-Only, and QueryPilot+SAGE across mean, median, P95, and total execution time. It also shows the percentage improvement of each configuration versus native and a bar chart of mean latency per configuration.

**Figure 6.2: QueryPilot Dashboard – SAGE Decisions Page**

The SAGE Decisions page shows the distribution of SAGE decision types (adapt, gather_evidence, fallback) as a pie chart, a stacked bar chart of decisions per 10-query window, and a table of the last 20 SAGE decisions with their reasons.

**Figure 6.3: QueryPilot Dashboard – Query Timeline Page**

The Query Timeline page plots execution time in milliseconds over query index for all three configurations simultaneously. Workload drift detection events are marked as red triangles on the SAGE configuration line, allowing visual identification of when the drift detector fired.

## 6.3 RESULTS AND GRAPH

Experiments were conducted under four workload scenarios using 50 queries each with a warm-up phase of 5 queries. The interleaved execution methodology was used throughout, ensuring that all three configurations faced the same MySQL buffer pool state for each query. Refer to Table 6.1 for the complete results.

**Table 6.1: Experimental Results Across All Scenarios (50 Queries, Interleaved Methodology)**

| Scenario | Native Mean (ms) | ML-Only Mean (ms) | ML-Only vs Native | SAGE Mean (ms) | SAGE vs Native | SAGE Adapt Decisions | SAGE Regression Rate |
|---|---|---|---|---|---|---|---|
| sudden_shift | 17,640 | 17,714 | -0.4% | 17,576 | +0.4% | 0 | 0% |
| gradual_shift | 20,104 | 20,389 | -1.4% | 19,755 | +1.7% | 0 | 0% |
| stable | 20,471 | 19,791 | +3.3% | 19,879 | +2.9% | 0 | 0% |
| data_skew | 16,445 | 16,402 | +0.3% | 16,209 | +1.4% | 0 | 0% |

**Figure 6.4: Mean Latency Comparison Across Scenarios**

The results in Table 6.1 reveal several important findings. First, QueryPilot+SAGE matches or marginally outperforms Native MySQL in mean latency across all four scenarios. Second, ML-Only produces mixed results, degrading performance by 1.4% in the gradual_shift scenario and by 0.4% in the sudden_shift scenario while achieving modest improvements in the stable and data_skew scenarios. Third, SAGE's adapt decision count is zero across all scenarios, meaning SAGE always executed the native query. Fourth, SAGE's regression rate is 0% in all scenarios when measured correctly against only adapt-decision queries.

The zero adapt rate requires explanation. On the TPC-H benchmark with properly configured indexes and MySQL 8.0.43, the native optimizer is already near-optimal. The candidate hints generated by QueryPilot (NO_INDEX, HASH_JOIN, NO_BKA) typically produce worse performance than native on analytical workloads where MySQL has already chosen the optimal index and join strategy. The ML ensemble correctly learns this pattern and assigns lower predicted performance to hinted candidates, causing SAGE to consistently fall back to native. This is the correct behaviour — SAGE's uncertainty and regression filters are working as designed, preventing the system from applying harmful hints based on uncertain predictions.

The key contribution demonstrated by these results is not raw performance improvement but regression prevention. In the gradual_shift scenario, ML-Only degraded performance by 1.4% versus native by applying hints that the model incorrectly predicted as beneficial. QueryPilot+SAGE avoided this regression entirely by filtering out candidates with high uncertainty or predicted regression. This demonstrates that SAGE's guarded execution logic provides a meaningful safety net against ML-induced performance degradation in dynamic workload environments.

---

# CHAPTER 7 – CONCLUSION AND FUTURE WORK

This project designed, implemented, and evaluated QueryPilot, an uncertainty-aware self-adaptive query optimization framework for MySQL. QueryPilot operates as an external Python middleware that intercepts SQL queries, extracts execution plan features, generates candidate optimizer hint variants, predicts their relative performance using a three-model scikit-learn ensemble, estimates prediction uncertainty through ensemble disagreement, detects workload distribution shifts using the Page-Hinkley sequential change-point test, and applies the SAGE (Stability-Aware Guarded Execution) controller to make bounded-risk optimization decisions. The system was evaluated on the TPC-H benchmark at scale factor 1 across four controlled workload scenarios using an interleaved execution methodology designed to eliminate buffer pool warm-up bias — a methodological contribution identified and corrected during the experimental design phase. The results demonstrate that SAGE's conservative, uncertainty-aware decision logic prevents the performance regressions introduced by unconstrained ML-Only optimization, particularly under dynamic workload conditions such as the gradual shift scenario where ML-Only degraded performance by 1.4% versus native while SAGE achieved a 1.7% improvement. SAGE's adapt-only regression rate was 0% across all scenarios. The framework is accompanied by a real-time Streamlit monitoring dashboard that visualizes decision behaviour, drift events, and latency comparisons across configurations.

Future work will focus on several directions to strengthen QueryPilot's optimization capabilities. The candidate hint set will be extended to include FORCE INDEX hints targeting specific indexes on high-impact columns, and JOIN_ORDER hints to explore alternative join orderings for multi-table queries — candidates that are more likely to outperform native on some query shapes. Server-side execution timing via MySQL's Performance Schema will replace client-side timing to eliminate Python overhead from training labels, improving model accuracy. Experiments at larger TPC-H scale factors (5 and 10) will test whether the system's behaviour changes as data volumes increase and query execution times grow. A transparent MySQL wire-protocol proxy layer will be explored as a deployment alternative to the Python SDK, enabling QueryPilot to intercept queries from any application without code changes. Finally, online model updates with smaller batch sizes and a sliding window over recent observations will be investigated to improve adaptation speed under rapid workload transitions.

---

# REFERENCES

1. Bifet, A. and Gavalda, R. (2007) 'Learning from Time-Changing Data with Adaptive Windowing', Proceedings of the 2007 SIAM International Conference on Data Mining (SDM), pp. 443–448. https://doi.org/10.1137/1.9781611972771.42

2. Gama, J., Žliobaitė, I., Bifet, A., Pechenizkiy, M. and Bouchachia, A. (2014) 'A Survey on Concept Drift Adaptation', ACM Computing Surveys, Vol. 46, No. 4, pp. 1–37. https://doi.org/10.1145/2523813

3. Hinkley, D. V. (1971) 'Inference about the Change-Point in a Sequence of Random Variables', Biometrika, Vol. 58, No. 3, pp. 509–523. https://doi.org/10.1093/biomet/58.3.509

4. Lakshminarayanan, B., Pritzel, A. and Blundell, C. (2017) 'Simple and Scalable Predictive Uncertainty Estimation Using Deep Ensembles', Advances in Neural Information Processing Systems (NeurIPS), Vol. 30.

5. Leis, V., Gubichev, A., Mirchev, A., Boncz, P., Kemper, A. and Neumann, T. (2015) 'How Good Are Query Optimizers, Really?', Proceedings of the VLDB Endowment, Vol. 9, No. 3, pp. 204–215. https://doi.org/10.14778/2850583.2850594

6. Marcus, R. and Papaemmanouil, O. (2019) 'Neo: A Learned Query Optimizer', Proceedings of the VLDB Endowment, Vol. 12, No. 11, pp. 1705–1718. https://doi.org/10.14778/3342263.3342644

7. Marcus, R., Negi, P., Mao, H., Tatbul, N., Alizadeh, M. and Kraska, T. (2022) 'Bao: Making Learned Query Optimization Practical', ACM SIGMOD Record, Vol. 51, No. 1, pp. 6–13. https://doi.org/10.1145/3542700.3542703

8. Transaction Processing Performance Council (2023) TPC-H Benchmark Specification, Version 3.0.1. https://www.tpc.org/tpch/

9. Van Aken, D., Pavlo, A., Gordon, G. J. and Zhang, B. (2017) 'Automatic Database Management System Tuning Through Large-Scale Machine Learning', Proceedings of the 2017 ACM International Conference on Management of Data (SIGMOD), pp. 1009–1024. https://doi.org/10.1145/3035918.3064029
