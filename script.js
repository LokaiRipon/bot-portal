// script.js
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('keyForm');
  const resultBox = document.getElementById('result');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const token = document.getElementById('adminToken').value.trim();
    const name = document.getElementById('licenseName').value.trim();

    if (!token || !name) {
      resultBox.textContent = "Please fill in both fields.";
      return;
    }

    try {
      const res = await fetch('https://your-render-url.com/api/generate_key', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ name })
      });

      const data = await res.json();
      if (res.ok) {
        resultBox.textContent = `✅ Key generated: ${data.key}`;
      } else {
        resultBox.textContent = `❌ Error: ${data.detail || 'Failed to generate key.'}`;
      }
    } catch (err) {
      resultBox.textContent = `❌ Network error: ${err.message}`;
    }
  });
});