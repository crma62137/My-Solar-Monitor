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
# จากรูป 27 คุณใช้ US แต่จากประสบการณ์ไทยมักจะไปตกที่ EU ลองตัวนี้ก่อนครับ
API_ENDPOINT = "https://openapi.tuyaus.com" 

DEVICES = {
    "PV Solar": "eb12a07e6d81bfad689phl",
    "Inverter": "eb366e7f16c29b4d66uoab",
    "PEA MAIN": "ebc4f09a8470bd323bkia0",
    "PEA 2": "ebe67840ae208eef35yseh" 
}

st.set_page_config(page_title="Solar Dashboard", layout="wide")
st_autorefresh(interval=30 * 1000, key="solar_refresh")

def get_tuya_data(device_id):
    try:
        openapi = TuyaOpenAPI(API_ENDPOINT, ACCESS_ID, ACCESS_SECRET)
        openapi.connect()
        response = openapi.get(f"/v1.0/devices/{device_id}/status")
        
        if response.get("success"):
            res = {item["code"]: item["value"] for item in response["result"]}
            
            # ดึงค่าตามรหัสที่เห็นในหน้าจอ JSON ของคุณ (รูป 29)
            # พยายามหาทุกลูกแบบที่อาจจะเป็นไปได้
            watt = res.get("cur_power") or res.get("active_power") or res.get("total_power") or 0
            volt = res.get("cur_voltage") or res.get("voltage") or 0
            curr = res.get("cur_current") or res.get("current") or 0
            
            # จัดการตัวหาร (ถ้าค่ามาเป็น 2300 แสดงว่าคือ 230.0V)
            return {
                "watt": float(watt) / 10 if watt > 10000 else float(watt),
                "voltage": float(volt) / 10 if volt > 500 else float(volt),
                "current": float(curr) / 1000 if curr > 100 else float(curr)
            }
        return {"watt": 0, "voltage": 0, "current": 0}
    except:
        return {"watt": 0, "voltage": 0, "current": 0}

def create_gauge(value, title, color):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': f"<b>{title}</b>", 'font': {'size': 18, 'color': 'white'}},
        number = {'suffix': " W", 'font': {'size': 24, 'color': 'white'}},
        gauge = {'axis': {'range': [0, 5000]}, 'bar': {'color': color}, 'bgcolor': "#333333"}
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)")
    return fig

# --- ส่วนแสดงผล ---
st.markdown("<h2 style='text-align: center; color: #FFD700;'>🏠 MyHouseControl: Solar Monitoring</h2>", unsafe_allow_html=True)

tz = pytz.timezone('Asia/Bangkok')
st.markdown(f"<p style='text-align: center; color: gray;'>อัปเดต: {datetime.now(tz).strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)

cols = st.columns(4)
colors = ["#2ecc71", "#3498db", "#f39c12", "#e74c3c"]

for i, (name, dev_id) in enumerate(DEVICES.items()):
    data = get_tuya_data(dev_id)
    with cols[i]:
        st.plotly_chart(create_gauge(data["watt"], name, colors[i]), use_container_width=True)
        st.markdown(f"<p style='text-align:center; color: white;'>{data['voltage']}V | {data['current']}A</p>", unsafe_allow_html=True)

st.markdown("---")
if st.button("🔄 ดึงข้อมูลเดี๋ยวนี้"):
    st.rerun()
