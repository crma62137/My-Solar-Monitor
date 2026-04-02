# ใช้ Python version 3.9 แบบประหยัดพื้นที่
FROM python:3.9-slim

# ตั้งค่าโฟลเดอร์ทำงานในระบบ
WORKDIR /app

# คัดลอกไฟล์ทั้งหมดจากเครื่องเราเข้าไปในระบบ Fly.io
COPY . .

# ติดตั้ง Library ตามที่ระบุไว้ในไฟล์แรก
RUN pip install --no-cache-dir -r requirements.txt

# เปิด Port 8501 สำหรับ Streamlit
EXPOSE 8501

# คำสั่งรันแอปพลิเคชัน
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
