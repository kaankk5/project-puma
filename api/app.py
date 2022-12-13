import datetime
import json
from functools import wraps
from pathlib import Path

import requests
from flask import Flask, request, jsonify, make_response, redirect, url_for, render_template
from flask_jwt_extended import JWTManager, get_jwt_identity
from flask_restful import Api
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from models.user_model import UserModel
from flask_jwt_extended import jwt_required
from db import db

env_path = Path("..") / ".pumavenv"


#
def token_required(function):
    @wraps(function)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing !!'}), 401
        data = jwt.decode(token, puma.config['SECRET_KEY'], algorithms=['HS256'])
        current_user = UserModel.objects.filter(id=data['id']).first()
        return function(current_user, *args, **kwargs)

    return decorated


from resources.user_resource import User, UserRegister, DeleteUser
from resources.homepage import Home
from config import API_SECRET, API_KEY

puma = Flask(__name__, static_folder="static", template_folder="templates", instance_relative_config=True)

api = Api(puma)
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

api.add_resource(UserRegister, "/register")
api.add_resource(User, "/login")
api.add_resource(Home, "/homepage")
api.add_resource(DeleteUser, "/delete")

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

puma.config["MONGODB_SETTINGS"] = [
    {
        "db": "test",
        "host": "localhost",
        "port": 27017,
        "alias": "default",
    }
]

puma.config['WTF_CSRF_ENABLED'] = False
puma.config["SECRET_KEY"] = "secretsecret"
puma.config["JWT_SECRET_KEY"] = "Dese.Decent.Pups.BOOYO0OST"

csrf = CSRFProtect()
csrf.init_app(puma)
db.init_app(puma)
jwt = JWTManager(puma)

# jwt = JWT(app, authenticate, identity)  # Auto Creates /auth endpoint


#
# from binance import ThreadedWebsocketManager
#
# twm = ThreadedWebsocketManager(api_key=API_KEY, api_secret=API_SECRET)
# # start is required to initialise its internal loop
# twm.start()
#

# def handle_socket_message(msg):
#     print(f"message type: {msg['e']}")
#     print(msg)
#


# @user.route('/<user_id>', defaults={'username': None})
# @user.route('/<user_id>/<username>')
# def show(user_id, username):
#     pass
#
from get_data import get_historical_kline


@puma.route("/chart", defaults={'symbol': 'BTCUSDT', 'interval': '4h'}, methods=['POST', 'GET'])
@puma.route("/chart/<symbol>/<interval>")
def default_chart(symbol, interval):
    return get_historical_kline(symbol, interval)
    # list of dictionries
    # [{'time': 1661702400.0, 'open': '20007.60', 'high': '20140.00', 'low': '19942.00', 'close': '19962.50'},
    #  {'time': 1661716800.0, 'open': '19962.60', 'high': '20035.00', 'low': '19508.00', 'close': '19547.50'}


main_page_currencies = ['BTCUSDT', 'AVAXUSDT', 'ETHUSDT', 'DOGEUSDT', 'MATICUSDT']


@puma.route("/currencies", methods=['GET'])
def live_currencies_main(symbol):
    return main_page_currencies


@puma.route("/dashboard/currencies", defaults={'symbol': 'BTCUSDT', 'interval': '4h'}, methods=['POST', 'GET'])
def live_currencies_dashboard(symbol):
    currencies = ['BTCUSDT', 'AVAXUSDT', 'ETHUSDT']
    currencies.insert(0, symbol)
    currencies.pop()

    # return redirect(url_for('display_charts',symbol=symbol,interval=interval))


from utils import *


@puma.route('/dashboard/portfolio', methods=['POST', 'GET'])
@jwt_required()
def portfolio():
    user_id = get_id(str_to_dict(get_jwt_identity()))
    user = UserModel.getquery_id(user_id)

    for script in user.scripts:
        user.add_portfolio(script.symbol)

    return jsonify(user.portfolio)


from furl import furl


@puma.route('/dashboard', methods=['POST', 'GET', 'PUT', 'DELETE'])
@jwt_required()
def dash():
    data = request.json
    user_id = get_id(str_to_dict(get_jwt_identity()))
    user = UserModel.getquery_id(user_id)
    if user.scripts:
        response = [{'symbol': i.symbol, 'interval': i.interval} for i in user.scripts]
        if request.method == 'DELETE':
            symbol = data['symbol']
            user.delete_script(symbol)
            return jsonify(response)

        return jsonify(response)

    else:
        return jsonify('No scripts yet')


