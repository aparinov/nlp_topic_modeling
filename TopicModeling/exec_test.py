from celery_tasks import run_stage
from celery.result import AsyncResult
from celery import chain
from pprint import pprint
from celery import app
from celery import current_app

data = {
    "lang" : "py",
    "code" : """import numpy as np
val //= 10
# raise Exception("Ooops!")

""",
    "dependencies" : ["numpy"],
    "input" : {"val":int},
    "output" : {"val":int}
}
local = {"val" : 123}

next_stage_id = 1
category = "preprocessing"

experiment = {
    "stages": [
        {
            "id":0,
            "data":data,
            "local":local
        },
        {
            "id":1,
            "data":data
         }
    ]
}

def retrieve_ids(chain):
    ids = []
    while chain.parent:
      ids.append(chain.id)
      chain = chain.parent
    ids.append(chain.id)
    return ids

def chain_status(ids):
    status = {}
    i = 1
    for id in ids:
        res = AsyncResult(id)
        status[str(i)] = {"id":id,"state":res.state}
        i += 1
    return status

def run_experiment(exp):
    ch = chain(run_stage.s(st["local"], st["data"])
               if st["id"]==0
               else run_stage.s(st["data"])
               for st in exp["stages"]).apply_async()

    ids = retrieve_ids(ch)

    print(type(ch))
    pprint(chain_status(ids))

    res = ch.get()

    pprint(chain_status(ids))

    return res

# print(list(worker for worker in current_app.control.inspect().ping()))


# st = run_stage.delay(data=data,local=local)
# id = st.task_id
# print(id)
#
# res = AsyncResult(id)
# print(res.state)

# print(st.get())


# PENDING
# The task is waiting for execution.
# STARTED
# The task has been started.
# RETRY
# The task is to be retried, possibly because of failure.
# FAILURE
# The task raised an exception, or has exceeded the retry limit. The result attribute then contains the exception raised by the task.
# SUCCESS
# The task executed successfully. The result attribute then contains the tasks return value.


print(run_experiment(experiment))

from celery.app.task import Task
# from celery_tasks import long_test
# test_task = long_test.delay(i=5)
# task_id = test_task.task_id

# import celery

from factory import create_celery_app

# celery = create_celery_app()
# from celery.app import task
# task.update_state(task_id=task_id, state='PAUSING')

from celery_tasks import celery

# celery.task().update_state(task_id=task_id, state='PAUSING')
# test_task.update_state(self=celery, task_id=task_id, state='PAUSING')
# test_task.update_state(self=celery, task_id=task_id, state='PAUSING')

from time import sleep
sleep(10)

# delete
# celery.control.revoke(task_id, terminate=True, signal='SIGKILL')



# Testing communication with executable
import subprocess
# from sys import stdout
import subprocess
import shlex

process = subprocess.Popen([r"/Users/user/Desktop/КДЗ/untitled/cmake-build-debug/untitled", "some arg"], stdout=subprocess.PIPE)
stdout = process.communicate()[0]
print('STDOUT:{}'.format(stdout))

print(process.poll())