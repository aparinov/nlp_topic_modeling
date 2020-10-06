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
from model_testing.model.enums import Langs
from base64 import b64decode, b64encode
from model_testing.workers import run, verify_input, verify_output, transfer_output_to_input, clean, prepare_input


import psutil
import subprocess
import sys
import tensorflow as tf


class Environment(BaseEntity):
    # TODO: test
    __tablename__ = 'environment'

    EnvironmentId = Column("Id", Integer, ForeignKey('base_entity.Id'), primary_key=True)
    name = Column(String(None), default="")
    py_dependencies = Column(String(None), default="")
    cuda_version = Column(String(None), default="")
    gpu_required = Column(db.Boolean, default=False)

    @staticmethod
    def get(id, name):
        p = []
        if name:
            p.append(db.session.query(Environment).filter(Environment.name == name).first())
        elif id:
            p.append(db.session.query(Environment).filter(Environment.Id == id).first())

        if len(p) == 0:
            raise Exception("No such Environment.")
        elif len(p) == 1:
            return p[0]
        else:
            if (p[0] == p[1]):
                return p[1]
            else:
                raise Exception("The request must provide 'id' or 'name' of the sole Environment record.")

    @staticmethod
    def create(name, cuda_version, gpu_required, py_dependencies, author):
        env = Environment()
        env.set_name(name)
        env.set_cuda_version(cuda_version)
        env.set_gpu_required(gpu_required)
        env.set_py_dependencies(py_dependencies)
        env.set_author(author)
        return env

    def set_name(self, name):
        if not name:
            raise Exception("Name not provided.")
        if type(name) is not str:
            raise Exception("Name must be string.")
        p = db.session.query(Environment).filter(Environment.name == name).first()
        if p and (p != self):
            raise Exception("Name must be unique.")
        self.name = name

    def set_cuda_version(self, cuda_version):
        if not cuda_version:
            raise Exception("'cuda_version' not provided.")
        if type(cuda_version) is not str:
            raise Exception("'cuda_version' must be string.")
        self.cuda_version = cuda_version

    def set_py_dependencies(self, py_dependencies):
        if not py_dependencies:
            raise Exception("'py_dependencies' not provided.")
        if type(py_dependencies) is not str:
            raise Exception("'py_dependencies' must be string.")
        self.py_dependencies = py_dependencies

    def set_gpu_required(self, gpu_required):
        if gpu_required is None:
            raise Exception("No 'gpu_required' flag provided provided.")
        if type(gpu_required) != bool:
            raise Exception("'gpu_required' flag must be boolean.")
        self.gpu_required = gpu_required

    def update(self, name, cuda_version, gpu_required, py_dependencies):
        if (self.name != name) and name:
            self.set_name(name)
        if cuda_version is not None:
            self.set_cuda_version(cuda_version)
        if gpu_required is not None:
            self.set_gpu_required(gpu_required)
        if py_dependencies is not None:
            self.set_py_dependencies(py_dependencies)

    def to_dict(self):
        author = self.get_author()
        return {
            "id": self.Id,
            "name": self.name,
            "cuda_version": self.cuda_version,
            "gpu_required": self.gpu_required,
            "py_dependencies": self.py_dependencies,
            "author_username" : author.username,
            "author_id" : author.id
        }

    __mapper_args__ = {'polymorphic_identity': 'environment'}




def get_free_ram():
    vm = psutil.virtual_memory()
    return (vm.total*(1. - vm.percent/100)) / (2**30)


# TODO: nvidia-smi to requirements
def get_free_vram():
    try:
        COMMAND = "nvidia-smi --query-gpu=memory.free --format=csv"
        output_to_list = lambda x: x.decode('ascii').split('\n')[:-1]
        memory_free_info = output_to_list(subprocess.check_output(COMMAND.split()))[1:]
        memory_free_values = [int(x.split()[0]) for i, x in enumerate(memory_free_info)]
        return memory_free_values
    except:
        return None


# TODO: nvcc to requirements
def get_cuda_version():
    try:
        COMMAND = "nvcc --version"
        version = subprocess.check_output(COMMAND.split()).decode('ascii').split(',')[1]
        return version
    except:
        return None


def get_packages():
    process = subprocess.Popen([sys.executable, "-m", "pip", "freeze"], stdout=subprocess.PIPE)
    stdout = process.communicate()[0]
    names_versions = stdout.decode('ascii').split("\n")
    names_versions = list(map(lambda x: [x.split('==')[0], x.split('==')[1]] if ('==' in x) else None, names_versions))
    res = []
    for nv in names_versions:
        if nv:
            res.append(nv)
    return dict(res)


def get_gpus():
    return tf.config.experimental.list_physical_devices('GPU')