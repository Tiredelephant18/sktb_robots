import subprocess 
import datetime 
import yaml


with open('/home/liza/Desktop/SKTB/rover/rtc_robotics/config/robot_params.yaml', 'r') as file:
    config = yaml.safe_load(file)


date = "date" 
date_output = subprocess.check_output(date) 
 
print("Video_started at: ", date_output.decode("utf-8")) 
 
command_fast = f"gst-launch-1.0 -v udpsrc port={config['configuration']['STREAM_PORT']} ! \
    'application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96' ! \
    rtph264depay ! h264parse ! decodebin ! videoconvert ! autovideosink sync=false"
subprocess.run(command_fast, shell=True, stdin=subprocess.PIPE)

now = datetime.datetime.now() 
formatted_time = now.strftime("%Y-%m-%d %H:%M:%S") 
print("rpi_stream started at: ", formatted_time)
