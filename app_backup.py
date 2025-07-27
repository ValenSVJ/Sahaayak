from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import uuid
import json

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, environment variables should be set manually
    pass

app = Flask(__name__)

# Security Configuration - Enhanced security setup
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')  # Change this in production
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyDyYEw7SLwswMtutVhtUy0zI2bvaf_SIdU')

# App configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Make API key available to templates (optional - for client-side usage)
@app.context_processor
def inject_api_key():
    return dict(GEMINI_API_KEY=GEMINI_API_KEY)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database setup
def init_db():
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    
    # Vendors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            password TEXT,
            location TEXT,
            is_approved BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Wholesalers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wholesalers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            shop_name TEXT NOT NULL,
            id_doc_path TEXT,
            license_doc_path TEXT,
            sourcing_info TEXT,
            location TEXT,
            is_approved BOOLEAN DEFAULT FALSE,
            trust_score REAL DEFAULT 4.7,
            response_rate REAL DEFAULT 95.0,
            delivery_rate REAL DEFAULT 92.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wholesaler_id INTEGER,
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            group_buy_eligible BOOLEAN DEFAULT TRUE,
            image_path TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            status TEXT DEFAULT 'In Stock',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (wholesaler_id) REFERENCES wholesalers (id)
        )
    ''')
    
    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wholesaler_id INTEGER,
            vendor_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            total_amount REAL,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (wholesaler_id) REFERENCES wholesalers (id),
            FOREIGN KEY (vendor_id) REFERENCES vendors (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Reviews table with reply column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wholesaler_id INTEGER,
            vendor_id INTEGER,
            rating INTEGER,
            comment TEXT,
            reply TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (wholesaler_id) REFERENCES wholesalers (id),
            FOREIGN KEY (vendor_id) REFERENCES vendors (id)
        )
    ''')
    
    # Analytics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wholesaler_id INTEGER,
            date DATE,
            total_orders INTEGER DEFAULT 0,
            total_revenue REAL DEFAULT 0,
            active_customers INTEGER DEFAULT 0,
            FOREIGN KEY (wholesaler_id) REFERENCES wholesalers (id)
        )
    ''')
    
    # Check if reply column exists in reviews table, if not add it
    cursor.execute("PRAGMA table_info(reviews)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'reply' not in columns:
        cursor.execute('ALTER TABLE reviews ADD COLUMN reply TEXT')
    
    # Insert sample data if empty
    cursor.execute('SELECT COUNT(*) FROM vendors')
    if cursor.fetchone()[0] == 0:
        # Sample vendors
        vendors_data = [
            ('Raj Patel', 'raj@example.com', '9876543210', 'vendor123', 'Ghatkopar', 1),
            ('Priya Shah', 'priya@example.com', '9876543211', 'vendor123', 'Ghatkopar', 1),
            ('Amit Kumar', 'amit@example.com', '9876543212', 'vendor123', 'Ghatkopar', 1),
            ('Sunita Devi', 'sunita@example.com', '9876543213', 'vendor123', 'Andheri', 1),
            ('Ravi Singh', 'ravi@example.com', '9876543214', 'vendor123', 'Andheri', 1),
        ]
        cursor.executemany('INSERT INTO vendors (name, email, phone, password, location, is_approved) VALUES (?, ?, ?, ?, ?, ?)', vendors_data)
        
        # Sample wholesaler
        cursor.execute('''
            INSERT INTO wholesalers (name, phone, password, shop_name, sourcing_info, location, is_approved, trust_score, response_rate, delivery_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('Mumbai Fresh Mart', '9999999999', 'password123', 'Fresh Mart Wholesale', 'Quality products from local farms', 'Ghatkopar', 1, 4.7, 95.0, 92.0))
        
        wholesaler_id = cursor.lastrowid
        
        # Sample products
        products_data = [
            (wholesaler_id, 'Organic Tomatoes', 'Vegetables', 45.0, 500, 1, None, 234, 12, 'In Stock'),
            (wholesaler_id, 'Fresh Spinach', 'Vegetables', 25.0, 200, 1, None, 156, 8, 'Low Stock'),
            (wholesaler_id, 'Premium Carrots', 'Vegetables', 35.0, 0, 1, None, 89, 5, 'Out of Stock'),
            (wholesaler_id, 'Red Onions', 'Vegetables', 30.0, 300, 1, None, 312, 18, 'In Stock'),
            (wholesaler_id, 'Basmati Rice', 'Grains & Cereals', 85.0, 150, 1, None, 445, 25, 'In Stock'),
        ]
        cursor.executemany('INSERT INTO products (wholesaler_id, name, category, price, stock, group_buy_eligible, image_path, views, likes, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', products_data)
        
        # Sample orders
        orders_data = [
            (wholesaler_id, 1, 1, 50, 2250.0, 'pending'),
            (wholesaler_id, 2, 2, 30, 750.0, 'completed'),
            (wholesaler_id, 3, 4, 25, 750.0, 'pending'),
            (wholesaler_id, 4, 1, 40, 1200.0, 'processing'),
            (wholesaler_id, 5, 5, 20, 1700.0, 'completed'),
            (wholesaler_id, 1, 3, 35, 1575.0, 'pending'),
            (wholesaler_id, 2, 4, 15, 375.0, 'pending'),
            (wholesaler_id, 5, 2, 10, 850.0, 'processing'),
        ]
        cursor.executemany('INSERT INTO orders (wholesaler_id, vendor_id, product_id, quantity, total_amount, status) VALUES (?, ?, ?, ?, ?, ?)', orders_data)
        
        # Sample reviews with replies
        reviews_data = [
            (wholesaler_id, 1, 5, 'Excellent quality vegetables, always fresh and delivered on time.', None),
            (wholesaler_id, 2, 4, 'Good products and reliable supplier. Competitive pricing.', 'Thank you for your feedback!'),
            (wholesaler_id, 3, 5, 'Outstanding service! Best wholesaler in the area.', None),
            (wholesaler_id, 4, 4, 'Quality products, but delivery could be faster.', 'We are working on improving delivery times.'),
        ]
        cursor.executemany('INSERT INTO reviews (wholesaler_id, vendor_id, rating, comment, reply) VALUES (?, ?, ?, ?, ?)', reviews_data)
        
        # Sample analytics data
        today = datetime.now()
        analytics_data = []
        for i in range(30):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            orders = 15 + (i % 10)
            revenue = float(orders * 850.0)  # Ensure float
            customers = 8 + (i % 5)
            analytics_data.append((wholesaler_id, date, orders, revenue, customers))
        
        cursor.executemany('INSERT INTO analytics (wholesaler_id, date, total_orders, total_revenue, active_customers) VALUES (?, ?, ?, ?, ?)', analytics_data)
    
    conn.commit()
    conn.close()
    
    # Update database schema to add any missing columns
    update_database_schema()

