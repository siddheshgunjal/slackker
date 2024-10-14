import time
import requests
import http.client as httplib
from slack_sdk import WebClient
from datetime import datetime
from slackker.utils.ccolors import colors

# Check whether server is still alive.
def check_internet(url, verbose=2):
    counter=1
    status=False
    sleepinsec=60

    while status is False:
        conn = httplib.HTTPConnection(url, timeout=5)
        try:
            conn.request("HEAD", "/")
            conn.close()
            status=True
            if verbose >= 2:
                colors.prCyan(f"[slackker] DEBUG: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')} Connection to '{url}' server successful!")
        except Exception:
            status=False
            colors.prYellow(f"[slackker] WARNING:: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')} Connection to '{url}' server failed. Please check your internet. Trying again in 60 sec..[attempt {counter}]")
            time.sleep(sleepinsec)
            counter=counter+1

    if counter>1:
        if verbose>=2:
            colors.prCyan(f"[slackker] DEBUG: {datetime.now().strftime('%d-%m-%Y %H:%M')} re-established connection to '{url}' server after {counter} attempts.")

    return status

# Check whether server is still alive at the end of epoch if not skip the training. 
def check_internet_epoch_end(url):
    counter=1
    status=False
    sleepinsec=10

    while status is False and counter <= 3:
        conn = httplib.HTTPConnection(url, timeout=5)
        try:
            conn.request("HEAD", "/")
            conn.close()
            status=True
        except Exception:
            status=False
            colors.prYellow(f"[slackker] WARNING: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')} Connection to '{url}' server failed. Trying again in 10 sec..[attempt {counter}]")
            time.sleep(sleepinsec)
            counter=counter+1
                
    if counter <= 3 and counter > 1:
        colors.prCyan(f"[slackker] DEBUG: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')} re-established connection to '{url}' server after {counter} attempts.")
    elif counter > 3:
        colors.prYellow(f'[slackker] WARNING: Skipping report update due to connection failure. {counter} attempts made before skipping')

    return status


def slack_connect(token, verbose=2):
    status = False

    try:
        client = WebClient(token=token)
        api_response = client.api_test()
        status = True
        if verbose >= 2:
            colors.prCyan(f"[slackker] DEBUG: Connection to slack API successful! {api_response}")
    except Exception as e:
        status = False
        colors.prRed(f"[slackker] ERROR: Invalid slack API token: {e}")

    return status

def get_telegram_chat_id(token, verbose=2):
    chat_id = False
    url = f"https://api.telegram.org/bot{token}/getUpdates"

    try:
        firstMsg = requests.get(url).json()
        chat_id = str(firstMsg["result"][0]["message"]["chat"]["id"])
        if verbose >= 2:
            colors.prCyan(f"[slackker] DEBUG: Connection to telegram API successful!")
            colors.prCyan(f"[slackker] DEBUG: Found chat with 'chat_id'={chat_id}")
    except Exception as e:
        chat_id = False
        colors.prRed(f"[slackker] ERROR: Could not connect to Telegram API: {e}")
        colors.prYellow(f"[slackker] SUGGESTION: Please send 'Hello' once to your bot to make it discoverable to slackker")

    return chat_id
