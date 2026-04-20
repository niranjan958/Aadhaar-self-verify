# Aadhaar OCR — Tesseract (No API Keys Required)

Pure Python Tesseract OCR for Aadhaar number validation.
No OCR.space API. No external API calls. 100% self-contained.

## How it works

```
Zoho Creator Form
      ↓ files: input.Upload_Aadhaar + aadhaar_number in URL
Render (this app)
      ↓ Tesseract reads text from image/PDF
      ↓ Extracts 12-digit numbers
      ↓ Compares with entered number
      ↓ Returns { match: true/false }
Zoho Creator
      ↓ Saves result to form fields
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | Health check |
| POST | /verify?aadhaar_number=XXXX | Verify Aadhaar |

## Deploy on Render

1. Push this repo to GitHub
2. Go to render.com → New Web Service
3. Connect your GitHub repo
4. Settings:
   - **Build Command:** `chmod +x build.sh && ./build.sh`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free
5. Click Deploy

## Deluge script (Zoho Creator)

```
renderUrl = "https://YOUR-RENDER-URL.onrender.com/verify?aadhaar_number=" + enteredNumber;

ocrResponseDetailed = invokeurl
[
  url: renderUrl
  type: POST
  files: input.Upload_Aadhaar
  detailed: true
];
```

## Supported file types
- JPG / JPEG
- PNG
- PDF (all pages scanned)

## No API keys needed
Tesseract runs locally on the server. Zero cost, zero limits.
