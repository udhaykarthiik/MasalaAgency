from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import mimetypes
from flask import send_from_directory, abort, send_file
from werkzeug.utils import safe_join
import sys
import logging
import time
from sqlalchemy import text

# Set up detailed logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 50)
print("🚀 Starting Masala Agency App...")
print(f"📅 Time: {datetime.now().isoformat()}")
print(f"🐍 Python version: {sys.version}")
print(f"📁 Current directory: {os.getcwd()}")
print(f"📂 Files in directory: {os.listdir('.')}")
print("=" * 50)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///masala.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Enable connection pooling health checks
    'pool_recycle': 300,    # Recycle connections every 5 minutes
}

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=True)
    shop_name = db.Column(db.String(100))
    owner_name = db.Column(db.String(100))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_agency = db.Column(db.Boolean, default=False)
    orders = db.relationship('Order', back_populates='customer', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    stock = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(20), default='kg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    orders = db.relationship('Order', back_populates='product')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price_at_order = db.Column(db.Float)
    total_amount = db.Column(db.Float)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    delivery_date = db.Column(db.DateTime)
    payment_status = db.Column(db.String(20), default='pending')
    customer = db.relationship('User', back_populates='orders')
    product = db.relationship('Product', back_populates='orders')
    
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Float)
    price = db.Column(db.Float)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Image serving route with better error handling
@app.route('/static/images/<path:filename>')
def serve_image(filename):
    """Serve images directly from static folder"""
    try:
        return send_from_directory(os.path.join(app.static_folder, 'images'), filename)
    except Exception as e:
        print(f"⚠️ Image not found: {filename}")
        return redirect(f"https://via.placeholder.com/300x200?text={filename.replace('.jpg','').replace('-','+')}")

# Health check endpoint for Render
@app.route('/health')
def health():
    """Health check endpoint for Render"""
    try:
        # Test database connection
        db.session.execute('SELECT 1').scalar()
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "products_count": Product.query.count()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

