from model_testing import db
from sqlalchemy import Column, Integer, String
from sqlalchemy import BIGINT, NVARCHAR, TIMESTAMP, ForeignKey, FLOAT, BLOB, LargeBinary
import datetime

# define mapping scheme
# https://docs.sqlalchemy.org/en/13/dialects/mssql.html
class BaseEntity(db.Model):
    __tablename__ = 'base_entity'
    id = Column(Integer, primary_key=True)
    author = Column(Integer, ForeignKey('users.id'))
    time_created = Column(TIMESTAMP(), default=datetime.datetime.utcnow)
    time_last_edited = Column(TIMESTAMP(), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    # tags = Column(String(None), nullable=True, default="")
    # PreviousVersion = Column(ForeignKey('base_entity.id'), nullable=True, default=1)
    discriminator = Column('type', String(50))
    __mapper_args__ = {'polymorphic_on': discriminator}

    @staticmethod
    def delete(entity):
        if entity is None:
            return None
        entity = db.session.query(BaseEntity).filter(BaseEntity.id==entity.id).first()
        if not entity:
            return None

        res = { "id": entity.id, "type" : entity.discriminator }
        dependent = []

        from model_testing.model.experiment import Experiment
        from model_testing.model.processing import Processing
        from model_testing.model.data_set import DataSet
        from  model_testing.model.exp_result import ExpResult
        from  model_testing.model.exp_execution import ExpExecution

        if entity.discriminator == "dataset":
            d = db.session.query(Experiment).filter(Experiment.dataset == entity.id).all()
            dependent = dependent + (d if d else [])
        elif entity.discriminator == "format":
            # Dataset
            d = db.session.query(DataSet).filter(DataSet.data_format == entity.id).all()
            dependent = dependent + (d if d else [])

            # Processing - input
            d = db.session.query(Processing).filter(Processing.input == entity.id).all()
            dependent = dependent + (d if d else [])

            # Processing - output
            d = db.session.query(Processing).filter(Processing.output == entity.id).all()
            dependent = dependent + (d if d else [])

            # Experiment
            d = db.session.query(Experiment).filter(Experiment.result_format == entity.id).all()
            dependent = dependent + (d if d else [])
        elif entity.discriminator == "processing":
            # Experiment
            # TODO: Test this trick. Check if ilike pattern don't pick processings with substrings in index.
            d = db.session.query(Experiment).filter(
                # lambda exp: entity.id in exp.processing_ids.split(' ')
                # entity.id in Experiment.processing_ids.split(' ')
                Experiment.processing_ids.ilike("%-{0}-%".format(entity.id))
            ).all()
            dependent = dependent + (d if d else [])
        elif entity.discriminator == "environment":
            # Processing
            d = db.session.query(Processing).filter(Processing.environment == entity.id).all()
            dependent = dependent + (d if d else [])
        elif entity.discriminator == "execution":
            # ExpResult
            d = db.session.query(ExpResult).filter(ExpResult.execution == entity.id).all()
            dependent = dependent + (d if d else [])
        elif entity.discriminator == "result":
            pass
        elif entity.discriminator == "experiment":
            # ExpResult
            d = db.session.query(ExpResult).filter(ExpResult.experiment == entity.id).all()
            dependent = dependent + (d if d else [])

            # ExpExecution
            d = db.session.query(ExpExecution).filter(ExpExecution.experiment == entity.id).all()
            dependent = dependent + (d if d else [])

        if len(dependent) != 0:
            res["dependent"] = []

            for dep in dependent:
                dep_res = BaseEntity.delete(dep)
                if dep_res:
                    res["dependent"].append(dep_res)

        db.session.delete(entity)
        db.session.commit()
        return res

    def set_author(self, author):
        self.author = author.id

    def get_author(self):
        from model_testing.model.user import User
        return db.session.query(User).filter(User.id == self.author).first()

    def to_dict(self):
        author = self.get_author()
        return {
            "created_at": str(self.time_created),
            "last_modified_at": str(self.time_last_edited),
            "author_username" : author.username,
            "author_id" : author.id
        }
