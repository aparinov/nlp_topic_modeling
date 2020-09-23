from flask import Flask, request, abort, jsonify, url_for, Blueprint, g
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
import os

from passlib.apps import custom_app_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from celery_tasks import run_stage

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1@localhost:5432/topicmodeling'

db = SQLAlchemy(app)
auth = HTTPBasicAuth()

# USER
#-------------------------------------------------#
USER = Blueprint("user", __name__)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    username = db.Column(db.String(32), index = True)
    password_hash = db.Column(db.String(128))
    admin_rights = db.Column(db.Boolean, default=False)
    exp_admin_rights = db.Column(db.Boolean, default=False)

    def generate_auth_token(self, expiration = 600):
        s = Serializer(app.config['SECRET_KEY'], expires_in = expiration)
        return s.dumps({ 'id': self.id })

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        user = User.query.get(data['id'])
        return user

    def hash_password(self, password):
        self.password_hash = custom_app_context.encrypt(password)

    def verify_password(self, password):
        return custom_app_context.verify(password, self.password_hash)

# serialization template for PersonModel in @marshal_with
# person_fields = {
#     'id' : fields.Integer,
#     'name' : fields.String,
#     'age' : fields.Integer,
#     'gender' : fields.String
# }

# parsing params
# person_args = reqparse.RequestParser()
# person_args.add_argument("age", type=int, help="Person's age", required=True)
# person_args.add_argument("name", type=str, help="Person's name", required=True)
# person_args.add_argument("gender", type=str, help="Person's gender", required=True)

@USER.route('/read', methods=["GET"])
def read_user():
    users = []
    for u in User.query.all():
       users.append({
           "username": u.username,
           "admin_rights": u.admin_rights,
           "exp_admin_rights": u.exp_admin_rights
       })
    return {"users":users}

@USER.route('/create', methods=["POST"])
@auth.login_required
def create_user():
    if not g.user.admin_rights:
        abort(101, "Permission required! Only administrator can create users.")

    username = request.json.get('username')
    password = request.json.get('password')
    admin_rights = request.json.get('admin_rights')
    exp_admin_rights = request.json.get('exp_admin_rights')

    if username is None or password is None:
        abort(400, 'Missing arguments!')
    if User.query.filter_by(username = username).first() is not None:
        abort(400, "User existing!")

    user = User(username = username, admin_rights=admin_rights, exp_admin_rights=exp_admin_rights)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({ 'username': user.username }), 201


@USER.route('/update', methods=["PATCH"])
@auth.login_required
def update_user():
    if not g.user.admin_rights:
        abort(101, "Permission required! Only administrator can update users.")

    username = request.json.get('username')
    password = request.json.get('password')
    admin_rights = request.json.get('admin_rights')
    exp_admin_rights = request.json.get('exp_admin_rights')

    user = User.query.filter_by(username = username).first()
    response = {}

    if not user:
        abort(404, "User does not exist")

    if password is not None:
        user.hash_password(password)
        response['password'] = "changed"

    if admin_rights is not None:
        user.admin_rights = admin_rights
        response['admin_rights'] = "changed"

    if exp_admin_rights is not None:
        user.exp_admin_rights = exp_admin_rights
        response['exp_admin_rights'] = "changed"
    db.session.commit()

    return response


@USER.route('/delete', methods=["DELETE"])
@auth.login_required
def delete_user():
    if not g.user.admin_rights:
        abort(101, "Permission required! Only administrator can delete users.")

    username = request.json.get('username')
    user = User.query.filter_by(username = username).first()

    if not user:
        abort(404, "User does not exist")
    db.session.delete(user)
    db.session.commit()
    return {'result': username + " deleted"}


