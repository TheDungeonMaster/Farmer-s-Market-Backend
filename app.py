#Imports
from itertools import product
import math
import random
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, and_, or_, select, join
from sqlalchemy.orm import sessionmaker
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import mysql.connector 
import pyotp
import os
from datetime import datetime
from flask_jwt_extended import JWTManager, create_access_token

#App
app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['JWT_SECRET_KEY'] = 'api_token_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:labkafarmer01@farmer-market.cheqy8c0cs83.eu-west-2.rds.amazonaws.com/farmermarketdb'
engine = create_engine("mysql://admin:labkafarmer01@farmer-market.cheqy8c0cs83.eu-west-2.rds.amazonaws.com/farmermarketdb")
Session = sessionmaker(bind=engine)
login_manager = LoginManager(app)
mail = Mail(app)
jwt = JWTManager(app)

#Database connections

db = SQLAlchemy(app)

# db = pymysql.connect(host = "farmer-market.cheqy8c0cs83.eu-west-2.rds.amazonaws.com",
#                     user = "admin",
#                     password = "labkafarmer01",
#                     database ="farmermarketdb")

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
    status = db.Column(db.String(20), default='active')
    username = db.Column(db.String(20))
    auth_token = db.Column(db.String(50), unique=True)
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
    status = db.Column(db.String(20), default='active')
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
    
class Chatroom(db.Model):
    __tablename__ = 'chatroom'
    chatroom_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_1 = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    user_2 = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    
class Messages(db.Model):
    __tablename__ = 'messages'
    message_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chatroom_id = db.Column(db.Integer, db.ForeignKey('chatroom.chatroom_id'))
    text = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    m_time = db.Column(db.DateTime, default=datetime.utcnow)
    edited = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='unseen')
    
class Order(db.Model):
    __tablename__ = 'order'
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    status = db.Column(db.String(20), default='pending')
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    preference = db.Column(db.String(100))
    buyer_id = db.Column(db.Integer, db.ForeignKey('buyer.buyer_id'))
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmer.farmer_id'))
    
class OrderItem(db.Model):
    __tablename__ = 'orderitem'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.order_id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'))
    amount = db.Column(db.Integer)
    
class Notifications(db.Model):
    __tablename__ = 'notifications'
    n_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    text = db.Column(db.String(200))
    title = db.Column(db.String(50))
    n_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='unseen')
    
#USER LOADER
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#GENERAL
@app.route('/')
def index():
    products = Product.query.all()
    role = current_user.role if current_user.is_authenticated else None
    farmer_id = None
    buyer_id = None
    status = None
    if role == 'farmer':
        farmer = Farmer.query.filter_by(email=current_user.email).first()
        status = farmer.status
        if farmer:
            farmer_id = farmer.farmer_id
    elif role == 'buyer':
        buyer = Buyer.query.filter_by(email=current_user.email).first()
        if buyer:
            buyer_id = buyer.buyer_id
    username = current_user.username if current_user.is_authenticated else None
    user = current_user if current_user.is_authenticated else None
    return render_template('index.html', products=products, user=user, username=username, role=role, farmer_id=farmer_id, buyer_id=buyer_id, status=status)

@app.route('/notifications')
def notifications():
    notifications = Notifications.query.filter_by(user_id=current_user.user_id).all()
    for notification in notifications:
        notification.status = 'seen'
        db.session.commit()
    return render_template('notifications.html', notifications=notifications)

@app.route('/send-notification/<int:user_id>', methods=['POST'])
def send_notification():
    data = request.get_json()
    title = data.get('title')
    text = data.get('text')
    user = User.query.get(user_id)
    notification = Notifications(user_id=user.user_id, title=title, text=text)
    db.session.add(notification)
    db.session.commit()
    return jsonify({'message': 'Notification sent successfully'}), 200

@app.route('/products')
def products():
    products = Product.query.all()
    if current_user.is_authenticated:
        role = current_user.role
    else:
        role = None
    return render_template('products.html', products = products, role = role)

@app.route('/products/vegetables')
def vegetables():
    vegetables = Product.query.filter_by(category='Vegetables').all()
    if current_user.is_authenticated:
        role = current_user.role
    else:
        role = None
    return render_template('products.html', products = vegetables, role = role)

@app.route('/products/fruits')
def fruits():
    fruits = Product.query.filter_by(category='fruits').all()
    if current_user.is_authenticated:
        role = current_user.role
    else:
        role = None
    return render_template('products.html', products = fruits, role = role)

@app.route('/products/seeds')
def seeds():
    seeds = Product.query.filter_by(category='seeds').all()
    if current_user.is_authenticated:
        role = current_user.role
    else:
        role = None
    return render_template('products.html', products = seeds, role = role)

@app.route('/search')
def search_products():
    query = request.args.get('query')
    products = Product.query.filter(or_(Product.title.contains(query), Product.description.contains(query), Product.farm_name.contains(query), Product.category.contains(query))).all()
    if current_user.is_authenticated:
        role = current_user.role
    else:
        role = None
    return render_template('products.html', products = products, role = role) 

#ADMINS
@app.route('/setup-admin')
def setup_admin():
    if not User.query.filter_by(role='admin').first():
        hashed_password = generate_password_hash('admin', method='pbkdf2:sha256')
        admin = User(email='admin@mail.com', password=hashed_password, role='admin', username='admin')
        db.session.add(admin)
        db.session.commit()
        return "Admin created!"
    return "Admin already exists."

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin' and current_user.role != 'moderator':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    return render_template('admin.html', role=current_user.role)

