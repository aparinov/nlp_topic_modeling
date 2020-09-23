
from base64 import b64encode
from os import urandom

# random_bytes = urandom(64)
# token = b64encode(random_bytes).decode('utf-8')

class Config():
    SECRET_KEY = '7f4LFiIUGpOWIWaMcF8dBxs88ba4vGBzVyg2fJLawc7i++fiBCpqc9KRNnaf2Zf176Ro5TPDRKSSR+Jx+6taRQ=='
    #SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    #SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:1@localhost:5432/topicmodeling'
