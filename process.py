from html import parser
import os, shutil
from garmin_fit_sdk import Decoder, Stream
from datetime import datetime, timezone, timedelta
import numpy as np
import pandas as pd
import argparse

def pre_process (filename, messages):
	try:
		name, _ = os.path.splitext (filename)

		with open(f'{name}.txt', "wt") as f:
			f.write (str(messages['session_mesgs']))

		if 'record_mesgs' in messages:
			df = pd.DataFrame(messages['record_mesgs'])
			df.to_csv (f"{name}.csv", index=False)
	except KeyError as e:
		print(f"Error: Missing expected data in messages for file {filename}. Key: {e}")
	except IOError as e:
		print(f"Error: Unable to write output files for {filename}. {e}")
	except Exception as e:
		print(f"Unexpected error during preprocessing for {filename}: {e}")

def main ():
	try:
		parser = argparse.ArgumentParser(description='Extract and process fit files.')
		parser.add_argument('folder', type=str, help='Folder containing fit files to process')
		args = parser.parse_args()
		input_path = args.folder

		if not os.path.isdir(input_path):
			print (f"Error: {input_path} is not a valid folder. Please provide a directory containing FIT files.")
			return

		output_path = './tracks/'
		try:
			if not os.path.isdir(output_path):
				os.mkdir (output_path)
		except OSError as e:
			print(f"Error: Unable to create output directory '{output_path}'. {e}")
			return

		targets = []
		try:
			for f in os.listdir (input_path):
				_, ext = os.path.splitext (f)

				if ext.lower() == '.fit':
					targets.append (os.path.join(input_path, f))
				else:
					print (f"Warning: {f} is not a FIT file, skipping.")
		except OSError as e:
			print(f"Error: Unable to read contents of input folder '{input_path}'. {e}")
			return

		if not targets:
			print("No FIT files found in the specified folder. Nothing to process.")
			return

		processing = 0
		for filename in targets:
			try:
				_, f = os.path.split(filename)
				
				stream = Stream.from_file(filename)
				decoder = Decoder(stream)
				messages, _ = decoder.read()

				if "activity_mesgs" not in messages or not messages["activity_mesgs"]:
					print(f"Error: No activity messages found in {filename}. Skipping this file.")
					continue

				event_date = messages["activity_mesgs"][0]['timestamp'].replace(tzinfo=timezone.utc).astimezone(tz=None)

				t_dir = os.path.join(output_path, str(event_date.year))
				try:
					if not os.path.isdir(t_dir):
						os.mkdir (t_dir)
				except OSError as e:
					print(f"Error: Unable to create year directory '{t_dir}' for {filename}. {e}")
					continue

				t_file = os.path.join(t_dir, f)
				print (f"{processing + 1} / {len(targets)} - Processing {filename}")
				if not os.path.isfile(t_file):
					pre_process (t_file, messages)
				else:
					print(f"Output file for {filename} already exists, skipping.")
				processing += 1
			except KeyError as e:
				print(f"Error: Missing required data in {filename}. Key: {e}. Skipping this file.")
			except IOError as e:
				print(f"Error: Unable to read FIT file {filename}. {e}. Skipping this file.")
			except Exception as e:
				print(f"Unexpected error processing {filename}: {e}. Skipping this file.")

	except Exception as e:
		print(f"An unexpected error occurred: {e}. Please check your input and try again.")

if __name__ == "__main__":
	main ()