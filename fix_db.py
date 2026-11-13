import sqlite3

def fix_db():
    conn = sqlite3.connect('database/ogong.db')
    conn.execute('PRAGMA foreign_keys = OFF;')
    
    # Create the new table without the check constraint
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_movements_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
            type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            reference TEXT,
            user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Copy data over
    conn.execute("""
        INSERT INTO stock_movements_new (id, product_id, type, quantity, reference, user_id, created_at)
        SELECT id, product_id, type, quantity, reference, user_id, created_at FROM stock_movements;
    """)
    
    # Drop old table
    conn.execute("DROP TABLE stock_movements;")
    
    # Rename new table to old table
    conn.execute("ALTER TABLE stock_movements_new RENAME TO stock_movements;")
    
    # Recreate indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements (product_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_user ON stock_movements (user_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements (created_at);")
    
    conn.commit()
    conn.close()
    print("Database fixed successfully.")

if __name__ == '__main__':
    fix_db()
