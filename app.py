import os
import re
import subprocess
import pytesseract
from flask import Flask, request, jsonify
from PIL import Image
from io import BytesIO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPIMAGE = os.path.join(BASE_DIR, 'tesseract', 'tesseract')
TESSDATA = os.path.join(BASE_DIR, 'tesseract', 'tessdata')

# ── Use AppImage directly with TESSDATA_PREFIX ────────
os.environ['TESSDATA_PREFIX'] = TESSDATA
os.environ['APPIMAGE_EXTRACT_AND_RUN'] = '1'
pytesseract.pytesseract.tesseract_cmd = APPIMAGE

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


def compress_image(image):
    if image.mode != 'RGB':
        image = image.convert('RGB')
    if image.width > 1200:
        ratio = 1200 / image.width
        image = image.resize((1200, int(image.height * ratio)), Image.LANCZOS)
    if image.height > 1600:
        ratio = 1600 / image.height
        image = image.resize((int(image.width * ratio), 1600), Image.LANCZOS)
    return image


def run_ocr(image):
    image = compress_image(image)
    text  = pytesseract.image_to_string(image, config='--oem 3 --psm 6')
    if not text.strip():
        text = pytesseract.image_to_string(image, config='--oem 3 --psm 11')
    return text


def is_match(entered, numbers_found, clean_ocr):
    if entered in numbers_found:
        return True
    if entered in clean_ocr:
        return True
    return False


@app.route('/', methods=['GET'])
def health():
    # Test if tesseract actually runs
    try:
        result = subprocess.run(
            [APPIMAGE, '--version'],
            capture_output=True, text=True,
            env={**os.environ, 'APPIMAGE_EXTRACT_AND_RUN': '1'},
            timeout=10
        )
        tess_version = result.stdout.strip() or result.stderr.strip()
        tess_ok = result.returncode == 0
    except Exception as e:
        tess_version = str(e)
        tess_ok = False

    return jsonify({
        "status":      "ok",
        "service":     "Aadhaar OCR — Tesseract",
        "tess_ok":     tess_ok,
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
                pages = convert_from_bytes(file_bytes, dpi=200)
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
