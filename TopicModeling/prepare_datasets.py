from os import walk
from os import listdir
from os.path import isfile, join
from time import time
from dicttoxml import dicttoxml
import json
import lxml.etree as etree
import re
from schemas import tm_dataset_instance, tm_dataset_schema, \
    tm_dataset_xsd, validate_json, validate_xml

start = time()
path = "/Users/user/Downloads/20news-18828"

data = {}
name = path.split("/")[-1]
topics = []
for x, _, _ in walk(path):
    topic = x.split("/")[-1]
    if (topic != name):
        topics.append(topic)

data['name'] = name
data['topics'] = []

chars = ['\x18', '\x1e', '\x06', '\x1c', '\x7f', '\x02', '\x19', '\x10', '\x1a', '\x03', '\x08', '\x1b','\x0c']
rx = '[' + re.escape(''.join(chars)) + ']'

for topic in topics:
    topic_path = path + "/" + topic
    topic_obj = {
        "name": topic,
        "documents":[]
    }

    documents = [f for f in listdir(topic_path) if isfile(join(topic_path, f))]
    for document in documents:
        with open(topic_path + "/" + document, 'rb') as file:
            content = file.read()
            content = content.decode('utf-8', errors="ignore")
            content = re.sub(rx, '', content)
        topic_obj["documents"].append({
            "name": document,
            "content": content
        })

    data['topics'].append(topic_obj)

xmled = dicttoxml(data, custom_root='dataset', attr_type=False, item_func=lambda x: x[:-1])
parser = etree.XMLParser(huge_tree=True)
x = etree.fromstring(xmled, parser=parser)

xmlv = etree.tostring(x, pretty_print=True).decode('utf-8')
jsonv = json.dumps(data, indent = 4)

# print(type(jsonv))
print("xml valid:",validate_xml(tm_dataset_xsd, xmlv))
print("json valid:",validate_json(tm_dataset_schema, jsonv))

# with open(data['name'] + ".json", "w") as file:
#     file.write(jsonv)
# #
# with open(data['name'] + ".xml", "w") as file:
#     file.write(xmlv)

end = time()
print(end - start)

