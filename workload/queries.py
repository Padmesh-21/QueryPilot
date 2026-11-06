import random

QUERIES = [
    {
        "id": "q1",
        "name": "Pricing summary",
        "sql": (
            "SELECT l_returnflag, l_linestatus, "
            "SUM(l_quantity) AS sum_qty, "
            "SUM(l_extendedprice) AS sum_base_price, "
            "SUM(l_extendedprice * (1 - l_discount)) AS sum_disc_price, "
            "COUNT(*) AS count_order "
            "FROM lineitem "
            "WHERE l_shipdate <= '{shipdate}' "
            "GROUP BY l_returnflag, l_linestatus "
            "ORDER BY l_returnflag, l_linestatus"
        ),
        "params": [
            {"shipdate": "1998-09-02"},
            {"shipdate": "1998-08-15"},
            {"shipdate": "1998-07-01"},
        ],
        "workload_tags": ["stable", "analytical", "scan_heavy"],
    },
    {
        "id": "q3",
        "name": "Shipping priority",
        "sql": (
            "SELECT l_orderkey, "
            "SUM(l_extendedprice * (1 - l_discount)) AS revenue, "
            "o_orderdate, o_shippriority "
            "FROM customer "
            "JOIN orders ON c_custkey = o_custkey "
            "JOIN lineitem ON l_orderkey = o_orderkey "
            "WHERE c_mktsegment = '{segment}' "
            "AND o_orderdate < '{orderdate}' "
            "AND l_shipdate > '{orderdate}' "
            "GROUP BY l_orderkey, o_orderdate, o_shippriority "
            "ORDER BY revenue DESC, o_orderdate "
            "LIMIT 10"
        ),
        "params": [
            {"segment": seg, "orderdate": od}
            for seg in ["BUILDING", "AUTOMOBILE", "MACHINERY", "HOUSEHOLD", "FURNITURE"]
            for od in ["1995-03-15", "1995-03-20", "1995-03-25"]
        ],
        "workload_tags": ["stable", "analytical", "join_heavy"],
    },
    {
        "id": "q5",
        "name": "Local supplier volume",
        "sql": (
            "SELECT n_name, SUM(l_extendedprice * (1 - l_discount)) AS revenue "
            "FROM customer "
            "JOIN orders ON c_custkey = o_custkey "
            "JOIN lineitem ON l_orderkey = o_orderkey "
            "JOIN supplier ON l_suppkey = s_suppkey AND c_nationkey = s_nationkey "
            "JOIN nation ON s_nationkey = n_nationkey "
            "JOIN region ON n_regionkey = r_regionkey "
            "WHERE r_name = '{region_name}' "
            "AND o_orderdate >= '{year}-01-01' "
            "AND o_orderdate < '{year2}-01-01' "
            "GROUP BY n_name "
            "ORDER BY revenue DESC"
        ),
        "params": [
            {"region_name": rn, "year": y, "year2": y2}
            for rn in ["ASIA", "EUROPE", "AMERICA"]
            for y, y2 in [("1994", "1995"), ("1995", "1996")]
        ],
        "workload_tags": ["stable", "analytical", "join_heavy"],
    },
    {
        "id": "q6",
        "name": "Forecasting revenue change",
        "sql": (
            "SELECT SUM(l_extendedprice * l_discount) AS revenue "
            "FROM lineitem "
            "WHERE l_shipdate >= '{year}-01-01' "
            "AND l_shipdate < '{year2}-01-01' "
            "AND l_discount BETWEEN {disc} - 0.01 AND {disc} + 0.01 "
            "AND l_quantity < {qty}"
        ),
        "params": [
            {"year": y, "year2": y2, "disc": d, "qty": q}
            for y, y2 in [("1994", "1995"), ("1995", "1996"), ("1993", "1994")]
            for d in [0.05, 0.06, 0.07]
            for q in [24, 25]
        ],
        "workload_tags": ["stable", "analytical", "scan_heavy"],
    },
    {
        "id": "q10",
        "name": "Returned item reporting",
        "sql": (
            "SELECT c_custkey, c_name, "
            "SUM(l_extendedprice * (1 - l_discount)) AS revenue, "
            "c_acctbal, n_name, c_address, c_phone, c_comment "
            "FROM customer "
            "JOIN orders ON c_custkey = o_custkey "
            "JOIN lineitem ON l_orderkey = o_orderkey "
            "JOIN nation ON c_nationkey = n_nationkey "
            "WHERE o_orderdate >= '{year}-{month}-01' "
            "AND o_orderdate < DATE_ADD('{year}-{month}-01', INTERVAL 3 MONTH) "
            "AND l_returnflag = 'R' "
            "GROUP BY c_custkey, c_name, c_acctbal, c_phone, n_name, c_address, c_comment "
            "ORDER BY revenue DESC "
            "LIMIT 20"
        ),
        "params": [
            {"year": y, "month": m}
            for y in [1993, 1994]
            for m in ["01", "10"]
        ],
        "workload_tags": ["stable", "analytical", "join_heavy"],
    },
]


def get_random_query(tags=None, rng=None):
    if rng is None:
        rng = random
    pool = QUERIES
    if tags:
        pool = [q for q in QUERIES if any(t in q["workload_tags"] for t in tags)]
    if not pool:
        pool = QUERIES
    return rng.choice(pool)


def instantiate(query_dict, param_override=None, rng=None):
    if rng is None:
        rng = random
    params = param_override or rng.choice(query_dict["params"])
    return query_dict["sql"].format(**params)
