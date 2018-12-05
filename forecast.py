import requests
import matplotlib.pyplot as plt
from PIL import Image 
from matplotlib.pyplot import imshow
import cv2
import numpy as np
import imutils
from bs4 import BeautifulSoup
import requests
import csv
import json
import datetime 
from pytz import timezone
import pytz
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection


key = '9c7ff8d4b65498dd88966f44707e4a5f'
url = 'https://api.darksky.net/forecast/'
princeton_jetty_latlong = '37.5013,122.4707'
r = requests.get(url + key + '/' + princeton_jetty_latlong)
jsonst =  r.json()
wind_speed = jsonst['currently']['windSpeed']
# print 'Wind Speed is %s MPH' %wind_speed
wind_direction_string = str(jsonst['currently']['windBearing'])
# print 'Wind Direction is %s' %wind_direction_string

wind_direction = jsonst['currently']['windBearing']


def rotate_image(mat, angle):
  # angle in degrees
    height, width = mat.shape[:2]
    image_center = (width/2, height/2)

    rotation_mat = cv2.getRotationMatrix2D(image_center, angle, 1.)

    abs_cos = abs(rotation_mat[0,0])
    abs_sin = abs(rotation_mat[0,1])

    bound_w = int(height * abs_sin + width * abs_cos)
    bound_h = int(height * abs_cos + width * abs_sin)

    rotation_mat[0, 2] += bound_w/2 - image_center[0]
    rotation_mat[1, 2] += bound_h/2 - image_center[1]

    rotated_mat = cv2.warpAffine(mat, rotation_mat, (bound_w, bound_h))
    new_image = Image.fromarray(rotated_mat)
    resize_new_image = new_image.resize((150,150))
    return resize_new_image

def get_cdip_swell_data():
    source = requests.get('http://cdip.ucsd.edu/m/products/?stn=142p1').text

    soup = BeautifulSoup(source, 'lxml')
    match = soup.find(class_="panel-body")
    text = match.text
    wave_height = float(text.split('/')[1].split('f')[0])
    period = float(text.split('Peak Period')[1].split('s')[0])
    direction = int(text.split('Direction')[1].split('T')[0].replace(' ','')[:3])

#     print 'Swell height is %sft' %wave_height 
#     print 'Swell period is %s' %period
    # print 'Swell direction is %s' %direction
    return wave_height

source = requests.get('http://cdip.ucsd.edu/m/products/?stn=142p1').text
soup = BeautifulSoup(source, 'lxml')
match = soup.find(class_="panel-body")
text = match.text
period = float(text.split('Peak Period')[1].split('s')[0])
# get_cdip_swell_data()
direction = -(int(text.split('Direction')[1].split('T')[0].replace(' ','')[:3])+180)
imge = Image.open("/Users/adamluba/Desktop/arrow.png")
img = np.asarray(imge)
angle = -(wind_direction +180)
water_temp = text.split('/')[2].split('Current')[0].replace(' ','')


################################################################################################################

source = requests.get('https://www.surfline.com/surf-report/ocean-beach-overview/5842041f4e65fad6a77087f8').text

data = source.split('__DATA__ =')[1].split('</script>')[0]
d = json.loads(data)
current_tide = float(d['spot']['report']['data']['forecast']['tide']['current']['height'])
next_tide_type = d['spot']['report']['data']['forecast']['tide']['next']['type']
next_tide = float(d['spot']['report']['data']['forecast']['tide']['next']['height'])
previous_tide_type = d['spot']['report']['data']['forecast']['tide']['previous']['type']
previous_tide = float(d['spot']['report']['data']['forecast']['tide']['previous']['height'])
current_time_epoch = d['spot']['report']['data']['forecast']['tide']['current']['timestamp']
next_time_epoch = d['spot']['report']['data']['forecast']['tide']['next']['timestamp']
previous_time_epoch = d['spot']['report']['data']['forecast']['tide']['previous']['timestamp']

