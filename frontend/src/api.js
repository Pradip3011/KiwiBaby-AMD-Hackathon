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
//
export async function login(email, password) {
  try {
    const res = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }), // 🔥 FIX
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
// GENERATE (🔥 NORMALIZED RESPONSE)
// -------------------------
export async function generate(requirement, format = 'json') {
  try {
    const res = await fetch(`${API_URL}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: getToken() ? `Bearer ${getToken()}` : '',
      },
      body: JSON.stringify({
        requirement,
        output_format: format,
      }),
    });

    let raw;

    if (format === 'json') {
      raw = await res.json();
    } else {
      raw = await res.text();
    }

    if (!res.ok) {
      throw new Error(typeof raw === 'string' ? raw : raw.detail || 'Backend error');
    }

    // 🔥 Normalize response for UI
    if (format === 'json') {
      return {
        testcases: raw.testcases || [],
        metrics: {
          coverage: raw.coverage_percent,
          qaScore: raw.qa_score,
          ruleScore: raw.rule_score,
        },
        details: {
          qa: raw.qa_details || {},
          rule: raw.rule_details || {},
        },
        missing: raw.missing_scenarios || [],
      };
    }

    return raw;
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
