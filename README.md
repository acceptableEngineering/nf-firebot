# National Forest FireBot
A Python script that scrapes incidents for any National Forest using WildCAD's "WildWeb" feature, and posts fire-related findings in a given Telegram channel (optional). An optional SMS/text messaging component provides a self-service portal for end-users via a web server. SMS messages are sent via Twilio.

---

## Live Demo / Real-World Usage
This code and GitHub project were created after meeting my own needs for monitoring action in Angeles National Forest. At the time of this writin, 136 people are making use of it, many of whom are wildland firefighters in our local national forest. You can see "ANF FireBot" in action here:
https://t.me/firebotanf

And read more about it here:
https://landmark717.com/blog/telegram-firebot.html

---

## Features

New Incident Notifications:

![Screenshot](https://github.com/acceptableEngineering/nf-firebot/blob/main/.github/README-images/Telegram-Notif.png?raw=true)


Changed Incident Notifications/Diffs:*

![Screenshot](https://github.com/acceptableEngineering/nf-firebot/blob/main/.github/README-images/Telegram-Change-Notif.png?raw=true)


Daily Recaps:
(Posts as a low priority notification/no push notification, via Telegram API `disable_notification`)

![Screenshot](https://github.com/acceptableEngineering/nf-firebot/blob/main/.github/README-images/Telegram-Daily-Recap.png?raw=true)

---

## Prerequisite
Before cloning this repo, you'll want to see if your forest of interest is listed on [WildWeb](http://www.wildcad.net/WildCADWeb.asp) OR already know if it uses the new `WildWebE.net` platform

---

## Input (Required)
- WildWeb

---

## Outputs (Optional)
- Telegram Channel
- SMS, via Twilio

---

## Our Setup

![Diagram](https://github.com/acceptableEngineering/nf-firebot/blob/main/.github/README-images/FireBot-Diagram.png?raw=true)

---

## Get Started
### Option #1: Quck Start
Assumes you have Python3 and pip3 installed already.
```
git clone git@github.com:acceptableEngineering/nf-firebot.git
cd nf-firebot
pip3 install -r requirements.txt
echo 'NF_IDENTIFIER=ANF' >> .env
python3 firebot.py
```

### Option #2: Customized Setup
Create a `.env` file with your National Forest ID and secret values. You can use one set of settings in a Production environment, and one locally.
```
NF_IDENTIFIER=ANF
WILDWEB_E=True
NF_WWE_IDENTIFIER=caancc
TELEGRAM_BOT_ID=botXXXXXXXXXX
TELEGRAM_BOT_SECRET=XXXX-XXXXXXXXXXXXXXX-XXXXXXXXX-XXX
TELEGRAM_CHAT_ID=-XXXXXXXXXXXXX
TWILIO_SID=XXXXXXXXXXXXX
TWILIO_AUTH_TOKEN=XXXXXXXXXXXXX
TWILIO_NUMBER=XXXXXXXXXXXXX
URL_SHORT=XXXX.X
```

### `.env` keys, defined
The only required key is `NF_IDENTIFIER`. It is also the only value that is not meant to be kept secret, so keep the values of the other keys to yourself! Also, if you run NF-FireBot without any/all of the keys for a feature, it will just run without attempting to use that feature.
- `NF_IDENTIFIER` (required): Your national forest's identifier as found [on WildCAD](http://www.wildcad.net/WildCADWeb.asp)
- `WILDWEB_E` (optional): Is your forest on the new WildWeb-E? Defaults to `False` (`wildcad.net`). If `True`, uses `wildwebe.net`
- `NF_WWE_IDENTIFIER` (optional, required if `WILDWEB_E` is set): If your forest is using WildWeb-E, set its ID here
- `TELEGRAM_BOT_ID` (optional): The ID of your Telegram bot (see below)
- `TELEGRAM_BOT_SECRET` (optional): The Secret for your Telegram bot (see below)
- `TELEGRAM_CHAT_ID` (optional): The Chat or User ID you want to post notifications to
    - Channel example: `@MyForestFireBot`
    - User DM example: `123456789`
- `TWILIO_SID` (optional): Your secret Twilio String Identifier, found in your Twilio dashboard
- `TWILIO_AUTH_TOKEN` (optional): Your secret Twilio API Auth Token, found in your Twilio dashboard
- `TWILIO_NUMBER` (optional): Your Twilio-registered phone number (EG: `+18184567890`)
- `URL_SHORT` (optional): The domain name you want to use as a URL shortener in SMS. (EG: `lm7.us`)

### Setup: Telegram (Optional)
Read about how to setup up a Telegram channel and bot/credentials: [Bots: An introduction for developers](https://core.telegram.org/bots/#3-how-do-i-create-a-bot)

### Setup: Twilio, for SMS Self-Service + URL Shortening (Optional)
This advanced feature adds SMS functionality that allows your end-users to manage their subscrptions with text messages. In our live implementation using Twilio Studio, we support:
- `Help Me`: provides a list of commands and email address to email for help
- `Subscribe`: subscribes the user to receive notifications (adds them to `db-contacts.json`)
- `Unsubscribe`: removes the user from the user DB (`db-contacts.json`) so they no longer receive notifications

Definitely use Twilio Studio to cut down on the parsing, validation, and conditionals that usually come along with an interactive SMS gateway. Here's what our live one looks like:

![Diagram](https://github.com/acceptableEngineering/nf-firebot/blob/main/.github/README-images/Twilio-Studio.png?raw=true)

---

### Execution Options
```
python3 firebot.py [debug] [mock]
```

#### Bare-bones
No options passed. Good for production use:
```
python3 firebot.py
```

#### Optional arguments:
- `debug`: Dev/debug mode which adds many helpful entries to `firebot-log.json`
- `mock`: Uses local mock data found in `.development/` instead of fetching via web

#### Dev Example:
```
python3 firebot.py debug mock
```

---

### Automated Execution
You will likely want to run the script frequently. One simple approach is to create a Crontab entry with `crontab -e` if your distro supports it. Add:
```
* * * * * python3 firebot.py
```
The exact command used in our running Prod environment is an adminttedly scrappy approach, but it works well, and posts to a monitored CloudWatch metric:
```
* * * * * cd ~/nf-firebot/ && git pull -X theirs > /dev/null 2>&1; python3 firebot.py && /usr/bin/aws cloudwatch put-metric-data --metric-name Run --namespace ANF-Firebot --value 1 --region us-west-2
```

---

### Development, Contributing
There are several ways to contribute to this project. You can provide feedback, ideas, and suggestions. Or if you want to get your hands dirty, you are welcome to fork this repo and propose changes through a Pull Request! You can setup your own sandbox Telegram channel(s) or message me and I can add you to the existing ones: mark@landmark717.com

---

### Disclaimer
As many first responders are now using ANF-FireBot (see "Live Demo" above):

THIS FREE SOFTWARE AND THE FULLY-OPERATIONAL INSTALLATION ("ANF FIREBOT") ARE PROVIDED WITHOUT WARRANTY WHATSOEVER. THE DEVELOPER(S), VOLUNTEER(S), AND OTHERS CANNOT BE HELD RESPONSIBLE FOR FALSE REPORTS, MISSED EVENTS/REPORTS, SERVICE OUTAGES, OR OTHER ISSUES. YOU SHOULD CONTINUE TO FOLLOW YOUR ORGANIZATION'S PROTOCOLS, TREATING THE INFORMATION PROVIDED BY FIREBOT AS ANECDOTAL.

NF-FIREBOT IS FREE TO USE, OPEN SOURCE SOFTWARE AND IS NOT AFFILIATED WITH WILDCAD, WILDWEB, WILDWEB-E, ETC.
