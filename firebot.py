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
import json
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
MOCK_DATA = False
logger.setLevel(logging.ERROR)

exec_path = os.path.dirname(os.path.realpath(__file__))
db = tinydb.TinyDB(exec_path + '/db.json')

secrets = dotenv_values(".env")

config = {
    "wildcad_url": "http://www.wildcad.net/WCCA-" + secrets['NF_IDENTIFIER'] + \
        "recent.htm"
}

# ------------------------------------------------------------------------------

for arg in sys.argv:
    if arg == 'debug':
        DEBUG = True
        logger.setLevel(logging.DEBUG)
        logger.debug('Debug log level')

    if arg == 'mock':
        MOCK_DATA = True
        config['wildcad_url'] = '.development/wildcad_mock_data.htm'
        logger.debug('Using mock data: %s', config['wildcad_url'])

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

# ------------------------------------------------------------------------------

def format_geo(input_str):
    """
    Formats dirty geolocation string to fit proper GPS/DM/DMM format
    """
    input_str = str(input_str)
    input_str = input_str.replace(' ', '')
    input_str = input_str.replace('-', '')

    return input_str

# ------------------------------------------------------------------------------

def utf8_encode(input_str):
    """
    Prepares a string for downstream curl by making ASCII Hexadecimal
    replacements. EG: "# 123" becomes "%23 123"
    """
    return urllib.parse.quote_plus(input_str)

# ------------------------------------------------------------------------------

def telegram(message_str, priority_str):
    """
    Output: Telegram Channel
    """
    chat_id = secrets['TELEGRAM_CHAT_ID']

    if priority_str == 'major':
        chat_id = secrets['TELEGRAM_SPECIAL_CHAT_ID']

    message_str = utf8_encode(message_str)
    url = 'https://api.telegram.org/' + secrets['TELEGRAM_BOT_ID'] + ':' + \
        secrets['TELEGRAM_BOT_SECRET'] + '/sendMessage?chat_id=' + \
        chat_id + '&text=' + message_str + '&parse_mode=html&disable_web_page_preview=true'

    if priority_str == 'low':
        url = url + '&disable_notification=true'

    if DEBUG is True:
        logger.debug('Telegram URL: %s', url)

    if('False' in [
        secrets['TELEGRAM_BOT_ID'],
        secrets['TELEGRAM_BOT_SECRET'],
        chat_id
    ]):
        logger.error('A required var is not set in .env! Cannot send Telegram message')
        return False

    return requests.get(url, timeout=10, allow_redirects=False)

# ------------------------------------------------------------------------------

def process_wildcad():
    """
    Data source: Wildcad
    """
    if MOCK_DATA:
        with open(config['wildcad_url'], 'r', encoding="utf-8") as file:
            page = file.read()
    else:
        try:
            page = requests.get(config['wildcad_url'])
        except requests.exceptions.RequestException as error:
            logger.error('Could not reach Wildcad URL %s', config['wildcad_url'])
            logger.error(error)
            sys.exit(1)

        if not page.content or page.headers['Content-Length'] == 0 or '</HTML>' not in page.content:
            logger.error('Wildcad payload empty %s', config['wildcad_url'])
            sys.exit(1)
        else:
            page = page.content

    tree = html.fromstring(page)
    rows = tree.xpath('//tr')
    data = []
    inci_list = []
    for row in rows:
        data.append([c.text_content() for c in row.getchildren()])

    counter = 0
    checked_ids = []

    for item in data:
        counter = counter + 1
        if counter > 2 and item[1] not in checked_ids: # Skip header rows
            item_date = item[0].split('/')
            item_date_split = item_date[2].split(' ')
            item_date[2] = item_date_split[0]
            item_date.append(item_date_split[1])
            checked_ids.append(item[1])

            item_dict = {
                'time_created': empty_fill(item[0]), # "Date" field
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

    return inci_list

# ------------------------------------------------------------------------------

def pad_date_prop(input_int):
    """
    Pads a given int. EG: 7 becomes 07
    """
    return str(f'{input_int:02}')

# ------------------------------------------------------------------------------

def get_date():
    """
    Returns a MM/DD/YYYY string, with padding/fill, EG: 08/01/2022
    """
    now = datetime.datetime.now()
    return str(pad_date_prop(now.month) + '/' + pad_date_prop(now.day) + '/' + str(now.year))

# ------------------------------------------------------------------------------

def empty_fill(input_str):
    """
    Returns an empty string when given a useless string, to maintain one-per-line
    formatting in notification messages
    """
    if len(input_str) < 1 or input_str == '.':
        return ''

    return input_str

# ------------------------------------------------------------------------------

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
            and key != 'time_created' # No sense in notifying on this one
        ):
            changed.append({
                "name": key,
                "new": inci_dict[key],
                "old": inci_db_entry_dict[key]
            })

    if changed:
        return changed

    return False

# ------------------------------------------------------------------------------

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
        return True

    return False

# ------------------------------------------------------------------------------

