import sys
import os
import socket
import time

HOST= "169.231.86.125"
PORT= 13000

print('Connect to' + HOST + ':' +str(PORT))
s= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

message  = " <Message>\r\n"
message += " <Start protocol='1D PROTON'>\r\n"
message += " <Option name='Scan' value='QuickScan'/>\r\n"
message += " </Start>\r\n"
message += " </Message>\r\n"

print('\r\nSend message:')
print(message)
s.send(message.encode())

print('\r\nMessage received:')
s.settimeout(10.0)
try:
    while True:
        time.sleep(0.2)
        chunk = s.recv(8192)
        if chunk:
            print(chunk.decode())

except socket.error as msg:
    s.settimeout(None)