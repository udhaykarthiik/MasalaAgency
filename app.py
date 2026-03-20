from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import sys
import logging
import time
import random
import string
from sqlalchemy import text
from flask import send_from_directory

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 50)
print("🚀 Starting Masala Agency App...")
print(f"📅 Time: {datetime.now().isoformat()}")
print(f"🐍 Python: {sys.version}")
print(f"📁 CWD: {os.getcwd()}")
print("=" * 50)

# ── App setup ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-secret-key-in-production')

# ============================================
# DATABASE CONFIGURATION - PostgreSQL Support
# ============================================
import os

def get_database_url():
    """Get database URL from environment, supports both PostgreSQL and SQLite"""
    # Check for DATABASE_URL (Render sets this when you add the environment variable)
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Fix postgres:// to postgresql:// for SQLAlchemy
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        print(f"📊 Using PostgreSQL database")
        return database_url
    
    # Check for individual PostgreSQL variables (alternative method)
    pg_host = os.environ.get('PGHOST')
    pg_port = os.environ.get('PGPORT', '5432')
    pg_user = os.environ.get('PGUSER')
    pg_password = os.environ.get('PGPASSWORD')
    pg_database = os.environ.get('PGDATABASE')
    
    if all([pg_host, pg_user, pg_password, pg_database]):
        print(f"📊 Using PostgreSQL database (from individual variables)")
        return f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
    
    # Fallback to SQLite for local development
    print(f"📊 Using SQLite database (local development)")
    return 'sqlite:///masala.db'

app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# ── File upload config ─────────────────────────────────────────────────────────
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join('static', 'images'), exist_ok=True)
os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)

# ── Extensions ─────────────────────────────────────────────────────────────────
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ── Helpers ────────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_order_number(user_id):
    """Generate a collision-safe order number."""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{user_id}{suffix}"


def handle_image_upload(file, product_name):
    """
    Save an uploaded image file and return its URL path.
    Returns None if no valid file was provided.
    Raises ValueError if the file type is not allowed.
    """
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename):
        raise ValueError('Invalid file type. Allowed: png, jpg, jpeg, gif, webp')

    filename = secure_filename(file.filename)
    name_part, ext = filename.rsplit('.', 1)
    unique_filename = f"{name_part}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(filepath)
    return f"/static/uploads/{unique_filename}"


# ── Context processor ──────────────────────────────────────────────────────────

@app.context_processor
def utility_processor():
    return {'now': datetime.utcnow, 'timedelta': timedelta}


# ── Models ─────────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(100), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    phone      = db.Column(db.String(15), unique=True, nullable=True)
    shop_name  = db.Column(db.String(100))
    owner_name = db.Column(db.String(100))
    address    = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_agency  = db.Column(db.Boolean, default=False)
    orders     = db.relationship('Order', back_populates='customer', lazy=True)


class Product(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(100), nullable=False)
    category       = db.Column(db.String(50))
    price          = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float)
    description    = db.Column(db.Text)
    image_url      = db.Column(db.String(200))
    stock          = db.Column(db.Integer, default=0)
    unit           = db.Column(db.String(20), default='kg')
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, onupdate=datetime.utcnow)
    orders         = db.relationship('Order', back_populates='product')