# @puma.route('/dashboard', methods=['POST', 'GET', 'PUT'])
# @jwt_required()
# def dash():
#     data = request.json
#     user_id = get_id(str_to_dict(get_jwt_identity()))
#     user = UserModel.getquery_id(user_id)
#
#     if request.method == 'GET':
#         if user.scripts:
#             response = [{'symbol': i.symbol, 'interval': i.interval} for i in user.scripts]
#             json_string = json.dumps(response)
#             return json_string
#         else:
#             return jsonify('No scripts yet')
#
# if request.method == 'DELETE':
#     f = furl("/abc?def='ghi'")
#     print(f.args[symbol])


import json
import asyncio


@puma.route('/scripts', methods=['POST', 'GET', 'PUT'])
@jwt_required()
def scripts():
    # users get queue data
    data = request.json
    symbol = data['symbol']
    script = data['script']
    interval = data['interval']
    user_id = get_id(str_to_dict(get_jwt_identity()))
    user = UserModel.getquery_id(user_id)
    data = {'userName': user.username,
            'symbol': symbol,
            }

    if request.method == 'POST':
        # if request.method == 'POST' and user.check_symbol(user_id, symbol):
        user.add_script(symbol, script, interval)
        user.save()
        json_object = json.dumps(data)
        loaded_r = json.loads(json_object)
        print(loaded_r)
        requests.post("http://127.0.0.1:8000/queues/create_queue", json=loaded_r, verify=False)

        #################################################################################
        return {'symbol': symbol, 'interval': interval, 'script': script}

    # return {'name': 'user.username'}


@puma.route('/scripts/<symbol>', methods=['POST', 'GET', 'PUT'])
@jwt_required()
def execute_script(symbol):
    user_id = get_id(str_to_dict(get_jwt_identity()))
    user = UserModel.getquery_id(user_id)
    data = request.json
    new_script = data['script']
    if request.method == 'GET':
        for i in user.scripts:
            if str(i.symbol) == str(symbol):
                return str(i.pyscript)

    if request.method == 'POST':
        user_script = user.find_pyscript_by_symbol(symbol)
        user.edit_script(symbol, new_script)
        user.save()
        if user.edit_script:
            json_object = json.dumps({
                'userName': user.username,
                'symbol': symbol

            })
            loaded_r = json.loads(json_object)
            requests.post("http://127.0.0.1:8000/queues/create_queue", json=loaded_r)
            return {'symbol': symbol, 'script': new_script}


# @puma.route('/dashboard/scripts/<scripts_id>')
# def scripts():
#     pass
# @puma.route('/dashboard/scripts')
# def scripts():
#     pass


#
#
# @puma.route("/dashboard/currencies", methods=['POST', 'GET'])
# @jwt_required()
# def index():
#     return '<h1>Welcome homepage</h1>'
#
#
# @puma.route("/dashboard/script", methods=['POST', 'GET'])
# @jwt_required()
# def index():
#     return '<h1>Welcome homepage</h1>'
#
#
# @puma.route("/dashboard/script/<script_id>", methods=['POST', 'GET'])
# @jwt_required()
# def index():
#     return '<h1>Welcome homepage</h1>'


puma.run(host="127.0.0.1", port=5000, debug=True)


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

#
#


@puma.route('/register', methods=['GET', 'POST'])
def register():
    data = request.json
    if UserModel.objects.filter(name=data['name']):
        return make_response('User already exists')
    else:
        hashed_password = generate_password_hash(data['password'], method='sha256')
        new_user = UserModel(name=data['name'],password=hashed_password)
        new_user.save()
        return jsonify({'message' : 'New user created'})


#
@puma.route('/login')
def login():
    data = request.json
    user = UserModel.objects.filter(name=data['name']).first()
    if check_password_hash(user.password, data['password']):
         token = jwt.encode(
             {'id':  json.dumps(str(user.id), default=str)[1:-1], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=45)},
             puma.config['SECRET_KEY'], "HS256")
         return jsonify({'token': token})
