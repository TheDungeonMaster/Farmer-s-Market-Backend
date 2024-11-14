#Imports
from itertools import product
import math
import random
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from flask_scss import Scss
import pymysql
import mysql.connector 
import pyotp
import os

#App
app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:labkafarmer01@farmer-market.cheqy8c0cs83.eu-west-2.rds.amazonaws.com/farmermarketdb'
engine = create_engine("mysql://admin:labkafarmer01@farmer-market.cheqy8c0cs83.eu-west-2.rds.amazonaws.com/farmermarketdb")
Session = sessionmaker(bind=engine)
login_manager = LoginManager(app)
mail = Mail(app)

#Database connections

db = SQLAlchemy(app)

# db = pymysql.connect(host = "farmer-market.cheqy8c0cs83.eu-west-2.rds.amazonaws.com",
#                     user = "admin",
#                     password = "labkafarmer01",
#                     database ="farmermarketdb")

db_config = {
    'host': 'farmer-market.cheqy8c0cs83.eu-west-2.rds.amazonaws.com',
    'user': 'admin',
    'password': 'labkafarmer01',
    'database': 'farmermarketdb'
}

class Product(db.Model):
    __tablename__ = 'product'
    product_id= db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(50), unique=True, nullable=False)
    description=db.Column(db.String(50), nullable=False)
    category=db.Column(db.String(15), nullable=False)
    organic_certification=db.Column(db.Integer, nullable=False)
    quantity=db.Column(db.Integer, nullable=False)
    price=db.Column(db.Integer, nullable=False)
    farm_name = db.Column(db.String(50))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    two_factor_secret = db.Column(db.String(16))
    def get_id(self):
           return (self.user_id)

class Buyer(db.Model):
    __tablename__ = 'buyer'
    buyer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    address = db.Column(db.String(150))
    username = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True)
    phone_number = db.Column(db.String(50), unique=True)
    def get_id(self):
           return (self.user_id)
    
class Farmer(db.Model):
    __tablename__ = 'farmer'
    farmer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    username = db.Column(db.String(20))
    phone_number = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(100), unique = True)
    status = db.Column(db.String(20), default='pending')
    def get_id(self):
           return (self.user_id)
    
class Farm(db.Model):
    __tablename__ = 'farm'
    farm_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    crop_type = db.Column(db.String(50))
    farm_name = db.Column(db.String(50))
    location = db.Column(db.String(100))
    farm_size = db.Column(db.String(50))
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmer.farmer_id'))

#USER LOADER
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#GENERAL
@app.route('/')
def index():
    return render_template('index.html', products=products)

@app.route('/products')
def products():
    products = Product.query.all()
    return render_template('products.html', products = products)

#ADMINS
@app.route('/setup-admin')
def setup_admin():
    if not User.query.filter_by(role='admin').first():
        hashed_password = generate_password_hash('admin', method='pbkdf2:sha256')
        admin = User(email='zhandos.dias.m@gmail.com', password=hashed_password, role='admin')
        db.session.add(admin)
        db.session.commit()
        return "Admin created!"
    return "Admin already exists."

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')

@app.route('/admin/pending-farmers', methods=['GET'])
@login_required
def pending_farmers():
    pending_farmers = Farmer.query.filter_by(status='pending').all()
    
    farmer_list = [
        {
            "farmer_id": farmer.farmer_id,
            "first_name": farmer.first_name,
            "last_name": farmer.last_name,
            "username": farmer.username,
            "phone_number": farmer.phone_number,
            "email": farmer.email,
        }
        for farmer in pending_farmers
    ]
    return jsonify(farmer_list)

@app.route('/admin/approve-farmer/<int:farmer_id>', methods=['POST'])
@login_required
def approve_farmer(farmer_id):
    if current_user.role != 'admin':
        return jsonify({"message": "Unauthorized"}), 403

    farmer = Farmer.query.get(farmer_id)
    if farmer:
        farmer.status = "approved"
        db.session.commit()

        # Send an approval notification email
        # msg = Message('Account Approved', recipients=[user.email])
        # msg.body = 'Your farmer account has been approved and is now active.'
        # mail.send(msg)

        return redirect(url_for('admin'))
    return jsonify({"message": "Farmer not found"}), 404

@app.route('/admin/reject-farmer/<int:farmer_id>', methods=['POST'])
@login_required
def reject_farmer(farmer_id):
    if current_user.role != 'admin':
        return jsonify({"message": "Unauthorized"}), 403

    farmer = Farmer.query.get(farmer_id)
    if farmer:
        farmer.status = "rejected"
        db.session.commit()

        # Optionally, send a rejection notification email
        # user = User.query.get(farmer.farmer_id)
        # msg = Message('Account Rejected', recipients=[user.email])
        # msg.body = 'Your farmer account registration has been rejected.'
        # mail.send(msg)

        # return jsonify({"message": "Farmer rejected"})
        return redirect(url_for('admin'))
    return jsonify({"message": "Farmer not found"}), 404

@app.route('/register')
def register():
    return render_template('register.html')

#FARMERS
@app.route('/register/farmer')
def register_farmer():
    return render_template('register_farmer.html')