class Order(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    order_number    = db.Column(db.String(30), unique=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id      = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity        = db.Column(db.Float, nullable=False)
    price_at_order  = db.Column(db.Float)
    total_amount    = db.Column(db.Float)
    order_date      = db.Column(db.DateTime, default=datetime.utcnow)
    status          = db.Column(db.String(20), default='pending')
    delivery_date   = db.Column(db.DateTime)
    payment_status  = db.Column(db.String(20), default='pending')
    customer        = db.relationship('User', back_populates='orders')
    product         = db.relationship('Product', back_populates='orders')


class OrderItem(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    order_id   = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity   = db.Column(db.Float)
    price      = db.Column(db.Float)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ============================================
# AUTO-INITIALIZE DATABASE WITH DEFAULT DATA
# ============================================
with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables created/verified")
        
        # Add sample products if none exist
        if Product.query.count() == 0:
            print("🌱 Seeding database with sample products...")
            products_data = [
                Product(name="Everest Chicken Masala", category="Chicken Masala", price=85, original_price=90,
                       description="Premium blend of spices for perfect chicken curry", stock=100, unit="kg"),
                Product(name="MDH Chicken Masala", category="Chicken Masala", price=75, original_price=80,
                       description="Traditional family recipe masala", stock=150, unit="kg"),
                Product(name="Badshah Chicken Masala", category="Chicken Masala", price=70,
                       description="Restaurant style chicken masala", stock=200, unit="kg"),
                Product(name="Shan Chicken Masala", category="Chicken Masala", price=95, original_price=100,
                       description="Authentic Pakistani blend for chicken", stock=80, unit="kg"),
                Product(name="Everest Garam Masala", category="Garam Masala", price=120,
                       description="Aromatic blend of premium spices", stock=80, unit="kg"),
                Product(name="MDH Garam Masala", category="Garam Masala", price=110,
                       description="Rich and aromatic garam masala", stock=120, unit="kg"),
                Product(name="Badshah Garam Masala", category="Garam Masala", price=105,
                       description="Complete garam masala for all dishes", stock=90, unit="kg"),
                Product(name="Everest Meat Masala", category="Meat Masala", price=130,
                       description="Special blend for mutton and beef", stock=60, unit="kg"),
                Product(name="MDH Meat Masala", category="Meat Masala", price=125,
                       description="Punjabi style meat masala", stock=70, unit="kg"),
                Product(name="Everest Kitchen King", category="All-in-One", price=140,
                       description="All-purpose masala for daily cooking", stock=150, unit="kg"),
            ]
            
            for p in products_data:
                filename = p.name.lower().replace(' ', '-') + '.jpg'
                p.image_url = f"/static/images/{filename}"
                db.session.add(p)
            
            db.session.commit()
            print(f"✅ Added {len(products_data)} sample products")
        else:
            print(f"✅ Database already has {Product.query.count()} products")
        
        # Create admin user if doesn't exist
        if not User.query.filter_by(email="admin@masalaagency.com").first():
            print("👑 Creating admin user...")
            hashed_password = generate_password_hash('admin123')
            admin = User(
                email="admin@masalaagency.com",
                password=hashed_password,
                phone="9999999999",
                shop_name="Masala Agency Admin",
                owner_name="Admin",
                address="Main Office",
                is_agency=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin created - Email: admin@masalaagency.com / Password: admin123")
        else:
            print("✅ Admin user already exists")
            
    except Exception as e:
        print(f"⚠️ Database initialization error: {str(e)}")
        print("App will continue, but you may need to run /init-db manually")


# ── Static file serving ────────────────────────────────────────────────────────

@app.route('/static/images/<path:filename>')
def serve_image(filename):
    try:
        return send_from_directory(os.path.join(app.static_folder, 'images'), filename)
    except Exception:
        return redirect(f"https://via.placeholder.com/300x200?text=No+Image")


@app.route('/static/uploads/<path:filename>')
def serve_upload(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception:
        return redirect("https://via.placeholder.com/300x200?text=Image+Not+Found")


# ── Health & debug routes ──────────────────────────────────────────────────────

@app.route('/health')
def health():
    try:
        db.session.execute(text('SELECT 1')).scalar()
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "products_count": Product.query.count()
        }), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route('/debug-images')
def debug_images():
    try:
        images_folder = os.path.join(app.static_folder, 'images')
        uploads_folder = app.config['UPLOAD_FOLDER']
        images  = os.listdir(images_folder)  if os.path.exists(images_folder)  else []
        uploads = os.listdir(uploads_folder) if os.path.exists(uploads_folder) else []
        products = Product.query.limit(5).all()
        return jsonify({
            'images_folder':  images_folder,
            'images':         images[:15],
            'image_count':    len(images),
            'uploads_folder': uploads_folder,
            'uploads':        uploads[:15],
            'upload_count':   len(uploads),
            'sample_products': [{'name': p.name, 'image_url': p.image_url} for p in products],
            'total_products': Product.query.count()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/debug-products')
def debug_products():
    try:
        products = Product.query.all()
        return jsonify({
            'total_products': len(products),
            'products': [{
                'id': p.id, 'name': p.name, 'category': p.category,
                'price': p.price, 'stock': p.stock, 'image_url': p.image_url
            } for p in products]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Init / setup routes (for manual initialization if needed) ─────────────────

@app.route('/init-db')
def init_database():
    """Seed the database with default products. Remove this route in production."""
    try:
        if Product.query.count() > 0:
            return jsonify({
                "message": f"Database already has {Product.query.count()} products",
                "products": [p.name for p in Product.query.all()]
            })

        products_data = [
            Product(name="Everest Chicken Masala", category="Chicken Masala", price=85, original_price=90,
                    description="Premium blend of spices for perfect chicken curry", stock=100, unit="kg"),
            Product(name="MDH Chicken Masala", category="Chicken Masala", price=75, original_price=80,
                    description="Traditional family recipe masala", stock=150, unit="kg"),
            Product(name="Badshah Chicken Masala", category="Chicken Masala", price=70,
                    description="Restaurant style chicken masala", stock=200, unit="kg"),
            Product(name="Shan Chicken Masala", category="Chicken Masala", price=95, original_price=100,
                    description="Authentic Pakistani blend for chicken", stock=80, unit="kg"),
            Product(name="Everest Garam Masala", category="Garam Masala", price=120,
                    description="Aromatic blend of premium spices", stock=80, unit="kg"),
            Product(name="MDH Garam Masala", category="Garam Masala", price=110,
                    description="Rich and aromatic garam masala", stock=120, unit="kg"),
            Product(name="Badshah Garam Masala", category="Garam Masala", price=105,
                    description="Complete garam masala for all dishes", stock=90, unit="kg"),
            Product(name="Everest Meat Masala", category="Meat Masala", price=130,
                    description="Special blend for mutton and beef", stock=60, unit="kg"),
            Product(name="MDH Meat Masala", category="Meat Masala", price=125,
                    description="Punjabi style meat masala", stock=70, unit="kg"),
            Product(name="Everest Kitchen King", category="All-in-One", price=140,
                    description="All-purpose masala for daily cooking", stock=150, unit="kg"),
        ]

        for p in products_data:
            filename = p.name.lower().replace(' ', '-') + '.jpg'
            p.image_url = f"/static/images/{filename}"
            db.session.add(p)

        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"✅ Added {len(products_data)} products",
            "products": [p.name for p in Product.query.all()]
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/create-admin')
def create_admin():
    """Create the agency admin user. Remove this route in production."""
    try:
        admin = User.query.filter_by(email="admin@masalaagency.com").first()
        if admin:
            return jsonify({"message": "Admin already exists", "email": admin.email})

        admin = User(
            email="admin@masalaagency.com",
            password=generate_password_hash('admin123'),
            phone="9999999999",
            shop_name="Masala Agency Admin",
            owner_name="Admin",
            address="Main Office",
            is_agency=True
        )
        db.session.add(admin)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "✅ Admin created",
            "email": "admin@masalaagency.com",
            "password": "admin123"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/fix-image-urls')
def fix_image_urls():
    """Fix image URLs in the database."""
    try:
        filename_map = {
            "Everest Chicken Masala": "everest-chicken.jpg",
            "MDH Chicken Masala":     "mdh-chicken.jpg",
            "Badshah Chicken Masala": "badshah-chicken.jpg",
            "Shan Chicken Masala":    "shan-chicken.jpg",
            "Everest Garam Masala":   "everest-garam.jpg",
            "MDH Garam Masala":       "mdh-garam.jpg",
            "Badshah Garam Masala":   "badshah-garam.jpg",
            "Everest Meat Masala":    "everest-meat.jpg",
            "MDH Meat Masala":        "mdh-meat.jpg",
            "Everest Kitchen King":   "everest-kitchen.jpg",
        }
        fixed = []
        for p in Product.query.all():
            if p.name in filename_map:
                new_url = f"/static/images/{filename_map[p.name]}"
                if p.image_url != new_url:
                    fixed.append({'name': p.name, 'old': p.image_url, 'new': new_url})
                    p.image_url = new_url
        if fixed:
            db.session.commit()
        return jsonify({'fixed_count': len(fixed), 'fixed_products': fixed})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── API routes ─────────────────────────────────────────────────────────────────

@app.route('/api/unread-orders-count')
@login_required
def unread_orders_count():
    if not current_user.is_agency:
        return jsonify({'error': 'Unauthorized'}), 403
    last_24h = datetime.utcnow() - timedelta(hours=24)
    count = Order.query.filter(
        Order.status == 'pending',
        Order.order_date >= last_24h
    ).count()
    return jsonify({'count': count})


@app.route('/api/mark-orders-read', methods=['POST'])
@login_required
def mark_orders_read():
    if not current_user.is_agency:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify({'success': True})


# ── Public routes ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    try:
        products = Product.query.all()
        categories = db.session.query(Product.category).distinct().all()
        products_by_category = {}
        for (cat_name,) in categories:
            if cat_name:
                products_by_category[cat_name] = (
                    Product.query.filter_by(category=cat_name).limit(4).all()
                )
        return render_template('index.html', products=products,
                               products_by_category=products_by_category)
    except Exception as e:
        logger.error(f"index: {e}")
        return render_template('500.html'), 500


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        similar = (Product.query
                   .filter_by(category=product.category)
                   .filter(Product.id != product_id)
                   .limit(4).all())
        return render_template('product_detail.html', product=product, similar_products=similar)
    except Exception as e:
        logger.error(f"product_detail: {e}")
        return render_template('500.html'), 500


@app.route('/category/<string:category_name>')
def category_products(category_name):
    try:
        products = Product.query.filter_by(category=category_name).all()
        return render_template('category.html', category=category_name, products=products)
    except Exception as e:
        logger.error(f"category_products: {e}")
        return render_template('500.html'), 500


@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            email    = request.form.get('email')
            password = request.form.get('password')
            remember = bool(request.form.get('remember'))
            user = User.query.filter_by(email=email).first()
            if not user or not check_password_hash(user.password, password):
                flash('Invalid email or password. Please try again.', 'danger')
                return redirect(url_for('login'))
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.shop_name}!', 'success')
            return redirect(url_for('admin_dashboard') if user.is_agency else url_for('index'))
        return render_template('login.html')
    except Exception as e:
        logger.error(f"login: {e}")
        return render_template('500.html'), 500


@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            email      = request.form.get('email')
            password   = request.form.get('password')
            phone      = request.form.get('phone') or None
            shop_name  = request.form.get('shop_name')
            owner_name = request.form.get('owner_name')
            address    = request.form.get('address')

            if User.query.filter_by(email=email).first():
                flash('Email already registered.', 'danger')
                return redirect(url_for('register'))

            new_user = User(
                email=email,
                password=generate_password_hash(password),
                phone=phone,
                shop_name=shop_name,
                owner_name=owner_name,
                address=address,
                is_agency=False
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html')
    except Exception as e:
        logger.error(f"register: {e}")
        return render_template('500.html'), 500


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    try:
        user_orders = Order.query.filter_by(user_id=current_user.id).all()
        return render_template('profile.html', orders=user_orders)
    except Exception as e:
        logger.error(f"profile: {e}")
        return render_template('500.html'), 500


@app.route('/order/<int:product_id>', methods=['POST'])
@login_required
def place_order(product_id):
    try:
        product  = Product.query.get_or_404(product_id)
        quantity = float(request.form.get('quantity', 1))

        if quantity <= 0:
            flash('Quantity must be greater than zero.', 'danger')
            return redirect(url_for('product_detail', product_id=product_id))

        if quantity > product.stock:
            flash(f'Only {product.stock} {product.unit} available in stock.', 'danger')
            return redirect(url_for('product_detail', product_id=product_id))

        new_order = Order(
            order_number   = generate_order_number(current_user.id),
            user_id        = current_user.id,
            product_id     = product_id,
            quantity       = quantity,
            price_at_order = product.price,
            total_amount   = round(product.price * quantity, 2),
            status         = 'pending',
            payment_status = 'pending'
        )

        product.stock = max(0, product.stock - int(quantity))

        db.session.add(new_order)
        db.session.commit()

        flash(f'Order placed successfully! Order #{new_order.order_number}', 'success')
        return redirect(url_for('profile'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"place_order: {e}")
        flash('Failed to place order. Please try again.', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))


@app.route('/track-order/<string:order_number>')
def track_order(order_number):
    try:
        order = Order.query.filter_by(order_number=order_number).first()
        if not order:
            flash('Order not found.', 'danger')
            return redirect(url_for('index'))
        return render_template('track_order.html', order=order)
    except Exception as e:
        logger.error(f"track_order: {e}")
        return render_template('500.html'), 500


# ── Admin routes ───────────────────────────────────────────────────────────────

def admin_required(f):
    """Decorator that redirects non-admin users."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_agency:
            flash('Unauthorized access.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    try:
        total_products  = Product.query.count()
        total_orders    = Order.query.count()
        total_customers = User.query.filter_by(is_agency=False).count()
        recent_orders   = Order.query.order_by(Order.order_date.desc()).limit(10).all()
        last_24h        = datetime.utcnow() - timedelta(hours=24)
        unread_count    = Order.query.filter(
            Order.status == 'pending',
            Order.order_date >= last_24h
        ).count()
        return render_template('admin/dashboard.html',
                               total_products=total_products,
                               total_orders=total_orders,
                               total_customers=total_customers,
                               recent_orders=recent_orders,
                               unread_count=unread_count)
    except Exception as e:
        logger.error(f"admin_dashboard: {e}")
        return render_template('500.html'), 500


@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    try:
        products = Product.query.all()
        return render_template('admin/products.html', products=products)
    except Exception as e:
        logger.error(f"admin_products: {e}")
        return render_template('500.html'), 500


@app.route('/admin/product/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_product():
    if request.method == 'POST':
        try:
            original_price_str = request.form.get('original_price')
            original_price     = float(original_price_str) if original_price_str else None

            # Handle image upload
            image_url = None
            if 'image' in request.files:
                try:
                    image_url = handle_image_upload(request.files['image'],
                                                    request.form.get('name', ''))
                except ValueError as ve:
                    flash(str(ve), 'danger')
                    return redirect(request.url)

            # Fallback image
            if not image_url:
                name_slug = request.form.get('name', 'product').lower().replace(' ', '-')
                placeholder = os.path.join('static', 'images', 'placeholder.jpg')
                image_url = ("/static/images/placeholder.jpg"
                             if os.path.exists(placeholder)
                             else f"/static/images/{name_slug}.jpg")

            new_product = Product(
                name           = request.form.get('name'),
                category       = request.form.get('category'),
                price          = float(request.form.get('price')),
                original_price = original_price,
                description    = request.form.get('description'),
                stock          = int(request.form.get('stock', 0)),
                unit           = request.form.get('unit'),
                image_url      = image_url
            )
            db.session.add(new_product)
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin_products'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"admin_add_product: {e}")
            flash(f'Error adding product: {str(e)}', 'danger')
            return redirect(url_for('admin_add_product'))

    return render_template('admin/add_product.html')


@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        try:
            original_price_str    = request.form.get('original_price')
            product.original_price = float(original_price_str) if original_price_str else None

            product.name        = request.form.get('name')
            product.category    = request.form.get('category')
            product.price       = float(request.form.get('price'))
            product.description = request.form.get('description')
            product.stock       = int(request.form.get('stock', 0))
            product.unit        = request.form.get('unit')

            # Handle optional image change
            if 'image' in request.files:
                try:
                    new_url = handle_image_upload(request.files['image'], product.name)
                    if new_url:
                        product.image_url = new_url
                except ValueError as ve:
                    flash(str(ve), 'danger')
                    return redirect(request.url)

            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin_products'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"admin_edit_product: {e}")
            flash(f'Error updating product: {str(e)}', 'danger')
            return redirect(url_for('admin_edit_product', product_id=product_id))

    return render_template('admin/edit_product.html', product=product)


@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_product(product_id):
    try:
        product      = Product.query.get_or_404(product_id)
        product_name = product.name

        # Delete the uploaded image file if it exists
        if product.image_url and '/uploads/' in product.image_url:
            try:
                filename = product.image_url.replace('/static/uploads/', '')
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as img_err:
                logger.warning(f"Could not delete image: {img_err}")

        db.session.delete(product)
        db.session.commit()
        flash(f'Product "{product_name}" deleted successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        logger.error(f"admin_delete_product: {e}")
        flash(f'Error deleting product: {str(e)}', 'danger')

    return redirect(url_for('admin_products'))


@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    try:
        orders = Order.query.order_by(Order.order_date.desc()).all()
        return render_template('admin/orders.html', orders=orders)
    except Exception as e:
        logger.error(f"admin_orders: {e}")
        return render_template('500.html'), 500


@app.route('/admin/order/update/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def admin_update_order(order_id):
    try:
        order      = Order.query.get_or_404(order_id)
        new_status = request.form.get('status')
        order.status = new_status
        if new_status == 'delivered':
            order.delivery_date = datetime.now()
        db.session.commit()
        flash(f'Order #{order.order_number} updated to "{new_status}".', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"admin_update_order: {e}")
        flash('Failed to update order.', 'danger')
    return redirect(url_for('admin_orders'))


@app.route('/admin/customers')
@login_required
@admin_required
def admin_customers():
    try:
        customers = User.query.filter_by(is_agency=False).all()
        return render_template('admin/customers.html', customers=customers)
    except Exception as e:
        logger.error(f"admin_customers: {e}")
        return render_template('500.html'), 500


@app.route('/admin/customer/<int:customer_id>')
@login_required
@admin_required
def admin_customer_detail(customer_id):
    try:
        customer = User.query.get_or_404(customer_id)
        orders   = (Order.query
                    .filter_by(user_id=customer_id)
                    .order_by(Order.order_date.desc())
                    .all())
        return render_template('admin/customer_detail.html',
                               customer=customer, orders=orders)
    except Exception as e:
        logger.error(f"admin_customer_detail: {e}")
        return render_template('500.html'), 500


# ── Error handlers ─────────────────────────────────────────────────────────────
# ── Debug routes for troubleshooting ──────────────────────────────────────────

@app.route('/list-images')
def list_images():
    """Lists all files in the static/images directory on the server."""
    try:
        images_dir = os.path.join(app.static_folder, 'images')
        uploads_dir = app.config['UPLOAD_FOLDER']
        
        images = []
        uploads = []
        
        if os.path.exists(images_dir):
            images = os.listdir(images_dir)
        
        if os.path.exists(uploads_dir):
            uploads = os.listdir(uploads_dir)
        
        image_files = [f for f in images if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
        upload_files = [f for f in uploads if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
        
        return jsonify({
            "images_directory": images_dir,
            "directory_exists": os.path.exists(images_dir),
            "images_found": image_files,
            "image_count": len(image_files),
            "uploads_directory": uploads_dir,
            "uploads_exists": os.path.exists(uploads_dir),
            "uploads_found": upload_files,
            "upload_count": len(upload_files)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/debug-products')
def debug_products():
    """Check products in database"""
    try:
        products = Product.query.all()
        return jsonify({
            'total_products': len(products),
            'products': [{
                'id': p.id,
                'name': p.name,
                'category': p.category,
                'price': p.price,
                'stock': p.stock,
                'image_url': p.image_url
            } for p in products]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# ── CLI commands ───────────────────────────────────────────────────────────────

@app.cli.command("add-sample-products")
def add_sample_products():
    with app.app_context():
        print(init_database().get_json().get('message', 'Done'))


@app.cli.command("create-agency")
def create_agency():
    with app.app_context():
        print(create_admin().get_json().get('message', 'Done'))


# ── Database init (already done above with auto-initialization) ───────────────

# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🔥 Running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)