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

# define mapping scheme
# https://docs.sqlalchemy.org/en/13/dialects/mssql.html
class BaseEntity(db.Model):
    __tablename__ = 'base_entity'
    Id = Column(Integer, primary_key=True)
    Author = Column(String(None), nullable=True, default="Admin")
    TimeCreated = Column(TIMESTAMP(), default=datetime.datetime.utcnow)
    TimeLastEdited = Column(TIMESTAMP(), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    Tags = Column(String(None), nullable=True, default="")
    PreviousVersion = Column(ForeignKey('base_entity.Id'), nullable=True, default=1)

    discriminator = Column('type', String(50))
    __mapper_args__ = {'polymorphic_on': discriminator}