@app.route('/delete-user/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin' and current_user.role != 'moderator':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    user = User.query.get(user_id)
    if user.role == 'buyer':
        buyer = Buyer.query.filter_by(email=user.email).first()
        db.session.delete(buyer)
    elif user.role == 'farmer':
        farmer = Farmer.query.filter_by(email=user.email).first()
        db.session.delete(farmer)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"}), 200

@app.route('/delete-farmer/<int:farmer_id>', methods=['DELETE'])
@login_required
def delete_farmer(farmer_id):
    if current_user.role != 'admin' and current_user.role != 'moderator':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    farmer = Farmer.query.get(farmer_id)
    user = User.query.filter_by(email=farmer.email).first()
    db.session.delete(user)
    db.session.delete(farmer)
    db.session.commit()
    return jsonify({"message": "Farmer deleted"}), 200

@app.route('/pending-farmers', methods=['GET'])
@login_required
def pending_farmers():
    if current_user.role != 'admin' and current_user.role != 'moderator':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    pending_farmers = Farmer.query.filter_by(status='pending').all()
    
    farmer_list = []
    for farmer in pending_farmers:
        farm = Farm.query.filter_by(farmer_id=farmer.farmer_id).first()
        farmer_list.append({
            "farmer_id": farmer.farmer_id,
            "first_name": farmer.first_name,
            "last_name": farmer.last_name,
            "username": farmer.username,
            "phone_number": farmer.phone_number,
            "email": farmer.email,
            'farm_name': farm.farm_name,
            'crop_type': farm.crop_type,
            'farm_size': farm.farm_size,
            'location': farm.location,
        })
    return jsonify(farmer_list)

@app.route('/farmers', methods=['GET'])
@login_required
def approved_farmers():
    if current_user.role != 'admin' and current_user.role != 'moderator':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    approved_farmers = Farmer.query.filter_by(status='approved').all()
    
    approved_farmers_list = []
    for approved_farmer in approved_farmers:
        farm = Farm.query.filter_by(farmer_id=approved_farmer.farmer_id).first()
        approved_farmers_list.append({
            "farmer_id": approved_farmer.farmer_id,
            "first_name": approved_farmer.first_name,
            "last_name": approved_farmer.last_name,
            "username": approved_farmer.username,
            "phone_number": approved_farmer.phone_number,
            "email": approved_farmer.email,
            'farm_name': farm.farm_name,
            'crop_type': farm.crop_type,
            'farm_size': farm.farm_size,
            'location': farm.location,
        })
    return jsonify(approved_farmers_list)

@app.route('/rejected-farmers', methods=['GET'])
@login_required
def rejected_farmers():
    if current_user.role != 'admin' and current_user.role != 'moderator':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    rejected_farmers = Farmer.query.filter_by(status='rejected').all()
    rejected_farmers_list = []
    for rejected_farmer in rejected_farmers:
        farm = Farm.query.filter_by(farmer_id=rejected_farmer.farmer_id).first()
        rejected_farmers_list.append({
            "farmer_id": rejected_farmer.farmer_id,
            "first_name": rejected_farmer.first_name,
            "last_name": rejected_farmer.last_name,
            "username": rejected_farmer.username,
            "phone_number": rejected_farmer.phone_number,
            "email": rejected_farmer.email,
            'farm_name': farm.farm_name,
            'crop_type': farm.crop_type,
            'farm_size': farm.farm_size,
            'location': farm.location,
        })
    return jsonify(rejected_farmers_list)

@app.route('/banned-users', methods=['GET'])
@login_required
def banned_users():
    if current_user.role != 'admin' and current_user.role != 'moderator':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    banned_users = User.query.filter_by(status='banned').all()
    
    banned_users_list = []
    for banned_user in banned_users:
        if banned_user.role == 'farmer':
            banned_farmer = Farmer.query.filter_by(email=banned_user.email).first()
            banned_users_list.append({
                "user_id": banned_user.user_id,
                'role': banned_user.role,
                "first_name": banned_farmer.first_name,
                "last_name": banned_farmer.last_name,
                "username": banned_farmer.username,
                "email": banned_farmer.email,
                "phone_number": banned_farmer.phone_number,
            })
        elif banned_user.role == 'buyer':
            banned_buyer = Buyer.query.filter_by(email=banned_user.email).first()
            banned_users_list.append({
            "user_id": banned_user.user_id,
            'role': banned_user.role,
            "first_name": banned_buyer.first_name,
            "last_name": banned_buyer.last_name,
            "username": banned_buyer.username,
            "phone_number": banned_buyer.phone_number,
            "email": banned_buyer.email,
        })
    return jsonify(banned_users_list)

@app.route('/banned-farmers', methods=['GET'])
@login_required
def banned_farmers():
    if current_user.role != 'admin' and current_user.role != 'moderator':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    banned_users = User.query.filter_by(status = 'banned', role = 'farmer').all()
    
    banned_users_list = []
    for banned_user in banned_users:
        banned_farmer = Farmer.query.filter(_or(Farmer.status == 'banned'), email=banned_user.email).first()
        banned_users_list.append({
            "user_id": banned_user.user_id,
            'role': 'farmer',
            "first_name": banned_farmer.first_name,
            "last_name": banned_farmer.last_name,
            "username": banned_farmer.username,
            "email": banned_farmer.email,
            "phone_number": banned_farmer.phone_number,
        })
    return jsonify(banned_users_list)

@app.route('/banned-buyers', methods=['GET'])
@login_required
def banned_buyers():
    if current_user.role != 'admin' and current_user.role != 'moderator':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    banned_users = User.query.filter_by(status='banned', role='buyer').all()
    
    banned_users_list = []
    for banned_user in banned_users:
        banned_buyer = Buyer.query.filter_by(email=banned_user.email).first()
        banned_users_list.append({
            "user_id": banned_user.user_id,
            'role': 'buyer',
            "first_name": banned_buyer.first_name,
            "last_name": banned_buyer.last_name,
            "username": banned_buyer.username,
            "email": banned_buyer.email,
            "phone_number": banned_buyer.phone_number,
        })
    return jsonify(banned_users_list)

@app.route('/approve-farmer/<int:farmer_id>', methods=['POST'])
@login_required
def approve_farmer(farmer_id):
    if current_user.role != 'admin' and current_user.role != 'moderator':
        return jsonify({"message": "Unauthorized"}), 403
    farmer = Farmer.query.get(farmer_id)
    if farmer:
        farmer.status = "approved"
        db.session.commit()
        user = User.query.filter_by(email=farmer.email).first()
        notification_title = "You application has been approved"
        notification_text = "Your application has been approved by the admin. You now have access to the dashboard where you can add new products and fullfill orders."
        notification = Notifications(user_id=user.user_id, title=notification_title, text=notification_text)
        db.session.add(notification)
        db.session.commit()
        return jsonify({"message": "Farmer approved"}), 200
    return jsonify({"message": "Farmer not found"}), 404

@app.route('/reject-farmer/<int:farmer_id>', methods=['POST'])
@login_required
def reject_farmer(farmer_id):
    if current_user.role != 'admin' and current_user.role != 'moderator':
        return jsonify({"message": "Unauthorized"}), 403
    farmer = Farmer.query.get(farmer_id)
    if farmer:
        farmer.status = "rejected"
        user = User.query.filter_by(email=farmer.email).first()
        user.status = 'banned'
        db.session.commit()
        user = User.query.filter_by(email=farmer.email).first()
        notification_title = "You application has been rejected"
        notification_text = "Your application has been rejected by the admin. Please contact the admin by email on admin@mail.com for more information."
        notification = Notifications(user_id=user.user_id, title=notification_title, text=notification_text)
        db.session.add(notification)
        db.session.commit()
        return jsonify({"message": "Farmer rejected"}), 200
    
    return jsonify({"message": "Farmer not found"}), 404

@app.route('/ban-farmer/<int:farmer_id>', methods=['POST'])
@login_required
def ban_farmer(farmer_id):
    if current_user.role != 'admin' and current_user.role != 'moderator':
        return jsonify({"message": "Unauthorized"}), 403

    farmer = Farmer.query.get(farmer_id)
    email = farmer.email
    user = User.query.filter_by(email=email).first()
    if farmer:
        farmer.status = "banned"
        user.status = "banned"
        db.session.commit()
        return jsonify({"message": "Farmer banned"})
    return jsonify({"message": "Farmer not found"}), 404

@app.route('/ban-buyer/<int:buyer_id>', methods=['POST'])
@login_required
def ban_buyer(buyer_id):
    if current_user.role != 'admin' and current_user.role != 'moderator':
        return jsonify({"message": "Unauthorized"}), 403

    buyer = Buyer.query.get(buyer_id)
    email = buyer.email
    user = User.query.filter_by(email=email).first()
    if buyer:
        buyer.status = "banned"
        user.status = "banned"
        db.session.commit()
        return jsonify({"message": "Buyer banned"})
    return jsonify({"message": "Buyer not found"}), 404

@app.route('/unban-user/<int:user_id>', methods=['POST'])
@login_required
def unban_user(user_id):
    if current_user.role != 'admin' and current_user.role != 'moderator':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    user = User.query.get(user_id)
    user.status = "active"
    db.session.commit()
    if user.role == 'farmer':
        farmer = Farmer.query.filter_by(email=user.email).first()
        farmer.status = "approved"
        db.session.commit()
    elif user.role == 'buyer':
        buyer = Buyer.query.filter_by(email=user.email).first()
        buyer.status = "active"
        db.session.commit()
    return jsonify({"message": "User unbanned"}), 200

@app.route('/admin/create-moderator', methods=['POST'])
@login_required
def create_moderator():
    if current_user.role != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "Email already exists"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"success": False, "message": "Username already exists"}), 400

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    moderator = User(email=email, username=username, password=hashed_password, role='moderator', status = 'active')
    db.session.add(moderator)
    db.session.commit()

    return jsonify({"success": True, "message": "Moderator created successfully"})

