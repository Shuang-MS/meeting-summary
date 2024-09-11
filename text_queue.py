import threading
import time
import unicodedata
import editdistance

def normalize_text(text):
    text = text.lower()
    normalized_text = ''
    for ch in text:
        if ch.isalnum() or ch.isspace():
            normalized_text += ch
        else:
            normalized_text += ' '
    return normalized_text

def lmatch(text, sub_text):
    min_distance = 65536
    min_distance_pos = 0
    
    i = 1
    normalized_text = ''
    normalized_sub_text = normalize_text(sub_text)
    for ch in text:
        normalized_text += normalize_text(ch)
        if len(normalized_text) + 10 > len(normalized_sub_text) and len(normalized_text) < len(normalized_sub_text) + 10:
            distance = editdistance.eval(normalized_text, normalized_sub_text)
            if distance < min_distance:
                min_distance = distance
                min_distance_pos = i
        i += 1
    return min_distance_pos

def ltrim(text):
    current_pos = 0
    for index, char in enumerate(text[current_pos:]):
        if not (char.isspace() or unicodedata.category(char).startswith('P')):
            current_pos = index
            break
    return text[current_pos:], current_pos


sentence_end_punctuations = ['.','。','!','！', '?', '？']
def rfind_sentence_end(text):
    i = len(text) - 1
    while i > -1:
        if text[i] in sentence_end_punctuations:
            return i
        i -= 1
    return i

partial_sentence_end_punctuations = [',', '，', ';', '；']
def rfind_partial_sentence_end(text):    
    i = len(text) - 1
    while i > -1:
        if text[i] in partial_sentence_end_punctuations:
            return i
        i -= 1
    return i


class TextQueue:
    def __init__(self):
        self.lock = threading.Lock()
        self.start_time = None
        self.partial = None
        self.taken = None
        self.queue = []

    def put(self, text):
        with self.lock:
            if self.taken:
                text, _ = ltrim(text[lmatch(text, self.taken):])
            self.queue.append(text)
            self.taken = None
            self.start_time = None
            self.partial = None

    def put_partial(self, text):
        with self.lock:
            self.partial = text
            if self.start_time is None:
                self.start_time = time.time()

    def get(self, min_wait_time=0):
        while True:
            with self.lock:
                if self.queue:
                    return self.queue.pop(0)
                
                if self.start_time is None:
                    return None
            
                if time.time() - self.start_time > min_wait_time:
                    start = 0
                    if self.taken:
                        start = lmatch(self.partial, self.taken)
                    text, n = ltrim(self.partial[start:])
                    
                    end = rfind_sentence_end(text)
                    if end > 0 and len(text[:end]) > 6:
                        text = text[:end]
                        self.taken = self.partial[:start + n + end]
                        return text
                    
                    if self.taken is None:
                        end = rfind_partial_sentence_end(text)
                        if end > 0 and len(text[:end]) > 6:
                            text = text[:end]
                            self.taken = self.partial[:start + n + end]
                            return text
                
            time.sleep(0.1)