"""Add po_file_path and email_file_path columns to orders table."""
import sqlite3, os
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'mrp.db')
con = sqlite3.connect(db_path)
cur = con.cursor()
existing = [row[1] for row in cur.execute("PRAGMA table_info(orders)")]
for col in ['po_file_path', 'email_file_path']:
    if col not in existing:
        cur.execute(f"ALTER TABLE orders ADD COLUMN {col} VARCHAR(500)")
        print(f"Added column: {col}")
    else:
        print(f"Column already exists: {col}")
con.commit()
con.close()
print("Done.")
