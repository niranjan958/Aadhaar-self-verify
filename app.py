import os
import re
import subprocess
import pytesseract
from flask import Flask, request, jsonify
from PIL import Image, ImageFilter, ImageEnhance
from io import BytesIO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TESS_BIN = os.path.join(BASE_DIR, 'tesseract', 'squashfs-root', 'AppRun')
TESSDATA = os.path.join(BASE_DIR, 'tesseract', 'tessdata')

os.environ['TESSDATA_PREFIX'] = TESSDATA
pytesseract.pytesseract.tesseract_cmd = TESS_BIN

app = Flask(__name__)


def extract_aadhaar_numbers(text):
    clean = re.sub(r'[^0-9]', '', text)
    found = []
    for i in range(len(clean) - 11):
        candidate = clean[i:i+12]
        if (len(candidate) == 12 and
                candidate[0] not in ('0', '1') and
                candidate not in found):
            found.append(candidate)
    return found, clean


def preprocess_image(image):
    # ── Step 1: Convert to grayscale — fewer pixels to process
    image = image.convert('L')

    # ── Step 2: Resize to max 800px width — faster OCR
    if image.width > 800:
        ratio = 800 / image.width
        image = image.resize((800, int(image.height * ratio)), Image.LANCZOS)

    # ── Step 3: Increase contrast — better digit detection
    enhancer = ImageEnhance.Contrast(image)
    image    = enhancer.enhance(2.0)

    # ── Step 4: Sharpen — cleaner edges on digits
    image = image.filter(ImageFilter.SHARPEN)

    return image


def run_ocr(image):
    image = preprocess_image(image)
    # digits only mode — much faster than full OCR
    text  = pytesseract.image_to_string(
        image,
        config='--oem 1 --psm 6 -c tessedit_char_whitelist=0123456789'
    )
    return text


def is_match(entered, numbers_found, clean_ocr):
    if entered in numbers_found:
        return True
    if entered in clean_ocr:
        return True
    return False


@app.route('/', methods=['GET'])
def health():
    try:
        result = subprocess.run(
            [TESS_BIN, '--version'],
            capture_output=True, text=True, timeout=10
        )
        tess_ok = result.returncode == 0
        tess_version = (result.stdout + result.stderr).strip()
    except Exception as e:
        tess_ok = False
        tess_version = str(e)

    return jsonify({
        "status":       "ok",
        "service":      "Aadhaar OCR — Tesseract",
        "tess_ok":      tess_ok,
        "tess_version": tess_version
    })


@app.route('/verify', methods=['POST'])
def verify():
    try:
        aadhaar_number = request.args.get("aadhaar_number", "").replace(" ", "").replace("-", "")

        uploaded_file = (
            request.files.get("content") or
            request.files.get("file") or
            request.files.get("Upload_Aadhaar") or
            (list(request.files.values())[0] if request.files else None)
        )

        if not aadhaar_number:
            return jsonify({"success": False, "match": False,
                            "message": "aadhaar_number missing"}), 400
        if len(aadhaar_number) != 12 or not aadhaar_number.isdigit():
            return jsonify({"success": False, "match": False,
                            "message": "Must be 12 digits"}), 400
        if not uploaded_file:
            return jsonify({"success": False, "match": False,
                            "message": "file missing"}), 400

        file_bytes = uploaded_file.read()
        if not file_bytes or len(file_bytes) < 100:
            return jsonify({"success": False, "match": False,
                            "message": "File empty"}), 400

        full_text = ""

        # ── PDF ───────────────────────────────────────────
        if file_bytes[:4] == b'%PDF':
            try:
                from pdf2image import convert_from_bytes
                pages = convert_from_bytes(file_bytes, dpi=150)
                for page in pages:
                    full_text += run_ocr(page) + " "
            except Exception as e:
                return jsonify({"success": False, "match": False,
                                "message": "PDF failed: " + str(e)}), 500

        # ── Image ─────────────────────────────────────────
        else:
            try:
                image     = Image.open(BytesIO(file_bytes))
                image.load()
                full_text = run_ocr(image)
            except Exception as e:
                return jsonify({"success": False, "match": False,
                                "message": "Image failed: " + str(e)}), 500

        if not full_text.strip():
            return jsonify({"success": False, "match": False,
                            "message": "No text detected"}), 200

        numbers_found, clean_ocr = extract_aadhaar_numbers(full_text)
        match = is_match(aadhaar_number, numbers_found, clean_ocr)

        return jsonify({
            "success":       True,
            "match":         match,
            "numbers_found": numbers_found,
            "entered":       aadhaar_number,
            "message":       "Match found" if match else "Number not found on card"
        })

    except Exception as e:
        return jsonify({"success": False, "match": False,
                        "message": "Server error: " + str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
