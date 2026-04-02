import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from tuya_connector import TuyaOpenAPI
from streamlit_autorefresh import st_autorefresh
import os
import pytz
from datetime import datetime

# --- 1. ตั้งค่าพื้นฐานและการเชื่อมต่อ ---
# ดึงค่าจาก Fly.io Secrets
ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")
# ใช้ Endpoint US ตามที่ระบุว่าเชื่อมต่อสำเร็จในอดีต
API_ENDPOINT = "https://openapi.tuyaus.com" 

# รายชื่อ Device IDs ของคุณ
DEVICES = {
    "PV Solar": "eb12a07e6d81bfad689phl",
    "Inverter": "eb366e7f16c29b4d66uoab",
    "PEA MAIN": "ebc4f09a8470bd323bkia0",
    "PEA 2": "ebc4f09a8470bd323bkia0" # ใช้ PEA MAIN สำรองตามที่คุณเคยระบุไว้
}

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Smart Solar Dashboard", layout="wide", initial_sidebar_state="collapsed")

# ระบบ Auto Refresh ทุก 30 วินาที
st_autorefresh(interval=30 * 1000, key="solar_refresh")

# --- 2. ฟังก์ชันดึงข้อมูลจาก Tuya ---
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

# --- 3. ฟังก์ชันสร้าง Gauge (ปรับขนาดให้พอดี 4 ตัวใน 1 แถว) ---
def create_gauge(value, title, color):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': f"<b>{title}</b>", 'font': {'size': 16}},
        number = {'suffix': " W", 'font': {'size': 20}},
        gauge = {
            'axis': {'range': [0, 5000], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 1,
        }
    ))
    fig.update_layout(height=220, margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig

# --- 4. ส่วนแสดงผล UI ---
st.markdown("<h2 style='text-align: center;'>☀️ MyHouseControl: Solar Monitoring</h2>", unsafe_allow_html=True)

# เวลาปัจจุบัน (ไทย)
tz = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz).strftime('%H:%M:%S')
st.markdown(f"<p style='text-align: center; color: gray;'>Last Sync: {now} (Auto-refresh 30s)</p>", unsafe_allow_html=True)

# ดึงข้อมูลจริง
results = {}
for name, dev_id in DEVICES.items():
    results[name] = get_tuya_status = get_tuya_data(dev_id)

# แสดงผล 4 Gauges ใน 1 แถว
cols = st.columns(4)
colors = ["#2ecc71", "#3498db", "#f39c12", "#e74c3c"] # Green, Blue, Orange, Red

for i, (name, data) in enumerate(results.items()):
    with cols[i]:
        # ดึงค่า Watt (สมมติชื่อ code คือ cur_power หรือตามรุ่นอุปกรณ์)
        # ตัวเลขอาจต้องหาร 10 หรือ 1 ตามรุ่นแอปเดิมของคุณ
        p_watt = data.get("cur_power", 0) 
        if p_watt > 10000: p_watt = p_watt / 10 # ปรับสเกลอัตโนมัติถ้าค่ามาเป็นหลักหมื่น
        
        st.plotly_chart(create_gauge(p_watt, name, colors[i]), use_container_width=True)
        
        # แสดงค่า Voltage และ Current ด้านล่าง
        v = data.get("cur_voltage", 0) / 10 if data.get("cur_voltage") else 0
        a = data.get("cur_current", 0) / 1000 if data.get("cur_current") else 0
        st.markdown(f"<div style='text-align:center;'><b>{v}V | {a}A</b></div>", unsafe_allow_html=True)

# --- 5. กราฟ Trend 4 ช่องด้านล่าง ---
st.markdown("---")
chart_cols = st.columns(4)
for i, name in enumerate(DEVICES.keys()):
    with chart_cols[i]:
        st.caption(f"{name} Power Trend")
        # สร้างข้อมูลจำลองสำหรับกราฟ (ในอนาคตสามารถเก็บลง Database ได้)
        dummy_data = pd.DataFrame({'W': [1500, 1540, 1547, 1530, 1544] if i==0 else [5, 6, 6, 7, 6]})
        st.line_chart(dummy_data, height=150)

# --- 6. Smart Home Control (ปุ่มกดด้านล่าง) ---
st.markdown("---")
st.subheader("🏠 Home Control")
btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
with btn_col1: st.button("💡 Outdoor Lights", use_container_width=True)
with btn_col2: st.button("🚿 Water Pump", use_container_width=True)
with btn_col3: st.button("🍃 Eco Mode", use_container_width=True)
with btn_col4: st.button("🔄 Refresh Data", use_container_width=True)
