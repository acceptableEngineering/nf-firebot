"""
N.F.-FireBot
(National Forest FireBot)

A Python script that scrapes WildWeb for US National Forest fire-related data,
and reports them to a given Telegram channel
"""
import datetime
import logging
import os
import sys
import requests
import tinydb
import urllib.parse
from dotenv import dotenv_values
from lxml import html

# ------------------------------------------------------------------------------

DEBUG = True
exec_path = os.path.dirname(os.path.realpath(__file__))
inci_list = []
db = tinydb.TinyDB(exec_path + '/db.json')

secrets = dotenv_values(".env")

config = {
    "wildcad_url": "http://www.wildcad.net/WCCA-" + secrets['NF_IDENTIFIER'] + \
        "recent.htm"
}
# ------------------------------------------------------------------------------

if len(sys.argv) > 1:
    if sys.argv[1] == 'live':
        DEBUG = False
else:
    logging.basicConfig(level=logging.DEBUG)

# ------------------------------------------------------------------------------

logging.debug('Running from %s', exec_path)


def search_attrs(arr, keyname, search):
    """
    Searches each key in a given array for a matching string
    """
    arr = arr['attributes']
    if arr[keyname]:
        if search in arr[keyname]:
            return True
    return False


def format_geo(input_str):
    """
    Formats dirty geolocation string to be HTTP request-friendly
    """
    input_str = str(input_str)
    input_str = input_str.replace(' ', '+')
    return input_str


def utf8_encode(input_str):
    """
    Prepares a string for downstream curl by making ASCII Hexadecimal
    replacements. EG: "# 123" becomes "%23 123"
    """
    if isinstance(input_str, str):
        input_str = urllib.parse.quote_plus(input_str)
        return input_str
    else:
        return False


def telegram(message_str, priority_str):
    """
    Output: Telegram Channel
    """
    message_str = utf8_encode(message_str)
    url = 'https://api.telegram.org/' + secrets['TELEGRAM_BOT_ID'] + ':' + \
        secrets['TELEGRAM_BOT_SECRET'] + '/sendMessage?chat_id=' + \
        secrets['TELEGRAM_CHAT_ID'] + '&text=' + message_str + '&parse_mode=html'

    if priority_str == 'low':
        url = url + '&disable_notification=true'

    if DEBUG is True:
        logging.debug(url)
    else:
        requests.get(url)


def process_wildcad():
    """
    Data source: Wildcad
    """
    page = requests.get(config['wildcad_url'])
    tree = html.fromstring(page.content)
    rows = tree.xpath('//tr')
    data = list()
    for row in rows:
        data.append([c.text_content() for c in row.getchildren()])

    counter = 0

    for item in data:
        counter = counter + 1
        if counter > 2:
            item_date = item[0].split('/')
            item_date_split = item_date[2].split(' ')
            item_date[2] = item_date_split[0]
            item_date.append(item_date_split[1])

            item_dict = {
                'id': empty_fill(item[1]),
                'name': empty_fill(item[2]),
                'type': empty_fill(item[3]),
                'location': empty_fill(item[4]),
                'comment': format_comment(item[5])
            }
            if ', ' in item[9]: # Item has geo data
                item_xy_split = item[9].split(', ')
                item_dict['x'] = item_xy_split[0]
                item_dict['y'] = item_xy_split[1]

            inci_list.append(item_dict)


def pad_date_prop(input_int):
    """
    Pads a given int. EG: 7 becomes 07
    """
    return str(f'{input_int:02}')


def get_date():
    """
    Returns a standardized YYYY-MM-DD string, with padding/fill
    """
    now = datetime.datetime.now()
    return str(now.year) + '-' + pad_date_prop(now.month) + '-' + \
        pad_date_prop(now.day)


def get_time():
    """
    Returns a standardized HH:MM:SS (24 hour) string, with padding/fill
    """
    now = datetime.datetime.now()
    return pad_date_prop(now.hour) + ':' + pad_date_prop(now.minute) + ':' + \
        pad_date_prop(now.second)


def empty_fill(input_str):
    """
    Pads a given input to two digits, useful for date/time. EG: "7" becomes "07"
    """
    if len(input_str) < 1 or input_str == '.':
        return ''

    return input_str


