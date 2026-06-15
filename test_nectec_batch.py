import cv2
import os
import requests
import numpy as np
import csv
import time
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

# ==================== CONFIG ====================
API_KEY = os.getenv("AIFORTHAI_API_KEY")
if not API_KEY:
    raise ValueError("ไม่พบ AIFORTHAI_API_KEY ใน .env")

API_URL    = "https://api.aiforthai.in.th/lpr-v2"
FONT_PATH  = "/System/Library/Fonts/Supplemental/Ayuthaya.ttf"  # Windows: "C:/Windows/Fonts/tahoma.ttf"
FONT_SIZE  = 60
DELAY      = 3    # วินาทีระหว่างภาพ
MAX_RETRY  = 3    # จำนวนครั้ง retry
TIMEOUT    = 15   # วินาที timeout ต่อ request

BASE_DIR      = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
INPUT_FOLDER  = os.path.join(BASE_DIR, "plateThai")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "plateThai_results")
CSV_FILE      = os.path.join(OUTPUT_FOLDER, "plate_report.csv")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
# ================================================


def load_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()


def draw_thai(img: np.ndarray, text: str, pos: tuple) -> np.ndarray:
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert("RGBA")
    overlay = Image.new("RGBA", img_pil.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)
    font    = load_font(FONT_SIZE)

    bbox = draw.textbbox(pos, text, font=font)
    draw.rectangle([bbox[0]-10, bbox[1]-10, bbox[2]+10, bbox[3]+10], fill=(0, 0, 0, 150))
    draw.text(pos, text, font=font, fill=(0, 255, 0, 255))

    composited = Image.alpha_composite(img_pil, overlay)
    return cv2.cvtColor(np.array(composited.convert("RGB")), cv2.COLOR_RGB2BGR)


def call_api(image_path: str, filename: str) -> Optional[dict]:
    headers = {"Apikey": API_KEY}
    ext  = os.path.splitext(filename)[1].lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"

    for attempt in range(1, MAX_RETRY + 1):
        try:
            with open(image_path, "rb") as f:
                response = requests.post(
                    API_URL,
                    headers=headers,
                    files={"image": (filename, f, mime)},
                    timeout=TIMEOUT,
                )

            if response.status_code == 429:
                wait = attempt * 5
                print(f"   ⏳ Rate limit — retry {attempt}/{MAX_RETRY} รอ {wait}s")
                time.sleep(wait)
                continue

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            print(f"   ⏳ Timeout — retry {attempt}/{MAX_RETRY}")
            time.sleep(attempt * 3)

        except Exception as e:
            print(f"   ❌ API Error: {e}")
            return None

    return None


def process_result(image: np.ndarray, plate: dict, output_path: str):
    plate_text = plate.get("lpr", "N/A")
    province   = plate.get("province_th") or plate.get("province") or "ไม่ทราบจังหวัด"
    label      = f"{plate_text} {province}"

    bbox = plate.get("bbox", {})
    if isinstance(bbox, dict) and "x" in bbox:
        x = int(bbox["x"])
        y = int(bbox["y"])
        w = int(bbox.get("width", 0))
        h = int(bbox.get("height", 0))
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 4)
        image = draw_thai(image, label, (x, max(0, y - 80)))
    else:
        image = draw_thai(image, label, (50, 50))

    cv2.imwrite(output_path, image)
    return plate_text, province


# ==================== MAIN ====================
image_files = sorted(
    f for f in os.listdir(INPUT_FOLDER)
    if f.lower().endswith((".png", ".jpg", ".jpeg"))
)
total = len(image_files)
print(f"🚀 พบภาพ {total} ไฟล์ — เริ่มสแกนด้วย NECTEC LPR API\n")

with open(CSV_FILE, mode="w", newline="", encoding="utf-8-sig") as csv_f:
    writer = csv.writer(csv_f)
    writer.writerow(["filename", "plate", "province", "status"])

    for idx, filename in enumerate(image_files, start=1):
        input_path  = os.path.join(INPUT_FOLDER, filename)
        output_path = os.path.join(OUTPUT_FOLDER, f"result_{filename}")

        print(f"[{idx:02d}/{total}] {filename}")

        image = cv2.imread(input_path)
        if image is None:
            print("   ⚠️  อ่านภาพไม่ได้ — ข้าม")
            writer.writerow([filename, "-", "-", "error: read_failed"])
            continue

        result = call_api(input_path, filename)
        if result is None:
            writer.writerow([filename, "-", "-", "error: api_failed"])
            continue

        if isinstance(result, list) and result:
            plate_text, province = process_result(image, result[0], output_path)
            print(f"   ✅ {plate_text}  {province}")
            writer.writerow([filename, plate_text, province, "success"])
        else:
            print("   ⚠️  ไม่พบป้ายทะเบียน")
            writer.writerow([filename, "-", "-", "no_plate"])

        time.sleep(DELAY)

print(f"\n🎉 เสร็จสมบูรณ์  ผลลัพธ์อยู่ที่: {CSV_FILE}")