def process_major_alerts():
    """
    If major incident, report it to special channel as well. For this to work,
    a new secret named TELEGRAM_SPECIAL_CHAT_ID needs to be defined in .env
    """
    if 'TELEGRAM_SPECIAL_CHAT_ID' not in secrets:
        logger.debug('TELEGRAM_SPECIAL_CHAT_ID not defined in secrets')
        return False

    inci_db = tinydb.Query()

    for inci in db.all():
        if(
            inci['name'] != 'New'
            and 'ANF-' in inci['name']
            and inci['resources'].strip() != ''
            and 'major_sent' not in inci
        ):
            logger.debug('New Major event detected: %s', inci['id'])

            this_notif_body = generate_notif_body(inci, 'major')

            if telegram(this_notif_body, 'major'):
                logger.debug('Adding flags.major_sent flag')
                inci['major_sent'] = True
                db.update(inci, inci_db.id == inci['id'])

    return True

# ------------------------------------------------------------------------------

def generate_notif_body(inci_dict, priority_str):
    """
    Returns a string usually passed into telegram() with a prepared message
    """
    notify_title = 'New Possible Fire Incident'

    if priority_str == 'special':
        notify_title = 'New MAJOR Fire'

    notif_body = '<b>' + notify_title + '</b>' + \
                '\nID: ' + empty_fill(inci_dict['id']) + \
                '\nName: ' + empty_fill(inci_dict['name']) + \
                '\nType: ' + empty_fill(inci_dict['type']) + \
                '\nLocation: ' + empty_fill(inci_dict['location']) + \
                '\nCreated: ' + empty_fill(relative_time(inci_dict['time_created'])) + \
                '\nComment: ' + empty_fill(inci_dict['comment']) + \
                '\nAcres: ' + empty_fill(inci_dict['acres']) + \
                '\nResources: ' + empty_fill(inci_dict['resources'])

    if 'x' in inci_dict and 'y' in inci_dict:
        notif_body += '\nMaps: ' + create_gmaps_url(inci_dict) + ' - ' + \
            create_applemaps_url(inci_dict) + ' - ' + create_waze_url(inci_dict)

    return notif_body

# ------------------------------------------------------------------------------

def relative_time(input_str):
    """
    Parses a date/time like "08/10/2022 16:08" into "Aug 10 '22, 16:08"
    """
    return datetime.datetime.strptime(input_str, '%m/%d/%Y %H:%M').strftime('%b %e \'%y, %H:%S PT')

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
    return '<a href="https://www.google.com/maps/search/' + \
        str(convert_gps_to_decimal(inci_dict['x'])) + ',-' + \
        str(convert_gps_to_decimal(inci_dict['y'])) + '?sa=X">Google Maps</a>'

# ------------------------------------------------------------------------------

def create_applemaps_url(inci_dict):
    """
    Returns a Google Maps URL for given X/Y coordinates
    """
    return '<a href="http://maps.apple.com/?ll=' + \
        str(convert_gps_to_decimal(inci_dict['x'])) + ',-' + \
        str(convert_gps_to_decimal(inci_dict['y'])) + '&q=' + inci_dict['id'] + '">Apple Maps</a>'

# ------------------------------------------------------------------------------

def create_gaigps_url(inci_dict):
    """
    Returns a GaiaGPS URL for given X/Y coordinates
    """
    return '<a href="https://www.gaiagps.com/map/?lat=' + \
        str(convert_gps_to_decimal(inci_dict['x'])) + '&lng=-' + \
        str(convert_gps_to_decimal(inci_dict['y'])) + '&z=6">Gaia GPS</a>'

# ------------------------------------------------------------------------------

def create_waze_url(inci_dict):
    """
    Returns a Waze URL for given X/Y coordinates
    """
    return '<a href="https://www.waze.com/ul?ll=' + \
        str(convert_gps_to_decimal(inci_dict['x'])) + '%2C-' + \
        str(convert_gps_to_decimal(inci_dict['y'])) + '">Waze</a>'

# ------------------------------------------------------------------------------

def granular_diff_list(inci_dict, inci_db_dict):
    """"
    Takes in fresh and stored dicts and computes granular diffs (additions,
    removals, and unchanged). Outputs an HTML formatted string
    """
    change_list_added = []
    change_list_removed = []
    change_list_unchanged = []
    resource_list = []
    inci_db_dict = inci_db_dict[0]

    inci_dict = sorted(inci_dict['resources'].strip().split(' '))
    inci_db_dict = sorted(inci_db_dict['resources'].strip().split(' '))

    for resource in inci_dict:
        resource_list.append(resource.strip())

    for resource in inci_db_dict:
        if resource not in resource_list:
            resource_list.append(resource.strip())

    for resource in resource_list:
        if resource not in inci_db_dict: # Newly-added resource
            change_list_added.append(resource.strip())
        elif resource not in inci_dict: # Newly-removed resource
            change_list_removed.append('<s>' + resource.strip() + '</s>')
        else: # Unchanged resource
            change_list_unchanged.append(resource.strip())

    output_str = ''

    if len(change_list_added) > 0:
        output_str += '\n   <em>Added</em> : ' + (', '.join(change_list_added))

    if len(change_list_removed) > 0:
        output_str += '\n   <em>Removed</em> : ' + (', '.join(change_list_removed))

    if len(change_list_unchanged) > 0:
        output_str += '\n   <em>No Change</em>: ' + (', '.join(change_list_unchanged))

    resource_count = len(change_list_added) + len(change_list_unchanged)

    return 'Resources (' + str(resource_count) + '): ' + output_str

