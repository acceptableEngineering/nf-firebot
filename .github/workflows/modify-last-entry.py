import tinydb

db = tinydb.TinyDB('../../db.json')
last_record = db.all()[-1]

inci_db = tinydb.Query()

last_record['resources'] = 'ENG-10 ENG-19 ENG-310'
print(last_record)

db.update(last_record,inci_db.id == last_record['id'])