def get_dashboard_stats(wholesaler_id):
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    
    # Get total products
    cursor.execute('SELECT COUNT(*) FROM products WHERE wholesaler_id = ?', (wholesaler_id,))
    total_products = cursor.fetchone()[0]
    
    # Get pending orders
    cursor.execute('SELECT COUNT(*) FROM orders WHERE wholesaler_id = ? AND status = "pending"', (wholesaler_id,))
    pending_orders = cursor.fetchone()[0]
    
    # Get this month's revenue from completed orders
    current_month = datetime.now().strftime('%Y-%m')
    cursor.execute('''
        SELECT COALESCE(SUM(total_amount), 0) FROM orders 
        WHERE wholesaler_id = ? AND created_at LIKE ? AND status = "completed"
    ''', (wholesaler_id, f'{current_month}%'))
    month_revenue = cursor.fetchone()[0] or 0
    
    # Get active customers (vendors who ordered this month)
    cursor.execute('''
        SELECT COUNT(DISTINCT vendor_id) FROM orders 
        WHERE wholesaler_id = ? AND created_at >= date('now', 'start of month')
    ''', (wholesaler_id,))
    active_customers = cursor.fetchone()[0]
    
    # Get wholesaler performance data
    cursor.execute('SELECT trust_score, response_rate, delivery_rate FROM wholesalers WHERE id = ?', (wholesaler_id,))
    performance = cursor.fetchone()
    
    conn.close()
    
    return {
        'total_products': total_products,
        'pending_orders': pending_orders,
        'month_revenue': float(month_revenue),  # Ensure float
        'active_customers': active_customers,
        'trust_score': performance[0] if performance else 4.7,
        'response_rate': performance[1] if performance else 95.0,
        'delivery_rate': performance[2] if performance else 92.0
    }

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# Wholesaler Registration
@app.route('/register-wholesaler', methods=['GET', 'POST'])
def register_wholesaler():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        password = request.form['password']
        shop_name = request.form['shop_name']
        sourcing_info = request.form['sourcing_info']
        location = request.form['location']
        
        # Check if phone number already exists
        conn = sqlite3.connect('vendor_clubs.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM wholesalers WHERE phone = ?', (phone,))
        existing = cursor.fetchone()
        
        if existing:
            flash('Phone number already registered. Please use a different number.', 'error')
            conn.close()
            return render_template('register_wholesaler.html')
        
        # Handle file uploads
        id_doc_path = None
        license_doc_path = None
        
        if 'id_proof' in request.files:
            id_file = request.files['id_proof']
            if id_file and allowed_file(id_file.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{id_file.filename}")
                id_doc_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                id_file.save(id_doc_path)
        
        if 'license_doc' in request.files:
            license_file = request.files['license_doc']
            if license_file and allowed_file(license_file.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{license_file.filename}")
                license_doc_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                license_file.save(license_doc_path)
        
        # Save to database
        cursor.execute('''
            INSERT INTO wholesalers (name, phone, password, shop_name, id_doc_path, license_doc_path, sourcing_info, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, phone, password, shop_name, id_doc_path, license_doc_path, sourcing_info, location))
        conn.commit()
        conn.close()
        
        flash('Thank you for registering! Your application is pending approval.', 'success')
        return redirect(url_for('register_wholesaler'))
    
    return render_template('register_wholesaler.html')

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password == 'admin123':
            session['is_admin'] = True
            return redirect(url_for('admin_wholesalers'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

@app.route('/admin/wholesalers')
def admin_wholesalers():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM wholesalers WHERE is_approved = 0')
    pending_wholesalers = cursor.fetchall()
    conn.close()
    
    return render_template('admin_wholesalers.html', wholesalers=pending_wholesalers)

@app.route('/admin/approve/<int:wholesaler_id>')
def approve_wholesaler(wholesaler_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE wholesalers SET is_approved = 1 WHERE id = ?', (wholesaler_id,))
    conn.commit()
    conn.close()
    
    flash('Wholesaler approved successfully!', 'success')
    return redirect(url_for('admin_wholesalers'))

@app.route('/admin/reject/<int:wholesaler_id>')
def reject_wholesaler(wholesaler_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM wholesalers WHERE id = ?', (wholesaler_id,))
    conn.commit()
    conn.close()
    
    flash('Wholesaler application rejected and removed.', 'success')
    return redirect(url_for('admin_wholesalers'))

# Wholesaler Routes
@app.route('/wholesaler/login', methods=['GET', 'POST'])
def wholesaler_login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        
        conn = sqlite3.connect('vendor_clubs.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, is_approved, password FROM wholesalers WHERE phone = ?', (phone,))
        wholesaler = cursor.fetchone()
        conn.close()
        
        if wholesaler:
            if wholesaler[3] == password:  # Check password
                if wholesaler[2]:  # is_approved
                    session['wholesaler_id'] = wholesaler[0]
                    session['wholesaler_name'] = wholesaler[1]
                    return redirect(url_for('wholesaler_dashboard'))
                else:
                    flash('Your application is still pending approval.', 'warning')
            else:
                flash('Invalid password. Please try again.', 'error')
        else:
            flash('Phone number not found. Please register first.', 'error')
    
    return render_template('wholesaler_login.html')

@app.route('/wholesaler/dashboard')
def wholesaler_dashboard():
    if 'wholesaler_id' not in session:
        return redirect(url_for('wholesaler_login'))
    
    wholesaler_id = session['wholesaler_id']
    stats = get_dashboard_stats(wholesaler_id)
    
    # Get recent products
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE wholesaler_id = ? ORDER BY created_at DESC LIMIT 4', (wholesaler_id,))
    recent_products = cursor.fetchall()
    
    # Get recent reviews with vendor names and replies
    cursor.execute('''
        SELECT r.id, r.rating, r.comment, r.reply, v.name, r.created_at 
        FROM reviews r 
        JOIN vendors v ON r.vendor_id = v.id 
        WHERE r.wholesaler_id = ? 
        ORDER BY r.created_at DESC LIMIT 3
    ''', (wholesaler_id,))
    recent_reviews = cursor.fetchall()
    
    conn.close()
    
    return render_template('wholesaler_dashboard.html', 
                         stats=stats, 
                         recent_products=recent_products, 
                         recent_reviews=recent_reviews)

@app.route('/wholesaler/profile')
def wholesaler_profile():
    if 'wholesaler_id' not in session:
        return redirect(url_for('wholesaler_login'))
    
    wholesaler_id = session['wholesaler_id']
    
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM wholesalers WHERE id = ?', (wholesaler_id,))
    wholesaler = cursor.fetchone()
    conn.close()
    
    if not wholesaler:
        flash('Wholesaler not found.', 'error')
        return redirect(url_for('wholesaler_login'))
    
    return render_template('wholesaler_profile.html', wholesaler=wholesaler)

@app.route('/wholesaler/products')
def wholesaler_products():
    if 'wholesaler_id' not in session:
        return redirect(url_for('wholesaler_login'))
    
    wholesaler_id = session['wholesaler_id']
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE wholesaler_id = ? ORDER BY created_at DESC', (wholesaler_id,))
    products = cursor.fetchall()
    conn.close()
    
    return render_template('products_manage.html', products=products)

@app.route('/wholesaler/orders')
def wholesaler_orders():
    if 'wholesaler_id' not in session:
        return redirect(url_for('wholesaler_login'))
    
    wholesaler_id = session['wholesaler_id']
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT o.*, v.name as vendor_name, p.name as product_name 
        FROM orders o 
        JOIN vendors v ON o.vendor_id = v.id 
        JOIN products p ON o.product_id = p.id 
        WHERE o.wholesaler_id = ? 
        ORDER BY o.created_at DESC
    ''', (wholesaler_id,))
    orders = cursor.fetchall()
    conn.close()
    
    return render_template('orders_manage.html', orders=orders)

@app.route('/wholesaler/analytics')
def wholesaler_analytics():
    if 'wholesaler_id' not in session:
        return redirect(url_for('wholesaler_login'))
    
    wholesaler_id = session['wholesaler_id']
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    
    # Get analytics data for charts
    cursor.execute('''
        SELECT date, total_orders, total_revenue, active_customers 
        FROM analytics 
        WHERE wholesaler_id = ? 
        ORDER BY date DESC LIMIT 30
    ''', (wholesaler_id,))
    analytics_data = cursor.fetchall()
    
    conn.close()
    
    return render_template('analytics.html', analytics_data=analytics_data)

@app.route('/wholesaler/add-product', methods=['GET', 'POST'])
def add_product():
    if 'wholesaler_id' not in session:
        return redirect(url_for('wholesaler_login'))
    
    if request.method == 'POST':
        name = request.form['name']
        category = request.form.get('main_category') or request.form.get('category')  # Main category (support both names)
        subcategory = request.form.get('subcategory', '')  # Specific item (not stored in DB, but available if needed)
        price = float(request.form['price'])
        stock = int(request.form['stock'])

        # Determine stock status
        if stock == 0:
            status = 'Out of Stock'
        elif stock < 50:
            status = 'Low Stock'
        else:
            status = 'In Stock'

        # Handle product image upload
        image_path = None
        if 'product_image' in request.files:
            image_file = request.files['product_image']
            if image_file and image_file.filename and allowed_file(image_file.filename):
                filename = secure_filename(f"product_{uuid.uuid4()}_{image_file.filename}")
                relative_path = f"uploads/{filename}"
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(full_path)
                image_path = relative_path

        # Save product to database
        conn = sqlite3.connect('vendor_clubs.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (wholesaler_id, name, category, price, stock, image_path, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session['wholesaler_id'], name, category, price, stock, image_path, status))
        conn.commit()
        conn.close()

        flash('Product added successfully!', 'success')
        return redirect(url_for('wholesaler_dashboard'))  # Redirect to dashboard

    return render_template('add_product.html')

@app.route('/wholesaler/edit-product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'wholesaler_id' not in session:
        return redirect(url_for('wholesaler_login'))
    
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        category = request.form.get('main_category') or request.form.get('category')  # Main category (support both names)
        subcategory = request.form.get('subcategory', '')  # Specific item (not stored in DB, but available if needed)
        price = float(request.form['price'])
        stock = int(request.form['stock'])

        # Determine stock status
        if stock == 0:
            status = 'Out of Stock'
        elif stock < 50:
            status = 'Low Stock'
        else:
            status = 'In Stock'

        # Handle image upload if new image provided
        cursor.execute('SELECT image_path FROM products WHERE id = ? AND wholesaler_id = ?', 
                      (product_id, session['wholesaler_id']))
        current_image = cursor.fetchone()[0]
        image_path = current_image

        if 'product_image' in request.files:
            image_file = request.files['product_image']
            if image_file and image_file.filename and allowed_file(image_file.filename):
                filename = secure_filename(f"product_{uuid.uuid4()}_{image_file.filename}")
                relative_path = f"uploads/{filename}"
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(full_path)
                image_path = relative_path

        # Update product
        cursor.execute('''
            UPDATE products 
            SET name = ?, category = ?, price = ?, stock = ?, status = ?, image_path = ?
            WHERE id = ? AND wholesaler_id = ?
        ''', (name, category, price, stock, status, image_path, product_id, session['wholesaler_id']))
        conn.commit()
        conn.close()

        flash('Product updated successfully!', 'success')
        return redirect(url_for('wholesaler_products'))
    
    # GET request - show edit form
    cursor.execute('SELECT * FROM products WHERE id = ? AND wholesaler_id = ?', 
                  (product_id, session['wholesaler_id']))
    product = cursor.fetchone()
    conn.close()
    
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('wholesaler_products'))
    
    return render_template('edit_product.html', product=product)

# API Routes
@app.route('/api/update-stock', methods=['POST'])
def update_stock():
    if 'wholesaler_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    product_id = data.get('product_id')
    new_stock = data.get('stock')
    
    # Determine new status
    if new_stock == 0:
        status = 'Out of Stock'
    elif new_stock < 50:
        status = 'Low Stock'
    else:
        status = 'In Stock'
    
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE products SET stock = ?, status = ? WHERE id = ? AND wholesaler_id = ?', 
                   (new_stock, status, product_id, session['wholesaler_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'status': status})

@app.route('/api/update-order-status', methods=['POST'])
def update_order_status():
    if 'wholesaler_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    order_id = data.get('order_id')
    new_status = data.get('status')
    
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET status = ? WHERE id = ? AND wholesaler_id = ?', 
                   (new_status, order_id, session['wholesaler_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/delete-product', methods=['POST'])
def delete_product():
    if 'wholesaler_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    product_id = data.get('product_id')
    
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    
    # Get image path to delete file
    cursor.execute('SELECT image_path FROM products WHERE id = ? AND wholesaler_id = ?', 
                  (product_id, session['wholesaler_id']))
    result = cursor.fetchone()
    
    if result and result[0]:
        image_path = os.path.join('static', result[0])
        if os.path.exists(image_path):
            os.remove(image_path)
    
    # Delete product
    cursor.execute('DELETE FROM products WHERE id = ? AND wholesaler_id = ?', 
                   (product_id, session['wholesaler_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/reply-review', methods=['POST'])
def reply_review():
    if 'wholesaler_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    review_id = data.get('review_id')
    reply_text = data.get('reply')
    
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE reviews SET reply = ? WHERE id = ? AND wholesaler_id = ?', 
                   (reply_text, review_id, session['wholesaler_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# First, update the database schema by adding this function
def update_database_schema():
    """Add profile_photo column to wholesalers table if it doesn't exist"""
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    
    # Check if profile_photo column exists
    cursor.execute("PRAGMA table_info(wholesalers)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'profile_photo' not in columns:
        cursor.execute('ALTER TABLE wholesalers ADD COLUMN profile_photo TEXT')
        conn.commit()
        print("✅ Added profile_photo column to wholesalers table")
    
    conn.close()

# Profile photo upload route
@app.route('/api/upload-profile-photo', methods=['POST'])
def upload_profile_photo():
    if 'wholesaler_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'profile_photo' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['profile_photo']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(f"profile_{session['wholesaler_id']}_{uuid.uuid4()}_{file.filename}")
        relative_path = f"uploads/{filename}"
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the new file
        file.save(full_path)
        
        # Update database with new profile photo path
        conn = sqlite3.connect('vendor_clubs.db')
        cursor = conn.cursor()
        
        # Get old profile photo to delete it
        cursor.execute('SELECT profile_photo FROM wholesalers WHERE id = ?', (session['wholesaler_id'],))
        old_photo = cursor.fetchone()
        
        # Update with new photo
        cursor.execute('UPDATE wholesalers SET profile_photo = ? WHERE id = ?', 
                      (relative_path, session['wholesaler_id']))
        conn.commit()
        conn.close()
        
        # Delete old profile photo if it exists
        if old_photo and old_photo[0]:
            old_path = os.path.join('static', old_photo[0])
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except:
                    pass  # If deletion fails, continue anyway
        
        return jsonify({
            'success': True, 
            'photo_url': url_for('static', filename=relative_path)
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

# Edit profile route
@app.route('/wholesaler/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'wholesaler_id' not in session:
        return redirect(url_for('wholesaler_login'))
    
    wholesaler_id = session['wholesaler_id']
    
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        shop_name = request.form['shop_name']
        location = request.form['location']
        sourcing_info = request.form['sourcing_info']
        
        # Update database
        cursor.execute('''
            UPDATE wholesalers 
            SET name = ?, shop_name = ?, location = ?, sourcing_info = ?
            WHERE id = ?
        ''', (name, shop_name, location, sourcing_info, wholesaler_id))
        
        conn.commit()
        
        # Update session name if changed
        session['wholesaler_name'] = name
        
        flash('Profile updated successfully!', 'success')
        conn.close()
        return redirect(url_for('wholesaler_profile'))
    
    # GET request - show edit form
    cursor.execute('SELECT * FROM wholesalers WHERE id = ?', (wholesaler_id,))
    wholesaler = cursor.fetchone()
    conn.close()
    
    if not wholesaler:
        flash('Wholesaler not found.', 'error')
        return redirect(url_for('wholesaler_login'))
    
    return render_template('edit_profile.html', wholesaler=wholesaler)

# Change password route
@app.route('/wholesaler/change-password', methods=['POST'])
def change_password():
    if 'wholesaler_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        return jsonify({'error': 'All password fields are required'}), 400
    
    if new_password != confirm_password:
        return jsonify({'error': 'New passwords do not match'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters long'}), 400
    
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    
    # Verify current password
    cursor.execute('SELECT password FROM wholesalers WHERE id = ?', (session['wholesaler_id'],))
    stored_password = cursor.fetchone()
    
    if not stored_password or stored_password[0] != current_password:
        conn.close()
        return jsonify({'error': 'Current password is incorrect'}), 400
    
    # Update password
    cursor.execute('UPDATE wholesalers SET password = ? WHERE id = ?', 
                  (new_password, session['wholesaler_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Password changed successfully'})

@app.route('/download/<path:filename>')
def download_file(filename):
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    return send_file(filename, as_attachment=True)

# Vendor Routes
@app.route("/vendor/login", methods=["GET", "POST"])
def vendor_login():
    if request.method == "POST":
        phone = request.form["phone"]
        password = request.form["password"]
        
        conn = sqlite3.connect("vendor_clubs.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vendors WHERE phone = ?", (phone,))
        vendor = cursor.fetchone()
        conn.close()
        
        if vendor and vendor[4] == password:
            if vendor[6]:  # is_approved
                session["vendor_id"] = vendor[0]
                session["vendor_name"] = vendor[1]
                flash("Login successful!")
                return redirect(url_for("vendor_dashboard"))
            else:
                flash("Your account is pending approval.")
                return redirect(url_for("vendor_login"))
        else:
            flash("Invalid phone or password.")
            return redirect(url_for("vendor_login"))
    
    return render_template("vendor_login.html")

@app.route("/vendor/dashboard")
def vendor_dashboard():
    if "vendor_id" not in session:
        return redirect(url_for("vendor_login"))
    
    vendor_id = session["vendor_id"]
    
    conn = sqlite3.connect("vendor_clubs.db")
    cursor = conn.cursor()
    
    # Get recent orders for this vendor
    cursor.execute("""
        SELECT o.*, p.name, p.price, p.category
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.vendor_id = ?
        ORDER BY o.created_at DESC
        LIMIT 5
    """, (vendor_id,))
    recent_orders = cursor.fetchall()
    
    # Get all categories for the grid
    cursor.execute("""
        SELECT DISTINCT category FROM products 
        WHERE category IS NOT NULL AND category != ""
        ORDER BY category
    """)
    categories = cursor.fetchall()
    
    conn.close()
    
    return render_template("vendor_dashboard.html", 
                         recent_orders=recent_orders,
                         categories=categories,
                         vendor_name=session.get("vendor_name", "Vendor"))

@app.route('/vendor/signup', methods=['GET', 'POST'])
def vendor_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        location = request.form['location']
        
        conn = sqlite3.connect('vendor_clubs.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO vendors (name, email, phone, password, location)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, email, phone, password, location))
            conn.commit()
            flash('Registration successful! Your account is pending approval.')
            return redirect(url_for('vendor_login'))
        except sqlite3.IntegrityError:
            flash('Email or phone number already exists.')
            return redirect(url_for('vendor_signup'))
        finally:
            conn.close()
    
    return render_template('vendor_signup.html')

@app.route('/vendor/logout')
def vendor_logout():
    session.pop('vendor_id', None)
    session.pop('vendor_name', None)
    flash('Logged out successfully!')
    return redirect(url_for('index'))

# Update the existing vendor route to show under development page
@app.route('/vendor')
def vendor():
    return render_template('vendor_under_development.html')

# Saved Payment Info route
@app.route('/vendor/saved-payment-info')
def saved_payment_info():
    return render_template('vendor_under_development.html')

# Category listing route
@app.route('/vendor/category/<category_id>')
def vendor_category(category_id):
    return render_template('vendor_under_development.html')
    category_mapping = {
        'vegetables': 'Vegetables',
        'dry-ingredients': 'Spices & Condiments',
        'dairy': 'Dairy Products',
        'breads': 'Grains & Cereals',
        'prepared': 'Packaged Foods',
        'oils-sauces': 'Sauces & Pastes',
        'snacks': 'Snacks & Beverages',
        'beverage': 'Snacks & Beverages',
        'packaging': 'Other',
        'desserts': 'Snacks & Beverages',
        'seafood-meat': 'Other'
    }
    
    wholesaler_category = category_mapping.get(category_id, 'Produce')
    
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM products 
        WHERE category = ? 
        ORDER BY name
    ''', (wholesaler_category,))
    products = cursor.fetchall()
    conn.close()
    
    return render_template('category_products.html', 
                         products=products,
                         category_name=wholesaler_category,
                         category_id=category_id)

# Vendor ordering routes
@app.route('/vendor/order', methods=['POST'])
def vendor_order():
    if 'vendor_id' not in session:
        return redirect(url_for('vendor_login'))
    
    vendor_id = session['vendor_id']
    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity', 1)
    
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    
    # Get product details
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    
    if product:
        # Create order
        cursor.execute('''
            INSERT INTO orders (vendor_id, product_id, quantity, status, created_at)
            VALUES (?, ?, ?, 'pending', datetime('now'))
        ''', (vendor_id, product_id, quantity))
        conn.commit()
        flash(f'Order placed successfully for {product[1]}!')
    else:
        flash('Product not found!')
    
    conn.close()
    return redirect(request.referrer or url_for('vendor_dashboard'))

# Demo payment route
@app.route('/vendor/payment', methods=['GET', 'POST'])
def vendor_payment():
    if 'vendor_id' not in session:
        return redirect(url_for('vendor_login'))
    
    if request.method == 'POST':
        # Demo payment processing
        flash('Payment successful! Your order has been confirmed.')
        return redirect(url_for('vendor_dashboard'))
    
    return render_template('saved_payment_info.html')

# Vendor search route
@app.route('/vendor/search')
def vendor_search():
    if 'vendor_id' not in session:
        return redirect(url_for('vendor_login'))
    
    query = request.args.get('q', '')
    
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM products 
        WHERE name LIKE ? OR category LIKE ? OR description LIKE ?
        ORDER BY name
    ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
    products = cursor.fetchall()
    conn.close()
    
    return render_template('category_products.html', 
                         products=products,
                         category_name=f'Search Results for "{query}"',
                         category_id='search')

# Search route
# Quick order route
@app.route('/vendor/quick-order/<int:product_id>')
def vendor_quick_order(product_id):
    return render_template('vendor_under_development.html')

# Cart route
@app.route('/vendor/cart')
def vendor_cart():
    return render_template('vendor_under_development.html')

# Place order route
@app.route('/vendor/place-order', methods=['POST'])
def place_order():
    return render_template('vendor_under_development.html')
    
    
    # Insert order into database
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    
    # Get wholesaler_id from product
    cursor.execute('SELECT wholesaler_id FROM products WHERE id = ?', (product_id,))
    result = cursor.fetchone()
    if result:
        wholesaler_id = result[0]
        
        # Insert order
        cursor.execute('''
            INSERT INTO orders (wholesaler_id, vendor_id, product_id, quantity, total_amount, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (wholesaler_id, session['vendor_id'], product_id, quantity, total_amount, 'pending'))
        
        order_id = cursor.lastrowid
        conn.commit()
        
        flash('Order placed successfully! Order ID: #' + str(order_id), 'success')
    else:
        flash('Product not found', 'error')
    
    conn.close()
    return redirect(url_for('vendor_dashboard'))

# Vendor orders history
@app.route('/vendor/orders')
def vendor_orders():
    return render_template('vendor_under_development.html')
    
    # Get vendor's orders
    conn = sqlite3.connect('vendor_clubs.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT o.*, p.name as product_name, w.name as wholesaler_name, w.phone as wholesaler_phone
        FROM orders o 
        JOIN products p ON o.product_id = p.id 
        JOIN wholesalers w ON o.wholesaler_id = w.id 
        WHERE o.vendor_id = ? 
        ORDER BY o.created_at DESC
    ''', (session['vendor_id'],))
    orders = cursor.fetchall()
    conn.close()
    
    # Render the orders template
    return render_template('vendor_orders.html', orders=orders, lang=lang)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)