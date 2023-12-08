from functions import send_notification
import firebase_admin
from firebase_admin import  credentials
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime


cred = credentials.Certificate("./credentials.json")
firebase_admin.initialize_app(cred)

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
    original_amount = db.Column(db.Float, nullable=False)  # Nouvelle colonne pour stocker le montant original
    amount = db.Column(db.Float, nullable=False)  # Montant après déduction des frais
    source_account = db.Column(db.String(20), nullable=False)
    destination_account = db.Column(db.String(20), nullable=True)
    date = db.Column(db.String(20), nullable=False)  #  # Stocke la date comme un objet date
    hour = db.Column(db.String(8), nullable=False) 
    status = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    fee = db.Column(db.Float, nullable=True)
    transaction_token = db.Column(db.String(255), nullable=True)
    
    
@app.route('/status-transaction', methods=['POST'])
def updateTransaction():
    
    data = request.get_json()

    # Extraire les informations du JSON
    reference = data['reference']
    new_status = data['status']


    try:
        # Récupérer la transaction à partir de la base de données
        transaction = Transactions.query.filter_by(reference=reference).first()

        if transaction:
            # Mettre à jour le statut de la transaction
            transaction.status = new_status
            db.session.commit()

            # Envoi de la notification avec Firebase Admin
            send_notification(transaction)

            return make_response(jsonify({'message': 'Transaction status updated successfully'}), 200)
        else:
            return make_response(jsonify({'message': 'Transaction not found'}), 404)
    except Exception as e:
        return make_response(jsonify({'message': str(e)}), 500)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    print(data['pinCode'])
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
    user_pin = data['pinCode'] # Pin code provided by the user during login

    user = User.query.filter_by(phone_number=phone_number).first()

    if user and user_pin is not None:
    # Obtenez le code PIN haché de l'utilisateur
        user_pin_hash = user.pin_code

    # Vérifiez si le code PIN fourni correspond au code PIN haché de l'utilisateur
        is_pin_code_correct = bcrypt.check_password_hash(user_pin_hash, user_pin)

        if is_pin_code_correct:
    # Si l'utilisateur existe et que le code PIN correspond, retournez les détails
            return make_response(jsonify({
            'firstName': user.first_name,
            'lastName': user.last_name,
            'phoneNumber': user.phone_number,
        # Vous ne devez pas renvoyer le code PIN haché, mais si nécessaire, vous pouvez le faire
            'pinCode': user.pin_code,
            }),200) 
        else:
            make_response(jsonify({'message': 'Login failed'}),404)
            return make_response(jsonify({'message': 'Login failed'}),404)
    else:
        return make_response(jsonify({'message': 'Login failed'}),404)


@app.route('/verify-number', methods=['POST'])
def verify_phone_number():
    data = request.get_json()
    phone_number_to_verify = data.get('phoneNumber')
    print(phone_number_to_verify)

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

    current_datetime = datetime.now()
    current_date = current_datetime.date()  # Utilise la date actuelle comme un objet date

    # Génération automatique de la référence pour le dépôt
    reference = f'MADIS00XX{data["sourceAccount"][-2:]}{current_date.strftime("%Y%m%d")}'

    # Calcul des frais pour le dépôt (1%)
    fee_percentage = 0.01
    original_amount = data['amount']
    fee = original_amount * fee_percentage
    final_amount = original_amount - fee

    new_transaction = Transactions(
        transaction_type='deposit',
        reference=reference,
        original_amount=original_amount,
        amount=final_amount,
        source_account=data['sourceAccount'],
        date=current_datetime.strftime('%d-%m-%Y'),
        hour=current_datetime.strftime('%H:%M:%S'),
        status='en cours',
        description=data.get('description'),
        payment_method=data.get('paymentMethod'),
        fee=fee,
        transaction_token=data.get('transactionToken')
    )

    db.session.add(new_transaction)
    db.session.commit()

    return make_response(jsonify({'message': 'Deposit successful'}), 201)

@app.route('/make-transfer', methods=['POST'])
def make_transfer():
    data = request.get_json()

    current_datetime = datetime.now()
    current_date = current_datetime.date()  # Utilise la date actuelle comme un objet date

    # Génération automatique de la référence pour le transfert
    reference = f'MADIS01XX{data["sourceAccount"][-2:]}{data["destinationAccount"][-2:]}{current_date.strftime("%Y%m%d")}'

    # Calcul des frais pour le transfert (1.5%)
    fee_percentage = 0.015
    original_amount = data['amount']
    fee = original_amount * fee_percentage
    final_amount = original_amount - fee

    new_transaction = Transactions(
        transaction_type='transfer',
        reference=reference,
        original_amount=original_amount,
        amount=final_amount,
        source_account=data['sourceAccount'],
        destination_account=data['destinationAccount'],
        hour=current_datetime.strftime('%H:%M:%S'),
        date=current_datetime.strftime('%d-%m-%Y'),
        status='en cours',
        description=data.get('description'),
        payment_method=data.get('paymentMethod'),
        fee=fee,
        transaction_token=data.get('transactionToken')
    )

    db.session.add(new_transaction)
    db.session.commit()

    return make_response(jsonify({'message': 'Transfer successful'}), 201)


@app.route('/get-transactions', methods=['GET'])
def get_all_transactions():
    try:
        transactions = Transactions.query.all()
        # Convertir les objets Transactions en un format JSON
        transactions_json = [{
            'id': transaction.id,
            'transactionType': transaction.transaction_type,
            'reference': transaction.reference,
            'originalAmount': transaction.original_amount,
            'amount': transaction.amount,
            'sourceAccount': transaction.source_account,
            'destinationAccount': transaction.destination_account,
            'date': transaction.date,
            'hours': transaction.hour,
            'status': transaction.status,
            'description': transaction.description,
            'paymentMethod': transaction.payment_method,
            'fee': transaction.fee
        } for transaction in transactions]

        return jsonify(transactions_json)
    except Exception as e:
        return make_response(jsonify({'message': str(e)}), 500)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='192.168.4.33', port=5000, debug=True)
