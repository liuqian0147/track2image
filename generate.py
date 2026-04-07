import os
import glob
from PIL import Image, ImageDraw, ImagePath, ImageFont
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import datetime
import math
import argparse

base_path = './tracks'
output_path = './output'

colors = {
    'running':"#68B8B2", 
    'running_generic':"#68B8B2",
    'running_trail':"#68B86E", 
    'running_track':"#68B8B2",
    'walking':"#B86890", 
    'cycling_road':"#9B68B8", 
    'cycling':"#9B68B8",
    'cycling_generic':"#9B68B8",
    'hiking':"#B88468",
    'hiking_generic':"#B88468",
    'swimming_open_water':"#A7B868",
    'swimming':"#A7B868",
}

img_size = (300, 300)
border = 25
bk_color = '#2A314A'
day_color = '#1F2537'
info_color = '#A4AFD4'
line_color = '#0A0C12'
altitude_color = '#747D9C'

default_font = "./fonts/OpenSans-ExtraBold.ttf"

def gen_track_image (filename): #filename = property file (.txt)

    property_file = f"{filename}"
    pth, f = os.path.split(filename)
    name, _ = os.path.splitext(f)
    data_file = os.path.join(pth, f"{name}.csv")    

    if not os.path.isfile (property_file):
        print (f"{property_file} not found.")
        return None

    p = {}
    with open (property_file, 'rt') as f:
        p = eval (f.read())

    #convert to local timezone
    event_date = p[0]['start_time'].replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
    output_file = os.path.join(pth, f"{event_date:%Y-%m-%d_%H-%M-%S}.png")

    sport_name = f"{p[0]['sport']}{('_' + p[0]['sub_sport']) if 'sub_sport' in p[0] else ''}"

    if not os.path.isfile (data_file):
        print (f"{data_file} not found.")
        return None

    df = pd.read_csv (data_file)
    if 'position_lat' not in df.columns or 'position_long' not in df.columns:
        print (f"{data_file} has no position data.")
        return None
    
    #clean up data
    df = df.dropna()

    width = img_size[0] - 2 * border
    height = img_size[1] - 2 * border

    im = Image.new ('RGBA', img_size, bk_color) #base image
    draw = ImageDraw.Draw (im)

    ############
    # draw altitude lines
    ############
    if sport_name in ['running_trail', 'hiking', 'hiking_generic']:
        df_al = df.dropna(subset=['distance', 'enhanced_altitude']) 

        d_a = [tuple(row) for row in df_al[['distance','enhanced_altitude']].to_numpy()]
        path = ImagePath.Path (d_a)
        box = path.getbbox() #(xl,yt,xr,yb)
        if (box[2] - box[0] > 0) or (box[3] - box[1] > 0):
            a = width / (box[2] - box[0])
            e = -height*0.25 / (box[3] - box[1]) #5000, assume 5k is the maximum altitude I climbed
            b, d = 0, 0
            c = -box[0] * a + border
            f = -box[1] * e + height + border #

            trans = (a, b, c, d, e, f)
            path.transform(trans)
            xy = path.tolist()
            xy += (border + width, border + height)
            xy.insert (0, (border, border + height))
            draw.polygon (xy, fill = altitude_color,  width = 1, outline = altitude_color)

    #draw track
    df_track = df.dropna(subset=['position_lat', 'position_long']) 

    #load tracks
    xy = [tuple(row) for row in df_track[['position_long','position_lat']].to_numpy()]
    path = ImagePath.Path (xy)
    box = path.getbbox() #(xl,yt,xr,yb)

    if (box[2] - box[0] == 0) or (box[3] - box[1] == 0):
        print (f"{filename} has no tracks.")
        return None

    #############
    #draw information
    #############
    distance = p[0]['total_distance']/1000
    total_seconds= p[0]['total_elapsed_time']
    # 计算各个时间单位
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    event_day = event_date.day

    info_str = f"{distance:.2f} km / {int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    draw.text ((img_size[0] - 10, 10), info_str, font=ImageFont.truetype(default_font, 15), fill=info_color, anchor='ra')

    ##############
    # draw day
    ##############
    fnt = ImageFont.truetype(default_font, 130)
    draw.text((img_size[0]/2, img_size[1]/2 - 15),  
        f"{event_day}",
        font = fnt, 
        fill = day_color, 
        anchor = 'mm')

    #############
    # draw track
    #############    

    a = width / (box[2] - box[0])
    e = -height / (box[3] - box[1])

    ratio = min (abs(a), abs(e))
    a = ratio
    e = -ratio

    b, d = 0, 0
    c = -box[0] * a + border
    f = -box[1] * e + height + border

    trans = (a, b, c, d, e, f)
    path.transform(trans)
    
    #align track in the middle of images
    box_rev = path.getbbox()
    #print (box_rev)

    if (box_rev[2] - box_rev[0] < width):
        #align x
        dx = (width - (box_rev[2] - box_rev[0])) / 2
        path.transform ((1, 0, dx, 0, 1, 0))

    if (box_rev[3] - box_rev[1] < height):
        #align y
        dy = -(height - (box_rev[3] - box_rev[1])) / 2
        path.transform((1, 0, 0, 0, 1, dy))

    xy = path.tolist()
    if sport_name not in colors:
        sport_name = "running" #default one
    draw.line (xy, colors[sport_name], width = 3)

    #start
    draw.circle(xy[0], radius = 3, fill="green", outline="white")
    #end
    draw.circle(xy[-1], radius = 3, fill="red", outline="white")

    ############
    # save to file
    ############
    im.save (output_file)
    return (output_file, event_date)


