# tap_controller.py
# simulates the IEEE 1149.1 JTAG TAP state machine

class TAPController:
    
    # simulates all 16 states

    STATES = [
        "Test-Logic-Reset", "Run-Test/Idle",
        "Select-DR-Scan", "Capture-DR", "Shift-DR", "Exit1-DR",
        "Pause-DR", "Exit2-DR", "Update-DR",
        "Select-IR-Scan", "Capture-IR", "Shift-IR", "Exit1-IR",
        "Pause-IR", "Exit2-IR", "Update-IR"
    ]

    def __init__(self):
        self.state = "Test-Logic-Reset"
        self.history = [self.state]

    def tms(self, bit):
        
        # transitions the TAP state machine following official IEEE 1149.1 state transition diagram
        # think lookup, if this go there
        
        transitions = {
            "Test-Logic-Reset": {0: "Run-Test/Idle", 1: "Test-Logic-Reset"},
            "Run-Test/Idle":    {0: "Run-Test/Idle", 1: "Select-DR-Scan"},
            "Select-DR-Scan":   {0: "Capture-DR", 1: "Select-IR-Scan"},
            "Capture-DR":       {0: "Shift-DR", 1: "Exit1-DR"},
            "Shift-DR":         {0: "Shift-DR", 1: "Exit1-DR"},
            "Exit1-DR":         {0: "Pause-DR", 1: "Update-DR"},
            "Pause-DR":         {0: "Pause-DR", 1: "Exit2-DR"},
            "Exit2-DR":         {0: "Shift-DR", 1: "Update-DR"},
            "Update-DR":        {0: "Run-Test/Idle", 1: "Select-DR-Scan"},
            "Select-IR-Scan":   {0: "Capture-IR", 1: "Test-Logic-Reset"},
            "Capture-IR":       {0: "Shift-IR", 1: "Exit1-IR"},
            "Shift-IR":         {0: "Shift-IR", 1: "Exit1-IR"},
            "Exit1-IR":         {0: "Pause-IR", 1: "Update-IR"},
            "Pause-IR":         {0: "Pause-IR", 1: "Exit2-IR"},
            "Exit2-IR":         {0: "Shift-IR", 1: "Update-IR"},
            "Update-IR":        {0: "Run-Test/Idle", 1: "Select-DR-Scan"},
        }
        self.state = transitions[self.state][bit]
        self.history.append(self.state)
        return self.state

    # data register, write data
    def goto_shift_dr(self):
        for bit in [1, 0, 0]:
            self.tms(bit)
        return self.state
    
    # instruction register, what command to execute next
    def goto_shift_ir(self):
        for bit in [1, 1, 0, 0]:
            self.tms(bit)
        return self.state

    # reset
    def reset(self):
        for _ in range(5):
            self.tms(1)
        self.tms(0) 
        return self.state
