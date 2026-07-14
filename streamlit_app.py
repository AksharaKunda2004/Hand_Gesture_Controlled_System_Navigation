import streamlit as st
import requests
import time

API = "http://127.0.0.1:8000"

st.title("🤖 Hand Gesture Controlled System Navigation")

if st.button("Start Gesture Recognizer"):
    try:
        r = requests.get(f"{API}/start")
        st.success("Gesture Recognizer Started")
    except:
        st.error("Failed to start recognizer")

if st.button("Stop Gesture Recognizer"):
    try:
        r = requests.get(f"{API}/stop")
        st.warning("Gesture Recognizer Stopped")
    except:
        st.error("Failed to stop recognizer")

# Auto-status refresh
st.subheader("Recognizer Status:")
status_placeholder = st.empty()

while True:
    try:
        r = requests.get(f"{API}/status").json()
        if r["running"]:
            status_placeholder.success("🟢 Running")
        else:
            status_placeholder.error("🔴 Not Running")
    except:
        status_placeholder.error("🔴 Server Offline")

    time.sleep(1)
