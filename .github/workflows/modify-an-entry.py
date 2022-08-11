import tinydb

db = tinydb.TinyDB('../../db.json')
last_record = db.all()[-1]

inci_db = tinydb.Query()

inci = db.search(inci_db.type == 'Wildfire')
inci = inci[0]

inci['resources'] = 'MM-1 MM-10 MM-100'

db.update(inci,inci_db.id == inci['id'])
