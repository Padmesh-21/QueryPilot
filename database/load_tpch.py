"""
Loads TPC-H .tbl files into the querypilot MySQL database.
Run from the project root: python database/load_tpch.py
"""
import os
import time
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

TBL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tpch-dbgen"))
SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema.sql")

# Load order matters — foreign keys must be satisfied
TABLES = [
    "region",
    "nation",
    "supplier",
    "part",
    "customer",
    "orders",
    "partsupp",
    "lineitem",
]


def get_connection(with_local_infile=False):
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        allow_local_infile=with_local_infile,
    )


def create_schema():
    print("Creating schema...")
    conn = get_connection()
    cursor = conn.cursor()
    with open(SCHEMA_FILE, "r") as f:
        sql = f.read()
    # Execute each statement separately
    for statement in sql.split(";"):
        statement = statement.strip()
        if statement:
            cursor.execute(statement)
    conn.commit()
    cursor.close()
    conn.close()
    print("Schema created.")


def enable_local_infile():
    """MySQL 8 disables local_infile by default — enable it for this session."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SET GLOBAL local_infile = 1")
    conn.commit()
    cursor.close()
    conn.close()


def load_table(table_name):
    tbl_path = os.path.join(TBL_DIR, f"{table_name}.tbl")
    # Use forward slashes — MySQL requires them even on Windows
    tbl_path_mysql = tbl_path.replace("\\", "/")

    load_sql = f"""
        LOAD DATA LOCAL INFILE '{tbl_path_mysql}'
        INTO TABLE {table_name}
        FIELDS TERMINATED BY '|'
        LINES TERMINATED BY '\\n'
        -- absorb trailing pipe by ignoring last empty column
    """
    # The .tbl files have a trailing | on each line, producing an extra empty field.
    # We handle this by listing columns explicitly (omitting the phantom last column).
    column_map = {
        "region":    "(r_regionkey, r_name, r_comment, @dummy)",
        "nation":    "(n_nationkey, n_name, n_regionkey, n_comment, @dummy)",
        "supplier":  "(s_suppkey, s_name, s_address, s_nationkey, s_phone, s_acctbal, s_comment, @dummy)",
        "part":      "(p_partkey, p_name, p_mfgr, p_brand, p_type, p_size, p_container, p_retailprice, p_comment, @dummy)",
        "customer":  "(c_custkey, c_name, c_address, c_nationkey, c_phone, c_acctbal, c_mktsegment, c_comment, @dummy)",
        "orders":    "(o_orderkey, o_custkey, o_orderstatus, o_totalprice, o_orderdate, o_orderpriority, o_clerk, o_shippriority, o_comment, @dummy)",
        "partsupp":  "(ps_partkey, ps_suppkey, ps_availqty, ps_supplycost, ps_comment, @dummy)",
        "lineitem":  "(l_orderkey, l_partkey, l_suppkey, l_linenumber, l_quantity, l_extendedprice, l_discount, l_tax, l_returnflag, l_linestatus, l_shipdate, l_commitdate, l_receiptdate, l_shipinstruct, l_shipmode, l_comment, @dummy)",
    }

    load_sql = f"""
        LOAD DATA LOCAL INFILE '{tbl_path_mysql}'
        INTO TABLE {table_name}
        FIELDS TERMINATED BY '|'
        LINES TERMINATED BY '\\n'
        {column_map[table_name]}
    """

    conn = get_connection(with_local_infile=True)
    cursor = conn.cursor()
    start = time.time()
    cursor.execute(load_sql)
    conn.commit()
    elapsed = time.time() - start
    rows = cursor.rowcount
    cursor.close()
    conn.close()
    print(f"  {table_name}: {rows:,} rows loaded in {elapsed:.1f}s")


def verify():
    print("\nVerifying row counts:")
    conn = get_connection()
    cursor = conn.cursor()
    for table in TABLES:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count:,}")
    cursor.close()
    conn.close()


if __name__ == "__main__":
    enable_local_infile()
    create_schema()
    print("\nLoading tables...")
    for table in TABLES:
        load_table(table)
    verify()
    print("\nDone. TPC-H loaded successfully.")
