document.addEventListener('DOMContentLoaded', () => {
    const imageInput = document.getElementById('imageInput');
    const classifyBtn = document.getElementById('classifyBtn');
    const imagePreview = document.getElementById('imagePreview');

    classifyBtn.addEventListener('click', async () => {
        const file = imageInput.files[0];
        if (!file) {
            alert("Please select an image first!");
            return;
        }

        // Show preview
        const reader = new FileReader();
        reader.onload = () => {
            imagePreview.src = reader.result;
            imagePreview.style.display = "block";
        };
        reader.readAsDataURL(file);

        // Classify
        const result = await classifyImage(file);

        if (result) {
            // waste_bin matches the serializer field name
            document.getElementById('bin').innerText = result.waste_bin || "N/A";
            document.getElementById('category').innerText = result.category || "N/A";
            document.getElementById('explanation').innerText = result.explanation || "N/A";
            document.getElementById('confidence').innerText =
                result.confidence != null ? result.confidence : "N/A";
        } else {
            alert("Classification failed. Check console for errors.");
        }
    });
});