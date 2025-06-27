import transport, vapourtec

R2 = vapourtec.R2R4(transport.serial("COM1"))

flow_rate = 200       # Flow rate in uL/min
reactor_volume = 3000 # Volume of reactor in uL

# R2.