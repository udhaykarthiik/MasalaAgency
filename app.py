# app.py - Complete Masala Agency Application with Normal Login
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import os
from flask import send_from_directory, abort

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///masala.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

with app.app_context():
    db.create_all()
    print("✅ Database tables created/verified!")

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # NEW: Hashed password
    phone = db.Column(db.String(15), unique=True, nullable=True)   # New (optional)
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
    
@app.route('/static/images/<path:filename>')
def serve_image(filename):
    # Try to find the image in static/images folder
    image_path = os.path.join(app.static_folder, 'images', filename)
    
    # If image exists, serve it
    if os.path.exists(image_path):
        return send_from_directory(os.path.join(app.static_folder, 'images'), filename)
    
    # If not found, return a placeholder
    return redirect(f"https://via.placeholder.com/300x200?text={filename.replace('.jpg','').replace('-','+')}")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()
    print("Database created successfully!")

# Command to add sample products
@app.cli.command("add-sample-products")
def add_sample_products():
    """Add sample products to database"""
    products = [
        Product(
            name="Everest Chicken Masala",
            category="Chicken Masala",
            price=85,
            original_price=90,
            description="Premium blend of spices for perfect chicken curry",
            image_url="/static/images/everest-chicken.jpg",
            stock=100,
            unit="kg"
        ),
        Product(
            name="MDH Chicken Masala",
            category="Chicken Masala",
            price=75,
            original_price=80,
            description="Traditional family recipe masala",
            image_url="/static/images/mdh-chicken.jpg",
            stock=150,
            unit="kg"
        ),
        Product(
            name="Badshah Chicken Masala",
            category="Chicken Masala",
            price=70,
            description="Restaurant style chicken masala",
            image_url="/static/images/badshah-chicken.jpg",
            stock=200,
            unit="kg"
        ),
        Product(
            name="Shan Chicken Masala",
            category="Chicken Masala",
            price=95,
            original_price=100,
            description="Authentic Pakistani blend for chicken",
            image_url="/static/images/shan-chicken.jpg",
            stock=80,
            unit="kg"
        ),
        Product(
            name="Everest Garam Masala",
            category="Garam Masala",
            price=120,
            description="Aromatic blend of premium spices",
            image_url="/static/images/everest-garam.jpg",
            stock=80,
            unit="kg"
        ),
        Product(
            name="MDH Garam Masala",
            category="Garam Masala",
            price=110,
            description="Rich and aromatic garam masala",
            image_url="/static/images/mdh-garam.jpg",
            stock=120,
            unit="kg"
        ),
        Product(
            name="Badshah Garam Masala",
            category="Garam Masala",
            price=105,
            description="Complete garam masala for all dishes",
            image_url="/static/images/badshah-garam.jpg",
            stock=90,
            unit="kg"
        ),
        Product(
            name="Everest Meat Masala",
            category="Meat Masala",
            price=130,
            description="Special blend for mutton and beef",
            image_url="/static/images/everest-meat.jpg",
            stock=60,
            unit="kg"
        ),
        Product(
            name="MDH Meat Masala",
            category="Meat Masala",
            price=125,
            description="Punjabi style meat masala",
            image_url="/static/images/mdh-meat.jpg",
            stock=70,
            unit="kg"
        ),
        Product(
            name="Everest Kitchen King",
            category="All-in-One",
            price=140,
            description="All-purpose masala for daily cooking",
            image_url="/static/images/everest-kitchen.jpg",
            stock=150,
            unit="kg"
        ),
    ]
    
    for product in products:
        existing = Product.query.filter_by(name=product.name).first()
        if not existing:
            db.session.add(product)
            print(f"Added: {product.name}")
        else:
            print(f"Exists already: {product.name}")
    
    db.session.commit()
    print(f"\n✅ Added sample products to database!")
    
# Command to create agency user
@app.cli.command("create-agency")
def create_agency():
    """Create agency admin user"""
    hashed_password = generate_password_hash('admin123')  # Default password
    agency = User(
        email="admin@masalaagency.com",
        password=hashed_password,
        phone="9999999999",
        shop_name="Masala Agency Admin",
        owner_name="Admin",
        address="Main Office",
        is_agency=True
    )
    db.session.add(agency)
    db.session.commit()
    print("✅ Agency user created!")
    print("   Email: admin@masalaagency.com")
    print("   Password: admin123")

# Routes
@app.route('/')
def index():
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

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    similar_products = Product.query.filter_by(category=product.category).filter(Product.id != product_id).limit(4).all()
    return render_template('product_detail.html', product=product, similar_products=similar_products)

@app.route('/category/<string:category_name>')
def category_products(category_name):
    products = Product.query.filter_by(category=category_name).all()
    return render_template('category.html', category=category_name, products=products)

# NEW: Normal Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
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

# NEW: Normal Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        shop_name = request.form.get('shop_name')
        owner_name = request.form.get('owner_name')
        address = request.form.get('address')
        
        # Check if user exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        # Create new user with hashed password
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    user_orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', orders=user_orders)

@app.route('/order/<int:product_id>', methods=['POST'])
@login_required
def place_order(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = float(request.form.get('quantity', 1))
    
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
    
    db.session.add(new_order)
    db.session.commit()
    
    flash(f'Order placed successfully! Order #{order_number}', 'success')
    return redirect(url_for('profile'))

@app.route('/track-order/<string:order_number>')
def track_order(order_number):
    order = Order.query.filter_by(order_number=order_number).first()
    if order:
        return render_template('track_order.html', order=order)
    else:
        flash('Order not found', 'danger')
        return redirect(url_for('index'))

# Admin routes (unchanged)
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_agency:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_customers = User.query.filter_by(is_agency=False).count()
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_products=total_products,
                         total_orders=total_orders,
                         total_customers=total_customers,
                         recent_orders=recent_orders)

@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_agency:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/product/add', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    if not current_user.is_agency:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        price = float(request.form.get('price'))
        description = request.form.get('description')
        stock = int(request.form.get('stock'))
        unit = request.form.get('unit')
        
        new_product = Product(
            name=name,
            category=category,
            price=price,
            description=description,
            stock=stock,
            unit=unit
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/add_product.html')

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_product(product_id):
    if not current_user.is_agency:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.category = request.form.get('category')
        product.price = float(request.form.get('price'))
        product.description = request.form.get('description')
        product.stock = int(request.form.get('stock'))
        product.unit = request.form.get('unit')
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_agency:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/order/update/<int:order_id>', methods=['POST'])
@login_required
def admin_update_order(order_id):
    if not current_user.is_agency:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    order.status = new_status
    
    if new_status == 'delivered':
        order.delivery_date = datetime.now()
    
    db.session.commit()
    flash(f'Order #{order.order_number} updated to {new_status}', 'success')
    return redirect(url_for('admin_orders'))

@app.route('/admin/customers')
@login_required
def admin_customers():
    if not current_user.is_agency:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    customers = User.query.filter_by(is_agency=False).all()
    return render_template('admin/customers.html', customers=customers)

@app.route('/admin/customer/<int:customer_id>')
@login_required
def admin_customer_detail(customer_id):
    if not current_user.is_agency:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    customer = User.query.get_or_404(customer_id)
    orders = Order.query.filter_by(user_id=customer_id).order_by(Order.order_date.desc()).all()
    return render_template('admin/customer_detail.html', customer=customer, orders=orders)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=False)