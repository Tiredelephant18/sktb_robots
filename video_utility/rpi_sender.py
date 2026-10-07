import subprocess
import datetime
import yaml
import signal
import os


with open('/home/student/rtc_robotics/config/robot_params.yaml', 'r') as file:
    config = yaml.safe_load(file)

def kill_process_by_name(process_name):
  output = subprocess.check_output(["ps", "aux"])
  lines = output.decode().splitlines()
  for line in lines:
    if process_name in line:
      pid = int(line.split()[1])
      try:
        os.kill(pid, signal.SIGKILL)
        print(f"Procces {process_name} (PID: {pid}) has stopped")
      except ProcessLookupError:
        print(f"Process {process_name} (PID: {pid}) has not found")

kill_process_by_name("video")
now = datetime.datetime.now()
formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")

command_fast = f"gst-launch-1.0 -v v4l2src device=/dev/video0 ! videoconvert ! videoscale ! video/x-raw,width=640,height=480,framerate=30/1 ! \
    x264enc tune=zerolatency bitrate=16000000 speed-preset=superfast ! h264parse ! rtph264pay pt=96 ! \
    udpsink port={config['configuration']['STREAM_PORT']} host={config['configuration']['STREAM_TARGET']}"

process = subprocess.Popen(command_fast.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print("viseostream port: ", config['configuration']['STREAM_PORT'])
print("videostream target: ", config['configuration']['STREAM_TARGET'])
print("rpi_stream started at: ", formatted_time)

output, error = process.communicate()
print(f"stdout: {output.decode('utf-8')}")
print(f"stderr: {error.decode('utf-8')}")

if process.returncode == 0:
    print("Pipeline completed")
else:
    print(f"Error: {process.returncode}")
