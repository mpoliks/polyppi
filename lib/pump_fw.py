import time, random, logging
from gpiozero import OutputDevice
from threading import Thread

PUMP_HW = [OutputDevice(5),
           OutputDevice(26),
           OutputDevice(24),
           OutputDevice(11),
           OutputDevice(13),
           OutputDevice(17)]

VALVE_HW = [OutputDevice(6),
            OutputDevice(8),
            OutputDevice(10),
            OutputDevice(12),
            OutputDevice(16),
            OutputDevice(22)]

class Pump(object):

    def __init__(self, id, pump_id, valve_id):
        self.pump = pump_id
        self.pump.off()
        self.valve = valve_id
        self.valve.off()
        self.id = id
        self.state = "inert" #inert, pumping, voiding
        
    def purge(self, level):
        logging.info("Purging System {} for {}".format(self.id, level))
        self.state = "voiding"
        self.pump.off()
        self.valve.on()
        time.sleep(level)
        self.valve.off()
        if level > 5:
            self.state = "inert"
            logging.info("Purged System {}".format(self.id))

    def inflate(self):
        logging.info("Pumping System {}".format(self.id))
        self.purge(2)
        pumplength = random.randint(10,30) 
        logging.info("Pumping System {} for {}".format(self.id, pumplength))
        self.valve.off()
        self.pump.on()
        time.sleep(pumplength)
        self.purge(10)


class PumpBehavior(object):

    def __init__(self):

        self.pumps = []
        self.previous_status = None
        self.thread_timer = 0

        for system in range(len(PUMP_HW)):
            self.pumps.append(Pump(system, PUMP_HW[system], VALVE_HW[system]))
            t = Thread(target= self.pumps[system].purge, args=(20,))
            t.start()

        self.vitals = {
            "pumps_triggered": 0
            }

   
    def update(self, status):

        num_pumps, period_min, period_max = 1, 1, 1

        if status != self.previous_status:
            self.thread_timer = time.time()
            self.previous_status = status
            logging.info("Status Changed, Moving to {}".format(status))

        if status == self.previous_status:

            if status == "kill":
                return

            if status == "inert":
                num_pumps = 1
                period_min = 15
                period_max = 30
                # pick a random pump and inflate/deflate every 15-30 seconds

            if status == "triggered":
                num_pumps = random.randint(3,6)
                period_min = 3
                period_max = 12
                # pick 3 random pumps and inflate/deflate every 10 seconds
           
            if time.time() >= self.thread_timer:
                next_trig = random.randint(period_min, period_max)
                logging.info("Next Pump Event of {} Pumps In {}".format(num_pumps, next_trig))
                self.run(num_pumps)
                self.thread_timer = time.time() + next_trig
 
   
    def run(self, attempts):
        for attempt in range(attempts):
            i = random.randint(0, (len(self.pumps) - 1))
            if self.pumps[i].state == "inert":
                t = Thread (target = self.pumps[i].inflate)
                t.start()
                self.vitals["pumps_triggered"] += 1

    def kill_all(self):
        print("Killing All Pumps -- Please Hold for 20 Seconds")
        logging.info("Killing All Pumps -- Please Hold for 20 Seconds")
        for pump in self.pumps:
            t = Thread(target = pump.purge)
            t.start()
        time.sleep(5)
        print("Killing All Pumps -- Hold for 15 Seconds")
        time.sleep(5)
        print("Killing All Pumps -- Hold for 10 Seconds")
        time.sleep(5)
        print("Killing All Pumps -- Hold for 5 Seconds")
        time.sleep(5)
        print("All Pumps Have Been Reset")
        logging.info("All Pumps Have Been Reset")
        return
