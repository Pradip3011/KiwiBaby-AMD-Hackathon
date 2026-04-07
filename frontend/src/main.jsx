import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles.css';

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Root element not found');
}

// 🔥 Check auth token (future-proofing)
const token = localStorage.getItem('token');

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App key={token ? 'auth' : 'guest'} />
  </React.StrictMode>,
);
