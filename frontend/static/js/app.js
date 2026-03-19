const API_BASE = "";

// Helper to get CSRF cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        document.cookie.split(';').forEach(cookie => {
            const trimmed = cookie.trim();
            if (trimmed.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(trimmed.slice(name.length + 1));
            }
        });
    }
    return cookieValue;
}

async function classifyImage(file) {
    if (!file) throw new Error("No file provided");

    const formData = new FormData();
    formData.append("image", file);

    try {
        const response = await fetch(`${API_BASE}/api/classify/`, {
            method: "POST",
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),  // ← add this
            },
            body: formData,
        });

        if (!response.ok) throw new Error(`Server error: ${response.status}`);

        const data = await response.json();
        console.log("Classification Result:", data);
        return data;
    } catch (err) {
        console.error("Classification error:", err);
        return null;
    }
}