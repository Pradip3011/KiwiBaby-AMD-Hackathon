// frontend/src/api.js

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// -------------------------
// Helper: get token
// -------------------------
function getToken() {
  return localStorage.getItem('token');
}

// -------------------------
// LOGIN
// -------------------------
export async function login(username) {
  try {
    const res = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username }),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || 'Login failed');
    }

    localStorage.setItem('token', data.token);

    return data;
  } catch (err) {
    console.error('Login Error:', err);
    throw err;
  }
}

// -------------------------
// GENERATE (🔥 FIXED)
// -------------------------
export async function generate(requirement, format = 'json') {
  try {
    const res = await fetch(`${API_URL}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: getToken() || '',
      },
      body: JSON.stringify({
        requirement,
        output_format: format,
      }),
    });

    let data;

    // 🔥 KEY FIX: handle JSON vs non-JSON properly
    if (format === 'json') {
      data = await res.json();
    } else {
      data = await res.text();
    }

    if (!res.ok) {
      throw new Error(typeof data === 'string' ? data : data.detail || 'Backend error');
    }

    return data;
  } catch (err) {
    console.error('Generate Error:', err);
    throw err;
  }
}

// -------------------------
// HISTORY
// -------------------------
export async function getHistory() {
  try {
    const res = await fetch(`${API_URL}/history`, {
      headers: {
        Authorization: getToken() || '',
      },
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || 'Failed to fetch history');
    }

    return data;
  } catch (err) {
    console.error('History Error:', err);
    throw err;
  }
}
