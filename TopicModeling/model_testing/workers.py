from model_testing import celery as celery_app
import subprocess
import os
import sys
from model_testing.schemas import validate_json, validate_xml
from model_testing.model.enums import DataFormats, ExecutionStatus
from base64 import b64decode
from celery.result import AsyncResult
from requests.auth import HTTPBasicAuth
from requests import post
from model_testing.config import ADMIN_NAME, ADMIN_PASS


def report_failure(exe_id, e):
    url = "http://127.0.0.1:5000/result/post"
    auth = HTTPBasicAuth(ADMIN_NAME, ADMIN_PASS)

    data = {"to_post": [{"exe_id" : exe_id,
                        "result" : str(e),
                        "status" : ExecutionStatus.failure.value}]}
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
        data = {"to_post":[{"result": result,
                            "exe_id": exe_id,
                            "status" : ExecutionStatus.finished.value}]}
        post(url, auth=auth, json=data)
        if os.path.isfile(path):
            os.remove(path)
        return None
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
            f.write(data)
    except Exception as e:
        report_failure(exe_id, e)


def validate(schema, instance, format_name, file_type="Input"):
    # TODO: Test
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
    except FileNotFoundError:
        report_failure(exe_id, "No dataset was provided in 'data/input/data.txt'.")


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
    except FileNotFoundError:
        report_failure(exe_id, "Given processing stage didn't save result to 'data/output/data.txt'.")


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


def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


@celery_app.task(bind=True, name="await_previous", max_retries=None)
def await_previous(self, prev_id):
    print(prev_id)
    if prev_id:
        allowed = ['SUCCESS','FAILURE', 'RETRY', 'REVOKED']
        res = AsyncResult(prev_id)
        print(res.state in allowed)
        if res.state not in allowed:
            raise self.retry(prev_id=prev_id, countdown=60)
    print(prev_id)


@celery_app.task(name="run_stage")
def run(exe_id, code="", lang_name="python", py_dependencies=None, args=""):
    try:
        source = b64decode(code)
        base_path = os.getcwd() + '/model_testing/data/stage/'

        args_ar = args.split(' ')

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
            argv = sys.argv

            sys.argv = args_ar
            d = dict(locals(), **globals())
            exec(source, d, d)

            sys.argv = argv

        elif lang_name == "exe":
            path_to_exe = os.getcwd() + '/model_testing/data/stage/program.exe'
            path_to_data = os.getcwd() + '/model_testing/data/'

            if os.path.isfile(path_to_exe):
                os.remove(path_to_exe)

            with open(path_to_exe, 'wb') as file:
                file.write(source)
            os.chmod(path_to_exe, 0b111101101)

            call = [path_to_exe, '--file_path', path_to_data] + (args_ar if args.strip() else [])

            process = subprocess.Popen(call, stdout=subprocess.PIPE)
            stdout = process.communicate()[0]

            if os.path.isfile(path_to_exe):
                os.remove(path_to_exe)

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
    i = len(names)
    for id, name in zip(ids, reversed(names)):
        res = AsyncResult(id, app=celery_app)
        status[str(i)] = {
            "id": id,
            "name": name,
            "state": res.state
        }
        i -= 1
    return status