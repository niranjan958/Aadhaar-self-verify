#!/bin/bash
set -e

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Downloading Tesseract binary ==="
mkdir -p ./tesseract/tessdata

wget -q "https://github.com/nicowillis/tesseract-linux-binary/releases/download/v5.0.0/tesseract" \
     -O ./tesseract/tesseract

chmod +x ./tesseract/tesseract

echo "=== Downloading English language data ==="
wget -q "https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata" \
     -O ./tesseract/tessdata/eng.traineddata

echo "=== Verifying ==="
./tesseract/tesseract --version && echo "Tesseract OK"

echo "=== Build complete ==="
