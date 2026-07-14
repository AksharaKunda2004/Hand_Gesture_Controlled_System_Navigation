import subprocess
import time

# Start FastAPI server
subprocess.Popen(["uvicorn", "api:app", "--reload"])

time.sleep(2)

# Start Streamlit UI
subprocess.Popen(["streamlit", "run", "streamlit_app.py"])
