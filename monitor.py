import threading
import time
from datetime import datetime

class SystemMonitor:
    
    def __init__(self, interface):
        self.interface = interface
        self.running = False
        self.status_log = []
        
