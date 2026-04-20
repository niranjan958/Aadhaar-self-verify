#!/bin/bash
set -e

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Downloading Tesseract binary ==="
mkdir -p /opt/tesseract/tessdata

# Download pre-built Tesseract 5 binary for Linux x64
wget -q "https://github.com/itinerantfoodie/tesseract-static/releases/download/v5.3.0/tesseract" \
     -O /opt/tesseract/tesseract || \
wget -q "https://github.com/nicowillis/tesseract-linux-binary/releases/download/v5.0.0/tesseract" \
     -O /opt/tesseract/tesseract

chmod +x /opt/tesseract/tesseract

echo "=== Downloading English language data ==="
wget -q "https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata" \
     -O /opt/tesseract/tessdata/eng.traineddata

echo "=== Verifying Tesseract ==="
/opt/tesseract/tesseract --version && echo "Tesseract OK" || echo "Tesseract binary check failed — will fallback"

echo "=== Build complete ==="
