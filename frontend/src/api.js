export async function generate(requirement, format = "json") {
  try {
    const res = await fetch("http://localhost:8000/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        requirement,
        output_format: format,
      }),
    });

    if (!res.ok) {
      let errorText;
      try {
        const error = await res.json();
        errorText = error.detail || "Backend error";
      } catch {
        errorText = await res.text(); // fallback to raw text
      }
      throw new Error(errorText);
    }

    return await res.json();
  } catch (err) {
    console.error("API Error:", err);
    throw err;
  }
}