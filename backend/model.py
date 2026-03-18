import threading
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image

try:
    from waste_rules import RULES
except ImportError:
    from backend.waste_rules import RULES

CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"

_processor = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)
_model = CLIPModel.from_pretrained(CLIP_MODEL_NAME)
_model.eval()

_model_lock = threading.Lock()

CONFIDENCE_THRESHOLD = 0.12
MIXED_WASTE_THRESHOLD = 0.40
TOP_K = 3

MIXED_WASTE_LABEL = "__mixed__"
CANDIDATE_LABELS = list(RULES.keys())

PROMPTS = {
    MIXED_WASTE_LABEL: [
        "a photo of a bin containing plastic bottles AND glass AND paper all mixed together",
        "a recycling bin with many different recyclable materials mixed together",
        "multiple distinct waste objects of clearly different materials in one photo",
        "a pile of assorted rubbish containing bottles, cans, and boxes all at once",
    ],
    "plastic bottle": [
        "a photo of a plastic bottle",
        "a plastic water bottle or plastic drinks bottle",
        "an empty plastic container or plastic packaging",
        "a crushed or whole plastic bottle for recycling",
    ],
    "glass bottle": [
        "a photo of a glass bottle",
        "a wine bottle, beer bottle, or glass jar",
        "a transparent glass container you can see through",
        "a hard breakable glass bottle",
    ],
    "cardboard box": [
        "a photo of a cardboard box",
        "brown corrugated cardboard packaging material",
        "a flattened or collapsed brown cardboard box",
        "a large brown shipping box or amazon delivery box",
        "stacked flattened cardboard boxes outside for recycling collection",
        "cardboard boxes broken down and piled up in a pile",
    ],
    "newspaper": [
        "a photo of a newspaper",
        "printed paper, magazine, or junk mail",
        "sheets of paper or office paper",
        "a book, envelope, or paper documents",
    ],
    "tin can": [
        "a photo of a tin can",
        "a metal food can for soup, beans, or tomatoes",
        "a large steel or tin container for food",
        "an empty tin food can",
    ],
    "aluminium can": [
        "a photo of an aluminium drinks can",
        "a soda can, beer can, or energy drink can",
        "a slim metal beverage can",
        "a crushed or whole aluminium can",
    ],
    "food scraps": [
        "a photo of food scraps or organic kitchen waste",
        "banana peels, apple cores, or vegetable peelings on their own",
        "leftover cooked food, raw food waste, or rotting food",
        "eggshells, coffee grounds, tea bags, or biodegradable food waste",
        "a single pile of food or organic waste for composting",
    ],
    "greasy pizza box": [
        "a photo of a greasy pizza box",
        "a cardboard box stained with food grease or oil",
        "a used pizza box with food residue",
        "food-contaminated cardboard that cannot be recycled",
    ],
    "plastic bag": [
        "a photo of a plastic bag",
        "a supermarket carrier bag or shopping bag",
        "plastic film, cling film, or bubble wrap",
        "a thin plastic bag or bin liner",
    ],
    "textiles": [
        "a photo of old clothing or fabric",
        "worn out shoes, shirts, or fabric items",
        "textile waste like clothes or fabric scraps",
        "a pile of old garments or fabric materials",
    ],
    "styrofoam": [
        "a photo of white styrofoam packaging",
        "polystyrene foam used for packaging electronics",
        "expanded foam packaging material",
        "a white foam tray or styrofoam cup",
    ],
    "wood": [
        "a photo of a wooden plank or timber",
        "scrap wood or broken wooden furniture",
        "wood offcuts or wooden boards",
        "treated or painted wood waste",
    ],
    "rubber": [
        "a photo of a rubber tyre or tire",
        "rubber hose, rubber mat, or rubber items",
        "a worn out car tyre or bicycle tyre",
        "rubber waste material",
    ],
    "ceramic": [
        "a photo of a broken ceramic plate or mug",
        "a ceramic bowl, dish, or cup",
        "cracked or chipped pottery or crockery",
        "ceramic tableware waste",
    ],
    "mirror": [
        "a photo of a mirror or window glass",
        "flat glass from a window or mirror",
        "a broken mirror or glass pane",
        "reflective flat glass that is not a bottle",
    ],
    "general waste": [
        "a photo of non-recyclable household rubbish in a bin",
        "a nappy, cotton wool, or sanitary waste",
        "broken non-recyclable items or food-contaminated packaging",
        "general black bin waste that cannot be recycled or composted",
    ],
    "battery": [
        "a photo of a battery or batteries",
        "AA, AAA, or rechargeable batteries",
        "a used battery ready for disposal",
        "a car battery or household battery",
    ],
    "light bulb": [
        "a photo of a light bulb",
        "a fluorescent tube or energy saving bulb",
        "a CFL or LED light bulb",
        "a broken or used light bulb",
    ],
    "e-waste": [
        "a photo of electronic waste",
        "an old phone, laptop, or computer",
        "broken electronics or electrical cables",
        "a discarded tablet, printer, or electronic device",
    ],
    "paint": [
        "a photo of a paint can",
        "liquid paint or a tin of house paint",
        "a partially used or empty paint container",
        "paint waste or paint brushes with paint",
    ],
    "aerosol": [
        "a photo of an aerosol spray can",
        "a deodorant can, hairspray, or spray paint can",
        "a pressurised aerosol container",
        "an empty or full spray can",
    ],
    "medicine": [
        "a photo of medicine or pills",
        "a blister pack of tablets or capsules",
        "a medicine bottle, syringe, or prescription drugs",
        "unused or expired medication",
    ],
}

