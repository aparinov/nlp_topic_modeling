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
from celery import chain
from model_testing.config import ADMIN_NAME, ADMIN_PASS




class Experiment(BaseEntity):
    # TODO: test
    __tablename__ = 'experiment'

    ExperimentId = Column('Id', Integer, ForeignKey('base_entity.Id'), primary_key=True)

    __mapper_args__ = {'polymorphic_identity': 'experiment'}

    Title = Column(String(None), default="")
    ShortTitle = Column(String(None), default="")

    Comment = Column(String(None), default="")

    ProcessingIDs = Column(String(None), default="")

    Baseline = Column(Integer, default=0)

    ResultFormat = Column(Integer, ForeignKey('formats.Id'))
    Dataset = Column(Integer, ForeignKey('datasets.Id'))

    @staticmethod
    def get(id, title):
        p = []
        if title:
            p.append(db.session.query(Experiment).filter(Experiment.Title == title).first())
        elif id:
            p.append(db.session.query(Experiment).filter(Experiment.Id == id).first())

        if len(p) == 0:
            raise Exception("No such Experiment.")
        elif len(p) == 1:
            return p[0]
        else:
            if (p[0] == p[1]):
                return p[1]
            else:
                raise Exception("The request must provide 'id' or 'title' of the sole Experiment record.")

    @staticmethod
    def create(title, short_title, comment, processing_arr, baseline, res_id, res_name, dataset_id, dataset_title):
        e = Experiment()
        e.set_title(title)
        e.set_short_title(short_title)
        e.set_comment(comment)
        e.set_processing(processing_arr)
        e.set_baseline(baseline)
        e.set_result_format(res_id, res_name)
        e.set_dataset(dataset_id, dataset_title)
        return e

    def set_title(self, title):
        if not title:
            raise Exception("Title not provided.")
        if type(title) is not str:
            raise Exception("Title must be string.")
        p = db.session.query(Experiment).filter(Experiment.Title == title).first()
        if p and (p != self):
            raise Exception("Title must be unique.")
        self.Title = title

    def set_short_title(self, title):
        if not title:
            raise Exception("Short Title not provided.")
        if type(title) is not str:
            raise Exception("Short Title must be string.")
        self.ShortTitle = title

    def set_comment(self, comment):
        if not comment:
            raise Exception("Comment not provided.")
        if type(comment) is not str:
            raise Exception("Comment must be string.")
        self.Comment = comment

    def set_processing(self, arr):
        if not arr:
            raise Exception("Processing IDs not provided.")
        if type(arr) != list:
            raise Exception("Processing IDs should be list of integers.")
        if len(arr) == 0:
            raise Exception("No Processing IDs provided.")
        for i in arr:
            if type(i) != int:
                raise Exception("Processing IDs should be list of integers.")
            if not Processing.get(i, None):
                raise Exception("Processing with id={} does not exist.".format(i))
        self.ProcessingIDs = " ".join(str(s) for s in arr)

    def set_baseline(self, num):
        if not num:
            raise Exception("Baseline not provided.")
        if type(num) != int:
            raise Exception("Baseline should be integer in range [0, 100].")
        if not (0 <= num <= 100):
            raise Exception("Baseline should be integer in range [0, 100].")
        self.Baseline = num

    def set_result_format(self, id, name):
        df = None
        try:
            df = DataFormat.get(id, name)
        except:
            raise Exception("No valid Result Format provided! "
                            "You must provide 'result_format_id' or 'result_format_name'.")
        self.ResultFormat = df.Id


    def set_dataset(self, id, name):
        ds = None
        try:
            ds = DataSet.get(id, name)
        except:
            raise Exception("No valid DataSet provided! "
                            "You must provide 'result_format_id' or 'result_format_name'.")
        self.Dataset = ds.Id

    def update(self, title, short_title, comment, processing_arr,
               baseline, format_id, format_name, dataset_id, dataset_title):
        if self.Title != title:
            self.set_title(title)
        if short_title:
            self.set_short_title(short_title)
        if comment:
            self.set_comment(comment)
        if processing_arr:
            self.set_processing(processing_arr)
        if baseline:
            self.set_baseline(baseline)
        if format_id or format_name:
            self.set_result_format(format_id, format_name)
        if dataset_id or dataset_title:
            self.set_dataset(dataset_id, dataset_title)

    def get_dataset(self):
        return DataSet.get(self.Dataset, None)

    def get_processing_ids(self):
        return [int(s) for s in self.ProcessingIDs.split(' ')]

    def get_processing(self):
        arr = self.get_processing_ids()
        for i in arr:
            if not Processing.get(i, None):
                raise Exception("Stage with id={} does not exist. Please update ProcessingIDs of '' experiment.".format(i, self.Title))
        return [Processing.get(i, None) for i in arr]

    def get_result_format(self):
        return DataFormat.get(self.ResultFormat, None)

    # Title, ShortTitle, Comment, ProcessingIDs, Baseline, ResultFormat, Dataset

    def to_dict(self):
        res = {"id": self.Id, "title": self.Title, "short_title": self.ShortTitle, "comment": self.Comment,
               "baseline": self.Baseline}

        f = self.get_result_format()
        if f:
            res["result_format_name"] = f.name
        else:
            res["result_format_name"] = None

        ds = self.get_dataset()
        if ds:
            res["dataset_title"] = ds.Title
        else:
            res["dataset_title"] = None

        return res


    def run(self):
        from model_testing.workers import retrieve_ids, chain_status, finalize_exp, verify_input
        from model_testing.model.exp_execution import ExpExecution

        ds = self.get_dataset()
        procs = self.get_processing()

        res_f = self.get_result_format()

        exp_exe = ExpExecution.create(self)
        db.session.add(exp_exe)
        db.session.commit()

        exe_id = exp_exe.Id

        schema = res_f.schema
        format_name = res_f.format.value


        chain_items = ds.get_chain_items(exe_id)
        for proc in procs:
            chain_items = chain_items + proc.get_chain_items(exe_id)
        chain_items = chain_items + [verify_input.si(exe_id, schema, format_name), finalize_exp.si(exe_id, ADMIN_NAME, ADMIN_PASS)]

        from celery import signature

        ch = chain(chain_items).apply_async()

        ids = retrieve_ids(ch)
        task_names = [signature(s)['task'] for s in chain_items]

        exp_exe.set_ids(ids)
        exp_exe.set_task_names(task_names)

        db.session.commit()

        return exp_exe.to_dict()

