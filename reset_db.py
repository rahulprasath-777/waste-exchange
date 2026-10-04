import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'waste_exchange.db')

# Delete the old database
if os.path.exists(db_path):
    os.remove(db_path)
    print("Old database deleted.")

# Clean uploads directory
uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'materials')
if os.path.exists(uploads_dir):
    for f in os.listdir(uploads_dir):
        fp = os.path.join(uploads_dir, f)
        if os.path.isfile(fp):
            os.remove(fp)
            print(f"Deleted uploaded file: {f}")
    print("Uploads cleaned.")
else:
    os.makedirs(uploads_dir, exist_ok=True)
    print("Uploads directory created.")

# Create fresh database
db = sqlite3.connect(db_path)
cursor = db.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        company_name TEXT NOT NULL,
        company_description TEXT,
        location TEXT,
        contact_phone TEXT,
        total_ratings INTEGER DEFAULT 0,
        avg_rating REAL DEFAULT 0.0,
        is_admin INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS waste_materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT DEFAULT 'Other',
        description TEXT,
        price_per_unit REAL NOT NULL,
        quantity INTEGER NOT NULL,
        unit TEXT DEFAULT 'kg',
        user_id INTEGER NOT NULL,
        company_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        buyer_id INTEGER NOT NULL,
        material_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        total_price REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (buyer_id) REFERENCES users(id),
        FOREIGN KEY (material_id) REFERENCES waste_materials(id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS material_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER NOT NULL,
        image_filename TEXT NOT NULL,
        is_primary INTEGER DEFAULT 0,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (material_id) REFERENCES waste_materials(id)
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
print("Fresh database created successfully!")
print("All users, materials, and orders have been cleared.")
