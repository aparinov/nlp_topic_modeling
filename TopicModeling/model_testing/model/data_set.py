import urllib.request

from sqlalchemy import Column, Integer, String
from sqlalchemy import BIGINT, NVARCHAR, TIMESTAMP, ForeignKey, FLOAT, BLOB, LargeBinary

from model_testing.schemas import validate_json, validate_xml
from model_testing import db
from model_testing.workers import clean, prepare_input
from model_testing.model.base_entity import BaseEntity
from model_testing.model.data_format import DataFormat
from model_testing.model.enums import DataFormats


class DataSet(BaseEntity):
    __tablename__ = 'datasets'

    dataset_id = Column('id', Integer, ForeignKey('base_entity.id'), primary_key=True)
    data_format = Column(Integer, ForeignKey('formats.id'))
    data = Column(LargeBinary())
    title = Column(String(None), default="")

    __mapper_args__ = {'polymorphic_identity': 'dataset'}

    @staticmethod
    def create(title, uri, format_id, format_name, author):
        ds = DataSet()
        ds.set_title(title)
        ds.set_data_format(format_id, format_name)
        ds.set_data(uri)
        ds.validate()
        ds.set_author(author)
        return ds

    @staticmethod
    def get(dataset_id, title):
        # TODO: test
        ds = []
        if title:
            ds.append(db.session.query(DataSet).filter(DataSet.title == title).first())
        if dataset_id:
            ds.append(db.session.query(DataSet).filter(DataSet.id == dataset_id).first())

        ds = list(filter(lambda x: x is not None, ds))

        if len(ds) == 0:
            raise Exception("No such Data Set.")
        elif len(ds) == 1:
            return ds[0]
        else:
            if ds[0] == ds[1]:
                return ds[0]
            else:
                raise Exception("The request must provide 'dataset_id' or 'title' of the sole Data Set record.")

    def set_data_format(self, dataformat_id, name):
        df = DataFormat.get(dataformat_id, name)
        self.data_format = df.id

    def set_data(self, uri):
        if uri is None:
            raise Exception("URI not provided.")
        if type(uri) is not str:
            raise Exception("URI must be string.")
        try:
            req = urllib.request.Request(url=uri)
            with urllib.request.urlopen(req) as f:
                data = f.read()
            self.data = data
        except Exception as e:
            raise Exception("Can't read file: {}".format(uri))

    def set_title(self, title):
        if title is None:
            raise Exception("Title not provided.")
        if type(title) is not str:
            raise Exception("Title must be string.")
        ds = db.session.query(DataSet).filter(DataSet.title == title).first()
        if ds and (ds != self):
            raise Exception("Title must be unique.")
        self.title = title

    def validate(self):
        if self.title is None:
            raise Exception("Title not provided.")
        if self.data_format is None:
            raise Exception("Data Format not provided.")
        if self.data is None:
            raise Exception("Data not provided.")

        df = DataFormat.get(self.DataFormat, None)
        if df is None:
            raise DataFormat("Data Format not available.")

        instance = self.Data.decode("utf-8")
        format = df.format
        format_name = df.name
        schema = df.schema
        title = self.title

        validation = True
        if format == DataFormats.json:
            validation = validate_json(schema, instance)
        elif format == DataFormats.xml:
            validation = validate_xml(schema, instance)

        if validation is not True:
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
        d = super().to_dict()
        d["data"] = self.Data.decode("utf-8")
        d["dataset_id"] = self.id
        d["title"] = self.title
        d["format_name"] = df.name
        d["format_id"] = df.id
        return d

    def to_dict_light(self):
        df = DataFormat.get(self.DataFormat, None)
        d = super().to_dict()
        d["dataset_id"] = self.id
        d["title"] = self.title
        d["format_name"] = df.name
        d["format_id"] = df.id
        return d

    def get_chain_items(self, exe_id):
        data = self.Data.decode('utf-8')
        return [clean.si(exe_id), prepare_input.si(exe_id, data)]