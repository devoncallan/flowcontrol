import serial
import time
from enum import Enum

class RunStateFlag(Enum):
    OFF = 0
    RUNNING = 1
    SYSTEM_OVERPRESSURE = 2
    PUMP_A_OVERPRESSURE = 3
    PUMP_B_OVERPRESSURE = 4
    UNDERPRESSURE = 5
    PUMP_A_UNDERPRESSURE = 6
    PUMP_B_UNDERPRESSURE = 7

class SystemStatus:
    def __init__(self, response):
        """Response should be of format:
        1: Run State Flag: 
            0 - off, 
            1 - running, 
            2 - system overpressure, 
            3 - Pump A overpressure, 
            4 - Pump B overpressure, 
            5 - underpressure (leak), 
            6 - Pump A underpressure, 
            7 - Pump B underpressure
        2 & 3: Pump A and B Flow Rate (uL/min)
        4 & 5: Airlock numbers
        6: Pressure limit mbar
        6: Front panel LEDs bitmap
        8-11: Temperature set points.
        Example:
            0,200,400,0,0,101010010111001010,20,45,60,20
        """
    
        self.valid = True
        try:
            parts = response.split(',')
            self.run_state_flag = RunStateFlag(int(parts[0]))
            self.pump_a_flow_rate = float(parts[1])
            self.pump_b_flow_rate = float(parts[2])
            self.airlock_numbers = (int(parts[3]), int(parts[4]))
            self.pressure_limit = int(parts[5])
            self.front_panel_leds = parts[6]
            self.temperature_set_points = [int(temp) for temp in parts[7:11]]
        except (IndexError, ValueError, TypeError) as e:
            self.valid = False
            self.error = f"Failed to parse response: {e}"

    def is_valid(self):
        return self.valid

    def __str__(self):
        if not self.valid:
            return f"Invalid System Status: {self.error}"
        return f"System Status: Run State={self.run_state_flag}, Pump A Rate={self.pump_a_flow_rate} uL/min, Pump B Rate={self.pump_b_flow_rate} uL/min"

class R2Interface:
    
    def __init__(self, module="R2S"):
        
        serial_port = None
        if module == "R2S":
            serial_port = "COM5"
        elif module == "R2":
            serial_port = "COM4"
        else:
            raise ValueError("Invalid module. Please choose either 'R2' or 'R2S'")
        
        self.connection = serial.Serial(
            port = serial_port,
            baudrate = 19200,
            bytesize = serial.EIGHTBITS,
            parity = serial.PARITY_NONE,
            stopbits = 1,
            xonxoff = 1,
            timeout = 2
        )
        
    def _send(self, command):
        """Sends a command and waits for the response."""
        command += "\r"
        command_bytes = command.encode('ascii')
        self.connection.write(command_bytes)
        
        # Wait for a response
        response = self.connection.readline()
        
        return response.decode('ascii').strip()
        
    def start(self):
        """Powers on pumps and heaters.
        Starts the pumps at their set flow rate and powers on the heaters of the connected R4.
        This command will start all pumps. If only one pump is required, its flow rate should be set to zero."""
        return self._send("PN")
    
    def stop(self):
        """Powers off pumps and heaters.
        Stops the pumps and powers off the heaters of the connected R4.
        This command will stop all pumps. If you only wish to stop a single pump, set its flow rate to zero."""
        return self._send("PF")
    
    def set_flowrate(self, pump_id, flow_rate):
        """Sets the flow rate of a pump.
        The flow rate is set in millilitres per minute (ml/min).
        This command will change the speed of a pump if it is running. If the pump is stopped, it will not cause the pump to start. 
        In sending this command, it will also set the gas flowrate to 0 for this pump."""
        return self._send(f"FR {pump_id} {flow_rate}")
    
    def switch_valve(self, valve_id):
        """Switches a valve.
        The valve_id is an integer from 0 to 9.
        0 and 1 = first valve (R/S, A pump)
        2 and 3 = second valve (R/S, B pump)
        4 and 5 = third valve (top inj.)
        6 and 7 = fourth valve (bottom inj.)
        8 and 9 = fifth valve (waste/collection)"""
        
        return self._send(f"KP {valve_id}")
    
    # def stop_experiment(self):
    #     msg = self._send("PF")
    #     time.sleep(5)
    #     self.connection.close()
        
    def switch_valve(self, valve):
        """
        0 and 1 = first valve (R/S, A pump)
        2 and 3 = second valve (R/S, B pump)
        4 and 5 = third valve (top inj.)
        6 and 7 = fourth valve (bottom inj.)
        8 and 9 = fifth valve (waste/collection)
        """
        
        return self._send(f"KP {valve}")
    
    def set_temp(self, channel, target):
        return self._send(f"R4 ST {channel} {target}")
    
    ############################
    ### Information Commands ###
    ############################
    
    def get_status(self) -> SystemStatus:
        response = self._send("GA")
        status = SystemStatus(response)
        if not status.is_valid():
            return {"error": "Invalid status data"}
        return status
        
    # def set_flowrate(self, channel, flow_rate):
    #     return self._send(f"FR {channel} {flow_rate}")
    
    
if __name__ == "__main__":
    
    r2 = R2Interface(module="R2S")
    
    r2.switch_valve(1)
    
    r2.set_temp(2, 50)
    
    time.sleep(1)
    
    r2.start()
    time.sleep(1)