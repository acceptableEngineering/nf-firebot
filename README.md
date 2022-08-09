# National Forest FireBot
A Python script that scrapes incidents for any National Forest using WildCAD's "WildWeb" feature, and posts fire-related findings in a given Telegram channel.


New Incident Notifications:
![Screenshot](https://github.com/acceptableEngineering/nf-firebot/blob/main/.github/README-images/Telegram-Notif.png?raw=true)

Changed Incident Notifications:*
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
- Telegram Channel

---

### Setup
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

### Execution
```
$ python3 firebot.py debug # Dev/debug mode
```
```
$ python3 firebot.py # Production mode
```

---

### Automatic Execution
You will likely want to run the script frequently. One simple approach is to create a Crontab entry with `crontab -e` if your distro supports it. Add:
```
* * * * * python3 firebot.py
```
The exact command used in our running Prod environment is an adminttedly scrappy approach, but also posts to a monitored CloudWatch metric:
```
* * * * * cd ~/nf-firebot/ && git pull -X theirs > /dev/null 2>&1 && python3 firebot.py live && /usr/bin/aws cloudwatch put-metric-data --metric-name Run --namespace ANF-Firebot --value 1 --region us-west-2
```

---

### Live Demo
This code and GitHub project were created after meeting my own needs for monitoring action in Angeles National Forest. You can see "ANF FireBot" in action here:
https://t.me/firebotanf

And read more about it here:
https://landmark717.com/blog/telegram-firebot.html

---

### Development, Contributing
There are several ways to contribute to this project. You can provide feedback, ideas, and suggestions. Or if you want to get your hands dirty, you are welcome to fork this repo and propose changes through a Pull Request!

---

### Disclaimer
As some first responders are now using ANF-FireBot (see "Live Demo" above):

> THIS FREE SOFTWARE AND THE FULLY-OPERATIONAL INSTALLATION ("ANF FIREBOT") ARE PROVIDED WITHOUT WARRANTY WHATSOEVER. THE DEVELOPER(S), VOLUNTEER(S), AND OTHERS CANNOT BE HELD RESPONSIBLE FOR FALSE REPORTS, MISSED EVENTS/REPORTS, SERVICE OUTAGES, OR OTHER ISSUES. YOU SHOULD CONTINUE TO FOLLOW YOUR ORGANIZATION'S PROTOCOLS, TREATING THE INFORMATION PROVIDED BY FIREBOT AS ANECDOTAL.
