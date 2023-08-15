import logging, smbus, time

## Battery Management:
bus = smbus.SMBus(1)
address = 0x57
transition_flag = False

class Battery (object):

    def __init__(self, bus, address):
        self.bus = bus
        self.address = address
        self.calibrate_battery()
        self.vitals = {
            "charge_level": self.charge_level(),
            "transition_events": 0
        }
        return

    def charge_status(self):
        if (self.bus.read_byte_data(self.address, 0x02) & (1<<7)):
            return "listening"
        return "playing"

    def calibrate_battery(self):
        self.bus.write_byte_data(self.address, 0x0b, 0x29) #turn off write protection
        time.sleep (0.01)
        self.bus.write_byte_data(self.address, 0x20, 0x48) #turn on SCL wake, charge protection
        time.sleep (0.01)
        if self.bus.read_byte_data(self.address, 0x20) == 0x48:
            logging.info("OK: Battery Initialized Correctly")
        else:
            logging.error("ERR: Battery Not Set Correctly!")
            logging.error(self.bus.read_byte_data(self.address, 0x20))

    def charge_level(self):
        return self.bus.read_byte_data(self.address, 0x2A)