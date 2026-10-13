import logo from '../assets/egspec-logo.svg';

export default function Header({
  onNewChat,
  lang,
  setLang,
  langs,
  autoSpeak,
  setAutoSpeak,
  speaking,
  supported,
}) {
  return (
    <header className="header">
      <a href="/" className="brandLogoLink" aria-label="EGS Pillay Engineering College">
        <img src={logo} alt="EGS Pillay Engineering College" className="brandLogo" />
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
  );
}