@app.route('/admin/moderators', methods=['GET'])
@login_required
def get_moderators():
    if current_user.role != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    moderators = User.query.filter_by(role='moderator').all()
    moderators_list = [{"user_id": mod.user_id, "email": mod.email, "username": mod.username} for mod in moderators]
    return jsonify(moderators_list)

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
    
    if username in [user.username for user in User.query.all()] and email in [user.email for user in User.query.all()]:
        flash('Both username and email already exist', 'error')
        return redirect(url_for('register_farmer'))
    if email in [user.email for user in User.query.all()]:
        flash('Email already exists')
        return redirect(url_for('register_farmer'))
    if username in [user.username for user in User.query.all()]:
        flash('Username already exists')
        return redirect(url_for('register_farmer'))
    
    user = User(email=email, password=hashed_password, role='farmer', username = username)
    db.session.add(user)
    db.session.flush()
    
    farmer = Farmer(first_name=first_name, last_name=last_name, username = username, phone_number=phone_number, email=email)
    db.session.add(farmer)
    db.session.commit()
    
    farm = Farm(farm_name=farm_name, crop_type=crop_type, location=location, farm_size=farm_size, farmer_id=farmer.farmer_id)
    db.session.add(farm)
    db.session.commit()
    
    login_user(user)
    return redirect(url_for('login'))

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
    orders = Order.query.filter_by(farmer_id=farmer_id, status='ordered').all()
    farm = Farm.query.filter_by(farmer_id=farmer_id).first()
    products = Product.query.filter_by(farm_name=farm.farm_name).all()
    low_stock_products = [product for product in products if product.quantity < 5]
    order_list = []
    for order in orders:
        order_items = OrderItem.query.filter_by(order_id=order.order_id).all()
        for order_item in order_items:
            product = Product.query.filter_by(product_id=order_item.product_id).first()
            order_list.append({
                "order_id": order.order_id,
                "product_id": order_item.product_id,
                "title": product.title,
                "price": product.price,
                "quantity": order_item.amount
            })
    return render_template('farmer_dashboard.html',farm=farm, farmer_id=farmer_id, products=products, low_stock_products=low_stock_products, order_list=order_list)

