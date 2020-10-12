from transformers import RobertaTokenizer
import tensorflow as tf
import os
import json
import argparse

gpus = tf.config.experimental.list_physical_devices('GPU')
if len(gpus) != 0:
    tf.config.experimental.set_memory_growth(gpus[0], True)


def read_ds_from_file(filename):
    data = {}
    with open(filename) as json_file:
        data = json.load(json_file)
    return data


def write_ds_to_file(filename, data):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file)


def retrieve_data(data_set):
    contents = []
    names = []
    topics = []
    for i in range(len(data_set['topics'])):
        topic = data_set['topics'][i]['name']
        for j in range(len(data_set['topics'][i]['documents'])):
            contents.append(data_set['topics'][i]['documents'][j]["content"])
            names.append(data_set['topics'][i]['documents'][j]["name"])
            topics.append(topic)
    return contents, names, topics


def reset_data(data_set, contents, names, topics=None):
    for i in range(len(data_set['topics'])):
        for j in range(len(data_set['topics'][i]['documents'])):
            name = names.pop(0)
            content = contents.pop(0)

            data_set['topics'][i]['documents'][j]["content"] = content
            data_set['topics'][i]['documents'][j]["name"] = name
    return data_set


def tensor2string(tensor):
    return ' '.join([str(i) for i in tensor.numpy().tolist()])


def tokenized2strings(inputs):
    ids = [tensor2string(t) for t in inputs['input_ids']]
    att = [tensor2string(t) for t in inputs['attention_mask']]
    res = []
    for i, a in zip(ids, att):
        res.append(i + "/" + a)
    return res


parser = argparse.ArgumentParser(conflict_handler='resolve', description='Text tokenization. No options.')
args = parser.parse_args()

data_path = os.path.join(os.getcwd(), 'model_testing', 'data')

inp_filename = os.path.join(data_path + "input", "data.txt")
out_filename = os.path.join(data_path + "output", "data.txt")
# data_path = os.getcwd() + '/model_testing/data'
#
# inp_filename = data_path + "/input/data.txt"
# out_filename = data_path + "/output/data.txt"

each = 1

dataset = read_ds_from_file(inp_filename)

data_content, data_names, data_topic = retrieve_data(dataset)

tokenizer = RobertaTokenizer.from_pretrained("roberta-large")

inputs = tokenizer(data_content[0:len(data_content):each], return_tensors="tf", truncation=True, padding=True)

_, data_names, _ = retrieve_data(dataset)
tokenized_dataset = reset_data(dataset, tokenized2strings(inputs), data_names)

write_ds_to_file(out_filename, tokenized_dataset)