import re

QUERY_TYPE_MAP = {"SELECT": 0, "INSERT": 1, "UPDATE": 2, "DELETE": 3}

def extract_features(sql, cursor):
    sql_upper = sql.upper().strip()
    first_token = sql_upper.split()[0] if sql_upper.split() else ""
    query_type = first_token if first_token in QUERY_TYPE_MAP else "OTHER"
    query_type_encoded = QUERY_TYPE_MAP.get(query_type, 4)

    num_joins = len(re.findall(r'\bJOIN\b', sql_upper))
    has_where = bool(re.search(r'\bWHERE\b', sql_upper))
    has_group_by = bool(re.search(r'\bGROUP\s+BY\b', sql_upper))
    has_order_by = bool(re.search(r'\bORDER\s+BY\b', sql_upper))

    try:
        cursor.execute(f"EXPLAIN {sql}")
        plan_rows = cursor.fetchall()
        col_names = [desc[0].lower() for desc in cursor.description]

        def col(row, name):
            idx = col_names.index(name) if name in col_names else None
            return row[idx] if idx is not None else None

        num_tables = len([r for r in plan_rows if col(r, "table") is not None])
        estimated_rows = sum((col(r, "rows") or 0) for r in plan_rows)
        estimated_cost = sum(
            (col(r, "rows") or 0) * (col(r, "filtered") or 100) / 100.0
            for r in plan_rows
        )
        uses_index = any(col(r, "key") is not None for r in plan_rows)
    except Exception:
        num_tables = 1
        estimated_rows = 0
        estimated_cost = 0.0
        uses_index = False

    return {
        "query_type": query_type,
        "query_type_encoded": query_type_encoded,
        "num_joins": num_joins,
        "num_tables": num_tables,
        "has_where": int(has_where),
        "has_group_by": int(has_group_by),
        "has_order_by": int(has_order_by),
        "estimated_rows": estimated_rows,
        "estimated_cost": estimated_cost,
        "uses_index": int(uses_index),
    }
