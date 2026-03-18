from PIL import Image
from model import classify_image

img = Image.open("../data/test_images/food waste/photo-1562077981-4d7eafd44932.avif")
result = classify_image(img)
print(f"Label:      {result['label']}")
print(f"Confidence: {result['confidence']}")
print(f"Bin:        {result['bin']}")
print(f"Category:   {result['category']}")
print(f"Explanation:{result['explanation']}")
