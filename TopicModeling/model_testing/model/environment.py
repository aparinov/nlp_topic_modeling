from model_testing import db

import platform
import psutil
import subprocess
import sys
import tensorflow as tf

from sqlalchemy import Column, Integer, String
from sqlalchemy import BIGINT, NVARCHAR, TIMESTAMP, ForeignKey, FLOAT, BLOB, LargeBinary
from model_testing.model.base_entity import BaseEntity


class Environment(BaseEntity):
    # TODO: test
    __tablename__ = 'environment'

    environment_id = Column("id", Integer, ForeignKey('base_entity.id'), primary_key=True)
    name = Column(String(None), default="")
    py_dependencies = Column(String(None), default="")
    cuda_version = Column(String(None), default="")
    architecture = Column(String(None), default="")
    gpu_required = Column(db.Boolean, default=False)

    @staticmethod
    def get(env_id, name):
        env = []
        if name:
            env.append(db.session.query(Environment).filter(Environment.name == name).first())
        if env_id:
            env.append(db.session.query(Environment).filter(Environment.id == env_id).first())

        env = list(filter(lambda x: x is not None, env))

        if len(env) == 0:
            raise Exception("No such Environment.")
        elif len(env) == 1:
            return env[0]
        else:
            if env[0] == env[1]:
                return env[0]
            else:
                raise Exception("The request must provide 'env_id' or 'name' of the sole Environment record.")

    @staticmethod
    def create(name, cuda_version, gpu_required, py_dependencies, architecture, author):
        env = Environment()
        env.set_name(name)
        env.set_cuda_version(cuda_version)
        env.set_gpu_required(gpu_required)
        env.set_py_dependencies(py_dependencies)
        env.set_author(author)
        env.set_architecture(architecture)
        return env

    def set_name(self, name):
        if name is None:
            raise Exception("Name not provided.")
        if type(name) is not str:
            raise Exception("Name must be string.")
        p = db.session.query(Environment).filter(Environment.name == name).first()
        if p and (p != self):
            raise Exception("Name must be unique.")
        self.name = name

    def set_architecture(self, architecture):
        if architecture is None:
            raise Exception("'architecture' not provided.")
        if type(architecture) is not str:
            raise Exception("'architecture' must be string.")
        self.architecture = architecture

    def set_cuda_version(self, cuda_version):
        if cuda_version is None:
            raise Exception("'cuda_version' not provided.")
        if type(cuda_version) is not str:
            raise Exception("'cuda_version' must be string.")
        self.cuda_version = cuda_version

    def set_py_dependencies(self, py_dependencies):
        if py_dependencies is None:
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

    def update(self, name, cuda_version, gpu_required, py_dependencies, architecture):
        if (self.name != name) and name:
            self.set_name(name)
        if cuda_version is not None:
            self.set_cuda_version(cuda_version)
        if gpu_required is not None:
            self.set_gpu_required(gpu_required)
        if py_dependencies is not None:
            self.set_py_dependencies(py_dependencies)
        if architecture is not None:
            self.set_architecture(architecture)

    def to_dict(self):
        d = super().to_dict()
        d["env_id"] = self.id
        d["name"] = self.name
        d["cuda_version"] = self.cuda_version
        d["gpu_required"] = self.gpu_required
        d["py_dependencies"] = self.py_dependencies
        d["architecture"] = self.architecture
        return d

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


def get_architecture():
    return platform.processor()