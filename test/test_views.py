import json

from flask import url_for

from api.wsgi import app


def test_handle_import_request_ok(mocker, test_client, import_id):
    mocker.patch('api.models.Import.create_import', return_value=import_id)
    with app.test_request_context():
        response = test_client.post(url_for('handle_import_request'), json={'citizens': []})
        assert response.status_code == 201
        assert response.data.decode() == '{"data": {"import_id": %d}}' % import_id


def test_handle_import_request_400(test_client):
    with app.test_request_context():
        response = test_client.post(url_for('handle_import_request'))
        assert response.status_code == 400


def test_handle_import_request_wrong_data(mocker, test_client, incorrect_relatives_import_data):
    mocker.patch('api.models.Import.create_import', return_value=None)
    with app.test_request_context():
        response = test_client.post(url_for('handle_import_request'), json={'not_citizen': []})
        assert response.status_code == 400
        response = test_client.post(url_for('handle_import_request'),
                                    json={'citizens': incorrect_relatives_import_data})
        assert response.status_code == 400


def test_handle_change_citizen_request_ok(mocker, test_client, citizen, correct_citizen_data):
    mocker.patch('api.models.Citizen.change_data', return_value=citizen)
    mocker.patch('api.models.Citizen.as_dict', return_value=correct_citizen_data)
    with app.test_request_context():
        response = test_client.patch(url_for('handle_change_citizen_request', import_id=1, citizen_id=1),
                                     json={'citizens': []})
        assert response.status_code == 200
        assert response.data.decode() == json.dumps(correct_citizen_data, ensure_ascii=False)


def test_handle_change_citizen_request_400(mocker, test_client):
    mocker.patch('api.models.Citizen.change_data', return_value=None)
    with app.test_request_context():
        response = test_client.patch(url_for('handle_change_citizen_request', import_id=1, citizen_id=1))
        assert response.status_code == 400
        response = test_client.patch(url_for('handle_change_citizen_request', import_id=1, citizen_id=1),
                                     json={'not_empty_wrong_data': []})
        assert response.status_code == 400


def test_handle_citizen_request_ok(mocker, test_client, correct_import_data):
    mocker.patch('api.models.Import.get_all_citizens', return_value=correct_import_data)
    with app.test_request_context():
        response = test_client.get(url_for('handle_citizens_request', import_id=1))
        assert response.status_code == 200
        assert response.data.decode() == json.dumps({'data': correct_import_data}, ensure_ascii=False)


def test_handle_citizen_request_400(mocker, test_client):
    mocker.patch('api.models.Import.get_all_citizens', return_value=None)
    with app.test_request_context():
        response = test_client.get(url_for('handle_citizens_request', import_id=1))
        assert response.status_code == 400


def test_birthdays_request_ok(mocker, test_client, correct_presents_response):
    mocker.patch('api.models.Citizen.count_presents', return_value=correct_presents_response)
    with app.test_request_context():
        response = test_client.get(url_for('handle_birthdays_request', import_id=1))
        assert response.status_code == 200
        assert response.data.decode() == json.dumps({'data': correct_presents_response}, ensure_ascii=False)


def test_birthdays_request_400(mocker, test_client, ):
    mocker.patch('api.models.Citizen.count_presents', return_value=None)
    with app.test_request_context():
        response = test_client.get(url_for('handle_birthdays_request', import_id=1))
        assert response.status_code == 400


def test_handle_age_stat_request_ok(mocker, test_client, correct_age_stat_response):
    mocker.patch('api.models.Citizen.get_age_stat', return_value=correct_age_stat_response)
    with app.test_request_context():
        response = test_client.get(url_for('handle_age_stat_request', import_id=1))
        assert response.status_code == 200
        assert response.data.decode() == json.dumps({'data': correct_age_stat_response}, ensure_ascii=False)


def test_handle_age_stat_request_400(mocker, test_client):
    mocker.patch('api.models.Citizen.get_age_stat', return_value=None)
    with app.test_request_context():
        response = test_client.get(url_for('handle_age_stat_request', import_id=1))
        assert response.status_code == 400
