from sklearn.cluster import KMeans

import numpy as np
import argparse

from sklearn.preprocessing import StandardScaler
from sklearn import metrics

import tensorflow as tf
import os
import json


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


def string2tensor(s, dtype=int, spec_dtype=tf.int32):
    t = np.fromstring(s, dtype=dtype, sep=' ')
    return tf.convert_to_tensor(t, dtype=spec_dtype)


def strings2embedded(strings):
    embedded = []
    for s in strings:
        embedded.append(string2tensor(s, dtype=float, spec_dtype=tf.float32))
    return tf.stack(embedded, axis=0, name='stack')


parser = argparse.ArgumentParser(conflict_handler='resolve', description='Evaluation of clustering for given embedding.'
                                                                         ' No options.')
args = parser.parse_args()

# data_path = os.getcwd() + '/model_testing/data'
#
# inp_filename = data_path + "/input/data.txt"
# out_filename = data_path + "/output/data.txt"

data_path = os.path.join(os.getcwd(), 'model_testing', 'data')

inp_filename = os.path.join(data_path + "input", "data.txt")
out_filename = os.path.join(data_path + "output", "data.txt")

dataset = read_ds_from_file(inp_filename)

data_content, data_names, data_topic = retrieve_data(dataset)
outputs = strings2embedded(data_content)

scaler = StandardScaler()
scaler.fit(outputs)
X_scaled = scaler.transform(outputs)

kmeans = KMeans(n_clusters=20,
                n_init=100,
                max_iter=500,
                algorithm="full")

kmeans.fit(X_scaled)

labels = kmeans.predict(X_scaled)

each = 1
topic_idx = dict((y, x) for x,y in enumerate(list(set(data_topic[0:len(data_topic):each]))))
true_labels = np.array([topic_idx[label] for label in data_topic[0:len(data_topic):each]])

ARI = metrics.adjusted_rand_score(true_labels.tolist(), labels.tolist())

result = {
    "clusters":[],
    "metric_type" : "Adjusted Rand Index",
    "metric_value" : ARI
}
num = len(labels)
for label in set(labels):
    cluster = {
        "cluster_name" : str(label),
        "cluster_ids": []
    }
    for i in range(num):
        if labels[i] == label:
            cluster["cluster_ids"].append(data_names[i])
    result["clusters"].append(cluster)

write_ds_to_file(out_filename, result)