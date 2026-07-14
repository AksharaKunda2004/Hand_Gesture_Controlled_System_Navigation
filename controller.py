import pyautogui
import ctypes
import subprocess
import os
import time

# =============================
# WINDOWS VOLUME CONTROL
# =============================

# Using Windows keybd_event to control volume
VK_VOLUME_UP = 0xAF
VK_VOLUME_DOWN = 0xAE

def volume_up():
    ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
    time.sleep(0.05)

def volume_down():
    ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
    time.sleep(0.05)

# =============================
# SYSTEM ACTIONS
# =============================

def do_click():
    pyautogui.click()

def next_slide():
    pyautogui.press("right")

def prev_slide():
    pyautogui.press("left")

def zoom_in():
    pyautogui.hotkey("ctrl", "+")  # Chrome, PDF, PowerPoint
    time.sleep(0.1)

def zoom_out():
    pyautogui.hotkey("ctrl", "-")
    time.sleep(0.1)

# =============================
# OPEN SPOTIFY APP
# =============================

def open_spotify():
    spotify_path = r"C:\Users\hp\AppData\Local\Microsoft\WindowsApps\Spotify.exe"
    if os.path.exists(spotify_path):
        subprocess.Popen([spotify_path], shell=True)
    else:
        print("Spotify.exe not found at:", spotify_path)
