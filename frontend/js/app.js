// frontend/js/app.js

const API_BASE = "http://127.0.0.1:8000";

// --- Check API Health ---
async function checkApiHealth() {
  try {
    const response = await fetch(`${API_BASE}/health/`);
    if (!response.ok) throw new Error("API not healthy");
    const data = await response.json();
    console.log("API Health:", data.status || "OK");
    return data;
  } catch (err) {
    console.error("Error checking API health:", err);
    return null;
  }
}

// --- Classify Image ---
async function classifyImage(file) {
  if (!file) throw new Error("No file provided");

  const formData = new FormData();
  formData.append("image", file);

  try {
    const response = await fetch(`${API_BASE}/classify/`, {
      method: "POST",
      body: formData
    });

    if (!response.ok) throw new Error("Classification failed");

    const data = await response.json();
    console.log("Classification Result:", data.result);
    return data;
  } catch (err) {
    console.error("Error classifying image:", err);
    return null;
  }
}

// --- Example Usage ---
// Only for testing with Node.js or later when you have file input
// checkApiHealth();

// simulate an image file in Node.js (if testing outside browser)
// const fs = require('fs');
// const testFile = fs.readFileSync('./test-image.jpg');
// classifyImage(testFile);