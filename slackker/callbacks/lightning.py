import numpy as np
from lightning.pytorch.callbacks import Callback
from slack_sdk import WebClient
from datetime import datetime
import argparse
import slackker.utils.checkker as checkker
import slackker.utils.functions as functions
from slackker.utils.ccolors import colors
import requests

class slackUpdate(Callback):
	"""Custom Lightning callback that posts to Slack while training a neural network"""
	def __init__(self, token, channel, modelName, train_logs=None, val_logs=None, export="png", sendPlot=True, verbose=0):
		
		if token is None:
			colors.prRed('[slackker] Please enter Valid Slack API Token.')
			return

		server = checkker.check_internet(url="www.slack.com", verbose=verbose)
		api = checkker.slack_connect(token=token, verbose=verbose)

		if server and api:
			self.client = WebClient(token=token)
			self.channel = channel
			self.modelName = modelName
			self.export = export
			self.sendPlot = sendPlot
			self.verbose = verbose
			self.train_logs = train_logs

			if export is not None:
				pass
			else:
				raise argparse.ArgumentTypeError("[slackker] 'export' argument is missing (supported formats: eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff)")

			if train_logs is None and val_logs is None:
				raise argparse.ArgumentTypeError("[slackker] Provice at least 1 log type, either 'train_logs' or 'val_logs' for logging purpose.")
			else:
				if type(train_logs) is not list and train_logs is not None:
					raise argparse.ArgumentTypeError("[slackker] 'train_logs' is a list type of argument, add values in '[]'")
				else:
					pass
				if type(val_logs) is not list and val_logs is not None:
					raise argparse.ArgumentTypeError("[slackker] 'val_logs' is a list type of argument, add values in '[]'")
				else:
					pass

	# Called when training starts
	def on_train_start(self, trainer, pl_module):
		functions.slack.report_stats(
			client=self.client,
			channel=self.channel,
			text=f'Training on "{self.modelName}" started at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
			verbose=self.verbose)

		self.training_logs = {}
		self.n_epochs = 0

	# Called when epoch ends
	def on_train_epoch_end(self, trainer, pl_module):
		metrics = trainer.callback_metrics
		logs = self.train_logs

		custom_logs = {}
		toPrint = []

		[custom_logs.update({i:float(metrics[i])}) for i in logs]

		[self.training_logs.setdefault(key, []).append(value) for key, value in custom_logs.items()]

		colors.prYellow(custom_logs)
		colors.prYellow(self.training_logs)

		[toPrint.append(f"{i}: {metrics[i]:.4f}") for i in logs]

		message = f"Epoch: {self.n_epochs}, {', '.join(toPrint)}"

		# Check internet before sending update on slacj
		server, attempt = checkker.check_internet_epoch_end(url="www.slack.com")

		# If internet working send message else skip sending message and continue training.
		if server == True:
			functions.slack.report_stats(
				client=self.client,
				channel=self.channel,
				text=message,
				verbose=self.verbose)
		else:
			pass

		self.n_epochs += 1

	# Prepare and send report with graphs at the end of training.
	def on_train_end(self, trainer, pl_module):
		print(f'Training Finished for {self.modelName}')