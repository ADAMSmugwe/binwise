// frontend/static/js/frontend-ui.js

document.addEventListener("DOMContentLoaded", () => {
    // 1. Element Selectors
    const imageInput = document.getElementById('imageInput');
    const uploadTrigger = document.getElementById('uploadButton'); 
    const imagePreview = document.getElementById('imagePreview');
    const classifyBtn = document.getElementById('classifyBtn');
    
    // Result Fields
    const binField = document.getElementById('bin');
    const categoryField = document.getElementById('category');
    const explanationField = document.getElementById('explanation');

    // View Containers
    const homeView = document.getElementById('input-view');
    const previewView = document.getElementById('preview-view');
    const resultView = document.querySelector('.results-view');

    /**
     * STEP 1: UPLOAD TRIGGER (Footer Icon)
     */
    if (uploadTrigger) {
        uploadTrigger.addEventListener('click', () => {
            imageInput.click();
        });
    }

    /**
     * STEP 2: PREVIEW ONLY (Runs on file selection)
     * No API call happens here. Just UI swap.
     */
    imageInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                // Update the frame source
                imagePreview.src = e.target.result;
                
                // Transition: Home -> Preview
                homeView.classList.add('hidden');
                previewView.classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        }
    });

    const cameraButton = document.getElementById('cameraButton');

if (cameraButton) {
    cameraButton.addEventListener('click', () => {
        imageInput.setAttribute('capture', 'environment'); 
        imageInput.click();
    });
}

const uploadButton = document.getElementById('uploadButton');
if (uploadButton) {
    uploadButton.addEventListener('click', () => {
        imageInput.removeAttribute('capture');
        imageInput.click();
    });
}

    /**
     * STEP 3: CLASSIFY API CALL (Runs ONLY on CTA Click)
     */
    classifyBtn.addEventListener('click', async () => {
        const file = imageInput.files[0];
        
        if (!file) {
            alert("No image found. Please go back and upload.");
            return;
        }

        try {
            // UI Feedback: Show Binnie is working
            classifyBtn.innerText = "Analyzing...";
            classifyBtn.disabled = true;

            // Call the engine from app.js
            const result = await classifyImage(file);

            if (result) {
                // Populate result card (Mapping keys from your app.js return)
                binField.innerText = result.bin;
                categoryField.innerText = result.category;
                explanationField.innerText = result.explanation;

                // Transition: Preview -> Results
                previewView.classList.add('hidden');
                resultView.classList.remove('hidden');
            } else {
                alert("Binnie couldn't identify this. Try another photo!");
            }
        } catch (err) {
            console.error("Classification Error:", err);
            alert("Connection error. Is the server running?");
        } finally {
            // Reset button state
            classifyBtn.innerText = "Classify Item";
            classifyBtn.disabled = false;
        }
    });

    /**
     * STEP 4: CONGRATS MODAL
     */
    const finishBtn = document.getElementById("finishBtn");
    const dialog = document.querySelector("#congrats-dialog"); // Adjusted to your modal ID
    const closeBtn = document.querySelector("#closeModal");

    if (finishBtn) {
        finishBtn.addEventListener("click", () => {
            dialog.showModal();
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener("click", () => {
            location.reload(); // Returns user to Home fresh
        });
    }
});