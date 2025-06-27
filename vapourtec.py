import time
import math
import sys

class R2R4(object):
    
    transport = None
    
    def __init__(self, transport):
        """Initialize the controller with a transport object. """
        
        transport.setTerminator("\r\n")
        transport.open()
        
        self.transport = transport
        
    def _send(self, line):
        return self.transport.send(line)
    
    def on(self):
        """Power on the machine."""
        return self._send("PN")
    
    def off(self):
        """Power off the machine."""
        msg = self._send("PF")
        time.sleep(5)
        self.transport.close()
    
    def set_temp(self, heater, target):
        """Set heater temperature.
        
        heater = 0, 1, 2, or 3.
        target = -1000 or 20 to 250 """
        
        return self._send(f"R4 ST {heater} {target}")
    
    def set_flowrate(self, channel, rate):
        """Set the pump flowrate.
        
        channel = ...
        rate = flowrate in uL/min"""
        
        return self._send(f"FR {channel} {rate}")
    
    def switch_valve(self, valve):
        """
        0 and 1 = first valve (R/S, A pump)
        2 and 3 = second valve (R/S, B pump)
        4 and 5 = third valve (top inj.)
        6 and 7 = fourth valve (bottom inj.)
        8 and 9 = fifth valve (waste/collection)
        """
        
        return self._send(f"KP {valve}")