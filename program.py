import sys
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

REPLACE_PATH = "replace_words.json"
EMOJI_PATH = "replace_emojis.json"
CONFIG_PATH = "config.json"
APIFPT_PATH = "api_fpt.json"

AUDIO_PATH = "read.mp3"
PICTURE_PATH = "picture.png"
LOG_PATH = "log.txt"

IMAGE_START_PATH = 'assets/image.png'
NAME_START = 'Chị google'
MESSAGE_START = 'Bắt đầu đọc bình luận'

GREETING_CHATBOT = 'Chào'

URL_FPT = 'https://api.fpt.ai/hmi/tts/v5'
# Variable =======================================================================================================
dict_words = {}
dict_emojis = {}
page_id = ''
cookie = {}
access_token = ''
timesleep = 15

url_comment = ''
params_comment = {}
last_id = ''
last_message = ''

api_fpt = []
cid_apt_fpt = 0
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
    global dict_words, dict_emojis, config, page_id, cookie, access_token, time_sleep, api_fpt
    with open(REPLACE_PATH, 'r', encoding='utf-8') as f:
        dict_words = json.load(f)
    with open(EMOJI_PATH, 'r', encoding='utf-8') as f:
        dict_emojis = json.load(f)
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
        page_id = config.get('page_id')
        cookie = format_cookie(config.get('cookie'))
        time_sleep = config.get('time_sleep') - 8
        print(f'page_id: {page_id}')
    with open(APIFPT_PATH, 'r', encoding='utf-8') as f:
        api_fpt = json.load(f)

    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        f.write('')
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
        "fields": "creation_time,id, title",
        "order": "reverse_chronological",
        "limit": 1
    }
    response = requests.get(url, params=params, cookies=cookie)
    json_data = json.loads(response.content.decode('utf-8'))
    if json_data.get('data'):
        video_id = json_data['data'][0]['id']
        video_title = json_data['data'][0]['title']
        url_comment = f"https://graph.facebook.com/v16.0/{video_id}/comments?"
        params_comment = {
            "access_token": access_token,
            "fields": "created_time,message,from{id,name,picture{url},gender,first_name}",
            "order": "reverse_chronological",
            "limit": 1
        }
        print(f'live_video: {video_title}')
    else:
        input("Not found video")
        sys.exit()
    
# Trim message
def trim_message(message):
    try:
        if len(message) > 60:
            message = message[:60]
            end_space_index = message.rfind(' ')
            message = message[:end_space_index]
        return message
    except:
        return message

# Remove char
def remove_char(message):
    origin_message = message
    try:
        special_chars = "/\\*\"\'-#$^>|}{"
        for char in special_chars:
            message = message.replace(char, '')
        return message
    except:
        return origin_message   
    
# Replace word:
def replace_words(message):
    origin_message = message
    try:     
        words = message.split()
        for i, word in enumerate(words):
            if word.upper() in dict_words:
                words[i] = dict_words[word.upper()]
        message = ' '.join(words)
        return message
    except:
        return origin_message
    
# Replace emoji
def replace_emojis(message):
    origin_message = message
    try:
        translation_table = str.maketrans(dict_emojis)
        message = message.translate(translation_table)
        return message
    except:
        return origin_message

# Hi chat bot
def add_greeting(message, first_name, gender):
    origin_message = message
    try:
        if GREETING_CHATBOT.upper() in message.upper():
            if gender == 'male': gender = 'anh'
            elif gender == 'female': gender = 'chị'
            else: gender = ''
            message += f'. Em chào {gender} {first_name}'
        return message
    except:
        return origin_message

 # Text to audio file
def text_to_audio(text):   
    try:
        tts_fpt(text)
    except:
        audio_gtts = gTTS(text, lang="vi", slow=False,)
        audio_gtts.save(AUDIO_PATH)
    finally:
        pass

def tts_fpt(text):
    global cid_apt_fpt
    voice = 'thuminh'
    payload = {}
    if '!male' in str(text):
        voice = 'giahuy'
        text.replace('!male','')
        
    while True:
        api_key = api_fpt[cid_apt_fpt]
        payload = text
        headers = {
            'api-key': api_key,
            'speed': '',
            'voice': voice
        }
        response_tts = requests.request('POST', URL_FPT, data=payload.encode('utf-8'), headers=headers)
        data_tts = json.loads(response_tts.content.decode('utf-8'))
        if 'async' in data_tts:
            async_url = data_tts['async']
            try_count = 0
            while True:
                time.sleep(2)
                response_audio = requests.get(async_url)
                if response_audio.status_code == 200:
                    file_content = response_audio.content
                    with open(AUDIO_PATH, "wb") as f:
                        f.write(file_content)
                    break
                else:
                    try_count += 1
                    if try_count > 1:
                        raise Exception
            break

        else:
            cid_apt_fpt += 1
            if cid_apt_fpt > 9:
                raise Exception
   
