#Imports
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

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    two_factor_secret = db.Column(db.String(16))
    status = db.Column(db.String(20), default='active')
    username = db.Column(db.String(20))
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
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary = True)
    query = 'SELECT * FROM product'
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('products.html', table_name = 'Products', rows=rows)

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
    if current_user.email == 'admin@mail.com':
        return render_template('admin.html')
    return render_template('moderator.html')

@app.route('/admin/pending-farmers', methods=['GET'])
@login_required
def pending_farmers():
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

@app.route('/admin/farmers', methods=['GET'])
@login_required
def approved_farmers():
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

@app.route('/admin/banned-users', methods=['GET'])
@login_required
def banned_users():
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

@app.route('/admin/banned-farmers', methods=['GET'])
@login_required
def banned_farmers():
    banned_users = User.query.filter_by(status='banned', role='farmer').all()
    
    banned_users_list = []
    for banned_user in banned_users:
        banned_farmer = Farmer.query.filter_by(email=banned_user.email).first()
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

@app.route('/admin/banned-buyers', methods=['GET'])
@login_required
def banned_buyers():
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

@app.route('/admin/ban-farmer/<int:farmer_id>', methods=['POST'])
@login_required
def ban_farmer(farmer_id):
    if current_user.role != 'admin':
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

@app.route('/admin/ban-buyer/<int:buyer_id>', methods=['POST'])
@login_required
def ban_buyer(buyer_id):
    if current_user.role != 'admin':
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

@app.route('/admin/unban-user/<int:user_id>', methods=['POST'])
@login_required
def unban_user(user_id):

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
    
    return redirect(url_for('farmer_dashboard'))

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

    return render_template('farmer_dashboard.html', farm=farm, products=products)

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
    
    return jsonify({"message": "Buyer registered successfully"})

@app.route('/admin/buyers', methods=['GET'])
@login_required
def buyers():
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
    username = data.get("username")
    
    user = User.query.filter_by(email=email_or_username).first()
    if not user and username:
        user = User.query.filter_by(username=email_or_username).first()
    
    if user and check_password_hash(user.password, password):
        login_user(user)
        response = {"message": f"{user.role.capitalize()} logged in successfully", "role": user.role}

        return jsonify(response), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401
        
#Main
if __name__ in '__main__':
        app.run(debug = True)