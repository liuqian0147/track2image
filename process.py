from html import parser
import os, shutil
from garmin_fit_sdk import Decoder, Stream
from datetime import datetime, timezone, timedelta
import numpy as np
import pandas as pd
import argparse

def pre_process (filename, messages):
	name, _ = os.path.splitext (filename)

	with open(f'{name}.txt', "wt") as f:
		f.write (str(messages['session_mesgs']))

	if 'record_mesgs' in messages:
		df = pd.DataFrame(messages['record_mesgs'])
		df.to_csv (f"{name}.csv", index=False)

def main ():
	parser = argparse.ArgumentParser(description='Extract and process fit files.')
	parser.add_argument('folder', type=str, help='Folder containing fit files to process')
	args = parser.parse_args()
	input_path = args.folder

	if not os.path.isdir(input_path):
		print (f"{input_path} not a folder.")
		return

	output_path = './tracks/'
	if not os.path.isdir(output_path):
		os.mkdir (output_path)

	targets = []
	for f in os.listdir (input_path):
		_, ext = os.path.splitext (f)

		if ext.lower() == '.fit':
			targets.append (os.path.join(input_path, f))
		else:
			print (f"{f} not a fit file, ignore.")

	processing = 0
	for filename in targets:
		_, f = os.path.split(filename)
		
		stream = Stream.from_file(filename)
		decoder = Decoder(stream)
		messages, _ = decoder.read()

		event_date = messages["activity_mesgs"][0]['timestamp'].replace(tzinfo=timezone.utc).astimezone(tz=None)

		t_dir = os.path.join(output_path, str(event_date.year))
		if not os.path.isdir(t_dir):
			os.mkdir (t_dir)

		t_file = os.path.join(t_dir, f)
		print (f"{processing + 1} / {len(targets)} - {filename}")
		if not os.path.isfile(t_file):
			pre_process (t_file, messages)
		processing += 1

if __name__ == "__main__":
	main ()