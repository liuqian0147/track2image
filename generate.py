import os
import glob
from PIL import Image, ImageDraw, ImagePath, ImageFont
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import datetime
import math
import argparse
from styles import styles

base_path = './tracks'
output_path = './output'

img_size = (300, 300)
border = 25
bk_color = '#2A314A'
day_color = '#1F2537'
info_color = '#A4AFD4'
line_color = '#0A0C12'
altitude_color = '#747D9C'

default_font = "./fonts/OpenSans-ExtraBold.ttf"

def gen_track_image (filename, colors):
    try:
        property_file = f"{filename}"
        pth, f = os.path.split(filename)
        name, _ = os.path.splitext(f)
        data_file = os.path.join(pth, f"{name}.csv")    

        if not os.path.isfile (property_file):
            print (f"Error: Property file {property_file} not found. Skipping.")
            return None

        p = {}
        try:
            with open (property_file, 'rt') as f:
                p = eval (f.read())
        except (SyntaxError, ValueError) as e:
            print(f"Error: Unable to parse property file {property_file}. {e}. Skipping.")
            return None
        except IOError as e:
            print(f"Error: Unable to read property file {property_file}. {e}. Skipping.")
            return None

        if not p or 'start_time' not in p[0]:
            print(f"Error: Invalid or missing data in property file {property_file}. Skipping.")
            return None

        #convert to local timezone
        event_date = p[0]['start_time'].replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
        output_file = os.path.join(pth, f"{event_date:%Y-%m-%d_%H-%M-%S}.png")

        sport_name = f"{p[0]['sport']}{('_' + p[0]['sub_sport']) if 'sub_sport' in p[0] else ''}"

        if not os.path.isfile (data_file):
            print (f"Error: Data file {data_file} not found. Skipping.")
            return None

        try:
            df = pd.read_csv (data_file)
        except pd.errors.EmptyDataError:
            print(f"Error: Data file {data_file} is empty. Skipping.")
            return None
        except pd.errors.ParserError as e:
            print(f"Error: Unable to parse CSV file {data_file}. {e}. Skipping.")
            return None
        except IOError as e:
            print(f"Error: Unable to read data file {data_file}. {e}. Skipping.")
            return None

        if 'position_lat' not in df.columns or 'position_long' not in df.columns:
            print (f"Error: Data file {data_file} has no position data. Skipping.")
            return None
        
        #clean up data
        df = df.dropna()

        width = img_size[0] - 2 * border
        height = img_size[1] - 2 * border

        try:
            im = Image.new ('RGBA', img_size, bk_color) #base image
            draw = ImageDraw.Draw (im)
        except Exception as e:
            print(f"Error: Unable to create image for {filename}. {e}. Skipping.")
            return None

        ############
        # draw altitude lines
        ############
        if sport_name in ['running_trail', 'hiking', 'hiking_generic']:
            df_al = df.dropna(subset=['distance', 'enhanced_altitude']) 

            d_a = [tuple(row) for row in df_al[['distance','enhanced_altitude']].to_numpy()]
            if d_a:
                try:
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
                except Exception as e:
                    print(f"Warning: Unable to draw altitude lines for {filename}. {e}")

        #draw track
        df_track = df.dropna(subset=['position_lat', 'position_long']) 

        #load tracks
        xy = [tuple(row) for row in df_track[['position_long','position_lat']].to_numpy()]
        if not xy:
            print (f"Error: {filename} has no track data. Skipping.")
            return None

        try:
            path = ImagePath.Path (xy)
            box = path.getbbox() #(xl,yt,xr,yb)

            if (box[2] - box[0] == 0) or (box[3] - box[1] == 0):
                print (f"Error: {filename} has invalid track bounds. Skipping.")
                return None
        except Exception as e:
            print(f"Error: Unable to process track path for {filename}. {e}. Skipping.")
            return None

        #############
        #draw information
        #############
        try:
            distance = p[0]['total_distance']/1000
            total_seconds= p[0]['total_elapsed_time']
            # calculate hours, minutes and seconds
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            event_day = event_date.day

            info_str = f"{distance:.2f} km / {int(hours):02}:{int(minutes):02}:{int(seconds):02}"
            draw.text ((img_size[0] - 10, 10), info_str, font=ImageFont.truetype(default_font, 15), fill=info_color, anchor='ra')
        except (KeyError, TypeError) as e:
            print(f"Warning: Unable to draw info text for {filename}. Missing data: {e}")
        except OSError as e:
            print(f"Warning: Unable to load font for info text in {filename}. {e}")

        ##############
        # draw day
        ##############
        try:
            fnt = ImageFont.truetype(default_font, 130)
            draw.text((img_size[0]/2, img_size[1]/2 - 15),  
                f"{event_day}",
                font = fnt, 
                fill = day_color, 
                anchor = 'mm')
        except OSError as e:
            print(f"Warning: Unable to load font for day text in {filename}. {e}")

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
        try:
            im.save (output_file)
            return (output_file, event_date)
        except IOError as e:
            print(f"Error: Unable to save image for {filename} to {output_file}. {e}. Skipping.")
            return None
    except Exception as e:
        print(f"Unexpected error generating track image for {filename}: {e}. Skipping.")
        return None


