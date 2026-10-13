from __future__ import annotations
import math
from array import array


def pcm16_to_float32(data: bytes):
    import numpy as np
    samples=np.frombuffer(data,dtype='<i2').astype(np.float32)
    return samples/32768.0


def audio_duration(data: bytes, sample_rate: int=16000) -> float:
    return len(data)/2/max(sample_rate,1)


def rms_energy(data: bytes) -> float:
    values=array('h');values.frombytes(data[:len(data)-(len(data)%2)])
    if not values:return 0.0
    return math.sqrt(sum(float(v)*v for v in values)/len(values))/32768.0


class VoiceActivityDetector:
    """Silero VAD with a deterministic RMS fallback for offline-safe startup."""
    def __init__(self,threshold: float=0.5,min_energy: float=0.012):
        self.threshold,self.min_energy=threshold,min_energy;self.model=None;self._attempted=False
    def _load(self):
        if self._attempted:return self.model
        self._attempted=True
        try:
            from silero_vad import load_silero_vad
            self.model=load_silero_vad()
        except Exception as exc:print(f'Silero VAD unavailable; RMS fallback active: {exc}')
        return self.model
    def contains_speech(self,data: bytes,sample_rate: int=16000) -> bool:
        if audio_duration(data,sample_rate)<0.12:return False
        model=self._load()
        if model:
            try:
                import torch
                from silero_vad import get_speech_timestamps
                audio=torch.from_numpy(pcm16_to_float32(data))
                with torch.no_grad():
                    stamps=get_speech_timestamps(audio,model,threshold=self.threshold,sampling_rate=sample_rate)
                return bool(stamps)
            except Exception:pass
        return rms_energy(data)>=self.min_energy
