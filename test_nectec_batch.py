import cv2
import os
import requests
import numpy as np
import csv
import time
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# โหลดค่าตัวแปรความลับจากไฟล์ .env
load_dotenv() 

# --- 1. ตั้งค่า API และ Path ---
# ดึง API Key จากไฟล์ .env (ทำให้โค้ดปลอดภัย ส่งให้ใครก็ไม่มี Key หลุด)
AIFORTHAI_API_KEY = os.getenv("AIFORTHAI_API_KEY") 

if not AIFORTHAI_API_KEY:
    print("❌ ไม่พบ API Key! กรุณาสร้างไฟล์ .env และใส่ AIFORTHAI_API_KEY")
    exit()

URL = "https://api.aiforthai.in.th/lpr-v2"

# ⚠️ เวลาส่งให้เพื่อน อย่าลืมให้เพื่อนแก้ Path 2 บรรทัดนี้ให้ตรงกับเครื่องของเขาด้วยนะครับ
INPUT_FOLDER = '/Users/thanasinyuntapun/vscode ai project/vissual/plateThai'
OUTPUT_FOLDER = "/Users/thanasinyuntapun/vscode ai project/vissual/plateThai_results"
CSV_FILE = os.path.join(OUTPUT_FOLDER, "plate_report.csv") 

if not os.path.exists(OUTPUT_FOLDER): os.makedirs(OUTPUT_FOLDER)

# --- 2. ฟังก์ชันวาดตัวหนังสือภาษาไทย ---
def draw_thai(img, text, pos):
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    # ⚠️ ถ้าเพื่อนใช้ Windows อาจจะต้องเปลี่ยน Path ฟอนต์ตรงนี้ด้วย (เช่น "C:/Windows/Fonts/tahoma.ttf")
    try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Ayuthaya.ttf", 60)
    except: font = ImageFont.load_default()
    
    # วาดพื้นหลังสีดำโปร่งแสงให้ตัวหนังสือ
    text_bbox = draw.textbbox(pos, text, font=font)
    draw.rectangle([text_bbox[0]-10, text_bbox[1]-10, text_bbox[2]+10, text_bbox[3]+10], fill=(0,0,0,150))
    draw.text(pos, text, font=font, fill=(0, 255, 0))
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

# --- 3. เริ่มกระบวนการ Batch Processing ---
print(f"🚀 เริ่มสแกนป้ายทะเบียนด้วย NECTEC API...")

image_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

# เปิดไฟล์ CSV เพื่อบันทึกผลลัพธ์
with open(CSV_FILE, mode='w', newline='', encoding='utf-8-sig') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(['ชื่อไฟล์', 'เลขทะเบียน', 'จังหวัด', 'สถานะ'])

    for index, filename in enumerate(image_files, start=1):
        input_path = os.path.join(INPUT_FOLDER, filename)
        output_path = os.path.join(OUTPUT_FOLDER, f"nectec_{filename}")
        
        print(f"[{index}/{len(image_files)}] กำลังประมวลผล: {filename}...")
        
        image = cv2.imread(input_path)
        if image is None:
            writer.writerow([filename, '-', '-', 'Error: อ่านภาพไม่ได้'])
            continue

        # ยิง Request ไปที่ API ของ NECTEC
        headers = {'Apikey': AIFORTHAI_API_KEY}
        with open(input_path, 'rb') as file:
            files = {'image': (filename, file, 'image/jpeg')}
            try:
                response = requests.post(URL, headers=headers, files=files)
                response.raise_for_status()
                result = response.json()
            except Exception as e:
                print(f"   ❌ API Error: {e}")
                writer.writerow([filename, '-', '-', 'Error: API ล้มเหลว'])
                continue

        # ตรวจสอบผลลัพธ์จาก API
        if isinstance(result, list) and len(result) > 0:
            plate = result[0] 
            plate_text = plate.get('lpr', 'ไม่พบข้อความ')
            province = plate.get('province_th') or plate.get('province') or 'ไม่ทราบจังหวัด'
            
            print(f"   ✅ อ่านได้: {plate_text} {province}")
            writer.writerow([filename, plate_text, province, 'สำเร็จ'])
            
            # วาดกรอบและข้อความลงบนภาพ
            full_text = f"{plate_text} {province}"
            bbox = plate.get('bbox', {})
            
            if isinstance(bbox, dict) and 'x' in bbox:
                x, y = int(bbox['x']), int(bbox['y'])
                w, h = int(bbox.get('width', 0)), int(bbox.get('height', 0))
                
                cv2.rectangle(image, (x, y), (x+w, y+h), (0, 0, 255), 4)
                image = draw_thai(image, full_text, (x, max(0, y-80)))
            else:
                image = draw_thai(image, full_text, (50, 50))
                
            cv2.imwrite(output_path, image)
        else:
            print(f"   ⚠️ ไม่พบป้ายในภาพนี้")
            writer.writerow([filename, '-', '-', 'ไม่พบป้ายทะเบียน'])
        
        # หน่วงเวลา 1 วินาที ป้องกัน Server แบน
        time.sleep(1)

print(f"\n🎉 สแกนเสร็จสมบูรณ์! ข้อมูลถูกบันทึกไว้ที่ plate_report.csv")