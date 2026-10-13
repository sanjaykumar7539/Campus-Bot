from array import array
from src.voice.audio_processing import audio_duration,rms_energy,VoiceActivityDetector
from src.voice.session import VoiceSession
from src.api import voice_routes

def pcm(value,count=16000):
    data=array('h',[value]*count)
    return data.tobytes()

def test_audio_duration_and_energy():
    assert audio_duration(pcm(1000),16000)==1.0
    assert rms_energy(pcm(0))==0.0
    assert rms_energy(pcm(4000))>0.1

def test_vad_rms_fallback(monkeypatch):
    detector=VoiceActivityDetector(min_energy=.02)
    monkeypatch.setattr(detector,'_load',lambda:None)
    assert detector.contains_speech(pcm(4000))
    assert not detector.contains_speech(pcm(0))

def test_voice_session_limits_and_partial(monkeypatch):
    import src.voice.session as module
    monkeypatch.setattr(module.config,'VOICE_MAX_AUDIO_BYTES',64000)
    monkeypatch.setattr(module.config,'VOICE_PARTIAL_INTERVAL_SECONDS',.5)
    session=VoiceSession()
    session.append(pcm(1000,8000))
    assert session.should_partial() and session.duration==.5
    session.mark_partial();assert not session.should_partial()


def test_voice_answer_does_not_add_unverified_visuals(monkeypatch):
    class FakeRAG:
        def invoke(self, **kwargs):
            return {'answer':'Library is in the campus','sources':[],'confidence':.9,'is_grounded':True}
    class FakeLogger:
        def log(self, **kwargs): return 7
    monkeypatch.setattr(voice_routes.chat_routes,'rag_chain',FakeRAG())
    monkeypatch.setattr(voice_routes.chat_routes,'chat_logger',FakeLogger())
    result=voice_routes.answer_question('Where is the library?','en','voice-test-session')
    assert result['message_id']==7
    assert result['visuals']==[]
