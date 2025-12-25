import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
import time
from datetime import datetime
import os

# Defaults to localhost if not set, but allows Render to inject the real URL
API_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Kartavya | Police Command", page_icon=None, layout="wide", initial_sidebar_state="expanded")

ZONES = {
    "NORTH": {"color": "#2979FF", "bounds": [[15.8, 73.6], [15.8, 74.2], [15.44, 74.2], [15.44, 73.6]], "center": [15.60, 73.90]},
    "SOUTH": {"color": "#FF6D00", "bounds": [[15.44, 73.6], [15.44, 74.2], [14.9, 74.2], [14.9, 73.6]], "center": [15.20, 74.00]}
}

def load_css():
    st.markdown("""
    <style>
        #MainMenu, footer {visibility: hidden;} header[data-testid="stHeader"] {background: transparent; z-index: 1;} div[data-testid="stDecoration"] {display: none;}
        
        /* HIDE ANCHOR LINKS (The chain icon next to headers) */
        .st-emotion-cache-1629p8f a, h1 a, h2 a, h3 a, h4 a, h5 a { display: none !important; pointer-events: none; }
        
        button[data-testid="collapsedControl"] {
            display: block !important; visibility: visible !important; color: white !important; background-color: #0056b3 !important;
            border-radius: 4px !important; width: 40px !important; height: 40px !important; position: fixed !important; top: 20px !important; left: 20px !important; z-index: 99999 !important; border: 1px solid #004494 !important;
        }
        .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', sans-serif; }
        .login-title { font-size: 3rem; font-weight: 800; color: #f0f6fc; margin-bottom: 0; line-height: 1.2; text-transform: uppercase; letter-spacing: 2px; }
        .login-subtitle { font-size: 1.1rem; color: #8b949e; font-weight: 400; margin-top: 5px; margin-bottom: 2rem; letter-spacing: 1px; text-transform: uppercase; border-top: 1px solid #30363d; display: inline-block; padding-top: 10px; }
        div[data-testid="stForm"] { background-color: #161b22; border: 1px solid #30363d; padding: 25px; border-radius: 4px; }
        button { border-radius: 2px !important; text-transform: uppercase; font-weight: 600; font-size: 13px; letter-spacing: 0.5px; }
        button[kind="primary"] { background-color: #1f6feb !important; border: 1px solid #1f6feb; color: white !important; }
        button[kind="secondary"] { background-color: #21262d !important; border: 1px solid #30363d; color: #c9d1d9 !important; }
        .status-pill { padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; border: 1px solid; display: inline-block; }
        .pill-safe { background: #23863620; color: #3fb950; border-color: #238636; }
        .pill-risk { background: #da363320; color: #f85149; border-color: #da3633; }
        .pill-warn { background: #9e6a0320; color: #d29922; border-color: #9e6a03; }
        .pill-info { background: #1f6feb20; color: #58a6ff; border-color: #1f6feb; }
        .notif-box { background: #21262d; border-left: 4px solid #d29922; padding: 15px; margin-bottom: 15px; border-radius: 0 4px 4px 0; }
        .log-entry { font-family: 'Courier New', monospace; padding: 4px 0; border-bottom: 1px solid #21262d; font-size: 12px; color: #8b949e; }
        .log-lvl { font-weight: bold; margin-right: 8px; }
        [data-testid="stSidebar"] img { border-radius: 50%; border: 2px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

if 'token' not in st.session_state: st.session_state.token = None
if 'role' not in st.session_state: st.session_state.role = None
if 'photo' not in st.session_state: st.session_state.photo = None
if 'map_center' not in st.session_state: st.session_state.map_center = [15.4909, 73.8278]
if 'map_zoom' not in st.session_state: st.session_state.map_zoom = 10
if 'preview_coords' not in st.session_state: st.session_state.preview_coords = None
if 'deploy_mode' not in st.session_state: st.session_state.deploy_mode = False
if 'ping_target' not in st.session_state: st.session_state.ping_target = None

def do_login(u, p):
    if not u or not p: st.toast("CREDENTIALS REQUIRED"); return
    try:
        res = requests.post(f"{API_URL}/auth/login", json={"username": u, "password": p}, timeout=5)
        if res.status_code == 200:
            d = res.json()
            st.session_state.token, st.session_state.role, st.session_state.username, st.session_state.photo = d['access_token'], d['role'], d['username'], d['profile_photo']
            if "north" in d['username']: st.session_state.map_center = ZONES["NORTH"]["center"]
            elif "south" in d['username']: st.session_state.map_center = ZONES["SOUTH"]["center"]
            st.rerun()
        else: st.error("ACCESS DENIED")
    except: st.error("SERVER UNREACHABLE")

def login_page():
    load_css()
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("""<div style="text-align: center; margin-bottom: 20px;"><div class="login-title">KARTAVYA</div><div class="login-subtitle">Advanced Police Command System</div></div>""", unsafe_allow_html=True)
        t1, t2 = st.tabs(["FIELD UNIT", "COMMAND HQ"])
        with t1:
            with st.form("f1"):
                u = st.text_input("UNIT ID", key="f_u"); p = st.text_input("ACCESS CODE", type="password", key="f_p")
                st.form_submit_button("INITIALIZE LINK", type="primary", on_click=lambda: do_login(st.session_state.f_u, st.session_state.f_p))
        with t2:
            st.caption("AUTHORIZED PERSONNEL ONLY")
            with st.form("f2"):
                u = st.text_input("OFFICER ID", key="h_u"); p = st.text_input("SECURE KEY", type="password", key="h_p")
                st.form_submit_button("AUTHENTICATE", type="primary", on_click=lambda: do_login(st.session_state.h_u, st.session_state.h_p))

def update_loc():
    requests.post(f"{API_URL}/checkin", json={"latitude": st.session_state.lat_in, "longitude": st.session_state.lng_in}, headers={"Authorization": f"Bearer {st.session_state.token}"})

def field_dashboard():
    load_css()
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        res = requests.get(f"{API_URL}/officer/me", headers=headers)
        data = res.json()
        pings = requests.get(f"{API_URL}/pings/active", headers=headers).json()
        logs = requests.get(f"{API_URL}/officer/logs", headers=headers).json()
        all_officers = requests.get(f"{API_URL}/status/all", headers=headers).json()
    except: st.error("NETWORK ERROR"); return

    with st.sidebar:
        st.image(st.session_state.photo, width=120)
        st.markdown(f"**UNIT:** {st.session_state.username.upper()}")
        st.divider()
        st.markdown("#### PING NETWORK")
        if st.toggle("RECEIVE PINGS", value=data['pings_enabled']):
            if not data['pings_enabled']: requests.post(f"{API_URL}/ping/toggle", headers=headers); st.rerun()
        else:
            if data['pings_enabled']: requests.post(f"{API_URL}/ping/toggle", headers=headers); st.rerun()
            
        with st.popover("SEND PING", use_container_width=True):
            avail = [o['username'] for o in all_officers if o['username'] != st.session_state.username and o['status_color'] != 'blue']
            target_opts = ["討 ALL NEARBY UNITS (5KM)"] + avail
            tgt = st.selectbox("TARGET", target_opts)
            msg = st.text_input("MESSAGE")
            if st.button("TRANSMIT"):
                if tgt.startswith("討"): r = requests.post(f"{API_URL}/ping/broadcast", json={"message": msg}, headers=headers)
                else:
                    tid = next(o['id'] for o in all_officers if o['username'] == tgt)
                    r = requests.post(f"{API_URL}/ping/send", json={"receiver_id": tid, "message": msg}, headers=headers)
                if r.status_code == 200: st.success("SENT")
                else: st.error(r.json().get('detail', 'Failed'))

        st.divider()
        st.markdown("#### GPS CONTROL")
        mode = st.radio("SOURCE", ["SIMULATE (SPOOF)", "DEVICE GPS"], horizontal=True)
        
        if 'lat_in' not in st.session_state: st.session_state.lat_in = data['current_lat'] or 15.4909
        if 'lng_in' not in st.session_state: st.session_state.lng_in = data['current_long'] or 73.8278

        if mode == "SIMULATE (SPOOF)":
            st.number_input("LATITUDE", format="%.4f", key="lat_in", on_change=update_loc)
            st.number_input("LONGITUDE", format="%.4f", key="lng_in", on_change=update_loc)
        else:
            if st.button("桃 GET DEVICE LOCATION", use_container_width=True):
                st.session_state.lat_in = 15.4909 # Mock Value
                st.session_state.lng_in = 73.8278
                update_loc(); st.toast("LOCATION UPDATED FROM DEVICE")

        st.divider()
        if st.button("TERMINATE SESSION", type="secondary", use_container_width=True): st.session_state.token = None; st.rerun()

    st.markdown("### FIELD TERMINAL")
    if pings:
        for p in pings:
            st.warning(f"藤 PING FROM {p['sender'].upper()}: {p['message']}")
            if st.button("LOCATE SIGNAL", key=f"p{p['id']}"):
                st.session_state.ping_target = [p['lat'], p['long']]
                requests.post(f"{API_URL}/ping/dismiss/{p['id']}", headers=headers); st.rerun()

    status, color = data['status'], "#1f6feb"
    if status == "safe": color = "#2ea043"
    if status == "risk": color = "#da3633"
    st.markdown(f"<div style='border-left: 4px solid {color}; background: {color}10; padding: 15px; margin-bottom: 20px;'><h3 style='color: {color}; margin: 0;'>{data['message']}</h3></div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns([2, 1])
    with c1:
        center = st.session_state.ping_target if st.session_state.ping_target else [st.session_state.lat_in, st.session_state.lng_in]
        m = folium.Map(location=center, zoom_start=14, tiles="CartoDB dark_matter")
        if data['target_lat']: folium.Circle([data['target_lat'], data['target_long']], radius=data['radius'], color="#1f6feb", weight=1, fill=True, fill_opacity=0.15).add_to(m)
        folium.Marker([st.session_state.lat_in, st.session_state.lng_in], icon=folium.Icon(color="green" if status=="safe" else "red", icon="user")).add_to(m)
        if st.session_state.ping_target: folium.Marker(st.session_state.ping_target, icon=folium.Icon(color="purple", icon="bell", prefix="fa")).add_to(m)
        st_folium(m, height=400)

    with c2:
        st.markdown("**LOGS**")
        with st.container(height=300):
            for log in logs:
                ts = log['timestamp'].replace("T", " ")[:16]
                lvl = log['level']
                c = "#58a6ff" if lvl=="INFO" else "#2ea043" if lvl=="SUCCESS" else "#f85149"
                st.markdown(f"<div class='log-entry'><span class='log-lvl' style='color:{c}'>{lvl}</span> <span style='color:#666'>[{ts}]</span><br>{log['message']}</div>", unsafe_allow_html=True)
        st.markdown("**ACTIONS**")
        if status not in ["on_leave", "req_leave"]:
            if st.button("SUBMIT LEAVE REQ", use_container_width=True):
                requests.post(f"{API_URL}/leave/request", headers=headers); st.rerun()

def supervisor_dashboard():
    load_css()
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    with st.sidebar:
        st.image(st.session_state.photo, width=120)
        st.markdown(f"**CMDR:** {st.session_state.username.upper()}")
        st.divider()
        if st.button("LOGOUT", type="secondary", use_container_width=True): st.session_state.token = None; st.rerun()

    c1, c2 = st.columns([6, 1])
    c1.markdown(f"### KARTAVYA HQ: {st.session_state.username.upper()}")
    try: officers = requests.get(f"{API_URL}/status/all", headers=headers).json(); logs = requests.get(f"{API_URL}/logs", headers=headers).json()
    except: st.error("DATALINK FAILURE"); return

    pending = [o for o in officers if o['leave_requested']]
    if pending:
        st.markdown(f"<div class='notif-box'><span class='notif-title'>笞ｸPENDING AUTHORIZATIONS: {len(pending)}</span></div>", unsafe_allow_html=True)
        for p in pending:
            with st.container():
                cols = st.columns([0.5, 3, 1, 1])
                cols[0].image(p['profile_photo'], width=35)
                cols[1].markdown(f"**{p['username'].upper()}**")
                if cols[2].button("AUTH", key=f"a{p['id']}", type="primary", use_container_width=True):
                    requests.post(f"{API_URL}/leave/approve/{p['id']}", headers=headers); st.rerun()
                if cols[3].button("DENY", key=f"d{p['id']}", type="secondary", use_container_width=True):
                    requests.post(f"{API_URL}/leave/deny/{p['id']}", headers=headers); st.rerun()

    c_map, c_cmd = st.columns([2, 1])
    with c_map:
        st.markdown("**TACTICAL MAP**")
        deploy_mode = st.toggle("ACTIVATE TARGETING SYSTEM", value=st.session_state.deploy_mode)
        
        # --- NEW MAP LEGEND ---
        st.markdown("""
        <div style="display: flex; gap: 8px; margin-bottom: 10px;">
            <span class="status-pill pill-safe">SECURE</span>
            <span class="status-pill pill-risk">ALERT</span>
            <span class="status-pill pill-warn">STANDBY</span>
            <span class="status-pill pill-info">OFF DUTY</span>
        </div>
        """, unsafe_allow_html=True)
        # ----------------------

        st.session_state.deploy_mode = deploy_mode
        m = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom, tiles="CartoDB dark_matter")
        user = st.session_state.username
        if user == "head" or "north" in user: folium.Polygon(ZONES["NORTH"]["bounds"], color="#2979FF", fill=True, fill_opacity=0.05).add_to(m)
        if user == "head" or "south" in user: folium.Polygon(ZONES["SOUTH"]["bounds"], color="#FF6D00", fill=True, fill_opacity=0.05).add_to(m)
        for o in officers:
            if o['current_lat']:
                c = "#2ea043" if o['status_color'] == "green" else "#da3633" if o['status_color'] == "red" else "#d29922" if o['status_color'] == "yellow" else "#1f6feb"
                folium.CircleMarker([o['current_lat'], o['current_long']], radius=4, color="white", weight=1, fill=True, fill_color=c, fill_opacity=1, tooltip=o['username']).add_to(m)
        if st.session_state.preview_coords:
            folium.Circle(st.session_state.preview_coords, radius=500, color="#d29922", dash_array="5,5").add_to(m)
            folium.Marker(st.session_state.preview_coords, icon=folium.Icon(color="orange", icon="crosshairs", prefix="fa")).add_to(m)
        map_data = st_folium(m, height=500)
        if deploy_mode and map_data and map_data.get('last_clicked'):
            lc = map_data['last_clicked']
            role = st.session_state.role
            valid = True
            if "north" in user and lc['lat'] < 15.44: valid = False
            if "south" in user and lc['lat'] >= 15.44: valid = False
            if valid:
                st.session_state.preview_coords = [lc['lat'], lc['lng']]; st.rerun()
            else: st.toast("JURISDICTION LIMIT")

    with c_cmd:
        st.markdown("**UNIT COMMAND**")
        sel = st.selectbox("IDENTIFIER", ["SELECT TARGET..."] + [o['username'] for o in officers], label_visibility="collapsed")
        if sel != "SELECT TARGET...":
            unit = next(o for o in officers if o['username'] == sel)
            st.image(unit['profile_photo'], width=50)
            pill, txt = "pill-info", "UNKNOWN"
            if unit['status_color'] == "green": pill, txt = "pill-safe", "SECURE"
            if unit['status_color'] == "red": pill, txt = "pill-risk", "ALERT"
            if unit['status_color'] == "yellow": pill, txt = "pill-warn", "STANDBY"
            if unit['status_color'] == "blue": pill, txt = "pill-info", "OFF DUTY"
            st.markdown(f"<span class='status-pill {pill}'>{txt}</span>", unsafe_allow_html=True)
            st.write("")
            c1, c2 = st.columns(2)
            if unit['current_lat'] and c1.button("LOCATE", use_container_width=True):
                st.session_state.map_center, st.session_state.map_zoom = [unit['current_lat'], unit['current_long']], 15; st.rerun()
            with st.popover("PING UNIT", use_container_width=True):
                msg = st.text_input("MSG"); 
                if st.button("SEND"): requests.post(f"{API_URL}/ping/send", json={"receiver_id": unit['id'], "message": msg}, headers=headers); st.toast("PING SENT")
            if unit['status_color'] in ["green", "red"] and st.button("END PATROL", type="primary", use_container_width=True):
                requests.post(f"{API_URL}/deploy/stop/{unit['id']}", headers=headers); st.rerun()
            if unit['status_color'] != "blue" and st.button("GRANT LEAVE", type="secondary", use_container_width=True):
                requests.post(f"{API_URL}/leave/grant/{unit['id']}", headers=headers); st.rerun()
            if unit['status_color'] == "blue" and st.button("RECALL", type="primary", use_container_width=True):
                requests.post(f"{API_URL}/leave/revoke/{unit['id']}", headers=headers); st.rerun()

        st.divider()
        st.markdown("**DEPLOYMENT**")
        if st.session_state.preview_coords:
            st.caption(f"TARGET: {st.session_state.preview_coords}")
            assign = st.multiselect("ASSIGN UNITS", [o['username'] for o in officers if o['status_color'] == 'yellow' and not o['leave_requested']])
            rad = st.slider("RADIUS (M)", 100, 2000, 500)
            if st.button("EXECUTE", type="primary", use_container_width=True):
                ids = [o['id'] for o in officers if o['username'] in assign]
                if ids:
                    requests.post(f"{API_URL}/deploy/bulk", json={"officer_ids":ids, "latitude":st.session_state.preview_coords[0], "longitude":st.session_state.preview_coords[1], "radius":rad}, headers=headers)
                    st.session_state.map_center, st.session_state.map_zoom, st.session_state.preview_coords = st.session_state.preview_coords, 14, None; st.rerun()
                else: st.warning("SELECT UNITS")
            if st.button("CANCEL"): st.session_state.preview_coords = None; st.rerun()
        else: st.info("SELECT MAP LOCATION" if deploy_mode else "ACTIVATE TARGETING FIRST")

    st.markdown("---")
    st.markdown("**MISSION LOGS**")
    with st.container(height=150):
        for log in logs:
            ts = log['timestamp'].replace("T", " ")[:16]
            lvl = log['level']
            c = "#58a6ff" if lvl=="INFO" else "#2ea043" if lvl=="SUCCESS" else "#f85149"
            st.markdown(f"<div class='log-entry'><span class='log-lvl' style='color:{c}'>{lvl}</span> <span style='color:#666'>[{ts}]</span> {log['message']}</div>", unsafe_allow_html=True)

def main():
    if not st.session_state.token: login_page()
    elif st.session_state.role == "field_officer": field_dashboard()
    else: supervisor_dashboard()

if __name__ == "__main__": main()