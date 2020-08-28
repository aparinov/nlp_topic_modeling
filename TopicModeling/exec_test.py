from celery_tasks import run_stage

data = {
    "lang" : "py",
    "code" : """import numpy as np
val //= 10
raise Exception("Ooops!")

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

# print(run_stage.delay(data, local).get())
from celery import chain

# res = chain(run_stage.s(local, data), run_stage.s(data))()
# res = res.get()

# res = run_stage(run_stage(local, data), data)
from pprint import pprint

# print(res)
# try:
#     pprint(res)
# except:
#     pass

def run_experiment(exp):
    ch = chain(run_stage.s(st["local"], st["data"])
               if st["id"]==0
               else run_stage.s(st["data"])
               for st in exp["stages"])()
    res = ch.get()
    return res

# print(run_experiment(experiment))
print(run_stage.delay(data=data,local=local).get())

# def exceptor():
#     raise Exception("не ок")
#
#
# import traceback
# try:
#     exceptor()
# except:
#     pprint(traceback.format_exc())