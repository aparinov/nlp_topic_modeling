from config import Config
from flask import Flask, request, abort, jsonify, url_for, Blueprint, g, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
import logging
import os

# from passlib.apps import custom_app_context
# from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
# from celery_tasks import run_stage

from celery import Celery

db = SQLAlchemy()
auth = HTTPBasicAuth()

celery = Celery(__name__, config_source='model_testing.celeryconfig')


def from_dict(d, field):
    return d[field] if field in d.keys() else None


def make_celery(app):
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask

    with app.app_context():
        celery.start()


def init_celery(app, celery):
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    # with app.app_context():
    #     celery.start()


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    db.init_app(app)
    logging.basicConfig(level=logging.DEBUG)

    from model_testing.model.enums import Langs, OSs, ImplStatus, DataFormats
    from model_testing.model.base_entity import BaseEntity
    from model_testing.model.user import User
    from model_testing.model.data_format import DataFormat
    from model_testing.model.data_set import DataSet
    from model_testing.model.processing import Processing
    from model_testing.model.experiment import Experiment
    from model_testing.model.exp_execution import ExpExecution
    from model_testing.model.exp_result import ExpResult

    # db.drop_all(app=app)
    # db.create_all(app=app)

    from model_testing.views.user import user_bp
    from model_testing.views.data_format import data_format
    from model_testing.views.data_set import data_set
    from model_testing.views.processing import processing
    from model_testing.views.experiment import experiment
    from model_testing.views.exp_result import result

    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(data_format, url_prefix='/data_format')
    app.register_blueprint(data_set, url_prefix='/data_set')
    app.register_blueprint(processing, url_prefix='/processing')
    app.register_blueprint(experiment, url_prefix='/experiment')
    app.register_blueprint(result, url_prefix='/result')

    init_celery(app, celery)

    return app


# from model_testing.database import User
from model_testing.model.user import User


@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)

    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username = username_or_token).first()

        if not user or not user.verify_password(password):
            return False
    # g.user = user
    return True