t = d['spot']['report']['data']['forecast']['tide']
# soup = BeautifulSoup(source, 'lxml')
# match = soup.find(class_= 'table table-sm table-striped table-inverse table-tide')
def tz2ntz(epoch, tz, ntz):

    # date_obj: datetime object
    # tz: old timezone
    # ntz: new timezone

    epoch_to_datetime = datetime.datetime.utcfromtimestamp(epoch)
    date_obj = epoch_to_datetime.replace(tzinfo=pytz.timezone(tz))
    new_date_obj = date_obj.astimezone(pytz.timezone(ntz))
    date_obj_string = new_date_obj.strftime('%m/%d/%Y %H-%M-%S')
    return date_obj_string
current_time= tz2ntz(current_time_epoch, 'UTC', 'US/Pacific')
next_time= tz2ntz(next_time_epoch, 'UTC', 'US/Pacific')[10:16].replace('-', ':')
previous_time= tz2ntz(previous_time_epoch, 'UTC', 'US/Pacific')[10:16].replace('-',':')




dta = {'height':[current_tide,next_tide, previous_tide], 'time':[current_time, next_time, previous_time]}
df = pd.DataFrame(data=dta)



def prettify_num(num):
    pretty_num = ''
    if abs(num) < 10**3:
        pretty_num = str(num)
    elif abs(num) < 10**6:
        pretty_num = str(round(1.0*num/10**3,1)) + 'K'
    elif abs(num) < 10**9:
        pretty_num = str(round(1.0*num/10**6,1)) + 'M'
    else:
        pretty_num = str(round(1.0*num/10**9,1)) + 'B'
    return pretty_num

def color_difference(first, second):
    if first > second:
        return '#3ff1d1' #teal
    elif second > first:
        return '#3ff1d1' #purple
    else: return '#e3e7ed' #gray


# Function: Parse the df and returns the numbers contextualized
# Input: df with at least two columns
# Output: an array of three numeric or null values: the percent(0-1), the current number, and the contract number
def parse(df):
    if df.size == 0:
        return [None, None]
    elif df.iloc[0,0] == -1:
        current = df.iloc[1,0]
        return [current, np.inf]
    else:
        past = float(df.iloc[2,0])
        current = float(df.iloc[1,0])
        return [past, current]

# Function: Parse the df and returns the prettified numbers to be sent to the matplot plot
# Input: df with at least two columns
# Output: an array of three prettified strings: the percent, the current number, and the contract number
def pretty_parse(df):
    [current, contract] = parse(df)
    if df.size == 0:
        return ['', '', 'NA']
    elif contract == np.inf:
        current = str(prettify_num(current))
        return [current, '$\infty$', '$\infty$']
    else:
        return [str(prettify_num(current)),
                str(prettify_num(contract)),
                str(prettify_num(current-contract)),
               pretty_percent(current, contract)]

##########################################################################
### HELPER PLOT FUNCTIONS
##########################################################################

# Function: create a centered text object
# Input: the axes object to append to and optionally (text, color, y_position, font_size)
# Output: matplot ax.text object
def kpi_text(ax4, text = '', text_color = 'black', y_position = 0, font_size = 10):
    return ax4.text(x = 0.5,
                   y = y_position,
                   s = text,
                   color = text_color,
                   family = 'sans-serif',
                   fontsize = font_size,
                   fontweight = 500,
                   horizontalalignment = 'center',
                   verticalalignment = 'center')

def get_arrow(past, current):
    if past > current:
        return u'$\u2193$'
    elif current > past:
        return u'$\u2191$'
    else:
        return '|'

def get_main_font_size(main_text, type):
    if type == 'percent':
        if len(main_text) > 3:
            return 80
        return 100
    else:
        if len(main_text) > 5:
            return 65
        else:
            return 80


##########################################################################
### MAIN PLOT
##########################################################################


