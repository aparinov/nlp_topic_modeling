from model_testing import db
from sqlalchemy import Column, Integer, String
from sqlalchemy import BIGINT, NVARCHAR, TIMESTAMP, ForeignKey, FLOAT, BLOB, LargeBinary
import datetime
from model_testing.model.user import User

# define mapping scheme
# https://docs.sqlalchemy.org/en/13/dialects/mssql.html
class BaseEntity(db.Model):
    __tablename__ = 'base_entity'
    id = Column(Integer, primary_key=True)
    author = Column(Integer, ForeignKey('users.id'))
    time_created = Column(TIMESTAMP(), default=datetime.datetime.utcnow)
    time_last_edited = Column(TIMESTAMP(), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    tags = Column(String(None), nullable=True, default="")
    # PreviousVersion = Column(ForeignKey('base_entity.id'), nullable=True, default=1)

    def set_author(self, author):
        self.author = author.id

    def get_author(self):
        return db.session.query(User).filter(User.id == self.author).first()

    def to_dict(self):
        author = self.get_author()
        return {
            "created_at": str(self.time_created),
            "last_modified_at": str(self.time_last_edited),
            "author_username" : author.username,
            "author_id" : author.id
        }

    discriminator = Column('type', String(50))
    __mapper_args__ = {'polymorphic_on': discriminator}