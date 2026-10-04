from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import io
from datetime import datetime
from functools import wraps
from PIL import Image

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'waste-exchange-secret-key-2024')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['DATABASE'] = os.path.join(BASE_DIR, 'waste_exchange.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGES_PER_MATERIAL = 5
CATEGORIES = ['Metal', 'Plastic', 'Paper', 'Glass', 'Electronic', 'Chemical', 'Other']

os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'materials'), exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def compress_image(image_file, max_width=1200, max_height=1200):
    img = Image.open(image_file)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=85, optimize=True)
    output.seek(0)
    return output


# ==================== DATABASE FUNCTIONS ====================

def get_db():
    """Get database connection"""
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db


def init_db():
    """Initialize database with tables"""
    db = get_db()
    cursor = db.cursor()

    # Users table
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

    # Waste materials table
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

    # Orders table
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

    # Material Images table
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

    # Reviews table
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


def run_migration():
    """Add any missing columns to existing database"""
    db = get_db()
    cursor = db.cursor()

    migrations = [
        "ALTER TABLE users ADD COLUMN company_description TEXT",
        "ALTER TABLE users ADD COLUMN location TEXT",
        "ALTER TABLE users ADD COLUMN contact_phone TEXT",
        "ALTER TABLE users ADD COLUMN total_ratings INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN avg_rating REAL DEFAULT 0.0",
        "ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0",
        "ALTER TABLE waste_materials ADD COLUMN category TEXT DEFAULT 'Other'",
    ]

    for sql in migrations:
        try:
            cursor.execute(sql)
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Create new tables if missing
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


# ==================== AUTHENTICATION ====================

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('login'))
        db = get_db()
        user = db.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        db.close()
        if not user or not user['is_admin']:
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== PUBLIC ROUTES ====================

@app.route('/')
def index():
    """Home page"""
    db = get_db()
    materials = db.execute('''
        SELECT m.*, i.image_filename
        FROM waste_materials m
        LEFT JOIN material_images i ON m.id = i.material_id AND i.is_primary = 1
        ORDER BY m.created_at DESC LIMIT 10
    ''').fetchall()
    db.close()
    return render_template('index.html', materials=materials)


@app.route('/search')
def search():
    """Advanced Search"""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    min_price = request.args.get('min_price', '').strip()
    max_price = request.args.get('max_price', '').strip()
    min_qty = request.args.get('min_qty', '').strip()
    sort = request.args.get('sort', 'newest').strip()

    sql = '''
        SELECT m.*, i.image_filename
        FROM waste_materials m
        LEFT JOIN material_images i ON m.id = i.material_id AND i.is_primary = 1
        WHERE 1=1
    '''
    params = []

    if query:
        sql += ' AND (m.name LIKE ? OR m.description LIKE ?)'
        params.extend(['%' + query + '%', '%' + query + '%'])
    if category:
        sql += ' AND m.category = ?'
        params.append(category)
    if min_price:
        try:
            sql += ' AND m.price_per_unit >= ?'
            params.append(float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            sql += ' AND m.price_per_unit <= ?'
            params.append(float(max_price))
        except ValueError:
            pass
    if min_qty:
        try:
            sql += ' AND m.quantity >= ?'
            params.append(int(min_qty))
        except ValueError:
            pass

    if sort == 'oldest':
        sql += ' ORDER BY m.created_at ASC'
    elif sort == 'price_low':
        sql += ' ORDER BY m.price_per_unit ASC'
    elif sort == 'price_high':
        sql += ' ORDER BY m.price_per_unit DESC'
    else:
        sql += ' ORDER BY m.created_at DESC'

    db = get_db()
    materials = db.execute(sql, params).fetchall()
    db.close()

    return render_template('search.html',
                           materials=materials,
                           categories=CATEGORIES,
                           search_query=query,
                           selected_category=category)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        company_name = request.form['company_name'].strip()

        error = None

        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif not company_name:
            error = 'Company name is required.'

        if error is None:
            db = get_db()
            try:
                db.execute(
                    'INSERT INTO users (username, email, password_hash, company_name) VALUES (?, ?, ?, ?)',
                    (username, email, generate_password_hash(password), company_name)
                )
                db.commit()
                db.close()
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                db.close()
                error = 'Username or email already registered.'

        flash(error, 'error')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        db = get_db()
        error = None
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        db.close()

        if user is None:
            error = 'Username not found.'
        elif not check_password_hash(user['password_hash'], password):
            error = 'Invalid password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['company_name'] = user['company_name']
            session['is_admin'] = bool(user['is_admin'])
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))

        flash(error, 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))


