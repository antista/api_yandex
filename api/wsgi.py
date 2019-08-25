from flask_sqlalchemy import SQLAlchemy
from flask import Flask

from api.database_worker import DataBaseWorker

app = Flask(__name__)

db_conn = 'postgres+psycopg2://admin:12345678@localhost:5432/yandex_test'

app.config['SQLALCHEMY_DATABASE_URI'] = db_conn
db = SQLAlchemy(app)
db_worker = DataBaseWorker(db)
app.secret_key = b'yhb77sw9_"F4Q8z\n\xec]/'
from .views import *

if app['development']:
  db.drop_all()
db.create_all()
