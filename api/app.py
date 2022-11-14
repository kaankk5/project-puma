import os
import datetime
import json
from functools import wraps
from pathlib import Path
import jwt
from flask import Flask, request, jsonify, make_response
from flask_mongoengine import MongoEngine
from flask_restful import Api
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from models import User


env_path = Path("..") / ".pumavenv"


def token_required(function):
    @wraps(function)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing !!'}), 401
        data = jwt.decode(token, puma.config['SECRET_KEY'], algorithms=['HS256'])
        current_user = User.objects.filter(id=data['id']).first()
        return function(current_user, *args, **kwargs)

    return decorated




puma = Flask(__name__, static_folder="static", template_folder="templates", instance_relative_config=True)

api = Api(puma)

puma.config["MONGODB_SETTINGS"] = [
    {
        "db": "test",
        "host": "localhost",
        "port": 27017,
        "alias": "default",
    }
]
puma.config["SECRET_KEY"] = "secretsecret"

csrf = CSRFProtect()
csrf.init_app(puma)

db = MongoEngine()
db.init_app(puma)



@puma.route("/")
@puma.route("/index")
def index():
    return '<h1>Welcome homepage</h1>'

@puma.route('/settings')
@token_required
def change_username(user):
    data = request.json
    if user.check_name(data['name']):
        user.update(name=data['name'])
        return jsonify('username changed')
    return jsonify('username already exists')

@puma.route('/register', methods=['GET', 'POST'])
def register():
    data = request.json
    if User.objects.filter(name=data['name']):
        return make_response('User already exists')
    else:
        hashed_password = generate_password_hash(data['password'], method='sha256')
        new_user = User(name=data['name'],password=hashed_password)
        new_user.save()
        return jsonify({'message' : 'New user created'})



@puma.route('/login')
def login():
    data = request.json
    user = User.objects.filter(name=data['name']).first()
    if check_password_hash(user.password, data['password']):
         token = jwt.encode(
             {'id':  json.dumps(str(user.id), default=str)[1:-1], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=45)},
             puma.config['SECRET_KEY'], "HS256")
         return jsonify({'token': token})

@puma.route('/settings/delete')
@token_required
def delete_user(user):
    User.objects(id=user.id).delete()
    return jsonify('User deleted')



@puma.route('/settings/password')
@token_required
def change_password(user):
    data = request.json
    pswrd = data['password']
    if user:
        user.update(password=generate_password_hash(pswrd, method='sha256'))
        return jsonify('Password change in silly level')
    else:
        return jsonify('Not success')


puma.run(host="127.0.0.1", port=5000, debug=True)