@app.route('/farmer/<int:farmer_id>/fulfill_order/<int:order_id>')
@login_required
def fulfill_order(farmer_id, order_id):
    order = Order.query.get(order_id)
    order_items = OrderItem.query.filter_by(order_id=order.order_id).all()
    for order_item in order_items:
        product = Product.query.filter_by(product_id=order_item.product_id).first()
        product.quantity -= order_item.amount
        db.session.commit()
    order.status = 'fulfilled'
    db.session.commit()
    buyer = Buyer.query.filter_by(buyer_id=order.buyer_id).first()
    user = User.query.filter_by(email=buyer.email).first()
    farm = Farm.query.filter_by(farmer_id=farmer_id).first()
    notification_text = f"Your order {order.order_id} has been fulfilled by {farm.farm_name}."
    notification_title = "Order Fulfilled"
    notification = Notifications(user_id=user.user_id, text=notification_text, title=notification_title)
    db.session.add(notification)
    db.session.commit()
    return redirect(url_for('farmer_dashboard', farmer_id=farmer_id))

@app.route('/farmer/<int:farmer_id>/info')
@login_required
def display_info_id(farmer_id):
    farm = Farm.query.filter_by(farmer_id=farmer_id).first()
    products = Product.query.filter_by(farm_name=farm.farm_name).all()
    farm_name = farm.farm_name
    return render_template('farmer_info.html', products=products, farmer_id=farmer_id, farm_name=farm_name, farm = farm)

@app.route('/farmer/<string:farm_name>/info')
@login_required
def display_info_product(farm_name):
    role = current_user.role
    farm = Farm.query.filter_by(farm_name=farm_name).first()
    farmer = Farmer.query.filter_by(farmer_id=farm.farmer_id).first()
    farmer_id = farmer.farmer_id
    products = Product.query.filter_by(farm_name=farm.farm_name).all()
    farm_name = farm.farm_name
    return render_template('farmer_info.html', products=products, farmer_id=farmer_id, farm_name=farm_name, farm = farm, role = role)

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

@app.route('/farmer/<int:farmer_id>/orders', methods=['GET'])
@login_required
def farmer_orders(farmer_id):
    farm = Farm.query.filter_by(farmer_id=farmer_id).first()
    products = Product.query.filter_by(farm_name=farm.farm_name).all()
    for product in products:
        order_items = OrderItem.query.filter_by(product_id=product.product_id).all()
        for order_item in order_items:
            orders = Order.query.filter_by(order_id=order_item.order_id, status='ordered').all()
            for order in orders:
                order_list = []
                product = Product.query.filter_by(product_id=order_item.product_id).first()
                order_list.append({
                    "order_id": order.order_id,
                    "product_id": order_item.product_id,
                    "title": product.title,
                    "price": product.price,
                    "quantity": order_item.amount
                })
    return jsonify(order_list), 200

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
    
    if username in [user.username for user in User.query.all()] and email in [user.email for user in User.query.all()]:
        flash('Both username and email already exist', 'error')
        return redirect(url_for('register_buyer'))
    if email in [user.email for user in User.query.all()]:
        flash('Email already exists', 'error')
        return redirect(url_for('register_buyer'))
    if username in [user.username for user in User.query.all()]:
        flash('Username already exists', 'error')
        return redirect(url_for('register_buyer'))

    user = User(email=email, password=hashed_password, role='buyer', username = username)
    db.session.add(user)
    db.session.flush()
    
    buyer = Buyer(first_name=first_name, last_name=last_name, address=address, username = username, email=email, phone_number=phone_number)
    db.session.add(buyer)
    db.session.commit()
    
    return redirect(url_for('login'))

@app.route('/buyers', methods=['GET'])
@login_required
def buyers():
    if current_user.role != 'admin' and current_user.role != 'moderator':
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    buyers = Buyer.query.filter_by(status='active').all()
    
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

#ORDERS
@app.route('/order/<int:buyer_id>')
@login_required
def order(buyer_id):
    order = Order.query.filter_by(buyer_id=buyer_id).first()
    if not order:
        return jsonify({"message": "Order not found"}), 404
    order_items = OrderItem.query.filter_by(order_id=order.order_id).all()
    order_list = []
    for order_item in order_items:
        product = Product.query.filter_by(product_id=order_item.product_id).first()
        order_list.append({
            "order_id": order.order_id,
            "product_id": order_item.product_id,
            "title": product.title,
            "price": product.price,
            "quantity": order_item.quantity
        })
    return jsonify(order_list), 200

