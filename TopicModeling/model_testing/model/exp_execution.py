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
from model_testing.model.enums import Langs
from model_testing.model.enums import ExecutionStatus
from celery import chain
from model_testing.model.experiment import Experiment
from model_testing.workers import chain_status
from model_testing import celery


class ExpExecution(BaseEntity):
    __tablename__ = 'execution'

    ExpExecutionId = Column('Id', Integer, ForeignKey('base_entity.Id'), primary_key=True)
    monitoring_IDs = Column(String(None), default="")
    monitoring_names = Column(String(None), default="")
    status = Column(Enum(ExecutionStatus))
    experiment = Column(Integer, ForeignKey('experiment.Id'))

    __mapper_args__ = {'polymorphic_identity': 'execution'}

    @staticmethod
    def create(exp, author):
        e = ExpExecution()
        status = ExecutionStatus.started
        # e.set_ids(arr)
        e.set_status(status)
        e.set_experiment(exp)
        e.set_author(author)
        return e

    @staticmethod
    def get(id):
        if id:
            return db.session.query(ExpExecution).filter(ExpExecution.Id == id).first()
        raise Exception("No such Experiment Execution.")

    def set_ids(self, arr):
        # arr must be list of ints
        if arr:
            ids = ' '.join([str(i) for i in arr])
            self.monitoring_IDs = ids

    def set_task_names(self, arr):
        if arr:
            names = ' '.join([str(i) for i in arr])
            self.monitoring_names = names

    def set_status(self, status):
        self.status = status

    def set_experiment(self, exp):
        self.experiment = exp.Id

    def get_experiment(self):
        return Experiment.get(self.experiment, None)

    def get_ids(self):
        # return [int(s) for s in self.monitoring_IDs.split(' ')]
        return self.monitoring_IDs.split(' ')

    def get_names(self):
        return self.monitoring_names.split(' ')

    def to_dict(self):
        exp = self.get_experiment()
        ids = self.get_ids()
        names = self.get_names()
        author = self.get_author()
        return {
            'execution_id': self.Id,
            'experiment' : exp.to_dict(),
            'status': self.status.value,
            "stages": chain_status(ids, names),
            "author_username" : author.username,
            "author_id" : author.id
        }

    def cancel(self):
        for id in self.get_ids():
            celery.control.revoke(id, terminate=True, signal='SIGKILL')
        self.set_status(ExecutionStatus.finished)