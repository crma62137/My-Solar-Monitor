import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from tuya_connector import TuyaOpenAPI
from streamlit_autorefresh import st_autorefresh
import os
import pytz
from datetime import datetime

# --- 1. การเชื่อมต่อระบบ (ดึงค่าจาก Environment Variables ใน Fly.io) ---
ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")
# ลองใช้ Endpoint US ตามที่คุณตั้งค่าไว้ ถ้ายังขึ้น 0 ให้เปลี่ยนเป็น https://openapi.tuyaeu.com
API_ENDPOINT = "https://openapi.tuyaus.com" 

# รายชื่อรหัสอุปกรณ์ที่แก้ไขให้ตรงกับบัญชีของคุณแล้ว
DEVICES = {
    "PV Solar": "eb12a07e6d81bfad689phl",
    "Inverter": "eb366e7f16c29b4d66uoab",
    "PEA MAIN": "ebc4f09a8470bd323bkia0",
    "PEA 2": "ebe67840ae208eef35yseh"  # แก้ไขรหัสไม่ให้ซ้ำกับ MAIN แล้ว
}

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="MyHouse Solar Dashboard", layout="wide")

# สั่งให้เว็บรีเฟรชตัวเองทุก 30 วินาที
st_autorefresh(interval=30 * 1000, key="solar_refresh")

# ฟังก์ชันดึงข้อมูลจาก Tuya แบบละเอียดขึ้น
def get_tuya_data(device_id):
    try:
        openapi = TuyaOpenAPI(API_ENDPOINT, ACCESS_ID, ACCESS_SECRET)
        openapi.connect()
        response = openapi.get(f"/v1.0/devices/{device_id}/status")
        if response.get("success"):
            # แปลงรูปแบบข้อมูลให้ดึงง่ายขึ้น
            res_dict = {item["code"]: item["value"] for item in response["result"]}
            
            # --- ดักจับค่า Watt จากหลายๆ Code ที่ Tuya ชอบใช้ ---
            # พยายามหาจาก cur_power ก่อน ถ้าไม่มีให้หาจาก active_power หรือ total_power
            p_watt = res_dict.get("cur_power") or res_dict.get("active_power") or res_dict.get("total_power") or 0
            
            # ปรับหน่วย: ถ้าค่าส่งมาหลักหมื่น (เช่น 15470) ให้หาร 10 เพื่อให้เป็น 1547.0 วัตต์
            if p_watt > 20000:
                p_watt = p_watt / 10
            
            # ปรับหน่วย Voltage และ Current
            v_raw = res_dict.get("cur_voltage") or res_dict.get("voltage") or 0
            a_raw = res_dict.get("cur_current") or res_dict.get("current") or 0
            
            return {
                "watt": float(p_watt),
                "voltage": float(v_raw) / 10 if v_raw > 0 else 0,
                "current": float(a_raw) / 1000 if a_raw > 0 else 0
            }
        return {"watt": 0, "voltage": 0, "current": 0}
    except:
        return {"watt": 0, "voltage": 0, "current": 0}

# ฟังก์ชันสร้างรูปเกจวัด (Gauge)
def create_gauge(value, title, color):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': f"<b>{title}</b>", 'font': {'size': 16}},
        number = {'suffix': " W", 'font': {'size': 24}, 'valueformat': '.1f'},
        gauge = {
            'axis': {'range': [0, 5000]},
            'bar': {'color': color},
            'bgcolor': "#eeeeee",
            'steps': [
                {'range': [0, 2500], 'color': "#f8f9fa"},
                {'range': [2500, 5000], 'color': "#e9ecef"}
            ],
        }
    ))
    fig.update_layout(height=220, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)")
    return fig

# --- ส่วนการแสดงผลบนหน้าเว็บ ---
st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🏠 MyHouseControl: Solar Dashboard</h2>", unsafe_allow_html=True)

# แสดงเวลาปัจจุบัน (ไทย)
tz = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz).strftime('%d/%m/%Y %H:%M:%S')
st.markdown(f"<p style='text-align: center; color: #6B7280;'>อัปเดตล่าสุด: {now}</p>", unsafe_allow_html=True)

# สร้างแถวสำหรับ 4 เกจ
cols = st.columns(4)
colors = ["#2ecc71", "#3498db", "#f39c12", "#e74c3c"] # เขียว, ฟ้า, ส้ม, แดง

# วนลูปดึงข้อมูลและแสดงผล
for i, (name, dev_id) in enumerate(DEVICES.items()):
    with st.spinner(f'กำลังอ่านค่า {name}...'):
        data = get_tuya_data(dev_id)
        
    with cols[i]:
        # แสดงเกจวัด
        st.plotly_chart(create_gauge(data["watt"], name, colors[i]), use_container_width=True)
        # แสดงรายละเอียด Voltage และ Current ด้านล่างเกจ
        st.markdown(
            f"<div style='text-align:center; background-color:#f1f5f9; padding:10px; border-radius:10px;'>"
            f"<span style='color:#475569;'>⚡ {data['voltage']:.1f} V</span> | "
            f"<span style='color:#475569;'>🔌 {data['current']:.3f} A</span>"
            f"</div>", 
            unsafe_allow_html=True
        )

st.markdown("---")

# ส่วนควบคุมบ้าน (Home Control)
st.subheader("🛠️ Home Control System")
c1, c2, c3, c4 = st.columns(4)
if c1.button("💡 Outdoor Lights", use_container_width=True):
    st.toast("กำลังสั่งเปิดไฟสนาม...")
if c2.button("🚿 Water Pump", use_container_width=True):
    st.toast("กำลังสั่งงานปั๊มน้ำ...")
if c3.button("🍃 Eco Mode", use_container_width=True):
    st.toast("เปิดโหมดประหยัดพลังงาน")
if c4.button("🔄 Force Refresh", use_container_width=True):
    st.rerun()
