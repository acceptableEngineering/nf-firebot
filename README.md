# National Forest FireBot
A Python script that scrapes incidents for any National Forest using WildCAD's "WildWeb" feature, and posts fire-related findings in a given Telegram channel. A new text messaging (SMS) component provides a self-service portal for end-users via a web server. SMS messages are sent via Twilio.

---


New Incident Notifications:

![Screenshot](https://github.com/acceptableEngineering/nf-firebot/blob/main/.github/README-images/Telegram-Notif.png?raw=true)

Changed Incident Notifications/Diffs:*


![Screenshot](https://github.com/acceptableEngineering/nf-firebot/blob/main/.github/README-images/Telegram-Change-Notif.png?raw=true)

Daily Recaps (Optional):*


![Screenshot](https://github.com/acceptableEngineering/nf-firebot/blob/main/.github/README-images/Telegram-Daily-Recap.png?raw=true)


\* Posts as a low priority notification (no push notification). See: `disable_notification` [in the Telegram docs](https://core.telegram.org/bots/api#sendmessage)

---

### Prerequisite
Before cloning this repo, you'll want to see if your forest of interest is listed on [WildWeb](http://www.wildcad.net/WildCADWeb.asp)

---

### Input
- WildWeb

---

### Output
- Telegram Channel(s)
- SMS (via Twilio)

---

### How it Works

![Diagram](https://github.com/acceptableEngineering/nf-firebot/blob/main/.github/README-images/FireBot-Diagram.png?raw=true)

---

### Scraper/Sender Setup
Using virtualenv:
```
$ pip3 install -r requirements.txt
```
Create a `.env` file with your National Forest ID and secret values. You can use one set of settings in a Production environment, and one locally.
```
NF_IDENTIFIER=ANF
TELEGRAM_BOT_ID=botXXXXXXXXXX
TELEGRAM_BOT_SECRET=XXXX-XXXXXXXXXXXXXXX-XXXXXXXXX-XXX
TELEGRAM_CHAT_ID=-XXXXXXXXXXXXX
```

Setting up a Telegram channel, and fetching credentials: [Bots: An introduction for developers](https://core.telegram.org/bots/#3-how-do-i-create-a-bot)

---

### Web Server (Self-Service), SMS Setup
You can use Twilio Studio to cut down on the parsing, validation, and conditionals that usually come along with an interactive SMS gateway:


---

### Execution
```
python3 fireboy.py [debug] [mock]
```

Bare-bones, no options passed. Good for production use:
```
python3 firebot.py
```

Optional arguments list:

- `debug`: Dev/debug mode which adds many helpful entries to `firebot-log.json`

- `mock`: Uses local mock data found in `.development/` instead of fetching via web

Argument usage/a good local dev example:
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
This code and GitHub project were created after meeting my own needs for monitoring action in Angeles National Forest. You can see "ANF FireBot" in action here:
https://t.me/firebotanf

And read more about it here:
https://landmark717.com/blog/telegram-firebot.html

---

### Development, Contributing
There are several ways to contribute to this project. You can provide feedback, ideas, and suggestions. Or if you want to get your hands dirty, you are welcome to fork this repo and propose changes through a Pull Request! You can setup your own sandbox Telegram channel(s) or message me and I can add you to the existing ones: mark@landmark717.com

---

### Disclaimer
As many first responders are now using ANF-FireBot (see "Live Demo" above):

THIS FREE SOFTWARE AND THE FULLY-OPERATIONAL INSTALLATION ("ANF FIREBOT") ARE PROVIDED WITHOUT WARRANTY WHATSOEVER. THE DEVELOPER(S), VOLUNTEER(S), AND OTHERS CANNOT BE HELD RESPONSIBLE FOR FALSE REPORTS, MISSED EVENTS/REPORTS, SERVICE OUTAGES, OR OTHER ISSUES. YOU SHOULD CONTINUE TO FOLLOW YOUR ORGANIZATION'S PROTOCOLS, TREATING THE INFORMATION PROVIDED BY FIREBOT AS ANECDOTAL.
