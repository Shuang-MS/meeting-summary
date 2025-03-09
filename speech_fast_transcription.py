import datetime
import json
import logging
import requests
import os
import time
from dotenv import load_dotenv


LOCALES = ["zh-CN", "en-US"]

load_dotenv()
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")
SPEECH_API_VERSION = os.getenv('SPEECH_API_VERSION', "2024-11-15")


time_line = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
logger = logging.getLogger()

def print_message(message):
     print('[{}]{}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message))
     logger.info(message)

def fast_transcript(audio):
    print_message("Get fast transcription start.")
    print_message("Speeck key: " + SPEECH_KEY)
    print_message("Speeck region: " + SPEECH_REGION)
    

    url = f"https://{SPEECH_REGION}.api.cognitive.microsoft.com/speechtotext/transcriptions:transcribe?api-version={SPEECH_API_VERSION}"
    print_message("Url: " + url)

    result = None
    if audio:
        print_message("Processing audio file")
        data = {
            "definition": json.dumps({
                'locales': LOCALES,
                'profanityFilterMode': 'Masked',
                'diarization': {
                    'maxSpeakers': 10,
                    'enabled': True}
            })
        }

        headers = {
            "Ocp-Apim-Subscription-Key": SPEECH_KEY,
            "Accept": "application/json"
        }

        files = {
            "audio": audio.getvalue()
        }

        response = requests.post(url, files=files, headers=headers, data=data)
        print(response.status_code)
    
    if response.status_code == 200:
        json_response = response.json()
        phrases = json_response.get('phrases', [])
        sb = ["Transcriptions: \n"]

        for phrase in phrases:
            content = format_speaker_segment(phrase)
            sb.append(content)

        result = ' '.join(sb)
        print_message("Result : " + result)
    else:
        print_message("Try to get fast transcription result")
        

    print_message("Get fast transcription end.")
    return result

def ms_to_timestamp(ms):
    total_seconds = ms / 1000
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def format_speaker_segment(speaker_data):
    if not speaker_data:
        return ""
    
    start_ms = speaker_data.get('offsetMilliseconds', 0)
    duration_ms = speaker_data.get('durationMilliseconds', 0)
    end_ms = start_ms + duration_ms
    
    start_timestamp = ms_to_timestamp(start_ms)
    end_timestamp = ms_to_timestamp(end_ms)
    
    speaker_num = speaker_data.get('speaker', 'Unknown')
    text = speaker_data.get('text', '')
    
    return f"[{start_timestamp} - {end_timestamp}] Speaker {speaker_num}: {text}\n"