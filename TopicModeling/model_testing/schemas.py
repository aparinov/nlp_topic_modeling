import fastjsonschema
from lxml import etree
import ast


def validate_xml(xsd, xml):
    try:
        schema_root = etree.XML(xsd)
        schema = etree.XMLSchema(schema_root)
        parser = etree.XMLParser(schema = schema)
        etree.fromstring(xml, parser)
    except Exception as e:
        return e.args
    return True


def validate_json(schema, instance):
    try:
        schema = ast.literal_eval(schema)
        instance = ast.literal_eval(instance)
        validate = fastjsonschema.compile(schema)
        validate(instance)
    except Exception as e:
        return e.args
    return True