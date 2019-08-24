from collections import defaultdict
from datetime import date
from numpy import percentile

from sqlalchemy import Enum

from api.wsgi import db, db_worker

REQUIRED_FIELDS = {'citizen_id', 'town', 'street', 'building', 'apartment', 'name', 'birth_date', 'gender',
                   'relatives'}


class Citizen(db.Model):
    __tablename__ = "citizens"
    import_id = db.Column(db.Integer, primary_key=True)
    citizen_id = db.Column(db.Integer, primary_key=True)
    town = db.Column(db.String(80), nullable=False)
    street = db.Column(db.String(80), nullable=False)
    building = db.Column(db.String(80), nullable=False)
    apartment = db.Column(db.Integer)
    name = db.Column(db.String(80), nullable=False)
    birth_date = db.Column(db.Date(), nullable=False)
    gender = db.Column(Enum("female", "male", name="gender_enum", create_type=False))
    relatives = db.relationship("Relations", backref='citizen')

    def as_dict(self):
        """ Возвращает словарь, содержащий все поля переданного citizen. """
        atr = {c.name: getattr(self, c.name) for c in self.__table__.columns if
               c.name != 'import_id' and c.name != 'birth_date'}
        atr['birth_date'] = self.birth_date.strftime('%d.%m.%Y')
        atr['relatives'] = Relations.get_all_relatives_id(self.import_id, self.citizen_id)
        return atr

    @staticmethod
    def get_citizen(import_id, citizen_id):  # pragma: no cover
        return Citizen.query.get((import_id, citizen_id))

    @staticmethod
    def create_citizen(import_id, data):
        if not Citizen.is_data_valid(data) or REQUIRED_FIELDS ^ data.keys() \
                or Citizen.get_citizen(import_id, data['citizen_id']):
            return None
        citizen = Citizen(import_id=import_id, citizen_id=data['citizen_id'], town=data['town'],
                          street=data['street'],
                          building=data['building'], apartment=data['apartment'], name=data['name'],
                          birth_date=date(*reversed([int(x) for x in data['birth_date'].split('.')])),
                          gender=data['gender'])
        db_worker.add(citizen)
        return citizen

    @staticmethod
    def change_data(import_id, citizen_id, data):
        if not Citizen.is_data_valid(data) \
                or REQUIRED_FIELDS & data.keys() != data.keys() \
                or 'citizen_id' in data.keys() \
                or not Citizen.get_citizen(import_id, citizen_id):
            return None
        citizen = Citizen.get_citizen(import_id, citizen_id)
        for key, value in data.items():
            if key == 'relatives':
                if not Relations.change_relations(import_id, citizen_id, value):
                    db_worker.rollback()
                    return None
            else:
                citizen.__setattr__(key, value)

        db_worker.commit()
        return citizen

    @staticmethod
    def count_presents(import_id):
        """ Метод пробегает по каждому citizen и увеличивает количество подарков,
            необходимых для каждого его родственника в этом месяце, на единицу.

            presents представляет собой массив из 12 словарей, соответствующих каждому месяцу года.
            Ключом такого словаря является citizen_id,
            а значением - количество подарков, необходимых купить данному citizen в этом месяце. """

        presents = [defaultdict(int) for _ in range(12)]
        if not Citizen.query.filter_by(import_id=import_id).first():
            return None
        for citizen in Citizen.query.filter_by(import_id=import_id):
            for relation in Relations.query.filter_by(import_id=import_id, citizen_id=citizen.citizen_id):
                presents[citizen.birth_date.month - 1][relation.relative_id] += 1
        return Citizen.presents_count_to_dict(presents)

    @staticmethod
    def get_age_stat(import_id):
        stat = defaultdict(list)
        for citizen in Citizen.query.filter_by(import_id=import_id):
            stat[citizen.town].append(Citizen.calculate_age(citizen.birth_date))
        res = []
        for town, ages in stat.items():
            res.append({'town': town, 'p50': round(percentile(ages, 50), 1),
                        'p75': round(percentile(ages, 75), 1),
                        'p99': round(percentile(ages, 99), 1)})
        return res

    @staticmethod
    def calculate_age(birth_date):  # pragma: no cover
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    @staticmethod
    def is_data_valid(data):
        if not data or type(data) is not dict:
            return False
        for value in data.values():
            if value is None:
                return False
        if ('citizen_id' in data.keys() and type(data['citizen_id']) is not int) \
                or ('apartment' in data.keys() and type(data['apartment']) is not int):
            return False
        for field in REQUIRED_FIELDS - {'citizen_id', 'apartment', 'relatives'}:
            if field in data.keys() and (type(data[field]) is not str or not data[field]):
                return False
        if 'gender' in data.keys() and data['gender'] not in {'male', 'female'}:
            return False
        if 'birth_date' in data.keys():
            try:
                date(*reversed([int(x) for x in data['birth_date'].split('.')]))
            except (ValueError, TypeError):
                return False
        if 'relatives' in data.keys():
            if type(data['relatives']) is not list:
                return False
            for relative_id in data['relatives']:
                if type(relative_id) is not int:
                    return False
        return True

    @staticmethod
    def presents_count_to_dict(presents):
        """ Возвращает подготовленный словарь с данными о подарках, необходимых для каждого citizen. """
        result = dict()
        for month in range(1, 13):
            result[str(month)] = []
            for citizen_id, presents_count in presents[month - 1].items():
                result[str(month)].append({'citizen_id': citizen_id, "presents": presents_count})
        return result


