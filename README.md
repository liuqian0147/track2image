# track2image
Do you love to run? Did you wear a sport watch to track your running activities? This track2image can illustrate your GPS tracks with enough information on a thumbnail PNG file, and combine whole years' images into a summary one, which is perfect to print in an A4. 

Currently support fit files that COROS exported.

## Where to get .fit files

1. Go to COROS website, switch to [activity](https://t.coros.com/admin/views/activities) tab
2. Click **Export**, select "fit" file and input your email address
3. Download the zip file from the link in email that sent by COROS
4. Extract zip file to a local folder (e.g., ./data)
5. Follow below instructions (Usage section) to generate your track images


### Example Images

#### Yearly Summary Image
The summary image below shows all your running activities for the year 2025. Each colored line represents a single run, mapped to a small thumbnail. The layout arranges all runs chronologically or by month, providing a visual overview of your running history for the year. This image is designed to fit on an A4 page for easy printing and sharing.

![Summary Image for 2025](./images/2025.png "2025 summary"){width=60%}

#### Detailed Event Image
The event image below illustrates a single running activity in detail. It displays the GPS track of your run, with additional information such as distance, duration, and possibly elevation. Visual markers may highlight the start and end points, and the route is color-coded to indicate different sport type.

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
