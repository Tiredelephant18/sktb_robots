import sys
import yaml
from time import sleep
from handler import ClientThread


# Open the YAML file in the parent directory
with open('/home/student/rtc_robotics/config/robot_params.yaml', 'r') as file:
    config = yaml.safe_load(file)

if __name__ == "__main__":
	robot = ClientThread(config['configuration']['HOST'], config['configuration']['PORT'])
	robot.setupConnection()
	robot.run()
	counter = 0
	while counter < 2:
		try:
			sleep(1)
			counter = counter + 1
		except KeyboardInterrupt:
			robot.closeConnection()
			break
