import fastjsonschema
from lxml import etree
from jsonschema import validate

# https://json-schema.org/learn/miscellaneous-examples.html
# https://www.liquid-technologies.com/online-xsd-validator
# https://www.freeformatter.com/xml-formatter.html#ad-output


tm_res_schema = """{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "description": "Experiment result description for topic modeling task",
    "type": "object",
    "required": ["metric_type", "metric_value", "clusters"],
    "properties": {
        "clusters": {
            "type": "array",
            "items": {"$ref" : "#/definitions/cluster"},
            "default": []
        },
        "metric_type": {
            "type": "string",
            "description": "Metric applied to measure result."
        },
        "metric_value": {
            "type": "number",
        }
    },
    "definitions": {
        "cluster": {
            "type": "object",
            "required": ["cluster_name", "cluster_ids"],
            "properties": {
                "cluster_name": {
                    "type": "string",
                    "description": "The name of the cluster."
                },
                "cluster_ids": {
                    "type": "array",
                    "items": {"type":"number"}
                }
            }
        }
    }
}"""

tm_res_instance = """{
    "clusters":[
        {
            "cluster_name": "cluster1",
            "cluster_ids": [1,2,3]
        }
    ],
    "metric_type":"f1",
    "metric_value":0.71
}"""

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

tm_dataset_instance = """{
        "name":"dataset",
        "topics":[
        {
            "name": "topic1",
            "documents": [
              {"name":"docname",
              "content":"sometext"}
            ]
        }
    ]
}"""


# scheme = {'type': 'string'}
# validate = fastjsonschema.compile(scheme)
# data = validate("wasd")

# validate = fastjsonschema.compile(tm_res_schema)
# data = validate(tm_res_instance)

# from jsonschema import validate
# validate(instance=tm_res_instance, schema=tm_res_schema)

tm_res_xsd = """
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
   <xsd:element name="experimentResult" type="experiment-type" />
   <xsd:complexType name="experiment-type">
      <xsd:sequence>
         <xsd:element name="clusters" type="clusters-type" />
         <xsd:element name="metricType" type="xsd:string" />
         <xsd:element name="metricValue" type="xsd:int" />
      </xsd:sequence>
   </xsd:complexType>
   <xsd:complexType name="clusters-type">
      <xsd:sequence>
         <xsd:element name="cluster" type="cluster-type" minOccurs="1" maxOccurs="unbounded" />
      </xsd:sequence>
   </xsd:complexType>
   <xsd:complexType name="cluster-type">
      <xsd:sequence>
         <xsd:element name="clusterName" type="xsd:string" />
         <xsd:element name="clusterIds" type="ids-type" />
      </xsd:sequence>
   </xsd:complexType>
   <xsd:complexType name="ids-type">
      <xsd:sequence>
         <xsd:element name="id" type="xsd:int" minOccurs="1" maxOccurs="unbounded" />
      </xsd:sequence>
   </xsd:complexType>
</xsd:schema>
"""

tm_res_xml = """
<experimentResult>
   <clusters>
      <cluster>
         <clusterName>cluster1</clusterName>
         <clusterIds>
            <id>1</id>
         </clusterIds>
      </cluster>
      <cluster>
         <clusterName>cluster2</clusterName>
         <clusterIds>
            <id>2</id>
            <id>3</id>
         </clusterIds>
      </cluster>
   </clusters>
   <metricType>f1-score</metricType>
   <metricValue>71</metricValue>
</experimentResult>
"""

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

tm_dataset_xml = """
<dataset>
   <name>Dataset</name>
   <topics>
      <topic>
         <topicName>topic1</topicName>
         <documents>
            <document>
               <name>1</name>
               <content>Some text</content>
            </document>
            <document>
               <name>3</name>
               <content>Some text</content>
            </document>
         </documents>
      </topic>
      <topic>
         <topicName>topic2</topicName>
         <documents>
            <document>
               <name>2</name>
               <content>Some text</content>
            </document>
         </documents>
      </topic>
   </topics>
</dataset>
"""


def validate_xml(xsd, xml):
    try:
        schema_root = etree.XML(xsd)
        schema = etree.XMLSchema(schema_root)
        parser = etree.XMLParser(schema = schema)
        etree.fromstring(xml, parser)
    except Exception as e:
        return e.args
    return True

import ast

def validate_json(schema, instance):
    try:
        schema = ast.literal_eval(schema)
        instance = ast.literal_eval(instance)
        validate = fastjsonschema.compile(schema)
        validate(instance)
    except Exception as e:
        return e.args
    return True


schemas =   [tm_res_schema,   tm_dataset_schema]
instances = [tm_res_instance, tm_dataset_instance]

# print(validate_json(schemas[0], instances[0]))
# print(validate_json(schemas[0], instances[1]))
# print(validate_json(schemas[1], instances[0]))
# print(validate_json(schemas[1], instances[1]))
#
xsds = [tm_res_xsd, tm_dataset_xsd]
xmls = [tm_res_xml, tm_dataset_xml]
#
# print(validate_xml(xsds[0], xmls[0]))
# print(validate_xml(xsds[0], xmls[1]))
# print(validate_xml(xsds[1], xmls[0]))
# print(validate_xml(xsds[1], xmls[1]))

# schemas_path = "./schemas/"
#
# with open(schemas_path + "tm_res_xsd.xml", "w") as file:
#     file.write(tm_res_xsd)
#
# with open(schemas_path + "tm_dataset_xsd.xml", "w") as file:
#     file.write(tm_dataset_xsd)
#
# with open(schemas_path + "tm_res_schema.json", "w") as file:
#     file.write(tm_res_schema)
#
# with open(schemas_path + "tm_dataset_schema.json", "w") as file:
#     file.write(tm_dataset_schema)