_text_features_cache = None
_text_labels_cache = None


def _get_text_features():
    global _text_features_cache, _text_labels_cache
    if _text_features_cache is None:
        _text_labels_cache = [MIXED_WASTE_LABEL] + CANDIDATE_LABELS
        averaged_features = []
        for label in _text_labels_cache:
            prompts = PROMPTS[label]
            inputs = _processor(text=prompts, return_tensors="pt", padding=True)
            with torch.no_grad():
                features = _model.get_text_features(**inputs)
                features = features / features.norm(dim=-1, keepdim=True)
                averaged = features.mean(dim=0)
                averaged = averaged / averaged.norm()
            averaged_features.append(averaged)
        _text_features_cache = torch.stack(averaged_features)
    return _text_features_cache, _text_labels_cache


def classify_image(image: Image.Image) -> dict:
    image = image.convert("RGB")
    image_inputs = _processor(images=image, return_tensors="pt")

    text_features, labels = _get_text_features()

    with _model_lock:
        with torch.no_grad():
            image_features = _model.get_image_features(**image_inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            similarities = (image_features @ text_features.T)[0]
            probs = torch.softmax(similarities * 100, dim=-1)

    top_indices = torch.topk(probs, k=min(TOP_K, probs.size(0))).indices.tolist()
    top_label = labels[top_indices[0]]
    top_confidence = probs[top_indices[0]].item()

    if top_label == MIXED_WASTE_LABEL and top_confidence >= MIXED_WASTE_THRESHOLD:
        return {
            "bin": "multiple",
            "category": "multiple_items",
            "explanation": "It looks like there are multiple waste items in this photo. Please photograph one item at a time for an accurate result.",
            "label": "mixed waste",
            "confidence": round(top_confidence, 2),
        }

    # Mixed waste won but with low confidence — use second-best label
    if top_label == MIXED_WASTE_LABEL:
        if len(top_indices) > 1:
            second_idx = top_indices[1]
            top_label = labels[second_idx]
            top_confidence = probs[second_idx].item()
            top_indices = top_indices[1:]

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
        if lbl == MIXED_WASTE_LABEL:
            continue
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
