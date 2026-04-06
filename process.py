import os, shutil
from garmin_fit_sdk import Decoder, Stream
from datetime import datetime, timezone, timedelta
import numpy as np
import pandas as pd

input_path = "./coros_history_20250109/"

def pre_process (filename, messages):
	#print (messages['session_mesgs'])
	
	name, ext = os.path.splitext (filename)

	with open(f'{name}.txt', "wt") as f:
		f.write (str(messages['session_mesgs']))
		# data = eval (f.read())

	if 'record_mesgs' in messages:
		df = pd.DataFrame(columns=['timestamp', 'lat', 'long', 'distance', 'altitude'])
		for r in messages['record_mesgs']:
			latitude = r['position_lat'] if 'position_lat' in r else 0
			longitude = r['position_long'] if 'position_long' in r else 0
			distance = r['distance'] if 'distance' in r else 0
			altitude = r['altitude'] if 'altitude' in r else 0
			df.loc[len(df)] = [r['timestamp'], latitude, longitude, distance, altitude]

		df.sort_values(by='timestamp', inplace=True)
		df.to_csv (f"{name}.csv", index=False)

def main ():

	output_path = './tracks/'
	if not os.path.isdir(output_path):
		os.mkdir (output_path)

	targets = []
	for f in os.listdir (input_path):
		name, ext = os.path.splitext (f)

		if ext.lower() == '.fit':
			targets.append (os.path.join(input_path, f))
		else:
			print (f"{f} not a fit file, ignore.")

	completed = 0
	for filename in targets:
		p, f = os.path.split(filename)
		
		stream = Stream.from_file(filename)
		decoder = Decoder(stream)
		messages, errors = decoder.read()

		event_date = messages["activity_mesgs"][0]['timestamp'].replace(tzinfo=timezone.utc).astimezone(tz=None)

		t_dir = os.path.join(output_path, str(event_date.year))
		if not os.path.isdir(t_dir):
			os.mkdir (t_dir)

		t_file = os.path.join(t_dir, f)
		print (f"{completed} / {len(targets)} - {filename}")
		if not os.path.isfile(t_file):
			pre_process (t_file, messages)
		completed += 1

if __name__ == "__main__":
	main ()