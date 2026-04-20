#!/bin/bash
set -e

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Downloading Tesseract binary ==="
mkdir -p /tmp/tesseract/tessdata

wget -q "https://github.com/nicowillis/tesseract-linux-binary/releases/download/v5.0.0/tesseract" \
     -O /tmp/tesseract/tesseract

chmod +x /tmp/tesseract/tesseract

echo "=== Downloading English language data ==="
wget -q "https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata" \
     -O /tmp/tesseract/tessdata/eng.traineddata

echo "=== Verifying ==="
/tmp/tesseract/tesseract --version && echo "Tesseract OK"

echo "=== Build complete ==="
