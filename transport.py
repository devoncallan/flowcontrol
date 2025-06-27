"""
Class for creating objects to communicate over a serial connection.
Messages are sent with a terminating sequence, and then the response
is read until the terminating sequence is recieved."""

import serial

class serial (object):
    ser = None
    _terminator = None
    _terminator_len = 0
    
    def __init__ (self, port):
        
        # self.ser = serial.Serial()
        # self.ser.port = port
        # self.ser.baudrate = 19200
        # self.ser.timeout = 1
        
        
        self.connection = serial.Serial(
            port = port,
            baudrate = 19200,
            bytesize = serial.EIGHTBITS,
            parity = serial.PARITY_NONE,
            stopbits = 1,
            xonxoff = 1,
            timeout = 2
        )
        
    def setTerminator(self, terminator):
        self._terminator = terminator
        self._terminator_len = len(terminator)
        
    def open(self):
        self.connection.open()
        
    def close(self):
        self.connection.close()
        
    def send(self, line):
        buff = ""
        self.socket.send(line + self._terminator)
        while len(buff) < self._terminator_len or buff[-self._terminator_len:] != self._terminator:
            buff = buff + self.connection.read()
            return buff[:-self._terminator_len]
