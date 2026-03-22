import React, { useState, useRef, useEffect } from 'react';
import { generate, login } from './api';
import './styles.css';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [req, setReq] = useState('');
  const [format, setFormat] = useState('json');
  const [loading, setLoading] = useState(false);

  const [user, setUser] = useState(null);
  const [username, setUsername] = useState('');

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ---------------- LOGIN ----------------
  async function handleLogin() {
    if (!username.trim()) {
      alert('Enter username');
      return;
    }

    try {
      const res = await login(username);

      // Save token
      localStorage.setItem('token', res.token);

      setUser(res.user);
    } catch (e) {
      alert('Login failed');
    }
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

        // 🔥 FINAL FIXES: newline + quotes
        content = raw.replace(/\\n/g, '\n').replace(/\\"/g, '"');
      }

      const aiMsg = {
        role: 'assistant',
        content,
      };

      setMessages((prev) => [...prev, aiMsg]);
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

  // ---------------- LOGIN SCREEN ----------------
  if (!user) {
    return (
      <div className="login-container">
        <h1>AI Test Case Agent</h1>

        <input placeholder="Enter username" value={username} onChange={(e) => setUsername(e.target.value)} />

        <button onClick={handleLogin}>Login</button>
      </div>
    );
  }

  // ---------------- MAIN APP ----------------
  return (
    <div className="chat-app">
      <header className="header">
        <h1>AI Test Case Agent</h1>
        <span>👤 {user}</span>
      </header>

      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="bubble">
              {/* 🔥 FINAL DISPLAY FIX */}
              <pre style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</pre>

              {msg.role === 'assistant' && (
                <button className="copy-btn" onClick={() => copy(msg.content)}>
                  Copy
                </button>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="bubble">Generating test cases... please wait ⏳</div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="input-area">
        <textarea value={req} onChange={(e) => setReq(e.target.value)} placeholder="Paste business requirement..." />

        <div className="controls">
          <select value={format} onChange={(e) => setFormat(e.target.value)}>
            <option value="json">JSON</option>
            <option value="gherkin">Gherkin</option>
            <option value="text">Text</option>
            <option value="excel">Excel</option>
          </select>

          <button onClick={onGenerate}>Generate</button>
        </div>
      </div>
    </div>
  );
}
