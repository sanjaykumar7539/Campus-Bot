import { useEffect, useRef } from 'react';

export default function Chat({
  messages,
  streaming,
  quickReplies,
  onAsk,
  input,
  setInput,
  onSubmit,
  listening,
  onVoice,
  onSpeak,
  speaking,
  voiceHint,
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streaming]);

  return (
    <div className="chatScreen">
      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            <div className="avatar">{m.role === 'user' ? 'You' : 'AI'}</div>
            <div className="bubble">
              {m.error ? (
                <p className="errorText">{m.content}</p>
              ) : (
                (m.content || '').split('\n').map((line, j) => (
                  <p key={j}>{line || '\u00A0'}</p>
                ))
              )}
              {m.role === 'bot' && m.content && !m.error && (
                <div className="msgActions">
                  <button
                    type="button"
                    className={speaking ? 'active' : ''}
                    onClick={() => onSpeak(m.content)}
                    title="Speak this answer"
                  >
                    {speaking ? '⏹ Stop' : '🔊 Speak'}
                  </button>
                </div>
              )}
              {m.sources?.length > 0 && (
                <div className="sources">
                  <div className="sourcesTitle">Verified sources</div>
                  {m.sources.map((s, k) => (
                    <div key={k} className="sourceCard">
                      <b>{s.document || 'Institute document'}</b>
                      <span>
                        Page {s.page ?? '—'}
                        {Number.isFinite(Number(s.relevance_score))
                          ? ` · ${Math.round(Number(s.relevance_score) * 100)}% match`
                          : ''}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {streaming &&
          messages[messages.length - 1]?.role === 'bot' &&
          !messages[messages.length - 1]?.content && (
            <div className="message bot">
              <div className="avatar">AI</div>
              <div className="bubble">
                <div className="typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          )}
        <div ref={bottomRef} />
      </div>

      {quickReplies?.length > 0 && (
        <div className="quickReplies">
          {quickReplies.map((r) => (
            <button key={r} type="button" onClick={() => onAsk(r)}>
              {r}
            </button>
          ))}
        </div>
      )}

      <div className="chatComposerBar">
        <form
          className="composer"
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit();
          }}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask EGSPEC…"
            aria-label="Ask EGSPEC"
            autoComplete="off"
            disabled={streaming}
          />
          <button
            type="button"
            className={`voiceBtn${listening ? ' listening' : ''}`}
            onClick={onVoice}
            aria-label="Voice input"
          >
            ◉
          </button>
          <button
            type="submit"
            className="sendBtn"
            disabled={streaming || !input.trim()}
            aria-label="Send"
          >
            ➤
          </button>
        </form>
        <div className={`voiceHint${listening ? ' active' : ''}`}>
          {voiceHint || ''}
        </div>
      </div>
    </div>
  );
}
