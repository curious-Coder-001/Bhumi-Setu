from pathlib import Path
import io
import re

import fitz
import pytesseract
from PIL import Image

# Tesseract installation path
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_document_text(file_path):
    file_path = Path(file_path)
    extracted_text = []

    if file_path.suffix.lower() == ".pdf":
        with fitz.open(file_path) as pdf:
            for page in pdf:
                text = page.get_text("text").strip()

                # Use OCR if the PDF has no readable text
                if len(text) < 30:
                    pix = page.get_pixmap(
                        matrix=fitz.Matrix(2, 2),
                        alpha=False
                    )
                    image = Image.open(
                        io.BytesIO(pix.tobytes("png"))
                    )
                    text = pytesseract.image_to_string(
                        image,
                        lang="asm"
                    )

                extracted_text.append(text)

    else:
        image = Image.open(file_path)

        # Focus on the upper Jamabandi section
        crop = image.crop((
            0,
            0,
            image.width,
            min(1200, image.height)
        ))

        # Enlarge for better Assamese OCR
        crop = crop.resize(
            (crop.width * 2, crop.height * 2)
        )

        text = pytesseract.image_to_string(
            crop,
            lang="asm"
        )

        extracted_text.append(text)

    return "\n".join(extracted_text).strip()

import joblib

MODEL_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "document_classifier.joblib"
)

def classify_document(extracted_text):
    if not MODEL_PATH.exists():
        return "Model Not Found"

    model = joblib.load(MODEL_PATH)

    if not extracted_text.strip():
        return "No Text Found"

    prediction = model.predict([extracted_text])

    return prediction[0]

def extract_land_fields(extracted_text):
    """
    Extract important land details from OCR text.
    Returns all detected values to support documents
    containing multiple land parcels.
    """

    patterns = {
        "district": r"\bDistrict\s*[:\-]?\s*([^,\n;]+)",
        "circle": r"\bCircle\s*[:\-]?\s*([^,\n;]+)",
        "mouza": r"\bMouza\s*[:\-]?\s*([^,\n;]+)",
        "village": r"\b(?:Revenue\s+Village|Village)\s*[:\-]?\s*([^,\n;]+)",
        "dag_number": r"\bDag\s*(?:No\.?|Number)?\*{0,2}\s*[:\-]\s*\*{0,2}\s*([A-Za-z0-9/-]+)",
        "patta_number": r"\b(?:K\.?P\.?\s*)?Patta\s*(?:No\.?|Number)?\*{0,2}\s*[:\-]\s*\*{0,2}\s*([A-Za-z0-9/-]+)",
        "land_area": r"\b\d+(?:\.\d+)?\s*(?:Bighas?|Kathas?|Lechas?|Bigha|Katha|Lecha)\b"
    }

    extracted_fields = {}

    for field, pattern in patterns.items():
        matches = re.findall(
            pattern,
            extracted_text,
            flags=re.IGNORECASE
        )

        extracted_fields[field] = list(dict.fromkeys(
            match.strip() for match in matches if match.strip()
        ))

    return extracted_fields


    return extracted_fields



import re

def normalize_land_value(value):
    if value is None:
        return ""

    value = str(value).lower().strip()
    value = re.sub(r"[^a-z0-9]", "", value)

    return value


def compare_land_fields(extracted_fields, record):

    field_mapping = {
        "district": "district",
        "circle": "circle",
        "village": "village",
        "dag_number": "dag_number",
        "patta_number": "patta_number"
    }

    results = {}

    for document_field, record_field in field_mapping.items():

        document_values = extracted_fields.get(document_field, [])
        record_value = getattr(record, record_field, None)

        if not document_values or not record_value:
            results[document_field] = "Not Available"
            continue

        normalized_values = [
            normalize_land_value(value)
            for value in document_values
        ]

        normalized_record = normalize_land_value(record_value)

        results[document_field] = (
            "Match"
            if normalized_record in normalized_values
            else "Mismatch"
        )

    return results
