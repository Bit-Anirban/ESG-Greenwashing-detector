import csv
import random
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
from torch.optim import AdamW

# ---------------- CONFIG ----------------

MODEL_NAME = "distilbert-base-uncased"
BATCH_SIZE = 8
EPOCHS = 3
LR = 2e-5
MAX_LEN = 128

# ---------------- LOAD DATA ----------------

data = []
with open("claims.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append((row["sentence"], int(row["label"])))

random.shuffle(data)

split = int(0.8 * len(data))
train_data = data[:split]
test_data = data[split:]

# ---------------- DATASET ----------------

tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_NAME)

class ClaimDataset(Dataset):
    def __init__(self, data):
        self.sentences = [d[0] for d in data]
        self.labels = [d[1] for d in data]
        self.encodings = tokenizer(
            self.sentences,
            truncation=True,
            padding=True,
            max_length=MAX_LEN
        )

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item

train_dataset = ClaimDataset(train_data)
test_dataset = ClaimDataset(test_data)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE)

# ---------------- MODEL ----------------

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = DistilBertForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=2
)
model.to(device)

optimizer = AdamW(model.parameters(), lr=LR)

# ---------------- TRAIN ----------------

model.train()
for epoch in range(EPOCHS):
    total_loss = 0
    for batch in train_loader:
        optimizer.zero_grad()

        batch = {k: v.to(device) for k, v in batch.items()}
        outputs = model(**batch)

        loss = outputs.loss
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    print(f"Epoch {epoch+1}/{EPOCHS} | Loss: {total_loss:.4f}")

# ---------------- TEST ----------------

model.eval()
correct = 0
total = 0

with torch.no_grad():
    for batch in test_loader:
        labels = batch["labels"].to(device)
        inputs = {k: v.to(device) for k, v in batch.items() if k != "labels"}

        outputs = model(**inputs)
        predictions = torch.argmax(outputs.logits, dim=1)

        correct += (predictions == labels).sum().item()
        total += labels.size(0)

accuracy = correct / total if total > 0 else 0
print(f"\n✅ Test Accuracy: {accuracy:.2f}")

# ---------------- SAVE MODEL ----------------

SAVE_PATH = "./claim_classifier"

model.save_pretrained(SAVE_PATH)
tokenizer.save_pretrained(SAVE_PATH)

print(f"\n✅ Model saved to {SAVE_PATH}")

