# Indian Multilingual Voice Assistant

The EGSPEC assistant supports both text and voice interaction.

## Languages
- English (India) — `en-IN`
- Tamil — `ta-IN`
- Hindi — `hi-IN`
- Telugu — `te-IN`
- Malayalam — `ml-IN`
- Kannada — `kn-IN`
- Thanglish text — response support through the existing multilingual chatbot pipeline; voice uses the Indian English locale.

## How it works
1. The microphone button uses the browser Web Speech Recognition API.
2. The selected sidebar language is sent to the existing `/api/v1/chat` endpoint.
3. The chatbot returns text plus the resolved response language.
4. The browser Speech Synthesis API chooses the best installed Indian-locale voice and speaks the answer.
5. Users can disable spoken replies or replay any assistant answer.

No extra cloud voice API key is required by this integration. Browser voice availability varies by operating system/browser. Chrome on Android typically provides the best experience. If a matching Indian voice is unavailable, the UI falls back to the closest language voice or text-only behavior.
# Real-Time Voice Streaming

CampusMind now supports a secure FastAPI WebSocket at
`/api/v1/voice/stream`. The browser captures mono audio, downsamples it to
16 kHz PCM16, and sends binary frames while the user speaks.

Pipeline:

`Microphone -> PCM16 WebSocket -> Silero VAD -> Faster-Whisper -> secured RAG -> answer chunks -> Piper/Edge-TTS -> browser playback`

Tap the microphone button once to start and again to stop. Partial transcripts
appear while recording. The final transcript is grounded through the same RAG,
rate/security, session, logging and citation pipeline used by text chat.

Defaults are CPU-friendly: Faster-Whisper `small`, CPU, INT8, beam size 1. The
first use may download the selected STT model. Use `base` or `tiny` on slower
laptops. Edge-TTS needs internet. For offline audio replies, install Piper and
set `VOICE_TTS_ENGINE=piper` plus `PIPER_MODEL_PATH`.

If the server voice dependencies are unavailable, the frontend falls back to
the browser SpeechRecognition/SpeechSynthesis implementation and text chat
continues working.

Protocol events: `ready`, `partial_transcript`, `final_transcript`, `status`,
`answer_chunk`, `answer_complete`, `audio_start`, binary audio frames,
`audio_end`, `no_speech`, `tts_unavailable`, `error`, and `done`.
