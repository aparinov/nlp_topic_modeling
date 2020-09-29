from config import Config
from flask import Flask, request, abort, jsonify, url_for, Blueprint, g
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from views.user import user_bp

import os

from passlib.apps import custom_app_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from celery_tasks import run_stage

from model_testing.database import User

db = SQLAlchemy()
auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username_or_token, password):
    print(username_or_token, password)
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username = username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    auth.init_app(app)

    app.register_blueprint(user_bp, url_prefix='/user')

    return app
