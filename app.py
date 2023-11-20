from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    pin_code = db.Column(db.String(8), nullable=False)

class Transactions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(50), nullable=False)
    reference = db.Column(db.String(50), nullable=False)
    method = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.String(20), nullable=False)
    source_account = db.Column(db.String(20), nullable=False)
    destination_account = db.Column(db.String(20), nullable=True)
    date = db.Column(db.String(20), nullable=False)
    hours = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    fee = db.Column(db.String(20), nullable=True)


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
   
    # Si le numéro de téléphone n'existe pas, procéder à l'enregistrement
    hashed_pin = bcrypt.generate_password_hash(data['pinCode']).decode('utf-8')

    new_user = User(
        first_name=data['firstName'],
        last_name=data['lastName'],
        phone_number=data['phoneNumber'],
        pin_code=hashed_pin
    )

    db.session.add(new_user)
    db.session.commit()

    # Retourner un code d'état 201 (Created) pour indiquer que l'enregistrement a réussi
    return make_response(jsonify({'message': 'Registration successful'}), 201)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    phone_number = data['phoneNumber']
    user_pin = data['pinCode']  # Pin code provided by the user during login

    user = User.query.filter_by(phone_number=phone_number).first()

    if user and bcrypt.check_password_hash(user.pin_code, user_pin):
        # Si l'utilisateur existe et que le code PIN correspond, retournez les détails
        return jsonify({
            'firstName': user.first_name,
            'lastName': user.last_name,
            'phoneNumber': user.phone_number,
            # Vous ne devez pas renvoyer le code PIN haché, mais si nécessaire, vous pouvez le faire
            'pinCode': user.pin_code,
        })
    else:
        return jsonify({'message': 'Login failed'})

@app.route('/verify-number', methods=['POST'])
def verify_phone_number():
    data = request.get_json()
    phone_number_to_verify = data.get('phoneNumber')

    # Vérifier si le numéro de téléphone existe déjà
    existing_user = User.query.filter_by(phone_number=phone_number_to_verify).first()
    if existing_user:
        return make_response(jsonify({'message': 'Phone number already registered'}), 409)
    else:
        return make_response(jsonify({'message': 'Phone number is available'}), 200)

#TRANSACTIONS


@app.route('/make-deposit', methods=['POST'])
def make_deposit():
    data = request.get_json()

    # Obtenir automatiquement la date et l'heure actuelles
    current_datetime = datetime.now()
    current_date = current_datetime.strftime('%Y-%m-%d')
    current_hours = current_datetime.strftime('%H:%M:%S')

    new_transaction = Transactions(
        transaction_type='deposit',
        reference=data['reference'],
        method=data['method'],
        amount=data['amount'],
        source_account=data['sourceAccount'],
        date=current_date,
        hours=current_hours,
        status='en cours',  # Définir le statut par défaut
        description=data.get('description'),
        payment_method=data.get('paymentMethod'),
        fee=data.get('fee')
    )

    db.session.add(new_transaction)
    db.session.commit()

    return make_response(jsonify({'message': 'Deposit successful'}), 201)

@app.route('/make-transfer', methods=['POST'])
def make_transfer():
    data = request.get_json()

    # Obtenir automatiquement la date et l'heure actuelles
    current_datetime = datetime.now()
    current_date = current_datetime.strftime('%Y-%m-%d')
    current_hours = current_datetime.strftime('%H:%M:%S')

    new_transaction = Transactions(
        transaction_type='transfer',
        reference=data['reference'],
        method=data['method'],
        amount=data['amount'],
        source_account=data['sourceAccount'],
        destination_account=data['destinationAccount'],
        date=current_date,
        hours=current_hours,
        status='en cours',  # Définir le statut par défaut
        description=data.get('description'),
        payment_method=data.get('paymentMethod'),
        fee=data.get('fee')
    )

    db.session.add(new_transaction)
    db.session.commit()

    return make_response(jsonify({'message': 'Transfer successful'}), 201)




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='192.168.4.116', port=5000, debug=True)
