# track2image
Do you love to run? Did you wear a sport watch to track your running activities? This track2image can illustrate your GPS tracks with enough information on a thumbnail PNG file, and combine whole years' images into a summary one, which is perfect to print in an A4. 

Currently support fit files that COROS exported.

## Where to get .fit files

1. Go to COROS website, switch to [activity](https://t.coros.com/admin/views/activities) tab
2. Click **Export**, select "fit" file and input your email address
3. Download the zip file from the link in email that sent by COROS
4. Extract zip file to a local folder (e.g., ./data)
5. Follow below instructions (Usage section) to generate your track images

Sample summary image for year 2025:

![Summary Image for 2025](./images/2025.png "2025 summary"){width=60%}

Event image in details:

![Event Image explained](./images/track_explained.png "track image")

## Usage

### Install pre-requirements
```bash
pip install -r requirements.txt
```
### Process .fit files, split them into each year folder
```bash
python process.py [fit_folder]
```
### Generate event images & a year image
```bash
python generate.py [year]
```
