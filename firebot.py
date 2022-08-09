"""
N.F.-FireBot
(National Forest FireBot)

A Python script that scrapes WildWeb for US National Forest fire-related data,
and reports them to a given Telegram channel
"""
import urllib.parse
import datetime
import logging
import os
import sys
import json_log_formatter
import requests
import tinydb
from dotenv import dotenv_values
from lxml import html

# Initialize JSON logging
formatter = json_log_formatter.JSONFormatter()

json_handler = logging.FileHandler(filename='./firebot-log.json')
json_handler.setFormatter(formatter)

logger = logging.getLogger('firebot_json')
logger.addHandler(json_handler)

# ------------------------------------------------------------------------------

DEBUG = False
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
    if sys.argv[1] == 'debug':
        DEBUG = True
        logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.ERROR)

# ------------------------------------------------------------------------------

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
    return urllib.parse.quote_plus(input_str)


def telegram(message_str, priority_str):
    """
    Output: Telegram Channel
    """
    chat_id = secrets['TELEGRAM_CHAT_ID']

    if priority_str == 'special':
        chat_id = secrets['TELEGRAM_SPECIAL_CHAT_ID']

    message_str = utf8_encode(message_str)
    url = 'https://api.telegram.org/' + secrets['TELEGRAM_BOT_ID'] + ':' + \
        secrets['TELEGRAM_BOT_SECRET'] + '/sendMessage?chat_id=' + \
        chat_id + '&text=' + message_str + '&parse_mode=html'

    if priority_str == 'low':
        url = url + '&disable_notification=true'

    if DEBUG is True:
        logger.debug('Telegram URL: %s', url)

    if('False' not in [
        secrets['TELEGRAM_BOT_ID'],
        secrets['TELEGRAM_BOT_SECRET'],
        chat_id
    ]):
        req_result = requests.get(url, timeout=10, allow_redirects=False)
        logger.debug(req_result)
    else:
        logger.error('A required var is not set in .env! Cannot send Telegram message')


