# 🚗 Thai License Plate Recognition (LPR) - Batch Processing

โปรเจกต์สแกนและอ่านป้ายทะเบียนรถยนต์ไทยอัตโนมัติแบบยกชุด (Batch Processing) พัฒนาขึ้นเพื่อเป็นเครื่องมือช่วยในการเก็บข้อมูลยานพาหนะ (Data Acquisition) โดยใช้เทคโนโลยี Computer Vision ร่วมกับ API จาก **AI For Thai (NECTEC)**

[Image of License Plate Recognition flow chart]

## ✨ ฟีเจอร์หลัก (Features)
- 📂 **Batch Processing:** สามารถอ่านรูปภาพป้ายทะเบียนทั้งหมดในโฟลเดอร์ได้ในการรันครั้งเดียว
- 🔍 **High Accuracy:** ใช้ LPR v2 API ที่มีความแม่นยำสูง รองรับป้ายทะเบียนไทยทุกรูปแบบ (รวมถึงป้ายเอียงและป้ายประมูล)
- 📊 **Automated Reporting:** สรุปผลการอ่านทั้งหมดลงในไฟล์ `plate_report.csv` (รองรับภาษาไทยสำหรับเปิดใน Excel)
- 🛡️ **Security First:** ออกแบบการเก็บ API Key ผ่าน Environment Variables (`.env`) เพื่อความปลอดภัยในการแชร์โค้ด

## 🛠️ เครื่องมือที่ใช้ (Tech Stack)
- **Language:** Python 3.x
- **Libraries:** - `OpenCV` & `Pillow`: สำหรับการจัดการรูปภาพและวาดตัวอักษรไทย
  - `Requests`: สำหรับเชื่อมต่อ RESTful API
  - `python-dotenv`: สำหรับจัดการความลับของโปรเจกต์
- **API Engine:** [AI For Thai](https://aiforthai.in.th/) (License Plate Recognition v2)

## 🚀 การติดตั้งและใช้งาน (Installation & Usage)

### 1. เตรียมสภาพแวดล้อม
```bash
# Clone โปรเจกต์
git clone [https://github.com/thanasinyuntapun-maker/thai-license-plate-recognition.git](https://github.com/thanasinyuntapun-maker/thai-license-plate-recognition.git)
cd thai-license-plate-recognition

# ติดตั้ง Libraries
pip install -r requirements.txt
