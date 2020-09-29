import json
import os

data = {}
data_path = os.getcwd() + '/model_testing/data'
with open(data_path + '/input/data.txt') as json_file:
    data = json.load(json_file)


with open(data_path + '/output/data.txt', 'w') as json_file:
    json.dump(data, json_file)