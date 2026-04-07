import React, { useState, useRef, useEffect } from 'react';
import { generate, login } from './api';
import './styles.css';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [req, setReq] = useState('');
  const [format, setFormat] = useState('json');
  const [loading, setLoading] = useState(false);

  const [user, setUser] = useState(null);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const [loginDisabled, setLoginDisabled] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (cooldown <= 0) return;

    const timer = setInterval(() => {
      setCooldown((prev) => {
        if (prev <= 1) {
          setLoginDisabled(false);
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [cooldown]);

  // ---------------- LOGIN ----------------
  async function handleLogin() {
    if (!email.trim() || !password.trim()) {
      alert('Enter email and password');
      return;
    }

    if (loginDisabled) return;

    try {
      const res = await login(email, password);
      localStorage.setItem('token', res.token);
      setUser(res.user || email);
    } catch (e) {
      console.error(e);

      if (e.message && e.message.includes('Too many')) {
        setLoginDisabled(true);
        setCooldown(60);
        alert('Too many attempts. Try again in 60 seconds.');
      } else {
        alert('Invalid credentials');
      }
    }
  }

  // 🔥 STREAM FUNCTION (FIXED)
  function streamResponse(fullText) {
    let index = 0;

    const interval = setInterval(() => {
      index++;

      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];

        if (last && last.role === 'assistant') {
          last.content = fullText.slice(0, index);
        }

        return updated;
      });

      if (index >= fullText.length) {
        clearInterval(interval);
      }
    }, 12); // speed control
  }

  // ---------------- GENERATE ----------------
  async function onGenerate() {
    if (!req.trim()) {
      alert('Please enter a requirement.');
      return;
    }

    const userMsg = { role: 'user', content: req };
    setMessages((prev) => [...prev, userMsg]);

    setLoading(true);

    try {
      const r = await generate(req, format);

      let content;

      if (format === 'json') {
        content = JSON.stringify(r.testcases, null, 2);
      } else {
        const raw = typeof r === 'string' ? r : JSON.stringify(r, null, 2);
        content = raw.replace(/\\n/g, '\n').replace(/\\"/g, '"');
      }

      // 🔥 Insert empty assistant message first
      setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

      // 🔥 Start streaming safely
      setTimeout(() => {
        streamResponse(content);
      }, 50);
    } catch (e) {
      console.error(e);
      alert(e.message || 'Error generating output.');
    }

    setLoading(false);
    setReq('');
  }

  function copy(text) {
    navigator.clipboard.writeText(text);
  }

  function formatContent(text) {
    return text.split('\n').map((line, i) => {
      if (line.trim() === '') return <br key={i} />;
      return <div key={i}>{line}</div>;
    });
  }

  // ---------------- LOGIN SCREEN ----------------
  if (!user) {
    return (
      <div className="login-container">
        <h1>AI Test Case Agent</h1>

        <input type="email" placeholder="Enter email" value={email} onChange={(e) => setEmail(e.target.value)} />

        <input
          type="password"
          placeholder="Enter password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button onClick={handleLogin} disabled={loginDisabled}>
          {loginDisabled ? `Try again in ${cooldown}s` : 'Login'}
        </button>
      </div>
    );
  }

  // ---------------- CHAT ----------------
  return (
    <div className="chat-app">
      <header className="header">
        <h1>QA Assistant</h1>

        <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
          <span>👤 {user}</span>

          <button
            onClick={() => {
              localStorage.removeItem('token');
              setUser(null);
            }}
          >
            Logout
          </button>
        </div>
      </header>

      <div className="main-layout">
        <div className="chat-section">
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', marginTop: '120px', color: '#6b7280' }}>
              <h2>How can I help you today?</h2>
            </div>
          )}

          <div className="messages">
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                <div className="bubble">
                  <div>{formatContent(msg.content)}</div>

                  {msg.role === 'assistant' && msg.content && (
                    <button className="copy-btn" onClick={() => copy(msg.content)}>
                      Copy
                    </button>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="message assistant">
                <div className="bubble">
                  <span style={{ opacity: 0.6 }}>Thinking...</span>
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          <div className="input-area">
            <textarea value={req} onChange={(e) => setReq(e.target.value)} placeholder="Message QA Assistant..." />

            <div className="controls">
              <select value={format} onChange={(e) => setFormat(e.target.value)}>
                <option value="json">JSON</option>
                <option value="gherkin">Gherkin</option>
                <option value="text">Text</option>
                <option value="excel">Excel</option>
              </select>

              <button onClick={onGenerate}>Send</button>
            </div>
          </div>
        </div>

        <div className="history-panel">
          <h3>📁 History (Coming Soon)</h3>
        </div>
      </div>

      <a
        href="https://www.linkedin.com/in/jhapradip"
        target="_blank"
        rel="noopener noreferrer"
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          background: '#ffffff',
          color: '#0f172a',
          padding: '6px 12px',
          borderRadius: '999px',
          border: '2px solid #3b82f6',
          fontWeight: '700',
          zIndex: 9999,
        }}
      >
        ⚡ PJ
      </a>
    </div>
  );
}
