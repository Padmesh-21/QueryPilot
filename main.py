from database.connection import get_connection

def test_connection():
    try:
        conn = get_connection()
        print("Connected to MySQL successfully.")
        print(f"MySQL version: {conn.server_info}")
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

def demo_sage():
    from database.connection import get_connection
    from sage.controller import SAGEController

    conn = get_connection()
    cursor = conn.cursor()
    sage = SAGEController()

    sql = "SELECT COUNT(*) FROM nation"
    result = sage.execute(sql, cursor)
    print(f"Decision: {result['decision']}")
    print(f"Reason: {result['reason']}")
    print(f"Time: {result['execution_time_ms']} ms")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    test_connection()