def gen_month_image (month):
    
    months = {
        1:"Jan",
        2:"Feb",
        3:"Mar",
        4:"Apr",
        5:"May",
        6:"Jun",
        7:"Jul",
        8:"Aug",
        9:"Sep",
        10:"Oct",
        11:"Nov", 
        12:"Dec"
    }
    assert (month > 0 and month <=12)
    im = Image.new ('RGBA', img_size, bk_color)
    draw = ImageDraw.Draw (im)

    draw.text((img_size[0]/2, img_size[1]/2 - 15),  
        months[month],
        font=ImageFont.truetype(default_font, 120), 
        fill=info_color, 
        anchor='mm')

    return im

def gen_year_image (year):

    im = Image.new ('RGBA', img_size, bk_color)
    draw = ImageDraw.Draw (im)

    draw.text((img_size[0]/2, img_size[1]/2 - 15),  
        #f"{year[:2]}\n{year[-2:]}",
        year,
        font=ImageFont.truetype(default_font, 120), 
        fill=info_color, 
        anchor='mm')
    
    return im

def main ():
    
    parser = argparse.ArgumentParser(description='Generate track images for one year.')
    parser.add_argument('year', type=str, help='Year to generate.')
    args = parser.parse_args()
    target_year = args.year

    targets, mm = [], []
    for file in glob.glob (os.path.join(base_path, target_year, "*.txt")):
        r = gen_track_image (file)
        if r: 
            targets.append(r[0])
            if r[1].month not in mm:
                mm.append(r[1].month)

    # generate summary image
    targets.sort() #target file named by date/time

    width, height = img_size[0], img_size[1]
    total = len(targets) + len(mm) + 1 #one year image + 12 month images

    cols = math.ceil(math.sqrt (total * 2 / 3))
    rows = math.ceil(total / cols)

    dest = Image.new('RGBA', (width * cols, height * rows), bk_color)
    dest.paste (gen_year_image(target_year), (0, 0))

    months = []
    i = 1
    for f in targets:
        _, filename = os.path.split(f)
        name, _ = os.path.splitext(filename)

        #2025-04-28 21:43:17+00:00
        event_date = datetime.datetime.strptime(name, "%Y-%m-%d_%H-%M-%S")

        if event_date.month not in months: #gen month image
            months.append (event_date.month)
            x = width * (i % cols)
            y = height * (i // cols)
            dest.paste(gen_month_image(event_date.month), (x, y))
            i += 1

        img = Image.open (f)
        x = width * (i % cols)
        y = height * (i // cols)
        #print (i, x, y)
        dest.paste (img, (x, y))
        i += 1

    #draw lines
    draw = ImageDraw.Draw (dest)
    for i in range(1, rows):
        draw.line (((0, i*height), (width*cols, i*height)), line_color, width= 1)
    for i in range(1, cols):
        draw.line (((i*width, 0), (i*width, rows*height)), line_color, width= 1)

    #draw frame
    draw.rounded_rectangle(((0, 0), (width*cols, height*rows)), outline=line_color, radius=3.0, width=5)

    if not os.path.isdir(output_path):
        os.mkdir (output_path)
    dest.save (target_file := os.path.join(output_path, f"{target_year}.png"))
    print (f"Summary image generated: {target_file}")

if __name__ == "__main__":
    main ()