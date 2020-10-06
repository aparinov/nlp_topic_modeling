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
from model_testing.model.data_set import DataSet
from model_testing.model.processing import Processing
from model_testing.model.experiment import Experiment
from model_testing.model.enums import Langs
from celery import chain


class ExpResult(BaseEntity):
    # TODO: test
    __tablename__ = 'results'

    result_id = Column('Id', Integer, ForeignKey('base_entity.Id'), primary_key=True)

    # baseline = Column(Integer, default=0)
    # value = Column(Integer, default=0)
    # metric = Column(String(None), default="")

    experiment = Column(Integer, ForeignKey('experiment.Id'))
    execution = Column(Integer, ForeignKey('execution.Id'))

    result = Column(LargeBinary())

    __mapper_args__ = {'polymorphic_identity': 'result'}


    @staticmethod
    def create(baseline, value, experiment, result):
        r = ExpResult()
        # r.set_baseline(baseline)
        # r.set_value(value)
        r.set_experiment(experiment)
        r.set_result(result)
        # r.set_author(experiment.get_author())
        return r

    @staticmethod
    def get(id):
        if id:
            return db.session.query(ExpResult).filter(ExpResult.Id == id).first()
        raise Exception("No such Experiment Result.")

    # def set_baseline(self, baseline):
    #     self.baseline = baseline
    #
    # def set_value(self, value):
    #     self.value = value

    def set_experiment(self, experiment):
        self.experiment = experiment.Id

    def set_execution(self, execution):
        self.execution = execution.Id

    def set_result(self, result):
        self.result = result.encode('utf-8')

    def to_dict(self):
        author = self.get_author()
        return {
            "id" : self.Id,
            "experiment" : Experiment.get(self.experiment, None).to_dict(),
            "result" : self.result.decode('utf-8'),
            "author_username" : author.username,
            "author_id" : author.id
        }

    def to_dict_light(self):
        author = self.get_author()
        return {
            "id" : self.Id,
            "experiment" : Experiment.get(self.experiment, None).to_dict(),
            "author_username" : author.username,
            "author_id" : author.id
        }