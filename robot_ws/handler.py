import socket
import threading
import struct
import smbus
import subprocess
import sys
import os
import numpy as np
from time import sleep
import math
import yaml
from disp import display
from h39 import rmotor, lightBulb
from event import ServoEvent
from datetime import datetime


# Open the YAML file in the parent directory
with open('/home/student/sktb_robots/config/robot_params.yaml', 'r') as file:
    config = yaml.safe_load(file)

class ClientThread(threading.Thread):
	def __init__(self, ip, port, debug = False):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.ip = ip
		self.port = port
		self.r_data = [0, 0, 0, 0, 0,
			       0, 0, 0, 0, 0,
			       0, 0, 0, 0, 0,
			       0, 0, 0, 0, 0,
			       0, 0, 0, 0]
		self._defaultpackage = 48
		self.debug = debug
		self.m_speed = 95
		self.k_turn = 0.4
		self.boost = 1
		self.dstate = 1
		self.sstate = 1
		self.mstate = 1
		self.lstate = 1
		self.setupDisplay()
		self.setupLamp()
		self.setupMotors()
		self.setupServo()
		print("Setup complete")
		print("[+] New server started from:", ip + " " + str(port))
		self.display.show_params(["Display:  ", "Bulb:  ", "Motors:  ", "Servo:  "], 
			[
				config['configuration']['state'][1] if self.dstate else config['configuration']['state'][0],
				config['configuration']['state'][1] if self.lstate else config['configuration']['state'][0],
				config['configuration']['state'][1] if self.mstate else config['configuration']['state'][0],
				config['configuration']['state'][1] if self.sstate else config['configuration']['state'][0]]
		)
		sleep(3)
		self.display.show_image()
		if (self.sstate == 1 and self.mstate == 1 and self.lstate == 1 and self.dstate == 1):
			print("Rover is ready")



	def setupConnection(self):
		try:
			print("Waiting for connection")
			self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.socket.bind((config['configuration']['HOST'], config['configuration']['PORT']))
			self.socket.listen(5)
			self.clientsocket, self.address = self.socket.accept()
			print(f"Connected from pult at {self.address} has been established!")
		except Exception as e:
			raise ConnectionError(f"Failed to connect to {self.address}", str(e))

	def closeConnection(self):
		self.display.show_params(["ip", "connection closed", "", ""], [f"{self.address}", "", "", ""])
		self.socket.close()
		print(f"Closing connection to {self.address}")

	def reciever(self):
		_exit = 1
		count = 0
		while _exit != 0:
			try:
				data = self.clientsocket.recv(self._defaultpackage)
				if (self.debug):
					print("Size of recieving data", len(data))

				if (len(data) < 24):
					count = count + 1

				if (len(data) == 24):
					self.r_data = np.frombuffer(data, dtype=np.uint8)
					if ((np.sum(self.r_data) - self.r_data[23]) % 2) != self.r_data[23]:
						#print(self.r_data)
						count = count + 1
					count = 0
				else:
					print("Recieved data is corrupted")
					self.motor.motor_stop()
					self.lamp.lampOff()
					self.r_data = [0, 0, 0, 0, 0,
						       0, 0, 0, 0, 0,
  						       0, 0, 0, 0, 0,
						       0, 0, 0, 0, 0,
						       0, 0, 0, 0]

				if count > 10:
					self.motor.motor_stop()
					_exit = 0
					self.closeConnection()
				sleep(config['configuration']['timings']['pulsebeat'])

			except:
				self.motor.motor_stop()
				_exit = 0
				self.closeConnection()

	def run(self):
		thread1=threading.Thread(target=self.reciever, daemon=False)
		thread1.start()
		thread2=threading.Thread(target=self.machinist, daemon=True)
		thread2.start()
		thread3=threading.Thread(target=self.servorer, daemon=True)
		thread3.start()
		thread4=threading.Thread(target=self.utiliter, daemon=True)
		thread4.start()

	def utiliter(self):
		while True:
			sleep(config['configuration']['timings']['pulsebeat'])
			if self.r_data[config['configuration']['keyboard']['x']] == 1:
				if self.boost <= 0.95:
					self.boost = self.boost + 0.05
					self.display.show_params(["speed", "", "", ""], [round(self.boost, 2), "", "", ""])
					print("current speed", round(self.boost, 2))
				self.motor.motor_speed_dercrese(self.m_speed, self.boost)
				sleep(config['configuration']['timings']['time_delay_seconds'])
			if self.r_data[config['configuration']['keyboard']['z']] == 1:
				if self.boost > 0.3:
					self.boost = self.boost - 0.05
					self.display.show_params(["speed", "", "", ""], [round(self.boost, 2), "", "", ""])
					print("z", round(self.boost, 2))
				self.motor.motor_speed_increase(self.m_speed, self.boost)
				sleep(config['configuration']['timings']['time_delay_seconds'])

			if self.r_data[config['configuration']['keyboard']['v']] == 1:
				self.lamp.lampOn()
				sleep(config['configuration']['timings']['time_delay_seconds'])

			if self.r_data[config['configuration']['keyboard']['b']] == 1:
				self.lamp.lampOff()
				sleep(config['configuration']['timings']['time_delay_seconds'])

			if (self.r_data[config['configuration']['keyboard']["1"]] == 1) and  (self.r_data[config['configuration']['keyboard']['z']] == 1) and  (self.r_data[config['configuration']['keyboard']['p']] == 1):
				self.closeConnection()
				self.display.show_params(["shutdown", "", "", ""], ["......", "......", "...", ""])
				os.system("shutdown now")


	def servorer(self):
		while True:
			sleep(config['configuration']['timings']['pulsebeat'])
			if self.sstate == 1:
				try:
					if self.r_data[config['configuration']['keyboard']['r']] == 1:
						self.serv.calibrationR()
						sleep(config['configuration']['timings']['time_delay_seconds'])

					if self.r_data[config['configuration']['keyboard']['t']] == 1:
						self.serv.calibrationE()
						sleep(config['configuration']['timings']['time_delay_seconds'])

					if self.r_data[config['configuration']['keyboard']["1"]] == 1:
						self.serv.decreaseCamAngle(1)
					if self.r_data[config['configuration']['keyboard']["2"]] == 1:
						self.serv.increaseCamAngle(1)

					if self.r_data[config['configuration']['keyboard']['q']] == 1:
						self.serv.decreaseWheelAngle(5)
					if self.r_data[config['configuration']['keyboard']['e']] == 1:
						self.serv.increaseWheelAngle(5)

					if self.r_data[config['configuration']['keyboard']['u']] == 1:
						self.serv.increaseManAngle(config['configuration']['servoName']["man1"], 2)
					if self.r_data[config['configuration']['keyboard']['h']] == 1:
						self.serv.decreaseManAngle(config['configuration']['servoName']["man1"], 2)

					if self.r_data[config['configuration']['keyboard']['i']] == 1:
						self.serv.increaseManAngle(config['configuration']['servoName']["man2"], 2)
					if self.r_data[config['configuration']['keyboard']['j']] == 1:
						self.serv.decreaseManAngle(config['configuration']['servoName']["man2"], 2)

					if self.r_data[config['configuration']['keyboard']['o']] == 1:
						self.serv.increaseManAngle(config['configuration']['servoName']["man3"], 3)
					if self.r_data[config['configuration']['keyboard']['k']] == 1:
						self.serv.decreaseManAngle(config['configuration']['servoName']["man3"], 3)

					if self.r_data[config['configuration']['keyboard']['p']] == 1:
						self.serv.increaseManAngle(config['configuration']['servoName']["man4"], 4)
					if self.r_data[config['configuration']['keyboard']['l']] == 1:
						self.serv.decreaseManAngle(config['configuration']['servoName']["man4"], 4)

				except AttributeError:
					pass

	def machinist(self):
		while True:
			sleep(config['configuration']['timings']['pulsebeat'])
			if self.mstate == 1:
				try:
					if self.r_data[config['configuration']['keyboard']['w']] == 1:
						self.motor.rotate_clockwise()
					elif self.r_data[config['configuration']['keyboard']['s']] == 1:
						self.motor.rotate_counterwise()
					elif self.r_data[config['configuration']['keyboard']['d']] == 1:
						self.motor.turn_right()
					elif self.r_data[config['configuration']['keyboard']['a']] == 1:
						self.motor.turn_left()
					else:
						self.motor.motor_stop()
				except AttributeError:
					pass

	def setupDisplay(self):
		try:
			self.display = display.Display()
			print("display: OK")

		except:
			self.dstate = 0
			print("display: error 0x3c")

	def setupLamp(self):
		try:
			self.lamp = lightBulb()
			self.lamp.setup()
			print("lamp: OK")
		except:
			self.lstate = 0
			self.lamp.destruct()
			print("lamp: error")

	def setupMotors(self):
		try:
			self.motor = rmotor()
			self.motor.modify_pwm1(rmotor.pwm_signal, 100, 1000)
			self.motor.modify_pwm2(rmotor.pwm_signal1, 100, 1000)
			print("motor: OK")
		except:
			self.mstate = 0
			print("motor: error")

	def setupServo(self):
		try:
			self.serv = ServoEvent()
			print("servo: OK")
		except:
			self.sstate = 0
			print("servo: error 0x40")

if __name__ == "__main__":
	try:
		print("Waiting for connection")
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind((config['HOST'], config['PORT']))
		s.listen(5)
		clientsocket, address = s.accept()
		print("Connected from {address} has been refused!")
	except Exception as e:
		raise ConnectionError(f"Failed to connect to {address}", str(e))

	newconnection = ClientThread(config['HOST'], config['PORT'])
	newconnection.run()

	while True:
		try:
			sleep(10)
		except KeyboardInterrupt:
			s.close()
			break
