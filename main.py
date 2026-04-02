import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from tuya_connector import TuyaOpenAPI
import os
import pytz
from datetime import datetime

# 1. ตั้งค่าการเชื่อมต่อ (ดึงจาก Fly.io Secrets)
ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")
# ถ้าใช้ในไทย มักจะเป็น Western Europe หรือ Central Europe (ตรวจสอบจากหน้า Tuya)
API_ENDPOINT = "https://openapi.tuyacn.com" 

# 2. ฟังก์ชันดึงข้อมูลจาก Tuya
def get_tuya_data(device_id):
    try:
        openapi = TuyaOpenAPI(API_ENDPOINT, ACCESS_ID, ACCESS_SECRET)
        openapi.connect()
        response = openapi.get(f"/v1.0/devices/{device_id}/status")
        return response.get("result", [])
    except Exception as e:
        st.error(f"Error connecting to Tuya: {e}")
        return []

# 3. ฟังก์ชันสร้าง Gauge (เข็มวัด)
def create_gauge(value, title, color):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': title},
        gauge = {
            'axis': {'range': [None, 5000]}, # ปรับช่วง Watt ได้ตามต้องการ
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# --- หน้าตาเว็บ ---
st.set_page_config(page_title="Solar Dashboard", layout="wide")
st.title("☀️ Smart Solar Energy Dashboard")

# แสดงเวลาไทย
tz = pytz.timezone('Asia/Bangkok')
st.write(f"Last Update: {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}")

# สร้าง 4 คอลัมน์สำหรับ Gauge
col1, col2, col3, col4 = st.columns(4)

# ตัวอย่างการแสดงผล (คุณต้องเอา Device ID ของคุณมาใส่แทน 'ID_...')
with col1:
    # สมมติค่า 490W จาก PV Solar
    st.plotly_chart(create_gauge(490, "PV Solar (W)", "#00ff00"), use_container_width=True)
    st.write("**Voltage:** 399.07 V")

with col2:
    st.plotly_chart(create_gauge(440, "Inverter (W)", "#0080ff"), use_container_width=True)
    st.write("**Voltage:** 226.41 V")

with col3:
    st.plotly_chart(create_gauge(10, "PEA MAIN (W)", "#ff8000"), use_container_width=True)
    st.write("**Voltage:** 234.8 V")

with col4:
    st.plotly_chart(create_gauge(10, "PEA 2 (W)", "#ff0000"), use_container_width=True)
    st.write("**Today's Yield:** 0.05 kWh")

# ส่วนของกราฟ Trend (สามารถเพิ่ม Logic เก็บข้อมูลย้อนหลังได้ที่นี่)
st.subheader("📊 Real-time Power Trends")
st.line_chart(pd.DataFrame({'Power': [440, 450, 430, 440, 460]})) # ตัวอย่างกราฟ
