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
from sqlalchemy.orm import sessionmaker, relationship

import datetime
# from schemas import tm_dataset_schema, tm_dataset_xsd
from urllib.parse import urlparse
import urllib.request
from model_testing.schemas import validate_json, validate_xml
from model_testing.model.base_entity import BaseEntity
from model_testing.model.data_format import DataFormat
from model_testing.model.enums import DataFormats

from model_testing.workers import run, verify_input, verify_output, transfer_output_to_input, clean, prepare_input

class DataSet(BaseEntity):
    __tablename__ = 'datasets'

    DataSetId = Column('Id', Integer, ForeignKey('base_entity.Id'), primary_key=True)
    DataFormat = Column(Integer, ForeignKey('formats.Id'))
    # DataFormat = relationship("DataFormat", cascade="all, delete-orphan")
    Data = Column(LargeBinary())
    Title = Column(String(None), default="")

    __mapper_args__ = {'polymorphic_identity': 'dataset'}

    @staticmethod
    def create(title, uri, format_id, format_name):
        ds = DataSet()
        ds.set_title(title)
        ds.set_data_format(format_id, format_name)
        ds.set_data(uri)
        ds.validate()
        return ds

    @staticmethod
    def get(id, title):
        # TODO: test
        ds = []
        if title:
            ds.append(db.session.query(DataSet).filter(DataSet.Title == title).first())
        elif id:
            ds.append(db.session.query(DataSet).filter(DataSet.Id == id).first())

        if len(ds) == 0:
            raise Exception("No such Data Set.")
        elif len(ds) == 1:
            return ds[0]
        else:
            if (ds[0] == ds[1]):
                return ds[1]
            else:
                raise Exception("The request must provide 'id' or 'title' of the sole Data Set record.")
        # if (((title == None) and (id == None)) or ((title != None) and (id != None))):
        #     raise Exception("Request must provide 'id' or 'name' of DataSet.")
        # ds = None
        # if title:
        #     ds = db.session.query(DataSet).filter(DataSet.Title == title).first()
        # elif id:
        #     ds = db.session.query(DataSet).filter(DataSet.Id == id).first()
        # if not ds:
        #     raise Exception("No such DataSet.")
        # return ds

    def set_data_format(self, id, name):
        df = DataFormat.get(id, name)
        self.DataFormat = df.Id

    def set_data(self, uri):
        if not uri:
            raise Exception("URI not provided.")
        if type(uri) is not str:
            raise Exception("URI must be string.")
        try:
            req = urllib.request.Request(url=uri)
            with urllib.request.urlopen(req) as f:
                data = f.read()#.decode("utf-8")
            self.Data = data
        except Exception as e:
            raise Exception("Can't read file: {}".format(uri))

    def set_title(self, title):
        if not title:
            raise Exception("Title not provided.")
        if type(title) is not str:
            raise Exception("Title must be string.")
        ds = db.session.query(DataSet).filter(DataSet.Title == title).first()
        if ds and (ds != self):
            raise Exception("Title must be unique.")
        self.Title = title

    def validate(self):
        if not self.Title:
            raise Exception("Title not provided.")
        if not self.DataFormat:
            raise Exception("DataFormat not provided.")
        if not self.Data:
            raise Exception("Data not provided.")

        df = DataFormat.get(self.DataFormat, None)
        if not df:
            raise DataFormat("Data Format not available.")

        instance = self.Data.decode("utf-8")
        format = df.format
        format_name = df.name
        schema = df.schema
        title = self.Title

        validation = True
        if (format == DataFormats.json):
            validation = validate_json(schema, instance)
        elif (format == DataFormats.xml):
            validation = validate_xml(schema, instance)

        if (validation is not True):
            raise Exception("File '{}' does not match '{}' format: {}.".format(title, format_name, validation))

    def update(self, new_title, new_uri, new_format_id, new_format_name):
        if new_title and (type(new_title) is str):
            self.set_title(new_title)
        if new_uri and (type(new_uri) is str):
            self.set_data(new_uri)
        if new_format_id or new_format_name:
            self.set_data_format(new_format_id, new_format_name)
        self.validate()

    def to_dict(self):
        df = DataFormat.get(self.DataFormat, None)
        ds = {
            "id" : self.Id,
            "title" : self.Title,
            "data" : self.Data.decode("utf-8"),
            "format_name" : df.name,
            "format_id" : df.Id
        }
        return ds

    # def to_file(self):
    #     # TODO: Test
    #     with open('/data/input/data.txt', 'w') as f:
    #         f.write(self.Data.decode("utf-8"))

    def get_chain_items(self, exe_id):
        data = self.Data.decode('utf-8')
        return [clean.si(exe_id), prepare_input.si(exe_id, data)]