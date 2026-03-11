const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function generate(requirement, format = 'json') {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);

    const res = await fetch(`${API_URL}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        requirement,
        output_format: format,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeout);

    if (!res.ok) {
      let errorText;

      try {
        const error = await res.json();
        errorText = error.detail || 'Backend error';
      } catch {
        errorText = await res.text();
      }

      throw new Error(errorText);
    }

    const data = await res.json();

    if (!data) {
      throw new Error('Invalid server response');
    }

    return data;
  } catch (err) {
    console.error('API Error:', err);
    throw err;
  }
}
