# 🌶️ Masala Agency - Online Ordering System

A complete web application for masala agencies to manage online orders from shop owners. This platform replaces manual order collection with a digital solution, saving time and reducing travel costs.

## ✨ Features

### For Shop Owners
- 🔐 **Email/Password Authentication** - Secure login with password hashing
- 🖼️ **Product Catalog** - Browse masala products with images, descriptions, and prices
- 📦 **Order Placement** - Place orders with quantity selection
- 📋 **Order History** - View past orders and their current status
- 🔍 **Order Tracking** - Real-time order tracking (pending → confirmed → dispatched → delivered)
- 📱 **Mobile Responsive** - Works perfectly on phones and tablets

### For Admin/Agency
- 📊 **Admin Dashboard** - Overview of products, orders, and customers
- ➕ **Product Management** - Add, edit, and delete products
- 👥 **Customer Management** - View all registered shop owners and their order history
- 📦 **Order Management** - View and update status of all orders
- 📈 **Order Tracking** - Update order status (pending → confirmed → dispatched → delivered)
- 💼 **Complete Control** - Full access to all system features

### Additional Features
- 🎨 **Professional UI** - Beautiful, responsive design with custom CSS
- 🛡️ **Security** - Passwords hashed with Werkzeug security
- 💾 **Database** - SQLite with SQLAlchemy ORM
- 🚀 **Easy Deployment** - Ready to deploy on platforms like Render

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **Python Flask** | Backend web framework |
| **SQLite** | Database |
| **SQLAlchemy** | ORM for database operations |
| **Flask-Login** | User session management |
| **Werkzeug** | Password hashing |
| **Bootstrap 5** | Frontend styling |
| **Jinja2** | HTML templating |
| **HTML/CSS** | Custom styling and structure |

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for cloning)

## 🚀 Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/udhaykarthiik/MasalaAgency.git
cd MasalaAgency

Step 2: Create Virtual Environment

# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate


Step 3: Install Dependencies
pip install flask flask-sqlalchemy flask-login

Step 4: Initialize Database

flask shell
>>> from app import db
>>> db.create_all()
>>> exit()

Step 5: Add Sample Products

flask add-sample-products

Step 6: Create Admin User

flask create-agency

Step 7: Run the Application

python app.py

📱 Default Users
Role	Email	Password	Phone
Admin	admin@masalaagency.com	admin123	9999999999
Shop Owner	(register new)	user choice	optional

🗂️ Project Structure

MasalaAgency/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore file
├── README.md             # Project documentation
├── static/               # Static files
│   ├── css/              # CSS stylesheets
│   │   └── style.css     # Custom styling
│   ├── images/           # Product images
│   └── js/               # JavaScript files
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Homepage
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── profile.html      # User profile
│   ├── product_detail.html # Product details
│   ├── category.html     # Category view
│   ├── track_order.html  # Order tracking
│   ├── 404.html          # 404 error page
│   ├── 500.html          # 500 error page
│   └── admin/            # Admin templates
│       ├── dashboard.html
│       ├── products.html
│       ├── add_product.html
│       ├── edit_product.html
│       ├── orders.html
│       ├── customers.html
│       └── customer_detail.html
└── instance/             # Database folder
    └── masala.db         # SQLite database


🎯 Usage Guide
For Shop Owners
Register - Click "Register as Shop Owner" and fill in your details

Login - Use your email and password

Browse Products - View all masala products by category

Place Order - Click on any product, select quantity, and place order

Track Orders - Go to "My Orders" to view order history and status

For Admin
Login - Use admin credentials (admin@masalaagency.com / admin123)

Dashboard - View overview of products, orders, and customers

Manage Products - Add, edit, or delete products

Manage Orders - View all orders and update their status

Manage Customers - View all registered shop owners and their order history


📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

📧 Contact
Developer: Udhay Karthik
Email: udhaykarthik51@gmail.com
GitHub: @udhaykarthiik
Project Link: https://github.com/udhaykarthiik/MasalaAgency
