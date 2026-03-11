import React, { useState } from 'react';
import { generate } from './api';
import './styles.css';

export default function App() {
  const [req, setReq] = useState('');
  const [out, setOut] = useState(null);
  const [format, setFormat] = useState('json');
  const [loading, setLoading] = useState(false);

  async function onGenerate() {
    if (!req.trim()) {
      alert('Please enter a requirement.');
      return;
    }

    try {
      setLoading(true);
      const r = await generate(req, format);
      setOut(r);
    } catch (err) {
      console.error(err);
      alert('Error generating output.');
    } finally {
      setLoading(false);
    }
  }

  function renderOutput() {
    if (!out) return 'Output will appear here';

    if (format === 'json') {
      return JSON.stringify(out.output, null, 2);
    }

    return out.output?.raw || '';
  }

  function copyOutput() {
    if (!out) return;

    const text = format === 'json' ? JSON.stringify(out.output, null, 2) : out.output?.raw;

    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  }

  return (
    <div className="app-container">
      <h1>AI Test Case Agent</h1>

      <textarea
        rows={6}
        value={req}
        onChange={(e) => setReq(e.target.value)}
        placeholder="Paste business requirement..."
      />

      <div className="toolbar">
        <label>Format:</label>

        <select value={format} onChange={(e) => setFormat(e.target.value)}>
          <option value="json">JSON</option>
          <option value="gherkin">Gherkin</option>
          <option value="text">Text</option>
          <option value="excel">Excel</option>
        </select>

        <button onClick={onGenerate} disabled={loading}>
          {loading ? 'Generating...' : 'Generate'}
        </button>

        <button onClick={copyOutput}>Copy Output</button>
      </div>

      <div className="output-container">
        <pre>{renderOutput()}</pre>
      </div>
    </div>
  );
}