def kpi_chart(df, titletext = 'KPI', subtitle = '', type = 'absolute'):
    next_timestamp = df.iloc[1,1]
    previous_timestamp = df.iloc[2,1]
    # Parse data
    [past, current] = parse(df)
    diff = abs(current - past)
    percent = 1.0 * (current-past)/past if df.size != 0 else None
    [ppast, pcurrent, pdiff] = map(prettify_num, [past, current, diff])

    # Set up figure canvas
    fig, ax4 = plt.subplots(figsize = (5,5))
    fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
    ax4.axis('off')

    #Colors
    mediumgray = '#999292'
    lightgray = '#cbd0d8'
    darkergreen = '#4f7c4f'
    lightergreen = '#639b63'
    darkred = '#a60c3a'

    ppercent = str(abs(int(percent*100))) + '%'
    main_text = ppercent if type == 'percent' else prettify_num(diff)

    # Font Size
    arrow_position_x = 0.2
    main_position_x = 0.68
    main_text_y = 0.45
    label_text_y = main_text_y - 0.25
    
    title = ax4.text(x = main_position_x,
                   y = 0.75,
                   s = titletext,
                   color = lightgray,
                   family = 'sans-serif',
                   fontsize = 25,
                   fontweight = 450,
                   horizontalalignment = 'center',
                   verticalalignment = 'center')

    arrow = ax4.text(x = arrow_position_x,
                   y = main_text_y if past != current else main_text_y + 0.03,
                   s = get_arrow(past, current),
                   color = color_difference(past, current),
                   family = 'sans-serif',
                   fontsize = 180 if past != current else 150,
                   fontweight = 50 if past == current else 300,
                   horizontalalignment = 'center',
                   verticalalignment = 'center')

    main = ax4.text(x = main_position_x,
                   y = main_text_y,
                   s = df.iloc[0,0],
                   color = '#353a34',
                   family = 'sans-serif',
                   fontsize = get_main_font_size(main_text, type),
#                    fontsize = 380 / (len(main_text)) if type == 'absolute' else 300/len(main_text),
                   fontweight = 500,
                   horizontalalignment = 'center',
                   verticalalignment = 'center')

    label = ax4.text(x = main_position_x,
                   y = label_text_y,
                   s = subtitle,
                   color = '#595a5b',
                   family = 'sans-serif',
                   fontsize = 14,
                   fontweight = 450,
                   horizontalalignment = 'center',
                   verticalalignment = 'center')


    top = ax4.text(x = arrow_position_x + .05,
               y = 0.75,
               s = '%s ft.\n%s' %(pcurrent,next_timestamp) if current > past else '%s ft.\n%s' %(ppast,previous_timestamp),
               family = 'sans-serif',
               fontsize = 20,
               fontweight = 50,
               color = color_difference(past, current) if current > past else lightgray,
               horizontalalignment = 'center',
               verticalalignment = 'center')

    bottom = ax4.text(x = arrow_position_x +.05,
               y = 0.2,
               s = '%s ft.\n%s' %(pcurrent,next_timestamp) if current < past else '%s ft.\n%s' %(ppast,previous_timestamp),
               family = 'sans-serif',
               fontsize = 20,
               fontweight = 50,
               color = color_difference(past, current) if current < past else lightgray,
               horizontalalignment = 'center',
               verticalalignment = 'center')


    return ax4
# kpi_chart(df, titletext = 'Tide', subtitle = '', type = 'absolute')






################################################################################################################


rotate_image(img,angle)
# get_cdip_swell_data()
def main():
    f = plt.figure()
    ax1 = f.add_subplot(1,3, 1)
    ax1.axis('off')
    ax1.imshow(rotate_image(img,direction))
    ax1.set_title('Swell', fontsize=20)
    ax1.text(0.5, 0.5, '%sft' %get_cdip_swell_data(),
        horizontalalignment='center',
        verticalalignment='center',
        fontsize=20,
        transform=ax1.transAxes)
    ax1.text(0.5, 0, '%s sec' %period,
        ha='center' ,
        va= 'bottom',
        fontsize=14,
        transform=ax1.transAxes)
    ax2 = f.add_subplot(1,3, 2)
    ax2.axis('off')
    ax2.imshow(rotate_image(img,angle))
    ax2.set_title('Wind', fontsize=20)
    ax2.text(0.5, 0.5, '%smph' %wind_speed,
        horizontalalignment='center',
        verticalalignment='center',
        fontsize=20,
        transform=ax2.transAxes)
    ax3 = f.add_subplot(1,3,3)
    ax3.axis('off')
    ax3.text(0.8, 0.3, '%s' %water_temp,
        horizontalalignment='center',
        verticalalignment='center',
        fontsize=28,
        color = '#3ff1d1',
        transform=ax3.transAxes)
    kpi_chart(df, titletext = 'Tide', subtitle = '', type = 'absolute')
    plt.show()
main()

