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
from model_testing.model.data_format import DataFormat
from model_testing.model.enums import Langs
from base64 import b64decode, b64encode
from model_testing.workers import run, verify_input, verify_output, transfer_output_to_input, clean, prepare_input


class Processing(BaseEntity):
    # TODO: test
    __tablename__ = 'processing'

    ProcessingId = Column(Integer, ForeignKey('base_entity.Id'), primary_key=True)
    name = Column(String(None), default="")

    input = Column(Integer, ForeignKey('formats.Id'))
    output = Column(Integer, ForeignKey('formats.Id'))

    source = Column(LargeBinary())
    lang = Column(Enum(Langs))

    args = Column(String(None), default="")

    @staticmethod
    def get(id, name):
        p = []
        if name:
            p.append(db.session.query(Processing).filter(Processing.name == name).first())
        elif id:
            p.append(db.session.query(Processing).filter(Processing.Id == id).first())

        if len(p) == 0:
            raise Exception("No such Processing stage.")
        elif len(p) == 1:
            return p[0]
        else:
            if (p[0] == p[1]):
                return p[1]
            else:
                raise Exception("The request must provide 'id' or 'name' of the sole Processing stage record.")

    @staticmethod
    def create(name, input_id, input_name, output_id, output_name, source_uri, lang_name, args):
        p = Processing()
        p.set_name(name)
        p.set_input(input_id, input_name)
        p.set_output(output_id, output_name)
        p.set_source(source_uri)
        p.set_lang(lang_name)
        p.set_args(args)
        return p

    def set_name(self, name):
        if not name:
            raise Exception("Name not provided.")
        if type(name) is not str:
            raise Exception("Name must be string.")
        p = db.session.query(Processing).filter(Processing.name == name).first()
        if p and (p != self):
            raise Exception("Name must be unique.")
        self.name = name

    def set_input(self, format_id, format_name):
        df = DataFormat.get(format_id, format_name)
        self.input = df.Id

    def set_output(self, format_id, format_name):
        df = DataFormat.get(format_id, format_name)
        self.output = df.Id

    def set_source(self, source_uri):
        if type(source_uri) == str:
            req = urllib.request.Request(url=source_uri)
            with urllib.request.urlopen(req) as f:
                self.source = f.read()#.decode('utf-8')
        else:
            raise Exception("Source URI must be string.")

    def set_lang(self, lang_name):
        if not lang_name:
            raise Exception("Language not provided.")
        if type(lang_name) is not str:
            raise Exception("Language must be provided with string.")
        allowed = [x.value for x in Langs]
        if not lang_name in allowed:
            raise Exception("Language not supported. Languages available: {}".format(allowed))
        self.lang = Langs[lang_name]

    def set_args(self, args):
        self.args = args

    def get_input(self):
        return db.session.query(DataFormat).filter(DataFormat.Id == self.input).first()

    def get_output(self):
        return db.session.query(DataFormat).filter(DataFormat.Id == self.output).first()

    def update(self, name, input_id, input_name, output_id, output_name, source_uri, lang_name, args):
        if (self.name != name) and name:
            self.set_name(name)
        if input_id or input_name:
            self.set_input(input_id, input_name)
        if output_id or output_name:
            self.set_output(output_id, output_name)
        if source_uri:
            self.set_source(source_uri)
        if lang_name:
            self.set_lang(lang_name)
        if args:
            self.set_args(args)

    def to_dict(self):
        return {
            "id": self.Id,
            "name": self.name,
            "lang_name": self.lang.value,
            "input_name": self.get_output().name,
            "output_name": self.get_input().name,
            "args": self.args
        }

    def get_chain_items(self, exe_id):
        inp = self.get_input()
        out = self.get_output()

        inp_schema = inp.schema
        inp_format = inp.format.value

        out_schema = out.schema
        out_format = out.format.value

        return [
            verify_input.si(exe_id, inp_schema, inp_format),
            run.si(exe_id, b64encode(self.source).decode('utf-8'), self.lang.value),
            verify_output.si(exe_id, out_schema, out_format),
            transfer_output_to_input.si(exe_id)
        ]

    __mapper_args__ = {'polymorphic_identity': 'processing'}