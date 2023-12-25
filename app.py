from datetime import datetime, timezone, timedelta
from flask import render_template
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from functools import wraps

app = Flask(__name__)

# Update the MySQL database URI with your PythonAnywhere MySQL credentials
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://Astra2020:cyberfox@Astra2020.mysql.pythonanywhere-services.com/Astra2020$casino'
app.config['SECRET_KEY'] = '0c06f185e52811ab2c087a05391131b3'

# Update the SQLALCHEMY_TRACK_MODIFICATIONS setting to suppress a warning
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    city_district = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))

    def __repr__(self):
        return f"User: {self.id, self.firstname, self.lastname, self.gender, self.date_of_birth, self.phone_number, self.country, self.city_district}"

    def __init__(self, firstname, lastname, gender, date_of_birth, phone_number, country, city_district, password):
        self.firstname = firstname
        self.lastname = lastname
        self.gender = gender
        self.date_of_birth = date_of_birth
        self.phone_number = phone_number
        self.country = country
        self.city_district = city_district
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

def format_user(user):
    local_created_at = user.created_at.astimezone(timezone(timedelta(hours=3)))
    return {
        "id": user.id,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "gender": user.gender,
        "date_of_birth": user.date_of_birth,
        "phone_number": user.phone_number,
        "country": user.country,
        "city_district": user.city_district,
        "created_at": local_created_at.strftime("%Y-%M-%D %H:%M:%S")
    }

with app.app_context():
    db.create_all()

# Add a route for the homepage
@app.route('/')
def homepage():
    return render_template('index.html')

# Registration endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    existing_user = Users.query.filter_by(phone_number=data['phone_number']).first()

    if existing_user:
        return jsonify({'message': 'Phone number already exists'}), 400

    new_user = Users(
        firstname=data['firstname'],
        lastname=data['lastname'],
        gender=data['gender'],
        date_of_birth=data['date_of_birth'],
        phone_number=data['phone_number'],
        country=data['country'],
        city_district=data['city_district'],
        password=data['password']
    )
    db.session.add(new_user)

    try:
        db.session.commit()
        return jsonify({'message': 'User created successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error creating user'}), 500

# Login endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = Users.query.filter_by(phone_number=data['phone_number']).first()

    if user and check_password_hash(user.password_hash, data['password']):
        # Adjust the expiration
        exp_time = datetime.now(timezone(timedelta(hours=3))) + timedelta(days=1)

        token = jwt.encode({
            'user_id': user.id,
            'exp': exp_time
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token})
    return jsonify({'message': 'Invalid credentials'}), 401

# Protect routes with authentication
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = Users.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

@app.route('/protected', methods=['GET'])
@token_required
def protected(current_user):
    return jsonify({'message': f'Hello, {current_user.firstname}!'})
