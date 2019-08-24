import json

from flask import request

from api.models import Import, Citizen
from .wsgi import app


@app.route('/imports', methods=['POST'])
def handle_import_request():
    if request.method == 'POST':
        data = request.json
        if not data or 'citizens' not in data.keys():
            return json.dumps({}), 400
        import_id = Import.create_import(data['citizens'])
        if not import_id:
            return json.dumps({}), 400
        return json.dumps({"data": {"import_id": import_id}}), 201
    return json.dumps({}), 405  # pragma:no cover


@app.route('/imports/<import_id>/citizens/<citizen_id>', methods=['PATCH'])
def handle_change_citizen_request(import_id, citizen_id):
    if request.method == 'PATCH':
        data = request.json
        if not data:
            return json.dumps({}), 400
        citizen = Citizen.change_data(int(import_id), int(citizen_id), data)
        if not citizen:
            return json.dumps({}), 400
        return json.dumps(citizen.as_dict(), ensure_ascii=False), 200
    return json.dumps({}), 405  # pragma:no cover


@app.route('/imports/<import_id>/citizens', methods=['GET'])
def handle_citizens_request(import_id):
    if request.method == 'GET':
        citizens = Import.get_all_citizens(int(import_id))
        if not citizens:
            return json.dumps({}), 400
        return json.dumps({"data": citizens}, ensure_ascii=False), 200
    return json.dumps({}), 405  # pragma:no cover


@app.route('/imports/<import_id>/citizens/birthdays', methods=['GET'])
def handle_birthdays_request(import_id):
    if request.method == 'GET':
        presents = Citizen.count_presents(int(import_id))
        if not presents:
            return json.dumps({}), 400
        return json.dumps({'data': presents}, ensure_ascii=False), 200
    return json.dumps({}), 405  # pragma:no cover


@app.route('/imports/<import_id>/towns/stat/percentile/age', methods=['GET'])
def handle_age_stat_request(import_id):
    if request.method == 'GET':
        age_stat = Citizen.get_age_stat(int(import_id))
        if not age_stat:
            return json.dumps({}), 400
        return json.dumps({'data': age_stat}, ensure_ascii=False), 200
    return json.dumps({}), 405  # pragma:no cover
