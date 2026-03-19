# BinWise AI Service

<p align="center">
  <img src="docs/images/binwise-overview.png" alt="BinWise overview" width="700"/>
</p>

A fullstack application service that looks at a photo of a waste item and tells you which bin it belongs in. Point it at an image, and it'll come back with a bin color, a category, and a short explanation of why.

Built with Django, CLIP (zero-shot image classification), and Django REST Framework. No training required — it works straight out of the box.

---

## How it works

BinWise uses **OpenAI's CLIP model** (`clip-vit-base-patch32`) to classify waste images. Instead of training a custom model, we use **prompt ensembling** — each waste category has 4–6 carefully written text descriptions that get averaged into a single strong embedding. The image is then compared against all category embeddings using cosine similarity, and the closest match wins.

It can also detect when multiple waste items are in one photo and ask the user to photograph one item at a time.

---

## What's inside

| File | What it does |
|------|--------------|
| `backend/model.py` | Loads CLIP and handles classification logic with prompt ensembling |
| `backend/waste_rules.py` | Lookup table mapping waste items to bins and guidance |
| `api/views.py` | Django REST Framework views — wires CLIP into the API |
| `api/urls.py` | API route definitions |
| `api/models.py` | WasteItem database model for logging classifications |
| `binwise_project/urls.py` | Main URL config |

---

## Getting started

You'll need Python 3.11 and above. If you don't
If you're setting up from scratch:

*Linux*
```bash
python3.11 -m venv venv311
source venv311/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

*Windows*
```bash
python -3.11 -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Run the database migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

Then start the server:

*Linux*
if venv is already activated, skip the first command.
```bash
source venv311/bin/activate
python manage.py runserver
```
*Windows*
if venv is already activated, skip the first command.
```bash
.\venv\Scripts\activate
python manage.py runserver
```

It'll be running at `http://127.0.0.1:8000`.

> The first request takes a few seconds while CLIP loads into memory. After that it's fast.

---

## API endpoints

### `POST /api/classify/`

Send an image as `multipart/form-data` with the key `image`.

```bash
curl -X POST -F "image=@photo.jpg" http://127.0.0.1:8000/api/classify/
```

## With Postman
Open Postman app or extension and paste this on the URL

`http://127.0.0.1:8000/api/classify/`

**Successful classification (classification):**

```json
{
{
  "id": 5,
  "image": "/media/image.jpeg",
  "item_name": "textiles",
  "waste_bin": "black",
  "category": "general waste",
  "confidence": 0.52,
  "explanation": "Used textiles should be donated or taken to a charity shop if still wearable.",
  "suggestions": null,
  "created_at": "2026-03-19T07:29:03.466725Z"
}
```

**Multiple items detected:**

```json
{
  "id": 6,
  "image": "/media/image2.jpeg",
  "item_name": "mixed waste",
  "waste_bin": "multiple",
  "category": "multiple_items",
  "explanation": "It looks like there are multiple waste items in this photo. Please photograph one item at a time for an accurate result.",
  "confidence": 0.74
}
```

**Low confidence — returns suggestions:**

```json
{
  "id": 7,
  "category": "unclear",
  "explanation": "Not confident enough. Here are the most likely matches.",
  "item_name": "cardboard box",
  "waste_bin": "gray",
  "confidence": 0.18,
  "suggestions": [
    { "label": "cardboard box", "bin": "blue", "category": "recyclable", "confidence": 0.18 },
    { "label": "general waste", "bin": "black", "category": "general waste", "confidence": 0.14 }
  ]
}
```

### `GET /api/health/`

Returns `{ "status": "ok" }` if the server is running.

---

## Bin colours

| Colour | Meaning |
|--------|---------|
| `blue` | Recyclable |
| `green` | Organic / compostable |
| `black` | General waste |
| `specialist` | Hazardous — needs special disposal |
| `gray` | Unclear — check local guidelines |
| `multiple` | Multiple items detected — photograph one at a time |

---

## Tweaking things

- **Confidence threshold** — change `CONFIDENCE_THRESHOLD` in `backend/model.py` (default `0.12`)
- **Mixed waste threshold** — change `MIXED_WASTE_THRESHOLD` (default `0.40`) — how confident CLIP needs to be before reporting multiple items
- **Text prompts** — update the `PROMPTS` dict in `backend/model.py` to improve accuracy for specific categories
- **Waste rules** — extend `RULES` in `backend/waste_rules.py` to add new item types
