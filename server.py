"""
N.F.-FireBot (National Forest FireBot)
https://github.com/acceptableEngineering/nf-firebot

./server.py

This is run by Uvicorn to create a server which is contacted by Twilio each time
someone texts 'Subscribe' or 'Unsubscribe'
"""
import json
import os
import tinydb

exec_path = os.path.dirname(os.path.realpath(__file__))
db = tinydb.TinyDB(exec_path + '/contact_db.json')

# ------------------------------------------------------------------------------

def add_to_db(body):
    """
    Adds a subscriber to the database if not already found in it
    """
    body_phone = str(body['number'])

    db_result = db.search(tinydb.Query().number == body_phone)

    if len(db_result) == 0:
        db.insert({
            'number': body_phone,
            'forest': 'ANF', # Possibly more options in the future, so fill
            'alert_level': 'all' # Multiple levels of alerts soon, so fill
        })

        return True

    return {
        "code": 400,
        "body": "you are already subscribed"
    }

# ------------------------------------------------------------------------------

def remove_from_db(body):
    """
    Removes a subscriber from the database, if they already exist in it
    """
    body_phone = str(body['number'])

    db_result = db.search(tinydb.Query().number == body_phone)

    if len(db_result) > 0:
        db.remove(
            tinydb.Query().number == body_phone
        )

        return True

    return {
        "code": 400,
        "body": "you aren't subscribed"
    }

# ------------------------------------------------------------------------------

def process_response(command_response):
    """
    Interprets a function's response to generate HTTP error/success codes
    """
    if command_response is True:
        return {
            "code": 200,
            "body": "OK"
        }

    return {
        "code": command_response['code'],
        "body": str(command_response['body'])
    }

# ------------------------------------------------------------------------------

async def read_body(receive):
    """
    Read and return the entire body from an incoming ASGI message
    """
    body = b''
    more_body = True

    while more_body:
        message = await receive()
        body += message.get('body', b'')
        more_body = message.get('more_body', False)

    return body


async def app(scope, receive, send):
    """
    Echo the method and path back in an HTTP response
    """
    assert scope['type'] == 'http'

    body = await read_body(receive)
    body = json.loads(body)

    if scope['path'].strip() == '/add':
        command_response = add_to_db(body)
    elif scope['path'].strip() == '/remove':
        command_response = remove_from_db(body)
    elif scope['path'].strip() == '/ping':
        command_response = True
    else:
        command_response = {
            "code": 400,
            "body": 'Invalid API method: ' + scope["path"]
        }

    server_response = process_response(command_response)

    await send({
        'type': 'http.response.start',
        'status': server_response['code'],
        'headers': [
            [b'content-type', b'text/plain'],
        ]
    })

    await send({
        'type': 'http.response.body',
        'body': server_response['body'].encode('utf-8')
    })

# ------------------------------------------------------------------------------