@app.route('/shopping_cart/<int:buyer_id>')
@login_required
def shopping_cart(buyer_id):
    grand_total = 0
    orders = Order.query.filter_by(buyer_id=buyer_id, status='pending').all()
    if not orders:
        return render_template('shopping_cart.html', order_list=[], grand_total=0)
    order_list = []
    for order in orders:
        orderitems = OrderItem.query.filter_by(order_id=order.order_id).all()
        orderitem_list = []
        for orderitem in orderitems:
            product = Product.query.filter_by(product_id=orderitem.product_id).first()
            total_price = product.price * orderitem.amount
            grand_total += total_price
            orderitem_list.append({
                "orderitem_id": orderitem.id,
                "order_id": order.order_id,
                "product_id": orderitem.product_id,
                "title": product.title,
                "price": product.price,
                "amount": orderitem.amount
            })
        order_list.append(orderitem_list)
    print(order_list)
    return render_template('shopping_cart.html', orders = orders, order_list=order_list, grand_total=grand_total, buyer_id=buyer_id)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    amount = request.form.get('amount')
    buyer = Buyer.query.filter_by(email=current_user.email).first()
    product = Product.query.filter_by(product_id=product_id).first()
    farm = Farm.query.filter_by(farm_name=product.farm_name).first()
    farmer_id = farm.farmer_id
    order = Order.query.filter_by(buyer_id=buyer.buyer_id, farmer_id=farmer_id, status='pending').first()
    if not order:
        order = Order(buyer_id=buyer.buyer_id, farmer_id=farmer_id, status='pending', preference='N/A')
        db.session.add(order)
        db.session.commit()
    order_item = OrderItem(order_id=order.order_id, product_id=product_id, amount=amount)
    db.session.add(order_item)
    db.session.commit()
    return redirect(request.referrer)

@app.route('/remove_from_cart/<int:orderitem_id>', methods=['DELETE', 'POST'])
@login_required
def remove_from_cart(orderitem_id):
    amount = request.form.get('amount')
    amount = int(amount)
    orderitem = OrderItem.query.filter_by(id=orderitem_id).first()
    if not orderitem:
        return jsonify({"message": "Order item not found"}), 404
    order = Order.query.filter_by(order_id=orderitem.order_id).first()
    if not order:
        return jsonify({"message": "Order not found"}), 404
    buyer_id = order.buyer_id
    orderitem.amount -= amount
    if orderitem.amount <= 0:
        db.session.delete(orderitem)
    db.session.commit()
    return redirect(url_for('shopping_cart', buyer_id=buyer_id))
    
@app.route('/checkout')
@login_required
def checkout():
    buyer = Buyer.query.filter_by(email=current_user.email).first()
    orders = Order.query.filter_by(buyer_id=buyer.buyer_id, status='pending').all()
    if not orders:
        return jsonify({"message": "Orders not found"}), 404
    for order in orders:
        order.status = 'ordered'
        db.session.commit()
        farmer = Farmer.query.filter_by(farmer_id=order.farmer_id).first()
        other_user = User.query.filter_by(email=farmer.email).first()
        notification_title = "New Order"
        notification_text = "You have a new order from " + buyer.first_name + " " + buyer.last_name + ". Check you dashboard for more details."
        notification = Notifications(user_id=other_user.user_id, title=notification_title, text=notification_text)
        db.session.add(notification)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/order-history/<int:buyer_id>')
@login_required
def order_history(buyer_id):
    orders = Order.query.filter_by(buyer_id=buyer_id).all()
    order_details = []
    for order in orders:
        orderitems = OrderItem.query.filter_by(order_id=order.order_id).all()
        order_total_price = 0
        products = []
        for orderitem in orderitems:
            products.append({'product':Product.query.filter_by(product_id=orderitem.product_id).first(), 'orderitem':orderitem})
            product = Product.query.filter_by(product_id=orderitem.product_id).first()
            order_total_price += product.price * orderitem.amount
        order_details.append({'order':order, 'products':products, 'orderitems':orderitems, 'order_total_price':order_total_price})
    return render_template('order_history.html', orders=orders, order_details=order_details)

@app.route("/api/notifications/unseen-count", methods=["GET"])
def api_notifications_unseen_count():
    user_id = request.args.get('user_id')
    notifications = Notifications.query.filter_by(user_id=user_id, status='unseen').all()
    return jsonify(len(notifications)), 200

@app.route("/api/shopping_cart", methods=["POST"])
def api_shopping_cart():
    data = request.get_json()
    buyer_id = data.get("buyer_id")
    grand_total = 0
    orders = Order.query.filter_by(buyer_id=buyer_id, status='pending').all()
    if not orders:
        return jsonify([]), 200
    order_list = []
    total_amount = 0
    for order in orders:
        orderitems = OrderItem.query.filter_by(order_id=order.order_id).all()
        orderitem_list = []
        for orderitem in orderitems:
            product = Product.query.filter_by(product_id=orderitem.product_id).first()
            total_price = product.price * orderitem.amount
            grand_total += total_price
            total_amount += orderitem.amount
            orderitem_list.append({
                "orderitem_id": orderitem.id,
                "order_id": order.order_id,
                "product_id": orderitem.product_id,
                "title": product.title,
                "price": product.price,
                "amount": orderitem.amount
            })
        order_list.append(orderitem_list)
        order_list.append({"grand_total": grand_total, "total_amount": total_amount})
    return jsonify(order_list), 200

@app.route("/api/checkout", methods=["POST"])
def api_checkout():
    data = request.get_json()
    buyer_id = data.get("buyer_id")
    orders = Order.query.filter_by(buyer_id=buyer_id, status='pending').all()
    if not orders: 
        return jsonify({"message": "Orders not found"}), 404
    for order in orders:
        order.status = 'ordered'
        db.session.commit()
    return jsonify({"message": "Checkout successful"}), 200

@app.route('/api/add_to_cart', methods=['POST'])
def api_add_to_cart():
    data = request.get_json()
    product_id = data.get("product_id")
    buyer_id = data.get("buyer_id")
    amount = data.get("amount")
    buyer = Buyer.query.filter_by(buyer_id=buyer_id).first()
    product = Product.query.filter_by(product_id=product_id).first()
    farm = Farm.query.filter_by(farm_name=product.farm_name).first()
    farmer_id = farm.farmer_id
    order = Order.query.filter_by(buyer_id=buyer.buyer_id, farmer_id=farmer_id, status='pending').first()
    if not order:
        order = Order(buyer_id=buyer.buyer_id, farmer_id=farmer_id, status='pending', preference='N/A')
        db.session.add(order)
        db.session.commit()
    order_item = OrderItem(order_id=order.order_id, product_id=product_id, amount=amount)
    db.session.add(order_item)
    db.session.commit()
    return jsonify({"message": "Product added to cart"}), 200

