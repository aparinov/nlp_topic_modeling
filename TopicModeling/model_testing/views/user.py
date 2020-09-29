from flask import Flask, request, abort, jsonify, url_for, Blueprint, g
# from main import User, auth, db
# import testing_framework as tf
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
import os
from model_testing import from_dict
from model_testing import db, auth
# from model_testing.database import User
from model_testing.model.user import User

from passlib.apps import custom_app_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

user_bp = Blueprint("user", __name__)

@user_bp.route('/get_all', methods=["GET"])
def get_all_user():
    users = []
    for u in User.query.all():
        users.append(u.to_dict())

    return {"response":users}


@user_bp.route('/get', methods=["GET"])
def get_user():
    to_get = request.json.get('to_get')
    res = {"response": []}
    incomplete_description = {"error":"Request must provide list 'to_get' of objects with 'id' or 'username'."}
    if to_get:
        for g in to_get:
            username = from_dict(g, 'username')
            id = from_dict(g, 'id')

            if (id is not None) or (username is not None):
                try:
                    us = User.get(id, username)
                    res["response"].append(us.to_dict())
                except Exception as e:
                    err = {"error": str(e)}
                    if id:
                        err['id'] = id
                    if username:
                        err['username'] = username
                    res["response"].append(err)
            else:
                res['response'].append(incomplete_description)
    else:
        res['response'].append(incomplete_description)

    return jsonify(res)


@user_bp.route('/post', methods=["POST"])
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


@user_bp.route('/update', methods=["PATCH"])
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


@user_bp.route('/delete', methods=["DELETE"])
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


@user_bp.route('/get_token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({ 'token': token.decode('ascii') })