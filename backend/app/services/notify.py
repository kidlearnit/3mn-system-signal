import os, requests

TG_TOKEN = os.getenv('TG_TOKEN')
TG_CHAT_ID = os.getenv('TG_CHAT_ID')

def tg_send_text(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"})

def tg_send_photo(path, caption=""):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
    with open(path, 'rb') as f:
        requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": caption}, files={'photo': f})
