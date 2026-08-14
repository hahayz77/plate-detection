import io
import re
import time
from typing import List, Dict, Any

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from paddleocr import PaddleOCR
from PIL import Image

app = FastAPI(
    title="License Plate OCR API",
    description="High accuracy plate detection and OCR using PaddleOCR",
    version="1.0.0"
)

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize PaddleOCR engine
print("[STARTUP] Initializing PaddleOCR engine...")
ocr = PaddleOCR(
    use_angle_cls=True,
    lang="en"
)
print("[STARTUP] PaddleOCR ready!")

MERCOSUL_PATTERN = re.compile(r"^[A-Z]{3}[0-9][A-Z][0-9]{2}$")
CLASSIC_PATTERN = re.compile(r"^[A-Z]{3}[0-9]{4}$")

DIGIT_TO_LETTER_MAP = {
    "0": "O", "1": "I", "2": "Z", "4": "A", "5": "S", "6": "G", "8": "B"
}
LETTER_TO_DIGIT_MAP = {
    "O": "0", "Q": "0", "D": "0", "I": "1", "L": "1", "Z": "2", "A": "4", "S": "5", "G": "6", "B": "8"
}

def clean_plate_text(text: str) -> str:
    """Remove special characters and whitespace, convert to uppercase."""
    return re.sub(r"[^A-Za-z0-9]", "", text).upper()

def correct_mercosul_candidate(candidate: str) -> str:
    """Apply position-based character corrections for Brazilian Mercosul / Classic plates."""
    if len(candidate) != 7:
        return candidate

    chars = list(candidate)

    # First 3 characters must be letters (LLL)
    for i in range(3):
        if chars[i].isdigit() and chars[i] in DIGIT_TO_LETTER_MAP:
            chars[i] = DIGIT_TO_LETTER_MAP[chars[i]]

    # 4th character must be a digit (N)
    if chars[3].isalpha() and chars[3] in LETTER_TO_DIGIT_MAP:
        chars[3] = LETTER_TO_DIGIT_MAP[chars[3]]

    # 5th character can be a letter (Mercosul) or a digit (Classic)
    # Check if 6th and 7th are digits
    for i in (5, 6):
        if chars[i].isalpha() and chars[i] in LETTER_TO_DIGIT_MAP:
            chars[i] = LETTER_TO_DIGIT_MAP[chars[i]]

    return "".join(chars)

def evaluate_plate_text(raw_text: str):
    """Check whether text matches Brazilian license plate standards."""
    clean = clean_plate_text(raw_text)
    corrected = correct_mercosul_candidate(clean)

    is_mercosul = bool(MERCOSUL_PATTERN.match(corrected))
    is_classic = bool(CLASSIC_PATTERN.match(corrected))

    return {
        "clean_text": clean,
        "corrected_text": corrected,
        "is_mercosul": is_mercosul,
        "is_classic": is_classic,
        "is_valid_plate": is_mercosul or is_classic
    }

@app.get("/")
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "License Plate OCR (PaddleOCR)",
        "version": "1.0.0"
    }

@app.post("/detect")
async def detect_plate(file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")

    start_time = time.time()

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        image_np = np.array(image)
        # Convert RGB to BGR for OpenCV / PaddleOCR compatibility
        image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read image: {str(e)}")

    img_height, img_width = image_bgr.shape[:2]

    # Run PaddleOCR detection & recognition
    try:
        ocr_results = ocr.ocr(image_bgr, cls=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR execution failed: {str(e)}")

    plates: List[Dict[str, Any]] = []
    all_detections: List[Dict[str, Any]] = []

    if ocr_results and len(ocr_results) > 0 and ocr_results[0] is not None:
        for line in ocr_results[0]:
            polygon_points, (recognized_text, confidence) = line

            # Calculate bounding box from polygon
            poly_np = np.array(polygon_points, dtype=np.int32)
            x, y, w, h = cv2.boundingRect(poly_np)

            # Ensure inside bounds
            x = max(0, x)
            y = max(0, y)
            w = min(img_width - x, w)
            h = min(img_height - y, h)

            evaluation = evaluate_plate_text(recognized_text)

            detection_item = {
                "raw_text": recognized_text,
                "text": evaluation["corrected_text"] if evaluation["is_valid_plate"] else evaluation["clean_text"],
                "confidence": round(float(confidence), 4),
                "is_mercosul": evaluation["is_mercosul"],
                "is_classic": evaluation["is_classic"],
                "is_valid_plate": evaluation["is_valid_plate"],
                "box": {
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h),
                    "polygon": [[int(pt[0]), int(pt[1])] for pt in polygon_points]
                }
            }

            all_detections.append(detection_item)

            if evaluation["is_valid_plate"]:
                plates.append(detection_item)

    # If no strict plate regex match was found, sort by length / confidence and pick best candidate
    if not plates and all_detections:
        candidate_detections = [
            d for d in all_detections
            if 5 <= len(d["text"]) <= 8 and d["confidence"] >= 0.5
        ]
        if candidate_detections:
            candidate_detections.sort(key=lambda item: item["confidence"], reverse=True)
            best_candidate = candidate_detections[0]
            plates.append({
                **best_candidate,
                "is_candidate": True
            })

    processing_time_ms = round((time.time() - start_time) * 1000, 2)

    return {
        "success": True,
        "image_width": img_width,
        "image_height": img_height,
        "processing_time_ms": processing_time_ms,
        "plates_count": len(plates),
        "plates": plates,
        "all_detections": all_detections
    }
