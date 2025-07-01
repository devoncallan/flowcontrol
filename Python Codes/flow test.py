import serial
import time

# from flow import R2

class R2Interface:
    def __init__(self, serial_port):
        self.connection =  serial.Serial(port = serial_port, baudrate=19200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
            stopbits=1, xonxoff=1, timeout=2)

    def Start(self):
        msg = "PN"
        self.send_command(msg)
    
    def stop_experiment(self):
        msg = "PF"
        self.send_command(msg)
        time.sleep(1)
        # self.connection.close()

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
        # time.sleep(1)

    def send_command(self,command):
        command = command + "\r"
        command_bytes = command.encode('ascii')
        self.connection.write(command_bytes)

        response = self.connection.readline()
        # print(command, response)
        return response

    def initiate_comms271(self):
        #commands require spaces (not underscores as shown in serial command guide X.X)
        msgs = ["TB h", "TG i 20 $", "TG b 20 H"]
        for msg in msgs:
            self.send_command(msg)
            time.sleep(2)
            print(R2.connection.readline().decode('ascii')) 

import numpy as np
import datetime
def flow_rate_ramp(r2: R2Interface, F0_mL_per_min, F1_mL_per_min):

    r2.switch_valve(1)

    ramp_time_min = 10
    increment_time_s = 15
    increment_time_min = increment_time_s / 60
    num_increments = int(ramp_time_min / increment_time_min) + 1
    time_steps = np.linspace(0, ramp_time_min, num=num_increments)
    print(time_steps)
    flow_rates = F0_mL_per_min + (F1_mL_per_min - F0_mL_per_min) * (time_steps / ramp_time_min)
    print(flow_rates)


    r2.SetFlowRate(int(flow_rates[0]*1000), 0)
    time.sleep(60)
    r2.switch_valve(1)
    # return

    for i, flow_rate in enumerate(flow_rates):
        time_step = time_steps[i]
        print(f'{datetime.datetime.now()}: {i} {time_step} {flow_rate}')
        r2.SetFlowRate(int(flow_rate*1000), 0)
        time.sleep(increment_time_s)

    r2.switch_valve(0)

def simple_flow_sweep(r2: R2Interface, F0_mL_per_min, F1_mL_per_min, pickup_vol_mL=4, reactor_vol_mL=2):

    r2.switch_valve(1)
    r2.switch_valve(3)
    
    r2.SetFlowRate(F0_mL_per_min * 1000, 0)
    r2.SetFlowRate(F0_mL_per_min * 1000, 1)
    min_res_time_min = reactor_vol_mL / F0_mL_per_min
    print(f'Min residence time: {min_res_time_min} min')

    pickup_time_min = pickup_vol_mL / F0_mL_per_min
    pickup_time_s = pickup_time_min * 60
    print(f'Waiting for {pickup_time_min} min.')
    time.sleep(pickup_time_s)

    r2.SetFlowRate(F1_mL_per_min * 1000, 0)
    r2.SetFlowRate(F1_mL_per_min * 1000, 1)
    max_res_time_min = reactor_vol_mL / F1_mL_per_min
    print(f'Max residence time: {max_res_time_min} min')

    r2.switch_valve(0)
    r2.switch_valve(2)

def set_temperature(r4: R2Interface, temperature):

    r4.stop_experiment()
    r4.Start()
    r4.set_temp(3, temperature)

if __name__ == "__main__":

    R4 = R2Interface('COM4')
    R2S = R2Interface('COM5')
    R2S.stop_experiment()
    R2S.Start()

    set_temperature(R4, 50)
    # R4.Start()
    # time.sleep(1)
    # R4.set_temp(3, 50)

    # R2S.switch_valve(1)
    # time.sleep(1)
    # print(R2S.send_command('GA'))

    R2S.switch_valve(0)
    R2S.switch_valve(2)

    set_flowrate_uL_min = 1000
    R2S.SetFlowRate(set_flowrate_uL_min, 0)
    R2S.SetFlowRate(set_flowrate_uL_min, 1)
    # time.sleep(20)

    simple_flow_sweep(R2S, F0_mL_per_min=1, F1_mL_per_min=0.1, pickup_vol_mL=0.5, reactor_vol_mL=2)
    # simple_flow_sweep_p2(R2S, F1_mL_per_min=0.1, reactor_vol_mL=2)

    # flow_rate_ramp(R2S, F0_mL_per_min=1.0, F1_mL_per_min=0.1)

    # R2S.SetFlowRate(500, 0)
    # R2S.SetFlowRate(500,1)

    quit()
    R2S.switch_valve(0)
    R2S.switch_valve(2)

    

    # print('Stop exp.')
    R2S.stop_experiment()
    R2S.Start()


    R2S.SetFlowRate(0, 1)
    R2S.SetFlowRate(0, 0)


    R2S.SetFlowRate(100, 0)
    R2S.SetFlowRate(100, 1)
    # time.sleep(10)
    # time.sleep(5)
    quit()
    print('Start exp.')
    R2S.Start()
    time.sleep(2)
    # R2S.send_command('AB 0 1000')
    # time.sleep(2)
    # R2S.send_command('CB 0')
    # R2S.Start()
    print('Set flow.')
    # R2S.SetFlowRate(100, 1)
    R2S.SetFlowRate(100, 0)
    R2S.SetFlowRate(150, 1)
    time.sleep(5)
    R2S.send_command('GA')
    flows = [100, 200, 300]
    for flow in flows:
        R2S.SetFlowRate(flow, 0)
        R2S.SetFlowRate(flow+50, 1)
        time.sleep(5)

    R2S.SetFlowRate(0, 0)
    R2S.SetFlowRate(0, 1)
    print('Stop.')
    # R2S.stop_experiment()
    # R2 = R2Interface('COM5')

    # R2.switch_valve(1)
    # R2.switch_valve(3)

   
    # R2.initiate_comms271()

    
    # for i in range(9):
    #     R2.switch_valve(i)
    #     time.sleep(3)
    
    # OFF = -1000
    # R2.set_temp(3,30)
    # while(True):
    #     time.sleep(1)
   
    # time.sleep(1)
    # print(R2.connection.readline().decode('ascii'))
   
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