@app.route('/api/remove_from_cart', methods=['DELETE'])
def api_remove_from_cart():
    data = request.get_json()
    buyer_id = data.get("buyer_id")
    order_item_id = data.get("order_item_id")
    amount = data.get("amount")
    orderitem = OrderItem.query.filter_by(id=orderitem_id).first()
    if not orderitem:
        return jsonify({"message": "Order item not found"}), 404
    order = Order.query.filter_by(order_id=orderitem.order_id).first()
    if not order:
        return jsonify({"message": "Order not found"}), 404
    buyer_id = order.buyer_id
    order_item.amount -= amount
    if order_item.amount <= 0:
        db.session.delete(order_item)
    db.session.commit()
    return jsonify({"message": "Product removed from cart"}), 200

@app.route('/api/order_history', methods=['GET'])
def api_order_history():
    data = request.get_json()
    buyer_id = data.get("buyer_id")

    orders = Order.query.filter_by(buyer_id=buyer_id).all()
    order_details = []

    for order in orders:
        orderitems = OrderItem.query.filter_by(order_id=order.order_id).all()
        order_total_price = 0
        products = []

        for orderitem in orderitems:
            product = Product.query.filter_by(product_id=orderitem.product_id).first()
            products.append({
                'product': {
                    'product_id': product.product_id,
                    'title': product.title,
                    'price': product.price,
                    'description': product.description,
                    'farm_name': product.farm_name,
                },
                'orderitem': {
                    'order_item_id': orderitem.id,
                    'order_id': orderitem.order_id,
                    'product_id': orderitem.product_id,
                    'amount': orderitem.amount,
                }
            })
            order_total_price += product.price * orderitem.amount

        order_details.append({
            'order': {
                'order_id': order.order_id,
                'status': order.status,
                'buyer_id': order.buyer_id,
                'farmer_id': order.farmer_id,
                'date': order.order_date.isoformat() if order.order_date else None,
            },
            'products': products,
            'order_total_price': order_total_price,
        })

    return jsonify(order_details), 200

#CHAT FOR MAIN PAGE
@app.route('/message/<string:farm_name>')
def message_farm(farm_name):
    farm = Farm.query.filter_by(farm_name=farm_name).first()
    farmer = Farmer.query.filter_by(farmer_id=farm.farmer_id).first()
    other_user = User.query.filter_by(username=farmer.username).first()
    chatroom = Chatroom.query.filter_by(user_1=current_user.user_id, user_2=other_user.user_id).first()
    if not chatroom:
        chatroom = Chatroom(user_1=current_user.user_id, user_2=other_user.user_id)
        db.session.add(chatroom)
        db.session.commit()
    chatroom_id = chatroom.chatroom_id
    return redirect(url_for('chatroom', chatroom_id=chatroom_id))

#START CHATTING USING USER ID
@app.route('/message/<int:user_id>')
def message_user(user_id):
    other_user = User.query.filter_by(user_id=user_id).first()
    chatroom = Chatroom.query.filter_by(user_1=current_user.user_id, user_2=other_user.user_id).first()
    if not chatroom:
        chatroom = Chatroom(user_1=current_user.user_id, user_2=other_user.user_id)
        db.session.add(chatroom)
        db.session.commit()
    chatroom_id = chatroom.chatroom_id
    return redirect(url_for('chatroom', chatroom_id=chatroom_id))

@app.route('/message/<int:farmer_id>')
def message_user_farmer(farmer_id):
    farmer = Farmer.query.filter_by(farmer_id=farmer_id).first()
    other_user = User.query.filter_by(email=farmer.email).first()
    chatroom = Chatroom.query.filter_by(user_1=current_user.user_id, user_2=other_user.user_id).first()
    if not chatroom:
        chatroom = Chatroom(user_1=current_user.user_id, user_2=other_user.user_id)
        db.session.add(chatroom)
        db.session.commit()
    chatroom_id = chatroom.chatroom_id
    return redirect(url_for('chatroom', chatroom_id=chatroom_id))

@app.route('/chatroom/<int:chatroom_id>')
def chatroom(chatroom_id):
    chatroom = Chatroom.query.filter_by(chatroom_id=chatroom_id).first()
    if current_user.user_id not in [chatroom.user_1, chatroom.user_2]:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    if current_user.user_id == chatroom.user_1:
        recipient_username = User.query.filter_by(user_id=chatroom.user_2).first().username
    elif current_user.user_id == chatroom.user_2:
        recipient_username = User.query.filter_by(user_id=chatroom.user_1).first().username
    user_1 = current_user.user_id
    user_2 = chatroom.user_2
    messages = Messages.query.filter_by(chatroom_id=chatroom_id).order_by(Messages.m_time.asc()).all()
    return render_template('chatroom.html', chatroom_id=chatroom_id, user_1=user_1, user_2=user_2, messages=messages, recipient_username=recipient_username)

@app.route('/send-message/<int:chatroom_id>', methods=['POST'])
def send_message(chatroom_id):
    chatroom = Chatroom.query.filter_by(chatroom_id=chatroom_id).first()
    if current_user.user_id not in [chatroom.user_1, chatroom.user_2]:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    user_1 = current_user.user_id
    user_2 = chatroom.user_2
    text = request.form.get('content')
    message = Messages(text=text, chatroom_id=chatroom_id, user_id=user_1)
    db.session.add(message)
    db.session.commit()
    return redirect(url_for('chatroom', chatroom_id=chatroom_id))

