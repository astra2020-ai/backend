from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from functools import wraps
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:cyberfox@localhost/casino'
app.config['SECRET_KEY'] = '0c06f185e52811ab2c087a05391131b3'
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

games = ['BAR', 'APPLE', 'ORANGE', 'MALON', 'BELL', 'STAR', '777', 'MANGO', 'BONUS']
values = [100, 50, 20, 10, 5, 3]
bonus = [10, 5, 3]
bonus_weight = [5, 20, 75]
single_bonus = [20, 10]
sigle_weight = [5, 95]
decide = ['2', '3']
decide_weight = [70, 30]
account = 0
Bonus = False

@app.route('/add_money', methods=['POST'])
def add_money():
    global account
    data = request.json
    added = data.get('amount', 0)
    account += int(added)

    return jsonify({'message': 'Transaction successful', 'balance': account})

@app.route('/balance', methods=['GET'])
def get_balance():
    return jsonify({'balance': account})

@app.route('/spin', methods=['POST'])
def spin():
    global account
    data = request.json
    bet = data.get('bet', [])

    results = []

    def spin_logic():
        global account
        gam = random.choices(games, weights=[1, 13, 13, 13, 13, 13, 13, 13, 8], k=1)
        wins = set(gam) & set(bet)

        if len(list(wins)) >= 1 or 'BONUS' in gam:
            if 'BONUS' in gam:
                bonus_results = []
                one_or_two = random.choices(decide, weights=decide_weight, k=1)
                if '2' in one_or_two:
                    gas = random.choices(games, weights=[0, 15, 15, 14, 14, 14, 14, 14, 0], k=3)
                    vas = random.choices(bonus, weights=bonus_weight, k=3)
                    bonus_results = [(x, int(num) * 500) for x, num in zip(gas, vas)]
                else:
                    gas = random.choices(games, weights=[0, 15, 15, 14, 14, 14, 14, 14, 0], k=2)
                    vas = random.choices(single_bonus, weights=sigle_weight, k=2)
                    bonus_results = [(x, int(num) * 500) for x, num in zip(gas, vas)]

                # Check if the bonus bets are correct before adding to results
                bonus_wins = set([bonus_bet for bonus_bet in bonus_results if bonus_bet[0] in bet])
                if bonus_wins:
                    earned_amount = sum([int(num) for _, num in bonus_wins])
                    account += earned_amount
                    # Include detailed information in results
                    results.extend([('bonus', {'objects': list(bonus_wins), 'earned_amount': earned_amount, 'total_balance': account})])
                else:
                    results.extend([('regular', {'objects': list(wins), 'earned_amount': 0, 'total_balance': account})])
            else:
                if "BAR" in gam:
                    bon = [100, 50]
                    val = random.choices(bon, weights=[5, 95], k=1)
                    res = int(val) * 500
                    account += int(res)
                    results.append(('regular', {'objects': list(wins), 'earned_amount': res, 'total_balance': account}))
                else:
                    val = random.choices(values, weights=[0, 0.5, 5, 10.5, 25, 60])[0]
                    res = int(val) * 500
                    account += int(res)
                    # Include detailed information in results
                    results.append(('regular', {'objects': list(wins), 'earned_amount': res, 'total_balance': account}))
        else:
            results.append(('regular', {'objects': gam, 'earned_amount': 0, 'total_balance': account}))

    if account >= 500:
        stake = len(bet) * 500
        if account >= stake:
            account -= stake

            # Regular spin
            spin_logic()

            # Bonus spin (if applicable)
            if results and results[-1][0] == 'bonus':
                spin_logic()

        else:
            return jsonify({'message': 'Bet is more than stake', 'results': results}), 400
    else:
        return jsonify({'message': 'Deposit money to your account', 'results': results}), 400

    return jsonify({'results': results})


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

if __name__ == '__main__':
    app.run(debug=True)
