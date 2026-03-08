"""Decode QR code from image and print URL."""
import sys
from pathlib import Path
import cv2
import numpy as np

img_path = sys.argv[1] if len(sys.argv) > 1 else None
if not img_path or not Path(img_path).exists():
    print("Usage: python decode_qr.py <image_path>", file=sys.stderr)
    sys.exit(1)

img = cv2.imread(img_path)
if img is None:
    print("Could not load image", file=sys.stderr)
    sys.exit(1)

det = cv2.QRCodeDetector()

def try_decode(im):
    data, _, _ = det.detectAndDecode(im)
    return data.strip() if data else None

# Try full image (original + grayscale)
for im in [img, cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)]:
    u = try_decode(im)
    if u:
        print(u)
        sys.exit(0)

# Crop top-right quarter (QR is usually there in book pages)
h, w = img.shape[:2]
crop = img[0 : h // 2, w // 2 : w]
for im in [crop, cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)]:
    u = try_decode(im)
    if u:
        print(u)
        sys.exit(0)

# Upscale crop and retry
if max(crop.shape[:2]) < 600:
    scaled = cv2.resize(crop, (crop.shape[1] * 2, crop.shape[0] * 2), interpolation=cv2.INTER_CUBIC)
    u = try_decode(scaled)
    if u:
        print(u)
        sys.exit(0)

print("No QR code found", file=sys.stderr)
sys.exit(1)
