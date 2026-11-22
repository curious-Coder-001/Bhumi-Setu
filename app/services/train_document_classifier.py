
from pathlib import Path

import pandas as pd
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_FILE = PROJECT_ROOT / "data" / "training_dataset.csv"
MODEL_FILE = PROJECT_ROOT / "data" / "document_classifier.joblib"

dataset = pd.read_csv(DATASET_FILE)

dataset = dataset.dropna(subset=["text", "category"])
dataset = dataset[dataset["text"].str.strip() != ""]

if len(dataset) < 2:
    raise ValueError("At least 2 usable documents are required.")

if dataset["category"].nunique() < 2:
    raise ValueError(
        "At least 2 different document categories are required."
    )

model = Pipeline([
    ("tfidf", TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        max_features=5000
    )),
    ("classifier", LinearSVC())
])

model.fit(dataset["text"], dataset["category"])

joblib.dump(model, MODEL_FILE)

print("Initial document classifier trained successfully.")
print(f"Training documents: {len(dataset)}")
print(f"Document categories: {list(dataset['category'].unique())}")
print(f"Model saved at: {MODEL_FILE}")
