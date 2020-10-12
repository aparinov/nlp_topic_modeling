from os import walk
from os import listdir
from os.path import isfile, join
from time import time
from dicttoxml import dicttoxml
import json
import lxml.etree as etree
import re
from model_testing.schemas import validate_json, validate_xml

tm_dataset_xsd = """
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
   <xsd:element name="dataset" type="dataset-type" />
   <xsd:complexType name="dataset-type">
      <xsd:sequence>
         <xsd:element name="name" type="xsd:string" />
         <xsd:element name="topics" type="topics-type" />
      </xsd:sequence>
   </xsd:complexType>
   <xsd:complexType name="topics-type">
      <xsd:sequence>
         <xsd:element name="topic" type="topic-type" minOccurs="1" maxOccurs="unbounded" />
      </xsd:sequence>
   </xsd:complexType>
   <xsd:complexType name="topic-type">
      <xsd:sequence>
         <xsd:element name="name" type="xsd:string" />
         <xsd:element name="documents" type="documents-type" />
      </xsd:sequence>
   </xsd:complexType>
   <xsd:complexType name="documents-type">
      <xsd:sequence>
         <xsd:element name="document" type="document-type" minOccurs="1" maxOccurs="unbounded" />
      </xsd:sequence>
   </xsd:complexType>
   <xsd:complexType name="document-type">
      <xsd:sequence>
         <xsd:element name="name" type="xsd:string" />
         <xsd:element name="content" type="xsd:string" />
      </xsd:sequence>
   </xsd:complexType>
</xsd:schema>
"""

tm_dataset_schema = """{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "description": "Dataset structure description for topic modeling.",
    "type": "object",
    "required": ["name", "topics"],
    "properties": {
        "topics": {
            "type": "array",
            "items": {"$ref" : "#/definitions/topic"},
            "default": []
        },
        "name": {
            "type": "string",
            "description": "The name of the dataset."
        }
    },
    "definitions": {
        "topic": {
            "type": "object",
            "required": ["name", "documents"],
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the topic."
                },
                "documents": {
                    "type": "array",
                    "items": {"$ref":"#/definitions/document"}
                }
            }
        },
        "document": {
            "type": "object",
            "required": ["name", "content"],
            "properties": {
                "name": {
                    "type":"string",
                    "description": "The name of the document."
                },
                "content": {"type":"string"}
            }
        }
    }
}"""

if __name__ == "__main__":
    """Supplementary code for dataset formatting."""
    start = time()
    path = "/Users/user/Downloads/20news-18828"

    data = {}
    name = path.split("/")[-1]
    topics = []
    for x, _, _ in walk(path):
        topic = x.split("/")[-1]
        if topic != name:
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
        num = len(documents)
        each = 100
        for i in list(range(num))[0:num:each]:
            document = documents[i]
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

    print("xml valid:",validate_xml(tm_dataset_xsd, xmlv))
    print("json valid:",validate_json(tm_dataset_schema, jsonv))

    # with open(data['name'] + ".json", "w") as file:
    #     file.write(jsonv)

    # with open("20news-xs.json", "w") as file:
    #     file.write(jsonv)

    # with open(data['name'] + ".xml", "w") as file:
    #     file.write(xmlv)

    end = time()
    print(end - start)