def process_wildcad():
    """
    Data source: Wildcad
    """
    try:
        page = requests.get(config['wildcad_url'])
    except requests.exceptions.RequestException as error:
        logger.error('Could not reach Wildcad URL %s', config['wildcad_url'])
        logger.error(error)
        sys.exit()

    tree = html.fromstring(page.content)
    rows = tree.xpath('//tr')
    data = []
    for row in rows:
        data.append([c.text_content() for c in row.getchildren()])

    counter = 0
    checked_ids = []

    for item in data:
        counter = counter + 1
        if counter > 2 and item[1] not in checked_ids:
            item_date = item[0].split('/')
            item_date_split = item_date[2].split(' ')
            item_date[2] = item_date_split[0]
            item_date.append(item_date_split[1])
            checked_ids.append(item[1])

            item_dict = {
                'id': empty_fill(item[1]), # "Inc #" field
                'name': empty_fill(item[2]), # "Name" field
                'type': empty_fill(item[3]), # "Type" field
                'location': empty_fill(item[4]), # "Location" field
                'comment': empty_fill(item[5]), # "WebComment" field
                'resources': empty_fill(item[6]), # "Resources" field
                'acres': empty_fill(item[8]), # "Acres" field
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
    Returns an empty string when given a useless string, to maintain one-per-line
    formatting in notification messages
    """
    if len(input_str) < 1 or input_str == '.':
        return ''

    return input_str


def event_has_changed(inci_dict, inci_db_entry_dict):
    """
    Given a new and stored event dict, determines if any values have changed,
    returning a list of dicts
    """
    inci_db_entry_dict = inci_db_entry_dict[0]
    changed = []

    for key in inci_dict:
        if (
            key in inci_db_entry_dict
            and inci_dict[key] != inci_db_entry_dict[key]
            and key != 'acres' # Newly-tracked field. Don't notify, just store
        ):
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
    ignore_list = ('DAILY STATUS')

    if(
        (
            'FIRE' in inci_dict['type'].strip().upper()
            or 'FIRE' in inci_dict['type'].strip().upper()
            or 'SMOKE' in inci_dict['name'].strip().upper()
        )
        and
        (
            inci_dict['type'].strip().upper() not in ignore_list
            and inci_dict['name'].strip().upper() not in ignore_list
        )
    ):
        check_major_fire(inci_dict)
        return True

    return False


def check_major_fire(inci_dict):
    """
    If major incident, report it to special channel(s) as well
    """
    if(
        'TELEGRAM_SPECIAL_CHAT_ID' in secrets
        and inci_dict['name'] != 'New'
        # and inci_dict['resources'].strip() != ''
        and empty_fill(inci_dict['acres']) != ''
    ):
        logger.debug('Major fire event detected: %s', inci_dict['id'])

        this_notif_body = '<b>New MAJOR Fire Incident</b>' + \
                    '\nID: ' + empty_fill(inci_dict['id']) + \
                    '\nName: ' + empty_fill(inci_dict['name']) + \
                    '\nType: ' + empty_fill(inci_dict['type']) + \
                    '\nLocation: ' + empty_fill(inci_dict['location']) + \
                    '\nComment: ' + empty_fill(inci_dict['comment']) + \
                    '\nAcres: ' + empty_fill(inci_dict['acres']) + \
                    '\nResources: ' + empty_fill(inci_dict['resources'])

        if 'x' in inci_dict and 'y' in inci_dict:
            this_notif_body += create_gmaps_url(inci_dict)

        telegram(this_notif_body, 'special')

# ------------------------------------------------------------------------------

def uppercase_first(input_str):
    """
    Simply uppercases the first letter of a given string
    """
    return input_str[0].upper() + input_str[1:]

# ------------------------------------------------------------------------------

def create_gmaps_url(inci_dict):
    """
    Returns a Google Maps URL for given X/Y coordinates
    """
    return '\nGoogle Maps: https://www.google.com/maps/search/' + \
        format_geo(inci_dict['x']) + ',' + format_geo(inci_dict['y']) + '?sa=X'

# ------------------------------------------------------------------------------

logger.debug('Running from %s', exec_path)

process_wildcad()

if len(inci_list) > 0:
    inci_db = tinydb.Query()
    for inci in inci_list:

        if db.search(inci_db.id == inci['id']):
            logger.debug('%s found in DB', inci['id'])
            inci_db_entry = db.search(inci_db.id == inci['id'])
            event_changes = event_has_changed(inci, inci_db_entry)

            if event_changes:
                logger.debug('%s has changed', inci['id'])
                SEND_MAPS_LINK = False

                # Event changed from type 'Wildfire'. Delete from DB
                if is_fire(inci) is False:
                    db.remove(inci_db.id == inci['id'])
                else:
                    db.update(inci, inci_db.id == inci['id'])

                NOTIF_BODY = 'Dispatch changed <b>' + inci['id'] + '</b>'
                for change in event_changes:
                    change_name = change['name']
                    NOTIF_BODY += '\n' + uppercase_first(change['name']) + ': ' + \
                        '<s>' + change['old'] + '</s> ' + change['new']

                    if change['name'] == 'x' or change['name'] == 'y':
                        SEND_MAPS_LINK = True

                if SEND_MAPS_LINK is True:
                    NOTIF_BODY += create_gmaps_url(inci)

                telegram(NOTIF_BODY, 'low')
            else:
                logger.debug('%s unchanged', inci['id'])
        else:
            if is_fire(inci):
                logger.debug('%s not found in DB, new inci', inci['id'])
                inci['date'] = get_date()
                inci['time'] = get_time()
                db.insert(inci)

                NOTIF_BODY = '<b>New Possible Fire Incident</b>' + \
                    '\nID: ' + empty_fill(inci['id']) + \
                    '\nName: ' + empty_fill(inci['name']) + \
                    '\nType: ' + empty_fill(inci['type']) + \
                    '\nLocation: ' + empty_fill(inci['location']) + \
                    '\nComment: ' + empty_fill(inci['comment']) + \
                    '\nAcres: ' + empty_fill(inci['acres']) + \
                    '\nResources: ' + empty_fill(inci['resources'])

                if 'x' in inci and 'y' in inci:
                    NOTIF_BODY += create_gmaps_url(inci)

                telegram(NOTIF_BODY, 'high')

# ------------------------------------------------------------------------------

date_now = datetime.datetime.now()

"""
Send daily recap if time is 23:59
"""
if str(date_now.hour) + ':' + str(date_now.minute) == '23:59':
    logger.debug('Generating daily recap')
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