@app.route('/register/farmer', methods=['POST'])
def register_farmer_post():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    username = request.form.get('username')
    email = request.form.get('email')
    phone_number = request.form.get('phone_number')
    password = request.form.get('password')
    farm_name = request.form.get('farm_name')
    crop_type = request.form.get('crop_type')
    location = request.form.get('location')
    farm_size = request.form.get('farm_size')
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
    user = User(email=email, password=hashed_password, role='farmer')
    db.session.add(user)
    db.session.flush()
    
    farmer = Farmer(first_name=first_name, last_name=last_name, username = username, phone_number=phone_number, email=email)
    db.session.add(farmer)
    db.session.commit()
    
    farm = Farm(farm_name=farm_name, crop_type=crop_type, location=location, farm_size=farm_size, farmer_id=farmer.farmer_id)
    db.session.add(farm)
    db.session.commit()
    
    login_user(user)
    return redirect(url_for('farmer_dashboard', farmer_id = farmer.farmer_id))

@app.route('/farmer/farm-info/<int:farmer_id>', methods=['GET'])
@login_required
def get_farm_info(farmer_id):
    
    farm = Farm.query.filter_by(farmer_id=farmer_id).first()

    response_data = {
        "farm_name": farm.name,
        "location": farm.location,
        "size": farm.size,
        "crop_type": farm.crop_type,
    }
    
    return jsonify(response_data)

@app.route('/farmer/farmer_dashboard/<int:farmer_id>')
@login_required
def farmer_dashboard(farmer_id):
    
    farm = Farm.query.filter_by(farmer_id=farmer_id).first()
    products = Product.query.filter_by(farm_name=farm.farm_name)
    low_stock_products = [product for product in products if product.quantity < 5]
    return render_template('farmer_dashboard.html',farm=farm, farmer_id=farmer_id, products=products, low_stock_products=low_stock_products)

@app.route('/farmer/farmer_dashboard/<int:farmer_id>', methods=['POST'])
@login_required
def delete_product(farmer_id):
    product_id = request.form.get('product_id')
    product = Product.query.get(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('farmer_dashboard', farmer_id=farmer_id))

@app.route('/farmer/<int:farmer_id>/edit-product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(farmer_id, product_id):
    product = Product.query.get(product_id)
    if request.method == 'POST':
        # Update product details with form data
        product.title = request.form.get('title')
        product.category = request.form.get('category')
        product.price = request.form.get('price')
        product.quantity = request.form.get('quantity')
        product.description = request.form.get('description')
        product.organic_certification = request.form.get('organic_certification')
            
        db.session.commit()
        return redirect(url_for('farmer_dashboard', farmer_id=farmer_id))
        
    return render_template('edit_product.html', product=product, farmer_id=farmer_id)
    
@app.route('/farmer/<int:farmer_id>/add-product', methods=['GET', 'POST'])
@login_required
def add_product(farmer_id):
    farm = Farm.query.filter_by(farmer_id=farmer_id).first()
    farm_name = farm.farm_name
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        price = request.form.get('price')
        quantity = request.form.get('quantity')
        description = request.form.get('description')
        organic_certification = request.form.get('organic_certification')
        
        product = Product(title=title, description=description, category=category,organic_certification=organic_certification, quantity=quantity, price=price, farm_name = farm_name)
        db.session.add(product)
        db.session.commit()

        return redirect(url_for('farmer_dashboard', farmer_id=farmer_id))
    
    return render_template('add_product.html', farmer_id=farmer_id, products=products)

#BUYERS        
@app.route('/register/buyer')
def register_buyer():
    return render_template('register_buyer.html')

@app.route('/register/buyer', methods=['POST'])
def register_buyer_post():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    username = request.form.get('username')
    email = request.form.get('email')
    phone_number = request.form.get('phone_number')
    address = request.form.get('address')
    password = request.form.get('password')
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
    user = User(email=email, password=hashed_password, role='buyer')
    db.session.add(user)
    db.session.flush()
    
    buyer = Buyer(first_name=first_name, last_name=last_name, address=address, username = username, email=email, phone_number=phone_number)
    db.session.add(buyer)
    db.session.commit()
    
    return jsonify({"message": "Buyer registered successfully"})

@app.route('/admin/buyers', methods=['GET'])
@login_required
def buyers():
    buyers = Buyer.query.all()
    
    buyer_list = [
        {
            "buyer_id": buyer.buyer_id,
            "first_name": buyer.first_name,
            "last_name": buyer.last_name,
            "address": buyer.address,
            "username": buyer.username,
            "email": buyer.email,
            "phone_number": buyer.phone_number,
        }
        for buyer in buyers
    ]
    return jsonify(buyer_list)

#LOGIN MANAGER
@app.route('/login')
def login():
    logout_user()
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and check_password_hash(user.password, password):
        if user.role == 'admin':
            login_user(user)
            return redirect(url_for('admin'))
        elif user.role == 'farmer':
            login_user(user)
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary = True)
            query = f"SELECT farmer_id FROM farmer WHERE farmer.email = '{email}'"
            cursor.execute(query)
            farmer_id = cursor.fetchone()['farmer_id']
            cursor.close()
            return redirect(url_for('farmer_dashboard', farmer_id = farmer_id))
        elif user.role == 'buyer':
            login_user(user)
            return redirect(url_for('products'))

    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/logout')
@login_required
def  logout():
    logout_user()
    return redirect(url_for('index'))

#Main
if __name__ in '__main__':
        app.run(debug = True)

