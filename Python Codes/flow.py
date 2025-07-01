import serial
import time

class R2Interface:
    def __init__(self, serial_port):
        self.connection =  serial.Serial(port = serial_port, baudrate=19200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
            stopbits=1, xonxoff=1, timeout=2)
        print(self.connection)

    def Start(self):
        msg = "PN"
        self.send_command(msg)
    
    def stop_experiment(self):
        msg = "PF"
        self.send_command(msg)
        time.sleep(5)
        self.connection.close()

    def switch_valve(self, valve):
        msg = "KP " + str(valve)
        self.send_command(msg)
        
        '''
        0 and 1 = first valve (R/S, A pump), 2 and 3 = second valve (R/S, B pump), 4 and 5 = third (top inj.), 
        6 and 7 = fourth (bot. inj.), 8 and 9 = fifth (waste/collection)
        '''

    def set_temp(self, channel, temp, ramp_rate = ""):
        msg = "R4 ST " + str(channel) + " " + str(temp)
        print(msg)
        self.send_command(msg)

    def SetFlowRate(self, flow_rate, ID):
        msg = "FR " + str(ID) + " " + str(flow_rate)
        self.send_command(msg)

    def send_command(self,command):
        command = command + "\r"
        command_bytes = command.encode('ascii')
        self.connection.write(command_bytes)

    def initiate_comms271(self):
        #commands require spaces (not underscores as shown in serial command guide X.X)
        msgs = ["TB h", "TG i 20 $", "TG b 20 H"]
        for msg in msgs:
            self.send_command(msg)
            time.sleep(2)
            print(self.connection.readline().decode('ascii')) 


if __name__ == "__main__":
    R2 = R2Interface('COM5')
   
    R2.initiate_comms271()

    # R2.Start()
    print('hello')
    R2.switch_valve(2)
    
    # R2.set_temp(2,50)
   
    time.sleep(1)
    print(R2.connection.readline().decode('ascii'))
   
    # R2.Start()
    # time.sleep(1)

    # print(R2.connection.readline().decode('ascii'))

    #R2.stop_experiment()

    '''
    print(R2.connection.readline().decode('ascii'))
    

    
    time.sleep(300)
    R2.set_temp(3,20,80)
    time.sleep(1)
    print(R2.connection.readline().decode('ascii'))
    time.sleep(300)
    '''

#Currently hangs on error. Need to deal with when "ERROR" is received. 
#Actually may not hang but instead progressed to next wait step.
#Reactor positions 2 and 4 can heat, positions 1, 3 and 4 can cool.

#Use 'COM 5' for controlling R2S pumps and its respective valve positions