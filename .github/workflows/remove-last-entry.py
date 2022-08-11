import tinydb

db = tinydb.TinyDB('../../db.json')
last_record = db.all()[-1]

inci_db = tinydb.Query()

db.remove(inci_db.id == last_record['id'])
