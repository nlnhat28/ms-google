import requests
import time
import json
import os
from gtts import gTTS
import playsound
import urllib
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pilmoji import Pilmoji

# Constant =======================================================================================================
FONT_1 = ImageFont.truetype("fonts/UTM HelvetIns.ttf", size = 34) 
FONT_2 = ImageFont.truetype("fonts/UTM HelvetIns.ttf", size = 30)
START_COLOR = (0, 0, 0, 200) # Black with 50% transparency
END_COLOR = (0, 0, 0, 0) # Black with 0% transparency

REPLACE_PATH = "replace.json"
CONFIG_PATH = "config.json"
AUDIO_PATH = "read.mp3"
PICTURE_PATH = "picture.png"
LOG_PATH = "log.txt"

# Variable =======================================================================================================
dict_replace = {}
page_id = ''
cookie = {}
access_token = ''
timesleep = 18

url_comment = ''
params_comment = {}
last_id = ''
last_message = ''

# Def ============================================================================================================
#Format Cookie
def format_cookie(cookie_string):
    cookie = {}
    for field in cookie_string.split(";"):
        key_value = field.strip().split("=", 1)
        if len(key_value) == 2:
            key, value = key_value
            cookie[key] = value
    return cookie

# Load file
def load_file():
    global dict_replace, config, page_id, cookie, access_token, time_sleep
    with open(REPLACE_PATH, 'r', encoding='utf-8') as f:
        dict_replace = json.load(f)
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)

        page_id = config.get('page_id')
        cookie = format_cookie(config.get('cookie'))
        time_sleep = config.get('time_sleep') - 8

# Get access_token
def get_substring_between(string, start, end):
    start_index = string.find(start)
    if start_index == -1:
        return ""
    start_index += len(start)
    end_index = string.find(end, start_index)
    if end_index == -1:
        return ""
    return string[start_index:end_index]
def get_access_token():
    global access_token
    start = "[{\"accessToken\":\""
    end = "\",\"clientID\""
    endpoint = f"https://business.facebook.com/content_management"
    response = requests.get(endpoint, cookies=cookie)
    content = str(response.content)
    access_token = get_substring_between(content, start, end)

# Get video id
def get_video_id():
    global video_id, url_comment, params_comment
    url = f'https://graph.facebook.com/v16.0/{page_id}/live_videos?'
    params = {
        "access_token": access_token,
        "fields": "creation_time,id",
        "order": "reverse_chronological",
        "limit": 1
    }
    response = requests.get(url, params=params, cookies=cookie)
    data = json.loads(response.content.decode('utf-8'))
    if data.get('data'):
        video_id = data['data'][0]['id']
        url_comment = f"https://graph.facebook.com/v16.0/{video_id}/comments?"
        params_comment = {
            "access_token": access_token,
            "fields": "created_time,message,from{id,name,picture{url}}",
            "order": "reverse_chronological",
            "limit": 1
        }
    else:
        print("Not found video")
        raise Exception

# Replace word:
def replace_words_in_dict(string, dictionary):
    words = string.split()
    for i, word in enumerate(words):
        if word.upper() in dictionary:
            words[i] = dictionary[word.upper()]
    replaced_string = ' '.join(words)
    return replaced_string

# Create image
def create_image(image, text1, text2):
    text1_bbox = FONT_1.getbbox(text1)
    text2_bbox = FONT_2.getbbox(text2)
    max_bbox = max(text1_bbox[2],text2_bbox[2])

    new_width = image.width + max_bbox + 28
    new_height = image.height + 16

    new_image = Image.new('RGBA', (new_width, new_height))

    for x in range(new_image.width):
        alpha = int((1.0 - x / float(new_image.width - 1)) * START_COLOR[3])
        color = START_COLOR[:3] + (alpha,)
        draw = ImageDraw.Draw(new_image)
        draw.line((x, 0, x, new_image.height), fill=color)

    new_image.paste(image, (8, 8))

    text1_position = (image.width + 16, 0)
    text2_position = (image.width + 16, new_height // 2 )

    with Pilmoji(new_image) as pilmoji:
        pilmoji.text(text2_position, text2, font=FONT_2, fill=(255, 255, 255, 255), emoji_position_offset=(0,8))
        pilmoji.text(text1_position, text1, font=FONT_1, fill=(255, 215, 0, 255), emoji_position_offset=(0,6))

    new_image = ImageOps.expand(new_image, border=(6, 0, 0, 0), fill=(255, 100, 0))

    new_image.save(PICTURE_PATH, format='PNG')

# Loop to read comment every time_sleep seconds
def read_comment_loop():
    global last_id, last_message
    while True:
        try:
            response = requests.get(url_comment, params=params_comment, cookies=cookie)
            data = json.loads(response.content.decode('utf-8'))

            # Check if there are comments
            if data.get("data"):
                latest_comment = data["data"][0]
                id = latest_comment['id']
                message = latest_comment['message']

                if id != last_id and message != last_message and message != '':
                    last_message = message
                    last_id = id

                    name = latest_comment['from']['name']
                    picture_url = latest_comment["from"]["picture"]["data"]["url"]

                    with open(LOG_PATH, 'a', encoding='utf-8') as f:
                        f.write(f"{message}\n")

                    message_replace = replace_words_in_dict(message[:60], dict_replace)
                    gtts_read = f"{name}. {message_replace}" 

                    show_name = f"{name}"
                    show_comment = f"{message}"[:60]
                    with urllib.request.urlopen(picture_url) as response:
                        image_data = response.read()                                  
                    show_image = Image.open(BytesIO(image_data))                                   
                    create_image(show_image, show_name, show_comment)

                    audio_gtts = gTTS(gtts_read, lang="vi", slow=False,)
                    audio_gtts.save(AUDIO_PATH)
                    playsound.playsound(AUDIO_PATH, block = True)
                    time.sleep(8)
                    os.remove(AUDIO_PATH)
                    os.remove(PICTURE_PATH)

        except Exception as e:
            print(f"Error occurred while making request: {e}")
            pass

        time.sleep(time_sleep)

# Main =========================================================================================================
load_file()
get_access_token()
get_video_id()
read_comment_loop()

