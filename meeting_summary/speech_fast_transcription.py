import datetime
import json
import logging
import requests
import os
import time
from dotenv import load_dotenv


LOCALE = "zh-CN"

load_dotenv()
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")


time_line = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
logger = logging.getLogger()

def print_message(message):
     print('[{}]{}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message))
     logger.info(message)

def fast_transcript(audio):
    print_message("Get fast transcription start.")
    print_message("Speeck key: " + SPEECH_KEY)
    print_message("Speeck region: " + SPEECH_REGION)
    

    url = f"https://{SPEECH_REGION}.api.cognitive.microsoft.com/speechtotext/transcriptions:transcribe?api-version=2024-05-15-preview"
    print_message("Url: " + url)

    parameters = {
        "locales": [LOCALE],
        "wordLevelTimestampsEnabled": True,
        "profanityFilterMode": "Masked",
        "channels": [0, 1],
        "diarizationSettings": {"minSpeakers": 1,"maxSpeakers":4}
    }
    print_message("Parameter : " + json.dumps(parameters))
    result = None
    if audio:
        files = {
            'definition': (None, json.dumps(parameters), 'application/json'),
            'audio': ('dddd', audio.getvalue(), 'application/octet-stream')
        }
        headers = {'Ocp-Apim-Subscription-Key': SPEECH_KEY}
        response = requests.post(url, files=files, headers=headers)

    if response.status_code == 200:
        json_response = response.json()
        phrases = json_response.get('phrases', [])
        sb = []
        for phrase in phrases:
            text = phrase.get('text', '')
            speaker = phrase.get('speaker', '')
            print_message(f"{speaker}: " + text)
            sb.append(f"{speaker}: " + text)
        result = ' '.join(sb)
        print_message("Result : " + result)
    else:
        print_message("Try to get fast transcription result")
        

    print_message("Get fast transcription end.")
    return result

