import subprocess
import sys
from celery import Celery
import traceback

celery = Celery('tasks', broker='amqp://0.0.0.0:5672', accept_content=['pickle'], backend='db+sqlite:///db.sqlite3')
celery.config_from_object("celeryconfig")


@celery.task(serializer="pickle")
def run_stage(local: dict, data: dict) -> dict:
    try:
        process = subprocess.Popen([sys.executable, "-m", "pip", "freeze"], stdout=subprocess.PIPE)
        stdout = process.communicate()[0]
        names_versions = stdout.decode('ascii').split("\n")
        names = list(map(lambda x: x.split('==')[0], names_versions))

        for var in local:
            if var in data["input"]:
                if type(local[var]) != data["input"][var]:
                    raise Exception("Input type mismatch for \"{}\", must be {} instead of {}.".format(var, str(data["input"][var]), str(type(local[var]))))

        if data["lang"] == "py":
            for package in data["dependencies"]:
                if (package not in names_versions) and (package not in names):
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    print(package, "installed!")
                # else:
                    # print("Already installed!")

            exec(data["code"], globals(), local)

            locals_cleared = {}

            for var in local:
                if var in data["output"]:
                    if type(local[var]) != data["output"][var]:
                        raise Exception("Output type mismatch for \"{}\", must be {} instead of {}.".format(var, str(data["output"][var]), str(type(local[var]))))
                    locals_cleared[var] = local[var]


            local = locals_cleared

        else:
            raise Exception("Language not suported.")
    except:
        return {"exception" : traceback.format_exc()}

    return local
