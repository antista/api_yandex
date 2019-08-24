class DataBaseWorker:
    def __init__(self, db):
        self.session = db.session

    def commit(self):
        self.session.commit()

    def add(self, object):
        self.session.add(object)

    def rollback(self):
        self.session.rollback()
