from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)
db=app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(15), unique=True, nullable=False)
    #email = db.Column(db.String(120), unique=True, nullable=False)
    pin_code = db.Column(db.String(8), nullable=False)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    hashed_pin = bcrypt.generate_password_hash(data['pinCode']).decode('utf-8')

    new_user = User(
        first_name=data['firstName'],
        last_name=data['lastName'],
        phone_number=data['phoneNumber'],
        #email=data['email'],
        pin_code=hashed_pin
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Registration successful'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    phone_number = data['phoneNumber']
    # pin_code = data['pinCode']  # Commenté car nous n'utilisons que le numéro de téléphone

    user = User.query.filter_by(phone_number=phone_number).first()

    if user:
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Login failed'})

# @app.before_first_request
# def create_database():
#     db.create_all()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
app.run(host='192.168.4.116', port=5000, debug=True)
