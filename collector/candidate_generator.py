import re


def _get_first_table(sql, cursor):
    try:
        cursor.execute(f"EXPLAIN {sql}")
        rows = cursor.fetchall()
        col_names = [desc[0].lower() for desc in cursor.description]
        table_idx = col_names.index("table") if "table" in col_names else None
        if table_idx is not None:
            for row in rows:
                t = row[table_idx]
                if t:
                    return t
    except Exception:
        pass
    return None


def _inject_hint(sql, hint):
    match = re.match(r'^\s*(SELECT)\s+', sql, re.IGNORECASE)
    if match:
        return sql[:match.end(1)] + f" /*+ {hint} */" + sql[match.end(1):]
    return sql


def generate_candidates(sql, cursor):
    candidates = [
        {"candidate_id": 0, "sql": sql, "description": "Native MySQL optimizer", "hint_type": "native"}
    ]

    sql_upper = sql.upper()
    has_joins = bool(re.search(r'\bJOIN\b', sql_upper))
    first_table = _get_first_table(sql, cursor)

    if first_table:
        candidates.append({
            "candidate_id": len(candidates),
            "sql": _inject_hint(sql, f"NO_INDEX({first_table})"),
            "description": f"Disable index on {first_table}",
            "hint_type": "no_index",
        })

    if has_joins and first_table:
        join_tables = re.findall(r'\bJOIN\s+(\w+)', sql, re.IGNORECASE)
        if join_tables:
            t2 = join_tables[0]
            candidates.append({
                "candidate_id": len(candidates),
                "sql": _inject_hint(sql, f"HASH_JOIN({first_table} {t2})"),
                "description": f"Force hash join between {first_table} and {t2}",
                "hint_type": "hash_join",
            })

        candidates.append({
            "candidate_id": len(candidates),
            "sql": _inject_hint(sql, f"NO_BKA({first_table})"),
            "description": f"Disable BKA on {first_table}",
            "hint_type": "no_bka",
        })

    return candidates[:4]
