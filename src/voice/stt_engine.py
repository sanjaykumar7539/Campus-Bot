from __future__ import annotations
import threading
from config import config
from .audio_processing import pcm16_to_float32


class FasterWhisperSTT:
    _model=None;_lock=threading.Lock()
    def _get_model(self):
        if self.__class__._model is None:
            with self._lock:
                if self.__class__._model is None:
                    from faster_whisper import WhisperModel
                    self.__class__._model=WhisperModel(config.VOICE_STT_MODEL,device=config.VOICE_STT_DEVICE,
                        compute_type=config.VOICE_STT_COMPUTE_TYPE,cpu_threads=config.VOICE_STT_CPU_THREADS)
        return self.__class__._model
    def transcribe(self,pcm: bytes,language: str|None=None) -> dict:
        model=self._get_model();audio=pcm16_to_float32(pcm)
        lang=None if not language or language in {'auto','tanglish'} else language
        segments,info=model.transcribe(audio,language=lang,beam_size=1,best_of=1,temperature=0.0,
            vad_filter=False,condition_on_previous_text=False,word_timestamps=False)
        text=' '.join(s.text.strip() for s in segments if s.text.strip()).strip()
        return {'text':text,'language':getattr(info,'language',lang or 'en'),
                'language_probability':float(getattr(info,'language_probability',0.0) or 0.0)}
