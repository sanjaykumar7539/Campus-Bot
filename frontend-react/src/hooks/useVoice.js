import { useState, useCallback, useRef, useEffect } from 'react';

export const VOICE_LANGS = [
  { code: 'en-IN', label: 'English (India)', tts: 'en-IN' },
  { code: 'ta-IN', label: 'தமிழ் (Tamil)', tts: 'ta-IN' },
  { code: 'hi-IN', label: 'हिन्दी (Hindi)', tts: 'hi-IN' },
  { code: 'te-IN', label: 'తెలుగు (Telugu)', tts: 'te-IN' },
  { code: 'ml-IN', label: 'മലയാളം (Malayalam)', tts: 'ml-IN' },
  { code: 'kn-IN', label: 'ಕನ್ನಡ (Kannada)', tts: 'kn-IN' },
];

function pickVoice(langCode) {
  if (!window.speechSynthesis) return null;
  const voices = window.speechSynthesis.getVoices();
  const base = langCode.split('-')[0];
  return (
    voices.find((v) => v.lang === langCode) ||
    voices.find((v) => v.lang.startsWith(base) && v.lang.includes('IN')) ||
    voices.find((v) => v.lang.startsWith(base)) ||
    voices.find((v) => v.lang.startsWith('en')) ||
    null
  );
}

export function useVoice(defaultLang = 'en-IN') {
  const [lang, setLang] = useState(defaultLang);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  // Voice must be opt-in. Remember an explicit choice, but default to silent.
  const [autoSpeak, setAutoSpeakState] = useState(
    () => localStorage.getItem('egspec_auto_speak') === 'true'
  );
  const [supported, setSupported] = useState({ stt: false, tts: false });
  const recognitionRef = useRef(null);
  const utterRef = useRef(null);

  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    setSupported({
      stt: Boolean(SR),
      tts: Boolean(window.speechSynthesis),
    });
    // Load voices
    if (window.speechSynthesis) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
      };
    }
  }, []);

  const setAutoSpeak = useCallback((enabled) => {
    const next = Boolean(enabled);
    localStorage.setItem('egspec_auto_speak', String(next));
    setAutoSpeakState(next);
    if (!next && window.speechSynthesis) window.speechSynthesis.cancel();
    if (!next) {
      setSpeaking(false);
      utterRef.current = null;
    }
  }, []);

  const stopSpeaking = useCallback(() => {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    setSpeaking(false);
    utterRef.current = null;
  }, []);

  const speak = useCallback(
    (text, langOverride) => {
      if (!text || !window.speechSynthesis) return;
      stopSpeaking();
      const u = new SpeechSynthesisUtterance(text);
      const code = langOverride || lang;
      u.lang = code;
      const voice = pickVoice(code);
      if (voice) u.voice = voice;
      u.rate = 1;
      u.pitch = 1;
      u.onstart = () => setSpeaking(true);
      u.onend = () => setSpeaking(false);
      u.onerror = () => setSpeaking(false);
      utterRef.current = u;
      window.speechSynthesis.speak(u);
    },
    [lang, stopSpeaking]
  );

  const startListening = useCallback(
    (onResult) => {
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SR) return false;

      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
        setListening(false);
        return false;
      }

      stopSpeaking();
      const rec = new SR();
      rec.lang = lang;
      rec.interimResults = true;
      rec.continuous = false;
      setListening(true);

      rec.onresult = (e) => {
        let text = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
          text += e.results[i][0].transcript;
        }
        onResult?.(text.trim(), e.results[e.results.length - 1]?.isFinal);
      };
      rec.onerror = () => {
        setListening(false);
        recognitionRef.current = null;
      };
      rec.onend = () => {
        setListening(false);
        recognitionRef.current = null;
      };

      recognitionRef.current = rec;
      rec.start();
      return true;
    },
    [lang, stopSpeaking]
  );

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setListening(false);
  }, []);

  return {
    lang,
    setLang,
    listening,
    speaking,
    autoSpeak,
    setAutoSpeak,
    supported,
    speak,
    stopSpeaking,
    startListening,
    stopListening,
    langs: VOICE_LANGS,
  };
}
