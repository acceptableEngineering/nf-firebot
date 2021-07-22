# National Forest FireBot
A Python script that scrapes incidents for any National Forest using WildCAD's "WildWeb" feature


New Incident Notifications:
![Screenshot](https://github.com/acceptableEngineering/nf-firebot/blob/main/.github/README-images/Telegram-Notif.png?raw=true)

Changed Incident Notifications:
![Screenshot](https://github.com/acceptableEngineering/nf-firebot/blob/main/.github/README-images/Telegram-Change-Notif.png?raw=true)

Optional Daily Recaps:
![Screenshot](https://github.com/acceptableEngineering/nf-firebot/blob/main/.github/README-images/Telegram-Daily-Recap.png?raw=true)

---

### Prerequisite
Before cloning this repo, you'll want to see if your forest of interest is listed on [WildWeb](http://www.wildcad.net/WildCADWeb.asp)

---

### Input
- WildWeb
- Coming soon: NIFC via ArcGIS

---

### Output
- Telegram Channel

---

### Setup
Using virtualenv:
```
$ pip3 install requirements.txt
```
Create a `.env` file with your National Forest ID and secret values:
```
NF_IDENTIFIER=ANF
TELEGRAM_BOT_ID=botXXXXXXXXXX
TELEGRAM_BOT_SECRET=XXXX-XXXXXXXXXXXXXXX-XXXXXXXXX-XXX
TELEGRAM_CHAT_ID=-XXXXXXXXXXXXX
```

Setting up a Telegram channel, and fetching credentials: [Bots: An introduction for developers](https://core.telegram.org/bots/#3-how-do-i-create-a-bot)

---

### Execution
```
$ python3 firebot.py # Dev/debug mode
```
```
$ python3 firebot.py live # Production mode
```