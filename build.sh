#!/bin/bash
set -e

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Downloading Tesseract AppImage ==="
mkdir -p ./tesseract/tessdata

wget -q "https://github.com/AlexanderP/tesseract-appimage/releases/download/v5.3.3/tesseract-5.3.3-x86_64.AppImage" \
     -O ./tesseract/tesseract.AppImage

chmod +x ./tesseract/tesseract.AppImage

echo "=== Extracting AppImage (so it runs fast without FUSE) ==="
cd ./tesseract
APPIMAGE_EXTRACT_AND_RUN=1 ./tesseract.AppImage --appimage-extract
cd ..

echo "=== Verifying extracted binary ==="
./tesseract/squashfs-root/AppRun --version && echo "Tesseract OK"

echo "=== Downloading English language data ==="
wget -q "https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata" \
     -O ./tesseract/tessdata/eng.traineddata

echo "=== Build complete ==="
