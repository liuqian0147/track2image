# track2image
Draw track images for your sport data (fit files supported) with detailed information. 

**Input**: path to .fit files, for example, "./coros_history_20250109"
**Output**: image files (.png) for each event and a combined image for one year

## Usage

* python process.py <folder contained files>
    ** it will create a "tracks" folder with year name for events
* python generte.py <year>
    ** e.g., python generate.py 2025. It will create an output folder to contained the combied image, each event image stored in the "./tracks/<year>/"



