from celery import Celery
# from config import config

# def create_app(config_filename):
#     app = Flask(__name__)
#     app.config.from_pyfile(config_filename)
#
#     from yourapplication.model import db
#     db.init_app(app)
#
#     from .views.admin import admin
#     from yourapplication.views.frontend import frontend
#     app.register_blueprint(admin)
#     app.register_blueprint(frontend)
#
#     return app

def create_celery_app():#app=None):
    # app = app or create_app(config)
    broker = "amqp://username:password@localhost:5672" #'amqp://0.0.0.0:5672'
    backend = 'db+sqlite:///db.sqlite3'
    celery = Celery('tasks', broker=broker,
                    accept_content=['pickle'], backend=backend)
    celery.config_from_object("celeryconfig")

    # celery.conf.update(app.config)
    # TaskBase = celery.Task

    # class ContextTask(TaskBase):
    #     abstract = True
    #
    #     def __call__(self, *args, **kwargs):
    #         with app.app_context():
    #             return TaskBase.__call__(self, *args, **kwargs)

    # celery.Task = ContextTask

    return celery