@app.route('/chats')
def chats():
    user_id = current_user.user_id
    chatrooms = Chatroom.query.filter(or_(Chatroom.user_1 == user_id, Chatroom.user_2 == user_id)).all()
    chat_details = []
    for chatroom in chatrooms:
        other_user_id = chatroom.user_2 if chatroom.user_1 == user_id else chatroom.user_1
        other_user = User.query.get(other_user_id)
        farm = Farm.query.filter_by(farmer_id=other_user.user_id).first()
        chat_details.append({
            "chatroom_id": chatroom.chatroom_id,
            "other_user_name": other_user.username,
            "farm_name": farm.farm_name if farm else "N/A"
        })
    return render_template('chats.html', chatrooms=chat_details, user_id=user_id)

@app.route('/api/messages/unseen-count', methods=['POST', 'GET'])
def api_messages_unseen_count():
    data = request.get_json()
    user_id = data.get('user_id')
    chatroom_id = data.get('chatroom_id')
    chatroom = Chatroom.query.filter_by(chatroom_id=chatroom_id).first()
    messages = Messages.query.filter_by(chatroom_id=chatroom_id).all()
    unseen_messages = [message for message in messages if message.user_id != user_id and message.status == 'unseen']
    return jsonify({"unseen_count": len(unseen_messages)}), 200

@app.route('/edit_message/<int:message_id>/<string:text>', methods=['POST'])
def edit_message(message_id, text):
    message = Messages.query.get(message_id)
    message.text = text
    message.edited = True
    db.session.commit()
    return redirect(url_for('chatroom', chatroom_id=message.chatroom_id))

@app.route('/delete_message/<int:message_id>', methods=['POST'])
def delete_message(message_id):
    message = Messages.query.get(message_id)
    db.session.delete(message)
    db.session.commit()
    return redirect(url_for('chatroom', chatroom_id=message.chatroom_id))

@app.route('/api/message', methods=['GET'])
def api_message():
    data = request.get_json()
    current_user_id = data.get('user_id')
    farmer_id = data.get('farmer_id')
    farmer = Farmer.query.filter_by(farmer_id=farmer_id).first()
    farmer_user = User.query.filter_by(username=farmer.username).first()
    chatroom = Chatroom.query.filter_by(user_1=current_user_id, user_2=farmer_user.user_id).first()
    if not chatroom:
        chatroom = Chatroom(user_1=current_user.user_id, user_2=user.user_id)
        db.session.add(chatroom)
        db.session.commit()
    chatroom_id = chatroom.chatroom_id
    return jsonify({"chatroom_id": chatroom_id})

@app.route('/api/get-messages', methods=['GET'])
def api_get_messages():
    data = request.get_json()
    chatroom_id = data.get('chatroom_id')
    messages = Messages.query.filter_by(chatroom_id=chatroom_id).order_by(Messages.m_time.asc()).all()
    message_list = []
    for message in messages:
        message_list.append({
            "text": message.text,
            "user_id": message.user_id,
            "m_time": message.m_time,
        })
    return jsonify({"messages": message_list}), 200

@app.route('/api/send-message', methods=['POST'])
def api_send_message():
    data = request.get_json()
    chatroom_id = data.get('chatroom_id')
    text = data.get('text')
    user_id = data.get('user_id')
    message = Messages(text=text, chatroom_id=chatroom_id, user_id=user_id)
    db.session.add(message)
    db.session.commit()
    return jsonify({"success": True}), 200

@app.route('/api/get-chatrooms', methods=['GET'])
def api_get_chatrooms():
    data = request.get_json()
    user_id = data.get('user_id')
    chatrooms = Chatroom.query.filter(or_(Chatroom.user_1 == user_id, Chatroom.user_2 == user_id)).all()
    chatroom_list = []
    for chatroom in chatrooms:
        if chatroom.user_1 == user_id:
            other_user_id = chatroom.user_2
        else:
            other_user_id = chatroom.user_1
        other_user = User.query.filter_by(user_id=other_user_id).first()
        chatroom_list.append({
            "chatroom_id": chatroom.chatroom_id,
            "other_user_name": other_user.username,
        })
    return jsonify({"chatrooms": chatroom_list}), 200

#LOGIN MANAGER
@app.route('/login')
def login():
    logout_user()
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    email_or_username = request.form.get('email_or_username')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email_or_username).first()
    if not user:
        user = User.query.filter_by(username=email_or_username).first()
    
    try:
        if user.status == 'banned':
            flash('Your account has been banned', 'error')
            return redirect(url_for('login'))
    except AttributeError:
        flash('Invalid credentials!', 'error')
        return redirect(url_for('login'))

    if user and check_password_hash(user.password, password):
        if user.role == 'admin' or user.role == 'moderator':
            login_user(user)
            return redirect(url_for('admin'))
        elif user.role == 'farmer':
            login_user(user)
            farmer = Farmer.query.filter_by(email=email_or_username).first()
            if not farmer:
                farmer = Farmer.query.filter_by(username=email_or_username).first()
            farmer_id = farmer.farmer_id
            return redirect(url_for('index'))
        elif user.role == 'buyer':
            login_user(user)
            return redirect(url_for('index'))
    flash('Invalid credentials!', 'error')
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def  logout():
    logout_user()
    return redirect(url_for('index'))

