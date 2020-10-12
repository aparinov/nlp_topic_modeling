from transformers import TFRobertaModel
import numpy as np
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


def string2tensor(s, dtype=int, spec_dtype=tf.int32):
    t = np.fromstring(s, dtype=dtype, sep=' ')
    return tf.convert_to_tensor(t, dtype=spec_dtype)


def strings2tokenized(strings):
    tokenized = {'input_ids' : [], 'attention_mask': []}
    for s in strings:
        ids, att = s.split('/')
        tokenized['input_ids'].append(string2tensor(ids))
        tokenized['attention_mask'].append(string2tensor(att))
    tokenized['input_ids'] = tf.convert_to_tensor(tokenized['input_ids'])
    tokenized['attention_mask'] = tf.convert_to_tensor(tokenized['attention_mask'])
    return tokenized


def embedded2strings(outputs):
    num = outputs.shape[0]
    strings = []
    for i in range(num):
        strings.append(tensor2string(outputs[i]))
    return strings


def chunk_input(inputs, step=10):
    ids = inputs['input_ids']
    attent = inputs['attention_mask']

    chunked_attent = [attent[x:x+step] for x in range(0, len(attent), step)]
    chunked_ids = [ids[x:x+step] for x in range(0, len(ids), step)]

    chunks = []
    for att, ids in zip(chunked_attent, chunked_ids):
        dic = {
            'input_ids': ids,
            'attention_mask': att
            }
        chunks.append(dic)

    return chunks


def test(inputs, model, chunk_size=10):
    chunked_inputs = chunk_input(inputs, chunk_size)
    size = len(chunked_inputs)

    del inputs

    res = []
    for i in range(size):
        inp = chunked_inputs[i]
        while True:
            try:
                outputs = model.call(inp, training=False,
                             output_attentions=False,
                             output_hidden_states=False)
                break
            except:
                pass

        last_hidden_states = outputs[0].numpy()
        last_hidden_states = np.array(tf.math.reduce_mean(last_hidden_states, axis=1))
        del outputs
        del inp
        res.append(last_hidden_states)

    return tf.concat(res, 0, name='concat')


parser = argparse.ArgumentParser(conflict_handler='resolve', description='Tokenized text embedding using RoBERTa model.'
                                                                         ' No options.')
args = parser.parse_args()

# data_path = os.getcwd() + '/model_testing/data'
# inp_filename = data_path + "/input/data.txt"
# out_filename = data_path + "/output/data.txt"

data_path = os.path.join(os.getcwd(), 'model_testing', 'data')

inp_filename = os.path.join(data_path + "input", "data.txt")
out_filename = os.path.join(data_path + "output", "data.txt")

dataset = read_ds_from_file(inp_filename)
data_content, data_names, data_topic = retrieve_data(dataset)

inputs = strings2tokenized(data_content)
RoBERTa = TFRobertaModel.from_pretrained('roberta-large')

outputs = test(inputs, RoBERTa, chunk_size=1)

_, data_names, _ = retrieve_data(dataset)
embedded_dataset = reset_data(dataset, embedded2strings(outputs), data_names)

write_ds_to_file(out_filename, embedded_dataset)