class Relations(db.Model):
    import_id = db.Column(db.Integer, primary_key=True)
    citizen_id = db.Column(db.Integer, primary_key=True)
    relative_id = db.Column(db.Integer, primary_key=True)

    __table_args__ = (db.ForeignKeyConstraint(['import_id', 'citizen_id'],
                                              ['citizens.import_id', 'citizens.citizen_id']),)

    @staticmethod
    def create_all_relations(import_id, relations):
        """ Принимает на вход словарь , ключами которого являются citizen_id,
            а значениями - set, содержащие citizen_id ближайших родственников данного citizen.

            Метод возвращиет True, если родственные связи успешно созданы, и False в противном случае. """

        for citizen_id, relatives in relations.items():
            for relative_id in relatives:
                if relative_id not in relations.keys() or citizen_id not in relations[relative_id] \
                        or not Relations.create_relation(import_id, citizen_id, relative_id):
                    return False
        return True

    @staticmethod
    def create_relation(import_id, citizen_id, relative_id):
        """ Создает одностороннее отношение и возвращает его. """
        if not Citizen.query.get((import_id, relative_id)) or citizen_id == relative_id:
            return None
        relation = Relations(import_id=import_id, citizen_id=citizen_id, relative_id=relative_id)
        db_worker.add(relation)
        return relation

    @staticmethod
    def change_relations(import_id, citizen_id, new_relatives):
        """ Двусторонне изменяет отношения между citizen и его relative. """
        old_relatives = {relation.relative_id for relation in
                         Relations.query.filter_by(import_id=import_id, citizen_id=citizen_id)}
        for relative_id in set(new_relatives) - old_relatives:
            if not Relations.create_relation(import_id, citizen_id, relative_id) \
                    or not Relations.create_relation(import_id, relative_id, citizen_id):
                return False
        for relative_id in old_relatives - set(new_relatives):
            Relations.delete_relation(import_id, citizen_id, relative_id)
        return True

    @staticmethod
    def delete_relation(import_id, citizen_id, relative_id):  # pragma: no cover
        """ Двусторонне удаляет отношения между citizen и его relative.
            Возвращает True, если удаление прошло успешно, False - в противном случае"""
        if not Relations.query.get((import_id, citizen_id, relative_id)) \
                or not Relations.query.get((import_id, relative_id, citizen_id)):
            return False
        Relations.query.filter_by(import_id=import_id, citizen_id=citizen_id, relative_id=relative_id).delete()
        Relations.query.filter_by(import_id=import_id, citizen_id=relative_id, relative_id=citizen_id).delete()
        return True

    @staticmethod
    def get_all_relatives_id(import_id, citizen_id):
        return [relation.relative_id for relation in
                Relations.query.filter_by(import_id=import_id, citizen_id=citizen_id)]


class Import:
    @staticmethod
    def get_new_import_id():
        last_rec = Citizen.query.order_by(
            Citizen.import_id.desc()).first()
        return 1 if not last_rec else last_rec.import_id + 1

    @staticmethod
    def create_import(data):
        if not data:
            return None
        import_id = Import.get_new_import_id()
        relationships = defaultdict(set)
        for citizen_data in data:
            citizen = Citizen.create_citizen(import_id, citizen_data)
            if not citizen:
                db_worker.rollback()
                return None
            relationships[citizen.citizen_id] = set(citizen_data['relatives'])

        is_relations_created = Relations.create_all_relations(import_id, relationships)
        if not is_relations_created:
            db_worker.rollback()
            return None
        db_worker.commit()
        return import_id

    @staticmethod
    def get_all_citizens(import_id):
        res = []
        for citizen in Citizen.query.filter_by(import_id=import_id):
            res.append(citizen.as_dict())
        return res
