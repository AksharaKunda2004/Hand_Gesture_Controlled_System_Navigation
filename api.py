from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import signal

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

recognizer_process = None

@app.get("/start")
def start_recognizer():
    global recognizer_process

    if recognizer_process is not None:
        return {"status": "already_running"}

    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200

    recognizer_process = subprocess.Popen(
        ["python", "gesture_recognizer.py"],
        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        shell=False
    )

    return {"status": "started"}

@app.get("/stop")
def stop_recognizer():
    global recognizer_process

    if recognizer_process is None:
        return {"status": "not_running"}

    try:
        recognizer_process.send_signal(signal.CTRL_BREAK_EVENT)
    except:
        try:
            recognizer_process.kill()
        except:
            pass

    recognizer_process = None
    return {"status": "stopped"}

@app.get("/status")
def status():
    global recognizer_process

    if recognizer_process is None:
        return {"running": False}

    if recognizer_process.poll() is not None:
        recognizer_process = None
        return {"running": False}

    return {"running": True}
