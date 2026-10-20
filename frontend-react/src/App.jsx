import { useState, useCallback, useRef, useEffect } from 'react';
import Header from './components/Header';
import Chat from './components/Chat';
import { useChat } from './hooks/useChat';
import { useVoice } from './hooks/useVoice';

export default function App() {
  const [input, setInput] = useState('');
  const [voiceHint, setVoiceHint] = useState('');
  const lastSpokenRef = useRef('');
  const { messages, streaming, quickReplies, send, reset } = useChat();
  const {
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
    langs,
  } = useVoice('en-IN');

  // Auto-speak completed bot answers
  useEffect(() => {
    if (!autoSpeak || streaming || !supported.tts) return;
    const last = messages[messages.length - 1];
    if (
      last?.role === 'bot' &&
      last.content &&
      !last.error &&
      last.content !== lastSpokenRef.current
    ) {
      lastSpokenRef.current = last.content;
      speak(last.content);
    }
  }, [messages, streaming, autoSpeak, speak, supported.tts]);

  const ask = useCallback(
    (text) => {
      const q = (text || input).trim();
      if (!q) return;
      stopSpeaking();
      setInput('');
      setVoiceHint('');
      send(q);
    },
    [input, send, stopSpeaking]
  );

  const onNewChat = () => {
    stopSpeaking();
    stopListening();
    reset();
    setInput('');
    setVoiceHint('');
    lastSpokenRef.current = '';
  };

  const onVoice = () => {
    if (listening) {
      stopListening();
      setVoiceHint('');
      return;
    }
    const ok = startListening((text, isFinal) => {
      setInput(text);
      if (isFinal && text) {
        setVoiceHint('Got it — send or edit your question');
      }
    });
    if (ok) setVoiceHint('Listening… speak now');
    else setVoiceHint('Voice input not supported in this browser');
  };

  const onSpeak = (text) => {
    if (speaking) stopSpeaking();
    else speak(text);
  };

  return (
    <div className="app">
      <Header
        onNewChat={onNewChat}
        lang={lang}
        setLang={setLang}
        langs={langs}
        autoSpeak={autoSpeak}
        setAutoSpeak={setAutoSpeak}
        speaking={speaking}
        supported={supported}
        onAsk={ask}
      />
      <Chat
          messages={messages}
          streaming={streaming}
          quickReplies={quickReplies}
          onAsk={ask}
          input={input}
          setInput={setInput}
          onSubmit={() => ask()}
          listening={listening}
          onVoice={onVoice}
          onSpeak={onSpeak}
          speaking={speaking}
          voiceHint={voiceHint}
        />
    </div>
  );
}
