from model_testing import db, auth

from passlib.apps import custom_app_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from flask import current_app

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Enum
from sqlalchemy import BIGINT, NVARCHAR, TIMESTAMP, ForeignKey, FLOAT, BLOB, LargeBinary
from sqlalchemy.orm import sessionmaker

import datetime
# from schemas import tm_dataset_schema, tm_dataset_xsd
from urllib.parse import urlparse
import urllib.request
from schemas import validate_json, validate_xml
from model_testing.model.base_entity import BaseEntity
from model_testing.model.enums import DataFormats


class DataFormat(BaseEntity):
    __tablename__ = 'formats'

    FormatId = Column('Id', BIGINT, ForeignKey('base_entity.Id'), primary_key=True)
    format = Column(Enum(DataFormats))
    schema = Column(String(None))
    name = Column(String(None), default="")

    __mapper_args__ = {'polymorphic_identity': 'format'}

    @staticmethod
    def create(name, format_name, uri):#, session):
        df = DataFormat()
        df.set_name(name)
        df.set_format(format_name)
        df.set_schema(uri)
        return df

    @staticmethod
    def get(id, name):
        # TODO: Test
        err = "The request must provide 'id' or 'name' of the sole Data Format record."
        df = []
        if name:
            df.append(db.session.query(DataFormat).filter(DataFormat.name == name).first())

        if id:
            df.append(db.session.query(DataFormat).filter(DataFormat.Id == id).first())

        if len(df) == 0:
            raise Exception("No such Data Format.")
        elif len(df) == 1:
            if df[0]:
                return df[0]
            else:
                raise Exception(err)
        else:
            if df[0] == df[1]:
                return df[1]
            else:
                raise Exception(err)

    def set_name(self, name):
        if not name:
            raise Exception("Name not provided.")
        if type(name) is not str:
            raise Exception("Name must be string.")
        df = db.session.query(DataFormat).filter(DataFormat.name == name).first()
        if df and (df != self):
            raise Exception("Name must be unique.")
        self.name = name

    def set_format(self, format_name):
        if not format_name:
            raise Exception("Format not provided.")
        if type(format_name) is not str:
            raise Exception("Format must be string.")
        allowed = [x.value for x in DataFormats]
        if not format_name in allowed:
            raise Exception("Format not supported. Formats available: {}".format(allowed))
        self.format = DataFormats[format_name]

    def set_schema(self, schema_uri):
        if type(schema_uri) == str:
            req = urllib.request.Request(url=schema_uri)
            with urllib.request.urlopen(req) as f:
                self.schema = f.read().decode('utf-8')
        else:
            raise Exception("Schema URI must be string.")

    def update_dataformat(self, name, format_name, schema_uri):
        if (self.name != name) and (name):
            self.set_name(name)
        if (str(self.format) != format_name) and (format_name):
            self.set_format(format_name)
        if (schema_uri):
            self.set_schema(schema_uri)

    def to_dict(self):
        df = {
            "id" : self.Id,
            "name" : self.name,
            "schema" : self.schema,
            "format" : self.format.value
        }
        return df