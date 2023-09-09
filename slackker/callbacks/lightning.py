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
	"""Custom Keras callback that posts to Slack while training a neural network"""
	def __init__(self, modelName, export="png", sendPlot=True, verbose=0):
		
		self.modelName = modelName
		self.export = export
		self.sendPlot = sendPlot
		self.verbose = verbose

	# Called when training starts
	def on_train_start(self, trainer, pl_module):
		print('Training Started')
		print(self.modelName)

	# Called when epoch ends
	def on_train_epoch_end(self, trainer, pl_module):
		metrics = trainer.callback_metrics
		print(f"Epoch: {trainer.current_epoch}, Train Loss: {metrics['train_loss']:.4f}, Train Accuracy: {metrics['train_acc']:.4f}")

	# Prepare and send report with graphs at the end of training.
	def on_train_end(self, trainer, pl_module):
		print('Training Finished')
		print(self.modelName)
