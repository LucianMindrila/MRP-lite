"""Migrate delivery_notes: make order_id nullable, add customer_id."""
import sqlite3, os
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'mrp.db')
con = sqlite3.connect(db_path)
cur = con.cursor()

# Check if already migrated
cols = [r[1] for r in cur.execute("PRAGMA table_info(delivery_notes)")]
if 'customer_id' in cols:
    print("Already migrated.")
    con.close()
    exit()

cur.executescript("""
BEGIN TRANSACTION;

CREATE TABLE delivery_notes_new (
    id          INTEGER NOT NULL PRIMARY KEY,
    dn_ref      VARCHAR(20) NOT NULL UNIQUE,
    order_id    INTEGER REFERENCES orders(id),
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    dispatch_date DATE NOT NULL,
    notes       TEXT,
    created_at  DATETIME
);

INSERT INTO delivery_notes_new (id, dn_ref, order_id, customer_id, dispatch_date, notes, created_at)
SELECT dn.id, dn.dn_ref, dn.order_id, o.customer_id,
       dn.dispatch_date, dn.notes, dn.created_at
FROM delivery_notes dn
JOIN orders o ON dn.order_id = o.id;

DROP TABLE delivery_notes;
ALTER TABLE delivery_notes_new RENAME TO delivery_notes;

COMMIT;
""")
con.close()
print("Migration complete.")
