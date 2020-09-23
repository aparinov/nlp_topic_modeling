from config import Config
from flask import Flask, request, abort, jsonify, url_for, Blueprint, g
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from views.user import user_bp

import os

from passlib.apps import custom_app_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from celery_tasks import run_stage

db = SQLAlchemy()
auth = HTTPBasicAuth()

def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    auth.init_app(app)

    app.register_blueprint(user_bp, url_prefix='/user')

    return app
