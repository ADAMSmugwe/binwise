import threading
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image

from waste_rules import RULES

CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"

_processor = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)
_model = CLIPModel.from_pretrained(CLIP_MODEL_NAME)
_model.eval()

_model_lock = threading.Lock()

CONFIDENCE_THRESHOLD = 0.12
TOP_K = 3

MIXED_WASTE_LABEL = "__mixed__"
CANDIDATE_LABELS = list(RULES.keys())

PROMPTS = {
    MIXED_WASTE_LABEL: "a photo of a pile of mixed waste with multiple different types of garbage and rubbish combined",
    "plastic bottle": "a photo of a plastic bottle or plastic container",
    "glass bottle": "a photo of a glass bottle, glass jar, or glass container — transparent, hard, and breakable glass material",
    "cardboard box": "a photo of brown corrugated cardboard, a cardboard box, or cardboard packaging material",
    "newspaper": "a photo of paper, newspaper, magazine, or printed sheets",
    "tin can": "a photo of a large metal tin can used for food such as soup, beans, or tomatoes",
    "aluminium can": "a photo of a slim aluminium drinks can for soda, beer, or energy drinks",
    "food scraps": "a photo of raw food waste such as banana peels, apple cores, vegetable scraps, eggshells, coffee grounds, or leftover cooked food",
    "greasy pizza box": "a photo of a greasy pizza box or food-stained cardboard",
    "plastic bag": "a photo of a plastic bag, carrier bag, or plastic film",
    "textiles": "a photo of clothing, fabric, shoes, or textiles",
    "styrofoam": "a photo of white styrofoam or polystyrene foam packaging",
    "wood": "a photo of wood, timber, or a wooden plank",
    "rubber": "a photo of rubber, a tyre, or rubber hose",
    "ceramic": "a photo of a ceramic plate, mug, or bowl",
    "mirror": "a photo of a mirror or flat window glass",
    "general waste": "a photo of non-recyclable household rubbish such as nappies, broken items, or mixed packaging that cannot be recycled",
    "battery": "a photo of a battery or batteries",
    "light bulb": "a photo of a light bulb or fluorescent tube",
    "e-waste": "a photo of electronic waste, a phone, laptop, or cable",
    "paint": "a photo of a paint can or liquid paint",
    "aerosol": "a photo of an aerosol can or spray can",
    "medicine": "a photo of medicine, pills, or a syringe",
}

_text_inputs = None
_text_labels = None


def _get_text_inputs():
    global _text_inputs, _text_labels
    if _text_inputs is None:
        _text_labels = [MIXED_WASTE_LABEL] + CANDIDATE_LABELS
        texts = [PROMPTS[label] for label in _text_labels]
        _text_inputs = _processor(text=texts, return_tensors="pt", padding=True)
    return _text_inputs, _text_labels


def classify_image(image: Image.Image) -> dict:
    image = image.convert("RGB")
    image_inputs = _processor(images=image, return_tensors="pt")
    text_inputs, labels = _get_text_inputs()

    with _model_lock:
        with torch.no_grad():
            image_features = _model.get_image_features(**image_inputs)
            text_features = _model.get_text_features(**text_inputs)

            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)

            similarities = (image_features @ text_features.T)[0]
            probs = torch.softmax(similarities * 100, dim=-1)

    top_indices = torch.topk(probs, k=min(TOP_K, probs.size(0))).indices.tolist()
    top_label = labels[top_indices[0]]
    top_confidence = probs[top_indices[0]].item()

    if top_label == MIXED_WASTE_LABEL:
        return {
            "bin": "multiple",
            "category": "multiple_items",
            "explanation": "It looks like there are multiple waste items in this photo. Please photograph one item at a time for an accurate result.",
            "label": "mixed waste",
            "confidence": round(top_confidence, 2),
        }

    if top_confidence > CONFIDENCE_THRESHOLD:
        rule = RULES[top_label]
        return {
            "bin": rule["bin"],
            "category": rule["category"],
            "explanation": rule["explanation"],
            "label": top_label,
            "confidence": round(top_confidence, 2),
        }

    suggestions = []
    for idx in top_indices:
        lbl = labels[idx]
        conf = probs[idx].item()
        rule = RULES[lbl]
        suggestions.append({
            "label": lbl,
            "bin": rule["bin"],
            "category": rule["category"],
            "confidence": round(conf, 2),
        })

    return {
        "bin": "gray",
        "category": "unclear",
        "explanation": "Not confident enough. Here are the most likely matches.",
        "label": top_label,
        "confidence": round(top_confidence, 2),
        "suggestions": suggestions,
    }
