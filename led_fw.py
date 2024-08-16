import time
import threading
from blinkt import set_pixel, show, clear, set_brightness

# Configure Blinkt! brightness
set_brightness(0.1)

# Global variable to keep track of the current LED state
current_state = None
LED_STATE_FILE = 'home/polyppi/raspberrypi-firmware/led_state.txt'

def get_led_state():
    try:
        with open(LED_STATE_FILE, "r") as f:
            state = f.read().strip()
            return state
    except FileNotFoundError:
        return None

def breathing_color(r, g, b, steps=50, interval=0.02):
    for i in range(steps):
        brightness = (1 + math.sin(i * math.pi / steps)) / 2
        clear()
        set_pixel(0, int(r * brightness), int(g * brightness), int(b * brightness))
        show()
        time.sleep(interval)
    clear()
    show()

def blink_red():
    while current_state not in ['a', 'b', 'c']:
        clear()
        set_pixel(0, 255, 0, 0)
        show()
        time.sleep(0.25)
        clear()
        show()
        time.sleep(0.25)

def handle_led():
    global current_state

    while True:
        state = get_led_state()

        if state != current_state:
            current_state = state

            if state == 'a':
                while current_state == 'a':
                    breathing_color(255, 255, 0)  # Yellow
            elif state == 'b':
                while current_state == 'b':
                    breathing_color(0, 255, 0)  # Green
            elif state == 'c':
                while current_state == 'c':
                    breathing_color(255, 255, 255)  # White
            else:
                blink_red()

        time.sleep(0.1)  # Small delay to prevent CPU overutilization

if __name__ == "__main__":
    # Start the LED handling in a separate thread
    led_thread = threading.Thread(target=handle_led)
    led_thread.daemon = True
    led_thread.start()

    # Main loop
    while True:
        time.sleep(1)  # Main thread remains idle, handling is done in the LED thread
