from sqlalchemy import Column, Integer, String
from sqlalchemy import Enum
from sqlalchemy import BIGINT, NVARCHAR, TIMESTAMP, ForeignKey, FLOAT, BLOB, LargeBinary

import urllib.request
import os
import subprocess

from model_testing import db
from model_testing.model.base_entity import BaseEntity
from model_testing.model.data_format import DataFormat
from model_testing.model.enums import Langs, ProgramStatus
from base64 import b64decode, b64encode
from model_testing.workers import run, verify_input, verify_output, transfer_output_to_input
from model_testing.model.environment import Environment


class Processing(BaseEntity):
    # TODO: test
    __tablename__ = 'processing'

    processing_id = Column('id', Integer, ForeignKey('base_entity.id'), primary_key=True)
    name = Column(String(None), default="")

    input = Column(Integer, ForeignKey('formats.id'))
    output = Column(Integer, ForeignKey('formats.id'))

    environment = Column(Integer, ForeignKey('environment.id'))

    source = Column(LargeBinary())
    lang = Column(Enum(Langs))
    status = Column(Enum(ProgramStatus))

    args_info = Column(String(None), default="")

    @staticmethod
    def get(id, name):
        p = []
        if name:
            p.append(db.session.query(Processing).filter(Processing.name == name).first())
        if id:
            p.append(db.session.query(Processing).filter(Processing.id == id).first())

        p = list(filter(lambda x: x is not None, p))

        if len(p) == 0:
            raise Exception("No such Processing stage.")
        elif len(p) == 1:
            return p[0]
        else:
            if p[0] == p[1]:
                return p[0]
            else:
                raise Exception("The request must provide 'processing_id' or 'name'"
                                " of the sole Processing stage record.")

    @staticmethod
    def create(name, input_id, input_name, output_id, output_name, source_uri,
               lang_name, env_id, env_name, status_name, author):
        p = Processing()
        p.set_name(name)
        p.set_input(input_id, input_name)
        p.set_output(output_id, output_name)
        p.set_environment(env_id, env_name)
        p.set_lang(lang_name)
        p.set_source(source_uri)
        p.set_status(status_name)
        p.set_author(author)
        return p

    def set_name(self, name):
        if name is None:
            raise Exception("Name not provided.")
        if type(name) is not str:
            raise Exception("Name must be string.")
        p = db.session.query(Processing).filter(Processing.name == name).first()
        if p and (p != self):
            raise Exception("Name must be unique.")
        self.name = name

    def set_input(self, format_id, format_name):
        df = DataFormat.get(format_id, format_name)
        self.input = df.id

    def set_output(self, format_id, format_name):
        df = DataFormat.get(format_id, format_name)
        self.output = df.id

    def set_environment(self, env_id, env_name):
        env = Environment.get(env_id, env_name)
        self.environment = env.id

    def set_source(self, source_uri):
        if type(source_uri) == str:
            req = urllib.request.Request(url=source_uri)
            with urllib.request.urlopen(req) as f:
                self.source = f.read()
            self.set_args_info()
        else:
            raise Exception("Source URI must be string.")

    def set_lang(self, lang_name):
        if lang_name is None:
            raise Exception("Language not provided.")
        if type(lang_name) is not str:
            raise Exception("Language must be provided with string.")
        allowed = [x.value for x in Langs]
        if not lang_name in allowed:
            raise Exception("Language not supported. Languages available: {}".format(allowed))
        self.lang = Langs[lang_name]

    def set_status(self, status_name):
        if status_name is None:
            raise Exception("Program Status not provided.")
        if type(status_name) is not str:
            raise Exception("Program Status must be provided with string.")
        allowed = [x.value for x in ProgramStatus]
        if not status_name in allowed:
            raise Exception("Program Status not supported. Program Statuses available: {}".format(allowed))
        self.status = ProgramStatus[status_name]

    def set_args_info(self):
        base_path = os.getcwd() + '/data/stage/'
        path = base_path + 'script.py'

        if os.path.isfile(path):
            os.remove(path)

        with open(path, 'wb') as file:
            file.write(self.source)
        os.chmod(path, 0b111101101)

        if self.lang == Langs.python:
            command = ['python3', path, '--help']
        else:
            command = [path, '--help']

        process = subprocess.Popen(command, stdout=subprocess.PIPE)
        out, err = process.communicate()

        if os.path.isfile(path):
            os.remove(path)

        if err:
            raise Exception("Provided code throw error when trying to get '--help' through the command line.")
        if not out:
            raise Exception("Provided code gives no information when trying to get '--help' through the command line.")

        self.args_info = out.decode('utf-8')


    def get_input(self):
        return db.session.query(DataFormat).filter(DataFormat.id == self.input).first()

    def get_output(self):
        return db.session.query(DataFormat).filter(DataFormat.id == self.output).first()

    def get_environment(self):
        return db.session.query(Environment).filter(Environment.id == self.environment).first()

    def update(self, name, input_id, input_name, output_id, output_name,
               source_uri, lang_name, env_id, env_name, status_name):
        if (self.name != name) and name:
            self.set_name(name)
        if input_id or input_name:
            self.set_input(input_id, input_name)
        if output_id or output_name:
            self.set_output(output_id, output_name)
        if env_id or env_name:
            self.set_environment(env_id, env_name)
        if lang_name:
            self.set_lang(lang_name)
        if status_name:
            self.set_status(status_name)
        if source_uri:
            self.set_source(source_uri)

    def to_dict(self):
        d = super().to_dict()
        d["processing_id"] = self.id
        d["name"] = self.name
        d["lang_name"] = self.lang.value
        d["status"] = self.status.value
        d["input_name"] = self.get_output().name
        d["output_name"] = self.get_input().name
        d["args_info"] = self.args_info
        d["environment"] = self.get_environment().name
        return d

    def get_chain_items(self, exe_id, args):
        inp = self.get_input()
        out = self.get_output()

        inp_schema = inp.schema
        inp_format = inp.format.value

        out_schema = out.schema
        out_format = out.format.value

        env = self.get_environment()

        return [
            verify_input.si(exe_id, inp_schema, inp_format),
            run.si(exe_id=exe_id,
                   code=b64encode(self.source).decode('utf-8'),
                   lang_name=self.lang.value,
                   py_dependencies=env.py_dependencies,
                   args=args),
            verify_output.si(exe_id, out_schema, out_format),
            transfer_output_to_input.si(exe_id)
        ]

    __mapper_args__ = {'polymorphic_identity': 'processing'}