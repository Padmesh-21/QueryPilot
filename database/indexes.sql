USE querypilot;

-- Orders
CREATE INDEX idx_orders_custkey    ON orders(o_custkey);
CREATE INDEX idx_orders_orderdate  ON orders(o_orderdate);

-- Lineitem
CREATE INDEX idx_lineitem_orderkey ON lineitem(l_orderkey);
CREATE INDEX idx_lineitem_shipdate ON lineitem(l_shipdate);
CREATE INDEX idx_lineitem_partkey  ON lineitem(l_partkey);

-- Customer
CREATE INDEX idx_customer_nationkey  ON customer(c_nationkey);
CREATE INDEX idx_customer_mktsegment ON customer(c_mktsegment);

-- Supplier
CREATE INDEX idx_supplier_nationkey ON supplier(s_nationkey);

-- Nation
CREATE INDEX idx_nation_regionkey ON nation(n_regionkey);
