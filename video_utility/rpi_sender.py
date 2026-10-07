import subprocess
import signal
import sys
import time
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
with open(REPO_ROOT / "config" / "robot_params.yaml", "r") as file:
    config = yaml.safe_load(file)

STREAM_PORT = config['configuration']['STREAM_PORT']
STREAM_TARGET = config['configuration']['STREAM_TARGET']

cmd = (f"rpicam-vid -t 0 --width 640 --height 480 --framerate 30 --codec h264 --inline -o - | "
       f"gst-launch-1.0 fdsrc ! h264parse ! rtph264pay config-interval=1 pt=96 ! "
       f"udpsink host={STREAM_TARGET} port={STREAM_PORT} sync=false")

print(f"videostream port: {STREAM_PORT}")
print(f"videostream target: {STREAM_TARGET}")
print(f"rpi_stream started at: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

process = subprocess.Popen(cmd, shell=True)   # вывод идёт в journalctl

def stop(sig, frame):
    print("Stopping stream...", flush=True)
    process.terminate()
    process.wait()
    sys.exit(0)

signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)   # systemctl stop шлёт SIGTERM

sys.exit(process.wait())