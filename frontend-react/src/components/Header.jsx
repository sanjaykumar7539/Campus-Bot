import logo from '../assets/egspec-logo.svg';

const INSTITUTIONS = [
  ['All Group Institutions', 'List all colleges under EGS Pillay Group'],
  ['Engineering · TNEA 3806', 'Tell me about EGS Pillay Engineering College'],
  ['Arts & Science · EGSPASC', 'What courses are available in EGS Pillay Arts and Science College?'],
  ['Polytechnic College', 'Tell me about EGS Pillay Polytechnic diploma courses'],
  ['College of Pharmacy', 'Tell me about EGS Pillay College of Pharmacy'],
  ['College of Nursing', 'Tell me about EGS Pillay College of Nursing'],
  ['Naturopathy & Yoga · BNYS', 'Tell me about EGS Pillay Naturopathy and Yoga Medical College'],
  ['International / Matric Schools', 'Tell me about EGS Pillay International School'],
];

export default function Header({
  onNewChat,
  lang,
  setLang,
  langs,
  autoSpeak,
  setAutoSpeak,
  speaking,
  supported,
  onAsk,
}) {
  return (
    <>
      <div className="topBar">
        <span className="topContacts">
          <a href="tel:+919363087377">+91 93630 87377</a><i />
          <a href="mailto:admission@egspec.org">admission@egspec.org</a>
          <mark>Admissions Open 2026–27</mark>
        </span>
        <span className="tneaBadge"><small>TNEA<br />CODE</small><b>3806</b></span>
      </div>
      <header className="header">
        <a href="/" className="brandLogoLink" aria-label="EGS Pillay Engineering College">
          <img src={logo} alt="EGS Pillay Engineering College" className="brandLogo" />
          <span className="brandCopy">
            <b>E.G.S. Pillay Group of Institutions</b>
            <small>A Premier Educational Group in the Cauvery Delta Region · Nagapattinam, Tamil Nadu</small>
          </span>
        </a>
        <div className="headerActions">
        {supported.tts && (
          <div className="voiceBar" title="Voice settings">
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              aria-label="Voice language"
            >
              {langs.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </select>
            <label className="toggle">
              <input
                type="checkbox"
                checked={autoSpeak}
                onChange={(e) => setAutoSpeak(e.target.checked)}
              />
              <span>Auto-speak{speaking ? ' ●' : ''}</span>
            </label>
          </div>
        )}
        <button className="iconBtn primary" onClick={onNewChat} aria-label="New chat">
          ＋ <span>New Chat</span>
        </button>
        </div>
      </header>
      <nav className="institutionTabs" aria-label="Institution quick selector">
        {INSTITUTIONS.map(([label, question], index) => (
          <button key={label} className={index === 0 ? 'active' : ''} type="button" onClick={() => onAsk(question)}>
            {label}
          </button>
        ))}
      </nav>
    </>
  );
}
