from model_testing import db
import urllib.request

from sqlalchemy import Column, Integer, String
from sqlalchemy import Enum
from sqlalchemy import BIGINT, NVARCHAR, TIMESTAMP, ForeignKey, FLOAT, BLOB, LargeBinary

from model_testing.model.base_entity import BaseEntity
from model_testing.model.enums import DataFormats


class DataFormat(BaseEntity):
    __tablename__ = 'formats'

    dataformat_id = Column('id', BIGINT, ForeignKey('base_entity.id'), primary_key=True)
    format = Column(Enum(DataFormats))
    schema = Column(String(None))
    name = Column(String(None), default="")

    __mapper_args__ = {'polymorphic_identity': 'format'}

    @staticmethod
    def create(name, format_name, uri, author):
        df = DataFormat()
        df.set_name(name)
        df.set_format(format_name)
        df.set_schema(uri)
        df.set_author(author)
        return df

    @staticmethod
    def get(dataformat_id, name):
        err = "The request must provide 'dataformat_id' or 'name' of the sole Data Format record."
        df = []
        if name:
            df.append(db.session.query(DataFormat).filter(DataFormat.name == name).first())
        if dataformat_id:
            df.append(db.session.query(DataFormat).filter(DataFormat.id == dataformat_id).first())
        df = list(filter(lambda x: x is not None, df))
        if len(df) == 0:
            raise Exception("No such Data Format.")
        elif len(df) == 1:
            return df[0]
        else:
            if df[0] == df[1]:
                return df[0]
            else:
                raise Exception(err)

    def set_name(self, name):
        if name is None:
            raise Exception("Name not provided.")
        if type(name) is not str:
            raise Exception("Name must be string.")
        df = db.session.query(DataFormat).filter(DataFormat.name == name).first()
        if df and (df != self):
            raise Exception("Name must be unique.")
        self.name = name

    def set_format(self, format_name):
        if format_name is None:
            raise Exception("Format not provided.")
        if type(format_name) is not str:
            raise Exception("Format must be string.")
        allowed = [x.value for x in DataFormats]
        if not format_name in allowed:
            raise Exception("Format not supported. Formats available: {}".format(allowed))
        self.format = DataFormats[format_name]

    def set_schema(self, schema_uri):
        if type(schema_uri) == str:
            req = urllib.request.Request(url=schema_uri)
            with urllib.request.urlopen(req) as f:
                self.schema = f.read().decode('utf-8')
        else:
            raise Exception("Schema URI must be string.")

    def update(self, name, format_name, schema_uri):
        if (self.name != name) and (name):
            self.set_name(name)
        if (str(self.format) != format_name) and (format_name):
            self.set_format(format_name)
        if (schema_uri):
            self.set_schema(schema_uri)

    def to_dict(self):
        d = super().to_dict()
        d["dataformat_id"] = self.id
        d["name"] = self.name
        d["schema"] = self.schema
        d["format"] = self.format.value
        return d