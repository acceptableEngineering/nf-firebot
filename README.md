# National Forest FireBot
A Python script that scrapes incidents for any National Forest using WildCAD's "WildWeb" feature, and posts fire-related findings in a given Telegram channel and/or text-em-all.com (mass SMS) account.

---

New Incident Notifications:

![Screenshot](https://github.com/acceptableEngineering/nf-firebot/blob/main/.github/README-images/Telegram-Notif.png?raw=true)

Changed Incident Notifications:*

![Screenshot](https://github.com/acceptableEngineering/nf-firebot/blob/main/.github/README-images/Telegram-Change-Notif.png?raw=true)

Daily Recaps (Optional):*

![Screenshot](https://github.com/acceptableEngineering/nf-firebot/blob/main/.github/README-images/Telegram-Daily-Recap.png?raw=true)

\* Posts as a low priority notification (no push notification). See: `disable_notification` [in the Telegram docs](https://core.telegram.org/bots/api#sendmessage)

---

### Diagram
![Diagram](https://github.com/acceptableEngineering/nf-firebot/blob/main/.github/README-images/Diagram.png?raw=true)

---

### Prerequisites
Before cloning this repo, you'll want to see if your National Forest of interest is listed on [WildWeb](http://www.wildcad.net/WildCADWeb.asp)

---

### Input
- WildWeb

---

### Output
- Telegram Channel
- text-em-all.com (mass SMS platform)

---

### Setup
Using virtualenv:
```
$ pip3 install -r requirements.txt
```
Create a `.env` file with your National Forest ID and secret values. You can use one set of settings in a Production setting, and another locally. If you choose not to use a feature, just leave its corresponding value(s) out of your `.env` file.
```
NF_IDENTIFIER=
TELEGRAM_BOT_ID=
TELEGRAM_BOT_SECRET=
TELEGRAM_CHAT_ID=
TEXTEMALL_OAUTH_KEY=
TEXTEMALL_OAUTH_SECRET=
TEXTEMALL_OAUTH_TOKEN=
URL_SHORT=
RUN_ENV=
```

Description of Values:

`NF_IDENTIFIER` - Required: your National Forest's designator as found in Prerequisites above. EG: ANF

`TELEGRAM_BOT_ID`, `TELEGRAM_BOT_SECRET`, and `TELEGRAM_CHAT_ID` - Optional: obtained by following [this guide to setup your own Telegram channel and bot](https://core.telegram.org/bots/#3-how-do-i-create-a-bot). You'll need these if you want to use the Telegram output component of FireBot

`TEXTEMALL_OAUTH_KEY`, `TEXTEMALL_OAUTH_SECRET`, and `TEXTEMALL_OAUTH_TOKEN` - Optional: obtained by setting up a text-em-all.com account and requesting API access. Required if you want to use the SMS component of FireBot

`URL_SHORT` - Optional: a publicly-accessible, fully-qualified domain name if you're going to use the URL shortener component

`RUN_ENV` - Optional: if you specify anything other than `production` here, text-em-all's Staging API will be called instead of their Production API. You can omit this value to have FireBot always call the Production API

---

### Execution
```
python3 fireboy.py [debug] [mock]
```

Bare-bones, no options passed, production use:
```
python3 firebot.py
```

Optional runtime arguments

- `debug`: Dev/debug mode which adds many helpful entries to `firebot-log.json`
- `mock`: Uses local mock data found in `.development/` instead of fetching via web. Useful for when WildWeb goes down, you're working offline, or don't want to flood them with unnecessary requests (be nice!)

A good local dev example
```
python3 firebot.py debug mock
```

---

### Automated Execution
You will likely want to run the script frequently. One simple approach is to create a Crontab entry with `crontab -e` if your distro supports it. Add:
```
* * * * * python3 firebot.py
```
The exact command used in our running Prod environment is an adminttedly scrappy approach, but also posts to a monitored CloudWatch metric:
```
* * * * * cd ~/nf-firebot/ && git pull -X theirs > /dev/null 2>&1 && python3 firebot.py live && /usr/bin/aws cloudwatch put-metric-data --metric-name Run --namespace ANF-Firebot --value 1 --region us-west-2
```

---

### Live Demo / Real-World Usage
This code and GitHub project were created after meeting my own needs for monitoring fire-related incidents in Angeles National Forest. You can see "ANF FireBot" in action [here](https://t.me/firebotanf) and [read more about it here](https://landmark717.com/blog/telegram-firebot.html).

---

### Development, Contributing
There are several ways to contribute to this project. You can provide feedback, ideas, and suggestions. Or if you want to get your hands dirty, you are welcome to fork this repo and propose changes through Pull Requests! You can setup your own sandbox Telegram channel(s) or message me and I can add you to the existing ones: mark@landmark717.com

---

### Disclaimer
To my delight and terror, many first responders are now relying on my own running instance of FireBot (see "Live Demo" above). As such, this seems important to include:

THIS FREE SOFTWARE AND THE FULLY-OPERATIONAL INSTALLATION ("ANF FIREBOT") ARE PROVIDED WITHOUT WARRANTY WHATSOEVER. THE DEVELOPER(S), VOLUNTEER(S), AND OTHERS CANNOT BE HELD RESPONSIBLE FOR FALSE REPORTS, MISSED EVENTS/REPORTS, SERVICE OUTAGES, LOSS OF LIFE, LOSS OF PROPERTY, OR OTHER ISSUES. YOU SHOULD CONTINUE TO FOLLOW YOUR ORGANIZATION'S PROTOCOLS, TREATING THE INFORMATION PROVIDED BY THIS SOFTWARE AND ANY RUNNING INSTANCES OF IT AS ANECDOTAL.
