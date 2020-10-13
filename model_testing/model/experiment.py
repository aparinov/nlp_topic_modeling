from flask import current_app
from celery import chain

from sqlalchemy import Column, Integer, String
from sqlalchemy import BIGINT, NVARCHAR, TIMESTAMP, ForeignKey, FLOAT, BLOB, LargeBinary

from datetime import datetime
from model_testing.model.base_entity import BaseEntity
from model_testing.model.data_format import DataFormat
from model_testing.model.data_set import DataSet
from model_testing.model.processing import Processing
from model_testing import db
from model_testing.config import ADMIN_NAME, ADMIN_PASS


class Experiment(BaseEntity):
    __tablename__ = 'experiment'

    experiment_id = Column('id', Integer, ForeignKey('base_entity.id'), primary_key=True)

    __mapper_args__ = {'polymorphic_identity': 'experiment'}

    title = Column(String(None), default="")
    short_title = Column(String(None), default="")

    comment = Column(String(None), default="")

    processing_ids = Column(String(None), default="")

    baseline = Column(FLOAT, default=0.)

    result_format = Column(Integer, ForeignKey('formats.id'))
    dataset = Column(Integer, ForeignKey('datasets.id'))

    @staticmethod
    def get(exp_id, title):
        exp = []
        if title:
            exp.append(db.session.query(Experiment).filter(Experiment.title == title).first())
        if exp_id:
            exp.append(db.session.query(Experiment).filter(Experiment.id == exp_id).first())

        exp = list(filter(lambda x: x is not None, exp))

        if len(exp) == 0:
            raise Exception("No such Experiment.")
        elif len(exp) == 1:
            return exp[0]
        else:
            if exp[0] == exp[1]:
                return exp[0]
            else:
                raise Exception("The request must provide 'exp_id' or 'title' of the sole Experiment record.")

    @staticmethod
    def create(title, short_title, comment, processing_arr, baseline, res_id, res_name, dataset_id, dataset_title, author):
        e = Experiment()
        e.set_title(title)
        e.set_short_title(short_title)
        e.set_comment(comment)
        e.set_processing(processing_arr)
        e.set_baseline(baseline)
        e.set_result_format(res_id, res_name)
        e.set_dataset(dataset_id, dataset_title)
        e.set_author(author)
        return e

    def set_title(self, title):
        if title is None:
            raise Exception("Title not provided.")
        if type(title) is not str:
            raise Exception("Title must be string.")
        p = db.session.query(Experiment).filter(Experiment.title == title).first()
        if p and (p != self):
            raise Exception("Title must be unique.")
        self.title = title

    def set_short_title(self, title):
        if title is None:
            raise Exception("Short Title not provided.")
        if type(title) is not str:
            raise Exception("Short Title must be string.")
        self.short_title = title

    def set_comment(self, comment):
        if comment is None:
            raise Exception("Comment not provided.")
        if type(comment) is not str:
            raise Exception("Comment must be string.")
        self.comment = comment

    def set_processing(self, arr):
        if arr is None:
            raise Exception("Processing IDs not provided.")
        if type(arr) != list:
            raise Exception("Processing IDs should be list of integers.")
        if len(arr) == 0:
            raise Exception("No Processing IDs provided.")
        for i in arr:
            if type(i) != int:
                raise Exception("Processing IDs should be list of integers.")
            if Processing.get(i, None) is None:
                raise Exception("Processing with id={} does not exist.".format(i))
        self.processing_ids = "-" + "-".join(str(s) for s in arr) + "-"

    def set_baseline(self, num):
        current_app.logger.info("Baseline = " + str(num))
        if num is None:
            raise Exception("Baseline not provided.")
        if type(num) != float:
            raise Exception("Baseline should be floating point number.")
        self.baseline = num

    def set_result_format(self, dataformat_id, name):
        df = None
        try:
            df = DataFormat.get(dataformat_id, name)
        except:
            raise Exception("No valid Result Format provided! "
                            "You must provide 'result_format_id' or 'result_format_name'.")
        self.result_format = df.id

    def set_dataset(self, dataset_id, name):
        ds = None
        try:
            ds = DataSet.get(dataset_id, name)
        except:
            raise Exception("No valid DataSet provided! "
                            "You must provide 'dataset_id' or 'dataset_title'.")
        self.dataset = ds.id

    def update(self, title, short_title, comment, processing_arr,
               baseline, format_id, format_name, dataset_id, dataset_title):
        if self.title != title:
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
        return DataSet.get(self.dataset, None)

    def get_processing_ids(self):
        # return [int(s) for s in self.processing_ids.split(' ')]
        return [int(s) for s in filter(lambda x: x != '', self.processing_ids.split('-'))]

    def get_processing(self):
        arr = self.get_processing_ids()
        for i in arr:
            if Processing.get(i, None) is None:
                raise Exception("Stage with id={} does not exist. "
                                "Please update ProcessingIDs of '' experiment.".format(i, self.title))
        return [Processing.get(i, None) for i in arr]

    def get_result_format(self):
        return DataFormat.get(self.result_format, None)

    def to_dict(self):
        d = super().to_dict()
        d["exp_id"] = self.id
        d["title"] = self.title
        d["short_title"] = self.short_title
        d["comment"] = self.comment
        d["baseline"] = self.baseline
        f = self.get_result_format()
        if f:
            d["result_format_name"] = f.name
        else:
            d["result_format_name"] = None
        ds = self.get_dataset()
        if ds:
            d["dataset_title"] = ds.title
        else:
            d["dataset_title"] = None
        processing = self.get_processing()
        d["processing"] = []
        for p in processing:
            d['processing'].append(p.to_dict())
        return d

    def run(self, delayed, args, user):
        from model_testing.workers import retrieve_ids, chain_status, finalize_exp, verify_input, await_previous
        from model_testing.model.exp_execution import ExpExecution
        from celery import signature

        launch_time = None

        if delayed:
            if type(delayed) == str:
                launch_time = datetime.strptime(delayed, '%Y-%m-%d %H:%M:%S.%f')
            else:
                raise Exception("The time of delayed task start should be a string in the format: "
                                "'Year-Month-Day Hour:Minute:Second (float)'")

        ds = self.get_dataset()
        procs = self.get_processing()

        if args is None:
            args = ["" for p in procs]
        if len(procs) != len(args):
            raise Exception("{} args provided for {} processing stages.".format(len(args), len(procs)))

        res_f = self.get_result_format()

        exp_exe = ExpExecution.create(self, user)

        prev_id = ExpExecution.get_last_id()
        current_app.logger.info(str(prev_id))

        db.session.add(exp_exe)
        db.session.commit()

        exe_id = exp_exe.id

        schema = res_f.schema
        format_name = res_f.format.value

        from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer)
        s = Serializer(current_app.config['SECRET_KEY'])
        tokenized_exe_id = s.dumps({ 'exe_id': exe_id }).decode('ascii')

        chain_items = [await_previous.si(prev_id)] + ds.get_chain_items(tokenized_exe_id)

        for i in range(len(procs)):
            proc = procs[i]
            arg = args[i]
            chain_items = chain_items + proc.get_chain_items(tokenized_exe_id, arg)
        chain_items = chain_items + [verify_input.si(tokenized_exe_id, schema, format_name),
                                     finalize_exp.si(tokenized_exe_id)]

        ch = chain(chain_items).apply_async(eta=launch_time, add_to_parent=True)#, acks_late = True, queue='A')

        ids = retrieve_ids(ch)
        task_names = [signature(s)['task'] for s in chain_items]

        exp_exe.set_ids(ids)
        exp_exe.set_task_names(task_names)

        db.session.commit()

        return exp_exe.to_dict()