# ==================== MAIN FEATURES ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """View all waste materials"""
    db = get_db()
    materials = db.execute('''
        SELECT m.*, i.image_filename
        FROM waste_materials m
        LEFT JOIN material_images i ON m.id = i.material_id AND i.is_primary = 1
        ORDER BY m.created_at DESC
    ''').fetchall()
    db.close()
    return render_template('dashboard.html', materials=materials)


@app.route('/my-materials')
@login_required
def my_materials():
    """View user's own waste materials"""
    db = get_db()
    materials = db.execute('''
        SELECT m.*, i.image_filename
        FROM waste_materials m
        LEFT JOIN material_images i ON m.id = i.material_id AND i.is_primary = 1
        WHERE m.user_id = ?
        ORDER BY m.created_at DESC
    ''', (session['user_id'],)).fetchall()
    db.close()
    return render_template('my_materials.html', materials=materials)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_material():
    """Upload a waste material"""
    if request.method == 'POST':
        name = request.form['name'].strip()
        category = request.form.get('category', 'Other')
        description = request.form.get('description', '').strip()
        price = request.form['price']
        quantity = request.form['quantity']
        unit = request.form['unit']

        error = None

        if not name:
            error = 'Material name is required.'
        elif not price:
            error = 'Price is required.'
        elif not quantity:
            error = 'Quantity is required.'

        if error is None:
            try:
                db = get_db()
                cursor = db.cursor()
                cursor.execute(
                    '''INSERT INTO waste_materials
                       (name, category, description, price_per_unit, quantity, unit, user_id, company_name)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (name, category, description, float(price), int(quantity), unit,
                     session['user_id'], session['company_name'])
                )
                material_id = cursor.lastrowid

                # Handle images
                images = request.files.getlist('images')
                valid_images = [img for img in images if img and img.filename and allowed_file(img.filename)]

                for i, file in enumerate(valid_images[:MAX_IMAGES_PER_MATERIAL]):
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                    filename = f"material_{material_id}_{timestamp}.jpg"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'materials', filename)
                    compressed = compress_image(file)

                    with open(filepath, 'wb') as f:
                        f.write(compressed.read())

                    is_primary = 1 if i == 0 else 0
                    cursor.execute(
                        'INSERT INTO material_images (material_id, image_filename, is_primary) VALUES (?, ?, ?)',
                        (material_id, filename, is_primary)
                    )

                db.commit()
                db.close()
                flash('Material uploaded successfully!', 'success')
                return redirect(url_for('my_materials'))
            except Exception as e:
                flash(f'Error uploading material: {str(e)}', 'error')

        else:
            flash(error, 'error')

    return render_template('upload_material_with_photos.html', categories=CATEGORIES)


@app.route('/material/<int:material_id>')
def view_material(material_id):
    """View material details"""
    db = get_db()
    material = db.execute(
        'SELECT * FROM waste_materials WHERE id = ?', (material_id,)
    ).fetchone()

    if material is None:
        db.close()
        flash('Material not found', 'error')
        return redirect(url_for('index'))

    images = db.execute(
        'SELECT * FROM material_images WHERE material_id = ? ORDER BY is_primary DESC, uploaded_at ASC',
        (material_id,)
    ).fetchall()
    db.close()

    return render_template('view_material_with_photos.html', material=material, images=images)


@app.route('/edit-material/<int:material_id>', methods=['GET', 'POST'])
@login_required
def edit_material(material_id):
    """Edit a waste material"""
    db = get_db()
    material = db.execute(
        'SELECT * FROM waste_materials WHERE id = ?', (material_id,)
    ).fetchone()

    if material is None or material['user_id'] != session['user_id']:
        db.close()
        flash('Unauthorized action', 'error')
        return redirect(url_for('my_materials'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        category = request.form.get('category', 'Other')
        description = request.form.get('description', '').strip()
        price = request.form['price']
        quantity = request.form['quantity']
        unit = request.form['unit']

        error = None
        if not name:
            error = 'Material name is required.'
        elif not price:
            error = 'Price is required.'
        elif not quantity:
            error = 'Quantity is required.'

        if error is None:
            db.execute(
                '''UPDATE waste_materials
                   SET name=?, category=?, description=?, price_per_unit=?, quantity=?, unit=?
                   WHERE id=?''',
                (name, category, description, float(price), int(quantity), unit, material_id)
            )
            db.commit()
            db.close()
            flash('Material updated successfully!', 'success')
            return redirect(url_for('my_materials'))

        flash(error, 'error')

    db.close()
    return render_template('edit_material.html', material=material)


@app.route('/order/<int:material_id>', methods=['GET', 'POST'])
@login_required
def order_material(material_id):
    """Place an order for waste material"""
    db = get_db()
    material = db.execute(
        'SELECT * FROM waste_materials WHERE id = ?', (material_id,)
    ).fetchone()

    if material is None:
        db.close()
        flash('Material not found', 'error')
        return redirect(url_for('dashboard'))

    if session['user_id'] == material['user_id']:
        db.close()
        flash('You cannot order your own material', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        quantity = request.form['quantity']
        error = None

        try:
            qty = int(quantity)
        except ValueError:
            qty = 0

        if not qty or qty <= 0:
            error = 'Invalid quantity.'
        elif qty > material['quantity']:
            error = f'Only {material["quantity"]} units available.'

        if error is None:
            total_price = qty * material['price_per_unit']
            db.execute(
                '''INSERT INTO orders (buyer_id, material_id, quantity, total_price, status)
                   VALUES (?, ?, ?, ?, ?)''',
                (session['user_id'], material_id, qty, total_price, 'pending')
            )
            new_quantity = material['quantity'] - qty
            db.execute(
                'UPDATE waste_materials SET quantity = ? WHERE id = ?',
                (new_quantity, material_id)
            )
            db.commit()
            db.close()
            flash('Order placed successfully! Status: Pending', 'success')
            return redirect(url_for('my_orders'))

        flash(error, 'error')

    db.close()
    return render_template('order_material.html', material=material)


@app.route('/my-orders')
@login_required
def my_orders():
    """View user's orders"""
    db = get_db()
    orders = db.execute(
        '''SELECT o.*, m.name, m.price_per_unit, u.company_name as seller_company,
                  r.id as review_id
           FROM orders o
           JOIN waste_materials m ON o.material_id = m.id
           JOIN users u ON m.user_id = u.id
           LEFT JOIN reviews r ON r.order_id = o.id
           WHERE o.buyer_id = ?
           ORDER BY o.created_at DESC''',
        (session['user_id'],)
    ).fetchall()
    db.close()
    return render_template('my_orders.html', orders=orders)


@app.route('/received-orders')
@login_required
def received_orders():
    """View orders received by user"""
    db = get_db()
    orders = db.execute(
        '''SELECT o.*, m.name, m.price_per_unit, u.username, u.company_name
           FROM orders o
           JOIN waste_materials m ON o.material_id = m.id
           JOIN users u ON o.buyer_id = u.id
           WHERE m.user_id = ?
           ORDER BY o.created_at DESC''',
        (session['user_id'],)
    ).fetchall()
    db.close()
    return render_template('received_orders.html', orders=orders)


@app.route('/update-order-status/<int:order_id>/<status>')
@login_required
def update_order_status(order_id, status):
    """Update order status"""
    if status not in ['pending', 'approved', 'rejected', 'completed']:
        flash('Invalid status', 'error')
        return redirect(url_for('received_orders'))

    db = get_db()
    order = db.execute(
        '''SELECT o.*, m.user_id FROM orders o
           JOIN waste_materials m ON o.material_id = m.id
           WHERE o.id = ?''',
        (order_id,)
    ).fetchone()

    if order is None:
        db.close()
        flash('Order not found', 'error')
        return redirect(url_for('dashboard'))

    if order['user_id'] != session['user_id']:
        db.close()
        flash('Unauthorized action', 'error')
        return redirect(url_for('dashboard'))

    db.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
    db.commit()
    db.close()
    flash(f'Order status updated to {status}', 'success')
    return redirect(url_for('received_orders'))


@app.route('/rate-order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def rate_order(order_id):
    """Rate a completed order"""
    db = get_db()
    order = db.execute(
        '''SELECT o.*, m.name, m.user_id as seller_id
           FROM orders o
           JOIN waste_materials m ON o.material_id = m.id
           WHERE o.id = ? AND o.buyer_id = ? AND o.status = 'completed' ''',
        (order_id, session['user_id'])
    ).fetchone()

    if order is None:
        db.close()
        flash('Order not found or not eligible for rating', 'error')
        return redirect(url_for('my_orders'))

    # Check if already rated
    existing_review = db.execute(
        'SELECT id FROM reviews WHERE order_id = ?', (order_id,)
    ).fetchone()

    if existing_review:
        db.close()
        flash('You have already rated this order', 'error')
        return redirect(url_for('my_orders'))

    if request.method == 'POST':
        rating = request.form.get('rating')
        review_text = request.form.get('review', '').strip()

        if not rating:
            flash('Please select a rating', 'error')
        else:
            rating = int(rating)
            seller_id = order['seller_id']

            db.execute(
                '''INSERT INTO reviews (order_id, reviewer_id, seller_id, rating, review)
                   VALUES (?, ?, ?, ?, ?)''',
                (order_id, session['user_id'], seller_id, rating, review_text)
            )

            # Update seller's avg rating
            avg = db.execute(
                'SELECT AVG(rating) as avg, COUNT(*) as cnt FROM reviews WHERE seller_id = ?',
                (seller_id,)
            ).fetchone()
            db.execute(
                'UPDATE users SET avg_rating = ?, total_ratings = ? WHERE id = ?',
                (avg['avg'], avg['cnt'], seller_id)
            )

            db.commit()
            db.close()
            flash('Rating submitted successfully!', 'success')
            return redirect(url_for('my_orders'))

    db.close()
    return render_template('rate_order.html', order=order)


@app.route('/delete-material/<int:material_id>')
@login_required
def delete_material(material_id):
    """Delete a waste material"""
    db = get_db()
    material = db.execute(
        'SELECT user_id FROM waste_materials WHERE id = ?', (material_id,)
    ).fetchone()

    if material is None or material['user_id'] != session['user_id']:
        db.close()
        flash('Unauthorized action', 'error')
        return redirect(url_for('dashboard'))

    # Delete associated images from disk
    images = db.execute(
        'SELECT image_filename FROM material_images WHERE material_id = ?', (material_id,)
    ).fetchall()
    for img in images:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'materials', img['image_filename'])
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass

    db.execute('DELETE FROM material_images WHERE material_id = ?', (material_id,))
    db.execute('DELETE FROM waste_materials WHERE id = ?', (material_id,))
    db.commit()
    db.close()

    flash('Material deleted successfully', 'success')
    return redirect(url_for('my_materials'))


# ==================== USER PROFILE ====================

@app.route('/profile/<int:user_id>')
def profile(user_id):
    """View user profile"""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if user is None:
        db.close()
        flash('User not found', 'error')
        return redirect(url_for('index'))

    materials = db.execute(
        '''SELECT m.*, i.image_filename
           FROM waste_materials m
           LEFT JOIN material_images i ON m.id = i.material_id AND i.is_primary = 1
           WHERE m.user_id = ?
           ORDER BY m.created_at DESC LIMIT 6''',
        (user_id,)
    ).fetchall()

    ratings = db.execute(
        '''SELECT r.*, u.username as buyer_name
           FROM reviews r
           JOIN users u ON r.reviewer_id = u.id
           WHERE r.seller_id = ?
           ORDER BY r.created_at DESC''',
        (user_id,)
    ).fetchall()

    order_row = db.execute(
        '''SELECT COUNT(*) as cnt FROM orders o
           JOIN waste_materials m ON o.material_id = m.id
           WHERE m.user_id = ? AND o.status = 'completed' ''',
        (user_id,)
    ).fetchone()
    order_count = order_row['cnt'] if order_row else 0

    db.close()
    return render_template('profile.html', user=user, materials=materials,
                           ratings=ratings, order_count=order_count)


@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    if request.method == 'POST':
        company_description = request.form.get('company_description', '').strip()
        location = request.form.get('location', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()

        db.execute(
            '''UPDATE users SET company_description=?, location=?, contact_phone=?
               WHERE id=?''',
            (company_description, location, contact_phone, session['user_id'])
        )
        db.commit()
        db.close()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile', user_id=session['user_id']))

    db.close()
    return render_template('edit_profile.html', user=user)


# ==================== ADMIN ====================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    db = get_db()

    stats = {
        'total_users': db.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'total_materials': db.execute('SELECT COUNT(*) FROM waste_materials').fetchone()[0],
        'total_orders': db.execute('SELECT COUNT(*) FROM orders').fetchone()[0],
        'pending_orders': db.execute("SELECT COUNT(*) FROM orders WHERE status='pending'").fetchone()[0],
        'completed_orders': db.execute("SELECT COUNT(*) FROM orders WHERE status='completed'").fetchone()[0],
        'total_value': db.execute('SELECT COALESCE(SUM(total_price), 0) FROM orders').fetchone()[0],
    }

    top_sellers = db.execute(
        '''SELECT u.id, u.company_name, u.avg_rating,
                  COUNT(o.id) as order_count
           FROM users u
           LEFT JOIN waste_materials m ON m.user_id = u.id
           LEFT JOIN orders o ON o.material_id = m.id AND o.status = 'completed'
           GROUP BY u.id
           ORDER BY order_count DESC LIMIT 10'''
    ).fetchall()

    recent_orders = db.execute(
        '''SELECT o.*, m.name, u.company_name
           FROM orders o
           JOIN waste_materials m ON o.material_id = m.id
           JOIN users u ON o.buyer_id = u.id
           ORDER BY o.created_at DESC LIMIT 20'''
    ).fetchall()

    db.close()
    return render_template('admin_dashboard.html', stats=stats,
                           top_sellers=top_sellers, recent_orders=recent_orders)


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500


if __name__ == '__main__':
    if os.path.exists(app.config['DATABASE']):
        run_migration()
    else:
        init_db()

    app.run(debug=True, port=5000)