#API FOR REGISTRATION
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    role = data.get("role", "buyer").lower()
    username = data.get("username")

    if role not in ["buyer", "farmer"]:
        return jsonify({"message": "Invalid role"}), 400

    email = data.get("email")
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 400
    elif User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already exists"}), 400
    password = data.get("password")
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
    user = User(email=email, password=hashed_password, role=role, username=username, status='active')
    db.session.add(user)
    db.session.flush()
    
    if user.role == 'buyer':
        buyer = Buyer(first_name=data.get("first_name"), 
                      last_name=data.get("last_name"),
                      address = data.get("address"),
                      username = data.get("username"),
                      email = email,
                      phone_number=data.get("phone_number"))
        db.session.add(buyer)
        db.session.commit()
    elif user.role == 'farmer':
        farmer = Farmer(first_name=data.get("first_name"),
                        last_name = data.get("last_name"),
                        username = data.get("username"),
                        phone_number=data.get("phone_number"),
                        email=email)
        
        db.session.add(farmer)
        db.session.commit()
        
        farm = Farm(crop_type = data.get("crop_type"),
                    farm_name = data.get("farm_name"),
                    location = data.get("location"),
                    farm_size = data.get("farm_size"),
                    farmer_id = farmer.farmer_id)
        db.session.add(farm)
        db.session.commit()
    return jsonify({"message": f"{role.capitalize()} registered successfully"}), 201

#API FOR LOGIN
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email_or_username = data.get("email_or_username")
    password = data.get("password")
    
    user = User.query.filter_by(email=email_or_username).first()
    if not user:
        user = User.query.filter_by(username=email_or_username).first()
    
    if user and check_password_hash(user.password, password):
        login_user(user)
        access_token = os.urandom(16).hex()
        user.auth_token = access_token
        db.session.commit()
        response = {"message": f"{user.role.capitalize()} logged in successfully", "role": user.role, "token": access_token}

        return jsonify(response), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401
    
@app.route('/api/logout', methods=['POST'])
def api_logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200
    
@app.route('/api/products', methods=['GET'])
def api_products():
    products = Product.query.all()
    product_list = []
    for product in products:
        product_list.append({
            "product_id": product.product_id,
            "title": product.title,
            "description": product.description,
            "category": product.category,
            "organic_certification": product.organic_certification,
            "quantity": product.quantity,
            'price': product.price,
            'farm_name': product.farm_name,
        })
    return jsonify(product_list)

#API FOR ADDING PRODUCT. PASS FARMER ID ALONG WITH THE DETAILS
@app.route('/api/add-product', methods=['POST'])
def api_add_product():
    data = request.get_json()
    farmer_id = data.get("farmer_id")
    farm = Farm.query.filter_by(farmer_id=farmer_id).first()
    farm_name = farm.farm_name
    
    title = data.get("title")
    description = data.get("description")
    category = data.get("category")
    organic_certification = data.get("organic_certification")
    quantity = data.get("quantity")
    price = data.get("price")
    farm_name = data.get("farm_name")
    
    product = Product(title=title, description=description, category=category,organic_certification=organic_certification, quantity=quantity, price=price, farm_name = farm_name)
    db.session.add(product)
    db.session.commit()
        
    return jsonify({"message": "Product added successfully"}), 201

#API FOR EDITING PRODUCT. PASS FARMER ID AND PRODUCT ID ALONG WITH THE CHANGES
@app.route('/api/edit-product', methods=['POST'])
def api_edit_product():
    data = request.get_json()
    farmer_id = data.get("farmer_id")
    product_id = data.get("product_id")
    
    product = Product.query.get(product_id)
    
    product.title = request.form.get('title')
    product.category = request.form.get('category')
    product.price = request.form.get('price')
    product.quantity = request.form.get('quantity')
    product.description = request.form.get('description')
    product.organic_certification = request.form.get('organic_certification')
        
    db.session.commit()

    return jsonify({"message": "Product updated successfully"}), 200

@app.route('/api/delete-product', methods=['POST'])
def api_delete_product():
    data = request.get_json()
    product_id = data.get("product_id")
    product = Product.query.get(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"}), 200

@app.route('/api/get-user-id/<role>/<int:role_id>', methods=['GET'])
def get_user_id(role, role_id):
    if role == "farmer":
        farmer = Farmer.query.get(role_id)
        if farmer:
            user = User.query.filter_by(email=farmer.email).first()
            if user:
                return jsonify({"success": True, "user_id": user.user_id})
    elif role == "buyer":
        buyer = Buyer.query.get(role_id)
        if buyer:
            user = User.query.filter_by(email=buyer.email).first()
            if user:
                return jsonify({"success": True, "user_id": user.user_id})
    return jsonify({"success": False, "message": "User not found"}), 404

@app.route('/api/user_info', methods=['GET', 'POST'])
def api_user_info():
    data = request.get_json()
    email = data.get("email")
    user = User.query.filter_by(email=email).first()
    if user:
        if user.role == 'buyer':
            buyer = Buyer.query.filter_by(email=email).first()
            if buyer:
                return jsonify({"role": user.role,
                                "user_id": user.user_id,
                                "auth_token": user.auth_token,
                                "buyer_id": buyer.buyer_id,
                                "username": buyer.username,
                                "first_name": buyer.first_name,
                                "last_name": buyer.last_name,
                                "phone_number": buyer.phone_number,
                                "address": buyer.address}), 200
        if user.role == 'farmer':
            farmer = Farmer.query.filter_by(email=email).first()
            farm = Farm.query.filter_by(farmer_id=farmer.farmer_id).first()
            if farmer and farm:
                return jsonify({"role": user.role,
                                "user_id": user.user_id,
                                "auth_token": user.auth_token,
                                "farmer_id": farmer.farmer_id,
                                "username": farmer.username,
                                "first_name": farmer.first_name,
                                "last_name": farmer.last_name,
                                "phone_number": farmer.phone_number,
                                "farm_name": farm.farm_name,
                                "location": farm.location,
                                "farm_size": farm.farm_size,
                                "crop_type": farm.crop_type}), 200
    return jsonify({"message": "User not found"}), 404
    
#Main
if __name__ == '__main__':
    app.run(debug=True)