# Create image
def create_image(image, text1, text2):
    try:
        text1_bbox = FONT_1.getbbox(text1)
        text2_bbox = FONT_2.getbbox(text2)
        max_bbox = max(text1_bbox[2],text2_bbox[2])

        new_width = image.width + max_bbox + 28
        new_height = 96 #image.height + 16

        new_image = Image.new('RGBA', (new_width, new_height))

        for x in range(new_image.width):
            alpha = int((1.0 - x / float(new_image.width - 1)) * START_COLOR[3])
            color = START_COLOR[:3] + (alpha,)
            draw = ImageDraw.Draw(new_image)
            draw.line((x, 0, x, new_image.height), fill=color)

        new_image.paste(image, (8, int((96 - image.height)/2)))

        text1_position = (image.width + 16, 0)
        text2_position = (image.width + 16, new_height // 2 )

        with Pilmoji(new_image) as pilmoji:
            pilmoji.text(text2_position, text2, font=FONT_2, fill=(255, 255, 255, 255), emoji_position_offset=(0,8))
            pilmoji.text(text1_position, text1, font=FONT_1, fill=(255, 215, 0, 255), emoji_position_offset=(0,6))

        new_image = ImageOps.expand(new_image, border=(6, 0, 0, 0), fill=(255, 100, 0))

        new_image.save(PICTURE_PATH, format='PNG')
    except:
        pass

# Start read
def start():
    print('Started')
    try:
        image = Image.open(IMAGE_START_PATH)
    except:
        pass
    name = NAME_START
    comment = MESSAGE_START
    text_to_audio(f'{name}.{comment}')
    create_image(image, name, comment)

    time.sleep(1)
    playsound.playsound(AUDIO_PATH, block = True)
    print('Running ...')

    time.sleep(8)
    os.remove(AUDIO_PATH)
    os.remove(PICTURE_PATH)

# Loop to read comment every time_sleep seconds
def read_comment_loop():
    global last_id, last_message
    while True:
        try:
            response = requests.get(url_comment, params=params_comment, cookies=cookie)
            json_data = json.loads(response.content.decode('utf-8'))
            
            if len(json_data["data"]) > 0:
                latest_comment = json_data["data"][0]
                id = latest_comment['id']
                message = latest_comment['message']

                if id != last_id and message != last_message and message != '':
                    last_message = message
                    last_id = id

                    name = latest_comment['from']['name']
                    first_name = latest_comment['from']['first_name']
                    gender = latest_comment['from']['gender']

                    picture_url = latest_comment["from"]["picture"]["data"]["url"]
                    message = message.strip().replace('\n',' ')

                    cut_message = trim_message(message)   

                    read_message = remove_char(cut_message)
                    read_message = replace_words(read_message)
                    read_message = replace_emojis(read_message) 
                    read_message = add_greeting(read_message, first_name, gender)

                    read_content = f"{name}. {read_message[:80]}" 

                    show_name = f"{name}"
                    show_comment = cut_message
                    if len(message) > 60: show_comment += ' ...'
                    
                    with urllib.request.urlopen(picture_url) as response:
                        image_data = response.read()                                  
                        show_avatar = Image.open(BytesIO(image_data)) 

                    text_to_audio(read_content)                                 
                    create_image(show_avatar, show_name, show_comment)

                    time.sleep(1)
                    playsound.playsound(AUDIO_PATH, block = True)

                    with open(LOG_PATH, 'a', encoding='utf-8') as f:
                        f.write(f"{name}: {message}\n")
                    print(f"{name}: {message}")

                    time.sleep(8)
                    os.remove(AUDIO_PATH)
                    os.remove(PICTURE_PATH)

        except Exception as e:
            print(f"Error in read_loop: {e}")       

        finally: time.sleep(time_sleep)

# Main =========================================================================================================
load_file()
get_access_token()
get_video_id()
start()
read_comment_loop()

