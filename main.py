import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from tuya_connector import TuyaOpenAPI
from streamlit_autorefresh import st_autorefresh
import os
import pytz
from datetime import datetime

# --- 1. การเชื่อมต่อระบบ ---
ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")
API_ENDPOINT = "https://openapi.tuyaus.com" 

# รายชื่อรหัสอุปกรณ์ของคุณ
DEVICES = {
    "PV Solar": "eb12a07e6d81bfad689phl",
    "Inverter": "eb366e7f16c29b4d66uoab",
    "PEA MAIN": "ebc4f09a8470bd323bkia0",
    "PEA 2": "ebc4f09a8470bd323bkia0"
}

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Solar Dashboard", layout="wide")

# สั่งให้เว็บรีเฟรชตัวเองทุก 30 วินาที
st_autorefresh(interval=30 * 1000, key="solar_refresh")

# ฟังก์ชันดึงข้อมูล
def get_tuya_data(device_id):
    try:
        openapi = TuyaOpenAPI(API_ENDPOINT, ACCESS_ID, ACCESS_SECRET)
        openapi.connect()
        response = openapi.get(f"/v1.0/devices/{device_id}/status")
        if response.get("success"):
            return {item["code"]: item["value"] for item in response["result"]}
        return {}
    except:
        return {}

# ฟังก์ชันสร้างรูปเกจวัด
def create_gauge(value, title, color):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': f"<b>{title}</b>", 'font': {'size': 18}},
        number = {'suffix': " W", 'font': {'size': 24}},
        gauge = {
            'axis': {'range': [0, 5000]},
            'bar': {'color': color},
            'bgcolor': "#eeeeee",
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)")
    return fig

# --- ส่วนการแสดงผลบนเว็บ ---
st.markdown("<h2 style='text-align: center;'>☀️ MyHouseControl: Solar Dashboard</h2>", unsafe_allow_html=True)

tz = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz).strftime('%H:%M:%S')
st.markdown(f"<p style='text-align: center; color: gray;'>อัปเดตล่าสุด: {now}</p>", unsafe_allow_html=True)

# ดึงข้อมูลจริงจาก Tuya
cols = st.columns(4)
colors = ["#2ecc71", "#3498db", "#f39c12", "#e74c3c"]

for i, (name, dev_id) in enumerate(DEVICES.items()):
    data = get_tuya_data(dev_id)
    # ดึงค่าวัตต์ (ถ้าไม่มีให้เป็น 0)
    p_watt = data.get("cur_power", 0)
    # ถ้าค่ามาเป็นหลักหมื่นให้หาร 10 (ปรับตามอุปกรณ์)
    if p_watt > 10000: p_watt = p_watt / 10
    
    with cols[i]:
        st.plotly_chart(create_gauge(p_watt, name, colors[i]), use_container_width=True)
        v = data.get("cur_voltage", 0) / 10 if data.get("cur_voltage") else 0
        a = data.get("cur_current", 0) / 1000 if data.get("cur_current") else 0
        st.markdown(f"<p style='text-align:center;'>{v}V | {a}A</p>", unsafe_allow_html=True)

st.markdown("---")
st.subheader("🏠 Home Control")
b1, b2, b3, b4 = st.columns(4)
b1.button("💡 Outdoor Lights", use_container_width=True)
b2.button("🚿 Water Pump", use_container_width=True)
b3.button("🍃 Eco Mode", use_container_width=True)
b4.button("🔄 Refresh Data", use_container_width=True)
