from datetime import date

import pytest

from api import wsgi
from api.models import Citizen, Import


@pytest.fixture
def app():
    return wsgi.app


@pytest.fixture
def citizen():
    return Citizen(import_id=1, citizen_id=1, town="Москва", street="Ленина", building='16к7стр5', apartment=7,
                   name="Иванов Иван Иванович", birth_date=date(1986, 12, 26), gender='male')


@pytest.fixture
def correct_citizen_data():
    return {"citizen_id": 1,
            "town": "Москва",
            "street": "Льва Толстого",
            "building": "16к7стр5",
            "apartment": 7,
            "name": "Иванов Иван Иванович",
            "birth_date": "26.12.1986",
            "gender": "male",
            "relatives": []
            }


@pytest.fixture
def correct_import_data():
    return [{"citizen_id": 1,
             "town": "Москва",
             "street": "Льва Толстого",
             "building": "16к7стр5",
             "apartment": 7,
             "name": "Иванов Иван Иванович",
             "birth_date": "26.12.1986",
             "gender": "male",
             "relatives": [2, 3]},
            {"citizen_id": 2,
             "town": "Москва",
             "street": "Льва Толстого",
             "building": "16к7стр5",
             "apartment": 7,
             "name": "Иванов Сергей Иванович",
             "birth_date": "17.04.1997",
             "gender": "male",
             "relatives": [1]},
            {"citizen_id": 3,
             "town": "Москва",
             "street": "Иосифа Бродского",
             "building": "2",
             "apartment": 11,
             "name": "Романова Мария Леонидовна",
             "birth_date": "23.11.1986",
             "gender": "female",
             "relatives": [1]}]


@pytest.fixture
def incorrect_relatives_import_data():
    return [{"citizen_id": 1,
             "town": "Москва",
             "street": "Льва Толстого",
             "building": "16к7стр5",
             "apartment": 7,
             "name": "Иванов Иван Иванович",
             "birth_date": "26.12.1986",
             "gender": "male",
             "relatives": [2]},
            {"citizen_id": 2,
             "town": "Москва",
             "street": "Льва Толстого",
             "building": "16к7стр5",
             "apartment": 7,
             "name": "Иванов Сергей Иванович",
             "birth_date": "17.04.1997",
             "gender": "male",
             "relatives": []}]


@pytest.fixture
def correct_presents_response():
    return {"1": [],
            "2": [],
            "3": [],
            "4": [{"citizen_id": 1,
                   "presents": 1}],
            "5": [],
            "6": [],
            "7": [],
            "8": [],
            "9": [],
            "10": [],
            "11": [{"citizen_id": 1,
                    "presents": 1}],
            "12": [{"citizen_id": 2,
                    "presents": 1},
                   {"citizen_id": 3,
                    "presents": 1}]}


@pytest.fixture
def correct_age_stat_response():
    return [{"town": "Москва",
             "p50": 32.0,
             "p75": 32.0,
             "p99": 32.0}]


@pytest.fixture(autouse=True)
def rollback_database():
    yield
    wsgi.db_worker.rollback()


@pytest.fixture
def import_id():
    return Import.get_new_import_id()


@pytest.fixture(scope='module')
def test_client():
    flask_app = wsgi.app
    testing_client = flask_app.test_client()
    ctx = flask_app.app_context()
    ctx.push()

    yield testing_client

    ctx.pop()