def format_comment(input_str):
    """
    """
    input_str.replace('...', '  ')

    return empty_fill(input_str)


def event_has_changed(inci_dict, inci_db_entry_dict):
    """
    Given a new and stored event dict, determines if any values have changed,
    returning a list of dicts
    """
    inci_db_entry_dict = inci_db_entry_dict[0]
    changed = []

    for key in inci_dict:
        if (key in inci_db_entry_dict) and (inci_dict[key] != inci_db_entry_dict[key]):
            changed.append({
                "name": key,
                "new": inci_dict[key],
                "old": inci_db_entry_dict[key]
            })

    if changed:
        return changed

    return False


def is_fire(inci_dict):
    """
    Simple algo determines whether the given incident matches our criteria for
    a fire incident
    """
    if(
        'fire' in inci_dict['location'].lower()
        or 'fire' in inci_dict['type'].lower()
        or 'smoke' in inci_dict['type'].lower()
        or 'fire' in inci_dict['name'].lower()
        and 'Resource Order' not in inci_dict['type']
        and 'MC DOWN' not in inci_dict['name'].upper()
        and 'TRAFFIC COLLISION' not in inci_dict['name'].upper()
        and 'DAILY STATUS' not in inci_dict['name'].upper()
    ):
        return True

    return False


def uppercase_first(input_str):
    """
    Simply uppercases the first letter of a given string
    """
    return input_str[0].upper() + input_str[1:]

# ------------------------------------------------------------------------------

process_wildcad()

if len(inci_list) > 0:
    for inci in inci_list:
        inci_db = tinydb.Query()

        if db.search(inci_db.id == inci['id']):
            logging.debug('%s: found in DB', inci['id'])
            inci_db_entry = db.search(inci_db.id == inci['id'])
            event_changes = event_has_changed(inci, inci_db_entry)

            if event_changes:
                logging.debug('%s: has changed', inci['id'])

                if is_fire(inci) is False:
                    db.remove(inci_db.id == inci['id'])
                else:
                    db.update(inci, inci_db.id == inci['id'])

                notification_body = 'Dispatch changed <b>' + inci['id'] + '</b>'
                for change in event_changes:
                    change_name = change['name']
                    notification_body += '\n' + uppercase_first(change['name']) + ': ' + \
                        '<s>' + change['old'] + '</s> ' + change['new']
                telegram(notification_body, 'low')
            else:
                logging.debug('%s: unchanged', inci['id'])
        else:
            if is_fire(inci):
                logging.debug('%s not found in DB, new inci', inci['id'])
                inci['date'] = get_date()
                inci['time'] = get_time()
                db.insert(inci)
                notification_body = '<b>New Possible Fire Incident</b>' + \
                    '\nID: ' + empty_fill(inci['id']) + \
                    '\nName: ' + empty_fill(inci['name']) + \
                    '\nType: ' + empty_fill(inci['type']) + \
                    '\nLocation: ' + empty_fill(inci['location']) + \
                    '\nComment: ' + format_comment(inci['comment'])

                if 'x' in inci and 'x' in inci:
                    notification_body = notification_body + '\nGoogle Maps: https://www.google.com/maps/search/' + \
                    format_geo(inci['x']) + ',' + format_geo(inci['y']) + '?sa=X'
                telegram(notification_body, 'high')

# ------------------------------------------------------------------------------

date_now = datetime.datetime.now()

"""
Send daily recap if time is 23:59
"""
if str(date_now.hour) + ':' + str(date_now.minute) == '23:59':
    logging.debug('Generating daily recap')
    inci_db = tinydb.Query()
    results = db.search(inci_db.date == get_date())
    NOTIF_BODY = '<b>Daily Recap:</b> '

    if results:
        COUNT = 0

        for result in results:
            COUNT = COUNT + 1

        if COUNT == 1:
            NOTIF_BODY = NOTIF_BODY + 'Today there was only <b>1</b> actual' + \
                ' fire incident in ' + secrets['NF_IDENTIFIER']
        else:
            NOTIF_BODY = NOTIF_BODY + 'Today there were <b>' + str(COUNT) + \
                '</b> actual fire incidents in ' + secrets['NF_IDENTIFIER']

        telegram(NOTIF_BODY, 'low')

# ------------------------------------------------------------------------------
