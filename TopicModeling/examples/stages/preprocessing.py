from bs4 import BeautifulSoup
import unidecode

import re
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


def apply_to_tm_ds(data_set, prepr):
    for i in range(len(data_set['topics'])):
        topic = data_set['topics'][i]
        for j in range(len(topic['documents'])):
            document = topic['documents'][j]
            content = document["content"]
            document["content"] = prepr(content)


def reset_data(data_set, contents, names):
    for i in range(len(data_set['topics'])):
        for j in range(len(data_set['topics'][i]['documents'])):
            name = names.pop(0)
            content = contents.pop(0)

            data_set['topics'][i]['documents'][j]["content"] = content
            data_set['topics'][i]['documents'][j]["name"] = name
    return data_set


# Noise Removal
def noise_removal(text):
    noisy_chars = r'[\-\>\<\\\(\)\[\]\/\*\_]+'
    return re.sub(noisy_chars, ' ', text)


# Remove urls
def urls_removal(text):
    urls = r'https?://\S+|www\.\S+'
    return re.sub(urls, '', text)


# Remove emails
def emails_removal(text):
    urls = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    return re.sub(urls, ' ', text).replace('\n', ' ').replace('-', ' ')


import argparse
parser = argparse.ArgumentParser(description='Process some integers.')


data_path = os.getcwd() + '/model_testing/data'

inp_filename = data_path + "/input/data.txt"
out_filename = data_path + "/output/data.txt"

dataset = read_ds_from_file(inp_filename)

apply_to_tm_ds(dataset, noise_removal)
apply_to_tm_ds(dataset, lambda text: text.lower())
apply_to_tm_ds(dataset, urls_removal)
apply_to_tm_ds(dataset, emails_removal)
apply_to_tm_ds(dataset, lambda text: BeautifulSoup(text, "lxml").text)
apply_to_tm_ds(dataset, lambda text: unidecode.unidecode(re.sub('[\s]+', ' ', text)))

write_ds_to_file(out_filename, dataset)