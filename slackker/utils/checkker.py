import sys
import time
import http.client as httplib
from slack_sdk import WebClient
from datetime import datetime, timezone
from slackker.utils.ccolors import colors

def _now():
    return datetime.utcnow().replace(tzinfo=timezone.utc)

# Check whether server is still alive.
def check_internet(url="www.slack.com", verbose=2):
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
                colors.prCyan(f"[slackker] {_now().strftime('%d-%m-%Y %H:%M')} Connection to slack Server successful!")
        except:
            status=False
            colors.prYellow(f"[slackker] ERROR: {_now().strftime('%d-%m-%Y %H:%M')} Connection to Slack server failed. Trying again in 60 sec..[attempt {counter}]")
            time.sleep(sleepinsec)
            counter=counter+1

    if counter>1:
        if verbose>=2:
        	colors.prCyan(f"[slackker] {_now().strftime('%d-%m-%Y %H:%M')} re-established connection to Slack server after {counter} attempts.")

    return status

# Check whether server is still alive at the end of epoch if not skip the training. 
def check_internet_epoch_end(url="www.slack.com"):
    counter=1
    status=False
    sleepinsec=10

    while status is False and counter <= 3:
        conn = httplib.HTTPConnection(url, timeout=5)
        try:
            conn.request("HEAD", "/")
            conn.close()
            status=True
        except:
            status=False
            colors.prYellow(f"[slackker] ERROR: {_now().strftime('%d-%m-%Y %H:%M')} Connection to Slack server failed. Trying again in 10 sec..[attempt {counter}]")
            time.sleep(sleepinsec)
            counter=counter+1
                
    if counter <= 3 and counter > 1:
        colors.prCyan(f"[slackker] {_now().strftime('%d-%m-%Y %H:%M')} re-established connection to Slack server after {counter} attempts.")
    elif counter > 3:
        colors.prCyan(f'[slackker] Skipping report update to slack due to connection failure. {counter} attempts made before skipping')

    return status, counter


def slack_connect(token, verbose=2):

	status = False

	try:
		client = WebClient(token=token)
		api_response = client.api_test()
		status = True
		if verbose >= 2:
			colors.prCyan(f"[slackker] Connection to slack API successful! {api_response}")

	except Exception as e:
		status = False
		colors.prRed(f"[slackker] ERROR: Invalid slack API token: {e}")

	return status
