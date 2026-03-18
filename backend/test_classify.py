import os
from PIL import Image
from model import classify_image

TEST_IMAGES = [
    ("../data/test_images/food waste/photo-1562077981-4d7eafd44932.avif", "food scraps"),
    ("../data/test_images/plasticbottle", "plastic bottle"),
    ("../data/test_images/glass bottle waste", "glass bottle"),
    ("../data/test_images/cardboard waste", "cardboard box"),
]

def run_tests():
    passed = 0
    failed = 0

    for path, expected_category in TEST_IMAGES:
        if os.path.isdir(path):
            files = [f for f in os.listdir(path) if not f.startswith(".")]
            if not files:
                print(f"SKIP  {path} — no images found")
                continue
            path = os.path.join(path, files[0])

        if not os.path.exists(path):
            print(f"SKIP  {path} — file not found")
            continue

        try:
            img = Image.open(path)
            result = classify_image(img)
            status = "PASS" if result["bin"] != "gray" else "WARN"
            if status == "WARN":
                failed += 1
            else:
                passed += 1
            print(
                f"{status}  {os.path.basename(path)}\n"
                f"      label={result['label']}  conf={result['confidence']}"
                f"  bin={result['bin']}  category={result['category']}\n"
            )
        except Exception as e:
            failed += 1
            print(f"FAIL  {path} — {e}\n")

    print(f"Results: {passed} passed, {failed} failed/warned")

if __name__ == "__main__":
    run_tests()
