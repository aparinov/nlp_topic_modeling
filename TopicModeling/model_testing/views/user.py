from flask import Flask, request, abort, jsonify, url_for, Blueprint, g
# from main import User, auth, db
# import testing_framework as tf
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
import os

from passlib.apps import custom_app_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

user_bp = Blueprint("user", __name__)

@user_bp.route('/read', methods=["GET"])
def read_user():
    users = []
    for u in User.query.all():
       users.append({
           "username": u.username,
           "admin_rights": u.admin_rights,
           "exp_admin_rights": u.exp_admin_rights
       })
    return {"users":users}

@user_bp.route('/create', methods=["POST"])
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