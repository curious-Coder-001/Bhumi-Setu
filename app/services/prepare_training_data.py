from pathlib import Path
import pandas as pd

from app.services.document_intelligence import extract_document_text

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRAINING_DIR = PROJECT_ROOT / "data" / "training_documents"
OUTPUT_FILE = PROJECT_ROOT / "data" / "training_dataset.csv"

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

rows = []

for category_folder in TRAINING_DIR.iterdir():

    if not category_folder.is_dir():
        continue

    category = category_folder.name

    for document_path in category_folder.iterdir():

        if document_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        try:
            text = extract_document_text(document_path)

            if text:
                rows.append({
                    "document": document_path.name,
                    "category": category,
                    "text": text
                })

                print(f"Processed: {document_path.name}")

        except Exception as error:
            print(f"Failed: {document_path.name} - {error}")

dataset = pd.DataFrame(
    rows,
    columns=["document", "category", "text"]
)

dataset.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print("\nDataset preparation completed.")
print(f"Documents processed: {len(dataset)}")
print(f"Dataset saved at: {OUTPUT_FILE}")
