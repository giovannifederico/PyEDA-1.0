# PyEDA v. 1.0.1 [05.18.18]
# A (very) simple tool to manage EDA experiments in Python.
#
# Giovanni dr. Federico
# http://www.giovannifederico.net
# research@giovannifederico.net
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.

import socket, threading, serial, time, csv, datetime

class PyEDA:

    def __init__(self, subject, bind_ip = '0.0.0.0', bind_port = 15000, device = '/dev/cu.wchusbserial14140', baudrate = 19200, data_dir = ''):
        self.bind_ip = bind_ip
        self.bind_port = bind_port
        self.device = device
        self.baudrate = baudrate
        self.subject = subject
        self.csv_file = str(subject) + ".csv"
        self.csv_fp = open(data_dir + self.csv_file, 'w')
        self.csv_writer = csv.writer(self.csv_fp)
        self.start_time = int(round(time.time() * 1000))
        self.status = "RUNNING"

    def Server(self):
        eda_recording = threading.Thread(name = 'EDA_RECORDING', target = self.read_sensor)
        tcp_srv = threading.Thread(name = 'TCP_SERVER', target = self.tcp_server)
        tcp_srv.start()
        if(tcp_srv.is_alive()):
            eda_recording.start()
            if(eda_recording.is_alive()):
                print("[!] PyEDA has been started!")

    def time_passed(self):
        return (int(round(time.time() * 1000)) - self.start_time)

    def __eda_sensor_connection(self):
        """Serial connection to the EDA sensor"""
        eda_sensor = serial.Serial(self.device, self.baudrate)
        return eda_sensor

    def read_sensor(self):
        ser = self.__eda_sensor_connection()
        while self.status == "RUNNING":
            eda_value = int(ser.readline())
            # print(str(self.time_passed()) + " " + str(eda_value))
            self.csv_writer.writerow((self.time_passed(), eda_value))
            self.csv_fp.flush()
        ser.close()
        return True

    def tcp_server(self):
        """Start TCP server for incoming triggers (defaults: localhost on port 15000)"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.bind_ip, self.bind_port))
        server.listen(1)
        print('[-] Listening for triggers on {}:{}'.format(self.bind_ip, self.bind_port))
        while self.status == "RUNNING":
            client_socket, address = server.accept()
            request = str(client_socket.recv(1024), 'utf-8')
            trigger = "TRIGGER: " + request
            self.csv_writer.writerow((self.time_passed(), trigger))
            self.csv_fp.flush()
            client_socket.send(b'OK')
            client_socket.close()
            print("[i] Trigger received (" + str(datetime.datetime.now()) + "): " + str(request))
            if (trigger == "TRIGGER: STOP"):
               self.status = "STOP"
        return True

    def SendTrigger(trigger, server_ip = '0.0.0.0', server_port = 15000):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((server_ip, server_port))
        client.send(str.encode(trigger))
        response = client.recv(1024)
        if(str(response, 'utf-8') == "OK"):
            print("[i] Trigger sent to the PyEDA Server!")