def gen_month_image (month):
    try:
        assert (month > 0 and month <=12)
        im = Image.new ('RGBA', img_size, bk_color)
        draw = ImageDraw.Draw (im)

        month_text = datetime.date(2000, month, 1).strftime('%b')

        try:
            draw.text((img_size[0]/2, img_size[1]/2 - 15),  
                month_text,
                font=ImageFont.truetype(default_font, 120), 
                fill=info_color, 
                anchor='mm')
        except OSError as e:
            print(f"Warning: Unable to load font for month image. {e}")

        return im
    except AssertionError:
        print(f"Error: Invalid month {month}. Must be 1-12.")
        return None
    except Exception as e:
        print(f"Error: Unable to generate month image for {month}. {e}")
        return None

def gen_year_image (year):
    try:
        im = Image.new ('RGBA', img_size, bk_color)
        draw = ImageDraw.Draw (im)

        try:
            draw.text((img_size[0]/2, img_size[1]/2 - 15),  
                #f"{year[:2]}\n{year[-2:]}",
                year,
                font=ImageFont.truetype(default_font, 120), 
                fill=info_color, 
                anchor='mm')
        except OSError as e:
            print(f"Warning: Unable to load font for year image. {e}")
        
        return im
    except Exception as e:
        print(f"Error: Unable to generate year image for {year}. {e}")
        return None

def main ():
    try:
        parser = argparse.ArgumentParser(description='Generate track images for one year with customizable color styles.')
        parser.add_argument('year', type=str, help='Year to generate.')
        parser.add_argument('--style', type=str, default='default', help='Color style to use (default, original, minimal, light, nature, sunset)')
        args = parser.parse_args()
        target_year = args.year
        selected_style = args.style

        if selected_style not in styles:
            print(f"Warning: Style '{selected_style}' not found. Available styles: {', '.join(styles.keys())}. Using default.")
            selected_style = 'default'

        style = styles[selected_style]
        global colors, bk_color, day_color, info_color, line_color, altitude_color
        colors = style['tracks']
        bk_color = style['background']
        day_color = style['day']
        info_color = style['info']
        line_color = style['line']
        altitude_color = style['altitude']

        try:
            targets, mm = [], []
            for file in glob.glob (os.path.join(base_path, target_year, "*.txt")):
                r = gen_track_image (file, colors)
                if r: 
                    targets.append(r[0])
                    if r[1].month not in mm:
                        mm.append(r[1].month)
        except Exception as e:
            print(f"Error: Unable to process files for year {target_year}. {e}")
            return

        if not targets:
            print(f"No valid track files found for year {target_year}. Please ensure processed data exists in {os.path.join(base_path, target_year)}.")
            return

        # generate summary image
        targets.sort() #target file named by date/time

        width, height = img_size[0], img_size[1]
        total = len(targets) + len(mm) + 1 #one year image + 12 month images

        cols = math.ceil(math.sqrt (total * 2 / 3))
        rows = math.ceil(total / cols)

        try:
            dest = Image.new('RGBA', (width * cols, height * rows), bk_color)
            year_img = gen_year_image(target_year)
            if year_img:
                dest.paste (year_img, (0, 0))
            else:
                print("Warning: Unable to generate year image.")
        except Exception as e:
            print(f"Error: Unable to create summary image canvas. {e}")
            return

        months = []
        i = 1
        for f in targets:
            try:
                _, filename = os.path.split(f)
                name, _ = os.path.splitext(filename)

                #2025-04-28 21:43:17+00:00
                event_date = datetime.datetime.strptime(name, "%Y-%m-%d_%H-%M-%S")

                if event_date.month not in months: #gen month image
                    months.append (event_date.month)
                    month_img = gen_month_image(event_date.month)
                    if month_img:
                        x = width * (i % cols)
                        y = height * (i // cols)
                        dest.paste(month_img, (x, y))
                        i += 1
                    else:
                        print(f"Warning: Skipping month image for {event_date.month}.")

                img = Image.open (f)
                x = width * (i % cols)
                y = height * (i // cols)
                #print (i, x, y)
                dest.paste (img, (x, y))
                i += 1
            except ValueError as e:
                print(f"Error: Unable to parse date from filename {f}. {e}. Skipping.")
            except IOError as e:
                print(f"Error: Unable to open image {f}. {e}. Skipping.")
            except Exception as e:
                print(f"Error: Unable to process image {f}. {e}. Skipping.")

        #draw lines
        try:
            draw = ImageDraw.Draw (dest)
            for i in range(1, rows):
                draw.line (((0, i*height), (width*cols, i*height)), line_color, width= 1)
            for i in range(1, cols):
                draw.line (((i*width, 0), (i*width, rows*height)), line_color, width= 1)

            #draw frame
            draw.rounded_rectangle(((0, 0), (width*cols, height*rows)), outline=line_color, radius=3.0, width=5)
        except Exception as e:
            print(f"Warning: Unable to draw grid lines on summary image. {e}")

        try:
            if not os.path.isdir(output_path):
                os.mkdir (output_path)
        except OSError as e:
            print(f"Error: Unable to create output directory {output_path}. {e}")
            return

        try:
            target_file = os.path.join(output_path, f"{target_year}.png")
            dest.save (target_file)
            print (f"Summary image generated: {target_file}")
        except IOError as e:
            print(f"Error: Unable to save summary image to {target_file}. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}. Please check your input and try again.")

if __name__ == "__main__":
    main ()