# Debug route to check images
@app.route('/debug-images')
def debug_images():
    """Debug endpoint to check image status"""
    try:
        static_folder = app.static_folder
        images_folder = os.path.join(static_folder, 'images')
        
        images = []
        if os.path.exists(images_folder):
            images = os.listdir(images_folder)
        
        products = Product.query.limit(5).all()
        product_images = [{
            'name': p.name,
            'image_url': p.image_url,
            'filename': os.path.basename(p.image_url) if p.image_url else None
        } for p in products]
        
        return jsonify({
            'static_folder_exists': os.path.exists(static_folder),
            'static_folder_path': static_folder,
            'images_folder_exists': os.path.exists(images_folder),
            'images_folder_path': images_folder,
            'images_in_folder': images[:15],
            'image_count': len(images),
            'sample_products': product_images,
            'total_products': Product.query.count()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to fix image URLs in database
@app.route('/fix-image-urls')
def fix_image_urls():
    """Fix image URLs in database"""
    try:
        products = Product.query.all()
        fixed = []
        
        filename_map = {
            "Everest Chicken Masala": "everest-chicken.jpg",
            "MDH Chicken Masala": "mdh-chicken.jpg",
            "Badshah Chicken Masala": "badshah-chicken.jpg",
            "Shan Chicken Masala": "shan-chicken.jpg",
            "Everest Garam Masala": "everest-garam.jpg",
            "MDH Garam Masala": "mdh-garam.jpg",
            "Badshah Garam Masala": "badshah-garam.jpg",
            "Everest Meat Masala": "everest-meat.jpg",
            "MDH Meat Masala": "mdh-meat.jpg",
            "Everest Kitchen King": "everest-kitchen.jpg"
        }
        
        for p in products:
            if p.name in filename_map:
                old_url = p.image_url
                new_url = f"/static/images/{filename_map[p.name]}"
                if old_url != new_url:
                    p.image_url = new_url
                    fixed.append({
                        'name': p.name,
                        'old': old_url,
                        'new': new_url
                    })
        
        if fixed:
            db.session.commit()
        
        return jsonify({
            'fixed_count': len(fixed),
            'fixed_products': fixed
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Initialize database with products
@app.route('/init-db')
def init_database():
    """Initialize database with products"""
    try:
        # Check if products exist
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
        
        # Set image URLs
        for p in products_data:
            filename = p.name.lower().replace(' ', '-') + '.jpg'
            p.image_url = f"/static/images/{filename}"
        
        for product in products_data:
            db.session.add(product)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"✅ Added {len(products_data)} products to database",
            "products": [p.name for p in Product.query.all()]
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Create admin user route
@app.route('/create-admin')
def create_admin():
    """Create admin user"""
    try:
        admin = User.query.filter_by(email="admin@masalaagency.com").first()
        if admin:
            return jsonify({
                "message": "Admin already exists",
                "email": admin.email,
                "shop_name": admin.shop_name
            })
        
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
        
        return jsonify({
            "success": True,
            "message": "✅ Admin created successfully",
            "email": "admin@masalaagency.com",
            "password": "admin123"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Create database tables (with retry logic)
with app.app_context():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            db.create_all()
            print(f"✅ Database tables created/verified! (attempt {attempt + 1}/{max_retries})")
            break
        except Exception as e:
            print(f"⚠️ Database creation attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                print("❌ Failed to create database tables after all retries")

# Routes
@app.route('/')
def index():
    try:
        products = Product.query.all()
        categories = db.session.query(Product.category).distinct().all()
        products_by_category = {}
        
        for category in categories:
            cat_name = category[0]
            if cat_name:
                products_by_category[cat_name] = Product.query.filter_by(category=cat_name).limit(4).all()
        
        return render_template('index.html', 
                             products=products,
                             products_by_category=products_by_category,
                             now=datetime.now())
    except Exception as e:
        print(f"❌ Error in index route: {str(e)}")
        return render_template('500.html'), 500

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        similar_products = Product.query.filter_by(category=product.category).filter(Product.id != product_id).limit(4).all()
        return render_template('product_detail.html', product=product, similar_products=similar_products)
    except Exception as e:
        print(f"❌ Error in product_detail route: {str(e)}")
        return render_template('500.html'), 500

@app.route('/category/<string:category_name>')
def category_products(category_name):
    try:
        products = Product.query.filter_by(category=category_name).all()
        return render_template('category.html', category=category_name, products=products)
    except Exception as e:
        print(f"❌ Error in category_products route: {str(e)}")
        return render_template('500.html'), 500

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            remember = True if request.form.get('remember') else False
            
            user = User.query.filter_by(email=email).first()
            
            if not user or not check_password_hash(user.password, password):
                flash('Please check your login details and try again.', 'danger')
                return redirect(url_for('login'))
            
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.shop_name}!', 'success')
            
            if user.is_agency:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        
        return render_template('login.html')
    except Exception as e:
        print(f"❌ Error in login route: {str(e)}")
        return render_template('500.html'), 500

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            phone = request.form.get('phone')
            shop_name = request.form.get('shop_name')
            owner_name = request.form.get('owner_name')
            address = request.form.get('address')
            
            existing = User.query.filter_by(email=email).first()
            if existing:
                flash('Email already registered', 'danger')
                return redirect(url_for('register'))
            
            hashed_password = generate_password_hash(password)
            new_user = User(
                email=email,
                password=hashed_password,
                phone=phone if phone else None,
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
        print(f"❌ Error in register route: {str(e)}")
        return render_template('500.html'), 500

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    try:
        user_orders = Order.query.filter_by(user_id=current_user.id).all()
        return render_template('profile.html', orders=user_orders)
    except Exception as e:
        print(f"❌ Error in profile route: {str(e)}")
        return render_template('500.html'), 500

@app.route('/order/<int:product_id>', methods=['POST'])
@login_required
def place_order(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        quantity = float(request.form.get('quantity', 1))
        
        if quantity > product.stock:
            flash(f'Only {product.stock} {product.unit} available in stock.', 'danger')
            return redirect(url_for('product_detail', product_id=product_id))
        
        order_number = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{current_user.id}"
        
        new_order = Order(
            order_number=order_number,
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity,
            price_at_order=product.price,
            total_amount=product.price * quantity,
            status='pending'
        )
        
        # Reduce stock
        product.stock -= quantity
        
        db.session.add(new_order)
        db.session.commit()
        
        flash(f'Order placed successfully! Order #{order_number}', 'success')
        return redirect(url_for('profile'))
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in place_order route: {str(e)}")
        flash('Failed to place order. Please try again.', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))

@app.route('/track-order/<string:order_number>')
def track_order(order_number):
    try:
        order = Order.query.filter_by(order_number=order_number).first()
        if order:
            return render_template('track_order.html', order=order)
        else:
            flash('Order not found', 'danger')
            return redirect(url_for('index'))
    except Exception as e:
        print(f"❌ Error in track_order route: {str(e)}")
        return render_template('500.html'), 500

# Admin routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_agency:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    try:
        total_products = Product.query.count()
        total_orders = Order.query.count()
        total_customers = User.query.filter_by(is_agency=False).count()
        recent_orders = Order.query.order_by(Order.order_date.desc()).limit(10).all()
        
        return render_template('admin/dashboard.html',
                             total_products=total_products,
                             total_orders=total_orders,
                             total_customers=total_customers,
                             recent_orders=recent_orders)
    except Exception as e:
        print(f"❌ Error in admin_dashboard route: {str(e)}")
        return render_template('500.html'), 500

@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_agency:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    try:
        products = Product.query.all()
        return render_template('admin/products.html', products=products)
    except Exception as e:
        print(f"❌ Error in admin_products route: {str(e)}")
        return render_template('500.html'), 500

@app.route('/admin/product/add', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    if not current_user.is_agency:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            category = request.form.get('category')
            price = float(request.form.get('price'))
            description = request.form.get('description')
            stock = int(request.form.get('stock'))
            unit = request.form.get('unit')
            
            # Generate filename from name
            filename = name.lower().replace(' ', '-') + '.jpg'
            
            new_product = Product(
                name=name,
                category=category,
                price=price,
                description=description,
                stock=stock,
                unit=unit,
                image_url=f"/static/images/{filename}"
            )
            
            db.session.add(new_product)
            db.session.commit()
            
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error adding product: {str(e)}")
            flash('Failed to add product. Please try again.', 'danger')
    
    return render_template('admin/add_product.html')

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_product(product_id):
    if not current_user.is_agency:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            product.name = request.form.get('name')
            product.category = request.form.get('category')
            product.price = float(request.form.get('price'))
            product.description = request.form.get('description')
            product.stock = int(request.form.get('stock'))
            product.unit = request.form.get('unit')
            
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating product: {str(e)}")
            flash('Failed to update product. Please try again.', 'danger')
    
    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_agency:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    try:
        orders = Order.query.order_by(Order.order_date.desc()).all()
        return render_template('admin/orders.html', orders=orders)
    except Exception as e:
        print(f"❌ Error in admin_orders route: {str(e)}")
        return render_template('500.html'), 500

@app.route('/admin/order/update/<int:order_id>', methods=['POST'])
@login_required
def admin_update_order(order_id):
    if not current_user.is_agency:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    try:
        order = Order.query.get_or_404(order_id)
        new_status = request.form.get('status')
        order.status = new_status
        
        if new_status == 'delivered':
            order.delivery_date = datetime.now()
        
        db.session.commit()
        flash(f'Order #{order.order_number} updated to {new_status}', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error updating order: {str(e)}")
        flash('Failed to update order. Please try again.', 'danger')
    
    return redirect(url_for('admin_orders'))

@app.route('/admin/customers')
@login_required
def admin_customers():
    if not current_user.is_agency:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    try:
        customers = User.query.filter_by(is_agency=False).all()
        return render_template('admin/customers.html', customers=customers)
    except Exception as e:
        print(f"❌ Error in admin_customers route: {str(e)}")
        return render_template('500.html'), 500

@app.route('/admin/customer/<int:customer_id>')
@login_required
def admin_customer_detail(customer_id):
    if not current_user.is_agency:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    try:
        customer = User.query.get_or_404(customer_id)
        orders = Order.query.filter_by(user_id=customer_id).order_by(Order.order_date.desc()).all()
        return render_template('admin/customer_detail.html', customer=customer, orders=orders)
    except Exception as e:
        print(f"❌ Error in admin_customer_detail route: {str(e)}")
        return render_template('500.html'), 500

# List images route
@app.route('/list-images')
def list_images():
    """Lists all files in the static/images directory on the server."""
    try:
        images_dir = os.path.join(app.static_folder, 'images')
        file_list = []
        
        if os.path.exists(images_dir):
            file_list = os.listdir(images_dir)
        else:
            return jsonify({"error": f"Directory not found: {images_dir}"})
        
        image_files = [f for f in file_list if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
        
        return jsonify({
            "images_directory": images_dir,
            "directory_exists": os.path.exists(images_dir),
            "all_contents": file_list,
            "image_files_found": image_files,
            "file_count": len(image_files)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# CLI Commands
@app.cli.command("add-sample-products")
def add_sample_products():
    """Add sample products to database"""
    try:
        response = init_database()
        print(response.get_json().get('message', 'Products added successfully!'))
    except Exception as e:
        print(f"❌ Error: {str(e)}")

@app.cli.command("create-agency")
def create_agency():
    """Create agency admin user"""
    try:
        response = create_admin()
        print(response.get_json().get('message', 'Admin created successfully!'))
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    print("🔥 Entering main block...")
    port = int(os.environ.get('PORT', 5000))
    print(f"🔌 Attempting to bind to port: {port}")
    print(f"🌐 Host: 0.0.0.0")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)