@USER.route('/get_token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({ 'token': token.decode('ascii') })


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username = username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True

#-------------------------------------------------#

# PROGRAM = Blueprint("program", __name__)
#
# # TODO: класс Program
# # TODO: класс Stage
#
# # TODO: пример
# stage = {
#   "input":"data:int[]",
#   "output":"int",
#   "description":"Sum",
#   "dependencies": [{
#       "lib":"tensorflow",
#       "version":"2.0.1"
#   }],
#   "author":1,
#   "time_created":12345,
#   "id":1
#  }
#
# # TODO: Рабочий пример с RoBERTa
#
# @PROGRAM.route('/get', methods=["GET"])
# @auth.login_required()
# def get_program():
#     # TODO: implement
#     return {}
#
#
# @PROGRAM.route('/update', methods=["PATCH"])
# @auth.login_required()
# def upd_program():
#     # TODO: implement
#     return {}
#
#
# @PROGRAM.route('/post', methods=["POST"])
# @auth.login_required()
# def post_program():
#     # TODO: implement
#     return {}
#
#
# @PROGRAM.route('/delete', methods=["DELETE"])
# @auth.login_required()
# def del_program():
#     # TODO: implement
#     return {}

#-------------------------------------------------#

SCHEMA = Blueprint("schema" , __name__)
from database import session as s
from database import create_dataformat, DataFormat

@SCHEMA.route('/get', methods=["GET"])
@auth.login_required()
def get_schema():
    # TODO: implement
    return {}


@SCHEMA.route('/update', methods=["PATCH"])
@auth.login_required()
def upd_schema():
    # TODO: implement
    return {}


@SCHEMA.route('/post', methods=["POST"])
# @auth.login_required()
def post_schema():
    name = request.json.get('name')
    format = request.json.get('file_format')
    schema = request.json.get('schema')

    try:
        create_dataformat(name, format, schema,s)
    except Exception as e:
        abort(400, e.args[0])

    id = s.query(DataFormat).filter(DataFormat.name == name).first().Id
    return jsonify({ 'id': id,
                     "name" : name,
                     "format" : format,
                     "schema" : schema
                     })


@SCHEMA.route('/delete', methods=["DELETE"])
@auth.login_required()
def del_schema():
    # TODO: implement
    return {}

#-------------------------------------------------#

# EXPERIMENT = Blueprint("experiment", __name__)
#
# # TODO: класс Experiment
#
# @app.route("/run_stage")
# def stage_running():
#
#     data = {
#     "lang" : "py",
#     "code" : """import numpy as np
# # print(type(np.array([1,2,3])))
# # print('works!')
# # print(val)
# val = 0
# """,
#     "dependencies" : ["numpy"],
#     "input" : {"val":int},
#     "output" : {"val":int}
# }
#
#     local = {"val" : 123}
#
#     res = run_stage.delay(local=local, data=data).get()
#
#     # res = run_stage.delay(data, local)
#     # print()
#     # print(res.status)
#     # res = res.get()
#     # print(res)
#     # print(type(res))
#     return res
#
# # TODO: Рабочий пример с 20 news groups
#
#
# @EXPERIMENT.route('/get', methods=["GET"])
# @auth.login_required()
# def get_experiment():
#     # TODO: implement
#     return {}
#
#
# @EXPERIMENT.route('/update', methods=["PATCH"])
# @auth.login_required()
# def upd_experiment():
#     # TODO: implement
#     return {}
#
#
# @EXPERIMENT.route('/post', methods=["POST"])
# @auth.login_required()
# def post_experiment():
#     # TODO: implement
#     return {}
#
#
# @EXPERIMENT.route('/delete', methods=["DELETE"])
# @auth.login_required()
# def del_experiment():
#     # TODO: implement
#     return {}
#
#
# @EXPERIMENT.route('/conduct', methods=["POST"])
# @auth.login_required()
# def conduct_experiment():
#     # TODO: implement
#     return {}
#
#
# @EXPERIMENT.route('/pause', methods=["POST"])
# @auth.login_required()
# def pause_experiment():
#     # TODO: implement
#     return {}
#
#
# @EXPERIMENT.route('/continue', methods=["POST"])
# @auth.login_required()
# def continue_experiment():
#     # TODO: implement
#     return {}
#
#
# @EXPERIMENT.route('/cancel', methods=["POST"])
# @auth.login_required()
# def cancel_experiment():
#     # TODO: implement
#     return {}
#
#
# @EXPERIMENT.route("/status")
# def status():
#     # TODO: implement
#     return {"status": "TODO"}


#-------------------------------------------------#

# app.register_blueprint(EXPERIMENT, url_prefix='/experiment')
# app.register_blueprint(PROGRAM, url_prefix='/program')

from views.user import user_bp
# app.register_blueprint(USER, url_prefix='/user')
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(SCHEMA, url_prefix='/schema')

# db.drop_all()
# db.create_all()

if User.query.filter_by(username = "admin").first() is None:
    print("admin" * 100)
    user = User(username = "admin", admin_rights=True, exp_admin_rights=True)
    user.hash_password("password")
    db.session.add(user)
    db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)