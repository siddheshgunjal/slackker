import sys
import time
# import logging
import http.client as httplib
from slack_sdk import WebClient
from datetime import datetime, timezone

# logging.basicConfig(level=logging.DEBUG)

def _now():
    return datetime.utcnow().replace(tzinfo=timezone.utc)


def check_internet(url="www.slack.com", verbose=3):
    # Check whether server is still alive.
    counter=1
    status=False
    sleepinsec=10

    while status is False:
        conn = httplib.HTTPConnection(url, timeout=5)
        try:
            conn.request("HEAD", "/")
            conn.close()
            status=True
            if verbose >= 2:
            	print("[slackker] Connection to slack Server successful!")
        except:
            status=False
            print(f"[slackker] >ERROR: {_now().strftime('%d-%m-%Y %H:%M')} Connection to Slack server failed. Trying again in 10 sec..[attempt {counter}]")
            time.sleep(sleepinsec)
            counter=counter+1

    if counter>1:
        if verbose>=2:
        	print(f"[slackker] {_now().strftime('%d-%m-%Y %H:%M')} re-established connection to Slack server after {counter} attempts.")

    return status


def slack_connect(token, verbose=2):

	status = False

	try:
		client = WebClient(token=token)
		api_response = client.api_test()
		status = True
		if verbose >= 2:
			print("[slackker] Connection to slack API successful! ", api_response)

	except Exception as e:
		status = False
		print(f"[slackker] >ERROR: Invalid slack API token: {e}")

	return status


# slack_connet("xoxp-4615231545733-4603743143687-P0ngiBAuMsp512V5DafBdhd", verbose=2)
# check_internet(verbose=2)