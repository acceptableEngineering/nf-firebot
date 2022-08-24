import tinydb

db = tinydb.TinyDB('../../db.json')
last_record = db.all()[-1]

inci_db = tinydb.Query()

inci = db.search(inci_db.type == 'Wildfire')
inci = inci[0]

inci['resources'] = 'LM-717'

db.update(inci,inci_db.id == inci['id'])
