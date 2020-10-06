from model_testing import celery as celery_app
# from flask_security.utils import config_value, send_mail
# from base.bp.users.models.user_models import User
# from base.extensions import mail # this is the flask-mail
import subprocess
import os
from model_testing.schemas import validate_json, validate_xml
from model_testing.model.enums import DataFormats
from base64 import b64decode, b64encode
from celery.result import AsyncResult
from requests.auth import HTTPBasicAuth
from requests import post
from model_testing.config import ADMIN_NAME, ADMIN_PASS
import json


def report_failure(exe_id, e):
    url = "http://127.0.0.1:5000/result/post"
    auth = HTTPBasicAuth(ADMIN_NAME, ADMIN_PASS)

    data = {"to_post": [
        {
            "execution_id" : exe_id,
            "result" : str(e)
        }
    ]
    }
    post(url, auth=auth, json=data)

    raise e


@celery_app.task(name="finalize_experiment")
def finalize_exp(exe_id, username, password):
    # TODO: send results to API, creating result record
    #  and setting status of experiment execution to 'SUCCESS'
    try:
        url = "http://127.0.0.1:5000/result/post"
        auth = HTTPBasicAuth(username, password)

        path = os.getcwd() + '/model_testing/data/input/data.txt'
        with open(path) as f:
            result = f.read()

        data = {
            "to_post": [
                {
                    "result": result,
                    "execution_id": exe_id
                }
            ]
        }

        post(url, auth=auth, json=data)

        if os.path.isfile(path):
            os.remove(path)
    except Exception as e:
        report_failure(exe_id, e)


@celery_app.task(name="clean_working_directories")
def clean(exe_id):
    # TODO: Test
    try:
        data_folder = os.getcwd() + '/model_testing/data/'
        for path in [data_folder + "stage", data_folder + "input", data_folder + "output"]:
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print('Failed to delete {} due to: {}'.format(file_path, e))
    except Exception as e:
        report_failure(exe_id, e)


@celery_app.task(name="prepare_input")
def prepare_input(exe_id, data):
    # TODO: Test
    try:
        path = os.getcwd() + '/model_testing/data/input/data.txt'

        with open(path, 'w') as f:
            f.write(data)#.decode("utf-8"))
    except Exception as e:
        report_failure(exe_id, e)


def validate(schema, instance, format_name, file_type="Input"):
    # TODO: Test
    validation = True
    format = DataFormats[format_name]
    validation = None
    if format == DataFormats.json:
        validation = validate_json(schema, instance)
    elif format == DataFormats.xml:
        validation = validate_xml(schema, instance)
    if validation is not True:
        raise Exception("{} file does not match '{}' format: {}.".format(file_type, format_name, validation))


@celery_app.task(name="verify_input")
def verify_input(exe_id, schema, format_name):
    # TODO: Test
    try:
        path = os.getcwd() + '/model_testing/data/input/data.txt'
        with open(path) as f:
            instance = f.read()
        validate(schema, instance, format_name, file_type="Input")
    except Exception as e:
        report_failure(exe_id, e)


@celery_app.task(name="verify_output")
def verify_output(exe_id, schema, format_name):
    # TODO: Test
    try:
        path = os.getcwd() + '/model_testing/data/output/data.txt'
        with open(path) as f:
            instance = f.read()
        validate(schema, instance, format_name, file_type="Output")
    except Exception as e:
        report_failure(exe_id, e)


@celery_app.task(name="finalize_stage")
def transfer_output_to_input(exe_id, ):
    # TODO: Test
    try:
        path = os.getcwd() + '/model_testing/data/'
        inp = path + "input/data.txt"
        out = path + "output/data.txt"

        if os.path.isfile(out):
            os.replace(out, inp)
    except Exception as e:
        report_failure(exe_id, e)


import sys
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


@celery_app.task(name="run_stage")
def run(exe_id, code="", lang_name="python", py_dependencies=None, args=""):
    try:
        source = b64decode(code)
        base_path = os.getcwd() + '/model_testing/data/stage/'

        if lang_name == "python":

            if py_dependencies:
                from model_testing.model.environment import get_packages

                required_packages = py_dependencies.split(" ")
                installed_packages = get_packages()

                for package in required_packages:
                    package_name, package_version = package.split("==")
                    if package_name not in installed_packages:
                        install_package(package)
                    elif installed_packages[package_name] != package_version:
                        install_package(package)

            # print(args * 1000)
            #
            # d = dict(locals(), **globals())
            # exec(source, d, d)
            path = base_path + 'script.py'
            if os.path.isfile(path):
                    os.remove(path)

            with open(path, 'wb') as file:
                file.write(source)
            os.chmod(path, 0b111101101)

            os.system(" ".join(['python3', path, args]))

            if os.path.isfile(path):
                os.remove(path)

        elif lang_name == "exe":
            try:
                path = base_path + 'program.exe'

                if os.path.isfile(path):
                    os.remove(path)

                with open(path, 'wb') as file:
                    file.write(source)
                os.chmod(path, 0b111101101)

                process = subprocess.Popen([path, os.getcwd() + '/model_testing/data/'], stdout=subprocess.PIPE) #r"/Users/user/Desktop/КДЗ/untitled/cmake-build-debug/untitled", "some arg"], stdout=subprocess.PIPE)
                stdout = process.communicate()[0]
                print('STDOUT:{}'.format(stdout))
                print(process.poll())

            except BaseException as e:
                print(e.args)

            if os.path.isfile(path):
                os.remove(path)
    except Exception as e:
        report_failure(exe_id, e)


def retrieve_ids(chain):
    ids = []
    while chain.parent:
      ids.append(chain.id)
      chain = chain.parent
    ids.append(chain.id)
    return ids


def chain_status(ids, names):
    status = {}
    i = 1
    for id, name in zip(ids, names):
        res = AsyncResult(id, app=celery_app)
        # celery_app.task)
        status[str(i)] = {
            "id": id,
            "name": name,
            "state": res.state
        }
        # task_name
        i += 1
    return status


# @celery_app.task
# def run_predefined(func):
#     func()

# @celery_app.task
# def send_async_email(msg):
#     """Background task to send an email with Flask-mail."""
#     #with app.app_context():
#     mail.send(msg)
#
# @celery_app.task
# def send_welcome_email(email, user_id, confirmation_link):
#     """Background task to send a welcome email with flask-security's mail.
#     You don't need to use with app.app_context() here. Task has context.
#     """
#     user = User.query.filter_by(id=user_id).first()
#     print(f'sending user {user} a welcome email')
#     send_mail(config_value('EMAIL_SUBJECT_REGISTER'),
#               email,
#               'welcome', user=user,
#               confirmation_link=confirmation_link)