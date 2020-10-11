from sqlalchemy import Column, Integer, String
from sqlalchemy import BIGINT, NVARCHAR, TIMESTAMP, ForeignKey, FLOAT, BLOB, LargeBinary
from model_testing.model.base_entity import BaseEntity
from model_testing.model.experiment import Experiment
from model_testing import db


class ExpResult(BaseEntity):
    # TODO: test
    __tablename__ = 'results'

    result_id = Column('id', Integer, ForeignKey('base_entity.id'), primary_key=True)

    experiment = Column(Integer, ForeignKey('experiment.id'))
    execution = Column(Integer, ForeignKey('execution.id'))

    result = Column(LargeBinary())

    __mapper_args__ = {'polymorphic_identity': 'result'}


    @staticmethod
    def create(baseline, value, experiment, result):
        r = ExpResult()
        r.set_experiment(experiment)
        r.set_result(result)
        return r

    @staticmethod
    def get(res_id):
        if res_id:
            res = db.session.query(ExpResult).filter(ExpResult.id == res_id).first()
            if res:
                return res
        raise Exception("No such Experiment Result.")

    def set_experiment(self, experiment):
        self.experiment = experiment.id

    def set_execution(self, execution):
        self.execution = execution.id

    # TODO : utf-8 для всех пользовательских данных (требования)
    def set_result(self, result):
        self.result = result.encode('utf-8')

    def to_dict(self):
        d = super().to_dict()
        d["res_id"] = self.id
        d["experiment"] = Experiment.get(self.experiment, None).to_dict()
        d["result"] = self.result.decode('utf-8')
        return d

    def to_dict_light(self):
        d = super().to_dict()
        d["res_id"] = self.id
        d["experiment"] = Experiment.get(self.experiment, None).to_dict()
        return d