# ------------------------------------------------------------------------------

def convert_gps_to_decimal(input_int):
    """
    Converts GPS/DM/DMM to decimal geo-coordinates used by all mapping platforms
    """
    input_int = format_geo(input_int)

    def conv_dm(this_input_int):
        degrees = int(this_input_int) // 100
        minutes = this_input_int - 100*degrees
        return degrees, minutes

    def decimal_degrees(degrees, minutes):
        return degrees + minutes/60

    return round(decimal_degrees(*conv_dm(float(input_int))), 4)

# ------------------------------------------------------------------------------

def process_alerts(inci_list):
    """
    The heart of this script, this compares what we know with what
    we just got (DB contents vs. fresh WildWeb fetch):
        - Delete entry if it no longer passes the is_fire() criteria
        - Update entry if any of its properties have changed, sends diff. alert
        - Adds an entry if it is not found in the DB, sends initial alert
    """
    if len(inci_list) > 0:
        inci_db = tinydb.Query()
    else:
        return False

    for inci in inci_list:

        if db.search(inci_db.id == inci['id']):
            logger.debug('%s found in DB', inci['id'])
            inci_db_entry = db.search(inci_db.id == inci['id'])
            event_changes = event_has_changed(inci, inci_db_entry)

            if event_changes:
                logger.debug('%s has changed', inci['id'])
                send_maps_link = False

                # Event changed from type 'Wildfire'. Delete from DB
                if is_fire(inci) is False:
                    db.remove(inci_db.id == inci['id'])
                else:
                    db.update(inci, inci_db.id == inci['id'])

                if 'TELEGRAM_CHAT_ID' in secrets and 'original_message_id' in inci_db_entry[0]:
                    if '@' in secrets['TELEGRAM_CHAT_ID']:
                        telegram_chat_id_stripped = secrets['TELEGRAM_CHAT_ID'].replace('@', '')
                    else:
                        telegram_chat_id_stripped = secrets['TELEGRAM_CHAT_ID']
                    notif_body = 'Dispatch changed <b><a href="https://t.me/' + \
                        telegram_chat_id_stripped + '/' + \
                        str(inci_db_entry[0]['original_message_id']) + '">' + \
                        inci['id'] + '</a></b>'
                else:
                    notif_body = 'Dispatch changed <b>' + inci['id'] + '</b>'

                for change in event_changes:
                    if change['name'] == 'resources':
                        notif_body += '\n' + granular_diff_list(inci, inci_db_entry)
                    else:
                        notif_body += '\n' + uppercase_first(change['name']) + ': ' + \
                        '<s>' + change['old'] + '</s> ' + change['new']

                    if change['name'] == 'x' or change['name'] == 'y':
                        send_maps_link = True

                if send_maps_link is True:
                    notif_body += '\nMaps: ' + create_gmaps_url(inci)  + ' - ' + \
                        create_applemaps_url(inci) + ' - ' + create_waze_url(inci)

                telegram(notif_body, 'low')
            else:
                logger.debug('%s unchanged', inci['id'])
        else:
            if is_fire(inci): # First time incident is seen, insert into DB
                logger.debug('%s not found in DB, new inci', inci['id'])
                db.insert(inci)

                telegram_json = telegram(generate_notif_body(inci, 'normal'), 'high')

                # Message sent successfully, store Telegram message ID
                if telegram_json is not False:
                    telegram_json = json.loads(telegram_json.content)
                    inci['original_message_id'] = telegram_json['result']['message_id']
                    db.update(inci, inci_db.id == inci['id'])

    return True

# ------------------------------------------------------------------------------

def process_daily_recap():
    """
    Send daily recap if time is 23:59
    """
    date_now = datetime.datetime.now()

    if str(date_now.hour) + ':' + str(date_now.minute) == '23:59':
        logger.debug('Generating daily recap')
        inci_db = tinydb.Query()
        results = db.search(inci_db.time_created.search(get_date()))
        notif_body = '<b>Daily Recap:</b> '

        if results:
            if len(results) == 1:
                notif_body = notif_body + 'Today there was only <b>1</b> actual' + \
                    ' fire incident in ' + secrets['NF_IDENTIFIER']
            else:
                notif_body = notif_body + 'Today there were <b>' + str(len(results)) + \
                    '</b> actual fire incidents in ' + secrets['NF_IDENTIFIER']

            telegram(notif_body, 'low')

# ------------------------------------------------------------------------------

logger.debug('Running from %s', exec_path)

process_wildcad_inci_list = process_wildcad()
process_alerts(process_wildcad_inci_list)
process_major_alerts()
process_daily_recap()
