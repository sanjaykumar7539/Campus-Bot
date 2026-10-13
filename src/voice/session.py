from __future__ import annotations
import time
from config import config
from .audio_processing import audio_duration

class VoiceSession:
    def __init__(self,sample_rate=16000,language='auto',session_id='voice'):
        self.sample_rate=sample_rate;self.language=language;self.session_id=session_id
        self.buffer=bytearray();self.last_partial_bytes=0;self.created=time.monotonic()
    def append(self,data):
        if len(self.buffer)+len(data)>config.VOICE_MAX_AUDIO_BYTES:raise ValueError('Voice audio limit exceeded')
        self.buffer.extend(data)
    def should_partial(self):
        step=int(self.sample_rate*2*config.VOICE_PARTIAL_INTERVAL_SECONDS)
        return len(self.buffer)-self.last_partial_bytes>=step
    def mark_partial(self):self.last_partial_bytes=len(self.buffer)
    @property
    def duration(self):return audio_duration(self.buffer,self.sample_rate)
