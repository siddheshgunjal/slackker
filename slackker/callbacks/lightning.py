import numpy as np
from lightning.pytorch.callbacks import Callback
from slack_sdk import WebClient
from datetime import datetime
import slackker.utils.checkker as checkker
import slackker.utils.functions as functions
from slackker.utils.ccolors import colors
import requests

class slackUpdate(Callback):
	"""Custom Lightning callback that posts to Slack while training a neural network"""
	def __init__(self, token, channel, modelName, trackLogs=None, monitor=None, export="png", sendPlot=True, verbose=0):
		
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
			self.trackLogs = trackLogs
			self.monitor = monitor

			if export is not None:
				pass
			else:
				raise argparse.ArgumentTypeError("[slackker] 'export' argument is missing (supported formats: eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff)")

			if trackLogs is None:
				colors.prRed("[slackker] Provice at least 1 log type for sending update.")
				exit()
			else:
				if type(trackLogs) is not list and trackLogs is not None:
					colors.prRed("[slackker] 'trackLogs' is a list type of argument, add values in '[]'")
					exit()
				else:
					pass

			if monitor is not None:
				if monitor not in trackLogs:
					colors.prRed("[slackker] Couldn't find Argument 'monitor' value in 'trackLogs' provided")
					exit()
				else:
					pass
			else:
				colors.prYellow("[slackker] Argument 'monitor' not provided, will skip reporting Best Epoch")

	# Called when training starts
	def on_fit_start(self, trainer, pl_module):
		functions.slack.report_stats(
			client=self.client,
			channel=self.channel,
			text=f'Training on "{self.modelName}" started at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
			verbose=self.verbose)

		self.training_logs = {}
		self.n_epochs = 0

	# Called when every training epoch ends
	def on_train_epoch_end(self, trainer, pl_module):
		metrics = trainer.callback_metrics
		logs = self.trackLogs

		custom_logs = {}
		toPrint = []

		[custom_logs.update({i:float(metrics[i])}) for i in logs]

		[self.training_logs.setdefault(key, []).append(value) for key, value in custom_logs.items()]

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
	def on_fit_end(self, trainer, pl_module):
		if self.monitor is not None:
			for key, value in self.training_logs.items():
				if "loss" in self.monitor.lower():
					if self.monitor.lower() in key.lower():
						# print(f"Lowest loss value is {min(value)}")
						message = f"Trained for {self.n_epochs} epochs. Best epoch was, Epoch {np.argmin(value)}"
				elif "acc" in self.monitor.lower():
					if self.monitor.lower() in key.lower():
						# print(f"Highest accuracy value is{max(value)}")
						message = f"Trained for {self.n_epochs} epochs. Best epoch was, Epoch {np.argmax(value)}"
		else:
			message = f"Trained for {self.n_epochs} epochs. Argument 'monitor' was not provided, skipped reporting Best Epoch"

		functions.slack.report_stats(
			client=self.client,
			channel=self.channel,
			text=message,
			verbose=self.verbose)

		functions.slack.lightning_plot_history(modelName=self.modelName,
			export=self.export,
			client=self.client,
			channel=self.channel,
			sendPlot=self.sendPlot,
			training_logs=self.training_logs,
			verbose=self.verbose)	