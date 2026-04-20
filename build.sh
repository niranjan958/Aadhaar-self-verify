#!/bin/bash
set -e

echo "=== Installing Python dependencies ==="
pip install -r requirements.txt

echo "=== Downloading Tesseract AppImage ==="
mkdir -p ./tesseract/tessdata

# Download real working Tesseract AppImage
wget -q "https://github.com/AlexanderP/tesseract-appimage/releases/download/v5.3.3/tesseract-5.3.3-x86_64.AppImage" \
     -O ./tesseract/tesseract

chmod +x ./tesseract/tesseract

# Extract AppImage so it runs without FUSE (Render doesn't support FUSE)
cd ./tesseract
./tesseract --appimage-extract > /dev/null 2>&1 || true
cd ..

# Use extracted binary if AppImage extraction worked
if [ -f "./tesseract/squashfs-root/AppRun" ]; then
  echo "Using extracted AppImage"
  cp ./tesseract/squashfs-root/usr/bin/tesseract ./tesseract/tesseract_bin
  cp -r ./tesseract/squashfs-root/usr/share/tessdata ./tesseract/tessdata_extracted || true
fi

echo "=== Downloading English language data ==="
wget -q "https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata" \
     -O ./tesseract/tessdata/eng.traineddata

echo "=== Build complete ==="
