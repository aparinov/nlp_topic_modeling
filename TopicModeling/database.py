from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Enum
from sqlalchemy import BIGINT, NVARCHAR, TIMESTAMP, ForeignKey, FLOAT, BLOB
from sqlalchemy.orm import sessionmaker

import datetime
from schemas import tm_dataset_schema, tm_dataset_xsd
from urllib.parse import urlparse
import urllib.request
from schemas import validate_json, validate_xml


# Connecting
connection_string = 'sqlite:///:memory:'
engine = create_engine(connection_string)#, echo=True)

# define declarative base class
Base = declarative_base()

# Scheme definition
# Define all enum
import enum

class DataFormats(enum.Enum):
    json = 'json'
    xml = 'xml'
    plain = 'plain text'
    binary = 'binary'
    db = 'database'

class OSs(enum.Enum):
    win = 'Win'
    linux = 'Linux'
    mac = 'MacOS'


class ImplStatus(enum.Enum):
    deprecated = 'Deprecated'
    incorrect = 'Incorrect'
    correct = 'Correct'
    has_new = 'HasNewVersion'


# define mapping scheme
# https://docs.sqlalchemy.org/en/13/dialects/mssql.html

# TODO: разобраться с nullable и default
class BaseEntity(Base):
    __tablename__ = 'base_entity'
    Id = Column(Integer, primary_key=True)
    Author = Column(NVARCHAR(None), nullable=True, default="Admin")
    TimeCreated = Column(TIMESTAMP(), default=datetime.datetime.utcnow)
    TimeLastEdited = Column(TIMESTAMP(), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    Tags = Column(NVARCHAR(None), nullable=True, default="")
    PreviousVersion = Column(ForeignKey('base_entity.Id'), nullable=True, default=1)

    discriminator = Column('type', String(50))
    __mapper_args__ = {'polymorphic_on': discriminator}


class Task(BaseEntity):
    __tablename__ = 'tasks'
    TaskId = Column('Id', BIGINT, ForeignKey('base_entity.Id'), primary_key=True)
    Title = Column(NVARCHAR(None))
    SuperTask = Column(NVARCHAR(None))
    Input = Column(BIGINT)
    DefaultInputFormat = Column(NVARCHAR(None))
    Output = Column(BIGINT)
    DefaultOutputFormat = Column(NVARCHAR(None))
    # TaskSettingsId = Column()
    # ExperimentId = Column()

    __mapper_args__ = {'polymorphic_identity': 'task'}


class Experiment(BaseEntity):
    __tablename__ = 'experiments'
    ExperimentId = Column('Id', BIGINT, ForeignKey('base_entity.Id'), primary_key=True)
    TitleShort = Column(NVARCHAR(None))
    Title = Column(NVARCHAR(None))
    Comment = Column(NVARCHAR(None)) # HTMLString
    # DataSets =
    BaseLine = Column(FLOAT())
    # RefRes = Column()
    # ExperimentEnviroment = Column()
    __mapper_args__ = {'polymorphic_identity': 'experiment'}


# заменено на enum
class DataFormat(BaseEntity):
    __tablename__ = 'formats'

    FormatId = Column('Id', BIGINT, ForeignKey('base_entity.Id'), primary_key=True)
    format = Column(Enum(DataFormats))
    schema = Column(NVARCHAR(None))
    name = Column(NVARCHAR(None), default="")

    __mapper_args__ = {'polymorphic_identity': 'format'}


class DataSet(BaseEntity):
    __tablename__ = 'datasets'

    DataSetId = Column(Integer, ForeignKey('base_entity.Id'), primary_key=True)
    DataFormat = Column(Integer, ForeignKey('formats.Id'))
    Data = Column(BLOB())
    Title = Column(NVARCHAR(None), default="")

    __mapper_args__ = {'polymorphic_identity': 'dataset'}


# class DataConverter(BaseEntity):
#     __tablename__ = 'converters'
#
#     DataConverterID = Column('Id', BIGINT, ForeignKey('base_entity.Id'), primary_key=True)
#     InputFormat = Column(DataFormats())
#     OutputFormat = Column(DataFormats())
#     # InputFormat = Column(Integer, ForeignKey('formats.Id'))
#     # OutputFormat = Column(Integer, ForeignKey('formats.Id'))
#
#     __mapper_args__ = {'polymorphic_identity': 'converter'}


class ExperimentEnviroment(BaseEntity):
    __tablename__ = 'environments'

    ExperimentEnviromentID = Column('Id', BIGINT, ForeignKey('base_entity.Id'), primary_key=True)

    __mapper_args__ = {'polymorphic_identity': 'environment'}


class ExpResult(BaseEntity):
    __tablename__ = 'results'

    ExpResultID = Column('Id', BIGINT, ForeignKey('base_entity.Id'), primary_key=True)

    ProgImplID = Column(ForeignKey('programs.Id'))  #- ? [exe file, REST interface]
    ExperimentID = Column(ForeignKey('experiments.Id'))
    EnviromentID = Column(ForeignKey('environments.Id'))
    Values = Column(NVARCHAR(None))         #(ResultDataset)
    StartTime = Column(TIMESTAMP())         # - начало прогона.
    StopTime = Column(TIMESTAMP())          # - конец прогона.
    Log = Column(NVARCHAR(None))            #- журнал работы программы.
    UserComments = Column(NVARCHAR(None))   #- пользовательские комментарии

    __mapper_args__ = {'polymorphic_identity': 'result'}


# ProgramImplementation - конкретная реализация алгоритма (программа), загруженная в систему
class ProgramImplementation(BaseEntity):
    __tablename__ = 'programs'

    ProgImplID = Column('Id', BIGINT, ForeignKey('base_entity.Id'), primary_key=True)

    Status = Column(Enum(ImplStatus))                   #(Set of enum[Deprecated, Incorrect, HasNewVersion, ..]) - статус.
    Os = Column(Enum(OSs))                              #(Enum[Win, Linux, MacOS]) - операционная система.
    EnvID = Column(ForeignKey('environments.Id'))   # - требования к окружению.
    TaskID = Column(ForeignKey('tasks.Id'))         #- решаемая задача.
    InputFormat = Column(Enum(DataFormats))             # - формат ввода.
    OutputFormat = Column(Enum(DataFormats))            #- формат вывода.
    # InputFormat = Column(ForeignKey('formats.Id'))  # - формат ввода.
    # OutputFormat = Column(ForeignKey('formats.Id')) #- формат вывода.
    CommandLineArgs = Column(NVARCHAR(None))        #(String) - аргументы командной строки.
    Blob = Column(BLOB())                           #- архив для развёртывания.

    __mapper_args__ = {'polymorphic_identity': 'program'}


# TaskSettings - настройки эксперимент
class TaskSettings(BaseEntity):
    __tablename__ = 'task_settings'

    TaskID = Column('Id', BIGINT, ForeignKey('base_entity.Id'), primary_key=True)
    # OutputFormat = Column(ForeignKey("formats.Id"))#– [ необходимо ли сохранять файл или в виде таблицы]
    OutputFormat = Column(Enum(DataFormats))    #– [ необходимо ли сохранять файл или в виде таблицы]
    Subquery = Column(NVARCHAR(None))       #- Текст подзапроса

    __mapper_args__ = {'polymorphic_identity': 'task_setting'}


# creates foreign key constraints between tables
Base.metadata.create_all(engine)

# starting session
Session = sessionmaker(bind=engine)
session = Session()

tm_ds_json_format_name = "Topic Modeling dataset in JSON"
tm_ds_xml_format_name = "Topic Modeling dataset in XML"


def create_dataformat(name, format_name, uri, session):
    format = DataFormats[format_name]

    req = urllib.request.Request(url=uri)
    with urllib.request.urlopen(req) as f:
        schema = f.read()

    df = DataFormat(format=format, schema=schema, name=name)
    session.add(df)
    session.commit()


def create_dataset(uri, format_name, session):
    format = session.query(DataFormat).filter(DataFormat.name == format_name).first()
    if not format:
        raise Exception("No such format provided!")

    id = format.Id
    title = uri.split("/")[-1]
    req = urllib.request.Request(url=uri)
    with urllib.request.urlopen(req) as f:
        data = f.read()

    schema = format.schema
    instance = data.decode("utf-8")
    validation = True
    if (format.format == DataFormats.json):
        validation = validate_json(schema, instance)
    elif (format.format == DataFormats.xml):
        validation = validate_xml(schema, instance)

    if (validation is not True):
        raise Exception('File "{}" does not match "{}" format: {}'.format(title, format_name, validation))


    ds = DataSet(DataFormat=id, Title=title, Data=data)
    session.add(ds)
    session.commit()


uri_json = "file:///Users/user/Desktop/nlp_topic_modeling/TopicModeling/data/20news-18828.json"
uri_xml = "file:///Users/user/Desktop/nlp_topic_modeling/TopicModeling/data/20news-18828.xml"

# Entity creation test
# create_dataformat(tm_ds_json_format_name, 'json', tm_dataset_schema, session)
# create_dataformat(tm_ds_xml_format_name, 'xml', tm_dataset_xsd, session)
#
# create_dataset(uri_json, tm_ds_json_format_name, session)
# create_dataset(uri_xml, tm_ds_xml_format_name, session)
# for (file, format) in [(uri_json, tm_ds_xml_format_name), (uri_xml, tm_ds_json_format_name)]:
#     try:
#         create_dataset(file, format, session)
#     except Exception as e:
#         print(e.args)

for format in session.query(DataFormat):
    print(format.name, end="\n\n")

for dataset in session.query(DataSet):
    print(dataset.Title)
    print(dataset.Data.decode("utf-8")[:100],end="\n\n")



# def get_data(dataset):
#     print(dataset.Title)
#     print(dataset.DataFormat)
#     print(dataset.FormatContent)
#
#     if (len(dataset.FormatContent) < 4):
#         raise Exception("No data provided. Database record is incorrect.")
#
#     if ((dataset.FormatContent[:4] == "file") and (dataset.DataFormat == DataFormats.plain)):
#
#         print(dataset.FormatContent[:4])
#         uri = dataset.FormatContent
#
#         from urllib.parse import urlparse
#         o = urlparse(uri)
#         # print(o)
#         # print(o.path.split("/")[-1])
#
#         import urllib.request
#         req = urllib.request.Request(url=uri)
# #
#         with urllib.request.urlopen(req) as f:
#             path = o.path.split("/")[-1]#'20news-18828.tar.gz'
#             open(path, 'wb').write(f.read())
#             from os import remove
#             import tarfile
#
#             file = tarfile.open(path)
#             filepath = file.getnames()[0].split("/")[0]
#             print(filepath)
#             data = file.extractall(path="./" + filepath)
#
#             from pathlib import Path
#             def rmdir(directory):
#                 directory = Path(directory)
#                 for item in directory.iterdir():
#                     if item.is_dir():
#                         rmdir(item)
#                     else:
#                         item.unlink()
#                 directory.rmdir()
#
#             rmdir(Path(filepath))
#             # remove(filepath)
#             remove(path)
#         print(type(data))
#         print(data)
#
#         # from urllib.request import urlopen
#         # urlpath =urlopen(uri)
#         # string = urlpath.read().decode('utf-8')
#         # print(string)
#
#         # import requests
#         # r = requests.get(uri, allow_redirects=True)
#         # open('smaple.txt', 'wb').write(r.content)
#
# get_data(res)

from . import db

from passlib.apps import custom_app_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from flask import current_app

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    username = db.Column(db.String(32), index = True)
    password_hash = db.Column(db.String(128))
    admin_rights = db.Column(db.Boolean, default=False)
    exp_admin_rights = db.Column(db.Boolean, default=False)

    def generate_auth_token(self, expiration = 600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in = expiration)
        return s.dumps({ 'id': self.id })

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        user = User.query.get(data['id'])
        return user

    def hash_password(self, password):
        self.password_hash = custom_app_context.encrypt(password)

    def verify_password(self, password):
        return custom_app_context.verify(password, self.password_hash)