import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'waste_exchange.db')

def migrate():
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()

    # Add columns to users
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN company_description TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN location TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN contact_phone TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN total_ratings INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN avg_rating REAL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Add columns to waste_materials
    try:
        cursor.execute("ALTER TABLE waste_materials ADD COLUMN category TEXT DEFAULT 'Other'")
    except sqlite3.OperationalError:
        pass

    # Create new tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS material_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER NOT NULL,
            image_filename TEXT NOT NULL,
            is_primary INTEGER DEFAULT 0,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (material_id) REFERENCES waste_materials(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            reviewer_id INTEGER NOT NULL,
            seller_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            review TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (reviewer_id) REFERENCES users(id),
            FOREIGN KEY (seller_id) REFERENCES users(id)
        )
    ''')

    db.commit()
    db.close()
    print("Migration completed successfully.")

if __name__ == '__main__':
    migrate()
