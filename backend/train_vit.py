import json
import os
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset
from transformers import ViTForImageClassification, AutoImageProcessor, TrainingArguments, Trainer
import evaluate
from torchvision import transforms
from PIL import Image

LOCAL_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "test_images"))
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "vit-finetuned-waste"))
BASE_MODEL = "google/vit-base-patch16-224"
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".bmp", ".tiff", ".tif"}

feature_extractor = AutoImageProcessor.from_pretrained(BASE_MODEL)

train_augmentations = transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(30),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.1),
    transforms.RandomGrayscale(p=0.1),
])


class WasteDataset(Dataset):
    def __init__(self, samples, label2id, is_train=False):
        self.samples = samples
        self.label2id = label2id
        self.is_train = is_train

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        image, label_name = self.samples[idx]
        if isinstance(image, str):
            image = Image.open(image)
        image = image.convert("RGB")
        if self.is_train:
            image = train_augmentations(image)
        inputs = feature_extractor(images=image, return_tensors="pt")
        return {
            "pixel_values": inputs["pixel_values"][0],
            "labels": torch.tensor(self.label2id[label_name], dtype=torch.long),
        }


def load_hf_dataset():
    from datasets import load_dataset
    hf_token = os.environ.get("HF_TOKEN")
    ds = load_dataset("dmedhi/garbage-image-classification-detection", token=hf_token)
    train_samples = [(row["image"], row["class_name"]) for row in ds["train"]]
    val_samples = [(row["image"], row["class_name"]) for row in ds["validation"]]
    label_names = sorted(set(row["class_name"] for row in ds["train"]))
    return train_samples, val_samples, label_names


def load_local_dataset():
    samples = []
    label_names = sorted([
        d for d in os.listdir(LOCAL_DATA_DIR)
        if os.path.isdir(os.path.join(LOCAL_DATA_DIR, d)) and not d.startswith(".")
    ])
    for label in label_names:
        folder = os.path.join(LOCAL_DATA_DIR, label)
        for fname in os.listdir(folder):
            if os.path.splitext(fname)[1].lower() in SUPPORTED_EXTS:
                samples.append((os.path.join(folder, fname), label))
    torch.manual_seed(42)
    split = int(0.8 * len(samples))
    indices = torch.randperm(len(samples)).tolist()
    train_samples = [samples[i] for i in indices[:split]]
    val_samples = [samples[i] for i in indices[split:]]
    return train_samples, val_samples, label_names


hf_token = os.environ.get("HF_TOKEN")
if hf_token:
    print("HF_TOKEN found. Loading dmedhi/garbage-image-classification-detection...")
    try:
        train_samples, val_samples, label_names = load_hf_dataset()
        print(f"HF dataset loaded. {len(train_samples)} train, {len(val_samples)} val, classes: {label_names}")
    except Exception as e:
        print(f"HF dataset failed ({e}). Falling back to local data.")
        train_samples, val_samples, label_names = load_local_dataset()
        print(f"Local data loaded. {len(train_samples)} train, {len(val_samples)} val")
else:
    print("No HF_TOKEN. Using local data.")
    train_samples, val_samples, label_names = load_local_dataset()
    print(f"Local data loaded. {len(train_samples)} train, {len(val_samples)} val")

label2id = {name: i for i, name in enumerate(label_names)}
id2label = {i: name for i, name in enumerate(label_names)}

train_dataset = WasteDataset(train_samples, label2id, is_train=True)
val_dataset = WasteDataset(val_samples, label2id, is_train=False)

accuracy_metric = evaluate.load("accuracy")


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return accuracy_metric.compute(predictions=predictions, references=labels)


model = ViTForImageClassification.from_pretrained(
    BASE_MODEL,
    num_labels=len(label_names),
    id2label=id2label,
    label2id=label2id,
    ignore_mismatched_sizes=True,
)

epochs = 5 if len(train_samples) > 100 else 20
batch_size = 16 if len(train_samples) > 100 else 8

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=batch_size,
    per_device_eval_batch_size=batch_size,
    num_train_epochs=epochs,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    logging_steps=10,
    remove_unused_columns=False,
    push_to_hub=False,
)


def collate_fn(batch):
    return {
        "pixel_values": torch.stack([b["pixel_values"] for b in batch]),
        "labels": torch.stack([b["labels"] for b in batch]),
    }


trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
    data_collator=collate_fn,
)

trainer.train()

preds = trainer.predict(val_dataset)
logits = torch.tensor(preds.predictions, dtype=torch.float32)
labels_tensor = torch.tensor(preds.label_ids, dtype=torch.long)


class TemperatureScaler(nn.Module):
    def __init__(self):
        super().__init__()
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, logits):
        return logits / self.temperature


scaler = TemperatureScaler()
optimizer = torch.optim.LBFGS([scaler.temperature], lr=0.1, max_iter=100)
criterion = nn.CrossEntropyLoss()


def step():
    optimizer.zero_grad()
    loss = criterion(scaler(logits), labels_tensor)
    loss.backward()
    return loss


optimizer.step(step)
temperature = max(scaler.temperature.item(), 0.1)
print(f"Calibrated temperature: {temperature:.4f}")

os.makedirs(OUTPUT_DIR, exist_ok=True)
model.save_pretrained(OUTPUT_DIR)
feature_extractor.save_pretrained(OUTPUT_DIR)

with open(os.path.join(OUTPUT_DIR, "temperature.json"), "w") as f:
    json.dump({"temperature": temperature, "label_names": label_names}, f)

print(f"Done. Model saved to {OUTPUT_DIR}")
