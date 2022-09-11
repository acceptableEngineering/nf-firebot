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
db = tinydb.TinyDB(exec_path + '/db_contacts.json')
db_urls = tinydb.TinyDB(exec_path + '/db_urls.json')

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

    if body:
        body = json.loads(body)

    if scope['path'].strip() == '':
        command_response = {
            "code": 400,
            "body": 'Invalid URL'
        }
    if scope['path'].strip() == '/add':
        command_response = add_to_db(body)
    elif scope['path'].strip() == '/remove':
        command_response = remove_from_db(body)
    elif scope['path'].strip() == '/ping':
        command_response = True
    else:
        request_url_strip = scope['path'].split('/')
        this_db_check = db_urls.search(tinydb.Query().id == request_url_strip[1].strip())
        if len(this_db_check) > 0:
            await send({
                'type': 'http.response.start',
                'status': 302,
                'headers': [
                    [b'Location', this_db_check[0]['url']],
                ]
            })
            this_body = '<head><meta http-equiv="Refresh" content="0; URL=' + \
                this_db_check[0]['url'] + '"></head>'
            await send({
                'type': 'http.response.body',
                'body': this_body.encode('utf-8')
            })
            command_response = False
        else:
            command_response = {
                "code": 400,
                "body": 'Path not found'
            }

    if command_response is not False:
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
