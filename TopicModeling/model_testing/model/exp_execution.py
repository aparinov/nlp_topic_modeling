from sqlalchemy import Column, Integer, String
from sqlalchemy import Enum
from sqlalchemy import BIGINT, NVARCHAR, TIMESTAMP, ForeignKey, FLOAT, BLOB, LargeBinary

from model_testing import db
from model_testing.model.base_entity import BaseEntity
from model_testing.model.enums import ExecutionStatus
from model_testing.model.experiment import Experiment
from model_testing.workers import chain_status
from model_testing import celery


class ExpExecution(BaseEntity):
    __tablename__ = 'execution'

    exp_execution_id = Column('id', Integer, ForeignKey('base_entity.id'), primary_key=True)
    monitoring_ids = Column(String(None), default="")
    monitoring_names = Column(String(None), default="")
    status = Column(Enum(ExecutionStatus))
    experiment = Column(Integer, ForeignKey('experiment.id'))

    __mapper_args__ = {'polymorphic_identity': 'execution'}

    @staticmethod
    def create(exp, author):
        e = ExpExecution()
        status = ExecutionStatus.started
        e.set_status(status)
        e.set_experiment(exp)
        e.set_author(author)
        return e

    @staticmethod
    def get(exe_id):
        if exe_id:
            exe = db.session.query(ExpExecution).filter(ExpExecution.id == exe_id).first()
            if exe:
                return exe
        raise Exception("No such Experiment Execution.")

    def set_ids(self, arr):
        # arr must be list of ints
        if arr:
            ids = ' '.join([str(i) for i in arr])
            self.monitoring_ids = ids

    def set_task_names(self, arr):
        if arr:
            names = ' '.join([str(i) for i in arr])
            self.monitoring_names = names

    def set_status(self, status):
        self.status = status

    def set_experiment(self, exp):
        self.experiment = exp.id

    def get_experiment(self):
        return Experiment.get(self.experiment, None)

    def get_ids(self):
        return self.monitoring_ids.split(' ')

    def get_names(self):
        return self.monitoring_names.split(' ')

    def to_dict(self):
        d = super().to_dict()
        d['exe_id'] = self.id
        d['experiment'] = self.get_experiment().to_dict()
        d['status'] = self.status.value
        d["stages"] = chain_status(self.get_ids(), self.get_names())
        return d

    def cancel(self):
        for id in self.get_ids():
            celery.control.revoke(id, terminate=True, signal='SIGKILL')
        self.set_status(ExecutionStatus.canceled)