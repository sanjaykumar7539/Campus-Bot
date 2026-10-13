const CARDS = [
  {
    icon: '📋',
    label: 'Latest Updates',
    desc: 'Circulars & news',
    q: 'What are the latest EGSPEC updates?',
    gradient: 'linear-gradient(135deg, rgba(175,0,95,0.25), rgba(80,20,60,0.15))',
  },
  {
    icon: '🎓',
    label: 'Admissions',
    desc: 'Courses & intake',
    q: 'Tell me about EGSPEC admissions',
    gradient: 'linear-gradient(135deg, rgba(0,27,112,0.35), rgba(30,60,120,0.15))',
  },
  {
    icon: '📝',
    label: 'Examinations',
    desc: 'Schedules & results',
    q: 'Tell me about EGSPEC examinations',
    gradient: 'linear-gradient(135deg, rgba(175,0,95,0.2), rgba(0,40,80,0.2))',
  },
  {
    icon: '🏛️',
    label: 'Departments',
    desc: 'Branches & faculty',
    q: 'Show EGSPEC departments',
    gradient: 'linear-gradient(135deg, rgba(0,40,90,0.35), rgba(175,0,95,0.12))',
  },
];

export default function Landing({
  onAsk,
  input,
  setInput,
  onSubmit,
  listening,
  onVoice,
  voiceHint,
}) {
  return (
    <div className="landing">
      <section className="hero">
        <div className="heroCopy">
          <div className="heroBadge">✦ Official campus AI assistant</div>
          <h1>
            Ask<span>EGSPEC</span>
          </h1>
          <div className="underline" />
          <p className="heroTag">
            Grounded answers from verified E.G.S. Pillay Engineering College sources.
            Type or speak in English, Tamil, Hindi, and more.
          </p>
          <div className="heroStats">
            <div className="stat">
              <strong>NAAC</strong>
              <span>A++</span>
            </div>
            <div className="stat">
              <strong>NBA</strong>
              <span>Tier-I</span>
            </div>
            <div className="stat">
              <strong>Est.</strong>
              <span>1995</span>
            </div>
          </div>
        </div>
        <div className="heroVisual" aria-hidden="true">
          <div className="heroGlow" />
          <div className="heroMotto">LEARN · GROW · LEAD</div>
          <svg className="campusArt" viewBox="0 0 720 280">
            <defs>
              <linearGradient id="buildingGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#8ec0f0" stopOpacity="0.5" />
                <stop offset="100%" stopColor="#3a6a9a" stopOpacity="0.2" />
              </linearGradient>
              <linearGradient id="accentLine" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#af005f" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#5eb8ff" stopOpacity="0.4" />
              </linearGradient>
            </defs>
            <path d="M20 240H700" stroke="url(#accentLine)" strokeWidth="1.5" fill="none" />
            {/* trees */}
            <ellipse cx="70" cy="200" rx="18" ry="28" fill="#1a4a6a" opacity="0.5" />
            <ellipse cx="650" cy="195" rx="22" ry="32" fill="#1a4a6a" opacity="0.45" />
            {/* buildings */}
            <path d="M55 240V175l60-32 60 32v65" stroke="#6b9bc7" strokeWidth="1.4" fill="url(#buildingGrad)" />
            <path d="M185 240V145h90v95" stroke="#6b9bc7" strokeWidth="1.4" fill="url(#buildingGrad)" />
            <path d="M280 240V95h200v145" stroke="#8eb4d4" strokeWidth="1.5" fill="url(#buildingGrad)" />
            <path d="M480 240V155h90v85" stroke="#6b9bc7" strokeWidth="1.4" fill="url(#buildingGrad)" />
            <path d="M575 240V175l55-28 50 28v65" stroke="#6b9bc7" strokeWidth="1.4" fill="url(#buildingGrad)" />
            {/* windows */}
            <g fill="#5eb8ff" opacity="0.35">
              <rect x="300" y="120" width="12" height="14" rx="1" />
              <rect x="325" y="120" width="12" height="14" rx="1" />
              <rect x="350" y="120" width="12" height="14" rx="1" />
              <rect x="375" y="120" width="12" height="14" rx="1" />
              <rect x="400" y="120" width="12" height="14" rx="1" />
              <rect x="425" y="120" width="12" height="14" rx="1" />
              <rect x="300" y="150" width="12" height="14" rx="1" />
              <rect x="325" y="150" width="12" height="14" rx="1" />
              <rect x="350" y="150" width="12" height="14" rx="1" />
              <rect x="375" y="150" width="12" height="14" rx="1" />
              <rect x="400" y="150" width="12" height="14" rx="1" />
              <rect x="425" y="150" width="12" height="14" rx="1" />
              <rect x="300" y="180" width="12" height="14" rx="1" />
              <rect x="325" y="180" width="12" height="14" rx="1" />
              <rect x="400" y="180" width="12" height="14" rx="1" />
              <rect x="425" y="180" width="12" height="14" rx="1" />
            </g>
            <text x="380" y="88" textAnchor="middle" fill="#b8d4f0" fontSize="15" fontWeight="700" letterSpacing="3">
              EGSPEC
            </text>
            {/* accent dot */}
            <circle cx="380" cy="70" r="4" fill="#af005f" />
          </svg>
          <div className="heroHand">
            A Brighter
            <br />
            Tomorrow Together
          </div>
        </div>
      </section>

      <section className="cards">
        {CARDS.map((c) => (
          <button
            key={c.label}
            className="card"
            type="button"
            onClick={() => onAsk(c.q)}
            style={{ backgroundImage: c.gradient }}
          >
            <div className="cardIcon">{c.icon}</div>
            <div className="cardFoot">
              <div>
                <b>{c.label}</b>
                <small>{c.desc}</small>
              </div>
              <span className="arrow">→</span>
            </div>
          </button>
        ))}
      </section>

      <div className="spacer" />

      <div className="composerWrap">
        <form
          className="composer"
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit();
          }}
        >
          <span className="spark">✦</span>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask EGSPEC anything…"
            aria-label="Ask EGSPEC"
            autoComplete="off"
          />
          <button
            type="button"
            className={`voiceBtn${listening ? ' listening' : ''}`}
            onClick={onVoice}
            aria-label="Voice input"
            title="Speak your question"
          >
            ◉
          </button>
          <button type="submit" className="sendBtn" aria-label="Send">
            ➤
          </button>
        </form>
        <div className={`voiceHint${listening ? ' active' : ''}`}>
          {voiceHint || (listening ? 'Listening… speak now' : 'Tap the mic to speak')}
        </div>
        <div className="siteLink">
          <a href="https://www.egspec.org" target="_blank" rel="noopener noreferrer">
            EGSPEC Official Website ↗
          </a>
        </div>
      </div>
    </div>
  );
}
