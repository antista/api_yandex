from api.models import REQUIRED_FIELDS, Citizen, Import, Relations


def test_citizen_as_dict(mocker, citizen):
    mocker.patch('api.models.Relations.get_all_relatives_id', return_value=[2, 3])
    data = citizen.as_dict()
    assert type(data) is dict
    assert 'import_id' not in data.keys()
    assert not REQUIRED_FIELDS - data.keys()
    assert type(data['building']) is str
    assert data['gender'] in {'male', 'female'}
    assert data['relatives'] == [2, 3]
    assert data['birth_date'] == "26.12.1986"
    assert type(data['citizen_id']) is int
    assert type(data['apartment']) is int


def test_create_citizen_ok(import_id, correct_citizen_data):
    citizen = Citizen.create_citizen(import_id, correct_citizen_data)
    assert citizen
    same_citizen = Citizen.create_citizen(import_id, correct_citizen_data)
    assert not same_citizen


def test_create_empty_citizen(import_id):
    assert not Citizen.create_citizen(import_id, {})


def test_change_data_ok(mocker, import_id, correct_citizen_data):
    mocker.patch('api.database_worker.DataBaseWorker.commit')
    Citizen.create_citizen(import_id, correct_citizen_data)
    citizen = Citizen.change_data(import_id, correct_citizen_data['citizen_id'], {
        "name": "Иванова Мария Леонидовна",
        "town": "Новосибирск",
        "apartment": 9})
    assert citizen
    assert citizen.name == "Иванова Мария Леонидовна"
    assert citizen.town == "Новосибирск"
    assert citizen.apartment == 9


def test_change_data_wrong(import_id, correct_citizen_data):
    assert not Citizen.change_data(5, 7, {'apartment': 9})
    Citizen.create_citizen(import_id, correct_citizen_data)
    citizen_id = correct_citizen_data['citizen_id']
    assert not Citizen.change_data(import_id, citizen_id, {})
    assert not Citizen.change_data(import_id, citizen_id, {'town': None})
    assert not Citizen.change_data(import_id, citizen_id, {'citizen_id': 10})
    assert not Citizen.change_data(import_id, citizen_id, {'relatives': [15]})


def test_data_valid(correct_citizen_data):
    assert Citizen.is_data_valid(correct_citizen_data)
    assert not Citizen.is_data_valid({})

    assert Citizen.is_data_valid({'citizen_id': 1})
    assert not Citizen.is_data_valid({'citizen_id': 'qwerty'})

    assert Citizen.is_data_valid({'gender': 'male'})
    assert Citizen.is_data_valid({'gender': 'female'})
    assert not Citizen.is_data_valid({'gender': 'another'})
    assert not Citizen.is_data_valid({'gender': 5})

    assert Citizen.is_data_valid({'town': 'Тамбов'})
    assert not Citizen.is_data_valid({'town': ''})
    assert not Citizen.is_data_valid({'town': None})
    assert not Citizen.is_data_valid({'town': 9})

    assert Citizen.is_data_valid({'apartment': 7})
    assert not Citizen.is_data_valid({'apartment': 'qwerty'})

    assert Citizen.is_data_valid({'birth_date': '20.07.1998'})
    assert not Citizen.is_data_valid({'birth_date': '20.13.1998'})
    assert not Citizen.is_data_valid({'birth_date': '31.02.1998'})
    assert not Citizen.is_data_valid({'birth_date': '3102.1998'})
    assert not Citizen.is_data_valid({'birth_date': '1998.07.20'})

    assert Citizen.is_data_valid({'relatives': []})
    assert Citizen.is_data_valid({'relatives': [2, 3]})
    assert not Citizen.is_data_valid({'relatives': 2})
    assert not Citizen.is_data_valid({'relatives': '2,3'})
    assert not Citizen.is_data_valid({'relatives': [2, '5a']})


def test_get_import_id(correct_citizen_data):
    import_id = Import.get_new_import_id()
    Citizen.create_citizen(import_id, correct_citizen_data)
    assert Import.get_new_import_id() == import_id + 1


def test_get_all_citizens(import_id, correct_citizen_data):
    assert not Import.get_all_citizens(import_id)
    Citizen.create_citizen(import_id, correct_citizen_data)
    citizens = Import.get_all_citizens(import_id)
    assert citizens
    assert type(citizens) is list
    assert len(citizens) == 1
    assert type(citizens[0]) is dict
    for key, value in citizens[0].items():
        assert key in correct_citizen_data.keys()
        if key == 'relatives':
            for relative in value:
                assert relative in correct_citizen_data[key]
        else:
            assert value == correct_citizen_data[key]

    Citizen.create_citizen(import_id, {key: value if key != 'citizen_id' else value + 1 for key, value in
                                       correct_citizen_data.items()})
    citizens = Import.get_all_citizens(import_id)
    assert len(citizens) == 2


def test_create_import(mocker, import_id, correct_import_data, correct_citizen_data, incorrect_relatives_import_data):
    mocker.patch('api.database_worker.DataBaseWorker.commit')
    assert Import.create_import(correct_import_data) == import_id
    assert len(Import.get_all_citizens(import_id)) == len(correct_import_data)
    assert not Import.create_import([])
    assert not Import.create_import([correct_citizen_data, {}])
    assert Import.create_import([correct_citizen_data])
    assert not Import.create_import(incorrect_relatives_import_data)
    assert Import.get_new_import_id() == import_id


def test_change_relatives(mocker, correct_import_data):
    mocker.patch('api.database_worker.DataBaseWorker.commit')
    import_id = Import.create_import(correct_import_data)

    citizen_id = correct_import_data[0]['citizen_id']
    old_relatives = Relations.get_all_relatives_id(import_id, citizen_id)
    assert Citizen.change_data(import_id, citizen_id, {'relatives': []})
    for relative_id in old_relatives:
        assert citizen_id not in Relations.get_all_relatives_id(import_id, relative_id)

    another_citizen_id = correct_import_data[1]['citizen_id']
    assert citizen_id not in Relations.get_all_relatives_id(import_id, another_citizen_id)
    assert Citizen.change_data(import_id, citizen_id, {'relatives': [another_citizen_id]})
    assert citizen_id in Relations.get_all_relatives_id(import_id, another_citizen_id)
    assert another_citizen_id in Relations.get_all_relatives_id(import_id, citizen_id)


def test_count_presents(mocker, correct_import_data, correct_presents_response, correct_age_stat_response):
    mocker.patch('api.database_worker.DataBaseWorker.commit')
    import_id = Import.create_import(correct_import_data)
    presents = Citizen.count_presents(import_id)
    assert presents == correct_presents_response
    assert Citizen.get_age_stat(import_id) == correct_age_stat_response
    assert not Citizen.count_presents(-54)
