import requests

send_data = {
    "from": {"email": "mark@landmark717.com"},
    "personalizations": [{
        "to": [
            {"email": "mark@landmark717.com"}
        ]
    }],
    "subject": "Hello",
    "content": [{"type": "text/plain", "value": "Heya!"}]
}

print(requests.post(
    'https://api.sendgrid.com/v3/mail/send',
    timeout=10,
    allow_redirects=False,
    headers={
        "Content-Type":"application/json",
        "Authorization": "Bearer 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"
    },
    json = send_data
).content)
