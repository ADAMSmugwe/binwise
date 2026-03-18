# E-cycling AI Service

A small backend service that looks at a photo of a waste item and tells you which bin it belongs in. Point it at an image, and it'll come back with a bin colour, a category, and a short explanation of why.

---

## What's inside

| File | What it does |
|------|--------------|
| `app.py` | Runs the Flask server and exposes the `/classify` endpoint |
| `model.py` | Loads the ViT model and handles the classification logic |
| `waste_rules.py` | A lookup table mapping waste items to bins and guidance |
| `train_vit.py` | Fine-tunes the ViT model on the local waste image dataset |
| `test_model.py` | Quickly tests model inference on a single image |
| `test_classify.py` | Runs the full classification pipeline against a few local images |

---

## Getting started

You'll need Python 3.11. If you haven't set up a virtual environment yet:

```bash
python3.11 -m venv venv311
source venv311/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Then start the server:

```bash
python app.py
```

It'll be running at `http://0.0.0.0:5001`.

---

## Using the API

Send a `POST` request to `/classify` with the image as form data:

```bash
curl -X POST -F "image=@photo.jpg" http://127.0.0.1:5001/classify
```

You'll get back something like:

```json
{
  "bin": "blue",
  "category": "recyclable",
  "explanation": "Clean plastic bottles can be melted into new products.",
  "label": "water bottle",
  "confidence": 0.92
}
```

If the model isn't confident enough or doesn't recognise the item, it'll return a `gray` bin so you know to double-check locally:

```json
{
  "bin": "gray",
  "category": "unclear",
  "explanation": "I'm not sure. Please check local guidelines.",
  "label": "...",
  "confidence": 0.18
}
```

The possible bin colours are `blue` (recyclable), `green` (organic), `black` (general waste), `specialist` (hazardous), and `gray` (unclear).

---

## Testing

Run a quick inference test on one image:

```bash
python test_model.py
```

Or test the full pipeline across several categories:

```bash
python test_classify.py
```

---

## Fine-tuning the model

If you want to train on the local dataset, run this from the repo root:

```bash
python backend/train_vit.py
```

Weights get saved to `backend/vit-finetuned-waste/`. To switch to the fine-tuned model, update `MODEL_NAME` in `model.py` to point at that folder.

---

## Tweaking things

- **Confidence threshold** — change `CONFIDENCE_THRESHOLD` in `model.py` (default is `0.3`)
- **Synonyms** — add entries to the `SYNONYMS` dict in `model.py` to map new model labels to existing rules
- **Waste rules** — extend `RULES` in `waste_rules.py` to cover new item types
- **Port** — change the `port=` value in `app.run()` inside `app.py`
