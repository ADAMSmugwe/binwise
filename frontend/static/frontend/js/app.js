// frontend/js/app.js

console.log("App script loaded")

const API_BASE = window.location.origin + "/api";

/**
 * --- Check API Health ---
 * Verifies the connection to the BinWise backend.
 */
async function checkApiHealth() {
  try {
    const response = await fetch(`${API_BASE}/health/`);
    if (!response.ok) throw new Error("API not healthy");
    const data = await response.json();
    return data;
  } catch (err) {
    console.error("Error checking API health:", err);
    return null;
  }
}

/**
 * --- Classify Image ---
 * Sends the image to the backend and formats the result for the UI cards.
 */
async function classifyImage(file) {
  if (!file) throw new Error("No file provided");

  const formData = new FormData();
  formData.append("image", file);

  try {
    const response = await fetch(`${API_BASE}/classify/` , {
      method: "POST",
      body: formData
    });

    if (!response.ok) throw new Error("Classification failed");

    const data = await response.json();
    
    // Map the API response to the specific fields used in your design cards
    // [cite: 2, 3, 4, 5]
    return {
      bin: data.waste_bin || "Unknown",
      category: data.category || "Uncategorized",
      explanation: data.explanation || "No details provided.",
      confidence: data.confidence ? (data.confidence * 100).toFixed(1) : "0"
    };
  } catch (err) {
    console.error("Error classifying image:", err);
    return null;
  }
}