import React from 'react';
import { useState } from 'react';
import { generate } from './api';
import "./styles.css";

export default function App() {
  const [req, setReq] = useState('');
  const [out, setOut] = useState(null);
  const [format, setFormat] = useState('json');

  async function onGenerate() {
    if (!req.trim()) {
      alert("Please enter a requirement.");
      return;
    }

    const r = await generate(req, format);
    setOut(r);
  }

  return (
    <div style={{ padding: 20, maxWidth: 900, margin: '0 auto' }}>
      <h1>AI Test Case Agent</h1>

      <textarea
        rows={8}
        style={{ width: '100%' }}
        value={req}
        onChange={(e) => setReq(e.target.value)}
        placeholder="Paste business requirement..."
      />

      <div style={{ marginTop: 8 }}>
        <label>Format: </label>
        <select value={format} onChange={(e) => setFormat(e.target.value)}>
          <option value="json">JSON</option>
          <option value="gherkin">Gherkin</option>
          <option value="csv">CSV</option>
          <option value="excel">Excel (XLSX)</option>
        </select>

        <button style={{ marginLeft: 8 }} onClick={onGenerate}>
          Generate
        </button>
      </div>

      <pre
        style={{
          marginTop: 12,
          background: '#f4f4f4',
          padding: 10,
          maxHeight: 420,
          overflow: 'auto',
        }}
      >
        {out ? JSON.stringify(out, null, 2) : 'Output will appear here'}
      </pre>
    </div>
  );
}
