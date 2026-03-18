from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, UnidentifiedImageError
import io
from model import classify_image

app = Flask(__name__)
CORS(app)

@app.route('/classify', methods=['POST'])
def classify():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    try:
        img = Image.open(io.BytesIO(file.read()))
    except UnidentifiedImageError:
        return jsonify({'error': 'Cannot read image — unsupported or corrupted file'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to open image: {str(e)}'}), 400

    try:
        result = classify_image(img)
    except Exception as e:
        return jsonify({'error': f'Classification failed: {str(e)}'}), 500

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
