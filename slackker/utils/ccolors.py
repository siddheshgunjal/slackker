class colors:
	# Assign colors to logging statements
	def prRed(sent):
		print("\033[91m {}\033[00m" .format(sent))

	def prCyan(sent):
		print("\033[96m {}\033[00m" .format(sent))

	def prYellow(sent):
		print("\033[93m {}\033[00m" .format(sent))