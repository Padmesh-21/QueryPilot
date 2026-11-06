import time
from database.connection import get_connection

def execute_query(sql):
    conn = get_connection()
    cursor = conn.cursor()

    start = time.perf_counter()
    cursor.execute(sql)
    results = cursor.fetchall()
    end = time.perf_counter()

    execution_time_ms = (end - start) * 1000

    cursor.close()
    conn.close()

    return {
        "results": results,
        "execution_time_ms": round(execution_time_ms, 3),
    }
