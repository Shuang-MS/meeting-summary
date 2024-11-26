import azure.cognitiveservices.speech as speechsdk
import threading
import time
from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential
from text_queue import TextQueue
import wave


service_key = "" 
service_endpoint = "https://api.cognitive.microsofttranslator.com"
service_region = "eastus"

class CancellationError(Exception):
    def __init__(self, code, details, *args):
        super().__init__(*args)
        self.code = code
        self.details = details

def push_stream_writer(filename, stream):
    start_time_0 = time.time()

    wf = wave.open(filename)
    frame_size = 4096  # 每次推送的数据块大小
    frame_rate = wf.getframerate()
    frame_duration = frame_size / frame_rate

    while True:
        start_time = time.time()
        data = wf.readframes(frame_size)
        if not data:
            break
        stream.write(data)
        elapsed_time = time.time() - start_time
        # time.sleep(frame_duration - elapsed_time)
        time.sleep(0.1)
    stream.close()
    wf.close()

    elapsed_time_0 = time.time() - start_time_0
    print(f'{elapsed_time_0:.1f}s: push audio finished')

def speech_recognize_continuous(filename, source_language, target_language):
    """performs continuous speech recognition with input from an audio file"""
    speech_config = speechsdk.SpeechConfig(subscription=service_key, region=service_region)
    #speech_config.set_property(speechsdk.PropertyId.Speech_LogFilename, "speech.log")
    #speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode, "Continuous")
    #speech_config.set_property(speechsdk.PropertyId.SpeechServiceResponse_StablePartialResultThreshold, "5")
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceResponse_RequestWordLevelTimestamps, "True")
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceResponse_PostProcessingOption, "TrueText")
    speech_config.set_profanity(speechsdk.ProfanityOption.Raw)
    speech_config.output_format = speechsdk.OutputFormat.Detailed
    speech_config.request_word_level_timestamps()

    # Setup the audio stream
    stream = speechsdk.audio.PushAudioInputStream()
    audio_config = speechsdk.audio.AudioConfig(stream=stream)

    #auto_detect_source_language_config = \
    #    speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=["en-US", "hi-IN", "zh-CN", "es-ES", "it-IT", "ja-JP"])

    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        language= source_language, 
        #auto_detect_source_language_config=auto_detect_source_language_config,
        audio_config=audio_config)
        #speech_recognizer.properties.set_property(speechsdk.PropertyId.AudioConfig_AudioSource, "FILE")

    done = False
    error = None
    queue = TextQueue()
    start_time = time.time()

    def stop_cb(evt: speechsdk.SessionEventArgs):
        """callback that signals to stop continuous recognition upon receiving an event `evt`"""
        # print('CLOSING on {}'.format(evt))
        nonlocal done
        done = True

    def cancel_cb(evt: speechsdk.SpeechRecognitionCanceledEventArgs):
        """callback that signals to stop continuous recognition upon receiving an event `evt`"""
        # print('CANCELING on {}'.format(evt))
        error_details = evt.error_details
        if error_details.error_code != speechsdk.CancellationErrorCode.NoError:
            # print('Error on {}'.format(evt.cancellation_details))
            nonlocal error
            error = CancellationError(error_details.error_code, error_details.error_details)

    def recognized_cb(evt: speechsdk.SpeechRecognitionEventArgs):
        # print(f'recognized: {evt.result}\n')
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            nonlocal queue, start_time
            queue.put(evt.result.text)
            elapsed = time.time() - start_time
            print(f'{elapsed:.1f}s: recognized: {evt.result.text}')


    def recognizing_cb(evt: speechsdk.SpeechRecognitionEventArgs):
        # print(f'recognizing: {evt.result.json}')
        if evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
            nonlocal queue, start_time
            queue.put_partial(evt.result.text)
            elapsed = time.time() - start_time
            print(f'{elapsed:.1f}s: recognizing: {evt.result.text}')


    # Connect callbacks to the events fired by the speech recogn-----izer
    speech_recognizer.recognizing.connect(recognizing_cb)
    speech_recognizer.recognized.connect(recognized_cb)
    # speech_recognizer.session_started.connect(lambda evt: print('SESSION STARTED: {}'.format(evt)))
    # speech_recognizer.session_stopped.connect(lambda evt: print('SESSION STOPPED {}'.format(evt)))
    # speech_recognizer.canceled.connect(lambda evt: print('CANCELED {}'.format(evt)))
    # Stop continuous recognition on either session stopped or canceled events
    speech_recognizer.session_stopped.connect(stop_cb)
    #speech_recognizer.canceled.connect(cancel_cb)

    connection = speechsdk.Connection.from_recognizer(speech_recognizer)
    connection.set_message_property('speech.context', 'phraseDetection', '{"mode":"CONVERSATION","language":"' + source_language + '","enrichment":{"conversation":{"intermediatePunctuationMode":"Implicit"}}}')
    connection.open(for_continuous_recognition=True)

    
    # Creates a speech synthesizer using the default speaker as audio output.
    # The default spoken language is "en-us".
    # speech_config = speechsdk.SpeechConfig(subscription=service_key, region=service_region)
    # speech_config.speech_synthesis_language = target_language    
    # speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    # connection = speechsdk.Connection.from_speech_synthesizer(speech_synthesizer)
    # connection.open(True)

    credential = AzureKeyCredential("")
    text_translator = TextTranslationClient(credential=credential, region="eastus", endpoint=service_endpoint)
    text_translator.translate(body=[""], to_language=[target_language], from_language=source_language)
    # Start continuous speech recognition
    speech_recognizer.start_continuous_recognition()

    start_time = time.time()
    print('0.0s: starting')

    push_stream_writer_thread = threading.Thread(target=push_stream_writer, args=[filename, stream])
    push_stream_writer_thread.start()
        
    while not done:
        while True:
            text = queue.get()
            if text is None:
                break

            elapsed = time.time() - start_time
            print(f'{elapsed:.1f}s: translating: {text}')

            try:
                response = text_translator.translate(body=[text], to_language=[target_language], from_language=source_language)
            except Exception as e:
                print(f'error: {e}')

            translated = response[0]['translations'][0]['text']
            elapsed = time.time() - start_time            
            print(f'{elapsed:.1f}s: translated: {translated}')

        #     elapsed = time.time() - start_time
        #     print(f'{elapsed:.1f}s: speaking: {translated}')
            
        #     result = speech_synthesizer.speak_text_async(translated).get()
        #     elapsed = time.time() - start_time
        #     print(f'{elapsed:.1f}s: spoken: {translated}')

        time.sleep(.1)

    speech_recognizer.stop_continuous_recognition()


filename = r"C:\work\microsoft\tmp\ai\speech\translation\audio\866202611-1-208_4.wav"

speech_recognize_continuous(filename, source_language="en-US", target_language="zh-CN")