import { useEffect, useRef } from 'react';

const CHAT_TOPICS = [
  ['Institutions under EGSP Group', 'List all colleges under EGS Pillay Group'],
  ['Engineering · TNEA 3806', 'Tell me about EGS Pillay Engineering College'],
  ['Placement records', 'Give EGSPEC placement details including package and recruiters'],
  ['Admissions & cutoff', 'How can I join EGSPEC through TNEA and what cutoff is needed?'],
  ['Scholarships', 'What scholarships are available at EGSPEC and who is eligible?'],
  ['Transport routes', 'List EGSPEC college bus routes and starting times'],
];

function AnswerContent({ text }) {
  const lines = (text || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const protectedText = (text || '').replace(
    /\b(?:(?:B|M)\.(?:E|Tech|Sc|Com|A)\.|Ph\.D|D\.Pharm|B\.Pharm|M\.Pharm|Pharm\.D|(?:[A-Z]\.\s*){2,})/g,
    (value) => value.replaceAll('.', '∯')
  );
  const units = lines.length > 1
    ? lines
    : protectedText
      .split(/(?<=[.!?])\s+/)
      .map((line) => line.replaceAll('∯', '.').trim())
      .filter(Boolean);

  return (
    <div className="answerContent">
      {units.map((unit, index) => {
        const clean = unit.replace(/^[-•]\s*/, '');
        const colon = clean.indexOf(':');
        const listParts = colon >= 0
          ? clean.slice(colon + 1).split(';').map((part) => part.trim()).filter(Boolean)
          : [];
        if (listParts.length >= 3) {
          const title = clean.slice(0, colon + 1);
          return (
            <div className="answerGroup" key={`${index}-${title}`}>
              <strong>{title}</strong>
              <ul>{listParts.map((part) => <li key={part}>{part}</li>)}</ul>
            </div>
          );
        }
        if (!/[.!?]$/.test(clean) && clean.length < 48 && !clean.includes(':')) {
          return <h4 key={`${index}-${clean}`}>{clean}</h4>;
        }
        return <div className="answerPoint" key={`${index}-${clean}`}>{clean}</div>;
      })}
    </div>
  );
}

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
  const messagesRef = useRef(null);

  useEffect(() => {
    const container = messagesRef.current;
    if (container) container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
  }, [messages, streaming]);

  return (
    <div className="chatScreen">
      <aside className="chatSidebar">
        <h3>Central Helpdesk</h3>
        <p>Verified information for EGS Pillay institutions.</p>
        <nav>
          {CHAT_TOPICS.map(([label, question]) => (
            <button key={label} type="button" onClick={() => onAsk(question)}>
              <span>{label}</span><b>→</b>
            </button>
          ))}
        </nav>
        <div className="sidebarAddress">
          <b>Campus location</b>
          <span>Old Nagore Road, Thethi Village, Nagapattinam – 611002</span>
        </div>
        <div className="sidebarStatus"><i /> Knowledge base online</div>
      </aside>
      <section className="chatPanel">
        <div className="chatPanelHeader">
          <div className="assistantMark">AI</div>
          <div><b>EGSPEC Campus Assistant</b><small>Official verified helpdesk</small></div>
        </div>
      <div className="messages" ref={messagesRef} tabIndex="0" aria-label="Conversation history">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            <div className="avatar">{m.role === 'user' ? 'You' : 'AI'}</div>
            <div className="bubble">
              {m.error ? (
                <p className="errorText">{m.content}</p>
              ) : (
                <AnswerContent text={m.content} />
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
      </section>
    </div>
  );
}
